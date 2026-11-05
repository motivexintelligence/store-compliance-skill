"""Regression tests for scripts/scan.py. Run: python3 -m unittest discover -s tests"""
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
SCAN = ROOT / "scripts" / "scan.py"

spec = importlib.util.spec_from_file_location("scan", SCAN)
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)


def run(fixture):
    apps = scan.find_app_dirs(FIXTURES / fixture)
    return [scan.Scan(a).run() for a in apps]


def ids(app):
    return {f["id"] for f in app["findings"]}


class FlutterFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.apps = run("flutter_app")
        cls.app = cls.apps[0]

    def test_one_app_found(self):
        self.assertEqual(len(self.apps), 1)
        self.assertEqual(self.app["facts"]["stack"], "flutter")

    def test_facts(self):
        f = self.app["facts"]
        self.assertEqual(f["android_sdk_levels"]["targetSdk"], "34")
        self.assertIn("google_mobile_ads", f["sdk_categories"]["ads"])

    def test_expected_findings(self):
        expected = {
            "AND-TARGET-SDK", "AND-BILLING-VERSION", "AND-PERM-READ_MEDIA_IMAGES", "AND-PERM-QUERY_ALL_PACKAGES",
            "AND-CLEARTEXT", "IOS-ATT", "X-REVIEW-MODE-SWITCH", "X-SIGN-IN-WITH-APPLE", "X-ACCOUNT-DELETION",
            "X-IAP-RESTORE", "X-PLACEHOLDER", "X-PRIVACY-POLICY-LINK",
        }
        self.assertTrue(expected <= ids(self.app), expected - ids(self.app))

    def test_findings_are_well_formed(self):
        for f in self.app["findings"]:
            self.assertIn(f["level"], scan.LEVELS)
            self.assertTrue(f["refs"] and f["title"])
            self.assertLessEqual(len(f["evidence"]), scan.MAX_EVIDENCE)


class Cli(unittest.TestCase):
    def test_json_output(self):
        out = subprocess.run([sys.executable, "-I", str(SCAN), str(FIXTURES / "flutter_app")],
                             capture_output=True, text=True, check=True).stdout
        data = json.loads(out)
        self.assertEqual(len(data["apps"]), 1)

    def test_no_app(self):
        r = subprocess.run([sys.executable, "-I", str(SCAN), str(ROOT / "references")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 1)
        self.assertIn("error", json.loads(r.stdout))


if __name__ == "__main__":
    unittest.main()
