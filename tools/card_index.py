#!/usr/bin/env python3
"""card_index.py — 校验实验知识卡片并生成 reference/cards/index.yaml（贡献卡片后运行）。

  python tools/card_index.py            # 校验 + 重新生成索引
  python tools/card_index.py --check    # 只校验（CI 用）
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CARDS = ROOT / "reference" / "cards"
REQUIRED_KEYS = ["id", "title", "system", "animal", "depth", "textbook_pages", "review_status"]
REQUIRED_H2 = {
    "full": ["一句话", "记录单", "常见", "讨论建议结构", "参考来源"],
    "lite": ["一句话", "机制链", "预期现象", "记录要点", "常见偏差", "讨论抓手", "临床联系", "参考来源"],
}


def parse_front(text: str):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    meta = {}
    for line in m.group(1).splitlines():
        line = line.split("  #")[0]
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    rows, errors = [], []
    for f in sorted(CARDS.glob("ex_*.md"), key=lambda p: [int(x) if x.isdigit() else x for x in re.split(r"[._]|(?<=\d)(?=[a-z])", p.stem[3:]) if x]):
        text = f.read_text(encoding="utf8")
        meta = parse_front(text)
        if not meta:
            errors.append(f"{f.name}: 缺少 front matter")
            continue
        for k in REQUIRED_KEYS:
            if k not in meta:
                errors.append(f"{f.name}: front matter 缺少 {k}")
        if meta.get("id") and f.stem != f"ex_{meta['id']}":
            errors.append(f"{f.name}: 文件名应为 ex_{meta['id']}.md")
        heads = re.findall(r"^## (.+)$", text, re.M)
        for need in REQUIRED_H2.get(meta.get("depth", "lite"), REQUIRED_H2["lite"]):
            if not any(need in h for h in heads):
                errors.append(f"{f.name}: 缺少栏目「{need}」")
        rows.append(meta)
    if errors:
        print("\n".join("✗ " + e for e in errors))
        sys.exit(1)
    print(f"✓ {len(rows)} 张卡片通过校验（full={sum(r['depth']=='full' for r in rows)}, lite={sum(r['depth']=='lite' for r in rows)}）")
    if a.check:
        return
    out = ["# 自动生成，请勿手改：python tools/card_index.py", "experiments:"]
    for r in rows:
        out += [f'  - id: "{r["id"]}"', f'    title: {r["title"]}', f'    system: {r["system"]}',
                f'    animal: {r["animal"]}', f'    depth: {r["depth"]}', f'    card: cards/ex_{r["id"]}.md',
                f'    textbook_pages: "{r["textbook_pages"]}"']
    (ROOT / "reference" / "cards" / "index.yaml").write_text("\n".join(out) + "\n", encoding="utf8")
    print("→ reference/cards/index.yaml")


if __name__ == "__main__":
    main()
