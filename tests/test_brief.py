import hashlib
import json
import subprocess
import sys
import unittest

from test_c1 import ROOT


class SyntheticBriefTests(unittest.TestCase):
    def test_calculation_uses_actual_bytes_units_and_locator(self):
        from contentflow.brief import processing_time_brief
        for values, expected in [((100, 75), "25"), ((80, 40), "50"), ((80, 90), "-12.5")]:
            raw = f"sample,value,unit\nbaseline,{values[0]},ms\noptimized,{values[1]},ms\n".encode()
            brief = processing_time_brief(raw)
            self.assertEqual(brief["relative_decrease_percent"], expected)
            self.assertEqual(brief["source_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(brief["locator"], "CSV records 2-3")
            self.assertEqual(brief["formula"], "(baseline - optimized) * 100 / baseline")
            self.assertTrue(brief["test_only"])
            self.assertEqual(brief["review_status"], "DRAFT")

    def test_invalid_evidence(self):
        from contentflow.brief import processing_time_brief
        for data in ("baseline,0,ms\noptimized,75,ms", "baseline,100,s\noptimized,75,ms",
                     "baseline,100,ms\noptimized,eval(),ms", "baseline,100,ms\nbaseline,75,ms",
                     "baseline,100,ms\noptimized,75,ms\nextra,42,ms"):
            with self.subTest(data=data), self.assertRaises(ValueError):
                processing_time_brief(("sample,value,unit\n" + data).encode())

    def test_standalone_synthetic_brief(self):
        proc = subprocess.run([sys.executable, "-B", "-m", "contentflow", "brief", "preview", "--json"],
                              cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertIn("TEST_ONLY", result["disclosure"])
        self.assertEqual(result["relative_decrease_percent"], "25")
        self.assertEqual(result["source_sha256"], hashlib.sha256(
            (ROOT / "contentflow/fixtures/processing-times.csv").read_bytes()).hexdigest())
