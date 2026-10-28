# 设计说明（Architecture & Design）

> 本文面向希望理解、审校或扩展本项目的读者。快速使用请看 [README](README.md) 与 [docs/GUIDE.md](docs/GUIDE.md)。

## 1. 目标与约束

**要解决的四个问题**

| # | 问题 | 设计响应 |
|---|---|---|
| P1 | 报告用语偏离课本，术语与判定标准不一致 | 课本对齐的 RAG（§4）+ `stylecheck` 逐句比对 |
| P2 | 数据与统计处理不规范、模型“心算”出错 | 工具层确定性代码（§3.2），n=1 不检验 |
| P3 | 参考文献不存在或书目错误 | 预核对文献登记表 + `refcheck` 对 Crossref 逐项核对 |
| P4 | 学生无服务器、不一定会编程 | 无服务器；skill + 命令行；dsh / 网页 / 仅模板三种入口 |

**非功能约束**：数据留在本机；可复现（相同输入得到相同输出）；可测试（30+ 项单元测试）；对模型强度不敏感（关键步骤由工具兜底）；版权与隐私可控（§8）。

**非目标**：不替学生产生数据或观察；不做 AI 检测或规避；不提供在线服务。

## 2. 总体架构

![架构](assets/readme/architecture.svg)

五层，自上而下单向依赖：

| 层 | 目录 | 职责 | 对外接口 |
|---|---|---|---|
| 入口 | `prompts/`、`AGENTS.md` | 会话启动、菜单路由、底线声明 | 自然语言 |
| Skill 层 | `.agents/skills/` | 把“做什么、何时做、怎么调用工具、边界是什么”写成指令 | SKILL.md（触发描述 + 步骤） |
| 工具层 | `tools/` | 确定性计算与检查 | CLI：参数 → stdout，退出码 |
| 知识层 | `reference/`、`knowledge/`、`corpus/` | RAG 语料与登记表 | 文件格式（§6） |
| 产出 | `templates/`、`examples/` | 模板、示例、Word/tex/PDF | 文件 |

**一条设计原则贯穿全局**：模型负责理解、组织与措辞；**数字、检验、引用、相似度、排版由工具产出**，模型只转述并标注来源。这样即便换用能力较弱的模型，关键结论仍可复核。

### 2.1 一次完整写作的数据流

```
学生原始记录
  │ ① intake      逐组提问，形成结构化记录（动物/药品/时间点/数据/观察/与讲义不同处）
  ▼
 ② rag.py search  --exp <编号> -c expr → -c textbook --full → -c literature     （术语·句式·页码·文献）
  ▼
 ③ labcalc.py     剂量/浓度/LD50/MAP/变化率…                                   （命令+结果可复核）
 ④ labstats.py    选方法 → 检验；n=1 只描述                                      （统计句+边界）
 ⑤ labplot.py     规范作图 + 建议图注
  ▼
 ⑥ analysis       观察(事实) → 预期 → 机制 → 偏差(假设+验证) → 局限 → 临床联系
 ⑦ 写作           reports/<名>/report.md（YAML 头 + 正文）
  ▼
 ⑧ stylecheck.py  术语覆盖 · 模板腔 · 与课本相似度 · 格式细节                  （只提示，不改文字）
 ⑨ refcheck.py    DOI/题名/第一作者/年份/卷页 vs Crossref                        （OK/WARN/FAIL/CHECK）
 ⑩ review         分级问题清单（必须改/建议改/可选）
  ▼
 ⑪ build.py       docx / tex / pdf（封面·目录·页眉·页码）
```
不必每次走完：总菜单（`prompts/menu.md`）按“我想……”路由到单个阶段，并按成本分级（L0 纯工具 / L1 检索+短生成 / L2 完整起草）先低后高。

## 3. 组件规格

### 3.1 Skill 层（12 个）
**契约**：每个 skill 是一个目录，含 `SKILL.md`：YAML 头（`name`、`description` = 触发条件）+ 正文（步骤、命令、边界）。dsh 等 harness 依据 `description` 自动发现并按需加载，**每个 skill 只做一件事**，避免上下文膨胀。

| skill | 触发 | 调用的工具/资源 | 输出 | 主要边界 |
|---|---|---|---|---|
| `menu` | 新会话/“能做什么” | `prompts/menu.md` | 12 项菜单+路由 | 先展示菜单 |
| `report` | 写整份报告 | 其余全部 | 流水线编排 | 硬规则总守门 |
| `intake` | 采集信息 | – | 结构化记录 | 一次问一组，不替学生编观察 |
| `rag` | 需要课本措辞/页码 | `rag.py` | 片段+出处 | 页码取自检索 |
| `data` | 计算 | `labcalc.py` | 命令+结果 | 不心算 |
| `stats` | 多组数据/“显著吗” | `labstats.py` | 统计句 | n=1 不检验；多重比较要校正 |
| `plot` | 作图 | `labplot.py` | 图+图注 | 误差线含义与 n 入图注 |
| `analysis` | 写讨论 | `expressions/`、`cards/` | 论证段落 | 偏差写成假设 |
| `style` | 润色/贴近课本 | `stylecheck.py` | 问题清单 | 不改数据与结论；非规避检测 |
| `cite` | 参考文献 | `refcheck.py`、登记表 | 核对清单 | 通过≠支持论点 |
| `review` | 整份检查 | 以上工具 | 分级清单 | 不直接大改学生文字 |
| `format` | 出稿/模板 | `build.py` | docx/tex/pdf | 规范见 `docs/FORMAT.md` |

