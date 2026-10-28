#!/usr/bin/env python3
"""labstats.py — 实验数据的常规统计分析（需要 scipy）。

  python tools/labstats.py describe 120 118 125 130
  python tools/labstats.py normality 1.2 1.4 1.1 1.5 1.3
  python tools/labstats.py ttest --a 5.1 4.8 5.5 --b 6.2 6.0 6.8            # 独立样本（默认 Welch）
  python tools/labstats.py ttest --a 80 82 85 --b 90 94 99 --paired        # 配对
  python tools/labstats.py anova --g 对照=1,2,3 --g 低=2,3,4 --g 高=5,6,7   # 单因素方差分析 + Tukey
  python tools/labstats.py mannwhitney --a 1 2 3 --b 4 5 6
  python tools/labstats.py corr --x 1 2 3 4 5 --y 2.1 3.9 6.2 7.8 10.1
  python tools/labstats.py linreg --x 1 2 3 4 5 --y 2.1 3.9 6.2 7.8 10.1
  python tools/labstats.py advise --groups 2 --n 5                          # 方法选择建议
  加 --json 输出机器可读结果。

约定：显著性水平 α = 0.05（双侧）；n < 3 不做检验；n ≤ 5 时正态性检验几乎没有检验力——
工具会提示。统计只回答“差异是否可能由随机波动造成”，不回答“机制是什么”。
"""
from __future__ import annotations

import argparse
import json
import math
import statistics as st
import sys


def need_scipy():
    try:
        import scipy.stats as ss  # noqa: F401
        return ss
    except ImportError:
        sys.exit("需要 scipy：pip install scipy")


def p_text(p: float) -> str:
    return "P < 0.001" if p < 0.001 else f"P = {p:.3f}"


def describe(v):
    n = len(v)
    if n == 0:
        raise ValueError("没有数据")
    mean = sum(v) / n
    sd = st.stdev(v) if n > 1 else float("nan")
    sem = sd / math.sqrt(n) if n > 1 else float("nan")
    out = dict(n=n, mean=mean, sd=sd, sem=sem, median=st.median(v), min=min(v), max=max(v))
    if n > 2:
        ss = need_scipy()
        h = ss.t.ppf(0.975, n - 1) * sem
        out["ci95"] = (mean - h, mean + h)
    out["text"] = f"{mean:.2f} ± {sd:.2f}（n = {n}）" if n > 1 else f"{mean:.2f}（n = 1，无法计算标准差）"
    return out


def normality(v):
    ss = need_scipy()
    if len(v) < 3:
        return dict(n=len(v), note="n < 3，无法做正态性检验")
    w, p = ss.shapiro(v)
    note = "n ≤ 5 时 Shapiro-Wilk 检验力很低，‘不显著’不能证明正态" if len(v) <= 5 else ""
    return dict(n=len(v), W=w, p=p, normal=p >= 0.05, note=note)


def ttest(a, b, paired=False, equal_var=False):
    ss = need_scipy()
    if min(len(a), len(b)) < 2:
        return dict(error="每组至少需要 2 个数据")
    if paired:
        if len(a) != len(b):
            return dict(error="配对检验要求两组等长")
        r = ss.ttest_rel(a, b)
        d = [x - y for x, y in zip(a, b)]
        sd = st.stdev(d)
        dz = (sum(d) / len(d)) / sd if sd else float("nan")
        df = len(a) - 1
        diff = sum(d) / len(d)
        se = sd / math.sqrt(len(d))
        name = "配对 t 检验"
    else:
        r = ss.ttest_ind(a, b, equal_var=equal_var)
        df = float(r.df) if hasattr(r, "df") else len(a) + len(b) - 2
        diff = sum(a) / len(a) - sum(b) / len(b)
        va, vb = st.variance(a), st.variance(b)
        se = math.sqrt(va / len(a) + vb / len(b))
        sp = math.sqrt(((len(a) - 1) * va + (len(b) - 1) * vb) / (len(a) + len(b) - 2))
        dz = diff / sp if sp else float("nan")
        name = "独立样本 t 检验（等方差）" if equal_var else "独立样本 t 检验（Welch，不假定方差齐）"
    h = ss.t.ppf(0.975, df) * se
    t, p = float(r.statistic), float(r.pvalue)
    return dict(test=name, t=t, df=df, p=p, mean_diff=diff, ci95_diff=(diff - h, diff + h), cohen_d=dz,
                text=f"t({df:.0f}) = {t:.2f}，{p_text(p)}" if float(df).is_integer() else f"t({df:.1f}) = {t:.2f}，{p_text(p)}", n=(len(a), len(b)))


def anova(groups: dict):
    ss = need_scipy()
    vals = list(groups.values())
    if len(vals) < 3:
        return dict(error="单因素方差分析至少 3 组；两组请用 t 检验")
    if min(len(v) for v in vals) < 2:
        return dict(error="每组至少 2 个数据")
    f, p = ss.f_oneway(*vals)
    dfb, dfw = len(vals) - 1, sum(len(v) for v in vals) - len(vals)
    out = dict(test="单因素方差分析", F=float(f), df=(dfb, dfw), p=float(p), text=f"F({dfb}, {dfw}) = {f:.2f}，{p_text(p)}")
    if p < 0.05 and hasattr(ss, "tukey_hsd"):
        res = ss.tukey_hsd(*vals)
        names = list(groups)
        pairs = []
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                pairs.append((names[i], names[j], float(res.pvalue[i][j])))
        out["tukey"] = pairs
    return out


