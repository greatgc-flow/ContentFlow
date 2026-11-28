"""Integration tests for source and pending-effect workspace bundles."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest

from contentflow.assets import AssetStore
from contentflow.outbox import FixtureOutbox
from contentflow.sources import SourceLedger
from test_outbox import A, BOUND, CAP, WS
from test_source_recovery import NOW, LATER
from test_asset_store import DIGEST, PAYLOAD


class WorkspaceRecoveryTests(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.root = self.base / "live sources"
        self.root.mkdir()
        self.live = self.base / "live outbox.sqlite3"
        self.snapshot = self.base / "checkpoint"
        self.restored = self.base / "restored"
        with AssetStore.create(self.root) as store:
            store.put(PAYLOAD, DIGEST)
        with SourceLedger.create(self.root, WS) as sources, FixtureOutbox.create(self.live, WS, CAP):
            sources.record(A, 0, digest=DIGEST, acquired_at=NOW, retain_until=LATER,
                           license_ref="fixture-license", rights=("read", "backup"))

    def test_combined_restore_uses_current_rights_and_outbox(self):
        from contentflow.workspace_recovery import checkpoint_workspace, inspect_workspace, restore_workspace
        with SourceLedger.open(self.root, WS) as sources, FixtureOutbox.open(self.live, WS) as outbox:
            outbox.prepare(A, {"private": "fixture-secret"}, BOUND)
            checkpoint_workspace(sources, outbox, self.snapshot, NOW)
            self.assertEqual(inspect_workspace(self.snapshot)["format"], "workspace-checkpoint-v1")
            sources.retire(A, 1)
            outbox.claim(A)
            restore_workspace(sources, outbox, self.snapshot, self.restored, NOW)
            with self.assertRaises(ValueError):
                outbox.claim(A)
        receipt = inspect_workspace(self.restored)
        self.assertEqual(receipt["format"], "workspace-review-v1")
        self.assertFalse(receipt["execution_authorized"])
        self.assertEqual(receipt["outbox"]["operations"][str(A)]["state"], "UNKNOWN")
        with SourceLedger.open(self.restored / "sources", WS) as projection:
            self.assertIsNone(projection.latest(A))
        with AssetStore.open(self.restored / "sources") as objects:
            with self.assertRaises(ValueError):
                objects.read(DIGEST)
        with self.assertRaises(ValueError):
            FixtureOutbox.open(self.restored / "outbox.json", WS)

    def test_cross_ledger_and_tampered_bundle_refuse_to_publish(self):
        from contentflow.workspace_recovery import checkpoint_workspace, inspect_workspace, restore_workspace
        from uuid import uuid4
        with SourceLedger.open(self.root, WS) as sources:
            with FixtureOutbox.create(self.base / "foreign.sqlite3", uuid4(), CAP) as foreign:
                with self.assertRaises(ValueError):
                    checkpoint_workspace(sources, foreign, self.snapshot, NOW)
                self.assertFalse(self.snapshot.exists())
            with FixtureOutbox.open(self.live, WS) as outbox:
                checkpoint_workspace(sources, outbox, self.snapshot, NOW)
                (self.snapshot / "outbox.json").write_bytes(b"invalid")
                with self.assertRaises(ValueError):
                    restore_workspace(sources, outbox, self.snapshot, self.restored, NOW)
                self.assertFalse(self.restored.exists())
                with self.assertRaises(ValueError):
                    inspect_workspace(self.snapshot)

    def test_failure_after_sources_never_seals_checkpoint_or_leaves_output(self):
        from contentflow.workspace_recovery import checkpoint_workspace, inspect_workspace
        with SourceLedger.open(self.root, WS) as sources, FixtureOutbox.open(self.live, WS) as outbox:
            with patch("contentflow.workspace_recovery.outbox_recovery._write", side_effect=OSError):
                with self.assertRaises(OSError):
                    checkpoint_workspace(sources, outbox, self.snapshot, NOW)
        self.assertFalse(self.snapshot.exists())
        self.snapshot.mkdir()
        with self.assertRaises(ValueError):
            inspect_workspace(self.snapshot)

    def test_standalone_console_round_trip(self):
        import json
        import os
        import subprocess
        import sys
        from test_c1 import ROOT

        def run(verb, *args):
            proc = subprocess.run([sys.executable, "-B", "-m", "contentflow", "workspace", verb,
                                   *map(str, args)], cwd=self.base, text=True, capture_output=True,
                                  env=dict(os.environ, PYTHONPATH=str(ROOT)), timeout=15)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            return json.loads(proc.stdout)

        with FixtureOutbox.open(self.live, WS) as outbox:
            outbox.prepare(A, {}, BOUND)
            outbox.claim(A)
        self.assertEqual(run("checkpoint", self.root, self.live, self.snapshot,
                             "--workspace-id", WS)["status"], "CHECKPOINTED")
        self.assertEqual(run("restore-review", self.root, self.live, self.snapshot, self.restored,
                             "--workspace-id", WS)["status"], "RESTORED_FOR_REVIEW")
        report = run("inspect", self.restored)
        self.assertFalse(report["execution_authorized"])
        self.assertEqual(report["outbox"]["operations"][str(A)]["state"], "UNKNOWN")

    def test_os_exit_before_seal_leaves_unreadable_candidate_and_live_ledger(self):
        import os
        import subprocess
        import sys
        from contentflow.workspace_recovery import inspect_workspace
        from test_c1 import ROOT

        child = """
