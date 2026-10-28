#!/usr/bin/env python3
"""stylecheck.py — 用语贴近课本程度检查（写完初稿后运行）。

  python tools/stylecheck.py reports/高钾血症/report.md --exp 2.7

输出四类提示：
  1. 规范术语：该实验的课本术语（knowledge/expressions/ex_<编号>.md「术语」栏）哪些用了、哪些还没用
  2. 口语 / 模板腔：命中 knowledge/style/avoid.yaml 的词句，附改法
  3. 与课本的相似度：逐句比对课本片段 ——
       ≥ 0.60  过于接近原文：请改写，或加引号并标注出处（避免抄袭）
       0.15–0.60  措辞贴近课本，较理想
       < 0.15  机制/定义类句子缺少课本依据：请核对来源
  4. 格式细节：数字与单位间的空格、中英文标点混用等

它只给出“提示”，不会改你的文字。需要课本原文时用 python tools/rag.py search。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import rag  # noqa: E402


def strip_md(text: str) -> str:
    text = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.S)
    text = re.sub(r"^>.*$", "", text, flags=re.M)            # 写作提示块
    text = re.sub(r"^\|.*\|\s*$", "", text, flags=re.M)      # 表格
    text = re.sub(r"[*_`#]", "", text)
    return text


def sentences(text: str):
    for line in text.splitlines():
        line = line.strip()
        if not line or re.match(r"^\[\d+\]", line):
            continue
        for s in re.split(r"(?<=[。！？；])", line):
            s = s.strip()
            if len(s) >= 18:
                yield s


def bigrams(s: str) -> set[str]:
    t = rag.tokens(s)
    return set(t)


def load_terms(exp: str) -> list[str]:
    f = ROOT / "knowledge" / "expressions" / f"ex_{exp}.md"
    if not f.exists():
        return []
    m = re.search(r"(?ms)^## 术语\s*\n(.*?)(?=^## |\Z)", f.read_text(encoding="utf8"))
    terms = []
    for line in (m.group(1) if m else "").splitlines():
        line = line.strip().lstrip("-*· ").strip()
        line = re.sub(r"[（(][^）)]*[）)]", "", line)  # 去掉括注（英文名、缩写）
        for part in re.split(r"[、，,；;]", line):
            part = part.strip().split(" ")[0]
            if part and re.search(r"[一-鿿]", part) and len(part) <= 16:
                terms.append(part)
    return terms


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("md", type=Path)
    ap.add_argument("--exp", help="实验编号，如 2.7（用于术语与相似度比对）")
    ap.add_argument("--high", type=float, default=0.60)
    ap.add_argument("--low", type=float, default=0.15)
    a = ap.parse_args()
    import yaml
    raw = a.md.read_text(encoding="utf8")
    text = strip_md(raw)
    n_flags = 0

    print(f"== 检查 {a.md} ==\n")
    # 1 术语
    if a.exp:
        terms = load_terms(a.exp)
        if terms:
            used = [t for t in terms if t in text]
            miss = [t for t in terms if t not in text]
            print(f"[1] 规范术语：已使用 {len(used)}/{len(terms)}")
            if miss:
                print("    尚未出现（若与你的内容相关，建议采用课本说法）：" + "、".join(miss))
        else:
            print(f"[1] 没有找到 knowledge/expressions/ex_{a.exp}.md 的术语栏，跳过。")
    print()

    # 2 口语 / 模板腔
    lex = yaml.safe_load((ROOT / "knowledge" / "style" / "avoid.yaml").read_text(encoding="utf8"))
    print("[2] 口语与模板腔")
    hits = 0
    for ln, line in enumerate(strip_md(raw).splitlines(), 1):
        for kind, label in (("colloquial", "口语"), ("template_tone", "模板腔")):
            for item in lex.get(kind, []):
                for m in re.finditer(item["pattern"], line):
                    hits += 1
                    print(f"    · {label}「{m.group(0)}」：{item['hint']}  ⟵ {line.strip()[:40]}…")
    if not hits:
        print("    未发现。")
    n_flags += hits
    print()

    # 3 与课本相似度
    print("[3] 与课本措辞的相似度（逐句，字二元组 Jaccard）")
    try:
        idx = rag.load()
        pool = [d for d in idx["docs"] if d["corpus"] in ("textbook",) and (not a.exp or d["exp"] in ("", a.exp) or d["exp"] == a.exp)]
    except Exception:  # noqa: BLE001
        pool = []
    if not pool:
        print("    没有 textbook 语料（先运行 python tools/kb.py build 教材.pdf，再 python tools/rag.py build），跳过。")
    else:
        pool_bg = [(d, bigrams(d["text"])) for d in pool]
        high = low = good = 0
        for s in sentences(text):
            sb = bigrams(s)
            if not sb:
                continue
            best, bd = 0.0, None
            for d, db in pool_bg:
                inter = len(sb & db)
                if not inter:
                    continue
                j = inter / len(sb)  # 句中有多少比例的二元组出现在该片段
                if j > best:
                    best, bd = j, d
            if best >= a.high:
                high += 1
                print(f"    ⚠ {best:.2f} 过于接近 {bd['locator']}：{s[:50]}…")
            elif best < a.low and re.search(r"(是指|称为|导致|引起|使得|通过|抑制|激活|机制|由于)", s):
                low += 1
                print(f"    ? {best:.2f} 机制/定义句缺少课本依据：{s[:50]}…")
            elif best >= a.low:
                good += 1
        print(f"    贴近课本 {good} 句；过于接近 {high} 句；缺依据 {low} 句。")
        n_flags += high + low
    print()

    # 4 格式细节
    print("[4] 格式细节")
    fmt = 0
    for ln, line in enumerate(text.splitlines(), 1):
        for m in re.finditer(r"\d(?:kg|mg|ml|mL|min|mmHg|μg|ug|g|s|mm|cm|U)\b", line):
            fmt += 1
            print(f"    · 数字与单位间应留空格：「{m.group(0)}」")
        for m in re.finditer(r"\d\s%", line):
            fmt += 1
            print(f"    · 百分号前不留空格：「{m.group(0)}」")
        for m in re.finditer(r"[一-鿿][,;:]|[,;:][一-鿿]", line):
            fmt += 1
            print(f"    · 中文语境请用全角标点：「{m.group(0)}」")
    if not fmt:
        print("    未发现。")
    n_flags += fmt
    print(f"\n共 {n_flags} 条提示。")


if __name__ == "__main__":
    main()
