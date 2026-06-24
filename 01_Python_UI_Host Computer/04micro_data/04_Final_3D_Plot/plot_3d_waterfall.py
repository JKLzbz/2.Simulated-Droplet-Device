import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from fastdtw import fastdtw

# 设置中文字体和负号显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 定义路径 (使用绝对路径或基于当前文件的相对路径)
current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(current_dir) # 04micro_data 根目录
people_dir = os.path.join(base_dir, '02people_data')
mech_dir = os.path.join(base_dir, '03mech_data')

distances = [10, 40, 70, 100]
people_folders = ['10cm_730good', '40cm_700good', '70cm_690good', '100cm_NOTGOOD687']
mech_folders = ['10cm_atom235', '40cm_atom220', '70cm_atom205', '100cm']

def get_average_wave(folder_path):
    csv_files = glob.glob(os.path.join(folder_path, '*.csv'))
    waves = []
    for f in csv_files:
        try:
            df = pd.read_csv(f, skiprows=1)
            if df.shape[1] == 0: continue
            raw_data = df.iloc[:, 0].values
            baseline = np.mean(raw_data[:200]) if len(raw_data) > 200 else raw_data[0]
            signal = raw_data - baseline
            
            kernel = np.ones(5) / 5
            smoothed = np.convolve(signal, kernel, mode='same')
            
            peak_idx = np.argmax(smoothed)
            start = max(0, peak_idx - 300)
            end = min(len(smoothed), peak_idx + 1200)
            
            wave_slice = smoothed[start:end]
            if len(wave_slice) < 1500:
                wave_slice = np.pad(wave_slice, (0, 1500 - len(wave_slice)), 'constant')
            
            waves.append(wave_slice[:1500])
        except Exception as e:
            print(f"Error processing {f}: {e}")
    
    if waves:
        return np.mean(waves, axis=0)
    return np.zeros(1500)

fig = plt.figure(figsize=(14, 10))
ax = fig.add_subplot(111, projection='3d')

x = np.arange(1500) * 10 # 10ms per sample
dtw_scores = []

for i, d in enumerate(distances):
    p_path = os.path.join(people_dir, people_folders[i])
    m_path = os.path.join(mech_dir, mech_folders[i])
    
    p_wave = get_average_wave(p_path)
    m_wave = get_average_wave(m_path)
    
    # 纯形态 DTW 打分 (去除幅度绝对值差异带来的惩罚)
    p_max = np.max(p_wave) if np.max(p_wave) > 0 else 1.0
    m_max = np.max(m_wave) if np.max(m_wave) > 0 else 1.0
    p_norm = p_wave / p_max
    m_norm = m_wave / m_max
    
    distance_dtw, _ = fastdtw(p_norm, m_norm, dist=lambda a,b: abs(a-b))
    
    # 将累积距离映射为 0~100% 的得分 (1500 个点最大可能误差约为 1500)
    score = max(0.0, 100.0 * (1.0 - distance_dtw / 1500.0))
    dtw_scores.append(score)
    
    # 绘制机器波形 (红色实线，加粗)
    ax.plot(x, [d]*1500, m_wave, color='#e74c3c', linewidth=3.5, zorder=4, alpha=1.0)
    
    # 绘制真人波形 (蓝色虚线)
    ax.plot(x, [d]*1500, p_wave, color='#3498db', linewidth=2.5, linestyle='--', zorder=5, alpha=0.9)
    
    # 寻找波峰位置，将文本浮空悬挂在各自波峰的正上方，并增加白色半透明背景防遮挡
    peak_x = x[np.argmax(p_wave)]
    text_z_offset = 15 if d == 10 else (12 if d == 40 else (10 if d == 70 else 5))
    ax.text(peak_x, d, np.max(p_wave) + text_z_offset, f'DTW: {score:.1f}%', 
            color='black', fontsize=11, fontweight='bold', ha='center',
            bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=2))

# 补充虚拟的线条用于生成图例
ax.plot([], [], [], color='#3498db', linestyle='--', linewidth=2.5, label='真人基准波形 (Human)')
ax.plot([], [], [], color='#e74c3c', linewidth=3.5, label='机器模拟波形 (Machine)')

ax.set_xlabel('时间轴 Time (ms)', fontsize=12, labelpad=15)
ax.set_ylabel('空间衰减距离 Distance (cm)', fontsize=12, labelpad=15)
ax.set_zlabel('气溶胶能量振幅 Raw Delta (pF)', fontsize=12, labelpad=10)
ax.set_yticks(distances)
ax.set_yticklabels([f'{d}cm' for d in distances])

# 修改为图 5-3
ax.set_title('图5-3 跨空间维度气溶胶流体扩散验证 (3D Waterfall Plot)', fontsize=16, fontweight='bold', pad=20)

# 设置 3D 视角
ax.view_init(elev=25, azim=-55)
ax.legend(loc='upper right', fontsize=12)

# 保存图片到当前文件夹
out_file = os.path.join(current_dir, '图5-3_3D_Waterfall_DTW_Plot.png')
plt.savefig(out_file, dpi=300, bbox_inches='tight')
print(f'3D Waterfall Plot saved to {out_file}')

for i, d in enumerate(distances):
    print(f'{d}cm -> DTW: {dtw_scores[i]:.2f}%')
