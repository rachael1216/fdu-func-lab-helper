---
name: fdu-lab-rag
description: 检索课本、讲义、实验知识卡、课本表述整理和重点文献，让报告用语贴近课本并能回到出处。写“原理/方法/讨论”、需要课本术语或页码、需要核对某个说法有没有依据时使用。
---

# 检索（RAG）· 让用语贴近课本

**为什么检索**：报告的术语、机制表述、判定标准应与课本一致。写之前先检索，据片段措辞，不凭记忆。

## 语料（每条结果带来源标签）
| 标签 | 内容 | 说明 |
|---|---|---|
| `textbook` | `reference/textbook/` 教材分章文本 | 已入库；`kb.py build` 可用自己的 PDF 重建 |
| `expr` | `knowledge/expressions/ex_*.md` | 各实验课本术语、句式、页码（AI 整理，待核） |
| `card` | `knowledge/cards/ex_*.md` | 机制链、预期现象、偏差（AI 起草，待核） |
| `literature` | `knowledge/literature/references.yaml` | 已核对书目的重点文献 + 要点 |
| 自定名 | `corpus/local/<目录>/` | 学生自放的讲义、其他教材、文献全文 |

## 命令
```
python tools/rag.py build                       # 首次或增删语料后
python tools/rag.py sources                     # 看各语料有多少片段
python tools/rag.py search 高钾血症 T波 -k 5
python tools/rag.py search 复能剂 -c literature
python tools/rag.py search 瞳孔 缩小 --exp 1.5 -c textbook --full
```
查询词用 2–4 个关键词，不要写整句。

## 用法
1. 先 `--exp <编号> -c expr` 取该实验的术语表与句式；再 `-c textbook --full` 看原文段落。
2. 课本没有而报告需要的内容（机制深化、临床联系），去 `-c literature` 或 `corpus/local/` 找；找不到就写“待核”，**不要编**。
3. 引用课本写“（教材 p.xx）”，页码取自检索结果，不凭记忆。
4. 用课本的**术语与判定标准**，用自己的**句子**：不整段照抄；相似度检查见 `fdu-lab-style`。
5. `expr`/`card` 是 AI 草稿，与教材冲突时以教材为准，并告诉学生。
