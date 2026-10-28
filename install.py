#!/usr/bin/env python3
"""install.py — 一键安装 fdu-lab（MCP 服务 + 12 个 skill + 本地 RAG 索引）。

  python install.py                         安装依赖、建索引、自检，并打印 MCP 配置
  python install.py --write ~/.claude.json  把 fdu-lab 写入指定的 MCP 配置文件（JSON，合并 mcpServers）
  python install.py --skills                另把 12 个 skill 复制到 ~/.agents/skills 与 ~/.dsh/skills
  python install.py --no-pip                跳过 pip install
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SERVER = ROOT / "mcp_server" / "server.py"


def sh(*cmd, quiet=False):
    return subprocess.run(cmd, cwd=ROOT, capture_output=quiet, text=True)


def self_test() -> bool:
    msgs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "prompts/list"}]
    p = subprocess.run([sys.executable, str(SERVER)], input="\n".join(map(json.dumps, msgs)) + "\n", capture_output=True, text=True, timeout=120)
    out = [json.loads(x) for x in p.stdout.splitlines() if x.strip()]
    ok = len(out) == 3 and len(out[1]["result"]["tools"]) >= 10 and len(out[2]["result"]["prompts"]) >= 13
    print(("✓" if ok else "✗"), f"MCP 自检：{len(out[1]['result']['tools'])} 个工具，{len(out[2]['result']['prompts'])} 个 prompt（菜单 + skill）" if ok else "MCP 自检失败")
    return ok


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", type=Path)
    ap.add_argument("--skills", action="store_true")
    ap.add_argument("--no-pip", action="store_true")
    a = ap.parse_args()

    if sys.version_info < (3, 10):
        sys.exit("需要 Python ≥ 3.10")
    if not a.no_pip:
        print("→ 安装依赖")
        sh(sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt")
    print("→ 建立本地 RAG 索引")
    sh(sys.executable, "tools/rag.py", "build")
    ok = self_test()

    entry = {"command": sys.executable, "args": [str(SERVER)]}
    if a.write:
        cfg = json.loads(a.write.read_text(encoding="utf8")) if a.write.exists() else {}
        cfg.setdefault("mcpServers", {})["fdu-lab"] = entry
        a.write.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf8")
        print("✓ 已写入", a.write)
    if a.skills:
        for d in (Path.home() / ".agents" / "skills", Path.home() / ".dsh" / "skills"):
            for s in sorted((ROOT / ".agents" / "skills").iterdir()):
                if s.is_dir():
                    d.mkdir(parents=True, exist_ok=True)
                    shutil.copytree(s, d / s.name, dirs_exist_ok=True)
            print("✓ skill →", d)
    print("\n在你的 MCP 客户端中加入以下服务（stdio）：")
    print(json.dumps({"mcpServers": {"fdu-lab": entry}}, ensure_ascii=False, indent=2))
    print(f"\nClaude Code：claude mcp add fdu-lab -- {sys.executable} {SERVER}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
