#!/usr/bin/env python3
"""render_tex.py — 编译 LaTeX 模板，生成预览 PDF：templates/latex/report-template.pdf。

有 ctex 时直接用 ctex；没有时用 tests/shim/ctexart.cls 兼容层（仅用于生成预览）。
  python tools/dev/render_tex.py
"""
import os
import shutil
import subprocess
import subprocess as sp
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "templates" / "latex"


def has_ctex() -> bool:
    r = sp.run(["kpsewhich", "ctexart.cls"], capture_output=True, text=True)
    return bool(r.stdout.strip())


def main():
    env = dict(os.environ)
    if not has_ctex():
        env["TEXINPUTS"] = str(ROOT / "tests" / "shim") + os.pathsep + env.get("TEXINPUTS", "")
        print("! 未找到 ctex，使用兼容层编译预览")
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        for f in ("fdureport.cls", "report-template.tex", "icon.png"):
            shutil.copy(SRC / f, t / f)
        shutil.copy(ROOT / "templates" / "cover" / "rabbit.pdf", t / "cover.pdf")
        for _ in range(2):
            subprocess.run(["xelatex", "-interaction=nonstopmode", "report-template.tex"], cwd=t, env=env, capture_output=True)
        shutil.copy(t / "report-template.pdf", SRC / "report-template.pdf")
    print("✓", SRC / "report-template.pdf")


if __name__ == "__main__":
    main()
