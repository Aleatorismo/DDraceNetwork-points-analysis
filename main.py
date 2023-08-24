import requests
import pandas as pd
import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from collections import OrderedDict
from scipy.interpolate import interp1d

# 玩家昵称
player_name = 'Randomium'

# 下载 json 文件
url = 'https://ddnet.org/players/?json2=' + player_name
r = requests.get(url)
print("Status code:", r.status_code)
rd = r.json()  # raw data

# 中文字体
plt.rcParams["font.family"] = ["sans-serif"]
plt.rcParams["font.sans-serif"] = ['SimHei']

# 处理数据

# 按地图名整理 rd
# nd['Kobra'] = {'points' : 4, 'type': 'Novice', 'time' : Timestamp('2021-04-03 14:51:35')}
nd = {}  # name sorted data
for t in rd['types'].keys():
    for m in rd['types'][t]['maps'].keys():
        try:
            nd[m] = {}
            nd[m]['time'] = pd.to_datetime(rd['types'][t]['maps'][m]['first_finish'], unit='s')
            nd[m]['points'] = rd['types'][t]['maps'][m]['points']
            nd[m]['type'] = t
        except KeyError:
            del nd[m]  # 若信息不全，视为无效数据并删除
            continue

# 生成时间序列，用于之后各图的横坐标
ft = pd.to_datetime(rd['first_finish']['timestamp'], unit='s').strftime('%Y/%m/%d')  # 初次游戏时间
lt = pd.to_datetime(rd['last_finishes'][00]['timestamp'], unit='s').strftime('%Y/%m/%d')  # 最后一次游戏时间
ti_index = pd.date_range(start=ft, end=lt)
ti_month = sorted(set([ti_index[i].strftime('%y/%m') for i in range(0, len(ti_index))]))  # 月序列
ti_day = sorted([ti_index[i].strftime('%y/%m/%d') for i in range(0, len(ti_index))])  # 日序列

# 按时间整理 nd（月）
# ddm['21/03'] = {'Novice': {'points': 130, 'number': 44, 'name': [...]}, 'Moderate': {...}, ...}
ddm = {}  # date sorted data monthly
# 初始化 ddm
for t in ti_month:
    ddm[t] = {}
    for ty in rd['types'].keys():
        ddm[t][ty] = {'points': 0, 'number': 0, 'name': []}

# 按时间整理 nd （日）
# ddd['21/03/21'] = {'Novice': {'points': 0, 'number': 0, 'name': []}, 'Moderate': {...}, ...}
ddd = {}  # date sorted data daily
# 初始化 ddd
for t in ti_day:
    ddd[t] = {}
    for ty in rd['types'].keys():
        ddd[t][ty] = {'points': 0, 'number': 0, 'name': []}

# 写入 ddm，ddn
for k in nd.keys():
    day = nd[k]['time'].strftime('%y/%m/%d')
    month = nd[k]['time'].strftime('%y/%m')
    ty = nd[k]['type']
    ddm[month][ty]['points'] += nd[k]['points']  # 当月累计分数
    ddm[month][ty]['number'] += 1  # 当月累计过图数
    ddm[month][ty]['name'].append(k)  # 当月过图名
    ddd[day][ty]['points'] += nd[k]['points']  # 当日累计分数
    ddd[day][ty]['number'] += 1  # 当日累计过图数
    ddd[day][ty]['name'].append(k)  # 当如过图名

# 绘图

# 柱状图顺序 从上至下 Insane Brutal Oldschool Moderate DDmax_Easy DDmax_Next DDmax_Pro DDmax_Nut Novice Dummy Solo
# Race Fun 及其对应的颜色
order = {'Insane': '#000000',
         'Brutal': '#d42447',
         'Oldschool': '#ff2689',
         'Moderate': '#ffae25',
         'DDmaX.Easy': '#bcd4e6',
         'DDmaX.Next': '#03c883',
         'DDmaX.Pro': '#090da7',
         'DDmaX.Nut': '#ff0000',
         'Novice': '#598221',
         'Dummy': '#5b92e5',
         'Solo': '#4f42b5',
         'Race': '#b784a7',
         'Fun': '#a8c3bc'}

# 画布尺寸
plt.figure(dpi=300, figsize=(10, 35))
# 文字尺寸及旋转角度
fts = 7
rot = 35
# x 轴坐标间距
x_spacing_m = int((len(ddm)) / 15) + 1
x_spacing_d = int((len(ddd)) / 15) + 1

# 图表抬头
plt.subplot(721)
plt.axis('off')
plt.title('Analysis Report for\n\n' + rd['player'] + '\n\nTotal Points: ' + str(
    rd['points']['points']) + '\n\nFinished Maps Count: ' + str(
    len(nd)) + '\n\nReport Generated on:\n\n' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), fontsize=20,
          fontproperties='SimHei', y=0)

