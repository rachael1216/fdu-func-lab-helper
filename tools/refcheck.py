#!/usr/bin/env python3
"""refcheck.py — 参考文献核对：防止编造、张冠李戴、页码年份写错。

  python tools/refcheck.py reports/高钾血症/report.md          # 核对报告末尾的参考文献
  python tools/refcheck.py report.md --offline                  # 只对照本仓库已核对的文献登记表
  python tools/refcheck.py --registry                           # 重新核对登记表里的全部条目（联网）
  python tools/refcheck.py fmt 10.1016/S0140-6736(07)61202-1    # 由 DOI 生成 GB/T 7714 格式条目

逐条检查：
  有 DOI  → 到 Crossref 取权威书目，对比题名、第一作者、年份、卷、页码；DOI 不存在则判为“找不到”
  无 DOI  → 用整条文字在 Crossref 检索，给出最像的候选与 DOI，供你确认（不自动采信）
  中文文献、图书、教材 → 无法自动核对，标“人工核对”
状态：OK 通过 · WARN 有出入（逐项列出）· FAIL DOI 不存在 · CHECK 需人工确认
退出码：存在 FAIL 时为 1，便于放进 CI。

提醒：核对通过只说明“这篇文献存在，书目信息正确”，不说明“它支持你的论点”——后者必须你自己读过。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "knowledge" / "literature" / "references.yaml"
API = "https://api.crossref.org/works"
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"<>]+", re.I)


# ------------------------------------------------------------------ 网络
def fetch_json(url: str, timeout: int = 20) -> dict:
    ua = "fdu-func-lab-helper/0.2 (reference checker)"
    mail = os.environ.get("CROSSREF_MAILTO")
    if mail:
        ua += f" (mailto:{mail})"
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
        return json.load(r)


def crossref_by_doi(doi: str):
    try:
        return fetch_json(f"{API}/{urllib.parse.quote(doi)}")["message"]
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise


def crossref_search(text: str, rows: int = 3):
    q = urllib.parse.urlencode({"query.bibliographic": text, "rows": rows})
    return fetch_json(f"{API}?{q}")["message"].get("items", [])


# ------------------------------------------------------------------ 解析
def parse_refs(md: str) -> list[tuple[str, str]]:
    m = re.search(r"(?ms)^#+\s*(?:参考文献|References?)\b.*?\n(.*?)(?=^#+\s|\Z)", md)
    block = m.group(1) if m else md
    refs = []
    for line in block.splitlines():
        mm = re.match(r"\s*\[(\d+)\]\s*(.+)", line)
        if mm:
            refs.append((mm.group(1), mm.group(2).strip()))
    return refs


def clean_doi(s: str) -> str:
    return re.sub(r"[.,;）)\]]+$", "", s.strip())


def norm(s: str) -> str:
    return re.sub(r"[^0-9a-z一-鿿]+", "", s.lower())


def title_of(item: dict) -> str:
    t = item.get("title") or [""]
    return t[0] if isinstance(t, list) else t


def family_names(item: dict) -> list[str]:
    return [a.get("family", "") for a in item.get("author", []) if a.get("family")]


def year_of(item: dict):
    for k in ("issued", "published-print", "published-online"):
        dp = (item.get(k) or {}).get("date-parts")
        if dp and dp[0] and dp[0][0]:
            return str(dp[0][0])
    return ""


def compare(ref_text: str, item: dict) -> list[str]:
    """对比一条参考文献文字与 Crossref 记录，返回出入列表（空 = 一致）。"""
    problems = []
    low = norm(ref_text)
    t = norm(title_of(item))
    if t and t not in low:
        # 允许标点、副标题、大小写差异：按词重合率
        tw = set(re.findall(r"[a-z0-9]{3,}", title_of(item).lower()))
        rw = set(re.findall(r"[a-z0-9]{3,}", ref_text.lower()))
        if not tw or len(tw & rw) / len(tw) < 0.7:
            problems.append(f"题名不符（Crossref：{title_of(item)}）")
    fam = family_names(item)
    if fam and norm(fam[0]) not in low:
        problems.append(f"第一作者不符（Crossref：{fam[0]}）")
    y = year_of(item)
    if y and not re.search(rf"\b{y}\b", ref_text):
        problems.append(f"年份不符（Crossref：{y}）")
    v = str(item.get("volume", ""))
    if v and not re.search(rf"\b{re.escape(v)}\b", ref_text):
        problems.append(f"卷号不符（Crossref：{v}）")
    pg = str(item.get("page", "")).replace("–", "-")
    if pg:
        first = re.split(r"[-–]", pg)[0]
        if first and not re.search(re.escape(first), ref_text):
            problems.append(f"页码不符（Crossref：{pg}）")
    return problems


def is_chinese(s: str) -> bool:
    return len(re.findall(r"[一-鿿]", s)) > 8


def similarity(ref_text: str, item: dict) -> float:
    a = set(re.findall(r"[a-z0-9]{3,}", (title_of(item) + " " + " ".join(family_names(item))).lower()))
    b = set(re.findall(r"[a-z0-9]{3,}", ref_text.lower()))
    return len(a & b) / len(a) if a else 0.0


# ------------------------------------------------------------------ 登记表
def load_registry():
    import yaml
    return {r["doi"].lower(): r for r in (yaml.safe_load(REGISTRY.read_text(encoding="utf8")) or []) if r.get("doi")}


def split_name(a: str) -> dict:
    """“ten Cate H”“Buckley N A” → 姓与缩写：末尾连续的 1–2 位大写词是缩写，其余为姓。"""
    toks = a.split()
    k = len(toks)
    while k > 1 and re.fullmatch(r"[A-Z]{1,2}|Jr", toks[k - 1]):
        k -= 1
    return {"family": " ".join(toks[:k]), "given": " ".join(toks[k:])}


def registry_to_item(r: dict) -> dict:
    return {"title": [r["title"]], "author": [split_name(a) for a in r["authors"]], "volume": r.get("volume", ""),
            "page": r.get("pages", ""), "issued": {"date-parts": [[int(r["year"])]]}}


# ------------------------------------------------------------------ GB/T 7714
def format_gbt(item: dict, et_al_hint: bool = False) -> str:
    def name(a):
        fam, giv = a.get("family", ""), a.get("given", "")
        ini = " ".join(w if w == "Jr" else w[0] for w in re.split(r"[\s\-.]+", giv) if w)
        return f"{fam.upper()} {ini}".strip()
    au = item.get("author", [])
    names = ", ".join(name(a) for a in au[:3]) + (", et al" if len(au) > 3 or et_al_hint else "")
    cont = (item.get("container-title") or [""])[0]
    vol, iss, pg = item.get("volume", ""), item.get("issue", ""), str(item.get("page", "")).replace("–", "-")
    s = f"{names}. {title_of(item)}[J]. {cont}, {year_of(item)}"
    if vol:
        s += f", {vol}" + (f"({iss})" if iss else "")
    if pg:
        s += f": {pg}"
    return s + (f". DOI: {item['DOI']}." if item.get("DOI") else ".")


# ------------------------------------------------------------------ 主流程
def check_refs(refs, offline=False, out=print):
    reg = load_registry()
    bad = 0
    for n, text in refs:
        m = DOI_RE.search(text)
        doi = clean_doi(m.group(0)) if m else ""
        if not doi and (is_chinese(text) or re.search(r"\[M\]|\[D\]|\[EB", text)):
            out(f"[{n}] CHECK 中文文献/图书/学位论文：请对照原书或知网/万方人工核对")
            continue
        if m and doi.lower() in reg and offline:
            diff = compare(text, registry_to_item(reg[doi.lower()]))
            status = "OK  " if not diff else "WARN"
            out(f"[{n}] {status} 登记表已核对 DOI:{doi}" + ("" if not diff else "\n      · " + "\n      · ".join(diff)))
            continue
        if offline:
            out(f"[{n}] CHECK 离线模式，且不在登记表中，需联网核对：{text[:60]}…")
            continue
        try:
            if doi:
                item = crossref_by_doi(doi)
                if item is None:
                    bad += 1
                    out(f"[{n}] FAIL 找不到 DOI:{doi}（Crossref 无此记录，可能是编造或抄错）")
                    continue
                diff = compare(text, item)
                if diff:
                    out(f"[{n}] WARN DOI:{doi} 存在，但与条目文字有出入：\n      · " + "\n      · ".join(diff))
                    out(f"      建议写法：{format_gbt(item)}")
                else:
                    out(f"[{n}] OK   DOI:{doi}")
            elif is_chinese(text) or re.search(r"\[M\]|\[D\]|\[EB", text):
                out(f"[{n}] CHECK 中文文献/图书/学位论文：请对照原书或知网/万方人工核对")
            else:
                cands = crossref_search(text)
                if not cands:
                    out(f"[{n}] CHECK 没有检索到候选，请人工核对：{text[:60]}…")
                    continue
                best = max(cands, key=lambda c: similarity(text, c))
                sim = similarity(text, best)
                tag = "CHECK 疑似为" if sim >= 0.6 else "CHECK 候选相似度低"
                out(f"[{n}] {tag}：{title_of(best)} ({year_of(best)}) DOI:{best.get('DOI')}\n      请确认后补上 DOI；建议写法：{format_gbt(best)}")
        except Exception as e:  # noqa: BLE001
            out(f"[{n}] CHECK 联网失败（{type(e).__name__}：{e}），可稍后重试或加 --offline")
    return bad


def main():
    argv = sys.argv[1:]
    if argv and argv[0] == "fmt":
        for d in argv[1:]:
            item = crossref_by_doi(clean_doi(d))
            print(format_gbt(item) if item else f"找不到 {d}")
        return
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("md", nargs="?", type=Path)
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--registry", action="store_true", help="核对登记表全部条目")
    a = ap.parse_args(argv)
    if a.registry:
        import yaml
        rows = yaml.safe_load(REGISTRY.read_text(encoding="utf8"))
        refs = []
        for i, r in enumerate(rows, 1):
            au = ", ".join(r["authors"]) + (", et al" if r.get("et_al") else "")
            refs.append((str(i), f"{au}. {r['title']}[J]. {r['journal']}, {r['year']}, {r.get('volume','')}({r.get('issue','')}): {r.get('pages','')}. DOI: {r['doi']}."))
        bad = check_refs(refs, a.offline)
    elif a.md:
        refs = parse_refs(a.md.read_text(encoding="utf8"))
        if not refs:
            sys.exit("没有在“参考文献”一节找到形如 [1] … 的条目。")
        bad = check_refs(refs, a.offline)
    else:
        ap.error("请给出 report.md，或使用 --registry / fmt")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
