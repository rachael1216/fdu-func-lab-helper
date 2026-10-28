#!/usr/bin/env python3
"""labplot.py — 按报告作图规范，从 CSV 画图（matplotlib）。

规范（详见 docs/FORMAT.md §5）：坐标轴写“量（单位）”；刻度朝内；去掉上、右边框；字号 ≥ 8 pt；
误差线说明写在图注；色盲友好配色 + 不同标记/线型（黑白打印仍可区分）；图题写在图下（放进 Word/LaTeX 的题注，不画在图里）；
默认 12 × 8 cm、300 dpi，可存 png / pdf / svg。

用法：
  python tools/labplot.py line  data.csv --x 时间 --y 数值 --group 组别 --xlabel "时间（min）" --ylabel "心率（次/min）" -o fig1.png
  python tools/labplot.py bar   data.csv --x 组别 --y 数值 --ylabel "血清钾（mmol/L）" --points -o fig2.png
  python tools/labplot.py dose  data.csv --dose 剂量 --n 每组数 --deaths 死亡数 -o fig3.png       # S 形曲线 + 概率单位直线
  python tools/labplot.py scatter data.csv --x 浓度 --y 吸光度 --fit -o fig4.png
  python tools/labplot.py line  data.csv … --err sem        # 误差线：sd（默认）| sem | none
CSV 为“长表”：每行一个观测，列名自定。UTF-8 编码；Excel 另存为“CSV UTF-8”。
输出时会打印一句建议图注（含 n 和误差线含义），直接粘到题注里改写即可。
"""
from __future__ import annotations

import argparse
import csv
import math
import statistics as st
import sys
from collections import OrderedDict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

OKABE_ITO = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#000000"]
MARKERS = ["o", "s", "^", "D", "v", "P", "X"]
STYLES = ["-", "--", "-.", ":", "-", "--", "-."]
SERIF = ["Times New Roman", "Liberation Serif", "DejaVu Serif"]
CJK = ["SimSun", "Songti SC", "STSong", "Noto Serif CJK SC", "Noto Serif SC", "Source Han Serif SC", "FangSong", "Noto Sans CJK SC",
       "Microsoft YaHei", "PingFang SC", "WenQuanYi Zen Hei", "SimHei"]


def setup(figsize=(12, 8), size=10):
    avail = {f.name for f in font_manager.fontManager.ttflist}
    cjk = [f for f in CJK if f in avail]
    plt.rcParams.update({
        "font.family": [f for f in SERIF if f in avail][:1] + cjk,
        "axes.unicode_minus": False,
        "font.size": size, "axes.labelsize": size, "xtick.labelsize": size - 1, "ytick.labelsize": size - 1, "legend.fontsize": size - 1,
        "axes.spines.top": False, "axes.spines.right": False,
        "xtick.direction": "in", "ytick.direction": "in",
        "axes.linewidth": 0.8, "lines.linewidth": 1.4, "lines.markersize": 5,
        "figure.figsize": (figsize[0] / 2.54, figsize[1] / 2.54), "savefig.dpi": 300,
    })
    if not cjk:
        print("! 未找到中文字体，图中中文可能显示为方框。请安装宋体/思源宋体。", file=sys.stderr)


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def num(x):
    return float(str(x).strip())


def summarize(vals, err):
    m = sum(vals) / len(vals)
    if len(vals) < 2 or err == "none":
        return m, 0.0
    sd = st.stdev(vals)
    return m, (sd / math.sqrt(len(vals)) if err == "sem" else sd)


def finish(fig, ax, a, caption):
    if a.xlabel:
        ax.set_xlabel(a.xlabel)
    if a.ylabel:
        ax.set_ylabel(a.ylabel)
    if ax.get_legend_handles_labels()[0] and not a.no_legend:
        ax.legend(frameon=False)
    fig.tight_layout()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    print(f"✓ {out}")
    print("建议图注（请按实际改写）：" + caption)


def cap_err(err, n_note):
    meaning = {"sd": "误差线为标准差（SD）", "sem": "误差线为标准误（SEM）", "none": "未绘制误差线"}[err]
    return f"{n_note}；{meaning}。"


def plot_line(a):
    rows = read_csv(a.csv)
    groups: "OrderedDict[str, OrderedDict[float, list]]" = OrderedDict()
    for r in rows:
        g = r[a.group] if a.group else "全部"
        groups.setdefault(g, OrderedDict()).setdefault(num(r[a.x]), []).append(num(r[a.y]))
    fig, ax = plt.subplots()
    ns = set()
    for i, (g, d) in enumerate(groups.items()):
        xs = sorted(d)
        ms = [summarize(d[x], a.err) for x in xs]
        ns |= {len(d[x]) for x in xs}
        ax.errorbar(xs, [m for m, _ in ms], yerr=[e for _, e in ms] if a.err != "none" else None, color=OKABE_ITO[i % 7], marker=MARKERS[i % 7],
                    linestyle=STYLES[i % 7], capsize=3, label=g if a.group else None, markerfacecolor="white" if i % 2 else OKABE_ITO[i % 7])
    n_note = f"每个时间点 n = {min(ns)}" if len(ns) == 1 else f"每个时间点 n = {min(ns)}–{max(ns)}"
    finish(fig, ax, a, cap_err(a.err, n_note))


