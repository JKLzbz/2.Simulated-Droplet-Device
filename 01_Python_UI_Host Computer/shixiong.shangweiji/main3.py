import sys
import time
from collections import deque
from typing import Optional

import serial.tools.list_ports
import pyqtgraph as pg

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QComboBox,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QGroupBox,
)

from serial_worker import SerialWorker


# ----------------------------
# 复用自 1209.py（限定范围内）
# 1) 自动扫描 COM 并添加到下拉框的逻辑
# ----------------------------
def get_ch340_port() -> Optional[str]:
    """
    扫描本机串口，优先返回描述包含 CH340 的端口号（例如 COM3）。
    注意：如果不是 CH340 设备，这里会返回 None。
    """
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "CH340" in (port.description or ""):
            return port.device
    return None


def update_serialport(combo: QComboBox, port: Optional[str]) -> None:
    """
    将检测到的端口加入下拉框并设为当前项（包含去重逻辑）。
    若 port 为 None，则不改动 items，仅保持当前选择。
    """
    if port is None:
        return

    existing_ports = [combo.itemText(i) for i in range(combo.count())]
    if port not in existing_ports:
        combo.addItem(port)
        combo.setCurrentText(port)
        return

    # 如果已存在：移除所有同名项再添加到末尾，保持“最近一次检测”在最后
    i = 0
    while i < combo.count():
        if combo.itemText(i) == port:
            combo.removeItem(i)
            continue
        i += 1
    combo.addItem(port)
    combo.setCurrentText(port)


# ----------------------------
# 复用自 1209.py（限定范围内）
# 2) pyqtgraph 图表初始化样式
# ----------------------------
def apply_1209_plot_style(plot: pg.PlotWidget, left_label: str, bottom_label: str) -> pg.PlotDataItem:
    """
    1209 风格：
    - 白色背景
    - 黑色坐标轴 + 加粗（width=2）
    - 曲线 width=2
    - 标签支持中文
    """
    plot.setBackground("w")
    plot.setLabel("left", left_label)
    plot.setLabel("bottom", bottom_label)

    axis = plot.getAxis("bottom")
    axis.setPen(pg.mkPen(width=2, color="k"))
    axis.setTextPen(pg.mkPen(color="k"))

    axis = plot.getAxis("left")
    axis.setPen(pg.mkPen(width=2, color="k"))
    axis.setTextPen(pg.mkPen(color="k"))

    curve = plot.plot(pen=pg.mkPen(pg.mkColor(255, 0, 0), width=2))
    return curve


