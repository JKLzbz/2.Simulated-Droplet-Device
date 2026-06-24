import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt

# 设置字体以支持中文显示，避免出现方框
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei'] 
plt.rcParams['axes.unicode_minus'] = False 

# ==========================================
# 1. 核心算法：巴特沃斯低通滤波器 (300Hz)
# ==========================================
def butter_lowpass_filter(data, cutoff, fs, order=3):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    y = filtfilt(b, a, data)
    return y

# ==========================================
# 2. 读取单个 CSV 文件 (请把名字改成你要看的那个)
# ==========================================
# 获取当前脚本所在目录，确保在任何终端路径下运行都能找到文件
current_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(current_dir, 'scope_1.csv')  # <--- 如果你想看别的文件，改这里！
print(f"正在读取文件: {file_path} ...")

try:
    df = pd.read_csv(file_path, skiprows=2, names=['Time', 'CH1', 'CH2'])
    df = df.dropna()
    df['Time'] = pd.to_numeric(df['Time'])
    df['CH1'] = pd.to_numeric(df['CH1'])
    df['CH2'] = pd.to_numeric(df['CH2'])

    # ==========================================
    # 3. 寻找触发点，对齐时间轴
    # ==========================================
    trigger_idx_list = df.index[df['CH1'] > 1.0].tolist()
    if not trigger_idx_list:
        print("没找到触发信号！请检查 CSV 文件。")
        exit()
        
    t0 = df['Time'].loc[trigger_idx_list[0]]
    df['Time_ms'] = (df['Time'] - t0) * 1000 # 转换成毫秒
    
    # 截取 -5ms 到 25ms 的核心区间
    window = df[(df['Time_ms'] >= -5) & (df['Time_ms'] <= 25)].copy()

    # ==========================================
    # 4. 执行滤波
    # ==========================================
    dt = df['Time'].iloc[1] - df['Time'].iloc[0]
    fs = 1.0 / dt
    # 给 CH2 (原始波动) 洗个澡，洗掉 300Hz 以上的毛刺，变成红线
    window['CH2_lp'] = butter_lowpass_filter(window['CH2'], cutoff=300, fs=fs, order=2)

    # ==========================================
    # 5. 画图 (会弹出一个可以交互的窗口)
    # ==========================================
    plt.figure(figsize=(12, 6))

    # 画原始数据（浅蓝色，带很多毛刺）
    plt.plot(window['Time_ms'], window['CH2'], label='Raw Data (CH2 原始波动)', color='steelblue', alpha=0.5)
    
    # 画滤波后数据（大红线，极度丝滑）
    plt.plot(window['Time_ms'], window['CH2_lp'], label='Filtered Data (300Hz 低通滤波)', color='red', linewidth=3)
    
    # 画一条 0ms 的垂直绿线，代表“ESP32开火瞬间”
    plt.axvline(0, color='green', linestyle='--', label='Trigger (T=0)')

    # 设置标题和坐标轴
    plt.title(f'Waveform Analysis: {file_path}', fontsize=16)
    plt.xlabel('Time (ms) - 触发后的时间', fontsize=12)
    plt.ylabel('Voltage (V) - 12V电源的微小波动(AC耦合剥离直流后)', fontsize=12)
    
    # 限制一下 Y 轴显示范围，让你看得更清楚坑在哪
    ch2_min = window['CH2_lp'].min()
    ch2_max = window['CH2_lp'].max()
    plt.ylim(ch2_min - 0.02, ch2_max + 0.02)
    plt.xlim(-2, 20) # 重点看 0 到 20 毫秒

    plt.grid(True, linestyle=':', alpha=0.8)
    plt.legend(loc='upper right')
    
    print("处理完成！请查看弹出的图表窗口。")
    print("【操作提示】使用弹窗下方的放大镜工具，框选 5ms ~ 10ms 的区域，亲自找一找那个最低的坑！")
    
    # 弹出交互式窗口
    plt.show()

except Exception as e:
    print(f"出错了: {e}")