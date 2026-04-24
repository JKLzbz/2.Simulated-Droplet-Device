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
    
    # 内流道起点 (向左延伸至宝塔最前端 X=-22)
    'A_top': (-22, 1.5),      'A_bot': (-22, -1.5)
}

# === 宝塔接头(外轮廓) 黄金 3 圈倒刺路径 ===
# 宝塔总长度 12mm (从 X=-10 到 X=-22)
pagoda_upper = [
    (-22, 2.4),     # 导角入口 (OD 4.8) -> y=2.4
    (-19, 3.1),     # 宝塔1 峰值 (OD 6.2)
    (-19, 2.5),     # 宝塔1 谷底 (OD 5.0)
    (-15.5, 3.1),   # 宝塔2 峰值 (OD 6.2)
    (-15.5, 2.5),   # 宝塔2 谷底 (OD 5.0)
    (-12, 3.1),     # 宝塔3 峰值 (OD 6.2)
    (-12, 2.5),     # 宝塔3 谷底 (OD 5.0)
    (-10, 2.5),     # 宝塔根部
    (-10, 6)        # 抬升至主壳体
]

pagoda_lower = [(x, -y) for x, y in pagoda_upper]

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

# === 标注关键点 ===
def annotate_pt(x, y, name_offset):
    ax.plot(x, y, 'ro', markersize=5)
    ax.text(x + name_offset[0], y + name_offset[1], f'({x}, {y})', fontsize=9, 
            color='white', bbox=dict(facecolor='black', alpha=0.7, boxstyle='round,pad=0.2'))

annotate_pt(*coords['B_top'], (-1.5, 0.8))
annotate_pt(*coords['C_top'], (-2, 0.8))
annotate_pt(*coords['D_top'], (0.5, 0.8))
annotate_pt(*coords['E_top'], (-3, 0.8))

# 宝塔核心参数标注
ax.text(-22, 4.5, "入口导角 OD: 4.8", color='blue', fontweight='bold')
ax.text(-19, 5.5, "波峰 OD: 6.2", color='blue', fontweight='bold')
ax.text(-12, 1.0, "波谷 OD: 5.0", color='blue', fontweight='bold')

plt.title("V7.0 工业级发生器内核 (全参数定死版)", fontsize=16, pad=20)
plt.tight_layout()
plt.show()