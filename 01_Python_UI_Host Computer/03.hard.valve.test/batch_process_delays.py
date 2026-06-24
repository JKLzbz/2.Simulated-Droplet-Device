import pandas as pd
import numpy as np
import os
import glob
from scipy.signal import butter, filtfilt
import matplotlib.pyplot as plt

def butter_lowpass(cutoff, fs, order=2):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def get_delay_from_csv(filepath):
    try:
        df = pd.read_csv(filepath, skiprows=2, names=['Time', 'CH1', 'CH2'], encoding='utf-8', on_bad_lines='skip')
        df = df.dropna()
        df['Time'] = pd.to_numeric(df['Time'], errors='coerce')
        df['CH1'] = pd.to_numeric(df['CH1'], errors='coerce')
        df['CH2'] = pd.to_numeric(df['CH2'], errors='coerce')
        df = df.dropna()
        
        t = df['Time'].values
        ch1 = df['CH1'].values
        ch2 = df['CH2'].values
        
        dt = t[1] - t[0]
        if dt == 0: return np.nan
        fs = 1.0 / dt
        
        trigger_idx = np.argmax(ch1 > 1.5)
        if trigger_idx == 0 and ch1[0] <= 1.5:
            trigger_idx = np.searchsorted(t, 0.0)
        t_trigger = t[trigger_idx]
        
        b, a = butter_lowpass(300.0, fs, order=2)
        if len(ch2) > 33:
            ch2_filt = filtfilt(b, a, ch2)
        else:
            ch2_filt = ch2
            
        start_idx = trigger_idx
        end_idx = np.searchsorted(t, t_trigger + 0.015)
        if end_idx > len(t): end_idx = len(t)
        
        window_t = t[start_idx:end_idx]
        window_ch2 = ch2_filt[start_idx:end_idx]
        
        if len(window_ch2) > 0:
            min_idx = np.argmin(window_ch2)
            dip_t = window_t[min_idx]
            return (dip_t - t_trigger) * 1000.0
        return np.nan
    except:
        return np.nan

if __name__ == "__main__":
    base_dir = r"D:\02Projects\01Simulated-Droplet-Device\01_Python_UI_Host Computer\03.hard.valve.test"
    # 现在文件夹已经被重组过了，只有 0load 以及 1 到 8
    folders = ['0load', '1', '2', '3', '4', '5', '6', '7', '8']
    pressures = [0.00, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08]

    results = []
    print("开始处理最新排列好的单调数据...")
    for folder, p in zip(folders, pressures):
        folder_path = os.path.join(base_dir, folder)
        csv_files = glob.glob(os.path.join(folder_path, '*.csv'))
        
        delays = []
        for f in csv_files:
            d = get_delay_from_csv(f)
            if not np.isnan(d) and 1.0 < d < 15.0:
                delays.append(d)
                
        if delays:
            mean_d = np.mean(delays)
            std_d = np.std(delays)
            results.append({
                'Pressure_MPa': p,
                'Count': len(delays),
                'Mean_Delay_ms': mean_d,
                'Std_Delay_ms': std_d
            })
            print(f"气压: {p:.2f} MPa | 解析文件: {len(delays)} | 平均延迟: {mean_d:.3f} ms | 标准差: {std_d:.3f} ms")

    # 保存最终表格
    res_df = pd.DataFrame(results)
    csv_out = os.path.join(base_dir, "Final_Delay_Summary.csv")
    res_df.to_csv(csv_out, index=False)
    
    # 绘制最高级的学术阴影图 (Shaded Envelope)
    x = res_df['Pressure_MPa']
    y = res_df['Mean_Delay_ms']
    std = res_df['Std_Delay_ms']

    plt.figure(figsize=(8, 5))
    plt.rcParams['font.sans-serif'] = ['SimHei']  # 正常显示中文标签
    plt.rcParams['axes.unicode_minus'] = False    # 正常显示负号
    
    plt.plot(x, y, '-o', color='#1f77b4', linewidth=2, markersize=6, label='Mean Delay')
    plt.fill_between(x, y - std, y + std, color='#1f77b4', alpha=0.2, label='Jitter Envelope ($\pm 1$ SD)')

    plt.title('变气压条件下的电磁阀机械延迟与抖动特性', fontsize=14, pad=15)
    plt.xlabel('工作气压 (MPa)', fontsize=12)
    plt.ylabel('机械延迟与抖动 (ms)', fontsize=12)
    plt.ylim(5.0, 8.0) # 黄金比例坐标
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(loc='lower right')
    
    img_out = os.path.join(base_dir, "Shaded_Delay_Curve.png")
    plt.savefig(img_out, dpi=300, bbox_inches='tight')
    print("\n处理完成！最终总表和高级阴影图均已更新并保存。")
