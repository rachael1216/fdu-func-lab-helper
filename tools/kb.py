#!/usr/bin/env python3
"""kb.py — 本地教材索引（"轻量 RAG"，不含任何教材原文）

教材是有版权的，所以本仓库**不包含**教材内容。每位同学用自己手上的
《功能学科实验教程》PDF 在本机建一次索引，之后 AI（或你自己）就能按
"实验编号"精确查询教材原文、页码，用来写"实验方法""讨论""参考文献"。

为什么不用向量库：教材只有约 30 个实验，每个实验天然是一个独立章节，
"按编号精确取回"比语义检索更准、零依赖、不需要服务器、不需要嵌入模型。

用法
----
  python tools/kb.py build  功能学科实验教程.pdf      # 建索引 -> reference/textbook/
  python tools/kb.py list                              # 列出所有实验
  python tools/kb.py show 2.7                          # 打印实验 2.7 教材原文
  python tools/kb.py show 2.7 --section 思考题         # 只看某个栏目
  python tools/kb.py find 葡萄糖酸钙                   # 全书关键词检索（带页码）
  python tools/kb.py cite 2.7                          # 生成参考文献条目（含页码）
  python tools/kb.py tech                              # 列出"基本技术/仪器"章节
  python tools/kb.py show tech:3.4                     # 第三章第四节（麻醉方法）

仅依赖 Python 3.8+ 标准库；读取 PDF 时依次尝试 PyMuPDF、pdftotext、pypdf。
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB_DIR = ROOT / "reference" / "textbook"
BOOK = "《功能学科实验教程》（严钰锋，马淑兰 主编，2020）"

CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
SECTION_TAGS = ["目的", "原理", "实验对象", "动物", "药品与器材", "实验步骤", "观察项目",
                "注意事项", "思考题", "测定指标及方法", "结果处理", "附"]


# ----------------------------------------------------------------- PDF -> pages
def _pages_pymupdf(pdf: Path):
    import fitz  # type: ignore
    with fitz.open(pdf) as doc:
        return [p.get_text() for p in doc]


def _pages_pdftotext(pdf: Path):
    exe = shutil.which("pdftotext")
    if not exe:
        raise RuntimeError("no pdftotext")
    out = subprocess.run([exe, "-layout", str(pdf), "-"], capture_output=True, check=True).stdout
    return out.decode("utf8", "ignore").split("\f")


def _pages_pypdf(pdf: Path):
    from pypdf import PdfReader  # type: ignore
    return [(p.extract_text() or "") for p in PdfReader(str(pdf)).pages]


def read_pages(pdf: Path):
    errs = []
    # pdftotext -layout 的版面保持得最好，优先使用
    for fn in (_pages_pdftotext, _pages_pymupdf, _pages_pypdf):
        try:
            pages = fn(pdf)
            if sum(len(p) for p in pages) > 5000:
                return pages
        except Exception as e:  # noqa: BLE001
            errs.append(f"{fn.__name__}: {e}")
    sys.exit("读取 PDF 失败。请安装其一：pip install pymupdf  /  poppler(pdftotext)  /  pip install pypdf\n" + "\n".join(errs))


# ----------------------------------------------------------------- cleaning
HEADER_RE = re.compile(r"^\s*功\s*能\s*学\s*科\s*实\s*验\s*教\s*程\s*$")
PAGEMARK_RE = re.compile(r"^\s*[—\-–]{2,}\s*(\d{1,3})?\s*[—\-–]{0,}\s*$")
EXP_RE = re.compile(r"^\s*实验\s*(\d{1,2})\s*[.．]\s*(\d{1,2})\s+(\S.*?)\s*$")
CH_RE = re.compile(r"^\s*第\s*([一二三四五六七八九])\s*章\s*(\S.*?)\s*$")
SEC_RE = re.compile(r"^\s*第\s*([一二三四五六七八九十]+)\s*节\s*(\S.*?)\s*$")
NEWPARA_RE = re.compile(r"^\s*([【（(]|[0-9]+\s*[．.、]|[①-⑳⑴-⒇]|图\s*\d|表\s*\d|\[|[a-zA-Z]\s*[．.]\s|[-•·]\s)")
END_PUNCT = "。；：！？.;:!?）)】”"


def squeeze_cjk(s: str) -> str:
    """去掉汉字之间多余的空格（"缺   氧" -> "缺氧"）。"""
    return re.sub(r"(?<=[一-鿿])\s+(?=[一-鿿])", "", s)


def clean_page(text: str):
    lines = []
    printed = None
    for raw in text.splitlines():
        s = raw.strip()
        if not s or HEADER_RE.match(s):
            continue
        m = PAGEMARK_RE.match(s)
        if m:
            if m.group(1):
                printed = int(m.group(1))
            continue
        if s in {"——", "—"}:
            continue
        lines.append(s)
    return lines, printed


def join_paragraphs(lines):
    out, buf = [], ""
    for ln in lines:
        if not buf:
            buf = ln
            continue
        if NEWPARA_RE.match(ln) or buf[-1] in END_PUNCT:
            out.append(buf)
            buf = ln
        else:
            if re.search(r"[A-Za-z0-9]$", buf) and re.match(r"[A-Za-z0-9]", ln):
                buf += " " + ln
            else:
                buf += ln
    if buf:
        out.append(buf)
    return out


# ----------------------------------------------------------------- build
def build(pdf: Path, out: Path = KB_DIR):
    pages = read_pages(pdf)
    # (page_no, line) 流；只保留正文（第六章"附录"之前，避免与书末目录重复）
    stream = []
    for i, pg in enumerate(pages, start=1):
        lines, printed = clean_page(pg)
        no = printed or i
        for ln in lines:
            stream.append((no, ln))
    cut = next((k for k, (_, ln) in enumerate(stream) if re.match(r"^第\s*六\s*章\s*附\s*录", squeeze_cjk(ln))), len(stream))
    stream = stream[:cut]

    # 标出标题位置
    marks = []  # (idx, kind, key, title, page)
    chapter = None
    for k, (pg, ln) in enumerate(stream):
        s = squeeze_cjk(ln)
        mc = CH_RE.match(s)
        if mc and "…" not in s:
            chapter = CN_NUM[mc.group(1)]
            marks.append((k, "chapter", str(chapter), mc.group(2), pg))
            continue
        me = EXP_RE.match(s)
        if me and "…" not in s and chapter == 5:
            # 真标题后 8 行内一定出现【目的】/【原理】等栏目；引用句（"同实验 2.1"）不会
            look = " ".join(x for _, x in stream[k + 1:k + 9])
            if "【" in look and not s.startswith("实验" + me.group(1) + "." + me.group(2) + "）"):
                key = f"{me.group(1)}.{me.group(2)}"
                if not any(m[1] == "exp" and m[2] == key for m in marks):
                    marks.append((k, "exp", key, me.group(3), pg))
            continue
        ms = SEC_RE.match(s)
        if ms and chapter in (1, 2, 3, 4) and "…" not in s:
            key = f"{chapter}.{CN_NUM.get(ms.group(1), 0)}"
            if not any(m[1] == "tech" and m[2] == key for m in marks):
                marks.append((k, "tech", key, ms.group(2), pg))

    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.md"):
        old.unlink()
    index = {"book": BOOK, "source_pdf": pdf.name, "experiments": [], "tech": []}
    boundaries = sorted(m[0] for m in marks if m[1] in ("exp", "tech", "chapter")) + [len(stream)]
    for m in marks:
        if m[1] == "chapter":
            continue
        k, kind, key, title, pg = m
        end = next(b for b in boundaries if b > k)
        seg = stream[k:end]
        body = join_paragraphs([ln for _, ln in seg[1:]])
        p_start, p_end = seg[0][0], seg[-1][0]
        title = re.sub(r"\s+", "", title)
        fname = f"ex_{key}.md" if kind == "exp" else f"tech_{key}.md"
        head = f"---\nid: {key}\nkind: {kind}\ntitle: {title}\npages: {p_start}-{p_end}\nbook: {BOOK}\n---\n\n"
        label = f"实验 {key}　{title}" if kind == "exp" else f"{key}　{title}"
        text = head + f"# {label}\n\n" + "\n\n".join(body) + "\n"
        (out / fname).write_text(text, encoding="utf8")
        rec = {"id": key, "title": title, "pages": [p_start, p_end], "file": fname}
        index["experiments" if kind == "exp" else "tech"].append(rec)

    def sort_key(r):
        return [int(x) for x in r["id"].split(".")]
    index["experiments"].sort(key=sort_key)
    index["tech"].sort(key=sort_key)
    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf8")
    print(f"✓ 已建立索引：{len(index['experiments'])} 个实验，{len(index['tech'])} 个技术/仪器章节 -> {out}")
    if len(index["experiments"]) < 25:
        print("! 实验数量偏少（预期约 30 个），请检查 PDF 是否为完整教材/是否扫描版。", file=sys.stderr)


# ----------------------------------------------------------------- query
def load_index():
    f = KB_DIR / "index.json"
    if not f.exists():
        sys.exit("还没有建索引。先运行：python tools/kb.py build 功能学科实验教程.pdf")
    return json.loads(f.read_text(encoding="utf8"))


def resolve(ref: str, idx):
    tech = ref.startswith("tech:")
    key = ref.split(":", 1)[1] if tech else ref
    pool = idx["tech"] if tech else idx["experiments"]
    hit = next((r for r in pool if r["id"] == key), None)
    if not hit:
        sys.exit(f"找不到 {ref}。可用 `python tools/kb.py list` 查看。")
    return hit


def cmd_list(_):
    idx = load_index()
    print(f"{idx['book']}\n")
    for r in idx["experiments"]:
        print(f"  实验 {r['id']:<5} {r['title']}  (p.{r['pages'][0]}-{r['pages'][1]})")


def cmd_tech(_):
    idx = load_index()
    for r in idx["tech"]:
        print(f"  tech:{r['id']:<5} {r['title']}  (p.{r['pages'][0]}-{r['pages'][1]})")


def cmd_show(a):
    idx = load_index()
    r = resolve(a.ref, idx)
    text = (KB_DIR / r["file"]).read_text(encoding="utf8")
    if a.section:
        m = re.search(r"(【%s】.*?)(?=\n\n【|\Z)" % re.escape(a.section), text, re.S)
        if not m:
            sys.exit(f"没有找到栏目【{a.section}】。常见栏目：{'、'.join(SECTION_TAGS)}")
        text = m.group(1)
    print(text)


def cmd_find(a):
    idx = load_index()
    n = 0
    for r in idx["experiments"] + idx["tech"]:
        txt = (KB_DIR / r["file"]).read_text(encoding="utf8")
        for para in txt.split("\n\n"):
            if a.keyword in para:
                n += 1
                tag = f"实验{r['id']}" if r in idx["experiments"] else f"tech:{r['id']}"
                snippet = para.replace("\n", " ")
                pos = snippet.find(a.keyword)
                lo = max(0, pos - 40)
                print(f"[{tag} {r['title']} p.{r['pages'][0]}-{r['pages'][1]}] …{snippet[lo:pos + 80]}…")
                if n >= a.limit:
                    return
    if n == 0:
        print("没有命中。")


def cmd_cite(a):
    idx = load_index()
    r = resolve(a.ref, idx)
    lab = f"实验{r['id']} {r['title']}" if not a.ref.startswith("tech:") else f"{r['id']} {r['title']}"
    print(f"{idx['book']}. {lab}：{r['pages'][0]}–{r['pages'][1]}.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    b = sp.add_parser("build", help="从教材 PDF 建本地索引")
    b.add_argument("pdf", type=Path)
    b.add_argument("-o", "--out", type=Path, default=KB_DIR)
    b.set_defaults(fn=lambda a: build(a.pdf, a.out))
    sp.add_parser("list", help="列出所有实验").set_defaults(fn=cmd_list)
    sp.add_parser("tech", help="列出基本技术/仪器章节").set_defaults(fn=cmd_tech)
    s = sp.add_parser("show", help="显示某实验教材原文")
    s.add_argument("ref", help="实验编号如 2.7；技术章节用 tech:3.4")
    s.add_argument("--section", help="只显示某栏目，如 思考题 / 实验步骤")
    s.set_defaults(fn=cmd_show)
    f = sp.add_parser("find", help="全书关键词检索")
    f.add_argument("keyword")
    f.add_argument("--limit", type=int, default=20)
    f.set_defaults(fn=cmd_find)
    c = sp.add_parser("cite", help="生成参考文献条目（含页码）")
    c.add_argument("ref")
    c.set_defaults(fn=cmd_cite)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
