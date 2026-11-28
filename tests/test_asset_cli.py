from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest

from test_asset_store import DIGEST, PAYLOAD
from test_c1 import ROOT


class AssetCommandTests(unittest.TestCase):
    def test_command_lifecycle_and_existing_checkpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            origin = root / "source workspace"
            origin.mkdir()
            source = root / "synthetic.csv"
            source.write_bytes(PAYLOAD)
            snapshot, restored = root / "snapshot", root / "restored"

            def run(*args, expected=0):
                proc = subprocess.run([sys.executable, "-B", "-m", "contentflow", "assets", *map(str, args)],
                                      cwd=root, env=dict(os.environ, PYTHONPATH=str(ROOT)),
                                      capture_output=True, text=True, timeout=10)
                self.assertEqual(proc.returncode, expected, proc.stderr)
                return json.loads(proc.stdout if expected == 0 else proc.stderr)

            self.assertEqual(run("init", origin)["status"], "INITIALIZED")
            self.assertEqual(run("add", origin, source, "--sha256", DIGEST)["sha256"], DIGEST)
            self.assertEqual(run("checkpoint", origin, snapshot)["status"], "CHECKPOINTED")
            self.assertEqual(run("verify", snapshot)["assets"], {DIGEST: len(PAYLOAD)})
            self.assertEqual(run("restore", snapshot, restored)["status"], "RESTORED")
            self.assertEqual(run("restore", snapshot, restored, expected=2)["status"], "INVALID_INPUT")
            self.assertEqual((restored / "objects/sha256" / DIGEST[:2] / DIGEST).read_bytes(), PAYLOAD)
