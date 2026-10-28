"""docx_cover.py — 对 pandoc 生成的 docx 做后处理（供 build.py 调用）：
封面（极简线稿）→ 目录（罗马页码）→ 正文（阿拉伯页码）、三线表、页眉。"""
from __future__ import annotations

import copy
from pathlib import Path

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BLACK, GREY, SAGE = RGBColor(0, 0, 0), RGBColor(0x59, 0x60, 0x6A), RGBColor(0x5F, 0x75, 0x68)


# ------------------------------------------------------------ 基础
def _fonts(run, east="宋体", latin="Times New Roman"):
    rpr = run._r.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.insert(0, rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs"):
        rf.set(qn(a), latin)
    rf.set(qn("w:eastAsia"), east)


def _run(p, text, size=12, bold=False, color=BLACK, east="宋体", latin="Times New Roman", spacing=None):
    r = p.add_run(text)
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    _fonts(r, east, latin)
    if spacing:
        sp = OxmlElement("w:spacing")
        sp.set(qn("w:val"), str(spacing))
        r._r.get_or_add_rPr().append(sp)
    return r


def _border(parent, tag, sz, color="000000", val="single"):
    e = OxmlElement(f"w:{tag}")
    e.set(qn("w:val"), val); e.set(qn("w:sz"), str(sz)); e.set(qn("w:space"), "0"); e.set(qn("w:color"), color)
    parent.append(e)


# ------------------------------------------------------------ 三线表
def style_tables(doc):
    """三线表：上、下 1.5 磅，表头下 0.75 磅；五号字，居中。"""
    for t in doc.tables:
        tblpr = t._tbl.tblPr
        for old in tblpr.findall(qn("w:tblBorders")):
            tblpr.remove(old)
        b = OxmlElement("w:tblBorders")
        _border(b, "top", 12)
        _border(b, "bottom", 12)
        tblpr.append(b)
        jc = tblpr.find(qn("w:jc"))
        if jc is None:
            jc = OxmlElement("w:jc")
            tblpr.append(jc)
        jc.set(qn("w:val"), "center")
        mar = OxmlElement("w:tblCellMar")
        for side, w in (("top", 40), ("bottom", 40), ("left", 80), ("right", 80)):
            e = OxmlElement(f"w:{side}")
            e.set(qn("w:w"), str(w)); e.set(qn("w:type"), "dxa")
            mar.append(e)
        tblpr.append(mar)
        for ri, row in enumerate(t.rows):
            for cell in row.cells:
                if ri == 0:
                    tcpr = cell._tc.get_or_add_tcPr()
                    tb = OxmlElement("w:tcBorders")
                    _border(tb, "bottom", 6)
                    tcpr.append(tb)
                for p in cell.paragraphs:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    pf = p.paragraph_format
                    pf.first_line_indent = Pt(0)
                    pf.space_before = pf.space_after = Pt(1)
                    pf.line_spacing = 1.2
                    for r in p.runs:
                        r.font.size = Pt(10.5)
                        if ri == 0:
                            r.font.bold = True


# ------------------------------------------------------------ 分节
def _sect(doc, kind, body_sect):
    """构造一个 sectPr。kind: 'cover' | 'toc'。"""
    s = OxmlElement("w:sectPr")
    if kind == "toc":
        for tag in ("headerReference", "footerReference"):
            for e in body_sect.findall(qn(f"w:{tag}")):
                s.append(copy.deepcopy(e))
    for tag in ("pgSz", "pgMar"):
        e = body_sect.find(qn(f"w:{tag}"))
        if e is not None:
            s.append(copy.deepcopy(e))
    if kind == "toc":
        n = OxmlElement("w:pgNumType")
        n.set(qn("w:fmt"), "upperRoman"); n.set(qn("w:start"), "1")
        s.append(n)
    else:
        v = OxmlElement("w:vAlign")
        v.set(qn("w:val"), "center")
        s.append(v)
    return s


def _break_par(doc, sect):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(0)
    p._p.get_or_add_pPr().append(sect)
    return p._p


# ------------------------------------------------------------ 封面
def add_cover(doc, meta: dict, picture: Path | None):
    """封面：学校/课程 → 题目 → 线稿 → 姓名学号日期；整页垂直居中。"""
    made = []

    def par(before=0, after=0, line=None):
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.space_before, pf.space_after = Pt(before), Pt(after)
        pf.first_line_indent = Pt(0)
        pf.left_indent = pf.right_indent = Pt(0)
        if line:
            pf.line_spacing = line
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        made.append(p._p)
        return p

    p = par(after=4)
    _run(p, "复旦大学上海医学院", 14, False, GREY, "黑体", spacing=60)
    p = par(after=40)
    _run(p, meta.get("course") or "功能学科综合实验", 16, False, BLACK, "黑体", spacing=40)
    p = par(after=6, line=1.2)
    _run(p, meta.get("title") or "实验报告", 26, True, BLACK, "黑体", "Arial")
    if meta.get("exp_no"):
        p = par(after=0)
        _run(p, f"实验 {meta['exp_no']}", 12, False, GREY, "宋体")
    if picture and Path(picture).exists():
        p = par(before=40, after=40)
        p.add_run().add_picture(str(picture), width=Cm(7.0))
    else:
        par(before=60, after=60)
    rows = [("班　级", meta.get("class", "")), ("姓　名", meta.get("student", "")), ("学　号", meta.get("student_id", "")),
            ("小　组", meta.get("group", "")), ("指导教师", meta.get("teacher", "")), ("日　期", meta.get("date", ""))]
    for k, v in rows:
        if not v:
            continue
        p = par(after=8)
        _run(p, f"{k}　", 13, False, GREY, "黑体")
        _run(p, v, 14, False, BLACK, "宋体")
    return made


def build_front(doc, meta: dict, picture: Path | None, cover: bool = True):
    body = doc.element.body
    body_sect = body.find(qn("w:sectPr"))
    first = body[0]
    sdt = next((e for e in body if e.tag == qn("w:sdt")), None)
    if cover:
        els = add_cover(doc, meta, picture)
        els.append(_break_par(doc, _sect(doc, "cover", body_sect)))
        for el in els:
            first.addprevious(el)
    if sdt is not None:
        brk = _break_par(doc, _sect(doc, "toc", body_sect))
        sdt.addnext(brk)
    n = OxmlElement("w:pgNumType")
    n.set(qn("w:start"), "1")
    body_sect.append(n)


# ------------------------------------------------------------ 页眉
def fill_header(doc, left: str, right: str, icon: Path | None = None):
    for sec in doc.sections:
        if sec.header.is_linked_to_previous:
            continue
        for p in sec.header.paragraphs:
            for r in p.runs:
                if "{{HEADER_L}}" in r.text:
                    r.text = r.text.replace("{{HEADER_L}}", left)
                if "{{HEADER_R}}" in r.text:
                    r.text = r.text.replace("{{HEADER_R}}", right)
        if icon and Path(icon).exists() and sec.header.paragraphs:
            p = sec.header.paragraphs[0]
            if not p._p.findall(".//" + qn("w:drawing")):
                run = p.add_run()
                run.add_picture(str(icon), height=Cm(0.5))
                p._p.remove(run._r)
                first_run = p._p.find(qn("w:r"))
                (first_run.addprevious if first_run is not None else p._p.append)(run._r)
                sp = p.add_run(" ")
                p._p.remove(sp._r)
                run._r.addnext(sp._r)


def update_fields_on_open(doc):
    st = doc.settings.element
    if st.find(qn("w:updateFields")) is None:
        e = OxmlElement("w:updateFields")
        e.set(qn("w:val"), "true")
        st.append(e)
