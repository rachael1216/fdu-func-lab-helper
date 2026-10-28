import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MD = ROOT / "examples" / "sample-report" / "report.md"


@unittest.skipUnless(shutil.which("pandoc"), "pandoc not installed")
class BuildTests(unittest.TestCase):
    def test_docx_has_cover_and_header(self):
        with tempfile.TemporaryDirectory() as td:
            subprocess.run([sys.executable, str(ROOT / "tools" / "build.py"), str(MD), "-o", td], check=True)
            f = Path(td) / "report.docx"
            self.assertTrue(f.exists())
            z = zipfile.ZipFile(f)
            names = z.namelist()
            self.assertTrue(any(n.startswith("word/media/") for n in names))
            xml = z.read("word/document.xml").decode("utf8")
            self.assertIn("LABORATORY REPORT", xml)
            self.assertIn("示例同学", xml)
            hdr = "".join(z.read(n).decode("utf8") for n in names if n.startswith("word/header"))
            self.assertNotIn("{{HEADER}}", hdr)

    def test_tex_generated(self):
        with tempfile.TemporaryDirectory() as td:
            subprocess.run([sys.executable, str(ROOT / "tools" / "build.py"), str(MD), "--to", "tex", "-o", td], check=True)
            t = (Path(td) / "report.tex").read_text(encoding="utf8")
            self.assertIn("\\fducover", t)
            self.assertIn("\\textsuperscript{+}", t)
            self.assertTrue((Path(td) / "fdureport.cls").exists())
            self.assertTrue((Path(td) / "cover.jpg").exists())


if __name__ == "__main__":
    unittest.main()
