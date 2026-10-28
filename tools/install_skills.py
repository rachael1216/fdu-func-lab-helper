#!/usr/bin/env python3
"""install_skills.py — 把 .agents/skills 下的全部 skill 安装到 DeepSeek Harness / 通用 agent 的全局目录。

  python tools/install_skills.py            # 安装到 ~/.dsh/skills 与 ~/.agents/skills
  python tools/install_skills.py --dest ~/.claude/skills
  python tools/install_skills.py --uninstall

在仓库目录里直接启动 dsh 时不需要安装（项目内 .agents/skills 会被自动发现）。
全局安装适合“在别的目录也想用”的情况；注意 skill 里的命令用相对路径 tools/…，需要在仓库根目录下运行。
"""
import argparse
import shutil
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / ".agents" / "skills"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", action="append", type=Path)
    ap.add_argument("--uninstall", action="store_true")
    a = ap.parse_args()
    dests = a.dest or [Path.home() / ".dsh" / "skills", Path.home() / ".agents" / "skills"]
    for d in dests:
        for s in sorted(SRC.iterdir()):
            if not s.is_dir():
                continue
            t = d / s.name
            if a.uninstall:
                shutil.rmtree(t, ignore_errors=True)
                print("removed", t)
            else:
                d.mkdir(parents=True, exist_ok=True)
                shutil.copytree(s, t, dirs_exist_ok=True)
                print("✓", t)


if __name__ == "__main__":
    main()
