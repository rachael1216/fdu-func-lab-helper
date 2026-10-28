import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import refcheck  # noqa: E402

LANCET = {"title": ["Management of acute organophosphorus pesticide poisoning"], "DOI": "10.1016/s0140-6736(07)61202-1",
          "author": [{"family": "Eddleston", "given": "Michael"}, {"family": "Buckley", "given": "Nick A"}, {"family": "Eyer", "given": "Peter"}, {"family": "Dawson", "given": "A"}],
          "container-title": ["The Lancet"], "volume": "371", "issue": "9612", "page": "597-607", "issued": {"date-parts": [[2008]]}}
GOOD = "EDDLESTON M, BUCKLEY N A, EYER P, et al. Management of acute organophosphorus pesticide poisoning[J]. The Lancet, 2008, 371(9612): 597-607. DOI: 10.1016/S0140-6736(07)61202-1."


class RefCheckTests(unittest.TestCase):
    def run_check(self, ref, item):
        out = []
        with mock.patch.object(refcheck, "crossref_by_doi", return_value=item):
            bad = refcheck.check_refs([("1", ref)], out=out.append)
        return bad, "\n".join(out)

    def test_ok(self):
        bad, o = self.run_check(GOOD, LANCET)
        self.assertEqual(bad, 0)
        self.assertIn("OK", o)

    def test_wrong_year_and_pages(self):
        _, o = self.run_check(GOOD.replace("2008", "2009").replace("597-607", "100-110"), LANCET)
        self.assertIn("WARN", o)
        self.assertIn("年份不符", o)
        self.assertIn("页码不符", o)

    def test_wrong_title(self):
        _, o = self.run_check(GOOD.replace("Management of acute organophosphorus pesticide poisoning", "Treatment of snake bite envenoming"), LANCET)
        self.assertIn("题名不符", o)

    def test_missing_doi_is_fail(self):
        bad, o = self.run_check(GOOD, None)
        self.assertEqual(bad, 1)
        self.assertIn("FAIL", o)

    def test_chinese_book_manual(self):
        out = []
        refcheck.check_refs([("1", "严钰锋，马淑兰．功能学科实验教程[M]．2020．")], out=out.append)
        self.assertIn("人工核对", out[0])

    def test_parse_refs_section(self):
        md = "# 讨论\n正文 [1]\n\n# 参考文献 {.unnumbered}\n\n[1] AAA. t[J]. J, 2000.\n[2] BBB. u[J]. K, 2001.\n"
        self.assertEqual([n for n, _ in refcheck.parse_refs(md)], ["1", "2"])

    def test_format_gbt(self):
        s = refcheck.format_gbt(LANCET)
        self.assertTrue(s.startswith("EDDLESTON M, BUCKLEY N A, EYER P, et al."))
        self.assertIn("The Lancet, 2008, 371(9612): 597-607", s)

    def test_registry_offline_ok(self):
        out = []
        refcheck.check_refs([("1", GOOD)], offline=True, out=out.append)
        self.assertIn("OK", out[0])


if __name__ == "__main__":
    unittest.main()
