import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# 读取数据
csv_file = '01TOF_RAW.csv'
df = pd.read_csv(csv_file, encoding='utf-8')

# 提取 TOF_raw(ms) 列
delays = df['TOF_raw(ms)'].values

# 过滤极端异常值 (网络断连或严重堵塞)，保留正常工作范围 (<100ms) 的数据
valid_delays = delays[delays < 100.0]

# 为了严格匹配论文中说的“50次打靶”，只截取前 50 个有效数据点
valid_delays = valid_delays[:50]

# 计算统计量
mean_delay = np.mean(valid_delays)
std_delay = np.std(valid_delays)

print(f"有效数据点: {len(valid_delays)} / {len(delays)}")
print(f"均值: {mean_delay:.2f} ms")
print(f"标准差: {std_delay:.2f} ms")

# 绘图设置
plt.figure(figsize=(10, 5))
plt.rcParams['font.sans-serif'] = ['SimHei']  # 正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False    # 正常显示负号

# X轴索引
x = np.arange(1, len(valid_delays) + 1)

# 绘制散点图
plt.scatter(x, valid_delays, color='#2ca02c', alpha=0.7, edgecolors='k', s=50, label='单次触发延迟 (TOF_raw)')

# 绘制均值线
plt.axhline(mean_delay, color='#d62728', linestyle='--', linewidth=2, label=f'统计均值 ($\mu={mean_delay:.1f}$ ms)')

# 绘制标准差阴影带
plt.fill_between(x, mean_delay - std_delay, mean_delay + std_delay, color='#d62728', alpha=0.2, label=f'抖动区间 ($\pm 1\sigma={std_delay:.1f}$ ms)')

# 设置坐标轴与标题
plt.title('极近场零距离系统通信与机电综合延迟散点分布图', fontsize=14, pad=15)
plt.xlabel('实验触发次数 (次)', fontsize=12)
plt.ylabel('固有综合延迟 TOF_raw (ms)', fontsize=12)
plt.ylim(0, 80)
plt.grid(True, linestyle='--', alpha=0.5)
plt.legend(loc='upper right')

# 保存图片
out_file = 'TOF_Jitter_Distribution.png'
plt.savefig(out_file, dpi=300, bbox_inches='tight')
print(f"绘图完成，已保存至 {out_file}")
