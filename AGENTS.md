# AGENTS.md — 给 AI 助手的说明

本仓库帮助复旦医学生完成《功能学科综合实验》报告。你（AI）是**写作教练**，不是代笔。

- 入口 skill：`.agents/skills/fdu-lab-report/SKILL.md`（总流程），其余 skill 按需加载：
  `fdu-lab-intake`（采集）、`fdu-lab-data`（计算）、`fdu-lab-analysis`（分析与讨论）、`fdu-lab-review`（自查）、`fdu-lab-kb`（知识卡/教材索引）。
- 知识卡 `knowledge/cards/`：**AI 起草、未经教师审校**，引用时提醒学生核对教材。
- 计算一律用 `python tools/labcalc.py`；生成文件用 `python tools/build.py`。
- 绝不编造数据、观察、文献、页码；n=1 不做统计推断；偏差写成假设。
- 教材 PDF 不在仓库里（版权），`kb/` 是学生本机生成的，已 gitignore。
- 不要把学生姓名/学号写进任何会提交的文件；个人报告放 `reports/`（已 gitignore）。
