import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(*a):
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "labstats.py"), "--json", *a], capture_output=True, text=True, encoding="utf8")
    return r


class StatsTests(unittest.TestCase):
    def test_welch(self):
        r = run("ttest", "--a", "5.1", "4.8", "5.5", "--b", "6.2", "6.0", "6.8")
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertLess(d["p"], 0.05)

    def test_anova(self):
        r = run("anova", "--g", "a=1,2,3", "--g", "b=2,3,4", "--g", "c=5,6,7")
        self.assertEqual(r.returncode, 0, r.stderr)
        d = json.loads(r.stdout)
        self.assertAlmostEqual(d["F"], 13.0, places=1)

    def test_small_n_refused(self):
        r = run("ttest", "--a", "1", "--b", "2")
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
