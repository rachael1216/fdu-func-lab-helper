#!/usr/bin/env python3
"""labdose.py — 质反应（剂量-死亡）数据的完整分析：LD50 及置信区间、Probit/Logit 拟合与比较、拟合优度、稳健性。

  python tools/labdose.py --dose 110.8 147.7 196.9 262.5 350 --n 22 22 22 22 22 --deaths 0 1 14 20 22
  python tools/labdose.py … --ref 200 --figs outdir      # 同时画图（剂量-反应+似然剖面；残差/bootstrap/留一法）
  python tools/labdose.py … --json

输出：
  1. 改良寇氏法 LD50 及 95% CI（教材方法；p 用观察死亡率）
  2. Probit、Logit 二项最大似然拟合：a、b、LD50、似然剖面 95% CI、AIC、偏差、Pearson 残差、拟合优度 P
  3. 精确（Clopper-Pearson）各组死亡率 95% CI
  4. LD05–LD95 表、LD90/LD10（曲线陡度）
  5. 稳健性：参数 bootstrap 偏差分布、留一剂量组 LD50

说明：LD50 的正式申报计算不在此工具范围；此工具用于课程报告的方法比较与稳健性说明。
需要 scipy、numpy；画图需要 matplotlib。n 为每组动物数（可只给一个数，表示各组相同）。
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

try:
    import numpy as np
    from scipy import optimize, stats
except ImportError:
    sys.exit("需要 scipy 和 numpy：pip install scipy numpy")

CRIT = stats.chi2.ppf(0.95, 1)  # 3.841


# ------------------------------------------------------------ 改良寇氏法
def koch(d, n, k):
    d, n, k = map(np.asarray, (d, n, k))
    p = k / n
    lg = np.log10(d)
    ratios = np.diff(lg)
    I = float(np.mean(ratios))
    m = float(lg[-1] - I * (p.sum() - 0.5))
    nbar = float(np.mean(n))
    s = float(I * math.sqrt((p * (1 - p)).sum() / (nbar - 1)))
    return dict(I=I, sum_p=float(p.sum()), M=m, s_M=s, ld50=10 ** m, lo=10 ** (m - 1.96 * s), hi=10 ** (m + 1.96 * s))


# ------------------------------------------------------------ 二项模型
LINKS = {"probit": (stats.norm.cdf, stats.norm.ppf), "logit": (lambda z: 1 / (1 + np.exp(-z)), lambda p: np.log(p / (1 - p)))}


def loglik(a, b, x, n, k, link):
    p = np.clip(LINKS[link][0](a + b * x), 1e-12, 1 - 1e-12)
    return float((k * np.log(p) + (n - k) * np.log(1 - p)).sum())


def fit(x, n, k, link):
    """返回 (a, b, loglik)。起点用经验 logit 回归。"""
    p = np.clip((k + 0.5) / (n + 1), 0.01, 0.99)
    b0, a0 = np.polyfit(x, LINKS[link][1](p), 1)
    r = optimize.minimize(lambda t: -loglik(t[0], t[1], x, n, k, link), [a0, b0], method="Nelder-Mead", options=dict(xatol=1e-10, fatol=1e-12, maxiter=4000))
    return float(r.x[0]), float(r.x[1]), float(-r.fun)


def profile_ll(theta_ln, x, n, k, link, b_start):
    """固定 ln(LD50/ref)=theta_ln（即 a=-b·theta_ln），对 b 最大化。"""
    f = lambda b: -loglik(-b * theta_ln, b, x, n, k, link)
    r = optimize.minimize_scalar(f, bracket=(b_start * 0.5, b_start * 1.5), tol=1e-10)
    return float(-r.fun)


def ld_ci(a, b, ll, x, n, k, link, ref, q=0.5):
    """LDq 的点估计与似然剖面 95% CI；q≠0.5 时按 ln(LDq/ref) 重参数化。"""
    z = LINKS[link][1](q)
    t_hat = (z - a) / b
    def prof(t):
        f = lambda bb: -loglik(z - bb * t, bb, x, n, k, link)
        r = optimize.minimize_scalar(f, bracket=(b * 0.5, b * 1.5), tol=1e-10)
        return float(-r.fun)
    g = lambda t: 2 * (ll - prof(t)) - CRIT
    span = 0.5
    lo = optimize.brentq(g, t_hat - span, t_hat - 1e-6)
    hi = optimize.brentq(g, t_hat + 1e-6, t_hat + span)
    return ref * math.exp(t_hat), ref * math.exp(lo), ref * math.exp(hi), t_hat


def analyse(d, n, k, ref, nboot=3000, seed=20261008, dev_list=(5.0, 10.0)):
    d, n, k = np.asarray(d, float), np.asarray(n, float), np.asarray(k, float)
    x = np.log(d / ref)
    out = {"koch": koch(d, n, k), "models": {}}
    sat = float((np.where(k > 0, k * np.log(np.clip(k / n, 1e-12, 1)), 0) + np.where(n - k > 0, (n - k) * np.log(np.clip((n - k) / n, 1e-12, 1)), 0)).sum())
    for link in ("probit", "logit"):
        a, b, ll = fit(x, n, k, link)
        ld, lo, hi, _ = ld_ci(a, b, ll, x, n, k, link, ref)
        p = LINKS[link][0](a + b * x)
        dev = 2 * (sat - ll)
        pear = (k - n * p) / np.sqrt(n * p * (1 - p))
        out["models"][link] = dict(a=a, b=b, loglik=ll, ld50=ld, lo=lo, hi=hi, aic=-2 * (ll + float(stats.binom.logpmf(k, n, k / n).sum() - (k * np.log(np.clip(k / n, 1e-300, 1)) + (n - k) * np.log(np.clip(1 - k / n, 1e-300, 1))).sum())) + 4, deviance=dev, df=len(d) - 2,
                                   gof_p=float(stats.chi2.sf(dev, len(d) - 2)), pearson=[float(v) for v in pear], pearson_chi2=float((pear ** 2).sum()),
                                   fitted=[float(v) for v in p])
    pm = out["models"]["probit"]
    rows = []
    for q in (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95):
        try:
            v, lo, hi, _ = ld_ci(pm["a"], pm["b"], pm["loglik"], x, n, k, "probit", ref, q)
            rows.append(dict(q=q, ld=v, lo=lo, hi=hi))
        except ValueError:
            rows.append(dict(q=q, ld=ref * math.exp((stats.norm.ppf(q) - pm["a"]) / pm["b"]), lo=None, hi=None))
    out["ldq"] = rows
    ld = {r["q"]: r["ld"] for r in rows}
    out["steepness_ld90_ld10"] = ld[0.90] / ld[0.10]
    out["exact_ci"] = [dict(dose=float(di), n=int(ni), deaths=int(ki), p=float(ki / ni),
                            lo=float(stats.beta.ppf(0.025, ki, ni - ki + 1)) if ki > 0 else 0.0,
                            hi=float(stats.beta.ppf(0.975, ki + 1, ni - ki)) if ki < ni else 1.0) for di, ni, ki in zip(d, n, k)]
    # bootstrap：以拟合的 Probit 为真模型，重抽偏差
    rng = np.random.default_rng(seed)
    pf = np.array(pm["fitted"])
    devs = []
    for _ in range(nboot):
        kb = rng.binomial(n.astype(int), pf).astype(float)
        try:
            ab, bb, llb = fit(x, n, kb, "probit")
        except Exception:  # noqa: BLE001
            continue
        satb = float((np.where(kb > 0, kb * np.log(np.clip(kb / n, 1e-12, 1)), 0) + np.where(n - kb > 0, (n - kb) * np.log(np.clip((n - kb) / n, 1e-12, 1)), 0)).sum())
        devs.append(2 * (satb - llb))
    devs = np.array(devs)
    out["bootstrap"] = dict(nboot=len(devs), p=float((devs >= pm["deviance"] - 1e-9).mean()), deviances=devs.tolist())
    loo = []
    for i in range(len(d)):
        m = np.arange(len(d)) != i
        a2, b2, _ = fit(x[m], n[m], k[m], "probit")
        loo.append(dict(omit=i + 1, dose=float(d[i]), ld50=float(ref * math.exp(-a2 / b2))))
    out["loo"] = loo
    mu, sigma = -pm["a"] / pm["b"], 1 / pm["b"]
    ld50 = ref * math.exp(mu)
    sens = []
    for dv in dev_list:
        for sg in (-1, 1):
            D = ld50 * (1 + sg * dv / 100)
            sens.append(dict(dev=sg * dv, dose=D, mortality=float(stats.norm.cdf(pm["a"] + pm["b"] * math.log(D / ref)))))
    out["sensitivity"] = dict(mu=mu, sigma=sigma, gsd=math.exp(sigma), slope_pp_per_pct=pm["b"] / math.sqrt(2 * math.pi), points=sens)
    return out


# ------------------------------------------------------------ 输出
def text(o, d, n, k, ref):
    kc = o["koch"]
    L = ["【改良寇氏法】", f"  I = {kc['I']:.6f}　Σp = {kc['sum_p']:.6f}　M = {kc['M']:.6f}　s_M = {kc['s_M']:.6f}",
         f"  LD50 = {kc['ld50']:.2f}（95% CI {kc['lo']:.2f}–{kc['hi']:.2f}）", "", "【二项模型（x = ln(D/%g)）】" % ref]
    for name, m in o["models"].items():
        L.append(f"  {name:<6} a={m['a']:.5f} b={m['b']:.5f}  LD50={m['ld50']:.2f}（{m['lo']:.2f}–{m['hi']:.2f}，似然剖面）  AIC={m['aic']:.3f}  "
                 f"偏差={m['deviance']:.3f}(df={m['df']}, P={m['gof_p']:.3f})  Pearson χ²={m['pearson_chi2']:.3f}")
    L += ["", "【各组死亡率与精确 95% CI】"]
    for r in o["exact_ci"]:
        L.append(f"  {r['dose']:>7.1f}  {r['deaths']}/{r['n']}  {r['p']*100:5.1f}%  [{r['lo']*100:.1f}, {r['hi']*100:.1f}]%")
    L += ["", "【Probit 的 LDq（似然剖面 95% CI）】"]
    for r in o["ldq"]:
        ci = f"（{r['lo']:.2f}–{r['hi']:.2f}）" if r["lo"] else "（CI 未收敛）"
        L.append(f"  LD{int(r['q']*100):02d}  {r['ld']:.2f} {ci}")
    L.append(f"  LD90/LD10 = {o['steepness_ld90_ld10']:.3f}")
    sv = o["sensitivity"]
    L += ["", f"【局部敏感性（Probit）】阈值 ln(T/{ref:g}) ~ N({sv['mu']:.5f}, {sv['sigma']:.5f}²)，几何标准差 e^σ = {sv['gsd']:.3f}",
          f"  LD50 处剂量每增加 1%，死亡概率约增加 {sv['slope_pp_per_pct']:.2f} 个百分点"]
    L += [f"  剂量偏离 LD50 {p['dev']:+g}%（{p['dose']:.1f} mg/kg）→ 预测死亡率 {p['mortality']*100:.1f}%" for p in sv["points"]]
    b = o["bootstrap"]
    L += ["", f"【参数 bootstrap】{b['nboot']} 次，观察偏差 {o['models']['probit']['deviance']:.3f}，P = {b['p']:.3f}", "【留一剂量组 LD50（Probit）】"]
    L += [f"  去掉第 {r['omit']} 组（{r['dose']:g}）→ {r['ld50']:.2f}" for r in o["loo"]]
    return "\n".join(L)


def figures(o, d, n, k, ref, outdir):
    import matplotlib.pyplot as plt
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import labplot  # type: ignore
    labplot.setup((16, 7.5))
    OI = labplot.OKABE_ITO
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    d, n, k = np.asarray(d, float), np.asarray(n, float), np.asarray(k, float)
    x = np.log(d / ref)
    pm, lm = o["models"]["probit"], o["models"]["logit"]
    # 图 1
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(plt.rcParams["figure.figsize"][0], plt.rcParams["figure.figsize"][1]))
    grid = np.linspace(x.min() - 0.15, x.max() + 0.15, 300)
    a1.plot(ref * np.exp(grid), LINKS["probit"][0](pm["a"] + pm["b"] * grid) * 100, color=OI[0], label="Probit")
    a1.plot(ref * np.exp(grid), LINKS["logit"][0](lm["a"] + lm["b"] * grid) * 100, color=OI[1], ls="--", label="Logit")
    ex = o["exact_ci"]
    a1.errorbar(d, [r["p"] * 100 for r in ex], yerr=[[r["p"] * 100 - r["lo"] * 100 for r in ex], [r["hi"] * 100 - r["p"] * 100 for r in ex]], fmt="o", color="k", capsize=3, label="观察（精确 95% CI）")
    a1.axhline(50, color="0.6", lw=0.8, ls=":")
    a1.axvline(pm["ld50"], color="0.6", lw=0.8, ls=":")
    a1.set_xscale("log")
    from matplotlib.ticker import NullFormatter
    a1.xaxis.set_minor_formatter(NullFormatter())
    a1.set_xticks([110, 150, 200, 300])
    a1.set_xticklabels(["110", "150", "200", "300"])
    a1.set_xlabel("剂量（mg/kg，对数刻度）")
    a1.set_ylabel("死亡率（%）")
    a1.legend(frameon=False, loc="center left", bbox_to_anchor=(0.0, 0.62))
    a1.set_title("A  剂量-反应曲线", loc="left", fontsize=10)
    ts = np.linspace(math.log(pm["lo"] / ref) - 0.08, math.log(pm["hi"] / ref) + 0.08, 120)
    for lk, mm, col, ls in (("probit", pm, OI[0], "-"), ("logit", lm, OI[1], "--")):
        prof = [2 * (mm["loglik"] - labplot_prof(t, x, n, k, lk, mm)) for t in ts]
        a2.plot(ref * np.exp(ts), prof, color=col, ls=ls, label=lk.capitalize())
    a2.axhline(CRIT, color="0.4", lw=0.8, ls=":")
    a2.set_ylim(0, 12)
    a2.set_xlabel("候选 LD50（mg/kg）")
    a2.set_ylabel("似然比统计量")
    a2.legend(frameon=False)
    a2.set_title("B  似然剖面（虚线：χ²₁ 的 95% 界值 3.841）", loc="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(outdir / "fig1_doseresponse.png", bbox_inches="tight")
    plt.close(fig)
    # 图 2
    fig, ax = plt.subplots(1, 3, figsize=(plt.rcParams["figure.figsize"][0], plt.rcParams["figure.figsize"][1]))
    ax[0].axhline(0, color="0.5", lw=0.8)
    ax[0].plot(d, pm["pearson"], "o-", color=OI[0])
    ax[0].set_xscale("log")
    ax[0].set_xticks([110, 150, 200, 300])
    ax[0].set_xticklabels(["110", "150", "200", "300"])
    ax[0].set_xlabel("剂量（mg/kg）")
    ax[0].set_ylabel("Pearson 残差")
    ax[0].set_title("A  模型残差", loc="left", fontsize=10)
    ax[1].hist(o["bootstrap"]["deviances"], bins=24, density=True, color="#9DB4C9", edgecolor="white")
    ax[1].axvline(pm["deviance"], color=OI[1], lw=1.6, label=f"观察偏差 = {pm['deviance']:.2f}")
    ax[1].set_xlabel("偏差")
    ax[1].set_ylabel("密度")
    ax[1].legend(frameon=False)
    ax[1].set_title("B  参数 bootstrap", loc="left", fontsize=10)
    ax[2].plot([r["omit"] for r in o["loo"]], [r["ld50"] for r in o["loo"]], "o", color=OI[1])
    ax[2].axhline(pm["ld50"], color="0.4", ls=":", lw=0.9)
    ax[2].vlines([r["omit"] for r in o["loo"]], pm["ld50"], [r["ld50"] for r in o["loo"]], color="0.6", lw=1)
    ax[2].set_xticks([r["omit"] for r in o["loo"]])
    ax[2].set_xlabel("被去掉的剂量组")
    ax[2].set_ylabel("LD50（mg/kg）")
    ax[2].set_title("C  留一剂量组", loc="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(outdir / "fig2_robustness.png", bbox_inches="tight")
    plt.close(fig)
    # 图 3：阈值分布与给药误差传播
    sv = o["sensitivity"]
    fig, ax = plt.subplots(1, 2, figsize=(plt.rcParams["figure.figsize"][0], plt.rcParams["figure.figsize"][1]))
    Dg = np.linspace(80, 450, 400)
    dens = stats.norm.pdf((np.log(Dg / ref) - sv["mu"]) / sv["sigma"]) / (sv["sigma"] * Dg)
    ax[0].plot(Dg, dens, color=OI[0])
    ax[0].fill_between(Dg, dens, color="#DCE6EF")
    ax[0].axvline(pm["ld50"], color=OI[1], ls="--", lw=1.2, label=f"中位数 = {pm['ld50']:.1f} mg/kg")
    ax[0].set_xlabel("个体耐受阈值（mg/kg）")
    ax[0].set_ylabel("概率密度")
    ax[0].legend(frameon=False)
    ax[0].set_title("A  群体耐受阈值分布", loc="left", fontsize=10)
    dd = np.linspace(-15, 15, 200)
    ax[1].plot(dd, [stats.norm.cdf(pm["a"] + pm["b"] * math.log(pm["ld50"] * (1 + v / 100) / ref)) * 100 for v in dd], color=OI[0])
    ax[1].plot([p["dev"] for p in sv["points"]], [p["mortality"] * 100 for p in sv["points"]], "o", color=OI[1])
    ax[1].axhline(50, color="0.6", lw=0.8, ls=":")
    ax[1].axvline(0, color="0.6", lw=0.8, ls=":")
    ax[1].set_xlabel("剂量相对 LD50 的偏离（%）")
    ax[1].set_ylabel("预测死亡率（%）")
    ax[1].set_title("B  给药误差传播（模型推导）", loc="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(outdir / "fig3_sensitivity.png", bbox_inches="tight")
    plt.close(fig)
    print(f"✓ {outdir}/fig1_doseresponse.png, fig2_robustness.png, fig3_sensitivity.png")


def labplot_prof(t, x, n, k, link, mm):
    f = lambda bb: -loglik(-bb * t, bb, x, n, k, link)
    r = optimize.minimize_scalar(f, bracket=(mm["b"] * 0.5, mm["b"] * 1.5), tol=1e-10)
    return float(-r.fun)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dose", nargs="+", type=float, required=True)
    ap.add_argument("--n", nargs="+", type=int, required=True)
    ap.add_argument("--deaths", nargs="+", type=int, required=True)
    ap.add_argument("--ref", type=float, default=None, help="x = ln(D/ref) 的参考剂量，默认取几何中点附近的整十数")
    ap.add_argument("--boot", type=int, default=3000)
    ap.add_argument("--dev", nargs="+", type=float, default=[5.0, 10.0], help="敏感性分析的剂量偏离百分数，如 3.7 5 10")
    ap.add_argument("--figs", help="输出图的目录")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    d, k = a.dose, a.deaths
    n = a.n * len(d) if len(a.n) == 1 else a.n
    if not (len(d) == len(n) == len(k)) or len(d) < 4:
        sys.exit("错误：剂量、n、死亡数需等长，且至少 4 个剂量组")
    if any(x < 0 or x > m for x, m in zip(k, n)) or sorted(d) != list(d):
        sys.exit("错误：死亡数应在 0..n，剂量需从小到大")
    if sum(1 for x, m in zip(k, n) if 0 < x < m) < 2:
        sys.exit("错误：至少需要 2 个“部分死亡”的剂量组才能拟合斜率")
    ref = a.ref or float(round(math.exp(np.mean(np.log(d))), -1))
    o = analyse(d, n, k, ref, a.boot, dev_list=tuple(a.dev))
    if a.json:
        o2 = {k2: v for k2, v in o.items()}
        o2["bootstrap"] = {kk: vv for kk, vv in o["bootstrap"].items() if kk != "deviances"}
        print(json.dumps(o2, ensure_ascii=False, indent=1))
    else:
        print(text(o, d, n, k, ref))
    if a.figs:
        figures(o, d, n, k, ref, a.figs)


if __name__ == "__main__":
    main()