### 3.2 工具层（CLI 契约）
统一约定：参数 → stdout（人读；`--json` 机读）；错误信息写 stderr 或 stdout 并以**非零退出码**结束；不联网（除 `refcheck`）；无隐藏状态。

| 工具 | 算法/要点 | 验证 |
|---|---|---|
| `rag.py` | 词法 BM25，见 §4 | `test_rag_style` |
| `labcalc.py` | 教材公式：给药体积、稀释还原、改良寇氏法 LD50、治疗指数、MAP、AChE 活力、肺系数、HRV 时域、Fisher 精确检验… | 对照教材例题 |
| `labstats.py` | SciPy：描述、Shapiro-Wilk、Welch/配对/等方差 t、单因素 ANOVA+Tukey、Mann-Whitney、Pearson/Spearman、线性回归；`advise` 给方法选择；n<2 拒绝 | `test_labstats` |
| `labplot.py` | Okabe-Ito 配色 + 标记/线型/填充区分；刻度朝内、去上右边框；SD/SEM 可选并生成建议图注；剂量-反应+概率单位图 | `test_labplot` |
| `stylecheck.py` | ①术语覆盖（`expressions/ex_*.md` 的“术语”）②`avoid.yaml` 口语/模板腔 ③逐句与课本相似度 = 句中字二元组被某片段**包含**的比例（≥0.60 过近；<0.15 缺依据）④数字单位/标点格式 | `test_rag_style` |
| `refcheck.py` | 有 DOI：Crossref 取书目，比对题名、第一作者、年份、卷、页；无 DOI：检索给候选，不自动采信；中文/图书标人工核对；`--offline` 对照登记表；`fmt` 由 DOI 生成 GB/T 7714 | `test_refcheck`（mock） |
| `build.py` | Markdown+YAML → pandoc → docx（`reference.docx` 样式母版 + python-docx 后处理：封面分节、罗马/阿拉伯页码、三线表、页眉）或 tex（`fdureport.cls`，基于 ctexart） | `test_build` |
| `kb.py` | 教材 PDF 按实验编号切分为 `reference/textbook/ex_*.md`（含页码） | – |

## 4. 知识层与 RAG

![RAG 管线](assets/readme/rag-pipeline.svg)

### 4.1 为什么要 RAG
报告的**措辞**（术语、机制表述、判定标准）应与课本一致。仅靠模型记忆容易出现“通用医学腔”和不存在的页码。RAG 让写作**先检索、再据片段措辞，并带出处**；`stylecheck` 再用同一语料反向检查。

### 4.2 语料与标签
| 标签 | 位置 | 内容 | 粒度 | 状态 |
|---|---|---|---|---|
| `textbook` | `reference/textbook/` | 《功能学科实验教程》PDF + 按实验/章节的文本 | 【目的】【原理】【步骤】…各一段，带页码范围 | 已入库 |
| `lecture` | `reference/lecture/` | 讲义、实验指导 | ≤380 字段落 | 自行放入 |
| 本地目录名 | `corpus/local/<目录>/` | 其他同类中文教材、文献全文（pdf/docx/md/txt） | ≤380 字段落 | 自行放入，gitignore |
| `card` | `knowledge/cards/` | 机制链、预期现象、常见偏差、临床联系 | “## ”小节 | **AI 草稿** |
| `expr` | `knowledge/expressions/` | 各实验术语、改写后的句式、页码（无教材原文） | “## ”小节 | **AI 整理，待核** |
| `literature` | `knowledge/literature/references.yaml` | 重点文献书目（Crossref 核对）+ 自述要点 | 1 条 1 片 | 书目已核 |

### 4.3 检索算法
- **分词**：中文取相邻汉字二元组（单字成词时取单字），英文/数字取小写词；无需词典、无需模型，结果完全可复现。
- **打分**：BM25，`k1 = 1.5`，`b = 0.75`；`idf = ln(1 + (N − df + 0.5)/(df + 0.5))`；平均长度在建索引时统计。
- **过滤**：`-c` 语料标签（可多个）、`--exp` 实验编号。
- **返回**：`[序号] (标签) 来源 · 出处定位 score  片段`。出处定位形如 `实验3.1【原理】 p.124-125`，引用页码**只取自这里**。
- **索引**：`corpus/index/rag.json`（`n`、`avg`、`df`、`docs[{corpus, source, exp, locator, text, tok, len}]`），当前约 1 000 个片段，毫秒级查询。
- **规模**：线性扫描，适合数千片段；语料上万段时应换倒排或外部检索。

