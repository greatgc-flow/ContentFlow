import json
from pathlib import Path
import tempfile
import unittest

from test_asset_store import DIGEST, PAYLOAD


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.workspace = self.root / "original"
        self.workspace.mkdir()

    def test_checkpoint_is_self_contained_and_independent(self):
        from contentflow.assets import AssetStore
        from contentflow.checkpoint import checkpoint, restore, verify
        snapshot = self.root / "checkpoint"
        with AssetStore.create(self.workspace) as original:
            original.put(PAYLOAD, DIGEST)
            orphan = original.objects / DIGEST[:2] / (DIGEST[:2] + "f" * 62)
            orphan.write_bytes(b"preserve unindexed")
            checkpoint(original, snapshot)
            self.assertEqual(original.orphans(), (orphan.name,))
            with self.assertRaises(FileExistsError):
                checkpoint(original, snapshot)
        self.assertEqual(verify(snapshot), {DIGEST: len(PAYLOAD)})
        self.assertFalse(any(p.name.endswith(("-wal", "-shm")) for p in snapshot.iterdir()))
        restored = self.root / "restored"
        restore(snapshot, restored)
        with AssetStore.open(restored) as copy:
            self.assertEqual(copy.read(DIGEST), PAYLOAD)
            self.assertEqual(copy.orphans(), ())
        with self.assertRaises(FileExistsError):
            restore(snapshot, self.workspace)
        self.assertEqual(orphan.read_bytes(), b"preserve unindexed")

    def test_corruption_and_unexpected_files_block_restore(self):
        from contentflow.assets import AssetStore
        from contentflow.checkpoint import checkpoint, restore
        snapshot = self.root / "checkpoint"
        with AssetStore.create(self.workspace) as original:
            original.put(PAYLOAD, DIGEST)
            checkpoint(original, snapshot)
        destination = self.root / "would-be-restore"
        obj = snapshot / "objects/sha256" / DIGEST[:2] / DIGEST
        obj.write_bytes(b"corruption")
        with self.assertRaises(ValueError):
            restore(snapshot, destination)
        self.assertFalse(destination.exists())
        self.assertEqual(obj.read_bytes(), b"corruption")
        obj.write_bytes(PAYLOAD)
        (snapshot / "unexpected.txt").write_bytes(b"x")
        with self.assertRaises(ValueError):
            restore(snapshot, destination)
        self.assertFalse(destination.exists())
        (snapshot / "unexpected.txt").unlink()
        marker = snapshot / "checkpoint.json"
        body = json.loads(marker.read_bytes())
        body["assets"] = {}
        marker.write_text(json.dumps(body), encoding="utf-8")
        with self.assertRaises(ValueError):
            restore(snapshot, destination)
        self.assertFalse(destination.exists())

    def test_missing_asset_prevents_sealing(self):
        from contentflow.assets import AssetStore
        from contentflow.checkpoint import checkpoint, verify
        snapshot = self.root / "bad"
        with AssetStore.create(self.workspace) as original:
            original.put(PAYLOAD, DIGEST)
            (original.objects / DIGEST[:2] / DIGEST).unlink()
            with self.assertRaises(ValueError):
                checkpoint(original, snapshot)
        self.assertFalse((snapshot / "checkpoint.json").exists())
        with self.assertRaises(ValueError):
            verify(snapshot)
