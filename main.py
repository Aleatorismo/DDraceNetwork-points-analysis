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
url = 'https://ddnet.tw/players/?json2=' + player_name
r = requests.get(url)
print("Status code:", r.status_code)
rd = r.json()


# 处理数据

# name sorted data
nd = {}
for t in rd['types'].keys():
    for m in rd['types'][t]['maps'].keys():
        try:
            nd[m] = {}
            nd[m]['time'] = pd.to_datetime(rd['types'][t]['maps'][m]['first_finish'], unit='s')
            nd[m]['points'] = rd['types'][t]['maps'][m]['points']
            nd[m]['type'] = t
        except KeyError:
            del nd[m]
            continue

# 生成时间序列
ft = pd.to_datetime(rd['first_finish']['timestamp'], unit='s').strftime('%Y/%m/%d')
lt = pd.to_datetime(rd['last_finishes'][00]['timestamp'], unit='s').strftime('%Y/%m/%d')
ti_index = pd.date_range(start=ft, end=lt)
ti_month = sorted(set([ti_index[i].strftime('%y/%m') for i in range(0, len(ti_index))]))
ti_day = sorted([ti_index[i].strftime('%y/%m/%d') for i in range(0, len(ti_index))])

# date sorted data monthly
ddm = {}
# 初始化 ddm
for t in ti_month:
    ddm[t] = {}
    ddm[t]['offset'] = 0
    for ty in rd['types'].keys():
        ddm[t][ty] = {'points': 0, 'number': 0, 'name': []}

for k in nd.keys():
    t = nd[k]['time'].strftime('%y/%m')
    ty = nd[k]['type']
    ddm[t][ty]['points'] += nd[k]['points']
    ddm[t][ty]['number'] += 1
    ddm[t][ty]['name'].append(k)

# date sorted data daily
ddd = {}
# 初始化 ddd
for t in ti_day:
    ddd[t] = {}
    ddd[t]['offset'] = 0
    for ty in rd['types'].keys():
        ddd[t][ty] = {'points': 0, 'number': 0, 'name': []}

for k in nd.keys():
    t = nd[k]['time'].strftime('%y/%m/%d')
    ty = nd[k]['type']
    ddd[t][ty]['points'] += nd[k]['points']
    ddd[t][ty]['number'] += 1
    ddd[t][ty]['name'].append(k)


# 绘图

# 柱状图顺序 从上之下 Insane Brutal Oldschool Moderate DDmax Novice Dummy Solo Race Fun 及其对应的颜色
order = dict(Insane='#000000', Brutal='#d42447', Oldschool='#ff2689', Moderate='#ffae25', DDmaX='#bcd4e6',
             Novice='#598221', Dummy='#5b92e5', Solo='#4f42b5', Race='#b784a7', Fun='#a8c3bc')

# 画布尺寸
plt.figure(dpi=300, figsize=(10, 35))
# 文字尺寸及旋转角度
fts = 7
rot = 35
# x轴坐标间距
x_spacing_m = int((len(ddm)) / 15) + 1
x_spacing_d = int((len(ddd)) / 15) + 1

# 图表抬头
plt.subplot(721)
plt.axis('off')
plt.title('Analysis Report for\n\n' + rd['player'] + '\n\nTotal Points: ' + str(
    rd['points']['points']) + '\n\nTotal Map Counts: ' + str(
    len(nd)) + '\n\nReport Generated on:\n\n' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), fontsize=20,
          fontproperties='cmr10', y=0)

# 数量柱状图
plt.subplot(723)
plt.subplots_adjust(hspace=0.4)  # 子图间距
for ty in reversed(list(order.keys())):
    for t in ddm.keys():
        plt.bar(t, ddm[t][ty]['number'], bottom=ddm[t]['offset'], label=ty, color=order[ty])
        ddm[t]['offset'] += ddm[t][ty]['number']
