#!/usr/bin/env python3
"""styleprofile.py — 从课本学习文风（“学术 humanizer”的数据部分，中文）。

做两件事：
  build    读 reference/textbook/ 的实验正文，统计课本的文风画像 → knowledge/style/profile.json
             句长分布、逗号密度、连接词频率、常见句首、课本高频搭配（跨多个实验出现的 3–6 字短语）
  compare  把你的报告与画像对照，指出：句子过长/过碎、连接词过多、模板腔以外的“与课本不同”的写法，
             并按实验给出可直接采用的课本搭配

  python tools/styleprofile.py build
  python tools/styleprofile.py compare reports/高钾血症/report.md --exp 2.7

原则：学“怎么说”（术语搭配、句式节奏），不抄“说了什么”；它不修改你的文字，也不以规避 AI 检测为目的。
"""
from __future__ import annotations

import argparse
import json
import re
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "reference" / "textbook"
OUT = ROOT / "knowledge" / "style" / "profile.json"
CONN = ["因此", "所以", "从而", "但是", "但", "而", "同时", "然后", "首先", "其次", "最后", "此外", "另外", "并且", "并", "以及", "可能", "提示", "说明", "表明", "显示", "导致", "引起", "使"]
EDGE = set("的了在与及和对将可以并而为是中之其所被把这该各个")
CJK = re.compile(r"[一-鿿]+")


def body_text(f: Path, explain_only: bool = False) -> str:
    """explain_only=True 只取【目的】【原理】【思考题】等说明性段落（文风学习对象），不含器材清单与仪器操作。"""
    t = f.read_text(encoding="utf8")
    t = re.sub(r"^---\n.*?\n---\n", "", t, flags=re.S)
    t = re.sub(r"^#.*$", "", t, flags=re.M)
    if explain_only:
        parts = re.split(r"(?=【)", t)
        t = "\n".join(p for p in parts if re.match(r"【(目的|原理|思考题)", p))
    return t


def sents(t: str):
    t = re.sub(r"\s+", "", t)
    for s in re.split(r"(?<=[。！？；])", t):
        if len(re.findall(r"[一-鿿]", s)) >= 8:
            yield s


def stats_of(ss: list[str]):
    L = sorted(len(s) for s in ss)
    n = len(L)
    q = lambda p: L[min(n - 1, int(p * n))]
    return dict(n=n, mean=round(st.mean(L), 1), median=q(0.5), p10=q(0.1), p90=q(0.9),
                commas=round(sum(s.count("，") for s in ss) / n, 2))


def conn_rate(text: str) -> dict:
    total = max(1, len(re.findall(r"[一-鿿]", text)))
    return {c: round(text.count(c) * 1000 / total, 2) for c in CONN}


def ngrams(text: str, lo=3, hi=6):
    for seg in CJK.findall(text):
        for n in range(lo, hi + 1):
            for i in range(len(seg) - n + 1):
                yield seg[i:i + n]


def build():
    files = sorted(SRC.glob("ex_*.md"))
    if not files:
        sys.exit("没有找到 reference/textbook/ex_*.md；先运行 python tools/kb.py build 教材.pdf")
    allss, text_all = [], ""
    df = defaultdict(set)
    per_exp = {}
    for f in files:
        t = body_text(f, explain_only=True)
        text_all += t
        ss = list(sents(t))
        allss += ss
        c = Counter(g for g in ngrams(" ".join(ss)) if g[0] not in EDGE and g[-1] not in EDGE)
        per_exp[f.stem[3:]] = {g: v for g, v in c.items() if v >= 3}
        for g in c:
            df[g].add(f.stem)
    starts = Counter(s[:2] for s in allss)
    stop = {"实验步骤", "药品与器材", "思考题", "注意事项", "实验注意事项", "示意图"}
    common = [(g, len(v)) for g, v in df.items() if len(v) >= 3 and g not in stop]
    # 去掉被更长短语包含且频次相同的短语：保留较长者
    common.sort(key=lambda x: (-x[1], -len(x[0])))
    kept = []
    for g, k in common:
        if any(g in h and k <= kk for h, kk in kept):
            continue
        kept.append((g, k))
        if len(kept) >= 220:
            break
    prof = dict(source=f"reference/textbook/ex_*.md（{len(files)} 个实验）", sentence=stats_of(allss), connectives=conn_rate("".join(allss)),
                openings=[[a, b] for a, b in starts.most_common(25)], collocations=[[g, k] for g, k in kept],
                per_exp={e: sorted(v, key=lambda g: -v[g])[:30] for e, v in per_exp.items()})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(prof, ensure_ascii=False, indent=1), encoding="utf8")
    s = prof["sentence"]
    print(f"✓ {OUT}\n  课本 {s['n']} 句：平均 {s['mean']} 字（P10–P90：{s['p10']}–{s['p90']}），每句 {s['commas']} 个逗号；高频搭配 {len(kept)} 条")


