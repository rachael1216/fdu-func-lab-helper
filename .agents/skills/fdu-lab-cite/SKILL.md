---
name: fdu-lab-cite
description: 参考文献的选择、格式化与核对：用已核对的重点文献登记表，联网校验 DOI/题名/作者/年份/卷页，防止编造或张冠李戴。报告写到引用、参考文献时使用。
---

# 文献核对

## 原则
1. 先用登记表：`python tools/rag.py search <关键词> -c literature`，取登记表里**已核对**的条目。
2. 登记表没有的文献，由学生提供题名/DOI；你**不得凭记忆补全作者、卷期、页码**。
3. 写完用 `refcheck` 核对：
```
python tools/refcheck.py reports/<名>/report.md            # 联网核对（Crossref）
python tools/refcheck.py reports/<名>/report.md --offline  # 只对照登记表
python tools/refcheck.py fmt 10.1016/S0140-6736(07)61202-1 # 由 DOI 生成 GB/T 7714 条目
```
## 状态含义
OK 通过 · WARN 有出入（逐项列出，按权威书目改）· FAIL DOI 不存在（多为编造或抄错，必须处理）· CHECK 中文文献/图书/教材，需人工核对。

## 边界
- 核对通过只说明“这篇文献存在且书目正确”，**不说明它支持你的论点**；论点是否被支持，必须学生读过原文。
- 引用正文用 [1] 顺序编码，列表用 GB/T 7714，含 DOI（见 `docs/FORMAT.md` §6）。
- 教材引用写“（教材 p.xx）”并列入参考文献，页码来自检索而非记忆。
- 条目是否被登记表标注 `et_al: true` 表示作者列表为截断，补全以 DOI 页面为准。
