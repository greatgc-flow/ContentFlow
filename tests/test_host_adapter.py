"""Validate ContentFlow's offline host adapter against the frozen fixture wire."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from uuid import UUID
import unittest

from contentflow.assets import AssetStore
from contentflow.execution import Money
from contentflow.outbox import FixtureOutbox
from contentflow.sources import SourceLedger
from test_asset_store import DIGEST, PAYLOAD
from test_c1 import ROOT

DESIGN = ROOT / "design/engram-package-platform-v0.3/fixtures"
WORKSPACE = UUID("00000000-0000-4000-8000-000000000001")


class HostAdapterTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.request = json.loads((DESIGN / "cf.request.json").read_text())
        self.request["deadline"] = (datetime.now(timezone.utc) + timedelta(minutes=1)).isoformat()
        (self.root / self.request["working_rel"]).mkdir(parents=True)
        self.source = self.root / "ContentFlow/data/live"
        self.source.mkdir(parents=True)
        self.outbox = self.source / "outbox.sqlite3"
        with AssetStore.create(self.source) as assets:
            assets.put(PAYLOAD, DIGEST)
        with SourceLedger.create(self.source, WORKSPACE), FixtureOutbox.create(self.outbox, WORKSPACE, Money(100, "KRW", 0)):
            pass
        (self.root / "ContentFlow/checkpoints").mkdir()
        (self.root / "ContentFlow/recovery").mkdir()

    def call(self, raw=None, *, authorize=False, request=None):
        req = self.request if request is None else request
        command = [sys.executable, "-B", "-m", "contentflow.host_adapter",
                   "--root", str(self.root), "--installation-id", "fixture-install",
                   "--generation", "gen-1", "--workspace-id", str(WORKSPACE),
                   "--plan-digest", self.request["plan_digest"]]
        if authorize:
            command.append("--allow-fixture-writes")
        return subprocess.run(command, cwd=ROOT, input=raw if raw is not None else json.dumps(req).encode(),
                              capture_output=True, timeout=15)

    def test_health_echo_and_read_only(self):
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        result = self.call()
        self.assertEqual(result.returncode, 0, result.stderr)
        response = json.loads(result.stdout)
        for key in ("request_id", "parent_op_id", "installation_id", "package_id", "generation", "operation"):
            self.assertEqual(response[key], self.request[key])
        self.assertEqual(response["status"], "OK")
        self.assertEqual(response["receipt"]["observed_state"], "UNCHANGED")
        self.assertEqual(before, {p.relative_to(self.root): p.read_bytes()
                                  for p in self.root.rglob("*") if p.is_file()})

    def test_rejects_duplicate_keys_forged_identity_paths_and_deadline(self):
        values = [{"protocol_version": "1.1"}, {"generation": "not-gen-1"}, {"installation_id": "foreign"},
                  {"working_rel": "ContentFlow/../elsewhere"}, {"plan_digest": "0" * 64},
                  {"deadline": "2020-01-01T00:00:00Z"}]
        for override in values:
            result = self.call(request=self.request | override)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertFalse(result.stdout)
        raw = json.dumps(self.request).replace('"fixture_only": true', '"fixture_only": true, "fixture_only": true').encode()
        self.assertEqual(self.call(raw).returncode, 2)

    def test_checkpoint_and_restore_need_explicit_fixture_authority_and_duplicate_is_unknown(self):
        checkpoint = "ContentFlow/checkpoints/backup-1"
        request = self.request | {"operation": "checkpoint", "phase": "DRAINED", "scope": ["BACKUP"],
                                  "checkpoint_rel": checkpoint}
        blocked = self.call(request=request)
        self.assertEqual(json.loads(blocked.stdout)["status"], "BLOCKED")
        self.assertFalse((self.root / checkpoint).exists())
        allowed = self.call(request=request, authorize=True)
        receipt = json.loads(allowed.stdout)["receipt"]
        self.assertIsNotNone(receipt["checkpoint_sha256"])
        self.assertEqual(receipt["observed_state"], "NEW")
        duplicate = json.loads(self.call(request=request, authorize=True).stdout)
        self.assertEqual((duplicate["status"], duplicate["next_action"]), ("UNKNOWN", "RECONCILE"))
        request.update(operation="restore", phase="APPLYING", scope=["DOMAIN_DATA"], request_id="restore-1")
        restored = json.loads(self.call(request=request, authorize=True).stdout)
        self.assertEqual(restored["status"], "OK")
        self.assertTrue((self.root / "ContentFlow/recovery/restore-1/workspace.json").is_file())