def plot_bar(a):
    rows = read_csv(a.csv)
    groups: "OrderedDict[str, list]" = OrderedDict()
    for r in rows:
        groups.setdefault(r[a.x], []).append(num(r[a.y]))
    fig, ax = plt.subplots()
    names = list(groups)
    for i, g in enumerate(names):
        m, e = summarize(groups[g], a.err)
        ax.bar(i, m, yerr=e if a.err != "none" else None, capsize=4, color="white", edgecolor=OKABE_ITO[i % 7], linewidth=1.2,
               hatch=["", "//", "..", "xx", "\\\\", "--"][i % 6], width=0.6)
        if a.points:
            ax.scatter([i + (k - (len(groups[g]) - 1) / 2) * 0.06 for k in range(len(groups[g]))], groups[g], color=OKABE_ITO[i % 7], s=14, zorder=3)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names)
    ns = {len(v) for v in groups.values()}
    finish(fig, ax, a, cap_err(a.err, "每组 n = " + (str(min(ns)) if len(ns) == 1 else "、".join(f"{k}:{len(v)}" for k, v in groups.items()))))


def probit(p):
    from statistics import NormalDist
    return NormalDist().inv_cdf(p) + 5


def plot_dose(a):
    rows = read_csv(a.csv)
    d = [num(r[a.dose]) for r in rows]
    n = [num(r[a.n]) for r in rows]
    k = [num(r[a.deaths]) for r in rows]
    p = [ki / ni for ki, ni in zip(k, n)]
    lx = [math.log10(x) for x in d]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(plt.rcParams["figure.figsize"][0] * 1.6, plt.rcParams["figure.figsize"][1]))
    ax1.plot(lx, [x * 100 for x in p], "o-", color=OKABE_ITO[0])
    ax1.axhline(50, color="0.6", lw=0.8, ls="--")
    ax1.set_xlabel("剂量对数（lg mg/kg）")
    ax1.set_ylabel("死亡率（%）")
    mid = [(x, y) for x, y in zip(lx, p) if 0 < y < 1]
    if len(mid) >= 2:
        py = [probit(y) for _, y in mid]
        px = [x for x, _ in mid]
        mx, my = sum(px) / len(px), sum(py) / len(py)
        b = sum((x - mx) * (y - my) for x, y in zip(px, py)) / sum((x - mx) ** 2 for x in px)
        c = my - b * mx
        ax2.plot(px, py, "s", color=OKABE_ITO[1])
        xs = [min(px) - 0.05, max(px) + 0.05]
        ax2.plot(xs, [c + b * x for x in xs], "-", color=OKABE_ITO[1])
        ax2.axhline(5, color="0.6", lw=0.8, ls="--")
        lg50 = (5 - c) / b
        ax2.set_xlabel("剂量对数（lg mg/kg）")
        ax2.set_ylabel("概率单位")
        print(f"概率单位回归估计 LD50 ≈ {10 ** lg50:.1f}（仅作作图参考；正式计算用 labcalc.py ld50）")
    fig.tight_layout()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    print(f"✓ {out}")
    print("建议图注（请按实际改写）：（A）剂量对数-死亡率曲线；（B）概率单位与剂量对数的关系；虚线分别示死亡率 50% 与概率单位 5。各剂量组 n = " + str(int(min(n))) + "。")


def plot_scatter(a):
    rows = read_csv(a.csv)
    x = [num(r[a.x]) for r in rows]
    y = [num(r[a.y]) for r in rows]
    fig, ax = plt.subplots()
    ax.scatter(x, y, color=OKABE_ITO[0], s=22, zorder=3)
    note = f"n = {len(x)}"
    if a.fit and len(x) >= 3:
        mx, my = sum(x) / len(x), sum(y) / len(y)
        b = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / sum((xi - mx) ** 2 for xi in x)
        c = my - b * mx
        ss_res = sum((yi - (c + b * xi)) ** 2 for xi, yi in zip(x, y))
        ss_tot = sum((yi - my) ** 2 for yi in y)
        r2 = 1 - ss_res / ss_tot if ss_tot else float("nan")
        xs = [min(x), max(x)]
        ax.plot(xs, [c + b * v for v in xs], color=OKABE_ITO[1], ls="--")
        note += f"；虚线为最小二乘直线 y = {b:.4g}x + {c:.4g}，R² = {r2:.3f}"
    finish(fig, ax, a, note + "。")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="kind", required=True)

    def common(s):
        s.add_argument("csv")
        s.add_argument("-o", "--out", required=True, help="输出文件，后缀决定格式：.png/.pdf/.svg")
        s.add_argument("--xlabel")
        s.add_argument("--ylabel")
        s.add_argument("--err", choices=["sd", "sem", "none"], default="sd")
        s.add_argument("--size", default="12x8", help="宽x高（cm），默认 12x8")
        s.add_argument("--no-legend", action="store_true")
    s = sp.add_parser("line"); common(s); s.add_argument("--x", required=True); s.add_argument("--y", required=True); s.add_argument("--group")
    s = sp.add_parser("bar"); common(s); s.add_argument("--x", required=True); s.add_argument("--y", required=True); s.add_argument("--points", action="store_true")
    s = sp.add_parser("dose"); common(s); s.add_argument("--dose", required=True); s.add_argument("--n", required=True); s.add_argument("--deaths", required=True)
    s = sp.add_parser("scatter"); common(s); s.add_argument("--x", required=True); s.add_argument("--y", required=True); s.add_argument("--fit", action="store_true")
    a = ap.parse_args()
    w, h = (float(v) for v in a.size.lower().split("x"))
    setup((w, h))
    {"line": plot_line, "bar": plot_bar, "dose": plot_dose, "scatter": plot_scatter}[a.kind](a)


if __name__ == "__main__":
    main()
