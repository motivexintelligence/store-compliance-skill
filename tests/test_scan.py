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
            "AND-16KB-PAGE", "AND-EDGE-TO-EDGE", "AND-PREDICTIVE-BACK", "AND-ORIENTATION-LOCK", "AND-MINIFY-OFF",
            "AND-RESTORE-CREDENTIALS", "AND-LEGACY-GSI", "AND-SIDELOAD-FLAVOR",
            "IOS-DEPLOYMENT-TARGET", "IOS-XCODE-PINNED-OLD", "IOS-SDK-MANIFEST-RISK", "IOS-PRIVACY-MANIFEST-INVALID",
            "IOS-ADS-IN-EXTENSION", "X-CUSTOM-REVIEW-PROMPT", "X-SIWA-RELAY-DOMAIN", "X-AGE-RATING-INPUTS",
            "HMS-GMS-DEPENDENCY",
        }
        self.assertTrue(expected <= ids(self.app), expected - ids(self.app))

    def test_findings_are_well_formed(self):
        for f in self.app["findings"]:
            self.assertIn(f["level"], scan.LEVELS)
            self.assertTrue(f["refs"] and f["title"])
            self.assertLessEqual(len(f["evidence"]), scan.MAX_EVIDENCE)


class HarmonyFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.apps = run("harmony_app")
        cls.app = cls.apps[0]

    def test_detected_as_arkts(self):
        self.assertEqual(len(self.apps), 1)
        self.assertEqual(self.app["facts"]["stack"], "arkts")
        self.assertEqual(self.app["facts"]["platforms"], ["harmonyos"])

    def test_facts(self):
        h = self.app["facts"]["harmonyos"]
        self.assertEqual(h["bundleName"], "com.demo")
        self.assertEqual((h["compatibleSdk"], h["targetSdk"]), (9, 12))
        self.assertIn("READ_IMAGEVIDEO", h["permissions"])

    def test_expected_findings(self):
        expected = {
            "HOS-BUILD-GATES", "HOS-TARGET-SDK", "HOS-SIGNING", "HOS-PERM-DECLARE", "HOS-PERM-RESTRICTED",
            "HOS-PERM-DEPRECATED", "HOS-PERM-LOCATION", "HOS-PERM-STARTUP", "HOS-CONSENT-FIRST", "HOS-HUAWEI-ID",
            "HOS-OHPM-DEPS", "AGC-ICP-FILING", "AGC-OAID", "X-PLACEHOLDER",
        }
        self.assertTrue(expected <= ids(self.app), expected - ids(self.app))

    def test_huawei_refs_added(self):
        placeholder = next(f for f in self.app["findings"] if f["id"] == "X-PLACEHOLDER")
        self.assertTrue(any("AppGallery" in r for r in placeholder["refs"]))


class Json5(unittest.TestCase):
    def test_comments_quotes_trailing_commas(self):
        text = "{ // c\n a: 'x', /* b */ \"u\": \"https://e.com/p\", list: [1, 2,], }"
        self.assertEqual(scan.json5_loads(text), {"a": "x", "u": "https://e.com/p", "list": [1, 2]})

    def test_api_level(self):
        self.assertEqual([scan.api_level(v) for v in ("5.0.0(12)", "26.0.0", 12, None)], [12, 26, 12, None])


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
