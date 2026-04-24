import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# 设置支持中文显示的字体
plt.rcParams['font.sans-serif'] = ['SimHei'] 
plt.rcParams['axes.unicode_minus'] = False

def draw_cylinder(ax, center_x, center_y, radius, height, bottom=0, color='blue', alpha=0.3):
    """
    绘制圆柱体的通用辅助函数
    """
    # 1. 绘制侧面
    z = np.linspace(bottom, bottom + height, 10)
    theta = np.linspace(0, 2*np.pi, 25)
    theta_grid, z_grid = np.meshgrid(theta, z)
    x_grid = radius * np.cos(theta_grid) + center_x
    y_grid = radius * np.sin(theta_grid) + center_y
    ax.plot_surface(x_grid, y_grid, z_grid, color=color, alpha=alpha, shade=True)
    
    # 2. 绘制顶部和底部的盖子 (增加保险：alpha上限为1.0)
    cap_alpha = min(1.0, alpha + 0.2) 
    for z_cap in [bottom, bottom + height]:
        r = np.linspace(0, radius, 5)
        tg, rg = np.meshgrid(theta, r)
        xg = rg * np.cos(tg) + center_x
        yg = rg * np.sin(tg) + center_y
        zg = np.full_like(xg, z_cap)
        ax.plot_surface(xg, yg, zg, color=color, alpha=cap_alpha, shade=True)

def draw_horizontal_pipe(ax, start_x, y, z, radius, length, color='gray', alpha=0.2):
    """
    绘制横向管道的辅助函数
    """
    x = np.linspace(start_x, start_x + length, 20)
    theta = np.linspace(0, 2*np.pi, 20)
    theta_grid, x_grid = np.meshgrid(theta, x)
    y_grid = radius * np.cos(theta_grid) + y
    z_grid = radius * np.sin(theta_grid) + z
    ax.plot_surface(x_grid, y_grid, z_grid, color=color, alpha=alpha, shade=True)

fig = plt.figure(figsize=(12, 9))
ax = fig.add_subplot(111, projection='3d')

# ==========================================
# 1. 下半部分：恒压供液底座（发生器核心）
# ==========================================

# 发生器主腔体 - 浅灰色
draw_cylinder(ax, 0, 0, 2, 3, bottom=0, color='lightgrey', alpha=0.4)
ax.text(0, 0, 0.5, "发生器主腔体", color='black', fontsize=10, ha='center')

# 马里奥特组件 (侧挂倒扣瓶)
draw_cylinder(ax, -4, 0, 1.5, 4, bottom=2, color='skyblue', alpha=0.3)
draw_cylinder(ax, -4, 0, 0.4, 1.5, bottom=1, color='deepskyblue', alpha=0.5)
ax.text(-4, 0, 6.5, "马里奥特储液瓶", color='blue', fontsize=9, ha='center')

# 抽水组件：吸水棉棒 - 棕色 (Alpha改为0.9防止溢出)
draw_cylinder(ax, 0, 0, 0.2, 4.9, bottom=0.1, color='peru', alpha=0.9)

# 造雾机关：16mm 压电陶瓷片
draw_cylinder(ax, 0, 0, 0.8, 0.1, bottom=5.0, color='silver', alpha=0.8)
ax.text(0, 0, 5.4, "16mm/5μm 雾化片", color='black', fontsize=10, fontweight='bold', ha='center')

# ==========================================
# 2. 上半部分：三口文丘里管
# ==========================================

# 主进气口主管道 (横向橙色)
draw_horizontal_pipe(ax, -6, 0, 7, 0.6, 12, color='orange', alpha=0.3)

# 副进气口 (垂直吸管)
draw_cylinder(ax, 0, 0, 0.4, 1.9, bottom=5.1, color='green', alpha=0.5)

# 标注
ax.text(-6, 0, 7.8, "主进气口(0.3MPa)", color='darkorange', fontsize=9, ha='center')
ax.text(6, 0, 7.8, "出气口(喷向FDC)", color='red', fontsize=9, ha='center')

# 模拟：飞沫流线
for _ in range(15):
    xs = np.linspace(0.5, 7, 5)
    ys = np.random.normal(0, 0.4, 5)
    zs = np.random.normal(7, 0.2, 5)
    ax.plot(xs, ys, zs, color='cyan', alpha=0.4, linewidth=1, linestyle=':')

# ==========================================
# 界面设置
# ==========================================
ax.set_title('模拟飞沫发生装置 - 3D 机械结构原理图', fontsize=15, pad=30)
ax.set_xlabel('X轴 (长度)')
ax.set_ylabel('Y轴 (宽度)')
ax.set_zlabel('Z轴 (高度)')

ax.view_init(elev=25, azim=-55)

# 移除背景色增强图纸感
ax.xaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
ax.yaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
ax.zaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))

plt.tight_layout()
plt.show()