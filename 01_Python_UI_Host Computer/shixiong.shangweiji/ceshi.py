import sys
import numpy as np
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMainWindow
import pyqtgraph as pg

# 初始化应用
app = QApplication([])

# 创建主窗口
win = QMainWindow()
win.setWindowTitle('实时数据')

# 创建绘图小部件并设置为中央小部件
central_widget = pg.PlotWidget()
win.setCentralWidget(central_widget)

# 设置绘图背景为白色
central_widget.setBackground('w')

# 初始化数据和曲线
data = []
curve = central_widget.plot(data, pen=pg.mkPen(pg.mkColor(61, 145, 64), width=2))  # 红色，线宽为2

# 初始化正弦信号的时间和频率
t = 0  # 时间初始值
frequency = 1  # 正弦波的频率 (Hz)


# 数据更新函数
def update_data():
    global data, t
    # 每次更新时增加时间，模拟正弦波
    t += 0.005  # 每5毫秒时间增加0.005秒
    value = np.sin(2 * np.pi * frequency * t)  # 生成一个正弦波数据点
    data.append(value)  # 添加新的数据点到数据列表

    if len(data) > 2000:
        data.pop(0)  # 保持数据列表的长度为2000


# 波形更新函数
def update_plot():
    global data
    update_data()  # 更新数据
    # 对数据进行平滑
    curve.setData(data)  # 更新曲线数据

# 创建定时器，每5ms更新数据
data_timer = QTimer()
data_timer.timeout.connect(update_data)
data_timer.start(5)  # 每5毫秒更新一次数据

# 创建定时器，每100ms更新图形显示
plot_timer = QTimer()
plot_timer.timeout.connect(update_plot)
plot_timer.start(5)  # 每100毫秒更新一次图形

# 显示主窗口
win.show()

# 运行应用
sys.exit(app.exec())