class MainWindow(QWidget):
    """
    主线程 / UI：
    - UI 线程只做 30Hz 定时刷新（QTimer 33ms）
    - 串口读+解析全部在 SerialWorker 子线程
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("飞沫与距离监测（main3）")
        self.resize(1100, 700)

        # --- 串口控件 ---
        self.combo_port = QComboBox()
        self.combo_baud = QComboBox()
        self.combo_baud.addItems(["9600", "38400", "57600", "115200", "256000", "921600"])
        self.combo_baud.setCurrentText("115200")

        self.btn_refresh = QPushButton("刷新串口")
        self.btn_toggle = QPushButton("打开串口")
        self.btn_toggle.setCheckable(True)

        # --- 状态区 ---
        self.label_state = QLabel("NO DATA")
        self.label_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_state.setFont(QFont("微软雅黑", 12, QFont.Weight.Bold))

        self.label_age = QLabel("age: -- s")
        self.label_age.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 一个简单的“灯”
        self.label_lamp = QLabel()
        self.label_lamp.setFixedSize(18, 18)
        self.label_lamp.setStyleSheet("border-radius: 9px; background: #9e9e9e;")

        # --- 图表 ---
        self.plot_droplet = pg.PlotWidget()
        self.plot_distance = pg.PlotWidget()

        # 复用 1209 的样式初始化（白底+黑轴+2px 曲线）
        self.curve_droplet = apply_1209_plot_style(self.plot_droplet, "飞沫 droplet", "采样点")
        self.curve_distance = apply_1209_plot_style(self.plot_distance, "距离 distance", "采样点")

        # 让两图横轴对齐并固定显示窗口长度
        self.max_points = 2000
        self.plot_droplet.setXRange(0, self.max_points)
        self.plot_distance.setXRange(0, self.max_points)

        # 数据缓存（只存 UI 刷新的数据点，不存原始串口全量）
        self._x = deque(range(self.max_points), maxlen=self.max_points)
        self._droplet_y = deque([0.0] * self.max_points, maxlen=self.max_points)
        self._distance_y = deque([0.0] * self.max_points, maxlen=self.max_points)

        # --- 线程相关 ---
        self.worker: Optional[SerialWorker] = None
        self._last_ui_update_mono: Optional[float] = None

        # --- 30Hz UI 刷新定时器 ---
        self.timer = QTimer(self)
        self.timer.setInterval(33)  # ~30Hz
        self.timer.timeout.connect(self.on_timer_tick)
        self.timer.start()

        self._build_layout()
        self._bind()

        # 初次扫描串口
        self.refresh_ports()

    def _build_layout(self):
        top = QGroupBox("串口控制")
        g = QGridLayout()
        g.addWidget(QLabel("端口"), 0, 0)
        g.addWidget(self.combo_port, 0, 1)
        g.addWidget(QLabel("波特率"), 0, 2)
        g.addWidget(self.combo_baud, 0, 3)
        g.addWidget(self.btn_refresh, 0, 4)
        g.addWidget(self.btn_toggle, 0, 5)

        g.addWidget(QLabel("状态"), 1, 0)
        row_state = QHBoxLayout()
        row_state.addWidget(self.label_lamp)
        row_state.addWidget(self.label_state, 1)
        row_state.addWidget(self.label_age)
        w_state = QWidget()
        w_state.setLayout(row_state)
        g.addWidget(w_state, 1, 1, 1, 5)
        top.setLayout(g)

        plots = QGroupBox("曲线")
        v = QVBoxLayout()
        v.addWidget(self.plot_droplet, 1)
        v.addWidget(self.plot_distance, 1)
        plots.setLayout(v)

        root = QVBoxLayout()
        root.addWidget(top, 0)
        root.addWidget(plots, 1)
        self.setLayout(root)

    def _bind(self):
        self.btn_refresh.clicked.connect(self.refresh_ports)
        self.btn_toggle.toggled.connect(self.toggle_serial)

    def refresh_ports(self):
        # 先用“限定要求”里的 CH340 自动发现逻辑
        ch340 = get_ch340_port()
        update_serialport(self.combo_port, ch340)

        # 额外：把当前系统能看到的 COM 端口也填进列表（不会破坏 CH340 优先逻辑）
        ports = [p.device for p in serial.tools.list_ports.comports()]
        existing = {self.combo_port.itemText(i) for i in range(self.combo_port.count())}
        for p in ports:
            if p not in existing:
                self.combo_port.addItem(p)

        if self.combo_port.count() == 0:
            self.combo_port.addItem("COM?")

    def toggle_serial(self, on: bool):
        if on:
            port = self.combo_port.currentText().strip()
            baud = int(self.combo_baud.currentText())

            # 防止重复启动
            if self.worker is not None and self.worker.isRunning():
                self.btn_toggle.setChecked(True)
                return

            self.worker = SerialWorker(
                port=port,
                baudrate=baud,
                stall_timeout_s=1.0,
                reconnect_interval_s=1.0,
            )
            self.worker.start()

            self.btn_toggle.setText("关闭串口")
        else:
            self.btn_toggle.setText("打开串口")
            if self.worker is not None:
                self.worker.stop()
                self.worker.wait(1000)
                self.worker = None

    def _set_state(self, state: str):
        self.label_state.setText(state)
        if state == "LIVE":
            self.label_lamp.setStyleSheet("border-radius: 9px; background: #00c853;")  # 绿
        elif state == "STALL":
            self.label_lamp.setStyleSheet("border-radius: 9px; background: #ffab00;")  # 黄
        else:
            self.label_lamp.setStyleSheet("border-radius: 9px; background: #9e9e9e;")  # 灰

    def on_timer_tick(self):
        """
        30Hz 刷新：
        - 从 worker snapshot 读取最新数据（不会阻塞串口读）
        - 只把“最新点”追加进曲线缓存
        - 计算 age，并更新状态（LIVE/STALL/NO DATA）
        """
        now = time.monotonic()

        if self.worker is None:
            self._set_state("NO DATA")
            self.label_age.setText("age: -- s")
            return

        latest, last_update_mono, connected, last_rx_mono = self.worker.snapshot_latest()
        if last_update_mono is None:
            # 线程在跑但尚未解析到一帧：如果连接中但无数据就是 NO DATA
            self._set_state("NO DATA" if connected else "STALL")
            self.label_age.setText("age: -- s")
            return

        age_s = max(0.0, now - last_update_mono)
        self.label_age.setText(f"age: {age_s:.2f} s")

        # 状态判定：有数据且 age 很新 -> LIVE；否则 STALL
        if age_s <= 0.5:
            self._set_state("LIVE")
        else:
            self._set_state("STALL")

        if latest is None:
            return

        droplet, distance = latest

        # 追加一个新点（主线程节流后的数据点），不做高频重绘
        self._droplet_y.append(float(droplet))
        self._distance_y.append(float(distance))

        # 用固定长度窗口更新曲线
        self.curve_droplet.setData(list(self._x), list(self._droplet_y))
        self.curve_distance.setData(list(self._x), list(self._distance_y))

        self._last_ui_update_mono = now

    def closeEvent(self, event):
        # 窗口关闭时确保线程退出
        try:
            if self.worker is not None:
                self.worker.stop()
                self.worker.wait(1000)
        finally:
            self.worker = None
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
