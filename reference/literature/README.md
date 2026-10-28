# 重点文献目录

课本之外、优先加入 RAG 的文献。书目均已用 Crossref 核对（见 `verified`）；要点为自述概括，不含原文。
用法：`python tools/rag.py search 关键词 -c literature`。全文 PDF 请自行下载后放入 `corpus/local/literature/`。

| 编号 | 文献（GB/T 7714） | 相关实验 | 关键词 |
|---|---|---|---|
| eddleston2008 | EDDLESTON M, BUCKLEY N A, EYER P, et al. Management of acute organophosphorus pesticide poisoning[J]. The Lancet, 2008, 371(9612): 597-607. DOI: 10.1016/S0140-6736(07)61202-1. | 1.5 | 有机磷、胆碱酯酶、阿托品、肟类复能剂、胆碱能危象 |
| eddleston2019 | EDDLESTON M. Novel clinical toxicology and pharmacology of organophosphorus insecticide self-poisoning[J]. Annual Review of Pharmacology and Toxicology, 2019, 59: 341-360. DOI: 10.1146/annurev-pharmtox-010818-021842. | 1.5 | 有机磷、自服中毒、药理学、临床毒理学 |
| eddleston2009 | EDDLESTON M, EYER P, WOREK F, et al. Pralidoxime in acute organophosphorus insecticide poisoning—a randomised controlled trial[J]. PLoS Medicine, 2009, 6(6): e1000104. DOI: 10.1371/journal.pmed.1000104. | 1.5 | 氯解磷定、碘解磷定、随机对照试验、复能剂 |
| ellman1961 | ELLMAN G L, COURTNEY K D, ANDRES V Jr, et al. A new and rapid colorimetric determination of acetylcholinesterase activity[J]. Biochemical Pharmacology, 1961, 7(2): 88-95. DOI: 10.1016/0006-2952(61)90145-9. | 1.5 | Ellman、胆碱酯酶活性、DTNB、比色法 |
| briggs1925 | BRIGGS G E, HALDANE J B S. A note on the kinetics of enzyme action[J]. Biochemical Journal, 1925, 19(2): 338-339. DOI: 10.1042/bj0190338. | 1.5 | 酶动力学、稳态假设、米氏方程 |
| schild1947 | SCHILD H O. pA, a new scale for the measurement of drug antagonism[J]. British Journal of Pharmacology and Chemotherapy, 1947, 2(3): 189-206. DOI: 10.1111/j.1476-5381.1947.tb00336.x. | 1.5, 5.2 | pA2、拮抗参数、竞争性拮抗 |
| arunlakshana1959 | ARUNLAKSHANA O, SCHILD H O. Some quantitative uses of drug antagonists[J]. British Journal of Pharmacology and Chemotherapy, 1959, 14(1): 48-58. DOI: 10.1111/j.1476-5381.1959.tb00928.x. | 5.2, 1.5 | Schild 作图、剂量比、pA2、竞争性拮抗 |
| weisberg2008 | WEISBERG L S. Management of severe hyperkalemia[J]. Critical Care Medicine, 2008, 36(12): 3246-3251. DOI: 10.1097/CCM.0b013e31818f222b. | 2.7 | 高钾血症、葡萄糖酸钙、胰岛素、心电图、抢救 |
| levi1999 | LEVI M, TEN CATE H. Disseminated intravascular coagulation[J]. New England Journal of Medicine, 1999, 341(8): 586-592. DOI: 10.1056/NEJM199908193410807. | 4.3 | 弥散性血管内凝血、组织因子、凝血酶生成、纤溶 |
| taylor2001 | TAYLOR F B Jr, TOH C H, HOOTS W K, et al. Towards definition, clinical and laboratory criteria, and a scoring system for disseminated intravascular coagulation[J]. Thrombosis and Haemostasis, 2001, 86(11): 1327-1330. DOI: 10.1055/s-0037-1616068. | 4.3 | DIC、ISTH、评分系统、血小板、纤维蛋白原 |
| semenza2011 | SEMENZA G L. Oxygen sensing, homeostasis, and disease[J]. New England Journal of Medicine, 2011, 365(6): 537-547. DOI: 10.1056/NEJMra1011165. | 3.2 | 缺氧、低氧诱导因子、HIF-1、氧稳态 |
| lei2018 | LEI M, WU L, TERRAR D A, et al. Modernized classification of cardiac antiarrhythmic drugs[J]. Circulation, 2018, 138(17): 1879-1896. DOI: 10.1161/CIRCULATIONAHA.118.035455. | 2.4, 2.4s | 抗心律失常药、Vaughan Williams 分类、利多卡因、钠通道 |
| sanders2012 | SANDERS K M, KOH S D, RO S, et al. Regulation of gastrointestinal motility—insights from smooth muscle biology[J]. Nature Reviews Gastroenterology & Hepatology, 2012, 9(11): 633-645. DOI: 10.1038/nrgastro.2012.168. | 5.2 | 消化道平滑肌、慢波、Cajal 间质细胞、胃肠动力 |
| lorke1983 | LORKE D. A new approach to practical acute toxicity testing[J]. Archives of Toxicology, 1983, 54(4): 275-287. DOI: 10.1007/BF01234480. | 8.1 | 急性毒性、LD50、动物数、逐步给药 |

## 按实验索引

- 实验 1.5：eddleston2008；eddleston2019；eddleston2009；ellman1961；briggs1925；schild1947；arunlakshana1959
- 实验 2.4：lei2018
- 实验 2.4s：lei2018
- 实验 2.7：weisberg2008
- 实验 3.2：semenza2011
- 实验 4.3：levi1999；taylor2001
- 实验 5.2：schild1947；arunlakshana1959；sanders2012
- 实验 8.1：lorke1983
