import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import os

# 修复中文显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 定义任务 (Phases and Hardware)
tasks = [
    ('阶段0 基础蓄压', 0, 2800, 'Phase'),
    ('阶段1 高频蓄雾', 2800, 3018, 'Phase'),
    ('阶段2a 阀芯起飞', 3018, 3025, 'Phase'),
    ('阶段2b 精准爆破', 3025, 3075, 'Phase'),
    ('阶段3 清风扫膛', 3075, 3125, 'Phase'),
    ('气泵 (Pump)', 0, 3025, 'Hardware'),
    ('雾化片 (Atomizer)', 2800, 3075, 'Hardware'),
    ('电磁阀 (Valve)', 3018, 3125, 'Hardware'),
    ('触发激光 (Laser)', 3025, 3125, 'Hardware')
]

fig, ax = plt.subplots(figsize=(15, 8))

# 颜色设置
color_phase = '#3498db'
color_hw = '#e74c3c'

labels = []
for i, (name, start, end, type_) in enumerate(reversed(tasks)):
    color = color_phase if type_ == 'Phase' else color_hw
    ax.barh(i, end - start, left=start, height=0.5, align='center', color=color, alpha=0.8, edgecolor='black')
    labels.append(name)
    
    # 在色块上添加持续时间文字
    duration = end - start
    if duration > 100:
        ax.text(start + duration/2, i, f'{duration}ms', ha='center', va='center', color='white', fontweight='bold')
    else:
        ax.text(end + 15, i, f'{duration}ms', ha='left', va='center', color='black', fontweight='bold')

# 坐标轴与标题格式化
ax.set_yticks(range(len(labels)))
ax.set_yticklabels(labels, fontsize=12)
ax.set_xlabel('时间轴 / ms', fontsize=12, fontweight='bold')
ax.set_title('图5-2 最优自适应物理时序 (基准HGW标定)', fontsize=15, fontweight='bold')

# 放大聚焦于起飞核心区域
ax.set_xlim(2700, 3200)
ax.grid(True, axis='x', linestyle='--', alpha=0.7)

# 核心危险区与爆破区高亮
ax.axvspan(3018, 3025, color='orange', alpha=0.3, label='机械延迟死区 (6.8ms)')
ax.axvspan(3025, 3075, color='red', alpha=0.15, label='射流爆发区 (50ms)')

ax.legend(loc='upper right', fontsize=12, facecolor='white', framealpha=0.9)
plt.tight_layout()

# 保存到本脚本同级目录
out_dir = os.path.dirname(os.path.abspath(__file__))
out_path = os.path.join(out_dir, 'V6_Optimal_Timing.png')
plt.savefig(out_path, dpi=300)
print(f'Gantt chart saved to {out_path}')
