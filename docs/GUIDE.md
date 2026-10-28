# 使用指南

本指南写给没有编程经验的同学。每一步后面都有“怎样确认成功”。遇到问题先看最后的排错表。

> **关于 dsh**：本项目把 dsh 理解为 DeepSeek Harness（DeepSeek 官方的命令行/本地网页智能体外壳），步骤依据其公开文档整理。**作者尚未在 dsh 上完整运行验证**；若某一步与你看到的界面不同，以 dsh 官方文档为准，并欢迎提 Issue 告知。

## 三种用法，任选其一

| | 适合谁 | 需要安装 | 能运行计算/排版工具 |
|---|---|---|---|
| A 网页粘贴 | 只想试一试 | 无 | 否（本机另行运行工具） |
| **B dsh 本地网页**（推荐） | 想一路到 Word 成稿 | Node、Python、pandoc | 是 |
| C 只用模板 | 自己写，只要格式 | Word 或 LaTeX | – |

## A. 网页粘贴（零安装）

1. 本机运行 `python tools/make_prompt.py 2.7 --print`（2.7 换成你的实验编号），复制输出。没有 Python 就跳过，直接用 B 或 C。
2. 打开 chat.deepseek.com，粘贴，按它的提问依次回答，贴入你自己的原始记录。
3. 它写好的 Markdown，用 `build.py` 排版，或粘进 `templates/word/功能学科实验报告模板.docx`。

## B. dsh 本地网页（推荐）

### B1 准备环境
1. **Node.js ≥ 22.19**：终端运行 `node -v`，显示 v22.19 以上即可。没有就到 nodejs.org 安装 LTS。
2. **Python ≥ 3.10**：`python --version`（Windows 用 `py --version`）。
3. **pandoc**：Windows `winget install JohnMacFarlane.Pandoc`；macOS `brew install pandoc`；或 `pip install pypandoc_binary`。
4. （只在需要 PDF 时）TeX Live 或 MiKTeX，含 ctex；也可以把 `.tex` 传到 Overleaf，选 XeLaTeX。
5. **DeepSeek API Key**：在 DeepSeek 开放平台注册、充值少量余额、创建 API Key，复制保存。**不要把 Key 发给别人，也不要写进仓库。**

### B2 获取项目
```bash
git clone https://github.com/rachael1216/fdu-func-lab-helper.git
cd fdu-func-lab-helper
pip install -r requirements.txt
python tools/build.py --doctor
```
✅ 成功标志：`--doctor` 末尾显示“环境 OK”。有 ✗ 就按提示补。

### B3 放入你的资料（强烈建议）
1. 把你自己的《功能学科实验教程》PDF 放在仓库目录，运行 `python tools/kb.py build 功能学科实验教程.pdf`（需要 `pip install pymupdf`）。
2. 其他同类教材或讲义放进 `corpus/local/<目录名>/`（见 `corpus/README.md`）。
3. `python tools/rag.py build`，再 `python tools/rag.py sources`。

✅ 成功标志：`sources` 列出 `textbook`、`expr`、`card`、`literature`（以及你放的目录）。
教材是有版权的，`kb/` 和 `corpus/local/` 都不会被提交。

### B4 启动 dsh
在**仓库目录**里运行：
```bash
npx @deepseek-ai/dsh web
```
浏览器打开 http://127.0.0.1:3080，在 Settings → Models 里填入 API Key。
dsh 会从项目的 `.agents/skills`（以及 `.dsh/skills`、`~/.dsh/skills`、`~/.agents/skills`）发现 skill。

✅ 成功标志：对话里问“你有哪些 fdu-lab 开头的 skill？”，它能列出 `fdu-lab-report` 等 11 个。
列不出来：确认是在仓库目录里启动的；或运行 `python tools/install_skills.py` 装到全局目录，重启 dsh。

### B5 写一份报告（完整流程）
对 dsh 说：

> 我要写实验 2.7 家兔高钾血症的报告。请按 fdu-lab-report 的流程带我做，先问我需要的信息。

流水线与你要做的事：

