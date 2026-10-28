---
name: fdu-lab-data
description: 用 tools/labcalc.py 做功能学实验计算（剂量、稀释、变化率、均值±SD、平均动脉压、心率、LD50 寇氏法、治疗指数、AChE 活性、肺系数、半衰期、Fisher 精确检验、HRV）。需要任何数值计算时使用，禁止心算。
---

# 数据处理

所有计算用命令行工具，把**命令与输出原样展示**，便于学生核对：

```
python tools/labcalc.py dose --weight 2.5 --dose 1000 --conc 20   # 20%乌拉坦 1 g/kg 的注射体积
python tools/labcalc.py change --before 120 --after 90                # 变化百分比
python tools/labcalc.py stats 1.2 1.4 1.1 1.5                         # 均值/SD/SEM
python tools/labcalc.py map --sbp 120 --dbp 80                        # 平均动脉压
python tools/labcalc.py ld50 --doses 100 150 200 --n 10 --deaths 1 5 9  # 改良寇氏法
python tools/labcalc.py --help                                        # 全部子命令
```

规则：
- 报告里的数字保留合理有效位数，单位写全；SD 与 SEM 要标明。
- n<3 不报 SD 的“显著性”，只给描述。
- 工具给出 warning（如死亡率范围不足）要原样转告并在讨论里写明局限。
- 没有对应子命令的计算：先说明用什么公式，再用 python 现算并展示代码。
