# corpus：语料目录

RAG 要检索的材料放在这里。**教材、讲义、文献全文有版权，不会提交到 GitHub**（`corpus/local/` 与 `corpus/index/` 已被 `.gitignore` 忽略），每位同学在本机放自己的资料。

```
corpus/
├── local/                 你自己的资料（不入库）
│   ├── textbook2/         子目录名就是检索时的语料标签（-c textbook2）
│   │   └── 病理生理学.pdf
│   ├── lecture/           课程讲义、实验指导 PPT 导出的 PDF
│   └── literature/        重点文献全文 PDF
└── index/rag.json         索引（python tools/rag.py build 生成）
```

支持 `.pdf`、`.docx`、`.md`、`.txt`。放好后运行：

```bash
python tools/kb.py build 功能学科实验教程.pdf    # 教材：按实验编号切分，写入 kb/
python tools/rag.py build                         # 建索引（教材 + 知识卡 + 表述库 + 文献登记 + corpus/local）
python tools/rag.py sources                       # 看看收进了哪些资料
```

## 建议补充的同类中文教材（请自备）

写作语言要贴近课本，不止功能学实验教程，可以再放入本课程相关理论教材与讲义，例如：

| 类别 | 与哪些实验相关 |
| --- | --- |
| 人民卫生出版社本科临床医学《生理学》 | 心血管、呼吸、消化、血液、泌尿、神经（2.x、3.x、5.x、1.x） |
| 人民卫生出版社本科临床医学《病理生理学》 | 缺氧、DIC、钾代谢紊乱、休克、心肺功能衰竭（2.6–2.10、3.2、3.3、4.3） |
| 人民卫生出版社本科临床医学《药理学》 | 胆碱受体药、抗心律失常药、药物量效关系与 LD50（1.5、2.4、5.2、8.x） |
| 课程组发的讲义、实验课 PPT | 本校实际方案（如氯化钡/家兔版本） |

版本按你们课程使用的为准。这些书的原文只在你的电脑上被检索，不会被上传。

## 重点文献

已核对书目的重点文献登记在 `knowledge/literature/references.yaml`（随仓库提供，仅含书目与要点概括）。
若你有全文 PDF，放进 `corpus/local/literature/` 即可被检索；新增文献条目前，先用 `python tools/refcheck.py` 核对。
