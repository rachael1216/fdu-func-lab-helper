---
name: fdu-lab-menu
description: 功能学实验助手的总菜单：用户刚打开、说“帮我写实验报告/你能做什么/菜单”、或不知道从哪开始时使用；列出 12 项功能并路由到对应 skill。
---

# 总菜单

完整提示词在 `.agents/skills/fdu-lab-menu/menu.md`（读取并按其中“菜单”表格原样展示，再等学生选择）。

要点：
1. 先展示菜单（12 项：写报告、查课本、算数据、统计、画图、写讨论、润色、核对文献、整份检查、出稿、模板、排错）。
2. 学生选编号后，加载对应 skill：1→`fdu-lab-report`，2→`fdu-lab-rag`，3→`fdu-lab-data`，4→`fdu-lab-stats`，5→`fdu-lab-plot`，6→`fdu-lab-analysis`，7→`fdu-lab-style`，8→`fdu-lab-cite`，9→`fdu-lab-review`，10/11→`fdu-lab-format`。
3. 成本先低后高：能用工具（L0）就不让模型长篇生成。
4. 底线：不编造；n=1 不推断；润色不改数据；不以规避 AI 检测为目的。
