---
name: fdu-lab-format
description: 把 Markdown 报告生成带封面、目录、页眉的 Word/LaTeX/PDF，并说明格式规范与通用模板。用户要出稿、改封面、问字体字号页边距、没装环境时使用。
---

# 排版与出稿

规范全文见 `docs/FORMAT.md`（A4；页边距 2.54/3.0 cm；正文宋体/Times New Roman 小四、1.5 倍行距、首行缩进 2 字；标题黑体 16/14/12；三线表；GB/T 7714）。

## 流程
1. 报告写成 `reports/<名>/report.md`，骨架 `templates/report-skeleton.md`（含各节写作提示）。YAML 头：title、course、exp_no、class、student、student_id、group、date、teacher、animal（rabbit/mouse）、ai_statement。
2. 出稿：
```
python tools/build.py --doctor                       # 检查环境
python tools/build.py reports/<名>/report.md         # Word
python tools/build.py reports/<名>/report.md --to all # Word + tex + pdf
```
3. 封面是单一的极简线稿（兔/鼠）；页眉左课程+图标、右学号；目录用罗马页码，正文从 1 起。
4. Word 打开后若目录为空，右键“更新域”（已设置打开时自动更新）。
5. 通用模板（不走脚本时手工用）：`templates/word/功能学科实验报告模板.docx`、`templates/latex/report-template.tex`（XeLaTeX，需 ctex；或上传 Overleaf）。
6. 没装 pandoc/XeLaTeX：只要 Word 就装 pandoc；PDF 另需 TeX Live/MiKTeX，或用 Overleaf。
