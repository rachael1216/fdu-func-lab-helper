#!/usr/bin/env python3
"""labcalc.py — 功能学科实验常用计算（纯 Python，零依赖）

设计原则：**数字由代码算，不由大模型算**。
大语言模型做多步算术、有效数字、对数运算时很容易出错；写进报告的每个计算结果
都应来自本文件（或你自己的 Excel/计算器），并在报告里写清"代入的数值"。

命令行用法（也可以 `import labcalc` 在 Python 里调用）：

  python tools/labcalc.py dose  --weight 2.4 --dose 75 --conc 5            # 给药体积
  python tools/labcalc.py conc  --reading 1.70 --dilution 2                # 稀释倍数还原
  python tools/labcalc.py ld50  --doses 110.8 147.7 196.9 262.5 350 \\
                                --n 28 --deaths 0 9 22 23 27               # 改良寇氏法
  python tools/labcalc.py ache  --od-test 0.492 --od-blank 0.312 \\
                                --od-std 0.324 --od-std-blank 0.060 --dilution 100
  python tools/labcalc.py lung  --lung-g 12.8 --weight 2.4                 # 肺系数
  python tools/labcalc.py stats 3.4 4.1 5.5                                # 均值/SD/SEM
  python tools/labcalc.py change --before 605 --after 1630                 # 变化百分比
  python tools/labcalc.py map   --sbp 110 --dbp 70                         # 平均动脉压
  python tools/labcalc.py hr    --rr 0.25                                  # RR 间期 → 心率
  python tools/labcalc.py halflife --t 0.5 1 2 4 --c 80 62 38 15           # 一级动力学半衰期
  python tools/labcalc.py ti    --ld50 175.8 --ed50 40                     # 治疗指数
  python tools/labcalc.py hrv   --rr 812 790 805 830 ...                   # SDNN/RMSSD/pNN50
  python tools/labcalc.py fisher -a 2 -b 1 -c 0 -d 3                       # 小样本率比较（转复率等）

加 --json 输出机器可读结果。
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from typing import Dict, List, Sequence


# ------------------------------------------------------------------ 基础
def sig(x: float, n: int = 4) -> float:
    """保留 n 位有效数字。"""
    if x == 0 or not math.isfinite(x):
        return x
    return round(x, n - 1 - int(math.floor(math.log10(abs(x)))))


def dose_volume(weight_kg: float, dose_mg_per_kg: float, conc_percent: float) -> Dict[str, float]:
    """按体重算给药体积。浓度以 % (g/100 mL) 表示，1% = 10 mg/mL。

    例：2.4 kg 家兔，75 mg/kg 敌百虫，浓度 5% → 总剂量 180 mg，体积 3.6 mL。
    """
    total_mg = weight_kg * dose_mg_per_kg
    mg_per_ml = conc_percent * 10.0
    return {"total_mg": sig(total_mg), "mg_per_ml": mg_per_ml, "volume_ml": sig(total_mg / mg_per_ml)}


def dose_from_volume(weight_kg: float, volume_ml: float, conc_percent: float) -> Dict[str, float]:
    """已知实际注射体积，反推 mg/kg（核对是否与教材一致）。"""
    total_mg = volume_ml * conc_percent * 10.0
    return {"total_mg": sig(total_mg), "dose_mg_per_kg": sig(total_mg / weight_kg)}


def dilution_correct(reading: float, factor: float) -> float:
    """仪器读数 × 稀释倍数 = 原液浓度（如血清 K⁺ 稀释 2 倍测得 1.70 → 3.40 mmol/L）。"""
    return sig(reading * factor)


def percent_change(before: float, after: float) -> Dict[str, float]:
    if before == 0:
        raise ValueError("基线为 0，无法计算百分比变化")
    return {"abs_change": sig(after - before), "percent": sig((after - before) / abs(before) * 100)}


def describe(values: Sequence[float]) -> Dict[str, float]:
    v = list(values)
    n = len(v)
    out = {"n": n, "mean": sig(statistics.fmean(v))}
    if n >= 2:
        sd = statistics.stdev(v)
        out.update({"sd": sig(sd), "sem": sig(sd / math.sqrt(n))})
    out.update({"min": min(v), "max": max(v)})
    return out


# ------------------------------------------------------------------ LD50（改良寇氏法）
def koushi_ld50(doses: Sequence[float], n: int, deaths: Sequence[int]) -> Dict[str, object]:
    """改良寇氏法（教材 实验 8.1）。要求：各组动物数 n 相等，剂量按等比级数排列。

    LD50 = lg⁻¹[ Xm − I(Σp − 0.5) ]
    S(lg LD50) = I·sqrt( Σ p(1−p) / (n−1) )
    95% 可信限（教材近似式）= LD50 ± 4.5·S·LD50
    另给出对数尺度上的严格式：lg⁻¹(lg LD50 ± 1.96·S)

    Xm = 最大剂量的对数；I = 相邻两组剂量比值的对数；p = 各组死亡率（小数）。
    """
    if len(doses) != len(deaths):
        raise ValueError("doses 与 deaths 长度必须相同")
    order = sorted(range(len(doses)), key=lambda i: doses[i])
    d = [float(doses[i]) for i in order]
    k = [int(deaths[i]) for i in order]
    if any(x > n or x < 0 for x in k):
        raise ValueError("死亡数不能大于每组动物数或为负")
    if len(d) < 3:
        raise ValueError("至少需要 3 个剂量组")
    ratios = [d[i + 1] / d[i] for i in range(len(d) - 1)]
    I = math.log10(ratios[-1])
    warnings: List[str] = []
    if max(ratios) / min(ratios) > 1.02:
        warnings.append(f"剂量不是等比级数（相邻比 {min(ratios):.3f}–{max(ratios):.3f}），I 取最高两组之比，结果仅供参考")
    p = [x / n for x in k]
    if p[0] > 0:
        warnings.append("最低剂量组死亡率 > 0（理想应为 0%），改良寇氏法的前提不完全满足")
    if p[-1] < 1:
        warnings.append("最高剂量组死亡率 < 100%（理想应为 100%），改良寇氏法的前提不完全满足")
    if any(p[i] > p[i + 1] for i in range(len(p) - 1)):
        warnings.append("死亡率随剂量并非单调递增，提示剂量-反应关系异常或样本量不足")
    xm = math.log10(d[-1])
    sp = sum(p)
    log_ld50 = xm - I * (sp - 0.5)
    ld50 = 10 ** log_ld50
    s = I * math.sqrt(sum(x * (1 - x) for x in p) / (n - 1))
    ci_textbook = (ld50 - 4.5 * s * ld50, ld50 + 4.5 * s * ld50)
    ci_log = (10 ** (log_ld50 - 1.96 * s), 10 ** (log_ld50 + 1.96 * s))
    return {
        "doses": d, "n_per_group": n, "deaths": k, "p": [round(x, 3) for x in p],
        "Xm": round(xm, 4), "I": round(I, 4), "sum_p": round(sp, 4),
        "LD50": sig(ld50, 4), "S_logLD50": round(s, 5),
        "CI95_textbook": [sig(ci_textbook[0], 4), sig(ci_textbook[1], 4)],
        "CI95_log": [sig(ci_log[0], 4), sig(ci_log[1], 4)],
        "warnings": warnings,
        "formula": "LD50 = lg⁻¹[Xm − I(Σp − 0.5)]；S = I·√(Σp(1−p)/(n−1))；95%CI = LD50 ± 4.5·S·LD50",
    }


def therapeutic_index(ld50: float, ed50: float) -> Dict[str, float]:
    """治疗指数 TI = LD50/ED50（越大越安全；注意量效曲线不平行时 TI 会失真，此时看安全范围 LD5/ED95）。"""
    return {"TI": sig(ld50 / ed50)}


# ------------------------------------------------------------------ 其它实验用到的公式
def ache_activity(od_test: float, od_blank: float, od_std: float, od_std_blank: float,
                  std_conc: float = 1.0, dilution: float = 100.0) -> Dict[str, float]:
    """胆碱酯酶活力（教材 实验 1.5）：
    (OD测定 − OD测定空白)/(OD标准 − OD标准空白) × 标准管浓度 × 样本稀释倍数。
    教材例：0.492, 0.312, 0.324, 0.060, 1, 100 → 68.18。"""
    val = (od_test - od_blank) / (od_std - od_std_blank) * std_conc * dilution
    return {"ache_activity": sig(val, 4)}


def lung_coefficient(lung_g: float, weight_kg: float) -> Dict[str, object]:
    """肺系数 = 肺重(g)/体重(kg)，教材给出的正常值约 4–5（实验 3.3）。"""
    v = lung_g / weight_kg
    return {"lung_coefficient": sig(v, 3), "interpretation": "高于正常范围，提示肺水肿" if v > 5 else "在/低于教材正常范围上限内"}


def mean_arterial_pressure(sbp: float, dbp: float) -> Dict[str, float]:
    return {"MAP": sig(dbp + (sbp - dbp) / 3, 4), "pulse_pressure": sig(sbp - dbp, 4)}


def heart_rate_from_rr(rr_s: float) -> Dict[str, float]:
    """RR 间期（秒）→ 心率（次/分）。"""
    return {"HR_bpm": sig(60.0 / rr_s, 4)}


def half_life_first_order(t: Sequence[float], c: Sequence[float]) -> Dict[str, float]:
    """一级动力学：对 ln C ~ t 做最小二乘直线回归，k = −斜率，t½ = ln2/k（实验 8.2）。"""
    if len(t) != len(c) or len(t) < 3:
        raise ValueError("至少 3 个时间点，且 t 与 c 等长")
    y = [math.log(x) for x in c]
    n = len(t)
    mt, my = sum(t) / n, sum(y) / n
    sxx = sum((a - mt) ** 2 for a in t)
    sxy = sum((a - mt) * (b - my) for a, b in zip(t, y))
    slope = sxy / sxx
    icpt = my - slope * mt
    ss_tot = sum((b - my) ** 2 for b in y)
    ss_res = sum((b - (icpt + slope * a)) ** 2 for a, b in zip(t, y))
    r2 = 1 - ss_res / ss_tot if ss_tot else 1.0
    k = -slope
    if k <= 0:
        raise ValueError("斜率 ≥ 0：浓度没有随时间下降，无法按消除相计算半衰期")
    return {"k": sig(k), "t_half": sig(math.log(2) / k), "C0_extrapolated": sig(math.exp(icpt)), "R2": round(r2, 4)}


def hrv_time_domain(rr_ms: Sequence[float]) -> Dict[str, float]:
    """HRV 时域指标（实验 7.3）：SDNN、RMSSD、pNN50、平均心率。输入为相邻 RR 间期（毫秒）。"""
    if len(rr_ms) < 3:
        raise ValueError("至少需要 3 个 RR 间期")
    diffs = [rr_ms[i + 1] - rr_ms[i] for i in range(len(rr_ms) - 1)]
    return {
        "mean_RR_ms": sig(statistics.fmean(rr_ms)),
        "mean_HR_bpm": sig(60000 / statistics.fmean(rr_ms)),
        "SDNN_ms": sig(statistics.stdev(rr_ms)),
        "RMSSD_ms": sig(math.sqrt(statistics.fmean([d * d for d in diffs]))),
        "pNN50_percent": sig(100 * sum(1 for d in diffs if abs(d) > 50) / len(diffs)),
    }


def fisher_exact_2x2(a: int, b: int, c: int, d: int) -> Dict[str, float]:
    """Fisher 精确检验（双侧），用于小样本率的比较。表格：
                 事件   无事件
        组 1       a       b          例：治疗组 转复 a / 未转复 b
        组 2       c       d              对照组 转复 c / 未转复 d
    样本只有 3 vs 3 时，几乎不可能得到 P<0.05——**这本身就是讨论的内容**（统计效力不足）。"""
    r1, r2, c1, n = a + b, c + d, a + c, a + b + c + d
    if min(a, b, c, d) < 0 or n == 0:
        raise ValueError("频数必须为非负整数且不全为 0")

    def pmf(x):
        return math.comb(r1, x) * math.comb(r2, c1 - x) / math.comb(n, c1)

    lo, hi = max(0, c1 - r2), min(r1, c1)
    p_obs = pmf(a)
    p = sum(pmf(x) for x in range(lo, hi + 1) if pmf(x) <= p_obs + 1e-12)
    return {"p_two_sided": round(min(1.0, p), 4)}


# ------------------------------------------------------------------ CLI
def _emit(res, as_json: bool):
    if as_json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return
    if not isinstance(res, dict):
        print(res)
        return
    for k, v in res.items():
        print(f"{k}: {v}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="功能学科实验常用计算", formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__)
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    sp = ap.add_subparsers(dest="cmd", required=True)

    a = sp.add_parser("dose", help="给药体积")
    a.add_argument("--weight", type=float, required=True, help="体重 kg")
    a.add_argument("--dose", type=float, required=True, help="剂量 mg/kg")
    a.add_argument("--conc", type=float, required=True, help="溶液浓度 %%")
    a.set_defaults(fn=lambda x: dose_volume(x.weight, x.dose, x.conc))

    a = sp.add_parser("backdose", help="由实际注射体积反推 mg/kg")
    a.add_argument("--weight", type=float, required=True)
    a.add_argument("--volume", type=float, required=True, help="mL")
    a.add_argument("--conc", type=float, required=True, help="%%")
    a.set_defaults(fn=lambda x: dose_from_volume(x.weight, x.volume, x.conc))

    a = sp.add_parser("conc", help="稀释倍数还原")
    a.add_argument("--reading", type=float, required=True)
    a.add_argument("--dilution", type=float, required=True)
    a.set_defaults(fn=lambda x: {"original": dilution_correct(x.reading, x.dilution)})

    a = sp.add_parser("ld50", help="改良寇氏法 LD50")
    a.add_argument("--doses", type=float, nargs="+", required=True)
    a.add_argument("--n", type=int, required=True, help="每组动物数")
    a.add_argument("--deaths", type=int, nargs="+", required=True)
    a.set_defaults(fn=lambda x: koushi_ld50(x.doses, x.n, x.deaths))

    a = sp.add_parser("ti", help="治疗指数")
    a.add_argument("--ld50", type=float, required=True)
    a.add_argument("--ed50", type=float, required=True)
    a.set_defaults(fn=lambda x: therapeutic_index(x.ld50, x.ed50))

    a = sp.add_parser("ache", help="胆碱酯酶活力")
    a.add_argument("--od-test", type=float, required=True)
    a.add_argument("--od-blank", type=float, required=True)
    a.add_argument("--od-std", type=float, required=True)
    a.add_argument("--od-std-blank", type=float, required=True)
    a.add_argument("--std-conc", type=float, default=1.0)
    a.add_argument("--dilution", type=float, default=100.0)
    a.set_defaults(fn=lambda x: ache_activity(x.od_test, x.od_blank, x.od_std, x.od_std_blank, x.std_conc, x.dilution))

    a = sp.add_parser("lung", help="肺系数")
    a.add_argument("--lung-g", type=float, required=True)
    a.add_argument("--weight", type=float, required=True)
    a.set_defaults(fn=lambda x: lung_coefficient(x.lung_g, x.weight))

    a = sp.add_parser("stats", help="均值/SD/SEM")
    a.add_argument("values", type=float, nargs="+")
    a.set_defaults(fn=lambda x: describe(x.values))

    a = sp.add_parser("change", help="变化百分比")
    a.add_argument("--before", type=float, required=True)
    a.add_argument("--after", type=float, required=True)
    a.set_defaults(fn=lambda x: percent_change(x.before, x.after))

    a = sp.add_parser("map", help="平均动脉压")
    a.add_argument("--sbp", type=float, required=True)
    a.add_argument("--dbp", type=float, required=True)
    a.set_defaults(fn=lambda x: mean_arterial_pressure(x.sbp, x.dbp))

    a = sp.add_parser("hr", help="RR 间期→心率")
    a.add_argument("--rr", type=float, required=True, help="秒")
    a.set_defaults(fn=lambda x: heart_rate_from_rr(x.rr))

    a = sp.add_parser("halflife", help="一级动力学半衰期")
    a.add_argument("--t", type=float, nargs="+", required=True)
    a.add_argument("--c", type=float, nargs="+", required=True)
    a.set_defaults(fn=lambda x: half_life_first_order(x.t, x.c))

    a = sp.add_parser("fisher", help="Fisher 精确检验 2x2")
    for k in "abcd":
        a.add_argument(f"-{k}", type=int, required=True)
    a.set_defaults(fn=lambda x: fisher_exact_2x2(x.a, x.b, x.c, x.d))

    a = sp.add_parser("hrv", help="HRV 时域指标")
    a.add_argument("--rr", type=float, nargs="+", required=True, help="RR 间期 ms")
    a.set_defaults(fn=lambda x: hrv_time_domain(x.rr))

    args = ap.parse_args(argv)
    try:
        _emit(args.fn(args), args.json)
    except ValueError as e:
        sys.exit(f"输入有误：{e}")


if __name__ == "__main__":
    main()
