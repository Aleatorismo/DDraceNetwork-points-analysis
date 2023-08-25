import requests
import pandas as pd
import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import matplotlib.font_manager as fm
from collections import OrderedDict
from scipy.interpolate import interp1d

# 用户名
player_name = 'Randomium'

# 字体
plt.rcParams["font.family"] = ["sans-serif", 'Simhei']

fts = 15  # 文字字号
legend_fts = 10  # 图例字号
x_fts = 7  # x 坐标轴数字字号
rot = 35  # 坐标轴数字旋转角度

# 柱状图顺序 从上至下 Insane Brutal Oldschool Moderate DDmax_Easy DDmax_Next DDmax_Pro DDmax_Nut Novice Dummy Solo
# Race Fun 及其对应的颜色
order = {'Insane': '#000000',
         'Brutal': '#d42447',
         'Oldschool': '#ff2689',
         'Moderate': '#ffae25',
         'DDmaX.Nut': '#ff0000',
         'DDmaX.Pro': '#090da7',
         'DDmaX.Next': '#03c883',
         'DDmaX.Easy': '#bcd4e6',
         'Novice': '#598221',
         'Dummy': '#5b92e5',
         'Solo': '#4f42b5',
         'Race': '#b784a7',
         'Fun': '#a8c3bc'}


def use_local_json():
    """
    使用本地 json 文件
    :return:
    """
    import json
    filename = 'test.json'
    with open(filename) as f:
        rd = json.load(f)  # raw data
    return rd


def download_json():
    """
    下载 json 文件
    :return: raw data
    """
    url = 'https://ddnet.org/players/?json2=' + player_name
    r = requests.get(url)
    print("Status code:", r.status_code)
    rd = r.json()  # raw data
    return rd


def get_date_sorted_data(rd):
    """
    整理 rd，按时间顺序排列

    按月份排序 ddm (date sorted data monthly)
    ddm['21/03'] = {'Novice': {'points': 130, 'number': 44}, 'Moderate': {...}, ...}

    按天排序 ddd (date sorted data daily)
    ddd['21/03/21'] = {'Novice': {'points': 0, 'number': 0}, 'Moderate': {...}, ...}

    :param rd: raw data
    :return:
    """
    # 生成时间序列
    ft = pd.to_datetime(rd['first_finish']['timestamp'], unit='s').strftime('%Y/%m/%d')  # 初次游戏时间
    lt = pd.to_datetime(rd['last_finishes'][00]['timestamp'], unit='s').strftime('%Y/%m/%d')  # 最后一次游戏时间
    ti_index = pd.date_range(start=ft, end=lt)
    ti_month = sorted(set([ti_index[i].strftime('%y/%m') for i in range(0, len(ti_index))]))  # 月序列
    ti_day = sorted([ti_index[i].strftime('%y/%m/%d') for i in range(0, len(ti_index))])  # 日序列

    # 初始化
    ddm = {}
    for t in ti_month:
        ddm[t] = {}
        for ty in rd['types'].keys():
            ddm[t][ty] = {'points': 0, 'number': 0}

    ddd = {}
    for t in ti_day:
        ddd[t] = {}
        for ty in rd['types'].keys():
            ddd[t][ty] = {'points': 0, 'number': 0}

    # 写入 ddm，ddd
    for ty in rd['types'].keys():
        for map_name in rd['types'][ty]['maps'].keys():

            try:
                day = pd.to_datetime(rd['types'][ty]['maps'][map_name]['first_finish'], unit='s').strftime('%y/%m/%d')
                month = pd.to_datetime(rd['types'][ty]['maps'][map_name]['first_finish'], unit='s').strftime('%y/%m')
            except KeyError:
                continue  # 若 'first finish' 键不存在，说明该地图没有通关，跳过当前项

            ddm[month][ty]['points'] += rd['types'][ty]['maps'][map_name]['points']  # 当月累计分数
            ddm[month][ty]['number'] += 1  # 当月累计过图数

            if day == '2023/04/02':
                pass
            ddd[day][ty]['points'] += rd['types'][ty]['maps'][map_name]['points']  # 当日累计分数
            ddd[day][ty]['number'] += 1  # 当日累计过图数

    return ddm, ddd


# 绘图


def head(points, count):
    """
    绘制图表抬头
    :param points: 总分数
    :param count: 总过图数
    :return:
    """
    plt.axis('off')
    plt.title('Analysis Report for\n\n' + rd['player'] + '\n\nTotal Points: ' + str(points) +
              '\n\nFinished Maps Count: ' + str(count) + '\n\nReport Generated on:\n\n' +
              datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), fontproperties=fm.FontProperties(size=fts), y=0)


def plot_bar(dd, plot_type, x_spacing, title):
    """
    绘制柱状图
    :param dd: date sorted data
    :param plot_type: 绘制类型 ('number' / 'points')
    :param x_spacing: x 轴坐标间距
    :param title: 图标题
    :return:
    """
    for t in dd.keys():
        offset = 0  # 柱状图基线偏移量
        for ty in reversed(list(order.keys())):  # 柱状图按字典 order 逆序绘制，从下至上
            plt.bar(t, dd[t][ty][plot_type], bottom=offset, label=ty, color=order[ty])
            offset += dd[t][ty][plot_type]  # 设置偏移量为当前绘制柱状图顶部的纵坐标

    plt.xticks(range(0, len(dd), x_spacing), fontsize=x_fts, rotation=rot)  # 设置 x 轴坐标
    plt.title(title, fontproperties=fm.FontProperties(size=fts), y=1.03)  # 设置标题


