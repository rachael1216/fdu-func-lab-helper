---
name: fdu-lab-kb
description: 查询功能学实验知识卡（机制链、预期现象、偏差、临床联系）和学生本地教材索引（kb/）。需要某个实验的背景、记录单或教材页码引用时使用。
---

# 知识库

1. 先查 `knowledge/index.yaml` 找到实验 id，再读 `knowledge/cards/ex_<id>.md`。
   卡片状态 `review_status: draft-ai` 表示 **AI 起草、未经教师审校**，回答时提醒学生以教材/老师为准。
2. 学生本地教材索引（可选，自行用自己的教材 PDF 生成，**教材不随仓库分发**）：
   ```
   python tools/kb.py build 功能学科实验教程.pdf     # 首次
   python tools/kb.py find 高钾血症                   # 检索
   python tools/kb.py show 2.7                        # 看某实验原文
   python tools/kb.py cite 3.1                        # 生成参考文献/页码引用
   ```
3. 引用教材时用 `kb.py cite` 的输出，不要凭记忆写页码。
4. 查不到就如实说“知识库里没有”，不要编。
