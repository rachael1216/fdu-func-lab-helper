<div align="center">

# FDU Func Lab Helper

**A report-writing assistant for the Fudan course *Functional Science Integrated Laboratory*: textbook retrieval + writing skills + verifiable calculation and citation tools**

**English** · [中文](README.md)

**Ruiqi Liu (刘瑞琦)**<br>Huashan Clinical Medical College, Fudan University<br>Class of 2024, five-year clinical medicine<br><a href="mailto:24301050114@m.fudan.edu.cn">24301050114@m.fudan.edu.cn</a>

[![license](https://img.shields.io/badge/license-MIT-5F7568)](LICENSE)
[![python](https://img.shields.io/badge/python-3.10%2B-5F7568)](requirements.txt)
[![skills](https://img.shields.io/badge/skills-12-5F7568)](.agents/skills)

<img src="assets/readme/architecture.svg" alt="RAG + skill architecture" width="100%">

</div>

## Abstract

Student lab reports commonly suffer from wording that drifts from the textbook, unprincipled statistics, and references that cannot be verified. This project addresses each with a separate layer. A **retrieval layer** indexes the textbook, lecture notes, per-experiment wording notes and key literature, so that terminology matches the textbook and every claim can be traced to a source. A **tool layer** performs calculation, statistics, plotting, language checks and citation checks deterministically in code. A **skill layer** orchestrates these into a writing pipeline in which the AI acts as a coach, not a ghost-writer. No server is required: it runs in the student's own DeepSeek Harness (dsh) or in a chat window. Word and LaTeX templates are included (one minimal cover, running header, three-line tables, GB/T 7714).
**Raw data and observations must come from the student's own experiment. The project is not meant to evade AI detection; declare AI use as the course requires.** The course materials are in Chinese, so the tools and skills are too.

## What it does

| Need | Component |
|---|---|
| Textbook-faithful wording | `tools/rag.py` (BM25 retrieval), `tools/stylecheck.py` (term coverage, template tone, per-sentence similarity to the textbook) |
| Key literature beyond the textbook | `knowledge/literature/`: 14 papers with bibliographic data verified against Crossref |
| Reference checking | `tools/refcheck.py`: DOI, title, first author, year, volume and pages; `fmt` builds GB/T 7714 entries |
| Data processing | `tools/labcalc.py`, `tools/labstats.py` (t-test, ANOVA + Tukey, rank-sum, correlation, regression) |
| Figures | `tools/labplot.py` and the plotting rules in `docs/FORMAT.md` |
| Templates | Word and LaTeX general templates covering content, requirements and fonts |

## Quick start

Requires Python ≥ 3.10 and pandoc (XeLaTeX with ctex for PDF).

```bash
git clone https://github.com/rachael1216/fdu-func-lab-helper.git
cd fdu-func-lab-helper && pip install -r requirements.txt
python tools/build.py --doctor
python tools/build.py examples/sample-report/report.md --to all
npx @deepseek-ai/dsh web     # then follow docs/GUIDE.md
```

## Related project

[**local-rag-cpp**](https://github.com/rachael1216/local-rag-cpp) (C++ / llama.cpp, local dense-vector question answering) complements this lexical retriever: use `python tools/rag.py export` to dump the corpus as chapter-headed plain text for it (not yet tested end to end). Architecture details: [DESIGN.md](DESIGN.md).

## Examples

See the Chinese README for screenshots. Typical commands:

```bash
python tools/rag.py search hyperkalemia --exp 2.7
python tools/labstats.py ttest --a 5.1 4.8 5.5 --b 6.2 6.0 6.8
python tools/refcheck.py reports/x/report.md
```

## How it works

Retrieval is BM25 over CJK character bigrams plus Latin words (pure Python). `stylecheck` flags sentences with similarity ≥ 0.60 to a textbook chunk (too close) or < 0.15 (no textbook basis). Statistics refuse n < 3 and never infer at n = 1. `refcheck` compares each entry with Crossref; a pass means the paper exists and the metadata is right, not that it supports your argument. See [DESIGN.md](DESIGN.md).

## Settings

Cover animal (`animal: rabbit|mouse` in the YAML header), corpora (`reference/`, `corpus/local/`), avoided phrases (`knowledge/style/avoid.yaml`), similarity thresholds (`stylecheck.py --high/--low`).

## Known limits

Cards and wording notes are AI drafts and unreviewed by instructors; the textbook is included in `reference/textbook/` at the repo owner's discretion (check licensing before redistributing); dsh steps follow public documentation and have not been fully run by the author; the LaTeX path was smoke-tested with a stand-in class only; the literature registry covers 14 papers.

## Repository layout

See the Chinese README.

## Contact

Ruiqi Liu · Fudan University Shanghai Medical College · 24301050114@m.fudan.edu.cn

## Citation

```bibtex
@software{liu2026fdufunclabhelper,
  author  = {Liu, Ruiqi},
  title   = {FDU Func Lab Helper: a RAG and skill toolkit for writing functional-science laboratory reports},
  year    = {2026},
  url     = {https://github.com/rachael1216/fdu-func-lab-helper},
  license = {MIT}
}
```
See [CITATION.cff](CITATION.cff).

## License

MIT. Third-party notices in [THIRD_PARTY.md](THIRD_PARTY.md).

## Acknowledgements

The textbook *功能学科实验教程* (ed. Yan Yufeng & Ma Shulan, 2020), Crossref, pandoc, python-docx, SciPy and matplotlib.