def mannwhitney(a, b):
    ss = need_scipy()
    r = ss.mannwhitneyu(a, b, alternative="two-sided")
    return dict(test="Mann-Whitney U 检验", U=float(r.statistic), p=float(r.pvalue), text=f"U = {r.statistic:.1f}，{p_text(r.pvalue)}",
                note="各组 n 很小时，该检验可达到的最小 P 值有下限（如 3 vs 3 时最小为 0.10），不显著不代表无差异")


def corr(x, y):
    ss = need_scipy()
    if len(x) != len(y) or len(x) < 3:
        return dict(error="x、y 需等长且 n ≥ 3")
    pr, pp = ss.pearsonr(x, y)
    sr, sp_ = ss.spearmanr(x, y)
    return dict(pearson_r=float(pr), pearson_p=float(pp), spearman_rho=float(sr), spearman_p=float(sp_),
                text=f"Pearson r = {pr:.3f}，{p_text(pp)}；Spearman ρ = {sr:.3f}，{p_text(sp_)}（n = {len(x)}）")


def linreg(x, y):
    ss = need_scipy()
    if len(x) != len(y) or len(x) < 3:
        return dict(error="x、y 需等长且 n ≥ 3")
    r = ss.linregress(x, y)
    return dict(slope=float(r.slope), intercept=float(r.intercept), r=float(r.rvalue), r2=float(r.rvalue ** 2), p=float(r.pvalue),
                stderr=float(r.stderr), text=f"y = {r.slope:.4g}x + {r.intercept:.4g}，R² = {r.rvalue ** 2:.3f}，{p_text(r.pvalue)}（n = {len(x)}）")


def advise(groups: int, n: int, paired: bool = False, normal: bool | None = None) -> list[str]:
    tips = []
    if n < 3:
        tips.append("每组 n < 3：只做描述（给出原始数据与变化量），不做假设检验。")
        return tips
    if groups == 1:
        tips.append("单组前后比较：用配对 t 检验（正态）或 Wilcoxon 符号秩检验（非正态/小样本）。")
    elif groups == 2:
        tips.append("两组：" + ("配对设计 → 配对 t 检验；非正态 → Wilcoxon 符号秩检验。" if paired else "独立设计 → Welch t 检验（默认）；非正态或有序资料 → Mann-Whitney U 检验。"))
    else:
        tips.append("三组及以上：单因素方差分析 + Tukey 事后比较；非正态 → Kruskal-Wallis 检验。重复测量同一动物 → 重复测量方差分析（本工具未实现，请在 SPSS/R 中完成）。")
    if n <= 5:
        tips.append("n ≤ 5：正态性无法可靠判断，优先给出个体数据点；结论用‘提示’而非‘证明’。")
    tips.append("时间序列（同一动物多个时间点）：不要对每个时间点分别做 t 检验后说‘显著’，应说明多重比较问题。")
    tips.append("率的比较（存活/死亡、转复/未转复）：Fisher 精确检验，见 labcalc.py fisher。")
    return tips


def fmt(d: dict) -> str:
    if "error" in d:
        return "错误：" + d["error"]
    lines = []
    for k, v in d.items():
        if k == "tukey":
            lines.append("Tukey 事后比较：")
            lines += [f"  {a} vs {b}：{p_text(p)}" for a, b, p in v]
        elif isinstance(v, float):
            lines.append(f"{k}: {v:.4g}")
        elif isinstance(v, tuple):
            lines.append(f"{k}: " + ", ".join(f"{x:.4g}" if isinstance(x, float) else str(x) for x in v))
        else:
            lines.append(f"{k}: {v}")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    sp = ap.add_subparsers(dest="cmd", required=True)
    for name in ("describe", "normality"):
        s = sp.add_parser(name)
        s.add_argument("values", nargs="+", type=float)
    for name in ("ttest", "mannwhitney"):
        s = sp.add_parser(name)
        s.add_argument("--a", nargs="+", type=float, required=True)
        s.add_argument("--b", nargs="+", type=float, required=True)
        if name == "ttest":
            s.add_argument("--paired", action="store_true")
            s.add_argument("--equal-var", action="store_true")
    s = sp.add_parser("anova")
    s.add_argument("--g", action="append", required=True, help="名称=数值,数值,… 可重复")
    for name in ("corr", "linreg"):
        s = sp.add_parser(name)
        s.add_argument("--x", nargs="+", type=float, required=True)
        s.add_argument("--y", nargs="+", type=float, required=True)
    s = sp.add_parser("advise")
    s.add_argument("--groups", type=int, required=True)
    s.add_argument("--n", type=int, required=True, help="每组例数")
    s.add_argument("--paired", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "describe":
        r = describe(a.values)
    elif a.cmd == "normality":
        r = normality(a.values)
    elif a.cmd == "ttest":
        r = ttest(a.a, a.b, a.paired, a.equal_var)
    elif a.cmd == "mannwhitney":
        r = mannwhitney(a.a, a.b)
    elif a.cmd == "anova":
        g = {}
        for item in a.g:
            name, vals = item.split("=", 1)
            g[name] = [float(x) for x in vals.split(",")]
        r = anova(g)
    elif a.cmd == "corr":
        r = corr(a.x, a.y)
    elif a.cmd == "linreg":
        r = linreg(a.x, a.y)
    else:
        r = {"建议": advise(a.groups, a.n, a.paired)}
    if a.json:
        print(json.dumps(r, ensure_ascii=False, default=lambda o: list(o) if isinstance(o, tuple) else str(o)))
    elif a.cmd == "advise":
        print("\n".join("· " + t for t in r["建议"]))
    else:
        print(fmt(r))
    if isinstance(r, dict) and "error" in r:
        sys.exit(1)


if __name__ == "__main__":
    main()