import os, sys
from datetime import datetime
from pathlib import Path
from uuid import UUID
from contentflow import workspace_recovery
from contentflow.outbox import FixtureOutbox
from contentflow.sources import SourceLedger
root, db, snapshot = map(Path, sys.argv[1:4])
workspace, now = UUID(sys.argv[4]), datetime.fromisoformat(sys.argv[5])
workspace_recovery._seal = lambda *_: os._exit(81)
with SourceLedger.open(root, workspace) as sources, FixtureOutbox.open(db, workspace) as outbox:
    workspace_recovery.checkpoint_workspace(sources, outbox, snapshot, now)
"""
        proc = subprocess.run([sys.executable, "-B", "-c", child, str(self.root), str(self.live),
                               str(self.snapshot), str(WS), NOW.isoformat()],
                              capture_output=True, cwd=self.base,
                              env=dict(os.environ, PYTHONPATH=str(ROOT)), timeout=15)
        self.assertEqual(proc.returncode, 81, proc.stderr)
        self.assertTrue((self.snapshot / "sources").exists())
        with self.assertRaises(ValueError):
            inspect_workspace(self.snapshot)
        with SourceLedger.open(self.root, WS) as current:
            self.assertEqual(current.latest(A)["digest"], DIGEST)

    def test_checkpoint_holds_both_ledger_writers_before_reading_sources(self):
        import sqlite3
        from contextlib import closing
        from contentflow import workspace_recovery
        capture = workspace_recovery.source_recovery._capture_sources

        def try_competing_writes(*args):
            for path in (self.root / "sources.sqlite3", self.live):
                with closing(sqlite3.connect(path, timeout=0)) as db:
                    with self.assertRaises(sqlite3.OperationalError):
                        db.execute("BEGIN IMMEDIATE")
            capture(*args)

        with SourceLedger.open(self.root, WS) as sources, FixtureOutbox.open(self.live, WS) as outbox:
            with patch.object(workspace_recovery.source_recovery, "_capture_sources", try_competing_writes):
                workspace_recovery.checkpoint_workspace(sources, outbox, self.snapshot, NOW)
        self.assertEqual(workspace_recovery.inspect_workspace(self.snapshot)["workspace"], str(WS))

    def test_resealed_invalid_workspace_uuid_is_rejected(self):
        from contentflow.domain import canonical, decode, digest
        from contentflow.workspace_recovery import checkpoint_workspace, inspect_workspace
        with SourceLedger.open(self.root, WS) as sources, FixtureOutbox.open(self.live, WS) as outbox:
            checkpoint_workspace(sources, outbox, self.snapshot, NOW)
        marker = self.snapshot / "workspace.json"
        document = decode(marker.read_bytes())
        document["body"]["workspace"] = []
        document["sha256"] = digest(document["body"])
        marker.write_bytes(canonical(document))
        with self.assertRaises(ValueError):
            inspect_workspace(self.snapshot)
