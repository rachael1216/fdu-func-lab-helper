<div align="center">

# FDU Func Lab Helper

**面向《功能学科综合实验》的实验报告写作助手：课本检索 + 写作 Skill + 可核对的计算与文献工具**

[English](README.en.md) · **中文**

**刘瑞琦 (Rachael Liu)**<sup>1</sup> · <a href="mailto:24301050114@m.fudan.edu.cn">24301050114@m.fudan.edu.cn</a>

<sup>1</sup> 复旦大学上海医学院，24 级临床医学五年制

[![license](https://img.shields.io/badge/license-MIT-5F7568)](LICENSE)
[![python](https://img.shields.io/badge/python-3.10%2B-5F7568)](requirements.txt)
[![skills](https://img.shields.io/badge/skills-11-5F7568)](.agents/skills)
[![status](https://img.shields.io/badge/cards%20%26%20expressions-AI%20draft-lightgrey)](knowledge)

<img src="assets/readme/architecture.svg" alt="RAG + Skill 架构" width="100%">

</div>

## 摘要

撰写功能学实验报告时，常见的问题有三类：用语偏离教材、数据与统计处理不规范、参考文献无法核实。
本项目把解决办法拆成三层：**检索层**以教材、讲义、课本表述整理和重点文献为语料，保证措辞与教材一致并能回到出处；
**工具层**用确定性代码完成计算、统计、作图、语言检查和文献核对；**Skill 层**把上述步骤编排成一条写作流水线，由 AI 担任写作教练而非代笔。
项目不含服务器，在学生自己的 DeepSeek Harness（dsh）或网页对话中即可使用；同时提供 Word 与 LaTeX 通用模板（单一极简封面、页眉、三线表、GB/T 7714）。
**原始数据与观察必须来自学生本人的实验；项目不用于规避 AI 检测，AI 使用情况应按课程要求声明。**

## 它做什么

| 需求 | 对应部分 |
|---|---|
| 用语贴近课本 | `tools/rag.py` 检索教材/表述整理；`tools/stylecheck.py` 检查术语覆盖、模板腔、与课本的相似度 |
| 课本之外的重点文献 | `knowledge/literature/`：14 篇已用 Crossref 核对书目的文献及要点 |
| 文献不出错 | `tools/refcheck.py`：核对 DOI、题名、第一作者、年份、卷页；`fmt` 由 DOI 生成 GB/T 7714 条目 |
| 数据处理 | `tools/labcalc.py`（剂量、LD50、治疗指数、MAP、AChE 活力等）；`tools/labstats.py`（t 检验、方差分析、秩和、相关、回归） |
| 作图 | `tools/labplot.py`：折线、柱状+散点、量效、拟合；规范见 `docs/FORMAT.md` |
| 分析思路 | `fdu-lab-analysis`：观察 → 预期 → 机制 → 偏差假设 → 局限 → 临床联系 |
| 模板 | Word 与 LaTeX 通用模板，含写作内容、格式要求与字体 |
| 各实验的专业表述 | `knowledge/expressions/`：7 个实验的术语、句式与页码 |

## 快速开始

需要：Python ≥ 3.10、pandoc；出 PDF 另需 XeLaTeX（TeX Live / MiKTeX，含 ctex）。

```bash
git clone https://github.com/rachael1216/fdu-func-lab-helper.git
cd fdu-func-lab-helper
pip install -r requirements.txt
python tools/build.py --doctor                  # 检查环境
python tools/build.py examples/sample-report/report.md --to all   # 试生成示例
```

在 dsh 中使用（详见 [docs/GUIDE.md](docs/GUIDE.md)）：

```bash
npx @deepseek-ai/dsh web      # 在仓库目录运行，浏览器打开 http://127.0.0.1:3080
```

然后对它说：“我要写实验 2.7 家兔高钾血症的报告，按 fdu-lab-report 的流程带我做。”
不想装 dsh：把 `prompts/` 里的提示词粘贴到 chat.deepseek.com；只要模板：直接用 `templates/` 下的 Word / tex。

## 示例

<div align="center"><img src="assets/readme/preview.png" alt="示例报告：封面与正文" width="92%"><br><sub>示例报告（虚构数据，仅演示版式）：封面、页眉、三线表、参考文献</sub></div>

```bash
python tools/rag.py search 高钾血症 T波 --exp 2.7 -c expr        # 取课本术语与句式
python tools/labstats.py ttest --a 5.1 4.8 5.5 --b 6.2 6.0 6.8   # t(4) = -3.82, P = 0.020
python tools/labplot.py bar data.csv --x 组别 --y 数值 --points -o fig1.png
python tools/stylecheck.py reports/高钾血症/report.md --exp 2.7
python tools/refcheck.py reports/高钾血症/report.md
```

## 工作原理

1. **检索**：片段按教材【章节】、知识卡标题、文献条目切分，建立中文字二元组 + 英文词的 BM25 索引（纯 Python，无服务器、无嵌入模型）。结果带 `textbook / expr / card / literature / 本地目录名` 标签。
2. **语言**：`stylecheck` 逐句与教材片段比对：相似度 ≥ 0.60 提示“过于接近原文”，< 0.15 提示“缺少课本依据”；并列出口语、模板腔及其改法。它只给提示，不改文字。
3. **统计与作图**：全部由代码完成；n = 1 不检验，n < 3 拒绝检验，小样本提示正态性检验无检验力。
4. **文献**：`refcheck` 到 Crossref 取权威书目逐项对比；中文文献、图书标“人工核对”。核对通过只说明文献存在且书目正确，不说明它支持你的论点。
5. **出稿**：Markdown（YAML 头）→ pandoc → docx / tex / pdf；封面、目录（罗马页码）、正文（阿拉伯页码）、页眉由脚本处理。

设计取舍（为何是 skill + 轻量 RAG 而非 agent 或向量库）见 [DESIGN.md](DESIGN.md)。

## 设置

| 项 | 位置 |
|---|---|
| 封面线稿 | YAML 头 `animal: rabbit | mouse`（`tools/make_cover.py` 生成） |
| 语料 | `kb/`（教材，本机生成）、`corpus/local/<目录>/`（自放 pdf/docx/md/txt）；改后 `python tools/rag.py build` |
| 避免用语 | `knowledge/style/avoid.yaml` |
| 相似度阈值 | `stylecheck.py --high 0.60 --low 0.15` |
| 联网核对 | 可选环境变量 `CROSSREF_MAILTO` |

教材：`python tools/kb.py build <你的教材.pdf>` 在本机生成 `kb/`（**教材不随仓库分发**，`kb/` 已被 gitignore）。

## 已知局限

- 知识卡（33）与课本表述整理（7 个实验）由 AI 起草，**未经教师审校**；与教材冲突时以教材和老师为准。`（待核）` 标记的条目尚无教材依据。
- 课本表述整理只含术语、改写后的句式与页码，不含教材原文。
- dsh 的使用步骤依据其公开文档整理，**作者尚未在 dsh 上完整运行验证**。
- LaTeX 版本在没有 ctex 的环境中只用替身类做过编译冒烟测试；真实 ctex 环境的结果以 CI 和你的本机为准。
- 文献登记表目前 14 篇，偏有机磷、高钾血症、DIC、缺氧、药理定量方法；其他实验需要自行补充（见 `corpus/README.md`）。
- 检索为词法匹配，不理解同义改写；查不到时换关键词。

## 目录结构

```
.agents/skills/    11 个 skill（总调度 + 采集/检索/计算/统计/作图/论证/语言/文献/自查/出稿）
tools/             rag · stylecheck · refcheck · labcalc · labstats · labplot · build · kb · make_cover …
knowledge/         cards（知识卡）· expressions（课本表述）· literature（文献）· style（避免用语）
templates/         word/（通用模板+样式母版）· latex/（fdureport.cls、通用 tex）· report-skeleton.md
corpus/            local/（自放语料，gitignore）
docs/              GUIDE.md（使用指南）· FORMAT.md（格式规范）
examples/          sample-report/（虚构示例）
tests/             单元测试与 LaTeX 替身类
```

## 联系方式

刘瑞琦 · 复旦大学上海医学院 · 24301050114@m.fudan.edu.cn。问题与改进建议欢迎提 Issue。

## 引用

```bibtex
@software{liu2026fdufunclabhelper,
  author  = {Liu, Ruiqi},
  title   = {FDU Func Lab Helper: a RAG and skill toolkit for writing functional-science laboratory reports},
  year    = {2026},
  url     = {https://github.com/rachael1216/fdu-func-lab-helper},
  license = {MIT}
}
```
机器可读版本见 [CITATION.cff](CITATION.cff)。

## 许可

MIT，见 [LICENSE](LICENSE)。第三方组件与数据来源见 [THIRD_PARTY.md](THIRD_PARTY.md)。

## 致谢

感谢《功能学科实验教程》（严钰锋、马淑兰 主编，2020）提供的课程内容；感谢 Crossref 提供开放的书目接口；感谢 pandoc、python-docx、SciPy、matplotlib 等开源项目。
