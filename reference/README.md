# reference · 参考资料库

RAG 检索的全部“原料”和报告模板，按用途分为三部分。

## ① 主要用于 RAG 的书籍

| 位置 | 内容 | 状态 | 检索标签 |
|---|---|---|---|
| `reference/textbook/功能学科实验教程.pdf` | 《功能学科实验教程》（严钰锋、马淑兰 主编，2020），219 页 | 已入库 | `textbook` |
| `reference/textbook/ex_*.md`、`tech_*.md` | 上书按实验编号切分的文本（`tools/kb.py build` 生成，含页码） | 已入库 | `textbook` |
| `reference/lecture/` | 课程讲义、实验指导（pdf/docx/md/txt） | 自行放入 | `lecture` |
| `corpus/local/<目录>/` | 其他同类中文教材（《生理学》《病理生理学》《药理学》）等 | 自行放入 | 目录名 |

> 版权提示：课本由仓库作者决定入库。若你 fork 后要公开分享，请先确认出版社许可，或删除 `reference/textbook/*.pdf` 仅保留自己本机使用。

建议补充的中文教材见 `corpus/README.md`。放入后运行 `python tools/rag.py build`。

## ② 重点文献目录

课本之外、优先进入 RAG 的文献：[`literature/README.md`](literature/README.md)（14 篇，书目均经 Crossref 核对，附 GB/T 7714 条目和相关实验）。
结构化登记表：`knowledge/literature/references.yaml`；全文 PDF 请自行下载放入 `corpus/local/literature/`。
新增文献：先 `python tools/refcheck.py fmt <DOI>` 核对，再写入登记表，最后 `python tools/make_reflist.py` 更新目录。

## ③ 模板（Template）

> **通用模板 = 写作内容 + 格式要求 + 字体**，Word 与 LaTeX 各一份，封面单一极简。

| 文件 | 说明 |
|---|---|
| `templates/word/功能学科实验报告模板.docx` | Word 通用模板：封面、目录、页眉、各节写作提示 |
| `templates/latex/report-template.tex` + `fdureport.cls` | LaTeX 通用模板（XeLaTeX，需 ctex；或整个文件夹传到 Overleaf） |
| `templates/report-skeleton.md` | Markdown 骨架（供 `tools/build.py` 出稿） |
| `docs/FORMAT.md` | 格式规范：页边距、字体字号、标题、图表、参考文献 |
