"""labcalc 单元测试：用教材例题和真实班级数据核对公式实现。  运行：python -m unittest discover tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import labcalc as L  # noqa: E402


class TestLabCalc(unittest.TestCase):
    def test_dose_volume(self):
        r = L.dose_volume(2.4, 75, 5)
        self.assertAlmostEqual(r["volume_ml"], 3.6, places=3)
        self.assertAlmostEqual(r["total_mg"], 180, places=3)

    def test_backdose(self):
        r = L.dose_from_volume(2.2, 4.4, 5)
        self.assertAlmostEqual(r["dose_mg_per_kg"], 100, places=3)

    def test_dilution(self):
        self.assertAlmostEqual(L.dilution_correct(1.70, 2), 3.40)
        self.assertAlmostEqual(L.dilution_correct(14.40, 10), 144.0)

    def test_ld50_class_data(self):
        # 全班汇总数据（每组 28 只）：LD50 ≈ 175.8 mg/kg，S ≈ 0.0181
        r = L.koushi_ld50([110.8, 147.7, 196.9, 262.5, 350], 28, [0, 9, 22, 23, 27])
        self.assertAlmostEqual(r["LD50"], 175.8, delta=0.3)
        self.assertAlmostEqual(r["S_logLD50"], 0.0181, delta=0.0003)
        lo, hi = r["CI95_textbook"]
        self.assertTrue(lo < 175.8 < hi)
        self.assertTrue(any("100%" in w for w in r["warnings"]))  # 最高剂量组死亡率 96.4%

    def test_ld50_order_independent(self):
        a = L.koushi_ld50([350, 110.8, 262.5, 147.7, 196.9], 28, [27, 0, 23, 9, 22])
        self.assertAlmostEqual(a["LD50"], 175.8, delta=0.3)

    def test_ache_textbook_example(self):
        r = L.ache_activity(0.492, 0.312, 0.324, 0.060, 1, 100)
        self.assertAlmostEqual(r["ache_activity"], 68.18, places=2)

    def test_lung(self):
        self.assertAlmostEqual(L.lung_coefficient(12, 2)["lung_coefficient"], 6.0)
        self.assertIn("肺水肿", L.lung_coefficient(12, 2)["interpretation"])

    def test_map(self):
        self.assertAlmostEqual(L.mean_arterial_pressure(120, 80)["MAP"], 93.33, places=1)

    def test_hr(self):
        self.assertAlmostEqual(L.heart_rate_from_rr(0.25)["HR_bpm"], 240)

    def test_percent_change(self):
        self.assertAlmostEqual(L.percent_change(605, 1630)["percent"], 169.4, places=1)

    def test_halflife(self):
        import math
        t = [0.5, 1, 2, 4, 6]
        c = [100 * math.exp(-0.3 * x) for x in t]
        r = L.half_life_first_order(t, c)
        self.assertAlmostEqual(r["k"], 0.3, places=3)
        self.assertAlmostEqual(r["t_half"], 2.31, places=2)
        with self.assertRaises(ValueError):
            L.half_life_first_order([1, 2, 3], [1, 2, 3])

    def test_hrv(self):
        r = L.hrv_time_domain([800, 850, 790, 900, 810])
        self.assertAlmostEqual(r["mean_RR_ms"], 830)
        self.assertGreater(r["RMSSD_ms"], 0)

    def test_fisher(self):
        # 经典 "品茶" 例：3/1 vs 1/3 → 双侧 p = 0.4857
        self.assertAlmostEqual(L.fisher_exact_2x2(3, 1, 1, 3)["p_two_sided"], 0.4857, places=3)
        # 3 vs 3 最极端的表 3/0 vs 0/3 → p = 0.1
        self.assertAlmostEqual(L.fisher_exact_2x2(3, 0, 0, 3)["p_two_sided"], 0.1, places=3)

    def test_describe(self):
        r = L.describe([3.4, 4.12, 5.54])
        self.assertEqual(r["n"], 3)
        self.assertAlmostEqual(r["mean"], 4.353, places=2)


if __name__ == "__main__":
    unittest.main()
