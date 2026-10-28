#!/usr/bin/env python3
"""build.py — 把一份 Markdown 实验报告一键变成「封面 + 目录 + 正文」的 Word / LaTeX / PDF

  python tools/build.py reports/高钾血症/report.md              # 默认生成 .docx
  python tools/build.py reports/高钾血症/report.md --to all     # docx + tex + pdf
  python tools/build.py report.md --to pdf --animal mouse      # 换封面线稿
  python tools/build.py --doctor                                # 检查环境是否齐全

report.md 的开头是 YAML 头（封面和页眉用）：

  ---
  title: 家兔高钾血症实验报告
  course: 功能学科综合实验
  exp_no: "2.7"
  class: 23 临床医学五年制
  student: 张三
  student_id: "23301050000"
  group: 第 3 组
  date: 2025.11.13
  teacher: 某某老师
  animal: rabbit           # 封面线稿：rabbit / mouse
  ai_statement: ""         # 可选：AI 使用说明（按课程要求填写，非空则附在文末）
  ---

依赖：pandoc（或 pip install pypandoc_binary）、python-docx、pyyaml；PDF 另需 XeLaTeX（含 ctex）。
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF_DOCX = ROOT / "templates" / "word" / "reference.docx"
TEX_TEMPLATE = ROOT / "templates" / "latex" / "pandoc-fdulab.latex"
COVER_DIR = ROOT / "assets" / "cover"
ANIMALS = ["rabbit", "mouse"]
DEFAULTS = {"course": "功能学科综合实验", "animal": "rabbit"}

# ------------------------------------------------------------------ 环境
def find_pandoc() -> str:
    exe = shutil.which("pandoc")
    if exe:
        return exe
    try:
        import pypandoc  # type: ignore
        return pypandoc.get_pandoc_path()
    except Exception:  # noqa: BLE001
        sys.exit("找不到 pandoc。安装方法：Windows `winget install JohnMacFarlane.Pandoc`；macOS `brew install pandoc`；"
                 "或 `pip install pypandoc_binary`。详见 docs/GUIDE.md")


def doctor():
    ok = True

    def line(name, good, hint=""):
        nonlocal ok
        print(("✓" if good else "✗"), name, "" if good else f"  → {hint}")
        ok = ok and good
    try:
        exe = find_pandoc()
        ver = subprocess.run([exe, "--version"], capture_output=True, text=True).stdout.splitlines()[0]
        line(f"pandoc ({ver})", True)
    except SystemExit as e:
        line("pandoc", False, str(e))
    for mod, pipname in (("docx", "python-docx"), ("yaml", "pyyaml")):
        try:
            __import__(mod)
            line(pipname, True)
        except ImportError:
            line(pipname, False, f"pip install {pipname}")
    line("Word 样式母版 templates/word/reference.docx", REF_DOCX.exists(), "python tools/make_reference_docx.py")
    line("封面线稿 assets/cover/", any(COVER_DIR.glob("*.png")), "python tools/make_cover.py")
    xe = shutil.which("xelatex")
    print(("✓" if xe else "–"), "xelatex（仅生成 PDF/tex 需要）", "" if xe else "→ 安装 TeX Live/MiKTeX，或用 Overleaf；只要 Word 可忽略")
    print("\n环境 OK，可以开始。" if ok else "\n请先按提示补齐 ✗ 项。")
    return ok


# ------------------------------------------------------------------ 读取 md
def split_front(text: str):
    import yaml
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m:
        return {}, text
    meta = yaml.safe_load(m.group(1)) or {}
    return {k: ("" if v is None else str(v)) for k, v in meta.items()}, m.group(2)


def norm_meta(meta: dict) -> dict:
    out = dict(DEFAULTS)
    out.update({k: v for k, v in meta.items() if v != ""})
    for k in ("title", "student", "student_id", "class", "group", "date", "teacher", "exp_no", "ai_statement"):
        out.setdefault(k, "")
    if out["animal"] not in ANIMALS:
        print(f"! 未知封面动物 {out['animal']}，改用 rabbit（可选：{', '.join(ANIMALS)}）", file=sys.stderr)
        out["animal"] = "rabbit"
    return out


def asset(animal: str, kind: str) -> Path:
    """kind: '' → 封面大图 png；'pdf' → 矢量；'icon' → 页眉小图标"""
    name = {"": f"{animal}.png", "pdf": f"{animal}.pdf", "icon": f"{animal}_icon.png"}[kind]
    p = COVER_DIR / name
    if not p.exists():
        sys.path.insert(0, str(ROOT / "tools"))
        import make_cover  # type: ignore
        make_cover.render(animal)
    return p


def ai_block(meta: dict) -> str:
    return f'\n\n> **AI 使用说明**　{meta["ai_statement"]}\n' if meta.get("ai_statement") else ""


# ------------------------------------------------------------------ DOCX
def run_pandoc(args):
    r = subprocess.run([find_pandoc()] + args, capture_output=True, text=True, encoding="utf8")
    if r.returncode != 0:
        sys.exit("pandoc 出错：\n" + r.stderr)
    if r.stderr.strip():
        print(r.stderr.strip(), file=sys.stderr)


def build_docx(meta: dict, body: str, out: Path, cover: bool = True):
    from docx import Document
    sys.path.insert(0, str(ROOT / "tools"))
    import docx_cover  # type: ignore
    if not REF_DOCX.exists():
        sys.exit("缺少 templates/word/reference.docx，请先运行 python tools/make_reference_docx.py")
    with tempfile.TemporaryDirectory() as td:
        md = Path(td) / "body.md"
        md.write_text(body + ai_block(meta), encoding="utf8")
        tmp = Path(td) / "body.docx"
        run_pandoc(["-f", "markdown+smart-smart", "-t", "docx", f"--reference-doc={REF_DOCX}", "--toc", "--toc-depth=2",
                    "--number-sections", "-M", "toc-title=目 录", "--resource-path", f"{out.parent}:{ROOT}",
                    "-o", str(tmp), str(md)])
        doc = Document(str(tmp))
    docx_cover.style_tables(doc)
    docx_cover.build_front(doc, meta, asset(meta["animal"], ""), cover)
    docx_cover.fill_header(doc, meta["course"] + "实验报告", meta["student_id"] or meta["student"], asset(meta["animal"], "icon"))
    docx_cover.update_fields_on_open(doc)
    doc.core_properties.title = meta["title"]
    doc.core_properties.author = meta["student"]
    doc.save(str(out))
    return out


# ------------------------------------------------------------------ TEX / PDF
SUP = dict(zip("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻", "0123456789+-"))
SUB = dict(zip("₀₁₂₃₄₅₆₇₈₉₊₋", "0123456789+-"))


def tex_safe(body: str) -> str:
    """把 Unicode 上下标（Ca²⁺、H₂O）换成 \\textsuperscript/\\textsubscript，避免字体缺字。"""
    def conv(chars, table, cmd):
        return "\\" + cmd + "{" + "".join(table[c] for c in chars) + "}"
    body = re.sub("[" + "".join(SUP) + "]+", lambda m: conv(m.group(0), SUP, "textsuperscript"), body)
    body = re.sub("[" + "".join(SUB) + "]+", lambda m: conv(m.group(0), SUB, "textsubscript"), body)
    return body


def build_tex(meta: dict, body: str, out: Path, cover: bool = True):
    import yaml
    out.parent.mkdir(parents=True, exist_ok=True)
    cls = ROOT / "templates" / "latex" / "fdureport.cls"
    for src, name in ((asset(meta["animal"], "pdf"), "cover.pdf"), (asset(meta["animal"], "icon"), "icon.png"), (cls, "fdureport.cls")):
        dst = out.parent / name
        if src.resolve() != dst.resolve():
            shutil.copy(src, dst)
    m = dict(meta)
    m["coverimage"], m["iconimage"] = "cover.pdf", "icon.png"
    m["nocover"] = not cover
    with tempfile.TemporaryDirectory() as td:
        mf = Path(td) / "meta.yaml"
        mf.write_text(yaml.safe_dump(m, allow_unicode=True), encoding="utf8")
        md = Path(td) / "body.md"
        md.write_text(tex_safe(body + ai_block(meta)), encoding="utf8")
        run_pandoc(["-f", "markdown+smart-smart", "-t", "latex", "--template", str(TEX_TEMPLATE), "--metadata-file", str(mf),
                    "--resource-path", f"{out.parent}:{ROOT}", "-o", str(out), str(md)])
    return out


def build_pdf(tex: Path):
    xe = shutil.which("xelatex")
    if not xe:
        sys.exit("没有找到 xelatex。请安装 TeX Live / MiKTeX（需含 ctex），或把 .tex、fdureport.cls 与封面图一起上传到 Overleaf（选 XeLaTeX 编译）。")
    for _ in range(2):  # 两遍：生成目录
        r = subprocess.run([xe, "-interaction=nonstopmode", "-halt-on-error", tex.name], cwd=tex.parent, capture_output=True, text=True, encoding="utf8", errors="ignore")
        if r.returncode != 0:
            log = tex.parent / (tex.stem + ".log")
            tail = log.read_text(encoding="utf8", errors="ignore")[-1800:] if log.exists() else r.stdout[-1800:]
            sys.exit("XeLaTeX 编译失败，日志末尾：\n" + tail)
    for ext in (".aux", ".out", ".toc"):
        (tex.parent / (tex.stem + ext)).unlink(missing_ok=True)
    return tex.with_suffix(".pdf")


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("md", nargs="?", type=Path)
    ap.add_argument("--to", choices=["docx", "tex", "pdf", "all"], default="docx")
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--no-cover", action="store_true")
    ap.add_argument("-o", "--outdir", type=Path)
    ap.add_argument("--doctor", action="store_true")
    a = ap.parse_args()
    if a.doctor:
        sys.exit(0 if doctor() else 1)
    if not a.md:
        ap.error("请给出 report.md 路径（或用 --doctor 检查环境）")
    meta, body = split_front(a.md.read_text(encoding="utf8"))
    meta = norm_meta(meta)
    if a.animal:
        meta["animal"] = a.animal
    outdir = a.outdir or a.md.parent
    outdir.mkdir(parents=True, exist_ok=True)
    stem = a.md.stem
    made = []
    if a.to in ("docx", "all"):
        made.append(build_docx(meta, body, outdir / f"{stem}.docx", not a.no_cover))
    if a.to in ("tex", "pdf", "all"):
        tex = build_tex(meta, body, outdir / f"{stem}.tex", not a.no_cover)
        made.append(tex)
        if a.to in ("pdf", "all"):
            made.append(build_pdf(tex))
    for p in made:
        print("✓", p)


if __name__ == "__main__":
    main()