### 4.4 检索协议（`fdu-lab-rag`）
1. `-c expr --exp <编号>`：该实验的术语表、句式、页码；
2. `-c textbook --full`：看课本原文段落，据其**术语与判定标准**用**自己的句子**表述；
3. 课本没有的（机制深化、临床联系）：`-c literature` 或 `corpus/local/`；仍没有就写“待核”，不编。

### 4.5 为什么是词法检索，以及与 local-rag-cpp 的关系
本任务的查询多是**术语类**（“高钾血症”“复能剂”“肺牵张反射”），语料是**结构化教材**，词法匹配稳定、可解释、零依赖。代价是不理解同义改写。
作者的另一个项目 **[local-rag-cpp](https://github.com/rachael1216/local-rag-cpp)**（C++ / llama.cpp，本地**稠密向量**检索 + 本地小模型问答，bge-small-zh 嵌入，无需联网）与本项目互补：

| | 本项目 `rag.py` | local-rag-cpp |
|---|---|---|
| 检索 | 词法 BM25 | 稠密向量（余弦相似度） |
| 擅长 | 术语精确匹配、带页码出处、与 skill/工具联动 | 同义改写、自然语言整句提问 |
| 依赖 | Python 标准库 | CMake、GCC 14、GGUF 模型 |
| 形态 | 命令行 + skill | 终端问答 |

`python tools/rag.py export` 会把全部语料导出为带“第N章”标题的纯文本（`corpus/index/corpus.txt`），其格式按 local-rag-cpp 的输入约定设计，可用于离线稠密检索试验；**作者尚未做端到端联调**，视为可选扩展。

## 5. 分析问题：三道防线
1. **确定性**：计算、统计、作图全部走代码，模型不心算。
2. **有据**：机制句来自 `textbook / expr / literature`，找不到依据写“待核”。
3. **论证协议**（`fdu-lab-analysis`）：观察（事实）→ 与预期比较 → 机制 → 偏差作为假设并给出验证方式 → 局限 → 临床联系。n=1 只描述；多组才检验；统计只回答“差异是否可能由随机波动造成”，不回答机制。

## 6. 数据格式（接口）
- **报告** `report.md`：YAML 头 `title, course, exp_no, class, student, student_id, group, date, teacher, animal, ai_statement` + Markdown 正文；`# 参考文献 {-}` 起为文献列表。
- **课本表述** `knowledge/expressions/ex_<编号>.md`：front matter（`id, title, kind: expr, textbook_pages, review_status`）+ 小节 `术语 / 目的与原理句式 / 方法措辞 / 结果描述 / 讨论抓手 / 出处`；`（待核）` 标记无教材依据的条目。
- **文献登记** `references.yaml`：`id, authors, et_al, title, journal, year, volume, issue, pages, doi, experiments, keywords, key_points, verified{method,date}`。
- **知识卡** `knowledge/cards/ex_<编号>.md`：`id, title, system, animal, depth, textbook_pages, review_status` + 机制链等；`card_index.py --check` 校验。

## 7. 质量保证
| 失败模式 | 对策 | 机制 |
|---|---|---|
| 编造数据/观察 | 数据只来自学生；总调度硬规则 | skill 约束 |
| 编造/错引文献 | 登记表预核对；`refcheck` 逐项比对 | 工具 + CI（离线） |
| 页码凭记忆 | 页码取自 `rag.py` 出处定位 | 协议 |
| 照抄课本 | `stylecheck` 相似度 ≥0.60 提示 | 工具 |
| 小样本滥用检验 | n=1 不检验，n<2 拒绝，提示正态性检验无检验力 | 工具 |
| 把偏差硬凑成“符合理论” | 偏差=假设+验证方式 | analysis |
| 模板腔/口语 | `avoid.yaml` 词表 + 改法 | 工具 |

**测试**：`python -m unittest discover tests`（统计、作图、检索与语言检查、文献核对（mock）、出稿）；CI 另跑 `card_index --check`、`refcheck --offline` 与示例出稿（含 XeLaTeX）。

## 8. 隐私、版权与安全
- 数据留在本机；API Key 只填在 dsh 设置里，不写入仓库。
- 课本放在 `reference/textbook/`，由仓库作者决定入库，**公开分发前需确认出版社许可**；其余语料 `corpus/local/` 默认 gitignore。
- `reports/`、`prompts/out/`、`corpus/index/` gitignore；仓库不含同学姓名学号或报告内容，示例已隐去身份信息。
- `refcheck` 请求不携带个人信息；可选 `CROSSREF_MAILTO` 自行设置。

## 9. 局限与路线
- 知识卡与课本表述整理未经教师审校；表述整理目前覆盖 7 个实验，文献登记 14 篇。
- 词法检索不理解同义改写（可选接入稠密检索，见 §4.5）。
- LaTeX 路径需在真实 ctex 环境验证（CI 已配置）；dsh 步骤尚未由作者完整实测。
- 路线：补全其余实验的表述整理；教师审校流程；更多文献与讲义语料；与 local-rag-cpp 联调。
