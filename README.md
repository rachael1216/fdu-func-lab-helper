<div align="center">

# FDU Func Lab Helper

### 复旦大学《功能学科综合实验》实验报告写作助手

**本地 RAG　·　12 个 Skill　·　总菜单　·　一个 MCP 服务**

<br>

**刘瑞琦 (Rachael Liu)**<br>
复旦大学 华山临床医学院<br>
24 级临床医学五年制<br>
<a href="mailto:24301050114@m.fudan.edu.cn">24301050114@m.fudan.edu.cn</a>

<br>

[简介](#1-简介) · [**安装**](#2-安装) · [使用](#3-使用) · [系统设计](#4-系统设计) · [RAG](#5-rag-课本对齐的本地检索) · [**参考资料库**](#7-参考资料库) · [示例](#8-示例) · [模板](#9-模板与格式规范)

[![license](https://img.shields.io/badge/license-MIT-0B5C8E)](LICENSE)
[![python](https://img.shields.io/badge/python-%E2%89%A53.10-0B5C8E)](requirements.txt)
[![MCP](https://img.shields.io/badge/MCP-stdio-00704F)](mcp_server/server.py)
[![skills](https://img.shields.io/badge/skills-12-0B5C8E)](.agents/skills)
[![tools](https://img.shields.io/badge/tools-10-00704F)](tools)
[![literature](https://img.shields.io/badge/literature-14%20Crossref--verified-B84A00)](#72-重点文献)

<img src="assets/readme/architecture.svg" alt="系统架构：学生 → MCP 客户端 → fdu-lab MCP 服务（Prompts、本地 RAG、Tools）→ 知识库与产出" width="100%">

</div>

## 摘要

实验报告写作中的三个常见问题是：用语偏离教材、数据与统计处理不规范、参考文献无法核实。本项目以 **MCP 服务**的形式把解决这三个问题的全部组件封装在一起：**本地 RAG** 以教材、讲义、课本表述整理和重点文献为语料，使措辞贴近课本并可回到页码；**12 个 Skill 与一份总菜单**把写作拆成采集、检索、计算、统计、作图、论证、语言、文献、自查、出稿等步骤；**10 个确定性工具**产出所有数字、检验、相似度、文献核对结果和排版文件。服务在本机以 stdio 运行，接入任一支持 MCP 的客户端（DeepSeek dsh、Claude Code 等）即可使用，数据留在本机。

## 1 简介

| 组件 | 内容 | 位置 |
|---|---|---|
| **本地 RAG** | 以《功能学科实验教程》全书为主，辅以讲义、其他中文教材、知识卡、课本表述整理和重点文献；中文字二元组 BM25；返回片段与页码 | [`reference/`](reference) · [`knowledge/`](knowledge) · [`tools/rag.py`](tools/rag.py) |
| **Skill 集合（12）** | `menu` `report` `intake` `rag` `data` `stats` `plot` `analysis` `style` `cite` `review` `format`，每个只做一件事 | [`.agents/skills/`](.agents/skills) |
| **总菜单** | 12 项功能的入口提示词，按成本分级（L0 工具 → L1 检索 → L2 起草） | [`prompts/menu.md`](prompts/menu.md) |
| **工具（10）** | `rag` `labcalc` `labstats` `labdose` `labplot` `stylecheck` `styleprofile` `refcheck` `build` `kb` | [`tools/`](tools) |
| **MCP 服务** | 把以上全部以 prompts / tools / resources 暴露给客户端 | [`mcp_server/server.py`](mcp_server/server.py) |
| **模板** | Word 与 LaTeX 通用模板，含写作内容、格式要求、字体；单一线稿封面 | [`templates/`](templates) |
| **示例** | 药物半数致死量（LD50）报告，展示计算、拟合、稳健性分析、作图和语言流程 | [`examples/`](examples/sample-report) |

分工原则：模型负责理解、组织与措辞；**数字、检验、引用、相似度、排版由工具产出**，模型转述结果并标注来源。

## 2 安装

> **一条命令完成**：安装依赖、建立 RAG 索引、自检 MCP 服务，并打印可直接粘贴的客户端配置。

### 2.1 环境

| 需要 | 说明 |
|---|---|
| Python ≥ 3.10 | `python --version` |
| pandoc | 出 Word / PDF 时使用。`brew install pandoc`、`winget install JohnMacFarlane.Pandoc` 或 `pip install pypandoc_binary` |
| XeLaTeX（含 ctex） | 仅出 PDF 时需要；也可把 `.tex` 上传 Overleaf，选 XeLaTeX |
| MCP 客户端 | DeepSeek dsh、Claude Code，或任一支持 stdio MCP 的客户端 |

### 2.2 获取并安装

```bash
git clone https://github.com/rachael1216/fdu-func-lab-helper.git
cd fdu-func-lab-helper
python install.py
```

`install.py` 依次完成：`pip install -r requirements.txt` → 建立索引 `corpus/index/rag.json` → 启动服务做一次握手自检 → 打印配置。成功时看到：

```
✓ MCP 自检：13 个工具，13 个 prompt（菜单 + skill）
```

### 2.3 接入客户端

服务以 stdio 方式启动，配置只有一段 JSON（路径由 `install.py` 按你的机器生成）：

```json
{
  "mcpServers": {
    "fdu-lab": {
      "command": "python",
      "args": ["/绝对路径/fdu-func-lab-helper/mcp_server/server.py"]
    }
  }
}
```

| 客户端 | 做法 |
|---|---|
| **Claude Code** | `claude mcp add fdu-lab -- python /绝对路径/fdu-func-lab-helper/mcp_server/server.py` |
| **DeepSeek dsh** | 在 dsh 的 MCP 服务器设置中添加同一段配置；在仓库目录启动 dsh 时还会自动发现 `.agents/skills`。dsh 网页：`npx @deepseek-ai/dsh web` → http://127.0.0.1:3080，Settings 中填入 API Key |
| **其他客户端** | 粘贴上面的 JSON 到其 `mcpServers` 配置 |
| **自动写入** | `python install.py --write ~/.claude.json` 把 `fdu-lab` 合并进指定的 JSON 配置文件 |

### 2.4 验证

在客户端中依次确认：

1. 工具列表里有 `rag_search`、`lab_calc`、`lab_dose`、`style_check`、`ref_check`、`build_report` 等 13 个工具；
2. Prompt 列表里有 `menu` 与 12 个 `fdu-lab-*`；
3. 对话中输入 **“菜单”**，应展示 12 项功能表；
4. 输入“用 rag_search 查课本里半数致死量的术语”，应返回带页码的 `textbook` 片段。

### 2.5 只安装 Skill（不用 MCP）

```bash
python install.py --skills        # 复制到 ~/.agents/skills 与 ~/.dsh/skills
```

在仓库目录里直接启动 dsh 时无需安装，项目内的 `.agents/skills` 会被自动发现。Skill 中的命令行写法（`python tools/…`）在无 MCP 时直接在终端运行。

### 2.6 无客户端：网页粘贴

```bash
python tools/make_prompt.py 2.7 --print       # 2.7 换成实验编号
```

把输出粘贴到 chat.deepseek.com，按提示作答。计算与排版命令在本机用 `tools/` 运行。

### 2.7 排错

| 现象 | 处理 |
|---|---|
| 自检失败 | 运行 `python mcp_server/server.py < /dev/null` 查看报错；确认 Python ≥ 3.10 |
| `rag_search` 无结果 | `python tools/rag.py build` 重建索引；`python tools/rag.py sources` 查看语料 |
| 找不到 pandoc | 按 2.1 安装后重开终端；`python tools/build.py --doctor` 检查环境 |
| PDF 缺中文 | 安装完整 TeX Live / MiKTeX（含 ctex），或用 Overleaf |
| 图中文字成方框 | 安装宋体或思源宋体 |
| `refcheck` 联网失败 | 检查网络；加 `--offline` 对照登记表 |
| Word 目录为空 | 右键目录 → 更新域 |

## 3 使用

### 3.1 总菜单

新会话先调用 `fdu_lab_menu`（或在 Prompt 列表选 `menu`）。直接说出需求也可，助手会路由到对应 Skill。

| # | 功能 | 提供 | 调用 | 产物 |
|---|---|---|---|---|
| 1 | 从零写一份报告 | 实验编号、原始记录、观察 | `report` 全流程 | Word / PDF |
| 2 | 查课本怎么说 | 关键词或实验编号 | `rag_search` | 片段 + 页码 |
| 3 | 算数据 | 体重、剂量、浓度、读数 | `lab_calc` | 命令 + 结果 |
| 4 | 做统计 | 各组数据 | `lab_stats` | 统计句 + 解读 |
| 5 | 画图 | CSV 或表格 | `lab_plot` | 图 + 图注 |
| 6 | 写分析与讨论 | 结果与观察 | `analysis` | 讨论段落 |
| 7 | 贴近课本文风（学术 humanizer） | 一段或整篇文字 | `style_profile` → 改写 → `style_check` | 差距清单 + 改写稿 |
| 8 | 核对参考文献 | 文献列表 | `ref_check` / `ref_format` | OK / WARN / FAIL |
| 9 | 检查整份报告 | report.md | `review` | 分级问题清单 |
| 10 | 排版出稿 | report.md | `build_report` | docx / tex / pdf |
| 11 | 只要模板 | – | `format` | 模板路径 |
| 12 | 遇到问题 | 报错信息 | 第 2.7 节 | 处理步骤 |

### 3.2 一份报告的完整流程（菜单 1）

对助手说：“我要写实验 2.7 家兔高钾血症的报告，按 fdu-lab-report 带我做。”

| 步骤 | 助手做什么 | 你做什么 |
|---|---|---|
| ① 采集 | 逐组提问 | 如实提供动物、药品、时间点、原始数据、**观察到的现象**、与讲义不同之处 |
| ② 检索 | 取课本术语、原理句式、页码 | 核对页码与手上的教材一致 |
| ③ 计算 | `lab_calc` / `lab_dose` | 核对命令与结果 |
| ④ 统计 | `lab_stats` 选方法并检验 | 确认分组与 n |
| ⑤ 作图 | `lab_plot` 出图与图注 | 看图，改图注 |
| ⑥ 论证 | 观察 → 预期 → 机制 → 偏差（假设）→ 局限 → 临床联系 | 补充自己的判断 |
| ⑦ 写作 | 写入 `reports/<名>/report.md` | 通读并改成自己的话 |
| ⑧ 语言 | `style_profile` + `style_check` | 决定取舍；与课本过近的句子改写 |
| ⑨ 文献 | `ref_check` | 读过再引用；处理全部 WARN / FAIL |
| ⑩ 自查 | `review` 清单 | 逐项确认 |
| ⑪ 出稿 | `build_report` | 打开检查；按课程要求声明 AI 使用 |

报告头（YAML）：

```yaml
---
title: 家兔高钾血症实验报告
course: 功能学科综合实验
exp_no: "2.7"
class: 24 临床医学五年制
student: 姓名
student_id: "学号"
date: 2026.11.13
animal: rabbit          # rabbit | mouse，决定封面线稿
ai_statement: ""        # 按课程要求填写，非空则附在文末
---
```

个人报告放在 `reports/`（已被 `.gitignore` 忽略）。

### 3.3 直接使用命令行

```bash
python tools/rag.py search 半数致死量 改良寇氏法 --exp 8.1 -c expr          # 课本术语与页码
python tools/labcalc.py dose --weight 2.5 --dose 1000 --conc 20              # 给药体积
python tools/labstats.py anova --g 对照=1,2,3 --g 低=2,3,4 --g 高=5,6,7      # 单因素方差分析
python tools/labdose.py --dose 110.8 147.7 196.9 262.5 350 --n 22 --deaths 0 1 14 20 22 --figs figs/
python tools/labplot.py bar data.csv --x 组别 --y 数值 --points -o fig1.png
python tools/stylecheck.py reports/某实验/report.md --exp 8.1
python tools/refcheck.py reports/某实验/report.md
python tools/build.py reports/某实验/report.md --to all
```

每个工具 `-h` 有完整说明；CSV 用长表，每行一次观测。

## 4 系统设计

### 4.1 MCP 接口

服务由 `mcp_server/server.py` 提供（仅用标准库，实现 `initialize`、`tools/*`、`prompts/*`、`resources/*`，行分隔 JSON-RPC）。

| 类别 | 条目 | 说明 |
|---|---|---|
| **Prompts**（13） | `menu`；`fdu-lab-report` `-intake` `-rag` `-data` `-stats` `-plot` `-analysis` `-style` `-cite` `-review` `-format` `-menu` | 客户端可直接选用；正文前附 CLI → MCP 工具的对应表 |
| **Tools**（13） | `fdu_lab_menu` `fdu_lab_skill` `rag_search` `rag_sources` `lab_calc` `lab_stats` `lab_dose` `lab_plot` `style_check` `style_profile` `ref_check` `ref_format` `build_report` | 一一对应 `tools/*.py`，参数与命令行一致 |
| **Resources** | `fdu-lab://menu` `fdu-lab://format` `fdu-lab://references` `fdu-lab://skill/<name>` | 菜单、格式规范、文献目录、各 Skill 原文 |

### 4.2 分层

| 层 | 目录 | 职责 |
|---|---|---|
| 入口 | `prompts/`、`mcp_server/`、`AGENTS.md` | 会话启动、菜单路由、协议 |
| Skill | `.agents/skills/` | 写明触发条件、步骤、调用的工具与边界 |
| 工具 | `tools/` | 确定性计算与检查；参数进、stdout 出、退出码表示成败 |
| 知识 | `reference/`、`knowledge/`、`corpus/` | RAG 语料与文献登记表，每个片段带来源标签 |
| 产出 | `templates/`、`examples/` | 模板、示例、Word / tex / PDF |

### 4.3 Skill

| Skill | 触发 | 调用 | 产出 |
|---|---|---|---|
| `menu` | 新会话 | 菜单 | 12 项路由 |
| `report` | 写整份报告 | 其余全部 | 流水线编排与硬规则 |
| `intake` | 采集信息 | – | 结构化记录 |
| `rag` | 需要课本措辞与页码 | `rag_search` | 片段 + 出处 |
| `data` | 计算 | `lab_calc` | 命令 + 结果 |
| `stats` | 多组比较 | `lab_stats` | 统计句 |
| `plot` | 作图 | `lab_plot` | 图 + 图注 |
| `analysis` | 写讨论 | `expr` / `card` | 论证段落 |
| `style` | 润色 | `style_profile`、`style_check` | 差距清单 + 改写 |
| `cite` | 参考文献 | `ref_check` | 核对清单 |
| `review` | 整份检查 | 以上工具 | 分级问题清单 |
| `format` | 出稿与模板 | `build_report` | docx / tex / pdf |

### 4.4 工具

| 工具 | 算法与要点 |
|---|---|
| `rag.py` | 字二元组 BM25，按语料标签与实验编号过滤，输出出处定位 |
| `labcalc.py` | 教材公式：给药体积、稀释还原、改良寇氏法 LD50、治疗指数、MAP、AChE 活力、肺系数、HRV、Fisher 精确检验 |
| `labstats.py` | SciPy：描述统计、Shapiro–Wilk、Welch / 配对 / 等方差 t、单因素 ANOVA + Tukey、Mann–Whitney、Pearson / Spearman、线性回归；给出方法选择建议；n < 2 时报错退出 |
| `labdose.py` | 质反应分析：改良寇氏法 LD50 及 95% CI；Probit / Logit 二项最大似然、似然剖面区间（LRT 3.841）、AIC、偏差与 Pearson 残差、参数 bootstrap、留一剂量组、LDq 表、局部剂量敏感性；三幅图 |
| `labplot.py` | Okabe–Ito 色盲友好配色，刻度朝内，SD / SEM 可选并生成建议图注 |
| `stylecheck.py` | 术语覆盖、模板腔词表、逐句与课本相似度（≥ 0.60 过近，< 0.15 缺依据）、数字单位与标点 |
| `styleprofile.py` | 课本文风画像：句长分布、逗号密度、连接词频率、句首多样性、跨实验高频搭配；`compare` 对照报告 |
| `refcheck.py` | DOI 对 Crossref：题名、第一作者、年份、卷、页；无 DOI 时给候选；`--offline` 对照登记表；`fmt` 生成 GB/T 7714 |
| `build.py` | Markdown + YAML → pandoc → docx（封面分节、罗马 / 阿拉伯页码、三线表、页眉）或 tex（`fdureport.cls`）→ PDF |
| `kb.py` | 教材 PDF 按实验编号切分为分章文本，保留页码 |

### 4.5 分析的三道防线

1. **确定性**：计算、统计、作图全部走代码。
2. **有据**：机制句来自课本或登记文献，找不到依据时标“待核”。
3. **论证协议**：观察（事实）→ 与预期比较 → 机制 → 偏差作为假设并给出验证方式 → 局限 → 临床联系；n = 1 只描述，多组才检验。

## 5 RAG：课本对齐的本地检索

报告的措辞（术语、机制表述、判定标准）应与课本一致，引用的页码应可回到出处。RAG 的作用是在写作前取出课本表述，写作后以同一语料反向检查。

<div align="center"><img src="assets/readme/rag-pipeline.svg" alt="RAG 管线：语料 → 读取 → 切片 → 分词 → 索引 → 查询 → 排序 → 返回出处，使用方为 skill、stylecheck、refcheck、export" width="100%"></div>

### 5.1 语料

| 标签 | 位置 | 内容 | 切片粒度 |
|---|---|---|---|
| `textbook` | `reference/textbook/` | 《功能学科实验教程》PDF 与分章文本 | 按【目的】【原理】【步骤】等小节，带页码范围 |
| `lecture` | `reference/lecture/` | 讲义、实验指导 | ≤ 380 字段落 |
| 目录名 | `corpus/local/<目录>/` | 其他中文教材（《生理学》《病理生理学》《药理学》等）、文献全文 | ≤ 380 字段落 |
| `card` | `knowledge/cards/` | 机制链、预期现象、常见偏差、临床联系（33 张） | 按 “## ” 小节 |
| `expr` | `knowledge/expressions/` | 各实验的课本术语、句式、页码（7 个实验 + 通用写法） | 按 “## ” 小节 |
| `literature` | `knowledge/literature/references.yaml` | 重点文献书目与要点（14 篇） | 一条一片 |

课本之外的重点文献优先进入 RAG；放入 `corpus/local/` 的资料在本机建索引，不提交。

### 5.2 检索协议

```bash
python tools/rag.py search 肺牵张反射 迷走神经 --exp 3.1 -c textbook --full
python tools/rag.py search 复能剂 -c literature -k 3
```

1. `-c expr --exp <编号>`：取该实验的术语表与句式；
2. `-c textbook --full`：读课本原文，用课本的术语和判定标准，以自己的句子表述；
3. 课本以外的内容查 `-c literature` 或 `corpus/local/`，仍无依据时标“待核”。

算法：中文取相邻汉字二元组、英文取小写词；BM25，k₁ = 1.5，b = 0.75，idf = ln(1 + (N − df + 0.5)/(df + 0.5))；索引 `corpus/index/rag.json` 记录 N、平均长度、df 与各片段的语料标签、来源和出处定位。

### 5.3 与 local-rag-cpp

作者的另一个项目 [**local-rag-cpp**](https://github.com/rachael1216/local-rag-cpp) 以 C++ / llama.cpp 实现本地稠密向量检索与问答。两者分工：

| | 本项目 `rag.py` | local-rag-cpp |
|---|---|---|
| 检索 | 词法 BM25 | 稠密向量（余弦相似度） |
| 擅长 | 术语精确匹配、页码出处、与 Skill 和工具联动 | 同义改写、整句自然语言提问 |
| 依赖 | Python 标准库 | CMake、GCC 14、GGUF 模型 |

`python tools/rag.py export` 把全部语料导出为带“第 N 章”标题的纯文本，可作为 local-rag-cpp 的输入。

## 6 语言：从课本学文风

写作语言的目标是贴近课本。流程分三步，对应菜单第 7 项：

| 步骤 | 内容 | 工具 |
|---|---|---|
| ① 画像 | 对照课本说明性段落（目的、原理、思考题）统计的文风：句长分布、逗号密度、连接词频率、句首多样性、该实验可采用的课本搭配 | `style_profile` |
| ② 改写 | 按差距清单改表达：术语对齐、拆长句、删口语与模板腔、有数据写数据；数据与结论保持不变 | skill `fdu-lab-style` |
| ③ 验证 | 术语覆盖、模板腔、逐句与课本相似度、数字与标点格式 | `style_check` |

画像由 `reference/textbook/` 生成并保存在 `knowledge/style/profile.json`，学的是表达方式；报告中直接引用课本时加引号并标注页码。AI 使用情况按课程要求在 `ai_statement` 中声明。

## 7 参考资料库

> **`reference/` 集中存放 RAG 的全部原料与文献目录**；报告模板见[第 9 节](#9-模板与格式规范)。

### 7.1 教材与讲义

| 编号 | 文献（GB/T 7714—2015） | 位置 | 检索标签 |
|---|---|---|---|
| [M1] | 严钰锋, 马淑兰. 功能学科实验教程[M]. 2020. | [`reference/textbook/`](reference/textbook)（PDF，219 页；`ex_*.md` 为按实验切分的文本，含页码） | `textbook` |
| [M2] | 课程讲义、实验指导 | `reference/lecture/` | `lecture` |
| [M3] | 《生理学》《病理生理学》《药理学》等同类中文教材 | `corpus/local/<目录>/`（自行放入，不提交） | 目录名 |

放入新资料后运行 `python tools/rag.py build`；教材的页码范围由 `tools/kb.py build` 写入分章文本。

### 7.2 重点文献

下列 14 篇文献的书目均已用 Crossref 的 DOI 接口核对（题名、作者、刊名、年、卷期页），要点以自述概括写入登记表 [`knowledge/literature/references.yaml`](knowledge/literature/references.yaml)，检索标签 `literature`。

<!-- REFLIST:START -->
| 序号 | 文献（GB/T 7714—2015） | 实验 |
|---|---|---|
| [1] | EDDLESTON M, BUCKLEY N A, EYER P, et al. Management of acute organophosphorus pesticide poisoning[J]. The Lancet, 2008, 371(9612): 597-607. DOI: 10.1016/S0140-6736(07)61202-1. | 1.5 |
| [2] | EDDLESTON M. Novel clinical toxicology and pharmacology of organophosphorus insecticide self-poisoning[J]. Annual Review of Pharmacology and Toxicology, 2019, 59: 341-360. DOI: 10.1146/annurev-pharmtox-010818-021842. | 1.5 |
| [3] | EDDLESTON M, EYER P, WOREK F, et al. Pralidoxime in acute organophosphorus insecticide poisoning—a randomised controlled trial[J]. PLoS Medicine, 2009, 6(6): e1000104. DOI: 10.1371/journal.pmed.1000104. | 1.5 |
| [4] | ELLMAN G L, COURTNEY K D, ANDRES V Jr, et al. A new and rapid colorimetric determination of acetylcholinesterase activity[J]. Biochemical Pharmacology, 1961, 7(2): 88-95. DOI: 10.1016/0006-2952(61)90145-9. | 1.5 |
| [5] | BRIGGS G E, HALDANE J B S. A note on the kinetics of enzyme action[J]. Biochemical Journal, 1925, 19(2): 338-339. DOI: 10.1042/bj0190338. | 1.5 |
| [6] | SCHILD H O. pA, a new scale for the measurement of drug antagonism[J]. British Journal of Pharmacology and Chemotherapy, 1947, 2(3): 189-206. DOI: 10.1111/j.1476-5381.1947.tb00336.x. | 1.5, 5.2 |
| [7] | ARUNLAKSHANA O, SCHILD H O. Some quantitative uses of drug antagonists[J]. British Journal of Pharmacology and Chemotherapy, 1959, 14(1): 48-58. DOI: 10.1111/j.1476-5381.1959.tb00928.x. | 5.2, 1.5 |
| [8] | WEISBERG L S. Management of severe hyperkalemia[J]. Critical Care Medicine, 2008, 36(12): 3246-3251. DOI: 10.1097/CCM.0b013e31818f222b. | 2.7 |
| [9] | LEVI M, TEN CATE H. Disseminated intravascular coagulation[J]. New England Journal of Medicine, 1999, 341(8): 586-592. DOI: 10.1056/NEJM199908193410807. | 4.3 |
| [10] | TAYLOR F B Jr, TOH C H, HOOTS W K, et al. Towards definition, clinical and laboratory criteria, and a scoring system for disseminated intravascular coagulation[J]. Thrombosis and Haemostasis, 2001, 86(11): 1327-1330. DOI: 10.1055/s-0037-1616068. | 4.3 |
| [11] | SEMENZA G L. Oxygen sensing, homeostasis, and disease[J]. New England Journal of Medicine, 2011, 365(6): 537-547. DOI: 10.1056/NEJMra1011165. | 3.2 |
| [12] | LEI M, WU L, TERRAR D A, et al. Modernized classification of cardiac antiarrhythmic drugs[J]. Circulation, 2018, 138(17): 1879-1896. DOI: 10.1161/CIRCULATIONAHA.118.035455. | 2.4, 2.4s |
| [13] | SANDERS K M, KOH S D, RO S, et al. Regulation of gastrointestinal motility—insights from smooth muscle biology[J]. Nature Reviews Gastroenterology & Hepatology, 2012, 9(11): 633-645. DOI: 10.1038/nrgastro.2012.168. | 5.2 |
| [14] | LORKE D. A new approach to practical acute toxicity testing[J]. Archives of Toxicology, 1983, 54(4): 275-287. DOI: 10.1007/BF01234480. | 8.1 |
<!-- REFLIST:END -->

查看某实验可用的文献：`python tools/rag.py search 关键词 -c literature --exp 1.5`。

### 7.3 新增文献

```bash
python tools/refcheck.py fmt 10.1016/S0140-6736(07)61202-1   # 由 DOI 生成 GB/T 7714 条目并核对
# 把条目写入 knowledge/literature/references.yaml（含 verified 字段）
python tools/make_reflist.py                                  # 更新本节与 reference/literature/README.md
python tools/refcheck.py --registry                           # 联网复核全部登记条目
```

### 7.4 参考文献格式（GB/T 7714—2015，顺序编码制）

| 类型 | 格式 |
|---|---|
| 期刊 | 作者. 题名[J]. 刊名, 年, 卷(期): 起止页. DOI. |
| 图书 | 作者. 书名[M]. 出版地: 出版者, 年: 页码. |
| 作者 | 西文姓大写、名缩写，前 3 位后加 “, et al”；中文作者姓名全写 |
| 正文引用 | 按出现顺序编号，写作 [1]、[1,3]、[2–4] |

## 8 示例

<div align="center"><img src="assets/readme/preview.png" alt="示例报告：封面、结果页（图 1 与 LDq 表）、敏感性分析页（图 3）" width="100%"><br>
<sub>示例报告《药物半数致死量（LD50）的测定》：封面 · 图 1 剂量–效应曲线与似然剖面及 LDq 表 · 图 3 阈值分布与给药误差传播（<a href="examples/sample-report/report.md">源文件</a> · <a href="examples/sample-report/report.docx">Word</a>）</sub></div>

示例以课堂实验的汇总数据（110 只小鼠，5 个剂量组，每组 22 只）为输入，展示各工具如何产出报告中的数字和图：

| 环节 | 工具 | 示例中的产出 |
|---|---|---|
| 教材方法 | `labcalc ld50` | 改良寇氏法 LD50 = 191.85 mg/kg，95% CI 178.25–206.48 |
| 模型比较 | `labdose` | Probit 193.10、Logit 191.92 mg/kg；AIC 13.823 / 13.901；偏差 1.859（P = 0.602） |
| 稳健性（图 2） | `labdose` | Pearson 残差、参数 bootstrap（3 000 次）、留一剂量组 LD50 范围 187.4–203.5 mg/kg |
| 局部敏感性（图 3） | `labdose` | 阈值耐受分布；给药体积 ±0.01 mL 对应的死亡率偏离 |
| 语言 | `style_profile`、`style_check` | 术语覆盖与相似度检查 |
| 文献 | `ref_check` | 参考文献逐项核对 |

附录列出可复现的全部命令。

## 9 模板与格式规范

通用模板由写作内容、格式要求和字体三部分组成，Word 与 LaTeX 各一份，封面为单一极简线稿（兔或小鼠，由 `animal` 选择），正文页带页眉。

| 文件 | 说明 |
|---|---|
| [`templates/word/功能学科实验报告模板.docx`](templates/word) | Word 通用模板：封面、目录、页眉、各节写作提示 |
| [`templates/latex/`](templates/latex) | `report-template.tex` + `fdureport.cls`（XeLaTeX，ctex）；整个文件夹可上传 Overleaf |
| [`templates/report-skeleton.md`](templates/report-skeleton.md) | Markdown 骨架，供 `build.py` 出稿 |
| [`templates/FORMAT.md`](templates/FORMAT.md) | 完整格式规范 |

| 项目 | 规定 |
|---|---|
| 版面 | A4；上下 2.54 cm，左右 3.0 cm |
| 正文 | 宋体（西文 Times New Roman），小四，1.5 倍行距，首行缩进 2 字符 |
| 标题 | 黑体：一级三号、二级四号、三级小四，加粗 |
| 图表 | 三线表，表题在上、图题在下，宋体五号；图注写明 n 与误差线含义 |
| 页码 | 目录罗马数字，正文阿拉伯数字 |
| 结构 | 摘要（200–300 字）→ 引言 → 材料与方法 → 结果 → 讨论 → 结论 → 参考文献 → 附录 |

## 10 目录结构

```
.agents/skills/        12 个 Skill（SKILL.md）
mcp_server/server.py   MCP 服务
tools/                 10 个工具 + 构建脚本
prompts/menu.md        总菜单
reference/             教材、讲义、重点文献目录（RAG 原料）
knowledge/             知识卡 · 课本表述 · 文献登记 · 文风画像
corpus/local/          自行放入的其他教材与文献（不提交）
templates/             Word / LaTeX / Markdown 模板与格式规范
examples/sample-report 示例报告
tests/                 单元测试
install.py             一键安装
```

## 11 开发与测试

```bash
python -m unittest discover tests          # 单元测试
python tools/card_index.py --check         # 知识卡校验
python tools/refcheck.py --offline examples/sample-report/report.md
python tools/make_arch.py                  # 重新生成架构图与 RAG 图
```

提交遵循：数字与引用由工具产出；新增知识卡须通过 `card_index --check`；新增文献须先 `refcheck fmt` 核对；不提交学生个人报告（`reports/`）。CI（`.github/workflows/ci.yml`）运行测试并构建示例。

## 12 引用与许可

```bibtex
@software{liu2026fdufunclab,
  author  = {刘瑞琦},
  title   = {FDU Func Lab Helper: 复旦大学《功能学科综合实验》实验报告写作助手},
  year    = {2026},
  url     = {https://github.com/rachael1216/fdu-func-lab-helper}
}
```

代码以 [MIT](LICENSE) 发布。第三方组件：pandoc（GPL，外部程序）、python-docx（MIT）、PyYAML（MIT）、SciPy / NumPy（BSD-3）、matplotlib（matplotlib License）、PyMuPDF（可选，AGPL，仅本机使用）、XeLaTeX / ctex（LPPL）。文献书目来自 Crossref REST API。教材版权归出版社所有。
