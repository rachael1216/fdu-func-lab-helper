#!/usr/bin/env python3
"""make_arch.py — 生成工程式架构图 assets/readme/architecture.svg（以及 png 预览）。"""
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
SAGE, SAGE_D, SAGE_L = "#5F7568", "#3F5548", "#E8EEE9"
BLUE, BLUE_L = "#4A6A8A", "#E6EDF4"
SAND, SAND_L = "#A67C52", "#F5EDE3"
ROSE, ROSE_L = "#9A5B5B", "#F6E9E9"
INK, GREY = "#1F2933", "#5B6670"
o = []
a = o.append


def rect(x, y, w, h, fill, stroke, r=8, sw=1.2, extra=""):
    a(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')


def text(x, y, s, size=12, fill=INK, weight=400, anchor="middle", extra=""):
    a(f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}" {extra}>{s}</text>')


def chip(x, y, w, h, title, sub, fill, stroke, tcol=INK):
    rect(x, y, w, h, fill, stroke, 7, 1.1, 'filter="url(#sh)"')
    text(x + w / 2, y + 20, title, 12.5, tcol, 700)
    if sub:
        text(x + w / 2, y + 37, sub, 10.5, GREY)


def layer(x, y, w, h, tag, title, fill, stroke):
    rect(x, y, w, h, fill, stroke, 12, 1.2)
    a(f'<rect x="{x}" y="{y}" width="26" height="{h}" rx="12" fill="{stroke}"/>')
    a(f'<rect x="{x+14}" y="{y}" width="12" height="{h}" fill="{stroke}"/>')
    a(f'<text transform="translate({x+18},{y+h/2}) rotate(-90)" font-size="12" fill="#fff" font-weight="700" text-anchor="middle" letter-spacing="2">{tag}</text>')
    text(x + 40, y + 20, title, 12.5, stroke, 700, "start")


def arrow(x1, y1, x2, y2, label="", dash=False, col=SAGE_D):
    d = 'stroke-dasharray="5 4"' if dash else ""
    a(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="1.6" {d} marker-end="url(#ar)"/>')
    if label:
        text(x1 + 8, (y1 + y2) / 2 + 4, label, 10.5, col, 600, "start")


W, H = 1240, 900
a(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="\'Noto Sans CJK SC\',\'PingFang SC\',\'Microsoft YaHei\',sans-serif">')
a(f'''<defs>
<marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="{SAGE_D}"/></marker>
<filter id="sh" x="-5%" y="-5%" width="110%" height="120%"><feDropShadow dx="0" dy="1.2" stdDeviation="1.2" flood-color="#000" flood-opacity="0.12"/></filter>
<linearGradient id="hd" x1="0" x2="1"><stop offset="0" stop-color="{SAGE_D}"/><stop offset="1" stop-color="{SAGE}"/></linearGradient>
</defs>''')
rect(0, 0, W, H, "#FFFFFF", "#FFFFFF", 0, 0)
rect(0, 0, W, 54, "url(#hd)", "none", 0, 0)
text(24, 34, "FDU Func Lab Helper · 工程架构", 20, "#fff", 700, "start")
text(W - 24, 34, "RAG + Skill + Tools · 无服务器 · 数据留在本机", 12.5, "#DCE6DF", 400, "end")

X0, WD = 64, 900
# ---- 1 entry
layer(24, 70, 960, 92, "入口", "ENTRY · 学生如何使用", "#FBFCFB", SAGE_D)
chip(X0 + 20, 96, 150, 54, "学生", "原始记录 · 观察", "#fff", SAGE_D)
chip(X0 + 188, 96, 150, 54, "A 网页粘贴", "chat.deepseek.com", "#fff", SAGE_D)
chip(X0 + 356, 96, 150, 54, "B dsh 本地网页", "推荐 · 自动发现 skill", SAGE_L, SAGE_D)
chip(X0 + 524, 96, 150, 54, "C 仅用模板", "Word / LaTeX", "#fff", SAGE_D)
chip(X0 + 692, 96, 188, 54, "总菜单提示词", "prompts/menu.md · AGENTS.md", "#FFF6D6", SAND)
# ---- 2 skills
layer(24, 188, 960, 232, "SKILL 层", "ORCHESTRATION · .agents/skills（12 个，每个只做一件事）", BLUE_L, BLUE)
rect(X0 + 12, 216, WD - 24, 32, BLUE, BLUE, 7)
text(X0 + WD / 2, 237, "fdu-lab-menu → fdu-lab-report　总调度：选路径 · 守硬规则（不编造 · n=1 不推断 · 偏差写成假设）", 12.5, "#fff", 700)
groups = [("① 准备", [("intake", "采集"), ("rag", "检索")]), ("② 计算", [("data", "公式"), ("stats", "统计"), ("plot", "作图")]),
          ("③ 写作", [("analysis", "论证"), ("style", "语言")]), ("④ 核验", [("cite", "文献"), ("review", "自查")]), ("⑤ 出稿", [("format", "排版")])]
gx = X0 + 12
widths = [188, 270, 188, 188, 0]
gw = [2, 3, 2, 2, 1]
unit = (WD - 24 - 4 * 10) / 10
for (name, items), n in zip(groups, gw):
    w = unit * n * 1.0 + (0)
    rect(gx, 262, w, 144, "#fff", BLUE, 8, 1)
    text(gx + w / 2, 280, name, 11.5, BLUE, 700)
    cw = (w - 8 - 6 * (len(items) - 1)) / len(items)
    for k, (t, s) in enumerate(items):
        chip(gx + 4 + k * (cw + 6), 292, cw, 50, t, s, BLUE_L, BLUE)
    text(gx + w / 2, 372, ["课本措辞", "确定性", "有据", "防编造", "docx/tex/pdf"][groups.index((name, items))], 10.5, GREY)
    text(gx + w / 2, 390, "", 10)
    gx += w + 10
# ---- 3 tools
layer(24, 446, 960, 150, "工具层", "TOOLS · tools/*.py（确定性代码，可测试可复现）", SAGE_L, SAGE)
tools = [("rag.py", "BM25 检索"), ("labcalc.py", "剂量·LD50·MAP"), ("labstats.py", "t·ANOVA·回归"), ("labplot.py", "规范作图"),
         ("stylecheck.py", "术语·相似度"), ("refcheck.py", "Crossref 核对"), ("build.py", "docx/tex/pdf"), ("kb.py", "教材切分")]
tw = (WD - 24 - 7 * 8) / 8
for i, (t, s) in enumerate(tools):
    chip(X0 + 12 + i * (tw + 8), 474, tw, 54, t, s, "#fff", SAGE)
text(X0 + WD / 2, 556, "模型负责理解与组织；数字、检验、引用、相似度、排版全部由工具产出并可复核", 11.5, SAGE_D, 600)
text(X0 + WD / 2, 576, "单元测试：labcalc · labstats · labplot · refcheck(mock) · rag/stylecheck · build（30 项）", 10.5, GREY)
# ---- 4 knowledge
layer(24, 622, 960, 150, "知识层", "KNOWLEDGE · reference/ + knowledge/（RAG 语料，每片段带来源标签）", SAND_L, SAND)
ks = [("textbook", "教材 PDF + 分章文本"), ("lecture", "讲义 / 实验指导"), ("corpus/local", "其他中文教材"), ("card", "知识卡 33 · AI 草稿"),
      ("expr", "课本表述 · 术语句式"), ("literature", "14 篇 · DOI 已核对")]
kw = (WD - 24 - 5 * 8) / 6
for i, (t, s) in enumerate(ks):
    chip(X0 + 12 + i * (kw + 8), 650, kw, 54, t, s, "#fff", SAND)
rect(X0 + 12, 716, WD - 24, 40, "#fff", SAND, 7, 1, 'stroke-dasharray="5 4"')
text(X0 + WD / 2, 733, "corpus/index/rag.json　中文字二元组 + 英文词 · BM25 · 纯 Python（无服务器、无嵌入模型）", 11.5, SAND, 700)
text(X0 + WD / 2, 749, "标签：textbook / lecture / card / expr / literature / 本地目录名", 10.5, GREY)
# ---- 5 output
layer(24, 798, 960, 80, "产出", "OUTPUT · 与外部", ROSE_L, ROSE)
chip(X0 + 12, 820, 170, 48, "report.md", "YAML 头 + 正文", "#fff", ROSE)
chip(X0 + 196, 820, 170, 48, "Word / PDF / tex", "封面·目录·页眉", "#fff", ROSE)
chip(X0 + 380, 820, 170, 48, "templates/", "通用模板·格式规范", "#fff", ROSE)
chip(X0 + 564, 820, 150, 48, "Crossref API", "外部 · 联网核对", "#fff", ROSE)
chip(X0 + 728, 820, 152, 48, "examples/", "改编自真实作业", "#fff", ROSE)
# ---- arrows between layers
arrow(500, 162, 500, 188, "")
arrow(300, 420, 300, 446, "调用 CLI")
arrow(700, 446, 700, 420, "返回结果", False)
arrow(500, 596, 500, 622, "检索")
arrow(500, 772, 500, 798, "渲染 / 核对")
# ---- guardrail panel
rect(1004, 70, 212, 808, "#FBF7F7", ROSE, 12, 1.2)
text(1110, 96, "治理护栏", 14, ROSE, 700)
text(1110, 114, "GUARDRAILS", 10, GREY, 400)
gr = [("不编造", "数据·观察·文献·页码·P 值\n找不到依据写“待核”"), ("n = 1 不推断", "单只动物只描述\nn &lt; 3 工具拒绝检验"), ("偏差=假设", "与预期不符写成可能原因\n并给出验证方式"),
      ("文献必核", "refcheck 逐项对 Crossref\n通过≠支持论点，需自己读"), ("语言≠规避", "润色不改数据与结论\n不以绕过 AI 检测为目的"), ("AI 声明", "ai_statement 按课程要求\n如实填写"),
      ("草稿标记", "卡片/表述为 AI 起草\n冲突时以教材与老师为准"), ("隐私", "reports/ 与 corpus/local/\n不入库；Key 只填 dsh")]
y = 140
for t, s in gr:
    rect(1016, y, 188, 84, "#fff", ROSE, 8, 1)
    text(1110, y + 22, t, 12.5, ROSE, 700)
    for i, ln in enumerate(s.split("\n")):
        text(1110, y + 44 + i * 16, ln, 10.5, GREY)
    y += 91
a('</svg>')
out = ROOT / "assets/readme/architecture.svg"
out.write_text("\n".join(o), encoding="utf8")
print("✓", out)
