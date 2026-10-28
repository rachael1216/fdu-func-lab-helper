#!/usr/bin/env python3
"""rag.py — 本地检索（RAG 的“R”）：让写作用语贴近课本，并能回到出处。

为什么要检索：实验报告的措辞（术语、机制表述、判定标准）应当与课本一致。
把教材、讲义和重点文献切成片段建索引，写作时先检索、再据片段措辞，并标明出处。

语料（每片段带来源标签）：
  textbook    reference/textbook/ex_*.md      教材（由 tools/kb.py 在本机从你自己的 PDF 生成，不入库）
  card        knowledge/cards/*.md           实验知识卡（AI 起草，未审校）
  expr        knowledge/expressions/*.md     各实验“课本表述”整理（术语、句式、页码）
  literature  knowledge/literature/*.yaml    重点文献登记（已核对书目 + 要点概括）
  <子目录名>  corpus/local/<子目录>/…        你自己放的讲义、其他教材、文献全文（pdf/docx/md/txt）

用法：
  python tools/rag.py build
  python tools/rag.py search 高钾血症 心电图 T波 -k 5
  python tools/rag.py search 复能剂 -c literature
  python tools/rag.py search 瞳孔 缩小 --exp 1.5 -c textbook --full
  python tools/rag.py sources

检索方法：中文字二元组 + 英文词的 BM25，纯 Python，无需服务器和模型；对几百页的课本足够精确且可复现。
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "corpus" / "index" / "rag.json"
LOCAL = ROOT / "corpus" / "local"
CHUNK = 380

_CJK = re.compile(r"[一-鿿]+")
_LAT = re.compile(r"[A-Za-z][A-Za-z0-9\-]*|\d+(?:\.\d+)?")


def tokens(text: str) -> list[str]:
    out: list[str] = []
    for m in _CJK.finditer(text):
        s = m.group(0)
        out += [s] if len(s) == 1 else [s[i:i + 2] for i in range(len(s) - 1)]
    out += [w.lower() for w in _LAT.findall(text)]
    return out


# ------------------------------------------------------------------ 切片
def split_paragraphs(text: str, size: int = CHUNK) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n|\n(?=\d+[．.、])", text) if p.strip()]
    out, buf = [], ""
    for p in paras:
        if len(buf) + len(p) > size and buf:
            out.append(buf)
            buf = ""
        while len(p) > size * 1.6:
            cut = max(p.rfind(c, 0, size) for c in "。；;！？\n")
            cut = cut if cut > size // 2 else size
            out.append((buf + p[:cut + 1]).strip())
            buf, p = "", p[cut + 1:]
        buf = (buf + "\n" + p).strip() if buf else p
    if buf:
        out.append(buf)
    return out


def front_matter(text: str):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip().strip('"')
    return meta, m.group(2)


def chunks_textbook(f: Path):
    meta, body = front_matter(f.read_text(encoding="utf8"))
    exp = meta.get("id", "") if meta.get("kind") == "exp" else ""
    loc_pages = meta.get("pages", "")
    parts = re.split(r"(?m)^(?=【[^】]{1,12}】)", body)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        m = re.match(r"【([^】]+)】", part)
        sec = m.group(1) if m else "正文"
        for piece in split_paragraphs(part):
            yield dict(corpus="textbook", source=meta.get("title", f.stem), exp=exp, locator=f"实验{exp}【{sec}】 p.{loc_pages}" if exp else f"{meta.get('title','')} p.{loc_pages}", text=piece)


def chunks_markdown(f: Path, corpus: str):
    meta, body = front_matter(f.read_text(encoding="utf8"))
    exp = meta.get("id", "")
    for part in re.split(r"(?m)^(?=## )", body):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"## (.+)", part)
        sec = m.group(1).strip() if m else "概述"
        for piece in split_paragraphs(part):
            yield dict(corpus=corpus, source=meta.get("title", f.stem), exp=exp, locator=f"{f.name} §{sec}", text=piece)


def chunks_literature(f: Path):
    import yaml
    for r in yaml.safe_load(f.read_text(encoding="utf8")) or []:
        au = ", ".join(r.get("authors", [])) + (" et al" if r.get("et_al") else "")
        text = f"{au}. {r['title']}. {r['journal']} {r['year']};{r.get('volume','')}({r.get('issue','')}):{r.get('pages','')}. " \
               f"关键词：{'、'.join(r.get('keywords', []))}。" + " ".join(r.get("key_points", []))
        yield dict(corpus="literature", source=r["id"], exp=",".join(r.get("experiments", [])), locator=f"DOI:{r.get('doi','')}", text=text)


def read_pdf(f: Path):
    pages: list[str] = []
    if shutil.which("pdftotext"):
        out = subprocess.run(["pdftotext", "-layout", str(f), "-"], capture_output=True, text=True, encoding="utf8", errors="ignore").stdout
        pages = out.split("\f")
    else:
        try:
            import fitz  # type: ignore
            pages = [pg.get_text() for pg in fitz.open(str(f))]
        except ImportError:
            print(f"! 无法读取 {f.name}：请安装 poppler(pdftotext) 或 pip install pymupdf", file=sys.stderr)
    return pages


def chunks_local(f: Path, tag: str):
    suf = f.suffix.lower()
    if suf == ".pdf":
        for i, pg in enumerate(read_pdf(f), 1):
            for piece in split_paragraphs(re.sub(r"[ \t]+", " ", pg)):
                yield dict(corpus=tag, source=f.stem, exp="", locator=f"p.{i}", text=piece)
    elif suf == ".docx":
        from docx import Document
        text = "\n\n".join(p.text for p in Document(str(f)).paragraphs if p.text.strip())
        for piece in split_paragraphs(text):
            yield dict(corpus=tag, source=f.stem, exp="", locator="docx", text=piece)
    elif suf in (".md", ".txt"):
        for piece in split_paragraphs(f.read_text(encoding="utf8", errors="ignore")):
            yield dict(corpus=tag, source=f.stem, exp="", locator=suf[1:], text=piece)


# ------------------------------------------------------------------ 建库
def build():
    docs: list[dict] = []
    for f in sorted((ROOT / "reference" / "textbook").glob("*.md")):
        docs += list(chunks_textbook(f))
    for f in sorted((ROOT / "knowledge" / "cards").glob("*.md")):
        docs += list(chunks_markdown(f, "card"))
    for f in sorted((ROOT / "knowledge" / "expressions").glob("*.md")):
        docs += list(chunks_markdown(f, "expr"))
    for f in sorted((ROOT / "knowledge" / "literature").glob("*.yaml")):
        docs += list(chunks_literature(f))
    if LOCAL.exists():
        for f in sorted(LOCAL.rglob("*")):
            if f.is_file() and f.suffix.lower() in (".pdf", ".docx", ".md", ".txt") and f.name.lower() != "readme.md":
                rel = f.relative_to(LOCAL).parts
                tag = rel[0] if len(rel) > 1 else "local"
                docs += list(chunks_local(f, tag))
    for i, d in enumerate(docs):
        d["id"] = i
        d["tok"] = Counter(tokens(d["text"]))
        d["len"] = sum(d["tok"].values())
    df: Counter = Counter()
    for d in docs:
        df.update(d["tok"].keys())
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps({"n": len(docs), "avg": sum(d["len"] for d in docs) / max(len(docs), 1), "df": df,
                                 "docs": [{**d, "tok": dict(d["tok"])} for d in docs]}, ensure_ascii=False), encoding="utf8")
    c = Counter(d["corpus"] for d in docs)
    print(f"✓ 索引 {len(docs)} 个片段 → {INDEX.relative_to(ROOT)}")
    for k, v in c.most_common():
        print(f"   {k:<12}{v}")
    if "textbook" not in c:
        print("   （没有 textbook 语料：先运行 python tools/kb.py build 你的教材.pdf）")


def load():
    if not INDEX.exists():
        build()
    return json.loads(INDEX.read_text(encoding="utf8"))


def search(query: str, k: int = 5, corpora: set[str] | None = None, exp: str | None = None, idx=None):
    idx = idx or load()
    q = Counter(tokens(query))
    n, avg, df = idx["n"], idx["avg"], idx["df"]
    res = []
    for d in idx["docs"]:
        if corpora and d["corpus"] not in corpora:
            continue
        if exp and exp not in d["exp"].split(","):
            continue
        s = 0.0
        for t in q:
            f = d["tok"].get(t)
            if not f:
                continue
            idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
            s += idf * f * 2.5 / (f + 1.5 * (0.25 + 0.75 * d["len"] / avg))
        if s > 0:
            res.append((s, d))
    res.sort(key=lambda x: -x[0])
    return res[:k]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("build")
    sp.add_parser("sources")
    s = sp.add_parser("search")
    s.add_argument("query", nargs="+")
    s.add_argument("-k", type=int, default=5)
    s.add_argument("-c", "--corpus", help="逗号分隔：textbook,card,expr,literature 或本地子目录名")
    s.add_argument("--exp", help="限定实验编号，如 2.7")
    s.add_argument("--full", action="store_true", help="输出整段而非摘要")
    s.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.cmd == "build":
        return build()
    idx = load()
    if a.cmd == "sources":
        c = Counter((d["corpus"], d["source"]) for d in idx["docs"])
        for (cp, src), v in sorted(c.items()):
            print(f"{cp:<12}{src}  ({v})")
        return
    res = search(" ".join(a.query), a.k, set(a.corpus.split(",")) if a.corpus else None, a.exp, idx)
    if a.json:
        print(json.dumps([{"score": round(s, 2), **{k: v for k, v in d.items() if k not in ("tok",)}} for s, d in res], ensure_ascii=False, indent=1))
        return
    if not res:
        print("没有检索到相关片段（换个关键词，或检查是否已 build / 放入语料）。")
    for i, (sc, d) in enumerate(res, 1):
        body = d["text"] if a.full else d["text"].replace("\n", " ")[:220] + ("…" if len(d["text"]) > 220 else "")
        print(f"[{i}] ({d['corpus']}) {d['source']} · {d['locator']}  score={sc:.1f}\n    {body}\n")


if __name__ == "__main__":
    main()
