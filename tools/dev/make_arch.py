#!/usr/bin/env python3
"""make_arch.py — 生成 README 用的两张工程图（SVG）：.github/img/architecture.svg、rag-pipeline.svg。

配色取学术图常用的色盲友好色（Okabe–Ito）：蓝＝Skill/服务，绿＝工具，橙＝知识库，灰＝外部。
所有文字按字宽估算并断言不超出方框。
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FONT = "'Noto Sans CJK SC','Source Han Sans SC','PingFang SC','Microsoft YaHei',Arial,sans-serif"
INK = "#1A1A1A"
SUB = "#3D3D3D"
C = {  # 描边色, 底色
    "blue": ("#0B5C8E", "#E4F0F8"),
    "green": ("#00704F", "#E2F3EC"),
    "orange": ("#B84A00", "#FBEBDD"),
    "gray": ("#4A4A4A", "#EFEFEF"),
}
SW = 2.8  # 描边


def tw(s: str, size: float, bold=False) -> float:
    return sum(size * (1.0 if re.match(r"[　-鿿＀-￯【】（）·“”—…]", ch) else 0.58 if ch != " " else 0.3) for ch in s) * (1.06 if bold else 1)


def formula_png():
    """用 matplotlib mathtext（STIX 字体）排版 BM25 公式，返回 (base64, 宽, 高)。"""
    import base64
    import io

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    matplotlib.rcParams["mathtext.fontset"] = "stix"
    tex = (r"$\mathrm{score}(q,d)=\sum_{t\in q}\mathrm{idf}(t)\cdot\dfrac{f(t,d)\,(k_1+1)}{f(t,d)+k_1\,(1-b+b\,|d|/\mathrm{avgdl})}$"
           r"$\qquad\mathrm{idf}(t)=\ln\!\left(1+\dfrac{N-\mathrm{df}(t)+0.5}{\mathrm{df}(t)+0.5}\right)$")
    fig = plt.figure(figsize=(1, 1))
    fig.text(0, 0, tex, fontsize=17)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight", pad_inches=0.04, transparent=True)
    plt.close(fig)
    from PIL import Image
    buf.seek(0)
    w, h = Image.open(buf).size
    return base64.b64encode(buf.getvalue()).decode(), w, h


class Svg:
    def __init__(self, w, h):
        self.w, self.h, self.o = w, h, []
        self.o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" font-family="{FONT}">')
        self.o.append('<defs><marker id="ar" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">'
                      f'<path d="M0 0L10 5L0 10z" fill="{INK}"/></marker></defs>')
        self.o.append(f'<rect width="{w}" height="{h}" fill="#fff"/>')

    def rect(self, x, y, w, h, hue, r=6, dash=False, fill=None, sw=SW):
        s, f = C[hue]
        d = ' stroke-dasharray="9 6"' if dash else ""
        self.o.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill or f}" stroke="{s}" stroke-width="{sw}"{d}/>')

    def text(self, x, y, s, size=14, col=INK, bold=False, anchor="middle", maxw=None):
        if maxw is not None:
            assert tw(s, size, bold) <= maxw, f"文字超出：{s!r} {tw(s, size, bold):.0f}>{maxw:.0f}"
        w = ' font-weight="700"' if bold else ""
        s = s.replace("&", "&amp;").replace("<", "&lt;")
        self.o.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{col}" text-anchor="{anchor}"{w}>{s}</text>')

    def box(self, x, y, w, h, hue, title, lines=(), tsize=15, lsize=13, fill=None):
        """文字整体垂直居中的方框。"""
        self.rect(x, y, w, h, hue, fill=fill)
        n = len(lines)
        block = tsize + (n * (lsize + 7) if n else 0)
        y0 = y + (h - block) / 2 + tsize * 0.82
        self.text(x + w / 2, y0, title, tsize, C[hue][0], True, maxw=w - 10)
        for i, ln in enumerate(lines):
            self.text(x + w / 2, y0 + 8 + (i + 1) * (lsize + 7) - 4, ln, lsize, SUB, maxw=w - 10)

    def arrow(self, x1, y1, x2, y2, both=False):
        e = ' marker-start="url(#ar)"' if both else ""
        self.o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{INK}" stroke-width="2.6" marker-end="url(#ar)"{e}/>')

    def save(self, name):
        self.o.append("</svg>")
        p = ROOT / ".github" / "img" / name
        p.write_text("\n".join(self.o), encoding="utf8")
        print("✓", p)


# ====================================================== 图 1：总体架构
def architecture():
    g = Svg(1200, 668)
    # 左：学生与客户端
    g.box(24, 74, 190, 120, "gray", "学生", ["原始记录 · 观察", "数据留在本机"], 17, 14)
    g.box(24, 226, 190, 288, "gray", "MCP 客户端", ["DeepSeek · dsh", "Claude Code", "其他 stdio 客户端", "选菜单编号", "按 skill 流程写作"], 17, 14)
    g.arrow(119, 194, 119, 226, both=True)
    # 中：MCP 服务
    g.rect(260, 74, 680, 530, "blue", dash=True, fill="#fff")
    g.text(600, 104, "fdu-lab MCP 服务　tools/mcp_server.py", 17, C["blue"][0], True, maxw=650)
    g.text(600, 124, "stdio · JSON-RPC · prompts / tools / resources", 13.5, SUB, maxw=650)
    # Prompts
    g.rect(280, 138, 640, 172, "blue")
    g.text(294, 166, "Prompts　菜单 + 12 个 Skill", 16, C["blue"][0], True, "start", maxw=600)
    sk = [("menu", "菜单"), ("report", "总调度"), ("intake", "采集"), ("rag", "检索"), ("data", "计算"), ("stats", "统计"),
          ("plot", "作图"), ("analysis", "论证"), ("style", "语言"), ("cite", "文献"), ("review", "自查"), ("format", "排版")]
    cw = (640 - 28 - 5 * 8) / 6
    for i, (n, r) in enumerate(sk):
        g.box(294 + (i % 6) * (cw + 8), 178 + (i // 6) * 60, cw, 52, "blue", n, [r], 14, 12.5, fill="#fff")
    # RAG
    g.rect(280, 322, 640, 84, "orange")
    g.text(294, 348, "本地 RAG　reference/index/rag.json", 16, C["orange"][0], True, "start", maxw=600)
    g.text(600, 372, "中文字二元组 + 英文词 · BM25（k1 = 1.5，b = 0.75）· 纯 Python", 13.5, SUB, maxw=610)
    g.text(600, 394, "按语料标签 -c、实验编号 --exp 过滤，返回片段与出处页码", 13.5, SUB, maxw=610)
    # Tools
    g.rect(280, 418, 640, 172, "green")
    g.text(294, 446, "Tools　10 个确定性工具", 16, C["green"][0], True, "start", maxw=600)
    tl = [("rag", "BM25 检索"), ("labcalc", "剂量·LD50"), ("labstats", "检验"), ("labdose", "质反应"), ("labplot", "规范作图"),
          ("stylecheck", "术语·相似度"), ("styleprofile", "文风画像"), ("refcheck", "文献核对"), ("build", "排版出稿"), ("kb", "教材切分")]
    cw = (640 - 28 - 4 * 8) / 5
    for i, (n, r) in enumerate(tl):
        g.box(294 + (i % 5) * (cw + 8), 458 + (i // 5) * 60, cw, 52, "green", n, [r], 14, 12.5, fill="#fff")
    g.arrow(214, 370, 260, 370, both=True)
    g.text(237, 356, "MCP", 12.5, SUB, True, maxw=44)
    # 右：知识库与产出
    g.rect(980, 138, 196, 326, "orange", fill="#fff")
    g.text(1078, 166, "知识库", 17, C["orange"][0], True, maxw=180)
    g.text(1078, 185, "reference/", 12.5, SUB, maxw=180)
    kb = [("textbook", "教材全书 · 分章"), ("lecture", "讲义 · 实验指导"), ("reference/local", "其他中文教材"), ("card · expr", "知识卡 · 课本表述"), ("literature", "14 篇 · DOI 已核")]
    for i, (n, r) in enumerate(kb):
        g.box(990, 198 + i * 52, 176, 46, "orange", n, [r], 14, 12.5)
    g.arrow(940, 364, 980, 364, both=True)
    g.text(960, 350, "检索", 12.5, SUB, True, maxw=36)
    g.box(980, 478, 196, 126, "gray", "产出", ["report.md", "Word · PDF · tex", "templates/ · examples/"], 17, 14)
    g.arrow(940, 534, 980, 534)
    g.text(960, 520, "生成", 12.5, SUB, True, maxw=36)
    # 护栏
    g.rect(24, 620, 1152, 36, "gray", fill="#fff")
    g.text(600, 644, "治理护栏：不编造数据与文献　·　n = 1 不推断　·　偏差写成假设　·　文献必核　·　AI 声明　·　数据不出本机", 14, INK, True, maxw=1130)
    g.o[0] = g.o[0].replace('viewBox="0 0 1200 668"', 'viewBox="0 58 1200 610"')
    g.save("architecture.svg")


# ====================================================== 图 2：RAG 管线
def rag():
    g = Svg(1200, 576)
    # 语料
    g.text(14, 30, "语料（每个片段带来源标签）", 15, INK, True, "start")
    cs = ["textbook 教材", "lecture 讲义", "local 其他教材", "card 知识卡", "expr 课本表述", "literature 文献"]
    cw = (1172 - 5 * 10) / 6
    for i, c in enumerate(cs):
        g.box(14 + i * (cw + 10), 44, cw, 40, "orange", c, [], 14)
    g.arrow(600, 86, 600, 118)
    # 六步
    st = [("① 读取", ["pdf · docx · md", "txt · yaml", "教材保留页码范围"]), ("② 切片", ["教材按【小节】", "文献一条一片", "其余段落 不超过 380 字"]),
          ("③ 分词", ["中文：字二元组", "英文：小写词", "无需词典与模型"]), ("④ 索引", ["rag.json", "N · avgdl · df", "片段 · 出处定位"]),
          ("⑤ 查询", ["同法分词", "-c 语料标签", "--exp 实验编号"]), ("⑥ 排序", ["BM25 打分", "取 top-k", "附出处定位"])]
    bw = 170
    gap = (1172 - 6 * bw) / 5
    for i, (t, ls) in enumerate(st):
        x = 14 + i * (bw + gap)
        g.rect(x, 122, bw, 140, "blue")
        g.o.append(f'<rect x="{x}" y="122" width="{bw}" height="36" rx="6" fill="{C["blue"][0]}"/>')
        g.o.append(f'<rect x="{x}" y="140" width="{bw}" height="18" fill="{C["blue"][0]}"/>')
        g.text(x + bw / 2, 147, t, 16, "#fff", True, maxw=bw - 10)
        for j, ln in enumerate(ls):
            g.text(x + bw / 2, 188 + j * 27, ln, 14, INK, maxw=bw - 10)
        if i < 5:
            g.arrow(x + bw, 192, x + bw + gap, 192)
    # 公式（排版图）
    g.rect(14, 284, 1172, 78, "gray", fill="#fff")
    b64, fw, fh = formula_png()
    sc = min(1130 / fw, 58 / fh)
    g.o.append(f'<image x="{600 - fw * sc / 2:.1f}" y="{284 + (78 - fh * sc) / 2:.1f}" width="{fw * sc:.1f}" height="{fh * sc:.1f}" href="data:image/png;base64,{b64}"/>')
    g.text(1170, 356, "k1 = 1.5，b = 0.75", 12.5, SUB, anchor="end")
    g.arrow(600, 362, 600, 388)
    # 返回
    g.rect(14, 392, 1172, 62, "green")
    g.text(600, 418, "⑦ 返回　[序号] (语料标签) 来源 · 出处定位 · 片段正文", 16, C["green"][0], True, maxw=1150)
    g.text(600, 442, "例：[1] (textbook) 教材 · 实验3.1【原理】p.124–125 · ……　引用页码取自这里，不凭记忆", 14, SUB, maxw=1150)
    # 使用方
    g.arrow(600, 454, 600, 480)
    us = [("rag（skill）", "取术语与句式"), ("stylecheck", "逐句比对教材"), ("refcheck", "对照文献登记表"), ("export", "供 local-rag-cpp 稠密检索")]
    uw = (1172 - 3 * 14) / 4
    for i, (t, d) in enumerate(us):
        g.box(14 + i * (uw + 14), 484, uw, 78, "blue", t, [d], 16, 14)
    g.save("rag-pipeline.svg")


if __name__ == "__main__":
    architecture()
    rag()
