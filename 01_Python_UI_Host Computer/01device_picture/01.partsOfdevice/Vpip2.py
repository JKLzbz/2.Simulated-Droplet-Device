import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(figsize=(15, 8))
ax.set_aspect('equal')
ax.axis('off')

# === 核心联动坐标字典 (喉管中心为 0,0) ===
coords = {
    # 喉管与吸气孔的完美对接 (长度 2.5mm)
    'C_top': (-1.25, 0.75),   'C_bot': (-1.25, -0.75), 
    'D_top': (1.25, 0.75),    'D_bot': (1.25, -0.75),  
    
    # 收缩段左移 (保持 4mm 长度，10.5° 夹角)
    'B_top': (-5.25, 1.5),    'B_bot': (-5.25, -1.5),  
    
    # 扩散段右移 (保持 17mm 长度，4.2° 夹角)
    'E_top': (18.25, 2.0),    'E_bot': (18.25, -2.0),  

    # 垂直吸气管与沉头槽
    'V_left': (-1.25, -15),   'V_right': (1.25, -15), 
    'S_left': (-10.1, -15),   'S_right': (10.1, -15),  
    'S_bot_L': (-10.1, -17.5), 'S_bot_R': (10.1, -17.5),
    
    # 宝塔接头内侧流道起点
    'A_top': (-18, 1.5),      'A_bot': (-18, -1.5)
}

# === 宝塔接头(外轮廓)路径 ===
# 从 x=-18 延伸到 x=-10 的外部特征
pagoda_upper = [
    (-18, 2.2),   # 导角起点 (OD 4.4)
    (-15, 2.9),   # 宝塔1 峰值 (OD 5.8)
    (-15, 2.5),   # 宝塔1 谷底 (OD 5.0)
    (-12, 2.9),   # 宝塔2 峰值 (OD 5.8)
    (-12, 2.5),   # 宝塔2 谷底 (OD 5.0)
    (-10, 2.5),   # 根部
    (-10, 6)      # 抬升至法兰/主壳体
]

pagoda_lower = [
    (-18, -2.2), (-15, -2.9), (-15, -2.5), (-12, -2.9), (-12, -2.5), (-10, -2.5), (-10, -6)
]

# === 绘制实体剖面 (灰色填充 + 斜线) ===
# 上半部分实体
upper_poly = pagoda_upper + [
    (18.25, 6), (18.25, 2.0), coords['E_top'], coords['D_top'], 
    coords['C_top'], coords['B_top'], (-10, 1.5), coords['A_top'], pagoda_upper[0]
]
ax.add_patch(patches.Polygon(upper_poly, facecolor='#BDC3C7', edgecolor='#2C3E50', lw=2, hatch='//'))

# 下半部分左侧实体 (包含宝塔下半部)
lower_left_poly = pagoda_lower + [
    (-10.1, -6), coords['S_bot_L'], coords['S_left'], coords['V_left'], 
    (-1.25, -0.75), coords['C_bot'], coords['B_bot'], (-10, -1.5), 
    coords['A_bot'], pagoda_lower[0]
]
ax.add_patch(patches.Polygon(lower_left_poly, facecolor='#BDC3C7', edgecolor='#2C3E50', lw=2, hatch='//'))

# 下半部分右侧实体
lower_right_poly = [
    (18.25, -6), (10.1, -6), coords['S_bot_R'], coords['S_right'], 
    coords['V_right'], (1.25, -0.75), coords['D_bot'], coords['E_bot'], 
    (18.25, -6)
]
ax.add_patch(patches.Polygon(lower_right_poly, facecolor='#BDC3C7', edgecolor='#2C3E50', lw=2, hatch='//'))

# === 标注流体通道中心线 ===
ax.axhline(0, color='red', linestyle='-.', lw=1, alpha=0.6)
ax.axvline(0, ymin=0.15, ymax=0.45, color='red', linestyle='-.', lw=1, alpha=0.6)

# === 绘制装配的雾化片和硅胶圈 ===
ax.add_patch(patches.Rectangle((-10, -21.5), 20, 4, facecolor='#F39C12', alpha=0.6))
ax.text(0, -19.5, "20mm 硅胶密封圈", ha='center', color='#D35400', fontweight='bold')
ax.plot([-8, 8], [-17.5, -17.5], color='#27AE60', lw=4) # 金属片

# === 标注坐标点 ===
def annotate_pt(x, y, name_offset):
    ax.plot(x, y, 'ro', markersize=5)
    ax.text(x + name_offset[0], y + name_offset[1], f'({x}, {y})', fontsize=9, 
            color='white', bbox=dict(facecolor='black', alpha=0.7, boxstyle='round,pad=0.2'))

annotate_pt(*coords['B_top'], (-2, 0.8))
annotate_pt(*coords['C_top'], (-1, 0.8))
annotate_pt(*coords['D_top'], (0.5, 0.8))
annotate_pt(*coords['E_top'], (-3, 0.8))
annotate_pt(-15, 2.9, (-1, 1.5)) # 标注宝塔尖端

# === 工程指示与注释 ===
# 宝塔说明
ax.annotate('双层宝塔倒刺接头\n外径 5.8mm, 内径 3mm\n紧咬 5mm 软管防脱落', xy=(-15, 3.5), xytext=(-22, 6.5),
            arrowprops=dict(facecolor='#2980B9', shrink=0.05, width=1.5, headwidth=6), 
            color='#2980B9', fontweight='bold', fontsize=11)
            
# 喉管说明
ax.text(0, 2.5, "长度 2.5mm\n完美覆盖下方吸气孔", ha='center', color='#E74C3C', fontweight='bold')

plt.title("V6.0 终极流体外设图：全联动坐标 + 宝塔防脱接头", fontsize=16, pad=20)
plt.tight_layout()
plt.show()