| 步骤 | AI 做什么 | 你做什么 |
|---|---|---|
| 1 采集 | 逐组提问 | 如实提供动物、药品、时间点、原始数据、**你观察到的现象**、与讲义不同之处 |
| 2 检索 | 取课本术语、原理句式、页码 | 核对页码是否对得上你的教材 |
| 3 计算 | 用 `labcalc.py` 算剂量、变化率、LD50 等 | 核对命令和结果 |
| 4 统计 | 用 `labstats.py` 选方法并检验 | 确认分组与 n 正确 |
| 5 作图 | 用 `labplot.py` 出图与图注 | 看图，改图注 |
| 6 论证 | 按“观察→预期→机制→偏差假设→局限→临床联系”写 | 补充你自己的判断 |
| 7 写作 | 写入 `reports/<名>/report.md` | 通读，改成自己的话 |
| 8 语言 | `stylecheck.py` 检查并提出改法 | 决定改不改；太像课本的句子要改写 |
| 9 文献 | `refcheck.py` 核对 | **读过再引用**；WARN/FAIL 必须处理 |
| 10 自查 | 清单 | 逐项确认 |
| 11 出稿 | `build.py` 生成 Word/PDF | 打开检查，按课程要求声明 AI 使用 |

✅ 成功标志：`reports/<名>/report.docx` 出现；打开后第 1 页是封面，之后有目录、页眉和页码。Word 里目录为空时右键“更新域”。

### B6 报告 YAML 头
```yaml
---
title: 家兔高钾血症实验报告
course: 功能学科综合实验
exp_no: "2.7"
class: 24 临床医学五年制
student: 你的姓名
student_id: "你的学号"
group: 第 3 组
date: 2026.11.13
teacher: 老师姓名
animal: rabbit        # rabbit 或 mouse
ai_statement: ""      # 按课程要求填写，非空则附在文末
---
```
个人报告放在 `reports/`（已 gitignore），不要提交。

## C. 只用模板
- Word：`templates/word/功能学科实验报告模板.docx`，每节有写作提示。
- LaTeX：`templates/latex/report-template.tex` + `fdureport.cls`，用 XeLaTeX 编译；或整个文件夹传到 Overleaf。
- 字体、字号、页边距、图表和参考文献格式见 [FORMAT.md](FORMAT.md)。

## 单独使用各工具
```bash
python tools/labcalc.py dose --weight 2.5 --dose 1000 --conc 20     # 给药体积
python tools/labstats.py anova --g 对照=1,2,3 --g 低=2,3,4 --g 高=5,6,7
python tools/labplot.py line data.csv --x 时间 --y 数值 --group 组别 -o fig.png
python tools/rag.py search 复能剂 -c literature
python tools/refcheck.py fmt 10.1016/S0140-6736(07)61202-1
```
每个工具 `-h` 有完整说明。CSV 用“长表”：每行一次观测。

## 使用边界
- AI 帮你整理和检查，**数据与观察必须来自你的实验**；不得让 AI 编造数据、现象或文献。
- 知识卡与课本表述整理是 AI 草稿，与教材或老师不一致时以教材和老师为准。
- 语言检查工具帮你贴近课本、去掉模板腔，**不是规避 AI 检测的工具**；课程要求声明 AI 使用的，请照实声明。
- 不要把别人的报告当范本喂给 AI；本项目的示例是虚构数据。

## 排错
| 现象 | 处理 |
|---|---|
| `找不到 pandoc` | 按 B1-3 安装后重开终端 |
| `xelatex` 报错或缺 ctex | 安装完整 TeX Live/MiKTeX，或用 Overleaf（XeLaTeX） |
| 图中文字成方框 | 安装宋体/思源宋体后重试 |
| `rag.py` 查不到教材 | 先 `kb.py build`，再 `rag.py build` |
| `refcheck` 联网失败 | 检查网络；先用 `--offline` 对照登记表 |
| dsh 不显示 skill | 在仓库目录启动，或 `python tools/install_skills.py` |
| Word 目录为空 | 右键目录 → 更新域 |