def strip_md(raw: str) -> str:
    t = re.sub(r"^---\n.*?\n---\n", "", raw, flags=re.S)
    t = re.split(r"\n#+\s*参考文献", t)[0]
    t = re.sub(r"```.*?```", "", t, flags=re.S)
    t = re.sub(r"\$\$.*?\$\$", "", t, flags=re.S)
    t = re.sub(r"^(?:>|\||#|!\[).*$", "", t, flags=re.M)
    t = re.sub(r"\$[^$]*\$|\[\d+(?:[,，-]\d+)*\]|[*_`]", "", t)
    return t


def compare(md: Path, exp: str | None):
    if not OUT.exists():
        build()
    prof = json.loads(OUT.read_text(encoding="utf8"))
    text = strip_md(md.read_text(encoding="utf8"))
    ss = list(sents(text))
    if not ss:
        sys.exit("没有可比较的正文句子")
    me, tb = stats_of(ss), prof["sentence"]
    print(f"== 文风对照：{md} ==\n")
    print(f"[1] 句长　你：平均 {me['mean']} 字（P10–P90 {me['p10']}–{me['p90']}）　课本：平均 {tb['mean']} 字（{tb['p10']}–{tb['p90']}）")
    if me["mean"] > tb["mean"] * 1.35:
        print("    · 整体偏长：把并列信息拆成两句，一句一个意思。")
    elif me["mean"] < tb["mean"] * 0.6:
        print("    · 整体偏碎：相关的观察与结论可以合并成一句。")
    long = [s for s in ss if len(s) > max(tb["p90"] * 1.3, 90)]
    for s in long[:5]:
        print(f"    · 过长（{len(s)} 字）：{s[:46]}…")
    print(f"\n[2] 逗号密度　你：{me['commas']}/句　课本：{tb['commas']}/句")
    me_c, tb_c = conn_rate("".join(ss)), prof["connectives"]
    over = [(c, me_c[c], tb_c.get(c, 0)) for c in CONN if me_c[c] > max(3, tb_c.get(c, 0) * 2.5)]
    print("\n[3] 连接词（每千字）" + ("：未见明显偏多" if not over else "：以下词用得比课本多得多，检查是否在撑结构"))
    for c, a, b in over:
        print(f"    · 「{c}」你 {a}　课本 {b}")
    colloc = [g for g, _ in prof["collocations"]]
    used = [g for g in colloc if g in text]
    print(f"\n[4] 课本高频搭配　你的报告用了 {len(used)}/{len(colloc)} 条")
    if exp and exp in prof["per_exp"]:
        mine = [g for g in prof["per_exp"][exp] if g not in text]
        print(f"    实验 {exp} 的课本搭配中你尚未用到的（相关的话建议采用）：")
        shown = []
        for g in mine:
            if len(g) >= 4 and not any(g in h or h in g for h in shown):
                shown.append(g)
            if len(shown) >= 15:
                break
        print("    " + "　".join(shown))
    top_open = Counter(s[:2] for s in ss).most_common(3)
    if top_open and top_open[0][1] / len(ss) > 0.12:
        print(f"\n[5] 句首单调：{top_open[0][1]}/{len(ss)} 句以「{top_open[0][0]}」开头，换用不同的主语或状语。")
    print("\n提示：这些只是与课本文风的差距，不是对错；不要为了“像课本”而抄句子（相似度用 stylecheck 查）。")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("build")
    c = sp.add_parser("compare")
    c.add_argument("md", type=Path)
    c.add_argument("--exp")
    a = ap.parse_args()
    build() if a.cmd == "build" else compare(a.md, a.exp)


if __name__ == "__main__":
    main()
