#!/usr/bin/env python3
"""fdu-lab MCP server（stdio，仅依赖标准库）。

把本项目的三部分封装为一个 MCP 服务：
  Prompts   总菜单 + 12 个 skill（prompts/list、prompts/get）
  Tools     本地 RAG 检索、计算、统计、质反应分析、作图、语言检查、文献核对、排版（tools/call）
  Resources 菜单、格式规范、文献目录、各 skill 原文（resources/read）

运行：python mcp_server/server.py     （由 MCP 客户端以 stdio 方式启动，工作目录无关）
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".agents" / "skills"
PROTOCOL = "2024-11-05"
VERSION = "0.3.0"

CLI_NOTE = (
    "【MCP 对应关系】skill 正文里的命令行写法在本环境改用同名 MCP 工具：\n"
    "tools/rag.py → rag_search / rag_sources；tools/labcalc.py → lab_calc；tools/labstats.py → lab_stats；\n"
    "tools/labdose.py → lab_dose；tools/labplot.py → lab_plot；tools/stylecheck.py → style_check；\n"
    "tools/styleprofile.py → style_profile；tools/refcheck.py → ref_check / ref_format；tools/build.py → build_report。\n\n"
)


# ------------------------------------------------------------------ 运行工具
def run(script: str, args: list[str], timeout: int = 180) -> tuple[int, str]:
    p = subprocess.run([sys.executable, "-X", "utf8", str(ROOT / "tools" / script), *map(str, args)], cwd=ROOT,
                       capture_output=True, text=True, timeout=timeout, encoding="utf8", errors="replace")
    return p.returncode, (p.stdout + (("\n" + p.stderr) if p.stderr.strip() else "")).strip()


def ensure_index() -> None:
    if not (ROOT / "corpus" / "index" / "rag.json").exists():
        run("rag.py", ["build"], 600)


def as_file(text: str | None, path: str | None) -> str:
    if path:
        return path
    if not text:
        raise ValueError("需要 text 或 path")
    f = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf8")
    f.write(text)
    f.close()
    return f.name


def skill_names() -> list[str]:
    return sorted(d.name for d in SKILLS.iterdir() if (d / "SKILL.md").exists())


def skill_text(name: str) -> str:
    f = SKILLS / name / "SKILL.md"
    if not f.exists():
        raise ValueError(f"没有这个 skill：{name}。可用：{', '.join(skill_names())}")
    return f.read_text(encoding="utf8")


def skill_desc(name: str) -> str:
    m = re.search(r"(?m)^description:\s*(.+)$", skill_text(name))
    return m.group(1).strip() if m else name


# ------------------------------------------------------------------ 工具定义
S = {"type": "string"}
ARGS = {"type": "array", "items": S, "description": "命令行参数，与对应 tools/*.py 的用法一致"}


def obj(props: dict, req: list[str] | None = None) -> dict:
    return {"type": "object", "properties": props, "required": req or []}


def t_rag_search(a):
    ensure_index()
    args = ["search", *a["query"].split(), "-k", str(a.get("k", 5))]
    if a.get("corpus"):
        args += ["-c", a["corpus"]]
    if a.get("exp"):
        args += ["--exp", str(a["exp"])]
    if a.get("full"):
        args.append("--full")
    return run("rag.py", args)


def t_rag_sources(_):
    ensure_index()
    return run("rag.py", ["sources"])


def t_style(script):
    def f(a):
        ensure_index()
        sub = ["compare"] if script == "styleprofile.py" else []
        args = [*sub, as_file(a.get("text"), a.get("path"))]
        if a.get("exp"):
            args += ["--exp", str(a["exp"])]
        return run(script, args)
    return f


def t_ref_check(a):
    args = [as_file(a.get("text"), a.get("path"))]
    if a.get("offline"):
        args.append("--offline")
    return run("refcheck.py", args)


def t_build(a):
    args = [a["path"], "--to", a.get("to", "docx")]
    if a.get("animal"):
        args += ["--animal", a["animal"]]
    if a.get("outdir"):
        args += ["-o", a["outdir"]]
    return run("build.py", args, 600)


TOOLS = {
    "fdu_lab_menu": ("展示 12 项功能总菜单（新会话先调用它）。", obj({}), lambda a: (0, (ROOT / "prompts" / "menu.md").read_text(encoding="utf8"))),
    "fdu_lab_skill": ("读取一个 skill 的完整指令；不给 name 则列出全部 skill。", obj({"name": S}),
                      lambda a: (0, skill_text(a["name"]) if a.get("name") else "\n".join(f"- {n}：{skill_desc(n)}" for n in skill_names()))),
    "rag_search": ("检索课本、讲义、课本表述、知识卡与重点文献（BM25，返回片段与出处页码）。corpus 可选 textbook/lecture/expr/card/literature；exp 为实验编号如 2.7。",
                   obj({"query": {"type": "string", "description": "2–4 个关键词，空格分隔"}, "k": {"type": "integer"}, "corpus": S, "exp": S, "full": {"type": "boolean"}}, ["query"]), t_rag_search),
    "rag_sources": ("列出已入库的语料及片段数。", obj({}), t_rag_sources),
    "lab_calc": ("实验计算：dose backdose conc ld50 ti ache lung stats change map hr 等子命令。例：[\"dose\",\"--weight\",\"2.5\",\"--dose\",\"1000\",\"--conc\",\"20\"]。",
                 obj({"args": ARGS}, ["args"]), lambda a: run("labcalc.py", a["args"])),
    "lab_stats": ("统计检验：ttest anova 回归等，自动检查 n 与前提。", obj({"args": ARGS}, ["args"]), lambda a: run("labstats.py", a["args"])),
    "lab_dose": ("质反应分析：改良寇氏法 LD50、Probit/Logit、似然剖面区间、拟合优度、bootstrap、留一法与作图。",
                 obj({"args": ARGS}, ["args"]), lambda a: run("labdose.py", a["args"])),
    "lab_plot": ("规范作图（bar/line/scatter 等，色盲友好调色，输出建议图注）。", obj({"args": ARGS}, ["args"]), lambda a: run("labplot.py", a["args"])),
    "style_check": ("语言检查：课本术语覆盖、口语与模板腔、逐句与课本的相似度、格式细节。", obj({"text": S, "path": S, "exp": S}), t_style("stylecheck.py")),
    "style_profile": ("课本文风画像对照：句长、逗号密度、连接词、句首、该实验可采用的课本搭配。", obj({"text": S, "path": S, "exp": S}), t_style("styleprofile.py")),
    "ref_check": ("参考文献核对：DOI/题名/第一作者/年份/卷页对照 Crossref（offline 仅对登记表）。", obj({"text": S, "path": S, "offline": {"type": "boolean"}}), t_ref_check),
    "ref_format": ("由 DOI 生成 GB/T 7714 条目。", obj({"doi": S}, ["doi"]), lambda a: run("refcheck.py", ["fmt", a["doi"]])),
    "build_report": ("把 report.md 排版为 docx / tex / pdf（封面、目录、页眉、页码）。", obj({"path": S, "to": {"type": "string", "enum": ["docx", "tex", "pdf", "all"]}, "animal": S, "outdir": S}, ["path"]), t_build),
}

RESOURCES = {
    "fdu-lab://menu": ("总菜单", ROOT / "prompts" / "menu.md"),
    "fdu-lab://format": ("格式规范", ROOT / "templates" / "FORMAT.md"),
    "fdu-lab://references": ("重点文献目录", ROOT / "reference" / "literature" / "README.md"),
}


# ------------------------------------------------------------------ 协议
def reply(i, result=None, error=None):
    m = {"jsonrpc": "2.0", "id": i}
    if error:
        m["error"] = error
    else:
        m["result"] = result
    sys.stdout.write(json.dumps(m, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def handle(m: dict):
    method, i, p = m.get("method"), m.get("id"), m.get("params") or {}
    if i is None:  # 通知
        return
    try:
        if method == "initialize":
            reply(i, {"protocolVersion": p.get("protocolVersion", PROTOCOL),
                      "capabilities": {"tools": {}, "prompts": {}, "resources": {}},
                      "serverInfo": {"name": "fdu-lab", "version": VERSION},
                      "instructions": "复旦《功能学科综合实验》报告写作助手。新会话先调用 fdu_lab_menu 展示菜单；写作前用 rag_search 取课本表述；数字、检验、引用由工具产出。"})
        elif method == "ping":
            reply(i, {})
        elif method == "tools/list":
            reply(i, {"tools": [{"name": n, "description": d, "inputSchema": s} for n, (d, s, _) in TOOLS.items()]})
        elif method == "tools/call":
            name, args = p.get("name"), p.get("arguments") or {}
            if name not in TOOLS:
                return reply(i, error={"code": -32602, "message": f"未知工具 {name}"})
            try:
                rc, out = TOOLS[name][2](args)
                reply(i, {"content": [{"type": "text", "text": out or "(无输出)"}], "isError": rc != 0})
            except Exception as e:  # noqa: BLE001
                reply(i, {"content": [{"type": "text", "text": f"{type(e).__name__}: {e}"}], "isError": True})
        elif method == "prompts/list":
            ps = [{"name": "menu", "description": "总菜单：12 项功能与路由"}]
            ps += [{"name": n, "description": skill_desc(n)} for n in skill_names()]
            reply(i, {"prompts": ps})
        elif method == "prompts/get":
            name = p.get("name")
            body = (ROOT / "prompts" / "menu.md").read_text(encoding="utf8") if name == "menu" else skill_text(name)
            reply(i, {"description": name, "messages": [{"role": "user", "content": {"type": "text", "text": CLI_NOTE + body}}]})
        elif method == "resources/list":
            rs = [{"uri": u, "name": n, "mimeType": "text/markdown"} for u, (n, _) in RESOURCES.items()]
            rs += [{"uri": f"fdu-lab://skill/{n}", "name": n, "mimeType": "text/markdown"} for n in skill_names()]
            reply(i, {"resources": rs})
        elif method == "resources/read":
            uri = p.get("uri", "")
            if uri in RESOURCES:
                text = RESOURCES[uri][1].read_text(encoding="utf8")
            elif uri.startswith("fdu-lab://skill/"):
                text = skill_text(uri.rsplit("/", 1)[1])
            else:
                return reply(i, error={"code": -32602, "message": f"未知资源 {uri}"})
            reply(i, {"contents": [{"uri": uri, "mimeType": "text/markdown", "text": text}]})
        else:
            reply(i, error={"code": -32601, "message": f"未实现 {method}"})
    except Exception as e:  # noqa: BLE001
        reply(i, error={"code": -32603, "message": f"{type(e).__name__}: {e}"})


def main():
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    for line in sys.stdin:
        line = line.strip()
        if line:
            try:
                handle(json.loads(line))
            except json.JSONDecodeError:
                reply(None, error={"code": -32700, "message": "parse error"})


if __name__ == "__main__":
    main()
