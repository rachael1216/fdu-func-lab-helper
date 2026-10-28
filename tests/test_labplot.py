import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class PlotTests(unittest.TestCase):
    def test_line_and_dose(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            (td / "a.csv").write_text("t,g,v\n0,a,1\n0,a,2\n1,a,3\n1,a,4\n0,b,1\n0,b,1.5\n1,b,2\n1,b,2.5\n", encoding="utf8")
            (td / "d.csv").write_text("dose,n,k\n100,10,0\n150,10,2\n200,10,5\n260,10,9\n", encoding="utf8")
            for args, out in ((["line", str(td / "a.csv"), "--x", "t", "--y", "v", "--group", "g"], "l.png"),
                              (["bar", str(td / "a.csv"), "--x", "g", "--y", "v", "--points"], "b.png"),
                              (["dose", str(td / "d.csv"), "--dose", "dose", "--n", "n", "--deaths", "k"], "d.png")):
                r = subprocess.run([sys.executable, str(ROOT / "tools" / "labplot.py"), *args, "-o", str(td / out)], capture_output=True, text=True, encoding="utf8")
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertTrue((td / out).stat().st_size > 2000)
                self.assertIn("建议图注", r.stdout)


if __name__ == "__main__":
    unittest.main()
