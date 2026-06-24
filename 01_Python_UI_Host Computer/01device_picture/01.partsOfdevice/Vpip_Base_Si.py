import matplotlib
matplotlib.use('Agg')  # 保持纯后台绘图，防卡死

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

# ================== 完美解决中文显示 ==================
plt.rcParams['font.sans-serif'] = ['SimHei']  
plt.rcParams['axes.unicode_minus'] = False    
# ==================================================================

fig, ax = plt.subplots(figsize=(8, 6.4))
ax.set_aspect('equal') 

# 尺寸参数 (单位: mm)
width = 50
height = 40
hole_radius = 2.0         
center_hole_radius = 6.0  
edge_dist = 5.0           

# 1. 绘制硅胶垫外轮廓
rect = patches.Rectangle((-width/2, -height/2), width, height, 
                         linewidth=2, edgecolor='black', facecolor='#e0f7fa', alpha=0.7)
ax.add_patch(rect)

# 2. 绘制中心气流圆孔
center_hole = patches.Circle((0, 0), center_hole_radius, 
                             linewidth=1.5, edgecolor='black', facecolor='white')
ax.add_patch(center_hole)

# 3. 绘制四个角的螺丝圆孔
hole_positions = [
    (width/2 - edge_dist, height/2 - edge_dist),    
    (-width/2 + edge_dist, height/2 - edge_dist),   
    (width/2 - edge_dist, -height/2 + edge_dist),   
    (-width/2 + edge_dist, -height/2 + edge_dist)   
]

for pos in hole_positions:
    hole = patches.Circle(pos, hole_radius, 
                          linewidth=1.5, edgecolor='black', facecolor='white')
    ax.add_patch(hole)

# ================= 标注尺寸线与文字 =================
# 总宽度 50mm
plt.plot([-width/2, width/2], [-height/2 - 4, -height/2 - 4], color='black', lw=1)
plt.plot([-width/2, -width/2], [-height/2 - 5, -height/2 - 3], color='black', lw=1)
plt.plot([width/2, width/2], [-height/2 - 5, -height/2 - 3], color='black', lw=1)
plt.text(0, -height/2 - 6, '50 mm', ha='center', va='top', fontsize=10, fontweight='bold')

# 总高度 40mm
plt.plot([width/2 + 4, width/2 + 4], [-height/2, height/2], color='black', lw=1)
plt.plot([width/2 + 3, width/2 + 5], [-height/2, -height/2], color='black', lw=1)
plt.plot([width/2 + 3, width/2 + 5], [height/2, height/2], color='black', lw=1)
plt.text(width/2 + 6, 0, '40 mm', ha='left', va='center', rotation=270, fontsize=10, fontweight='bold')

# 孔位距离边缘
plt.plot([width/2 - edge_dist, width/2], [height/2 - edge_dist, height/2 - edge_dist], color='red', ls='--', lw=1)
plt.text(width/2 - edge_dist/2, height/2 - edge_dist - 0.5, '5mm', color='red', ha='center', va='top', fontsize=9)
plt.plot([width/2 - edge_dist, width/2 - edge_dist], [height/2 - edge_dist, height/2], color='red', ls='--', lw=1)
plt.text(width/2 - edge_dist - 0.5, height/2 - edge_dist/2, '5mm', color='red', ha='right', va='center', fontsize=9)


# ================= 修改标注位置 =================

# 标注中心孔径 (引线指向左侧圆弧边缘，文字放在左侧宽阔空白区)
plt.annotate(r'$\phi$12 mm' + '\n中心通气孔', 
             xy=(-6, 0),        # 箭头终点：左侧圆弧边缘 (x=-6, y=0)
             xytext=(-18, 0),   # 文字起点：向左平移到 x=-18
             arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.5),
             ha='right', va='center', fontsize=10)

# 标注螺丝孔径
plt.annotate(r'$\phi$4 mm' + '\n螺丝过孔', 
             xy=(20, 15), 
             xytext=(25, 20),
             arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.5),
             ha='center', va='bottom', fontsize=10)

# =================================================

# 图表边距与修饰
plt.title('法兰硅胶密封垫 2D 图纸 (厚度: 2.0 mm)', fontsize=14, pad=20, fontname='SimHei') 
plt.xlim(-width/2 - 10, width/2 + 15)
plt.ylim(-height/2 - 10, height/2 + 10)
plt.grid(True, linestyle=':', alpha=0.6)
plt.xticks([])
plt.yticks([])

save_dir = r"D:\Projects\Simulated-Droplet-Device\01_Python_UI_Host Computer\picture_droplet_generate_mechanics"
os.makedirs(save_dir, exist_ok=True)
full_path = os.path.join(save_dir, 'Vpip_base_si.png')

plt.savefig(full_path, dpi=300, bbox_inches='tight')
print(f"图纸已成功生成并保存至: {full_path}")