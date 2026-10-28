# 贡献指南

最有价值的贡献：**审校/补全知识卡**。

1. 复制 `knowledge/cards/ex_2.7.md` 的结构（full）或任一 lite 卡。
2. 必填 front matter：`id,title,system,animal,depth,textbook_pages,review_status`。
3. 审校后把 `review_status: draft-ai` 改为 `reviewed`，并在“参考来源”写明依据（教材页/老师/文献）。
4. 运行 `python tools/card_index.py`（校验并更新索引）与 `python -m unittest discover tests`。
5. 不要提交教材原文、个人报告、含姓名学号的文件。

提 PR 前请确认：数据与文献真实、无编造。

## 其他贡献方式
- **补充课本表述**：参照 `knowledge/expressions/ex_2.7.md` 的结构，只写术语、改写后的句式与页码，**不要粘贴教材原文**。
- **补充文献**：在 `knowledge/literature/references.yaml` 加条目，先用 `python tools/refcheck.py fmt <DOI>` 核对书目，要点用自己的话写。
- 提交前运行 `python -m unittest discover tests`。
