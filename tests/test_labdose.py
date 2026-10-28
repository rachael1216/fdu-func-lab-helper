import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARGS = ["--dose", "110.8", "147.7", "196.9", "262.5", "350", "--n", "22", "--deaths", "0", "1", "14", "20", "22", "--ref", "200", "--boot", "200", "--json"]


class DoseTests(unittest.TestCase):
    def test_reference_values(self):
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "labdose.py"), *ARGS], capture_output=True, text=True, encoding="utf8")
        self.assertEqual(r.returncode, 0, r.stderr)
        o = json.loads(r.stdout)
        self.assertAlmostEqual(o["koch"]["ld50"], 191.85, places=1)
        self.assertAlmostEqual(o["koch"]["lo"], 178.25, places=1)
        pm, lm = o["models"]["probit"], o["models"]["logit"]
        self.assertAlmostEqual(pm["ld50"], 193.10, places=1)
        self.assertAlmostEqual(pm["lo"], 179.16, delta=0.05)
        self.assertAlmostEqual(lm["ld50"], 191.92, places=1)
        self.assertAlmostEqual(pm["aic"], 13.823, places=2)
        self.assertAlmostEqual(pm["gof_p"], 0.602, places=2)
        self.assertAlmostEqual(o["sensitivity"]["slope_pp_per_pct"], 2.108, places=2)

    def test_rejects_degenerate(self):
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "labdose.py"), "--dose", "1", "2", "3", "4", "--n", "10", "--deaths", "0", "0", "10", "10"], capture_output=True, text=True, encoding="utf8")
        self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
