import unittest
from pathlib import Path
import tomllib

from test_c1 import ROOT


class DistributionTests(unittest.TestCase):
    def test_standalone_command_and_fixture_are_packaged(self):
        manifest = tomllib.loads((ROOT / "pyproject.toml").read_text())
        self.assertEqual(manifest["project"]["scripts"]["contentflow"], "contentflow.__main__:main")
        self.assertEqual(manifest["project"]["dependencies"], [])
        self.assertTrue(any(Path(ROOT / "contentflow").glob(
            manifest["tool"]["setuptools"]["package-data"]["contentflow"][0])))
