from vpython import *

# === 1. 场景与单位设置 ===
# 建议使用 ISO 国际单位制（米 MKS），可视化更精准。
# 为了方便阅读，我这里使用 1000 倍率（1个单位代表 1 毫米 mm）

# 创建画布
scene = canvas(title="模拟飞沫发生装置：激光干涉原理立体可视化",
               width=1000, height=800, center=vector(0, 10, 10),
               background=color.white)

# 设置初始视角，以便更好地观察切割
scene.camera.pos = vector(60, 60, 40)
scene.camera.axis = vector(-60, -60, -40)

# === 2. 发生装置核心组件 ===

# A. 文丘里管（‘啸风’ Whirlwind）主体
# 参数：长 100mm, 半径 15mm。透明度 0.3，以便看清喷口。
venturi_body = cylinder(pos=vector(0, 0, -20),
                        axis=vector(0, 0, 100), # 沿Z轴正向延伸
                        radius=15, # 半径15mm
                        color=color.gray(0.5), opacity=0.3)

# B. 喷口（Nozzle）
# 参数：长 10mm, 半径 2mm。紧贴文丘里管前端。
nozzle = cylinder(pos=vector(0, 0, 80),
                  axis=vector(0, 0, 10), # 沿Z轴正向延伸
                  radius=2, # 半径2mm 
                  color=color.gray(0.2))

# C. FDC2214 传感器区（模拟）
# 放在喷口前方 20mm 处，作为飞沫击中的目标。
fdc_target = box(pos=vector(0, 0, 110),
                 size=vector(20, 20, 2), # 传感器板的大小
                 color=color.yellow, opacity=0.5)

# === 3. 激光系统 ===

# D. 一字线激光头（Mounted ABOVE and TILTED）
# 我推荐将其固定在文丘里管外壁上方（Z=60mm附近），镜头向下倾斜约 35°。
laser_mount = cylinder(pos=vector(0, 16, 60), # 位于文丘里管正上方，Z=60
                       axis=vector(0, 0, 5), # 挂架厚度
                       radius=3, color=color.gray(0.2))

laser_head = box(pos=vector(0, 16, 65), # 激光头主体
                 size=vector(10, 6, 15), # 激光头的大小
                 color=color.black)

# E. 一字线激光光幕（二维扇形光平面）
# 核心：必须偏折角度，使其与水平射出的飞沫气柱在空间交叉相交。
# 这里模拟一个薄至 0.2mm 的绿色光幕，偏折角度约 35°。
laser_sheet = box(pos=vector(0, 11, 88), # 光幕的中心位置
                  size=vector(0.2, 18, 30), # 极其薄（一字线特质）
                  # 偏折角度：axis 向量 (0, -0.018, 0.005) 决定了向下倾斜
                  axis=vector(0, -18, 5),
                  color=color.green, opacity=0.4, emissive=True)

# === 4. 模拟飞沫爆发（爆发核心时刻的状态） ===

# F. 飞沫气柱（Simplified Cone Plume）
# 飞沫从 2mm 喷口喷出后，会呈锥形迅速扩散。
# 我们重点可视化 FDC2214 传感器和激光光幕之间的这一小段。
# 这个圆锥表示气柱的实体轮廓。
droplet_plume = cone(pos=vector(0, 0, 90.1), # 从喷口尖端开始
                     axis=vector(0, 0, 19.8), # 向传感器延伸
                     radius=10, # 在传感器处的扩散半径（约10mm）
                     color=color.gray(0.1), opacity=0.1)

# === 5. 丁达尔效应切割界面（视觉爆闪的核心证据） ===

# 在飞沫圆锥气柱与斜向绿色光幕完美交叉相交的几何区域，
# 会产生一个极其清晰、明亮、二维的绿色散射截面。
# 它是飞沫存在的无可辩驳的光学证据。
intersection_slice = ellipsoid(pos=vector(0, 0, 88), # 与光幕中心对齐
                             size=vector(2, 6, 8), # 一个拉伸的椭圆/截面
                             color=color.green, opacity=0.7, emissive=True)

# === 6. 辅助标签与坐标系 ===

label(pos=venturi_body.pos+vector(-15, -10, 0), text='啸风 Venturi管 (R15)')
label(pos=nozzle.pos+vector(0, -5, 0), text='喷口 (R2)')
label(pos=fdc_target.pos+vector(10, 0, 0), text='FDC2214 监测区', color=color.yellow)
label(pos=laser_head.pos+vector(-10, 0, 0), text='一字线激光头\n(倾斜俯射)', color=color.green)
label(pos=intersection_slice.pos+vector(0, -15, 0),
      text='丁达尔效应切面\n无可辩驳的视觉爆闪证据', color=color.green)

# 显示一个参考坐标系
axes = [
    arrow(pos=vector(-50,0,0), axis=vector(20,0,0), color=color.red),  # X
    arrow(pos=vector(-50,0,0), axis=vector(0,20,0), color=color.green), # Y
    arrow(pos=vector(-50,0,0), axis=vector(0,0,20), color=color.blue)   # Z
]

# === 保持窗口持续运行不退出 ===
while True:
    rate(30)  # 限制刷新率至30帧/秒，防止把 CPU 跑满

# === 代码结束 ===
print("可视化已开启。浏览器会自动弹出一个交互窗口。")
print("在窗口中：鼠标右键拖动=旋转，鼠标滚轮=缩放，Shift+左键=平移。")