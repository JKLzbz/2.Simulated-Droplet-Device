"""
serial_worker.py

串口子线程：只负责“读串口 → 解析 → 更新最新值变量”，不高频 emit 信号，不直接驱动 UI 重绘。

最佳实践：
- 读写分离：线程写最新值，UI 用 QTimer 以固定频率拉取并刷新曲线
- 自动重连：串口断开/无数据时，线程内自恢复
"""

from __future__ import annotations

import time
from typing import Optional, Tuple

import serial
import serial.tools.list_ports
from PyQt6.QtCore import QMutex, QMutexLocker, QThread

from protocol_parser import ProtocolParser


def list_serial_ports() -> list[str]:
    """列出当前可用串口（COMx）。"""
    return [p.device for p in serial.tools.list_ports.comports()]


def get_ch340_port() -> Optional[str]:
    """
    复用 1209 的“自动识别 CH340”逻辑：
    找到描述中包含 CH340 的端口，优先返回。
    """
    for port in serial.tools.list_ports.comports():
        if "CH340" in (port.description or ""):
            return port.device
    return None


class SerialWorker(QThread):
    """
    串口读线程（读写分离版本）
    - latest_data: (droplet, distance)
    - latest_updated_at: 最近一次有效帧的时间戳（time.time()）
    - connected: 串口是否成功打开
    """

    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        no_data_warn_s: float = 3.0,
        no_data_reconnect_s: float = 10.0,
        parent=None,
    ):
        super().__init__(parent)
        self.port = port
        self.baudrate = baudrate
        self.no_data_warn_s = no_data_warn_s
        self.no_data_reconnect_s = no_data_reconnect_s

        self._mutex = QMutex()
        self.latest_data: Optional[Tuple[float, int]] = None
        self.latest_updated_at: float = 0.0
        self.connected: bool = False
        self.last_error: str = ""

        self._running = True
        self._parser = ProtocolParser()
        self._ser: Optional[serial.Serial] = None

    def stop(self) -> None:
        self._running = False
        try:
            if self._ser and self._ser.is_open:
                self._ser.close()
        except Exception:
            pass

    def _set_status(self, *, connected: Optional[bool] = None, error: Optional[str] = None) -> None:
        with QMutexLocker(self._mutex):
            if connected is not None:
                self.connected = connected
            if error is not None:
                self.last_error = error

    def _update_latest(self, data: Tuple[float, int]) -> None:
        with QMutexLocker(self._mutex):
            self.latest_data = data
            self.latest_updated_at = time.time()

    def snapshot(self) -> tuple[Optional[Tuple[float, int]], float, bool, str]:
        """UI 线程读取数据用：一次性拿到最新值和状态。"""
        with QMutexLocker(self._mutex):
            return self.latest_data, self.latest_updated_at, self.connected, self.last_error

    def _open_serial(self) -> bool:
        try:
            self._ser = serial.Serial(self.port, self.baudrate, timeout=0)  # 非阻塞
            self._set_status(connected=True, error="")
            return True
        except Exception as e:
            self._ser = None
            self._set_status(connected=False, error=str(e))
            return False

    def _close_serial(self) -> None:
        try:
            if self._ser and self._ser.is_open:
                self._ser.close()
        except Exception:
            pass
        self._ser = None
        self._set_status(connected=False)

    def run(self) -> None:
        last_data_t = 0.0
        last_warn_t = 0.0

        while self._running:
            if not self._ser or not self._ser.is_open:
                if not self._open_serial():
                    time.sleep(0.5)
                    continue
                # 新连接后清空解析缓冲，避免“旧残留”影响
                self._parser = ProtocolParser()
                last_data_t = 0.0
                last_warn_t = 0.0

            try:
                # 非阻塞读取：有多少读多少
                n = self._ser.in_waiting if self._ser else 0
                if n:
                    raw = self._ser.read(n)
                    self._parser.feed_data(raw)
                    last_data_t = time.time()

                    # 尽量把缓冲区里能解析的都解析掉，但不 emit，只更新 latest_data
                    while True:
                        parsed = self._parser.parse()
                        if parsed is None:
                            break
                        self._update_latest(parsed)
                else:
                    time.sleep(0.005)  # 让出时间片，避免占满 CPU

                now = time.time()
                if last_data_t and (now - last_data_t > self.no_data_warn_s) and (now - last_warn_t > self.no_data_warn_s):
                    # 只更新 error 文本，不刷屏，不弹窗
                    self._set_status(error="已连接但一段时间未收到数据")
                    last_warn_t = now

                if last_data_t and (now - last_data_t > self.no_data_reconnect_s):
                    # 长时间无数据：主动重连（常见于发送端挂死但串口还“开着”）
                    self._close_serial()
                    time.sleep(0.2)
                    continue
            except Exception as e:
                self._set_status(connected=False, error=str(e))
                self._close_serial()
                time.sleep(0.5)

        self._close_serial()

