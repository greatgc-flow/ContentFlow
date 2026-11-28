import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_c1 import ROOT


PAYLOAD = b"sample,value,unit\nbaseline,100,ms\noptimized,75,ms\n"
DIGEST = hashlib.sha256(PAYLOAD).hexdigest()


class AssetStoreTests(unittest.TestCase):
    def setUp(self):
        work = tempfile.TemporaryDirectory()
        self.addCleanup(work.cleanup)
        self.root = Path(work.name) / "workspace"
        self.root.mkdir()

    def test_verified_content_addressing_and_idempotency(self):
        from contentflow.assets import AssetStore
        with AssetStore.create(self.root) as store:
            self.assertEqual(store.put(PAYLOAD, DIGEST), DIGEST)
            self.assertEqual(store.put(PAYLOAD, DIGEST), DIGEST)
            self.assertEqual(store.read(DIGEST), PAYLOAD)
            self.assertEqual(store.orphans(), ())
            with self.assertRaises(ValueError):
                store.put(b"wrong bytes", DIGEST)
            with self.assertRaises(ValueError):
                store.read("../outside")
        self.assertEqual(list((self.root / "objects/sha256" / DIGEST[:2]).iterdir()),
                         [self.root / "objects/sha256" / DIGEST[:2] / DIGEST])

    def test_missing_or_corrupt_committed_file_is_reported_and_preserved(self):
        from contentflow.assets import AssetStore
        path = self.root / "objects/sha256" / DIGEST[:2] / DIGEST
        with AssetStore.create(self.root) as store:
            store.put(PAYLOAD, DIGEST)
            path.write_bytes(b"corrupt")
            for action in (lambda: store.read(DIGEST), lambda: store.put(PAYLOAD, DIGEST)):
                with self.assertRaises(ValueError):
                    action()
            self.assertEqual(path.read_bytes(), b"corrupt")
            path.unlink()
            for action in (lambda: store.read(DIGEST), lambda: store.put(PAYLOAD, DIGEST)):
                with self.assertRaises(ValueError):
                    action()

    def test_real_interruption_before_metadata_commit(self):
        from contentflow.assets import AssetStore
        with AssetStore.create(self.root):
            pass
        child = """
from pathlib import Path
import os,sys
from contentflow.assets import AssetStore
with AssetStore.open(Path(sys.argv[1])) as store:
    store._db.set_trace_callback(lambda sql: os._exit(75) if sql == 'COMMIT' else None)
    store.put(bytes.fromhex(sys.argv[2]), sys.argv[3])
"""
        result = subprocess.run([sys.executable, "-B", "-c", child, str(self.root), PAYLOAD.hex(), DIGEST],
                                cwd=self.root.parent, env=dict(os.environ, PYTHONPATH=str(ROOT)), timeout=10)
        self.assertEqual(result.returncode, 75)
        with AssetStore.open(self.root) as store:
            self.assertEqual(store.orphans(), (DIGEST,))
            with self.assertRaises(ValueError):
                store.read(DIGEST)
            store.put(PAYLOAD, DIGEST)
            self.assertEqual(store.orphans(), ())
            self.assertEqual(store.read(DIGEST), PAYLOAD)

    def test_existing_database_and_linked_object_root(self):
        from contentflow.assets import AssetStore
        database = self.root / "assets.sqlite3"
        database.write_bytes(b"existing")
        with self.assertRaises(FileExistsError):
            AssetStore.create(self.root)
        with self.assertRaises(ValueError):
            AssetStore.open(self.root)
        self.assertEqual(database.read_bytes(), b"existing")
        database.unlink()
        outside = self.root.parent / "outside"
        outside.mkdir()
        try:
            (self.root / "objects").symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("symlink creation requires OS permission")
        with self.assertRaises(ValueError):
            AssetStore.create(self.root)
        self.assertFalse(database.exists())
        self.assertEqual(list(outside.iterdir()), [])
