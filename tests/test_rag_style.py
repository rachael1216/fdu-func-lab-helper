import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable


class RagStyleTests(unittest.TestCase):
    def test_rag_literature(self):
        subprocess.run([PY, str(ROOT / "tools" / "rag.py"), "build"], check=True, capture_output=True)
        r = subprocess.run([PY, str(ROOT / "tools" / "rag.py"), "search", "有机磷", "复能剂", "-c", "literature", "-k", "3"], capture_output=True, text=True, encoding="utf8")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Eddleston", r.stdout)

    def test_stylecheck_flags_template_tone(self):
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "r.md"
            f.write_text("# 讨论\n\n值得注意的是，血钾升高挺明显。\n", encoding="utf8")
            r = subprocess.run([PY, str(ROOT / "tools" / "stylecheck.py"), str(f), "--exp", "2.7"], capture_output=True, text=True, encoding="utf8")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("值得注意的是", r.stdout)
            self.assertIn("挺", r.stdout)

    def test_styleprofile(self):
        subprocess.run([PY, str(ROOT / "tools" / "styleprofile.py"), "build"], check=True, capture_output=True)
        r = subprocess.run([PY, str(ROOT / "tools" / "styleprofile.py"), "compare", str(ROOT / "examples" / "sample-report" / "report.md"), "--exp", "8.1"], capture_output=True, text=True, encoding="utf8")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("句长", r.stdout)

    def test_terms_split(self):
        sys.path.insert(0, str(ROOT / "tools"))
        import stylecheck
        terms = stylecheck.load_terms("8.1")
        self.assertIn("腹腔注射", terms)
        self.assertIn("盐酸普鲁卡因", terms)


if __name__ == "__main__":
    unittest.main()
