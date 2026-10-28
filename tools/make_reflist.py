#!/usr/bin/env python3
"""make_reflist.py — 由 knowledge/literature/references.yaml 生成 reference/literature/README.md（文献目录，GB/T 7714）。"""
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import refcheck  # type: ignore


def main():
    items = yaml.safe_load((ROOT / "knowledge/literature/references.yaml").read_text(encoding="utf8"))
    exps = {}
    for it in items:
        for e in it.get("experiments", []):
            exps.setdefault(e, []).append(it)
    out = ["# 重点文献目录", "", "课本之外、优先加入 RAG 的文献。书目均已用 Crossref 核对（见 `verified`）；要点为自述概括，不含原文。",
           "用法：`python tools/rag.py search 关键词 -c literature`。全文 PDF 请自行下载后放入 `corpus/local/literature/`。", ""]
    out += ["| 编号 | 文献（GB/T 7714） | 相关实验 | 关键词 |", "|---|---|---|---|"]
    for it in items:
        au = [{"family": a.split()[0], "given": " ".join(a.split()[1:])} for a in it["authors"]]
        item = {"title": [it["title"]], "author": au, "container-title": [it["journal"]], "volume": it.get("volume", ""),
                "issue": it.get("issue", ""), "page": it.get("pages", ""), "issued": {"date-parts": [[int(it["year"])]]}, "DOI": it["doi"]}
        ref = refcheck.format_gbt(item, bool(it.get("et_al")))
        out.append(f"| {it['id']} | {ref} | {', '.join(it.get('experiments', []))} | {'、'.join(it.get('keywords', []))} |")
    out += ["", "## 按实验索引", ""]
    for e in sorted(exps):
        out.append(f"- 实验 {e}：" + "；".join(i["id"] for i in exps[e]))
    (ROOT / "reference/literature/README.md").write_text("\n".join(out) + "\n", encoding="utf8")
    print("✓ reference/literature/README.md")


if __name__ == "__main__":
    main()
