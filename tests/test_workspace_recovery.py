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
