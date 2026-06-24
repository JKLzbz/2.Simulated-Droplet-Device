import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt

# ==========================================
# 核心算法：巴特沃斯低通滤波器
# ==========================================
def butter_lowpass_filter(data, cutoff, fs, order=3):
    nyq = 0.5 * fs # 奈奎斯特频率
    normal_cutoff = cutoff / nyq # 归一化截止频率
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    y = filtfilt(b, a, data) # filtfilt 可以保证滤波后没有相位延迟（时间不会错位）
    return y

# ==========================================
# 主程序：批量收割 100 个 CSV
# ==========================================
def main():
    # 自动将工作目录切换到当前脚本所在的文件夹，避免跨文件夹运行时找不到 CSV
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # 找到当前文件夹下所有的 csv 文件
    csv_files = glob.glob('*.csv')
    print(f"找到 {len(csv_files)} 个 CSV 文件，开始批量处理...\n")

    delay_results = [] # 用来装 100 个延迟时间的列表

    for file in csv_files:
        try:
            # 1. 读取数据（跳过泰克示波器前两行表头）
            df = pd.read_csv(file, skiprows=2, names=['Time', 'CH1', 'CH2'])
            df = df.dropna()
            
            # 将字符转换为数字
            df['Time'] = pd.to_numeric(df['Time'])
            df['CH1'] = pd.to_numeric(df['CH1'])
            df['CH2'] = pd.to_numeric(df['CH2'])
            
            # 2. 寻找发令枪响的瞬间 (CH1 上升沿，设阈值为 1.0V)
            trigger_idx_list = df.index[df['CH1'] > 1.0].tolist()
            if not trigger_idx_list:
                print(f"[{file}] 未找到 CH1 触发信号，跳过。")
                continue
            
            t0 = df['Time'].loc[trigger_idx_list[0]] # 绝对零点
            df['Time_ms'] = (df['Time'] - t0) * 1000 # 把时间全部转换成毫秒，并以 t0 为 0 点
            
            # 3. 截取我们需要分析的窗口 (-2ms 到 20ms)
            window = df[(df['Time_ms'] >= -2) & (df['Time_ms'] <= 20)].copy()
            
            if len(window) < 100:
                continue # 数据不够长，跳过
                
            # 4. 计算采样率 (fs)
            dt = df['Time'].iloc[1] - df['Time'].iloc[0]
            fs = 1.0 / dt
            
            # 5. 【核心】对 CH2 (12V 电源) 进行 300Hz 低通滤波
            window['CH2_filtered'] = butter_lowpass_filter(window['CH2'], cutoff=300, fs=fs, order=2)
            
            # 6. 在 2ms ~ 20ms 的区间内，寻找滤波后曲线的最低点（机械坑）
            search_window = window[(window['Time_ms'] >= 2.0) & (window['Time_ms'] <= 18.0)]
            min_idx = search_window['CH2_filtered'].idxmin()
            mechanical_delay = search_window['Time_ms'].loc[min_idx]
            
            # 将算出的延迟加入总表
            delay_results.append(mechanical_delay)
            print(f"[{file}] 算出机械延迟: {mechanical_delay:.3f} ms")
            
        except Exception as e:
            print(f"[{file}] 处理出错: {e}")

    # ==========================================
    # 统计与画图（写报告的王炸组合）
    # ==========================================
    if not delay_results:
        print("没有成功提取到任何数据！")
        return

    delay_array = np.array(delay_results)
    mean_delay = np.mean(delay_array)
    std_delay = np.std(delay_array)
    
    print("\n" + "="*40)
    print("🎯 终极统计结果报告")
    print("="*40)
    print(f"有效样本数: {len(delay_array)}")
    print(f"平均开启延迟: {mean_delay:.3f} ms")
    print(f"标准差 (Jitter): {std_delay:.3f} ms")
    print(f"最快响应: {np.min(delay_array):.3f} ms")
    print(f"最慢响应: {np.max(delay_array):.3f} ms")
    
    # 画一张直方图展示这 100 次的分布情况
    plt.figure(figsize=(10, 6))
    plt.hist(delay_array, bins=15, color='skyblue', edgecolor='black', alpha=0.7)
    plt.axvline(mean_delay, color='red', linestyle='dashed', linewidth=2, label=f'Mean: {mean_delay:.2f}ms')
    plt.title('Distribution of Solenoid Valve Mechanical Delay (100 Samples)')
    plt.xlabel('Mechanical Delay (ms)')
    plt.ylabel('Frequency (Count)')
    plt.legend()
    plt.grid(axis='y', alpha=0.75)
    
    plt.savefig('delay_distribution.png', dpi=300)
    print("\n✅ 已生成延迟分布统计图：delay_distribution.png")
    plt.show()

if __name__ == '__main__':
    main()