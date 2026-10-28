# 第三方组件与数据来源

## 软件依赖（均未随仓库分发源码，由 pip / 系统包安装）
| 组件 | 用途 | 许可 |
|---|---|---|
| pandoc | Markdown → docx / tex | GPL-2.0-or-later（作为外部程序调用） |
| python-docx | Word 后处理 | MIT |
| PyYAML | 读取 YAML | MIT |
| SciPy / NumPy | 统计检验 | BSD-3-Clause |
| matplotlib | 作图、封面线稿 | PSF-based (matplotlib license) |
| PyMuPDF（可选） | 读取教材 PDF（`kb.py`） | AGPL-3.0 / 商业；仅本机使用，不分发 |
| XeLaTeX、ctex、titlesec、tcolorbox、fancyhdr、geometry | PDF 排版 | LPPL 等 |
| Noto CJK 字体（仅测试替身） | `tests/shim/` 冒烟测试 | SIL OFL 1.1 |

## 数据来源
- **Crossref REST API**：文献书目核对与登记表核对（2026-10-29 通过 DOI 端点核对）。书目事实不受版权保护；要点概括为作者自述。
- **《功能学科实验教程》**（严钰锋、马淑兰 主编，2020）：有版权，**不在仓库中**。`knowledge/expressions/` 只含术语、改写后的句式模板和页码；`kb/` 由学生本机生成并被 gitignore。
- **知识卡、课本表述整理**：AI 起草，未经教师审校。

## 图像
封面兔/鼠线稿由 `tools/make_cover.py` 用 matplotlib 绘制，随项目以 MIT 许可发布。
