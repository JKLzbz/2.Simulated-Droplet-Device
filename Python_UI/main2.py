import sys
import socket
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QSlider, QPushButton, QLabel, QGroupBox)
from PyQt6.QtCore import Qt
import pyqtgraph as pg  # 极其硬核的实时绘图库

# ==========================================
# ⚙️ 网络配置 (务必对齐你的 ESP32)
# ==========================================
ESP_IP = "172.20.10.3"  # 替换成 ESP32 串口打印出的实际 IP 地址
PORT = 80

class CoughSimulator(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('咳嗽飞沫发生与实时监测系统 V3.0 - 核心控制台')
        self.resize(1000, 600)
        self.setStyleSheet("background-color: #f5f6fa; font-family: 'Microsoft YaHei';")

        main_layout = QHBoxLayout()

        # ==========================================
        # 🎛️ 左侧：硬件控制台 (发送 TCP 指令)
        # ==========================================
        left_panel = QVBoxLayout()

        # --- 1. 气泵控制组 ---
        group_pump = QGroupBox("1. 气泵与调速")
        group_pump.setStyleSheet("font-weight: bold;")
        layout_pump = QVBoxLayout()
        
        self.lbl_speed = QLabel("当前气压估算: 100%")
        layout_pump.addWidget(self.lbl_speed)
        
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 1023)
        self.slider.setValue(1023)
        self.slider.valueChanged.connect(self.on_slider_change)
        layout_pump.addWidget(self.slider)

        h_pump_btns = QHBoxLayout()
        btn_pump_on = QPushButton("打开气泵")
        btn_pump_on.clicked.connect(lambda: self.send_cmd("PUMP_ON"))
        btn_pump_off = QPushButton("关闭气泵")
        btn_pump_off.clicked.connect(lambda: self.send_cmd("PUMP_OFF"))
        h_pump_btns.addWidget(btn_pump_on)
        h_pump_btns.addWidget(btn_pump_off)
        
        layout_pump.addLayout(h_pump_btns)
        group_pump.setLayout(layout_pump)
        left_panel.addWidget(group_pump)

        # --- 2. 独立测试组 ---
        group_test = QGroupBox("2. 硬件单步测试")
        group_test.setStyleSheet("font-weight: bold;")
        layout_test = QVBoxLayout()
        
        btn_valve_on = QPushButton("打开电磁阀 (释放气流)")
        btn_valve_on.clicked.connect(lambda: self.send_cmd("VALVE_ON"))
        
        btn_valve_off = QPushButton("关闭电磁阀 (气流闭锁)")
        btn_valve_off.clicked.connect(lambda: self.send_cmd("VALVE_OFF"))
        
        btn_atom = QPushButton("触发雾化板按键 (开/关)")
        btn_atom.clicked.connect(lambda: self.send_cmd("ATOM_TOGGLE"))
        
        layout_test.addWidget(btn_valve_on)
        layout_test.addWidget(btn_valve_off)
        layout_test.addWidget(btn_atom)
        group_test.setLayout(layout_test)
        left_panel.addWidget(group_test)

        # --- 3. 核心宏指令 ---
        group_macro = QGroupBox("3. 核心实验动作")
        group_macro.setStyleSheet("font-weight: bold;")
        layout_macro = QVBoxLayout()
        
        btn_perfect = QPushButton("🎯 触发完美咳嗽 (神级重叠时序)")
        btn_perfect.setStyleSheet("background-color: #27ae60; color: white; font-size: 15px; height: 50px; border-radius: 5px;")
        btn_perfect.clicked.connect(lambda: self.send_cmd("COUGH_PERFECT"))
        
        layout_macro.addWidget(btn_perfect)
        group_macro.setLayout(layout_macro)
        left_panel.addWidget(group_macro)

        # --- 4. 紧急安全全停 ---
        left_panel.addStretch()
        btn_stop = QPushButton("🛑 紧急安全全停")
        btn_stop.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold; font-size: 16px; height: 60px; border-radius: 5px;")
        btn_stop.clicked.connect(lambda: self.send_cmd("STOP"))
        left_panel.addWidget(btn_stop)


        # ==========================================
        # 📈 右侧：动态波形显示面板 (预留给 FDC2214)
        # ==========================================
        right_panel = QVBoxLayout()
        group_plot = QGroupBox("实时飞沫电容脉冲图 (FDC2214 Monitor)")
        group_plot.setStyleSheet("font-weight: bold;")
        layout_plot = QVBoxLayout()

        # 初始化 pyqtgraph 绘图组件
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground('w') # 白色背景
        self.graph_widget.setLabel('left', '电容变化量 (pF)', color='k')
        self.graph_widget.setLabel('bottom', '采样点时间轴', color='k')
        self.graph_widget.showGrid(x=True, y=True)
        
        # 预制一条蓝色线条
        self.curve = self.graph_widget.plot(pen=pg.mkPen(color='#2980b9', width=2))
        
        # 这里预留了数据数组，明天咱们用串口读取 FDC 数据后，直接往这里 append 就能出图！
        self.data_x = []
        self.data_y = []

        layout_plot.addWidget(self.graph_widget)
        group_plot.setLayout(layout_plot)
        right_panel.addWidget(group_plot)

        # === 组装左右面板 ===
        main_layout.addLayout(left_panel, stretch=1)  # 占 1 份宽度
        main_layout.addLayout(right_panel, stretch=2) # 占 2 份宽度，图表要大！
        self.setLayout(main_layout)

    # -------------------------
    # 动作与通信函数
    # -------------------------
    def on_slider_change(self):
        val = self.slider.value()
        percent = int((val / 1023) * 100)
        self.lbl_speed.setText(f"当前气压估算: {percent}%")
        self.send_cmd(f"SPEED:{val}")

    def send_cmd(self, cmd):
        """核心通信器：打开 Socket，发送指令，立刻关闭"""
        try:
            # 使用 context manager 自动管理连接和关闭
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1.0) # 设置1秒超时，防止网络卡顿导致界面死机
                s.connect((ESP_IP, PORT))
                # 加上 \r 发送，契合 ESP32 的 readStringUntil('\r')
                s.sendall((cmd + '\r').encode('utf-8'))
                print(f"[成功] -> 已发送指令: {cmd}")
        except TimeoutError:
            print(f"[错误] -> 连接 ESP32 超时！请检查单片机是否开机且连上 Wi-Fi。")
        except ConnectionRefusedError:
            print(f"[错误] -> 目标拒绝连接！IP 地址 {ESP_IP} 正确吗？")
        except Exception as e:
            print(f"[错误] -> 网络异常: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = CoughSimulator()
    ex.show()
    sys.exit(app.exec())