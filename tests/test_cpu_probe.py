"""Real Linux media qualification for the pinned development build."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_c1 import ROOT


PIN = "e8a8d46f5225f3062cec7c07fb145d58ae73c603cb740dcd5bad34bfb54e455a"
BINARY = Path("/usr/bin/ffmpeg")


@unittest.skipUnless(BINARY.is_file() and hashlib.sha256(BINARY.read_bytes()).hexdigest() == PIN,
                     "pinned Linux FFmpeg unavailable")
class NativeMediaTests(unittest.TestCase):
    def test_full_export_decode_and_corruption_oracle(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "fixture output"
            def invoke(op):
                return subprocess.run([sys.executable, "-B", str(ROOT / "tools/probe_cpu.py"), op, str(dest)],
                                      capture_output=True, text=True, timeout=120, cwd=tmp)
            made = invoke("render")
            self.assertEqual(made.returncode, 0, made.stderr)
            manifest = json.loads((dest / "manifest.json").read_bytes())
            self.assertEqual(manifest["qc"]["decoded_frames"], 450)
            self.assertTrue(manifest["test_only"])
            self.assertEqual(manifest["publication"], "PROHIBITED")
            self.assertGreater(manifest["qc"]["audio_peak"], 100)
            self.assertEqual(manifest["qc"]["captions"], 2)
            for name in ("source.csv", "brief.json", "article.md", "scenes.json", "chart.svg",
                         "thumbnail.png", "captions.srt", "preview.mp4"):
                self.assertEqual(hashlib.sha256((dest / name).read_bytes()).hexdigest(),
                                 manifest["files"][name])
            self.assertEqual(invoke("verify").returncode, 0)
            self.assertNotEqual(invoke("render").returncode, 0)
            # Resealing a placeholder thumbnail must still fail the independent visual oracle.
            thumbnail = dest / "thumbnail.png"
            marker = dest / "manifest.json"
            original_png, original_marker = thumbnail.read_bytes(), marker.read_bytes()
            subprocess.run([str(BINARY), "-v", "error", "-y", "-f", "lavfi", "-i",
                            "color=black:size=1080x1920", "-frames:v", "1", "-threads", "1",
                            str(thumbnail)], check=True, timeout=20)
            manifest["files"]["thumbnail.png"] = hashlib.sha256(thumbnail.read_bytes()).hexdigest()
            marker.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            self.assertNotEqual(invoke("verify").returncode, 0)
            thumbnail.write_bytes(original_png)
            marker.write_bytes(original_marker)
            (dest / "captions.srt").write_text("stale", encoding="ascii")
            self.assertNotEqual(invoke("verify").returncode, 0)
            self.assertEqual((dest / "captions.srt").read_text(), "stale")
