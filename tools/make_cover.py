#!/usr/bin/env python3
"""make_cover.py — 生成实验报告封面题图（8 个主题，纯 matplotlib 绘制，可复现）

  python tools/make_cover.py                      # 生成全部主题到 assets/covers/
  python tools/make_cover.py --theme ecg          # 只生成一个
  python tools/make_cover.py --theme resp --out my_cover.jpg --seed 7

主题 theme：
  general  通用（心电+量效曲线+细胞网络）      cardio  心血管（心电图 PQRST）
  neuro    神经肌肉（动作电位+神经元分支）      resp    呼吸（膈肌放电及其积分曲线）
  pharm    药理（量效 S 曲线+苯环）            blood   血液（红细胞+纤维蛋白网）
  gi       消化（平滑肌张力曲线与加药标记）    renal   泌尿（肾单位+液滴）

没有使用任何学校徽标/商标；色板为"深海蓝-青-珊瑚红"的原创配色。
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import Circle, Polygon  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
W, H = 2480, 1240          # 21 cm × 10.5 cm @ 300 dpi
INK, BLUE, SKY = "#081650", "#1B3FB0", "#5AA7FF"
TEAL, CORAL, WHITE = "#2DD4BF", "#FF6B6B", "#FFFFFF"
THEMES = ["general", "cardio", "neuro", "resp", "pharm", "blood", "gi", "renal"]


# ---------------------------------------------------------------- helpers
def background(ax, rng):
    yy, xx = np.mgrid[0:H, 0:W]
    t = np.clip((xx / W) * 0.65 + (1 - yy / H) * 0.35, 0, 1)
    c0, c1 = np.array(matplotlib.colors.to_rgb(INK)), np.array(matplotlib.colors.to_rgb(BLUE))
    img = c0[None, None, :] * (1 - t[..., None]) + c1[None, None, :] * t[..., None]
    # 青色辉光
    gx, gy = W * 0.86, H * 0.78
    glow = np.exp(-(((xx - gx) / (W * 0.33)) ** 2 + ((yy - gy) / (H * 0.55)) ** 2))
    img = img * (1 - 0.35 * glow[..., None]) + np.array(matplotlib.colors.to_rgb(TEAL))[None, None, :] * 0.35 * glow[..., None]
    ax.imshow(img, extent=(0, W, H, 0), origin="upper", aspect="auto", zorder=0)
    # 心电纸式网格
    for x in range(0, W, 62):
        ax.plot([x, x], [0, H], color=WHITE, alpha=0.05 if (x // 62) % 5 else 0.10, lw=1.0, zorder=1)
    for y in range(0, H, 62):
        ax.plot([0, W], [y, y], color=WHITE, alpha=0.05 if (y // 62) % 5 else 0.10, lw=1.0, zorder=1)


def glow_line(ax, x, y, color=WHITE, lw=5, z=5, alpha=1.0):
    for w, a in ((lw * 4.5, 0.06), (lw * 2.6, 0.10), (lw * 1.5, 0.18)):
        ax.plot(x, y, color=color, lw=w, alpha=a * alpha, solid_capstyle="round", zorder=z - 1)
    ax.plot(x, y, color=color, lw=lw, alpha=alpha, solid_capstyle="round", solid_joinstyle="round", zorder=z)


def wave_bottom(ax):
    x = np.linspace(0, W, 600)
    base = 150
    y1 = base + 26 * np.sin(x / W * 2 * math.pi * 1.1 + 0.6)
    ax.fill_between(x, 0, y1 * 1.0, color=WHITE, zorder=20)
    y2 = base + 40 + 30 * np.sin(x / W * 2 * math.pi * 1.1 + 0.2)
    ax.plot(x, y2, color=WHITE, alpha=0.22, lw=3, zorder=19)
    ax.plot(x, y1 + 10, color=TEAL, alpha=0.55, lw=3, zorder=21)


def gauss(t, mu, sig):
    return np.exp(-((t - mu) / sig) ** 2)


def ecg_beat(t):
    return (0.16 * gauss(t, 0.18, 0.035) - 0.14 * gauss(t, 0.285, 0.011) + 1.0 * gauss(t, 0.31, 0.011)
            - 0.28 * gauss(t, 0.335, 0.013) + 0.34 * gauss(t, 0.56, 0.055))


def ecg_signal(n_beats, rr, x0, x1, y0, amp, rng, jitter=0.0):
    xs = np.linspace(x0, x1, 4000)
    total = n_beats * rr
    tt = (xs - x0) / (x1 - x0) * total
    ph = np.mod(tt, rr)
    return xs, y0 + amp * ecg_beat(ph) + jitter * rng.normal(size=xs.size)


# ---------------------------------------------------------------- themes
def theme_cardio(ax, rng):
    for k, (off, a, lw) in enumerate([(-300, 0.18, 3), (320, 0.22, 3), (-120, 0.35, 4)]):
        xs, ys = ecg_signal(7.4, 1.0, 120, W - 120, H * 0.5 + off, 140 * (1 + 0.1 * k), rng)
        glow_line(ax, xs, ys, WHITE, lw, z=3, alpha=a)
    xs, ys = ecg_signal(7.4, 1.0, 120, W - 120, H * 0.50, 250, rng)
    glow_line(ax, xs, ys, CORAL, 4.5, z=6)
    for k in range(7):                                    # R 峰标记
        px = 120 + (W - 240) * (k + 0.31) / 7.4
        ax.add_patch(Circle((px, H * 0.50 + 250), 9, color=WHITE, zorder=8))


def theme_neuro(ax, rng):
    # 神经元树突分支（随机生成，固定种子）
    def branch(x, y, ang, length, depth):
        if depth == 0 or length < 18:
            return
        x2, y2 = x + length * math.cos(ang), y + length * math.sin(ang)
        ax.plot([x, x2], [y, y2], color=SKY, alpha=0.25 + 0.08 * depth, lw=1 + depth * 1.3, zorder=3, solid_capstyle="round")
        if depth <= 2:
            ax.add_patch(Circle((x2, y2), 6 + depth * 2, color=TEAL, alpha=0.7, zorder=4))
        for d in (-0.55, 0.45):
            branch(x2, y2, ang + d + rng.normal(0, 0.12), length * 0.72, depth - 1)
    for s, (x, y) in enumerate([(160, H * 0.42), (260, H * 0.78)]):
        for a in np.linspace(-1.1, 1.1, 5):
            branch(x, y, a, 120 + 30 * s, 5)
        ax.add_patch(Circle((x, y), 34, color=WHITE, alpha=0.85, zorder=5))
    # 动作电位序列
    xs = np.linspace(480, W - 100, 6000)
    ys = np.full_like(xs, -70.0)
    for c in (760, 1190, 1560, 1860, 2100):
        d = xs - c
        ys += np.where(d > 0, 100 * np.exp(-d / 38) * (1 - np.exp(-d / 3.2)) * 1.25, 0) * (d < 330)
        ys -= np.where(d > 55, 14 * np.exp(-(d - 55) / 70), 0) * (d < 330)
    yy = H * 0.40 + (ys + 70) * 4.2
    glow_line(ax, xs, yy, WHITE, 5, z=6)
    ax.plot([480, W - 100], [H * 0.40] * 2, color=CORAL, lw=3, ls=(0, (2, 6)), alpha=0.8, zorder=4)
    ax.plot([480, W - 100], [H * 0.40 + 4.2 * 55] * 2, color=SKY, lw=2, ls=(0, (1, 8)), alpha=0.6, zorder=4)


def theme_resp(ax, rng):
    # 膈肌放电（高频簇）+ 积分曲线
    xs = np.linspace(120, W - 120, 9000)
    period = 330
    ph = np.mod(xs - 120, period) / period
    env = np.where(ph < 0.46, np.abs(np.sin(np.pi * np.minimum(ph, 0.46) / 0.46)) ** 1.3, 0)
    drift = 1 + 0.35 * np.sin((xs - 120) / W * 3.2)
    sig = env * drift * rng.normal(size=xs.size) * 210
    glow_line(ax, xs, H * 0.60 + sig, SKY, 2.4, z=4, alpha=0.95)
    integ = np.convolve(env * drift, np.ones(25) / 25, mode="same")
    glow_line(ax, xs, H * 0.28 + integ * 230, CORAL, 7, z=6)
    # 呼吸容积正弦
    glow_line(ax, xs, H * 0.84 + 60 * np.sin((xs - 120) / period * 2 * math.pi - 1.2), TEAL, 4, z=4, alpha=0.8)
    for k in range(7):
        ax.plot([120 + k * period] * 2, [H * 0.17, H - 200], color=WHITE, alpha=0.10, lw=2, ls=(0, (3, 6)), zorder=2)


def theme_pharm(ax, rng):
    x = np.linspace(-3, 3, 400)
    cols = [SKY, TEAL, WHITE, CORAL]
    for i, (e50, hill, c) in enumerate(zip([-1.3, -0.5, 0.35, 1.2], [1.0, 1.3, 1.6, 1.2], cols)):
        y = 1 / (1 + np.exp(-hill * 2.2 * (x - e50)))
        X = 150 + (x + 3) / 6 * 1500
        Y = H * 0.25 + y * 560 + 130
        glow_line(ax, X, Y, c, 5.5, z=5 + i, alpha=0.95)
        xp = np.array([-2.4, -1.6, -0.8, 0, 0.8, 1.6, 2.4])
        yp = 1 / (1 + np.exp(-hill * 2.2 * (xp - e50))) + rng.normal(0, 0.025, xp.size)
        ax.scatter(150 + (xp + 3) / 6 * 1500, H * 0.25 + np.clip(yp, 0, 1) * 560 + 130, s=70, color=c, alpha=0.9, zorder=9, edgecolor=INK, linewidth=1.5)
    ax.plot([150, 1650], [H * 0.25 + 280 + 130] * 2, color=WHITE, alpha=0.4, lw=2, ls=(0, (2, 6)), zorder=3)

    def ring(cx, cy, r, a0=0):
        pts = [(cx + r * math.cos(a0 + k * math.pi / 3), cy + r * math.sin(a0 + k * math.pi / 3)) for k in range(6)]
        ax.add_patch(Polygon(pts, closed=True, fill=False, ec=WHITE, lw=4, alpha=0.9, zorder=6, joinstyle="round"))
        inner = [(cx + 0.62 * r * math.cos(a0 + k * math.pi / 3 + math.pi / 6), cy + 0.62 * r * math.sin(a0 + k * math.pi / 3 + math.pi / 6)) for k in range(6)]
        for k in (0, 2, 4):
            ax.plot([inner[k][0], inner[(k + 1) % 6][0]], [inner[k][1], inner[(k + 1) % 6][1]], color=WHITE, lw=3, alpha=0.7, zorder=6)
        return pts
    p = ring(1930, H * 0.50, 135)
    q = ring(1930 + 233.8, H * 0.50 - 135 * 0.5 - 135 * 0.5 + 0, 135)
    ax.plot([p[0][0], p[0][0] + 110], [p[0][1], p[0][1] - 90], color=CORAL, lw=5, zorder=6)
    ax.add_patch(Circle((p[0][0] + 130, p[0][1] - 105), 24, color=CORAL, zorder=7))
    ax.add_patch(Circle((q[3][0] - 40, q[3][1] + 120), 18, color=TEAL, zorder=7))


def theme_blood(ax, rng):
    pts = []
    for _ in range(26):
        pts.append((rng.uniform(150, W - 150), rng.uniform(H * 0.22, H * 0.9), rng.uniform(55, 100)))
    for i, (x1, y1, _r) in enumerate(pts):                     # 纤维蛋白丝
        for (x2, y2, _r2) in pts[i + 1:]:
            d = math.hypot(x1 - x2, y1 - y2)
            if d < 430:
                ax.plot([x1, x2], [y1, y2], color=WHITE, alpha=0.16 + 0.22 * (1 - d / 430), lw=1.6, zorder=3)
    for (x, y, r) in pts:
        ax.add_patch(Circle((x, y), r, color=CORAL, alpha=0.88, zorder=5))
        ax.add_patch(Circle((x, y), r * 0.55, color="#C9364A", alpha=0.75, zorder=6))
        ax.add_patch(Circle((x - r * 0.28, y + r * 0.28), r * 0.14, color=WHITE, alpha=0.35, zorder=7))
    for _ in range(70):                                            # 血小板
        ax.add_patch(Circle((rng.uniform(100, W - 100), rng.uniform(H * 0.2, H * 0.95)), rng.uniform(5, 11), color=TEAL, alpha=0.8, zorder=6))


def theme_gi(ax, rng):
    xs = np.linspace(110, W - 110, 5000)
    base = H * 0.55
    tone = np.zeros_like(xs)
    marks = [(560, 150), (1010, 250), (1480, 90), (1930, 200)]
    for m, h in marks:
        tone += h * (1 / (1 + np.exp(-(xs - m) / 14))) * np.exp(-np.clip(xs - m, 0, None) / 520)
    slow = 28 * np.sin((xs - 110) / 38) * (1 + 0.5 * np.sin(xs / 400)) + 10 * np.sin((xs - 110) / 11)
    y = base + tone * 1.7 + slow
    glow_line(ax, xs, y, WHITE, 5, z=6)
    ax.plot([110, W - 110], [base, base], color=SKY, alpha=0.5, lw=2, ls=(0, (2, 6)), zorder=3)
    for (m, _h), c, lab in zip(marks, [CORAL, TEAL, CORAL, TEAL], ["A", "B", "Ba", "Atr"]):
        ax.plot([m, m], [H * 0.82, H * 0.22], color=c, lw=3, ls=(0, (6, 6)), alpha=0.8, zorder=4)
        ax.scatter([m], [H * 0.82], s=240, color=c, zorder=8, edgecolor=WHITE, linewidth=2)
        ax.text(m, H * 0.82, lab, color=WHITE, ha="center", va="center", fontsize=11, fontweight="bold", zorder=9)


def theme_renal(ax, rng):
    cx, cy = 360, H * 0.58
    for r, a in ((150, 0.9), (112, 0.55), (74, 0.35)):             # 肾小球
        ax.add_patch(Circle((cx, cy), r, fill=False, ec=CORAL if r == 74 else WHITE, lw=5, alpha=a, zorder=5))
    ax.add_patch(Circle((cx, cy), 36, color=CORAL, alpha=0.9, zorder=6))
    t = np.linspace(0, 1, 1200)
    px = cx + 150 + t * (W - cx - 330)                              # 肾小管：弯曲
    py = cy + 40 * np.sin(t * 16) - 220 * np.sin(t * math.pi * 1.0) * (1 - t) ** 0.4
    glow_line(ax, px, py, SKY, 9, z=4, alpha=0.9)
    glow_line(ax, px, py + 38, WHITE, 3, z=4, alpha=0.5)
    for _ in range(46):                                            # 液滴
        k = rng.integers(0, 1200)
        ax.add_patch(Circle((px[k] + rng.normal(0, 12), py[k] + rng.uniform(40, 290)), rng.uniform(5, 12), color=TEAL, alpha=0.85, zorder=6))
    ax.plot([W - 380, W - 380], [py[-1] + 30, H - 220], color=TEAL, lw=7, alpha=0.8, zorder=5)


def theme_general(ax, rng):
    xs, ys = ecg_signal(6.0, 1.0, 120, W - 120, H * 0.52, 300, rng)
    glow_line(ax, xs, ys, CORAL, 6, z=6)
    x = np.linspace(-3, 3, 300)
    for i, (e50, c) in enumerate(zip([-0.6, 0.6], [SKY, TEAL])):
        y = 1 / (1 + np.exp(-2.4 * (x - e50)))
        glow_line(ax, 1500 + (x + 3) / 6 * 760, H * 0.17 + y * 200 + 20 * i, c, 4.5, z=5, alpha=0.9)
    for k in range(18):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(160, 420)
        ax.add_patch(Circle((330 + r * math.cos(a), H * 0.55 + r * math.sin(a) * 0.6), rng.uniform(6, 15), color=TEAL if k % 2 else SKY, alpha=0.7, zorder=4))


FUNCS = {"general": theme_general, "cardio": theme_cardio, "neuro": theme_neuro, "resp": theme_resp,
         "pharm": theme_pharm, "blood": theme_blood, "gi": theme_gi, "renal": theme_renal}


def render(theme: str, out: Path, seed: int = 2026):
    rng = np.random.default_rng(seed)
    fig = plt.figure(figsize=(W / 300, H / 300), dpi=300)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(H, 0)
    ax.axis("off")
    ax.invert_yaxis()                                              # 现在 y 向上，0 在底部
    # 背景用图像坐标（自上而下）；曲线用 y 向上。
    ax.set_ylim(0, H)
    bg = fig.add_axes([0, 0, 1, 1], zorder=0)
    bg.set_xlim(0, W)
    bg.set_ylim(H, 0)
    bg.axis("off")
    background(bg, rng)
    ax.set_zorder(1)
    ax.patch.set_alpha(0)
    FUNCS[theme](ax, rng)
    wave_bottom(ax)
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=300, format="jpeg" if out.suffix.lower() in (".jpg", ".jpeg") else None,
                pil_kwargs={"quality": 90, "optimize": True} if out.suffix.lower() in (".jpg", ".jpeg") else None)
    plt.close(fig)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", choices=THEMES + ["all"], default="all")
    ap.add_argument("--out", type=Path, help="输出文件（单主题时）")
    ap.add_argument("--seed", type=int, default=2026)
    a = ap.parse_args()
    themes = THEMES if a.theme == "all" else [a.theme]
    for t in themes:
        out = a.out if (a.out and a.theme != "all") else ROOT / "assets" / "covers" / f"cover_{t}.jpg"
        print("✓", render(t, out, a.seed))


if __name__ == "__main__":
    main()
