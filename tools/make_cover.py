#!/usr/bin/env python3
"""make_cover.py — 生成封面线稿插图（默认：家兔）。输出 assets/cover/rabbit.png / rabbit.pdf / rabbit_icon.png。

  python tools/make_cover.py            # 重新生成
  python tools/make_cover.py --animal mouse

封面刻意保持极简：线稿 + 学号 + 日期，不含校徽。想换成别的动物，改这里的画法即可。
"""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Ellipse, FancyBboxPatch

OUT = Path(__file__).resolve().parent.parent / "assets" / "cover"
FILL, EDGE, INNER = "#E8EEE9", "#5F7568", "#C9D6CD"


def rabbit(ax):
    kw = dict(fc=FILL, ec=EDGE, lw=1.8, joinstyle="round")
    ax.plot([18, 84], [4.6, 4.6], color="#D5DBD7", lw=1.0, zorder=0)
    ax.add_patch(Ellipse((68.6, 6.6), 11, 3.6, **kw, zorder=2))                            # 前爪
    ax.add_patch(FancyBboxPatch((60.5, 6.4), 6, 17, boxstyle="round,pad=0,rounding_size=3", **kw, zorder=2))  # 前腿
    ax.add_patch(Circle((19.5, 21), 3.8, **kw, zorder=1))                                 # 尾
    ax.add_patch(Ellipse((40, 20), 40, 22, **kw, zorder=3))                              # 身体
    ax.add_patch(Ellipse((34, 8.4), 15, 6, **kw, zorder=4))                              # 后足
    ax.add_patch(Ellipse((66, 46), 6.4, 18, angle=4, **kw, zorder=2))                    # 耳（后）
    ax.add_patch(Ellipse((66.8, 46), 2.2, 12.5, angle=4, fc=INNER, ec="none", zorder=2))
    ax.add_patch(Ellipse((76.5, 43.5), 6, 16.5, angle=-24, **kw, zorder=2))              # 耳（前）
    ax.add_patch(Ellipse((76.2, 43.5), 2, 11.5, angle=-24, fc=INNER, ec="none", zorder=2))
    ax.add_patch(Ellipse((70, 30), 18, 15, **kw, zorder=5))                              # 头
    ax.add_patch(Circle((75, 31.8), 0.85, fc=EDGE, ec="none", zorder=6))                 # 眼
    ax.add_patch(Circle((78.7, 29.4), 0.55, fc=EDGE, ec="none", zorder=6))               # 鼻
    for dy in (-0.2, -1.6):                                                               # 须
        ax.plot([78.9, 84], [29.2 + dy, 28.4 + dy * 2.2], color=EDGE, lw=0.9, zorder=6)
    ax.set_xlim(8, 92)
    ax.set_ylim(2, 58)


def mouse(ax):
    kw = dict(fc=FILL, ec=EDGE, lw=1.8, joinstyle="round")
    ax.plot([16, 90], [4.6, 4.6], color="#D5DBD7", lw=1.0, zorder=0)
    from matplotlib.patches import PathPatch
    from matplotlib.path import Path as P
    ax.add_patch(PathPatch(P([(24, 14), (10, 16), (6, 8), (14, 6)], [P.MOVETO, P.CURVE4, P.CURVE4, P.CURVE4]), fc="none", ec=EDGE, lw=1.8, zorder=1, capstyle="round"))  # 尾
    ax.add_patch(Ellipse((44, 17), 44, 22, **kw, zorder=3))
    ax.add_patch(Ellipse((38, 7.5), 15, 5.5, **kw, zorder=4))
    ax.add_patch(FancyBboxPatch((66, 5.8), 5.5, 13, boxstyle="round,pad=0,rounding_size=2.6", **kw, zorder=2))
    ax.add_patch(Ellipse((70.5, 6.2), 9, 3.2, **kw, zorder=2))
    ax.add_patch(Circle((70, 36), 7.4, **kw, zorder=2))                                   # 耳
    ax.add_patch(Circle((70, 36), 4.6, fc=INNER, ec="none", zorder=2))
    ax.add_patch(Ellipse((77, 26), 22, 15, angle=8, **kw, zorder=5))
    ax.add_patch(Circle((81.5, 28), 0.9, fc=EDGE, ec="none", zorder=6))
    ax.add_patch(Circle((88, 25.4), 0.8, fc=EDGE, ec="none", zorder=6))
    for dy in (0, -1.6):
        ax.plot([88, 94], [25.2 + dy, 25 + dy * 2], color=EDGE, lw=0.9, zorder=6)
    ax.set_xlim(2, 98)
    ax.set_ylim(2, 46)


def render(animal="rabbit"):
    OUT.mkdir(parents=True, exist_ok=True)
    draw = {"rabbit": rabbit, "mouse": mouse}[animal]
    fig, ax = plt.subplots(figsize=(6, 4.6))
    ax.set_aspect("equal")
    ax.axis("off")
    draw(ax)
    fig.patch.set_alpha(0)
    for ext, dpi in (("png", 300), ("pdf", None)):
        fig.savefig(OUT / f"{animal}.{ext}", transparent=True, bbox_inches="tight", pad_inches=0.05, **({"dpi": dpi} if dpi else {}))
    fig.savefig(OUT / f"{animal}_icon.png", transparent=True, bbox_inches="tight", pad_inches=0.02, dpi=200)
    plt.close(fig)
    print("✓", OUT / f"{animal}.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--animal", choices=["rabbit", "mouse"])
    a = ap.parse_args()
    for an in ([a.animal] if a.animal else ["rabbit", "mouse"]):
        render(an)