plt.xticks(range(0, len(ddm), x_spacing_m), fontsize=fts, rotation=rot)
plt.title('Counts(Monthly)', fontsize=20, fontproperties='cmr10', y=1.03)
# 生成图例同时去除冗余图例
handles, labels = plt.gca().get_legend_handles_labels()
by_label = OrderedDict(zip(labels, handles))
plt.legend(reversed(by_label.values()), reversed(by_label.keys()), bbox_to_anchor=(1.9, 2.3), prop='cmr10')

# 分数柱状图
plt.subplot(724)
for t in ddm.keys():
    ddm[t]['offset'] = 0
for ty in reversed(list(order.keys())):
    for t in ddm.keys():
        plt.bar(t, ddm[t][ty]['points'], bottom=ddm[t]['offset'], label=ty, color=order[ty])
        ddm[t]['offset'] += ddm[t][ty]['points']
plt.xticks(range(0, len(ddm), x_spacing_m), fontsize=fts, rotation=rot)
plt.title('Points(Monthly)', fontsize=20, fontproperties='cmr10', y=1.03)

# 数量、分数曲线图
plt.subplot(725)
xt = list(ddm.keys())
x = np.array(range(0, len(xt)))
x_smooth = np.linspace(x.min(), x.max(), 300)
for ty in list(order.keys()):
    yn = []
    yp = []
    for t in ddm.keys():
        yn.append(ddm[t][ty]['number'])
        yp.append(ddm[t][ty]['points'])
    yn = np.array(yn)
    yp = np.array(yp)
    yn_smooth = interp1d(x, yn, kind='quadratic')(x_smooth)
    yp_smooth = interp1d(x, yp, kind='quadratic')(x_smooth)
    plt.subplot(725)
    plt.plot(x_smooth, yn_smooth, color=order[ty])
    plt.subplot(726)
    plt.plot(x_smooth, yp_smooth, color=order[ty])
plt.xticks(x, xt, fontsize=fts, rotation=rot)
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(x_spacing_m))
plt.subplot(725)
plt.xticks(x, xt, fontsize=fts, rotation=rot)
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(x_spacing_m))

# 数量柱状图（天）
plt.subplot2grid((7, 2), (3, 0), colspan=2, rowspan=1)
for t in ddd.keys():
    for ty in reversed(list(order.keys())):
        plt.bar(t, ddd[t][ty]['number'], bottom=ddd[t]['offset'], color=order[ty])
        ddd[t]['offset'] += ddd[t][ty]['number']
plt.title('Counts(Daily)', fontsize=20, fontproperties='cmr10', y=1.02)
plt.xticks(fontsize=fts, rotation=rot)
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(x_spacing_d))

# 分数柱状图（天）
plt.subplot2grid((7, 2), (4, 0), colspan=2, rowspan=1)
for t in ddd.keys():
    ddd[t]['offset'] = 0
for t in ddd.keys():
    for ty in reversed(list(order.keys())):
        plt.bar(t, ddd[t][ty]['points'], bottom=ddd[t]['offset'], color=order[ty])
        ddd[t]['offset'] += ddd[t][ty]['points']
plt.title('Points(Daily)', fontsize=20, fontproperties='cmr10', y=1.02)
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
plt.title('Total Counts(Daily)', fontsize=20, fontproperties='cmr10', y=1.02)
plt.xticks(x, xt, fontsize=fts, rotation=rot)
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(x_spacing_d))

plt.subplot2grid((7, 2), (6, 0), colspan=2, rowspan=1)
plt.plot(x, yp)
plt.title('Total Points(Daily)', fontsize=20, fontproperties='cmr10', y=1.02)
plt.xticks(x, xt, fontsize=fts, rotation=rot)
plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(x_spacing_d))

# 水印
plt.figtext(0.9, 0.07, 'Report Made By: Randomium', ha="right", va="bottom", fontsize=20, fontproperties='cmr10')


# 保存图表
plt.savefig('report_' + rd['player'] + '.png')
plt.close()
