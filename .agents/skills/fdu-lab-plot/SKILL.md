---
name: fdu-lab-plot
description: 按报告规范作图：折线（时间过程）、柱状（组间比较）、量-效/剂量-死亡率与概率单位图、散点+回归；含作图要求与图注。需要为报告画图、改图、写图注时使用。
---

# 作图助手

## 命令（输入为“长表”CSV，UTF-8）
```
python tools/labplot.py line    data.csv --x 时间 --y 数值 --group 组别 --xlabel "时间（min）" --ylabel "心率（次/min）" -o fig1.png
python tools/labplot.py bar     data.csv --x 组别 --y 数值 --ylabel "血清钾（mmol/L）" --points -o fig2.png
python tools/labplot.py dose    data.csv --dose 剂量 --n 每组数 --deaths 死亡数 -o fig3.png
python tools/labplot.py scatter data.csv --x 浓度 --y 吸光度 --fit -o fig4.png
```
`--err sd|sem|none` 选误差线；`--size 12x8` 设宽高（cm）。输出会打印建议图注（含 n、误差线含义）。

## 选图
时间过程 → 折线；组间比较 → 柱状+散点（`--points` 显示个体，n 小时必须显示）；量效 → `dose`；标准曲线/相关 → `scatter --fit`。
n = 1 或只有两三个点：用表格，不画误差线。

## 作图要求（报告规范）
1. 坐标轴标“量（单位）”，单位用法定符号；刻度朝内；去掉上、右边框；字号 ≥ 8 pt。
2. 色盲友好配色，并用**不同标记/线型/填充**区分，黑白打印仍可辨。
3. 误差线含义（SD 或 SEM）和 n 必须写在图注里；描述变异用 SD，推断均值精度用 SEM，别混用。
4. 图题写在图**下方**（Word/LaTeX 的题注），不要画在图内；表题在表上方。
5. 一图一个结论；同类图坐标范围保持一致；不用 3D、不用渐变。
6. 图中文字用宋体/Times New Roman；导出 300 dpi png，或 pdf/svg 矢量。
7. 横轴为剂量时用对数刻度，并说明。
8. 图必须在正文中被引用（“如图 1 所示”），并用一两句写出该图显示了什么。
