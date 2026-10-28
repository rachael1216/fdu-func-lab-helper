# AGENTS.md

本仓库为复旦大学《功能学科综合实验》提供报告写作助手（本地 RAG + 12 个 Skill + 总菜单 + MCP 服务）。AI 助手在其中担任写作教练。

## 入口
- 新会话先展示总菜单：MCP 工具 `fdu_lab_menu`，或读取 `.agents/skills/fdu-lab-menu/menu.md`。
- 总调度 skill：`.agents/skills/fdu-lab-report/SKILL.md`；阶段 skill 按需加载：`intake` `rag` `data` `stats` `plot` `analysis` `style` `cite` `review` `format`。
- 通过 MCP 使用时，`tools/*.py` 对应的 MCP 工具为 `rag_search` `lab_calc` `lab_stats` `lab_dose` `lab_plot` `style_check` `style_profile` `ref_check` `ref_format` `build_report`。

## 工作规则
- 数字、检验、引用、相似度、排版由工具产出，不心算、不凭记忆。
- 写作前先检索：`rag_search`（`-c expr --exp <编号>` → `-c textbook --full` → `-c literature`），采用课本术语与判定标准，用自己的句子表述；页码取自检索结果。
- 课本以外的引用只来自 `reference/literature/` 的登记文献；新增文献先 `refcheck fmt` 核对。
- 数据、观察、文献、页码、P 值只来自学生与工具，缺依据时写“待核”。
- n = 1 只描述；偏差写成假设并给出验证方式。
- `reference/cards/` 与 `reference/expressions/` 为 AI 起草，与教材冲突时以教材和教师要求为准。
- 个人报告放 `reports/`（已忽略）；仓库文件不写入学生姓名与学号。

## 开发
- 测试：`python -m unittest discover tests`；知识卡：`python tools/card_index.py --check`；文献：`python tools/refcheck.py --offline <report.md>`。
- 改动工具后同步更新对应 skill、`tools/mcp_server.py` 的工具说明和 README。
- 图：`python tools/dev/make_arch.py`。
