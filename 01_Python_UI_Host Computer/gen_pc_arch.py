import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

fig, ax = plt.subplots(figsize=(12, 14))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis('off')

def draw_box(ax, x, y, w, h, text, facecolor, edgecolor, fontsize=12):
    box = patches.FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.5,rounding_size=1',
                                 linewidth=2, edgecolor=edgecolor, facecolor=facecolor, zorder=2)
    ax.add_patch(box)
    ax.text(x + w/2, y + h/2, text, ha='center', va='center', fontsize=fontsize, fontweight='bold', color='#2c3e50', zorder=3)
    return x + w/2, y + h/2, y + h, y

layer_colors = ['#f8f9fa', '#e9ecef', '#dee2e6', '#ced4da']
layer_titles = ['[1] 通信与缓冲层', '[2] 数据预处理层', '[3] 核心算法决策层', '[4] 双轨反馈与下发层']
y_starts = [5, 25, 45, 75]
y_heights = [15, 15, 25, 20]

for i in range(4):
    rect = patches.Rectangle((5, y_starts[i]), 90, y_heights[i], linewidth=1, edgecolor='#adb5bd', facecolor=layer_colors[i], alpha=0.5, zorder=1)
    ax.add_patch(rect)
    ax.text(7, y_starts[i] + y_heights[i] - 2, layer_titles[i], fontsize=14, fontweight='bold', color='#495057', zorder=3)

# Layer 1
cx1, cy1, t1, b1 = draw_box(ax, 20, 8, 25, 8, 'TCP/IP 异步接收线程', '#d1ecf1', '#17a2b8')
cx2, cy2, t2, b2 = draw_box(ax, 55, 8, 25, 8, 'Jitter Buffer\n(抗抖动环形队列)', '#d1ecf1', '#17a2b8')
ax.annotate('', xy=(55, cy1), xytext=(45, cy1), arrowprops=dict(arrowstyle='->', lw=2, color='#6c757d'))

# Layer 2
cx3, cy3, t3, b3 = draw_box(ax, 10, 28, 22, 8, '基线漂移消除\n零偏置归一', '#d4edda', '#28a745')
cx4, cy4, t4, b4 = draw_box(ax, 38, 28, 24, 8, 'VL53L1X 空间几何补偿\n(平方反比衰减修正)', '#d4edda', '#28a745')
cx5, cy5, t5, b5 = draw_box(ax, 68, 28, 22, 8, '滑动平均平滑\n(提取宏观包络)', '#d4edda', '#28a745')
ax.annotate('', xy=(cx3, b3), xytext=(cx2, t2), arrowprops=dict(arrowstyle='->', lw=2, color='#6c757d'))
ax.annotate('', xy=(38, cy3), xytext=(32, cy3), arrowprops=dict(arrowstyle='->', lw=2, color='#6c757d'))
ax.annotate('', xy=(68, cy3), xytext=(62, cy3), arrowprops=dict(arrowstyle='->', lw=2, color='#6c757d'))

# Layer 3
cx6, cy6, t6, b6 = draw_box(ax, 10, 58, 25, 8, 'HGW 生理参数解析\n&\nGupta 曲线推演', '#fff3cd', '#ffc107')
cx7, cy7, t7, b7 = draw_box(ax, 65, 58, 25, 8, '实测波形特征提取\n(绝对幅值 & PVT锁定)', '#fff3cd', '#ffc107')
cx8, cy8, t8, b8 = draw_box(ax, 35, 48, 30, 8, 'FastDTW 动态时间规整算法\n(形态打分与绝对误差量化)', '#cce5ff', '#007bff')

ax.annotate('', xy=(cx7, b7), xytext=(cx5, t5), arrowprops=dict(arrowstyle='->', lw=2, color='#6c757d'))
ax.annotate('', xy=(35, cy8+2), xytext=(cx6, b6), arrowprops=dict(arrowstyle='->', lw=2, color='#6c757d', connectionstyle='angle,angleA=-90,angleB=180,rad=10'))
ax.annotate('', xy=(65, cy8+2), xytext=(cx7, b7), arrowprops=dict(arrowstyle='->', lw=2, color='#6c757d', connectionstyle='angle,angleA=-90,angleB=0,rad=10'))

# Layer 4
cx9, cy9, t9, b9 = draw_box(ax, 15, 80, 20, 8, '前馈定位\n气压-PVT 锁定', '#f8d7da', '#dc3545')
cx10, cy10, t10, b10 = draw_box(ax, 40, 80, 20, 8, 'SISO反馈 1\n微调 ATOM', '#f8d7da', '#dc3545')
cx11, cy11, t11, b11 = draw_box(ax, 65, 80, 20, 8, 'SISO反馈 2\n微调 BLAST', '#f8d7da', '#dc3545')
cx12, cy12, t12, b12 = draw_box(ax, 40, 70, 20, 6, '组装微秒级指令帧\n下发控制核', '#e2e3e5', '#6c757d')

ax.annotate('', xy=(cx10, b10), xytext=(cx8, t8), arrowprops=dict(arrowstyle='->', lw=2, color='#6c757d'))
ax.annotate('', xy=(cx11, b11), xytext=(cx8+10, t8), arrowprops=dict(arrowstyle='->', lw=2, color='#6c757d'))
ax.annotate('', xy=(cx12, t12), xytext=(cx10, b10), arrowprops=dict(arrowstyle='->', lw=2, color='#6c757d'))
ax.annotate('', xy=(cx12, t12), xytext=(cx11, b11), arrowprops=dict(arrowstyle='->', lw=2, color='#6c757d'))

# Final output
ax.annotate('发送至 ESP32 硬件', xy=(cx12, b12-8), xytext=(cx12, b12), arrowprops=dict(arrowstyle='->', lw=3, color='#dc3545'), fontsize=14, fontweight='bold', color='#dc3545', ha='center')

plt.title('上位机“云端”算法架构与决策反馈流程图', fontsize=20, fontweight='bold', pad=20)

out_dir = r'D:\02Projects\01Simulated-Droplet-Device\docs\研电赛\论文\论文照片'
if not os.path.exists(out_dir):
    os.makedirs(out_dir)
out_png = os.path.join(out_dir, '上位机软件架构与决策流程图_新版.png')
out_svg = os.path.join(out_dir, '上位机软件架构与决策流程图_新版.svg')

plt.savefig(out_png, dpi=300, bbox_inches='tight')
plt.savefig(out_svg, format='svg', bbox_inches='tight')
print(f'Diagram successfully saved to:\n{out_png}\n{out_svg}')