def plot_curve(dd, plot_type, x_spacing, title=None):
    """
    绘制平滑曲线图
    :param dd: date sorted data
    :param plot_type: 绘制类型 ('number' / 'points')
    :param x_spacing: x 轴坐标间距
    :param title: 图标题
    :return:
    """
    xt = list(dd.keys())  # x 坐标
    x = np.array(range(0, len(xt)))
    x_smooth = np.linspace(x.min(), x.max(), 300)  # 细分 x 轴坐标，用于后续平滑曲线
    for ty in list(order.keys()):
        y = []  # y 坐标
        for t in dd.keys():
            y.append(dd[t][ty][plot_type])
        y = np.array(y)
        y_smooth = interp1d(x, y, kind='quadratic')(x_smooth)  # 平滑曲线
        plt.plot(x_smooth, y_smooth, color=order[ty])
    plt.xticks(x, xt, fontsize=x_fts, rotation=rot)  # 设置 x 轴坐标
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(x_spacing))  # 按预定的坐标间距，删除过多的 x 轴坐标标签
    if title:
        plt.title('Points(Daily)', fontproperties=fm.FontProperties(size=fts), y=1.02)  # 如果存在标题，就生成标题


def plot_cumulative_curve(dd, plot_type, x_spacing, title):
    """
    绘制累积曲线图
    :param dd: date sorted data
    :param plot_type: 绘制类型 ('number' / 'points')
    :param x_spacing: x 轴坐标间距
    :param title: 图标题
    :return: 最后一个数据点的纵坐标，即总 number / 总 points
    """
    xt = dd.keys()
    x = np.array(range(0, len(dd)))
    y = []
    for t in dd.keys():
        n = sum([dd[t][ty][plot_type] for ty in list(order.keys())])
        try:
            y[-1]
        except IndexError:
            y.append(n)
        else:
            y.append(n + y[-1])

    plt.plot(x, y)
    plt.title(title, fontproperties=fm.FontProperties(size=fts), y=1.02)
    plt.xticks(x, xt, fontsize=x_fts, rotation=rot)
    plt.gca().xaxis.set_major_locator(ticker.MultipleLocator(x_spacing))

    return y[-1]


if __name__ == '__main__':
    print('Downloading json')
    rd = download_json()  # 获取 json 文件

    print('Sorting data')
    ddm, ddd = get_date_sorted_data(rd)  # 预整理数据

    plt.figure(dpi=300, figsize=(10, 35))  # 画布尺寸

    # x 轴坐标间距
    x_spacing_m = int((len(ddm)) / 15) + 1
    x_spacing_d = int((len(ddd)) / 15) + 1

    plt.subplots_adjust(hspace=0.4)  # 子图间距

    # 数量柱状图
    print('Drawing bar graph of monthly finished maps count')
    plt.subplot(723)
    plot_bar(ddm, 'number', x_spacing_m, 'Finished Maps (Monthly)')

    # 生成图例同时去除冗余图例
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = OrderedDict(zip(labels, handles))
    plt.legend(reversed(by_label.values()), reversed(by_label.keys()), bbox_to_anchor=(1.9, 2.3),
               prop=fm.FontProperties(size=legend_fts))

    # 分数柱状图
    print('Drawing bar graph of monthly points')
    plt.subplot(724)
    plot_bar(ddm, 'points', x_spacing_m, 'Points (Monthly)')

    # 数量曲线图
    print('Drawing curve graph of monthly finished maps count')
    plt.subplot(725)
    plot_curve(ddm, 'number', x_spacing_m)

    # 分数曲线图
    print('Drawing curve graph of monthly points')
    plt.subplot(726)
    plot_curve(ddm, 'points', x_spacing_m)

    # 数量柱状图（日）
    print('Drawing bar graph of daily finished maps count')
    plt.subplot2grid((7, 2), (3, 0), colspan=2, rowspan=1)
    plot_bar(ddd, 'number', x_spacing_d, 'Finished Maps (Daily)')

    # 分数柱状图（日）
    print('Drawing bar graph of daily points')
    plt.subplot2grid((7, 2), (4, 0), colspan=2, rowspan=1)
    plot_bar(ddd, 'points', x_spacing_d, 'Points (Daily)')

    # 数量累积曲线图（日）
    print('Drawing curve graph of cumulative finished maps count')
    plt.subplot2grid((7, 2), (5, 0), colspan=2, rowspan=1)
    count = plot_cumulative_curve(ddd, 'number', x_spacing_d, 'Cumulative Finished Maps (Daily)')

    # 分数累积曲线图（日）
    print('Drawing curve graph of cumulative points')
    plt.subplot2grid((7, 2), (6, 0), colspan=2, rowspan=1)
    points = plot_cumulative_curve(ddd, 'points', x_spacing_d, 'Cumulative Points (Daily)')

    # 图表抬头
    plt.subplot(721)
    head(points, count)

    # 水印
    plt.figtext(0.9, 0.07, 'Report Made By: Randomium & Segn', ha="right", va="bottom",
                fontproperties=fm.FontProperties(size=fts))

    # 保存图标
    plt.savefig('report_' + rd['player'] + '.png')
    plt.close()
