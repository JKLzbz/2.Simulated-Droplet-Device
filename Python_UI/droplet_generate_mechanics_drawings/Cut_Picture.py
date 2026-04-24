import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(figsize=(12, 6))
ax.set_xlim(-10, 80)
ax.set_ylim(-30, 30)
ax.set_aspect('equal')
ax.axis('off')

# === 绘制文丘里管上壁 (灰黑色) ===
upper_wall = [
    [0, 10], [25, 10], [30, 4], [35, 4], [55, 8], [70, 8]
]
# === 绘制文丘里管下壁 (灰黑色) ===
lower_wall_left = [
    [0, -10], [25, -10], [28, -4]
]
lower_wall_right = [
    [37, -4], [55, -8], [70, -8]
]

# 绘制墙体线条
def plot_wall(points):
    x, y = zip(*points)
    ax.plot(x, y, color='#2C3E50', lw=4)

plot_wall(upper_wall)
plot_wall(lower_wall_left)
plot_wall(lower_wall_right)

# === 绘制下方的垂直吸气道与沉头槽 ===
# 垂直道 (2.5mm 内径)
ax.plot([28, 28], [-4, -15], color='#2C3E50', lw=4)
ax.plot([37, 37], [-4, -15], color='#2C3E50', lw=4)
# 沉头槽 (20.2mm 宽, 用于压死硅胶圈)
ax.plot([15, 28], [-15, -15], color='#2C3E50', lw=4)
ax.plot([15, 15], [-15, -25], color='#2C3E50', lw=4)
ax.plot([37, 50], [-15, -15], color='#2C3E50', lw=4)
ax.plot([50, 50], [-15, -25], color='#2C3E50', lw=4)

# === 绘制雾化片与硅胶圈 (装配位) ===
# 硅胶圈 (外径20mm)
ax.add_patch(patches.Rectangle((15.5, -22), 19, 4, facecolor='#BDC3C7', alpha=0.8)) # 胶圈
ax.add_patch(patches.Rectangle((22.5, -20), 5, 1, facecolor='#27AE60')) # 16mm金属片中心
ax.text(25, -24, "雾化片及硅胶圈 (在此处被压紧)", ha='center', color='#27AE60', fontsize=10)

# === 标注关键尺寸与名称 ===
# 进气口
ax.annotate('1. 主进气口 (内径 3mm)\n接气泵软管', xy=(5, 0), xytext=(-5, 15),
             arrowprops=dict(arrowstyle='->'), fontsize=11)
# 喉管
ax.annotate('2. 加速喉管 (1.5mm)\n产生核心负压', xy=(32.5, 0), xytext=(20, 20),
             arrowprops=dict(arrowstyle='->'), fontweight='bold', color='#E74C3C')
# 垂直卷吸道
ax.annotate('3. 卷吸孔 (2.5mm)', xy=(32.5, -10), xytext=(45, -10),
             arrowprops=dict(arrowstyle='->'), fontsize=10)
# 沉头槽
ax.annotate('4. 沉头密封槽 (20.2mm)\n正好罩住并压扁硅胶圈', xy=(15, -15), xytext=(-10, -20),
             arrowprops=dict(arrowstyle='->'), fontsize=10, color='#2980B9')
# 出口
ax.annotate('5. 出气扩散段\n射向传感器', xy=(65, 0), xytext=(65, 15),
             arrowprops=dict(arrowstyle='->'), fontsize=11)

# 气流示意
ax.quiver([5, 15, 31, 50, 65], [0, 0, 0, 0, 0], [1, 1, 3, 1, 1], [0, 0, 0, 0, 0], 
          color='#3498DB', scale=15, width=0.005)
# 雾滴卷吸示意
ax.quiver([32.5], [-12], [0], [1], color='#2ECC71', scale=15, width=0.005)

plt.title("三口文丘里气动剪切模块 C：内部流道工程截面图", fontsize=15, pad=20)
plt.show()