# 数量柱状图
plt.subplot(723)
plt.subplots_adjust(hspace=0.4)  # 子图间距
for t in ddm.keys():
    offset = 0  # 柱状图基线偏移量
    for ty in reversed(list(order.keys())):  # 柱状图按字典 order 逆序绘制，从下至上
        plt.bar(t, ddm[t][ty]['number'], bottom=offset, label=ty, color=order[ty])
        offset += ddm[t][ty]['number']  # 设置偏移量为当前绘制柱状图顶部的纵坐标

plt.xticks(range(0, len(ddm), x_spacing_m), fontsize=fts, rotation=rot)  # 设置 x 轴坐标
plt.title('Finished Maps (Monthly)', fontsize=20, fontproperties='SimHei', y=1.03)  # 设置标题

# 生成图例同时去除冗余图例
handles, labels = plt.gca().get_legend_handles_labels()
by_label = OrderedDict(zip(labels, handles))
plt.legend(reversed(by_label.values()), reversed(by_label.keys()), bbox_to_anchor=(1.9, 2.3), prop='SimHei')

# 分数柱状图
plt.subplot(724)
for t in ddm.keys():
    offset = 0
    for ty in reversed(list(order.keys())):
        plt.bar(t, ddm[t][ty]['points'], bottom=offset, label=ty, color=order[ty])
        offset += ddm[t][ty]['points']
plt.xticks(range(0, len(ddm), x_spacing_m), fontsize=fts, rotation=rot)
plt.title('Points(Monthly)', fontsize=20, fontproperties='SimHei', y=1.03)

# 数量、分数曲线图
xt = list(ddm.keys())  # x 坐标
x = np.array(range(0, len(xt)))
x_smooth = np.linspace(x.min(), x.max(), 300)  # 细分 x 轴坐标，用于后续平滑曲线
for ty in list(order.keys()):
    yn = []  # 过图数 y 坐标
    yp = []  # 分数 y 坐标
    for t in ddm.keys():
        yn.append(ddm[t][ty]['number'])
        yp.append(ddm[t][ty]['points'])
    yn = np.array(yn)
    yp = np.array(yp)
    yn_smooth = interp1d(x, yn, kind='quadratic')(x_smooth)  # 平滑曲线
    yp_smooth = interp1d(x, yp, kind='quadratic')(x_smooth)
    plt.subplot(725)
    plt.plot(x_smooth, yn_smooth, color=order[ty])
    plt.subplot(726)
    plt.plot(x_smooth, yp_smooth, color=order[ty])
plt.xticks(x, xt, fontsize=fts, rotation=rot)  # 设置 x 轴坐标
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(x_spacing_m))  # 按预定的坐标间距，删除过多的 x 轴坐标标签
plt.subplot(725)
plt.xticks(x, xt, fontsize=fts, rotation=rot)
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(x_spacing_m))

# 数量柱状图（天）
plt.subplot2grid((7, 2), (3, 0), colspan=2, rowspan=1)
for t in ddd.keys():
    offset = 0
    for ty in reversed(list(order.keys())):
        plt.bar(t, ddd[t][ty]['number'], bottom=offset, color=order[ty])
        offset += ddd[t][ty]['number']
plt.title('Finished Maps (Daily)', fontsize=20, fontproperties='SimHei', y=1.02)
plt.xticks(fontsize=fts, rotation=rot)
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(x_spacing_d))

# 分数柱状图（天）
plt.subplot2grid((7, 2), (4, 0), colspan=2, rowspan=1)
for t in ddd.keys():
    offset = 0
    for ty in reversed(list(order.keys())):
        plt.bar(t, ddd[t][ty]['points'], bottom=offset, color=order[ty])
        offset += ddd[t][ty]['points']
plt.title('Points(Daily)', fontsize=20, fontproperties='SimHei', y=1.02)
plt.xticks(fontsize=fts, rotation=rot)
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(x_spacing_d))

# 整体数量、整体分数曲线图（天）
xt = ddd.keys()
x = np.array(range(0, len(ddd)))
yn = []
yp = []
for t in ddd.keys():
    n = 0
    p = 0
    for ty in list(order.keys()):
        n += ddd[t][ty]['number']
        p += ddd[t][ty]['points']
    try:
        yn[-1]
    except IndexError:
        yn.append(n)
        yp.append(p)
    else:
        yn.append(n + yn[-1])
        yp.append(p + yp[-1])

plt.subplot2grid((7, 2), (5, 0), colspan=2, rowspan=1)
plt.plot(x, yn)
plt.title('Cumulative Finished Maps (Daily)', fontsize=20, fontproperties='SimHei', y=1.02)
plt.xticks(x, xt, fontsize=fts, rotation=rot)
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(x_spacing_d))

plt.subplot2grid((7, 2), (6, 0), colspan=2, rowspan=1)
plt.plot(x, yp)
plt.title('Cumulative Points(Daily)', fontsize=20, fontproperties='SimHei', y=1.02)
plt.xticks(x, xt, fontsize=fts, rotation=rot)
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(x_spacing_d))

# 水印
plt.figtext(0.9, 0.07, 'Report Made By: Randomium & Segn', ha="right", va="bottom", fontsize=20,
            fontproperties='SimHei')

# 保存图表
plt.savefig('report_' + rd['player'] + '.png')
plt.close()
