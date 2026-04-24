import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

plt.rcParams['font.sans-serif'] = ['SimHei']  # 设置字体为黑体以正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False    # 解决设置中文字体后，负号 '-' 显示为方块的问题
# 创建画布
fig, ax = plt.subplots(figsize=(6, 6))
ax.set_aspect('equal') # 保证比例 1:1，圆不会变椭圆

# 定义尺寸参数 (单位: mm)
outer_diameter = 35.0
inner_diameter = 28.0
outer_radius = outer_diameter / 2
inner_radius = inner_diameter / 2

# 1. 绘制外圈圆 (硅胶垫外轮廓)
outer_circle = patches.Circle((0, 0), outer_radius, 
                              linewidth=2, edgecolor='black', facecolor='#e0f7fa', alpha=0.8)
ax.add_patch(outer_circle)

# 2. 绘制内圈圆 (通孔)
inner_circle = patches.Circle((0, 0), inner_radius, 
                              linewidth=2, edgecolor='black', facecolor='white')
ax.add_patch(inner_circle)

# ================= 标注尺寸线与文字 =================
# 标注外径 (OD: 35mm)
plt.plot([-outer_radius, outer_radius], [outer_radius + 2, outer_radius + 2], color='black', lw=1)
plt.plot([-outer_radius, -outer_radius], [outer_radius + 1, outer_radius + 3], color='black', lw=1)
plt.plot([outer_radius, outer_radius], [outer_radius + 1, outer_radius + 3], color='black', lw=1)
plt.text(0, outer_radius + 3, f'外径 (OD): {outer_diameter} mm', 
         ha='center', va='bottom', fontsize=11, fontweight='bold')

# 标注内径 (ID: 28mm)
plt.plot([-inner_radius, inner_radius], [0, 0], color='red', ls='--', lw=1.5)
plt.text(0, -1.5, f'内径 (ID): {inner_diameter} mm', 
         color='red', ha='center', va='top', fontsize=11, fontweight='bold')

# 标注厚度
plt.annotate('厚度: 2.0 mm\n(马里奥特瓶端面密封)', xy=(outer_radius*0.7, outer_radius*0.7), 
             xytext=(outer_radius + 2, outer_radius + 5),
             arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.5),
             ha='left', va='bottom', fontsize=11, fontweight='bold')

# 中心十字定位线
plt.plot([-3, 3], [0, 0], color='gray', lw=1)
plt.plot([0, 0], [-3, 3], color='gray', lw=1)

# 设置图表标题与边距
plt.title('马里奥特瓶底座 硅胶密封环 2D 图纸', fontsize=14, pad=20, fontname='SimHei')
plt.xlim(-outer_radius - 10, outer_radius + 15)
plt.ylim(-outer_radius - 10, outer_radius + 15)
plt.grid(True, linestyle=':', alpha=0.6)

# 取消坐标轴刻度数字
plt.xticks([])
plt.yticks([])
# 定义你的目标文件夹
save_dir = r"D:\Projects\VScode_py_all\picture_droplet_generate_mechanics"
# 检查文件夹是否存在，如果不存在则自动创建（防报错神器）
if not os.path.exists(save_dir):
    os.makedirs(save_dir)
# 使用 os.path.join 把 文件夹路径 和 文件名 合成一个完整的“绝对路径”
full_path = os.path.join(save_dir, 'bottle_base_si.png')
# 保存时，传入这个完整的绝对路径
plt.savefig(full_path, dpi=300, bbox_inches='tight')
print(f"图纸已成功生成！这次真的进去了: {full_path}")