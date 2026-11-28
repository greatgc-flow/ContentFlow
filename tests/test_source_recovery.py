"""Exercise source lineage, retention and tombstone replay with synthetic data."""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
import unittest

from contentflow.assets import AssetStore

NOW = datetime(2026, 11, 28, tzinfo=timezone.utc)
LATER = NOW + timedelta(days=1)


class SourceRecoveryTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name)
        self.root = self.base / "live workspace"
        self.root.mkdir()
        self.workspace = uuid4()
        self.first = uuid4()
        self.second = uuid4()
        with AssetStore.create(self.root) as store:
            self.first_digest = store.put(b"synthetic first", sha256(b"synthetic first").hexdigest())
            self.second_digest = store.put(b"synthetic second", sha256(b"synthetic second").hexdigest())

    def add(self, ledger, source, digest, *, expected=0, rights=("read", "backup"), expires=LATER):
        return ledger.record(source, expected, digest=digest, acquired_at=NOW, retain_until=expires,
                             license_ref="fixture-license", rights=rights)

    def test_durable_revision_and_policy(self):
        from contentflow.sources import SourceLedger
        with SourceLedger.create(self.root, self.workspace) as ledger:
            self.assertEqual(self.add(ledger, self.first, self.first_digest), 1)
            self.assertEqual(self.add(ledger, self.first, self.second_digest, expected=1), 2)
            with self.assertRaises(ValueError):
                self.add(ledger, self.first, self.first_digest, expected=1)
            with self.assertRaises(ValueError):
                self.add(ledger, self.second, "f"*64)
        with SourceLedger.open(self.root, self.workspace) as ledger:
            self.assertEqual(ledger.latest(self.first)["digest"], self.second_digest)
            self.assertEqual(ledger.eligible(NOW)[str(self.first)]["revision"], 2)
            self.assertEqual(ledger.eligible(LATER), {})
        with self.assertRaises(ValueError):
            SourceLedger.open(self.root, uuid4())

    def test_old_snapshot_replays_tombstone_and_uses_current_policy(self):
        from contentflow.sources import SourceLedger, checkpoint_sources, restore_sources
        snapshot, restored = self.base / "snapshot", self.base / "restored"
        with SourceLedger.create(self.root, self.workspace) as live:
            self.add(live, self.first, self.first_digest)
            self.add(live, self.second, self.second_digest)
            checkpoint_sources(live, snapshot, NOW)
            live.retire(self.first, expected_revision=1)
            self.assertEqual(live.retire(self.first, expected_revision=1), 2)
        with SourceLedger.open(self.root, self.workspace) as live:
            self.assertIsNone(live.latest(self.first))
            self.assertEqual(restore_sources(live, snapshot, restored, NOW), (str(self.second),))
            self.assertTrue((live.root / "objects/sha256" / self.first_digest[:2] / self.first_digest).exists())
        with SourceLedger.open(restored, self.workspace) as copy:
            self.assertIsNone(copy.latest(self.first))
            with self.assertRaises(ValueError):
                self.add(copy, self.first, self.second_digest)
            self.assertEqual(copy.latest(self.second)["digest"], self.second_digest)
        with AssetStore.open(restored) as store:
            with self.assertRaises(ValueError):
                store.read(self.first_digest)
            self.assertEqual(store.read(self.second_digest), b"synthetic second")

    def test_read_only_rights_deduplicated_data_and_expiry(self):
        from contentflow.sources import SourceLedger, checkpoint_sources, restore_sources
        from contentflow.checkpoint import verify
        snapshot, restored = self.base / "snapshot", self.base / "restored"
        with SourceLedger.create(self.root, self.workspace) as live:
            self.add(live, self.first, self.first_digest, rights=("read",))
            self.add(live, self.second, self.first_digest)
            checkpoint_sources(live, snapshot, NOW)
            self.assertEqual(set(verify(snapshot / "assets")), {self.first_digest})
            self.assertEqual(restore_sources(live, snapshot, restored, LATER), ())
        with AssetStore.open(restored) as store:
            with self.assertRaises(ValueError):
                store.read(self.first_digest)

    def test_foreign_or_tampered_snapshot_never_creates_destination(self):
        from contentflow.sources import SourceLedger, checkpoint_sources, restore_sources
        snapshot, restored = self.base / "snapshot", self.base / "restored"
        with SourceLedger.create(self.root, self.workspace) as live:
            self.add(live, self.first, self.first_digest)
            checkpoint_sources(live, snapshot, NOW)
            marker = snapshot / "sources.json"
            original = marker.read_bytes()
            marker.write_bytes(original.replace(str(self.workspace).encode(), str(uuid4()).encode()))
            with self.assertRaises(ValueError):
                restore_sources(live, snapshot, restored, NOW)
            self.assertFalse(restored.exists())
            marker.write_bytes(original)
            asset = snapshot / "assets/objects/sha256" / self.first_digest[:2] / self.first_digest
            asset.write_bytes(b"changed")
            with self.assertRaises(ValueError):
                restore_sources(live, snapshot, restored, NOW)
            self.assertFalse(restored.exists())
