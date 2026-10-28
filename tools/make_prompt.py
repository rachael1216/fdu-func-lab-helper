#!/usr/bin/env python3
"""make_prompt.py — 生成「粘贴式提示词」，给只想用 chat.deepseek.com 网页版的同学（不需要任何安装）。

  python tools/make_prompt.py 2.7            # 生成 prompts/out/ex_2.7.prompt.md
  python tools/make_prompt.py 2.7 --print    # 直接打印，便于复制

把生成的整段文字粘贴到 DeepSeek 对话框，然后按它的提问依次回答（粘贴你的原始记录）。
网页版不能运行 labcalc 和 build：计算请按它给出的公式在本地用 `python tools/labcalc.py` 复核，
最后把它写好的 Markdown 用 build.py 或 Word 模板排版。
"""
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SK = ROOT / ".agents" / "skills"


def strip_front(t):
    return t.split("---", 2)[2].strip() if t.startswith("---") else t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exp")
    ap.add_argument("--print", action="store_true")
    a = ap.parse_args()
    card = ROOT / "knowledge" / "cards" / f"ex_{a.exp}.md"
    parts = ["# 角色\n你是复旦医学生《功能学科综合实验》报告的写作教练，不是代笔。规则如下。\n"]
    for n in ("fdu-lab-report", "fdu-lab-intake", "fdu-lab-analysis", "fdu-lab-review"):
        parts.append(f"\n## 规则：{n}\n" + strip_front((SK / n / "SKILL.md").read_text(encoding="utf8")))
    parts.append("\n（说明：你在网页聊天里无法运行命令；凡需要计算，请写出公式和代入过程，并提示我用 `python tools/labcalc.py` 复核。）\n")
    if card.exists():
        parts.append(f"\n# 本次实验知识卡（AI 起草，未经教师审校）\n{strip_front(card.read_text(encoding='utf8'))}\n")
    else:
        parts.append(f"\n# 注意\n仓库里没有实验 {a.exp} 的知识卡，请向我索要讲义相关内容。\n")
    parts.append("\n# 现在开始\n请先用一句话确认你理解了规则，然后问我第一组问题。\n")
    text = "\n".join(parts)
    if a.print:
        print(text)
        return
    out = ROOT / "prompts" / "out"
    out.mkdir(parents=True, exist_ok=True)
    f = out / f"ex_{a.exp}.prompt.md"
    f.write_text(text, encoding="utf8")
    print(f"✓ {f}（{len(text)} 字符）")


if __name__ == "__main__":
    main()
