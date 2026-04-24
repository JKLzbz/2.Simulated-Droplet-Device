import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(figsize=(14, 8))
ax.set_aspect('equal')
ax.axis('off')

# === 核心坐标字典 (喉管中心为 0,0) ===
# 所有的 X, Y 坐标已经为你严格计算完毕！
coords = {
    'A_top': (-15, 1.5),    'A_bot': (-15, -1.5),    # 进气口起点 (左延伸10mm插管子)
    'B_top': (-5, 1.5),     'B_bot': (-5, -1.5),     # 收缩段起点
    'C_top': (-1.25, 0.75),    'C_bot': (-1.25, -0.75),    # 喉管起点 (收缩长度4mm)
    'D_top': (1.25, 0.75),     'D_bot': (1.25, -0.75),     # 喉管终点 (喉管长度2mm)
    'E_top': (18, 2.0),     'E_bot': (18, -2.0),     # 扩散段终点 (扩散长度17mm)
    
    'V_left': (-1.25, -15), 'V_right': (1.25, -15),  # 2.5mm 垂直吸气管底部 (Y=-15)
    'S_left': (-10.1, -15), 'S_right': (10.1, -15),  # 20.2mm 沉头槽天花板
    'S_bot_L': (-10.1, -17.5), 'S_bot_R': (10.1, -17.5) # 沉头槽底部 (深2.5mm)
}

# === 绘制实体剖面 (用灰色填充 + 斜线表示剖切的实体部分) ===
# 上半部分实体
upper_poly = [
    (-15, 6), (18, 6), (18, 2.0), coords['E_top'], coords['D_top'], 
    coords['C_top'], coords['B_top'], coords['A_top'], (-15, 6)
]
ax.add_patch(patches.Polygon(upper_poly, facecolor='#BDC3C7', edgecolor='#2C3E50', lw=2, hatch='//'))

# 下半部分左侧实体
lower_left_poly = [
    (-15, -6), (-10.1, -6), coords['S_bot_L'], coords['S_left'], 
    coords['V_left'], (-1.25, -0.75), coords['C_bot'], coords['B_bot'], 
    coords['A_bot'], (-15, -6)
]
ax.add_patch(patches.Polygon(lower_left_poly, facecolor='#BDC3C7', edgecolor='#2C3E50', lw=2, hatch='//'))

# 下半部分右侧实体
lower_right_poly = [
    (18, -6), (10.1, -6), coords['S_bot_R'], coords['S_right'], 
    coords['V_right'], (1.25, -0.75), coords['D_bot'], coords['E_bot'], 
    (18, -6)
]
ax.add_patch(patches.Polygon(lower_right_poly, facecolor='#BDC3C7', edgecolor='#2C3E50', lw=2, hatch='//'))

# === 标注流体通道中心线 ===
ax.axhline(0, color='red', linestyle='-.', lw=1, alpha=0.6)
ax.axvline(0, ymin=0.1, ymax=0.5, color='red', linestyle='-.', lw=1, alpha=0.6)

# === 绘制装配的雾化片和硅胶圈 ===
ax.add_patch(patches.Rectangle((-10, -21.5), 20, 4, facecolor='#F39C12', alpha=0.6))
ax.text(0, -19.5, "20mm 硅胶密封圈 (被沉头槽压紧)", ha='center', color='#D35400', fontweight='bold')
ax.plot([-8, 8], [-17.5, -17.5], color='#27AE60', lw=4) # 金属片

# === 标注关键点坐标 (Fusion 360 建模直接抄) ===
def annotate_pt(pt_name, text_offset):
    x, y = coords[pt_name]
    ax.plot(x, y, 'ro', markersize=6)
    ax.text(x + text_offset[0], y + text_offset[1], f'({x}, {y})', fontsize=10, 
            color='white', bbox=dict(facecolor='black', alpha=0.7, boxstyle='round,pad=0.2'))

annotate_pt('B_top', (-2, 0.5))
annotate_pt('C_top', (-1, 0.5))
annotate_pt('D_bot', (1, -1.5))
annotate_pt('E_top', (-3, 0.5))
annotate_pt('V_left', (-4, 1))

# === 标注圆角和角度 ===
# 收缩角标注
ax.text(-3, 2.5, "单侧 10.5°", color='blue', fontweight='bold')
# 扩散角标注
ax.text(8, 2.5, "单侧 4.2°", color='blue', fontweight='bold')
# 内部圆角标注 (使用箭头指示)
ax.annotate('此处做 R=0.5mm 圆角\n(让雾气顺滑吸入)', xy=(-1.25, -15), xytext=(-12, -12),
            arrowprops=dict(facecolor='magenta', shrink=0.05), color='magenta', fontweight='bold')

plt.title("V5 终极版：三口文丘里管 绝对坐标制图 (原点 0,0 为喉管中心)", fontsize=16, pad=20)
plt.tight_layout()
plt.show()