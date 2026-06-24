import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# 1. 创建画布
fig, ax = plt.subplots(figsize=(10, 6))

# 定义颜色
body_color = '#e0e0e0'  # 灰色实体块
air_color = '#ffffff'   # 白色流道
arrow_color = '#d62728' # 红色箭头
text_color = '#333333'

# 2. 画外部实体块 (灰色背景)
# 坐标 (x, y), 宽, 高
ax.add_patch(patches.Rectangle((0, 0), 200, 120, color=body_color, alpha=0.9))

# --- 3. 画内部流道 (挖空部分) ---

# (A) 左侧：高压进气口 (入口粗)
# 用多边形画一个收缩的喷嘴形状
# 坐标点依次连接
nozzle_shape = np.array([
    [0, 70], [40, 70], [70, 62], [90, 62], # 上边缘 (逐渐向下收缩)
    [90, 58], [70, 58], [40, 50], [0, 50]  # 下边缘 (逐渐向上收缩)
])
ax.add_patch(patches.Polygon(nozzle_shape, closed=True, color=air_color))

# (B) 右侧：混合扩压段 (出口变宽)
outlet_shape = np.array([
    [90, 62], [100, 70], [200, 70],  # 上边缘扩张
    [200, 50], [100, 50], [90, 58]   # 下边缘扩张
])
ax.add_patch(patches.Polygon(outlet_shape, closed=True, color=air_color))

# (C) 上方：雾化进气口 (垂直吸入)
vert_inlet_shape = np.array([
    [85, 120], [95, 120], # 顶部入口
    [95, 62], [85, 62]    # 连接到底部主管道
])
ax.add_patch(patches.Polygon(vert_inlet_shape, closed=True, color=air_color))


# --- 4. 添加标注和箭头 ---

# 箭头：高压气
ax.annotate("High Pressure Air\n(0.3 MPa)", xy=(50, 60), xytext=(10, 60),
            arrowprops=dict(facecolor=arrow_color, shrink=0.05),
            fontsize=10, ha='center', va='center')

# 箭头：吸入雾气
ax.annotate("Fog Suction\n(Entrainment)", xy=(90, 75), xytext=(90, 110),
            arrowprops=dict(facecolor=arrow_color, shrink=0.05),
            fontsize=10, ha='center', va='center')

# 箭头：喷出飞沫
ax.annotate("Cough Spray\n(Turbulent Mist)", xy=(190, 60), xytext=(140, 60),
            arrowprops=dict(facecolor=arrow_color, shrink=0.05),
            fontsize=10, ha='center', va='center')

# 文字说明
ax.text(20, 75, "Inlet (Dia 5mm)", fontsize=9)
ax.text(90, 45, "Nozzle Throat (Dia 2mm)", fontsize=9, color='red', ha='center', fontweight='bold')
ax.text(160, 45, "Expansion Outlet", fontsize=9, ha='center')

# 添加原理说明框
note_text = (
    "Device Principle (Venturi Effect):\n"
    "1. High pressure air speeds up at the 2mm Nozzle.\n"
    "2. High velocity creates Low Pressure (Vacuum).\n"
    "3. Fog is sucked in from the top inlet.\n"
    "4. Air and Fog mix and spray out."
)
ax.text(5, 5, note_text, fontsize=10, bbox=dict(facecolor='white', alpha=0.8))

# 设置显示范围和去除坐标轴
ax.set_xlim(0, 200)
ax.set_ylim(0, 120)
ax.axis('off')
ax.set_title("Concept Design: Venturi Atomizer Nozzle", fontsize=14, fontweight='bold', pad=15)

# 5. 显示并保存
plt.tight_layout()
plt.show()