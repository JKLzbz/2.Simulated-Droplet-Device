"""
serial_worker.py

监测端 串口子线程：
- 打开指定 COM 口，高波特率接收下位机数据
- read(4096) 接收，喂给 ProtocolParser（AA FF + 29字节）
- 与 WiFiWorker 接口保持完全一致
"""

from __future__ import annotations

import time
from collections import deque
from typing import Optional, Tuple

import serial
from PyQt6.QtCore import QMutex, QMutexLocker, QThread

from protocol_parser import ProtocolParser


class SerialWorker(QThread):
    """
    串口接收线程（读写分离版本）
    """

    def __init__(
        self,
        port: str,
        baudrate: int = 460800,
        no_data_warn_s: float = 86400.0,
        no_data_reconnect_s: float = 86400.0,
        parent=None,
    ):
        super().__init__(parent)
        self.port = port
        self.baudrate = baudrate
        self.no_data_warn_s = no_data_warn_s
        self.no_data_reconnect_s = no_data_reconnect_s

        self._mutex = QMutex()
        self.latest_data: Optional[Tuple[float, float, float]] = None
        self.latest_updated_at: float = 0.0
        self.data_queue: deque[Tuple[float, float, float]] = deque(maxlen=5000)
        self.connected: bool = False
        self.last_error: str = ""

        self._running = True
        self._parser = ProtocolParser()
        self._ser: Optional[serial.Serial] = None

    def stop(self) -> None:
        self._running = False
        self._close_conn()

    def snapshot(self) -> tuple[Optional[Tuple[float, float, float]], float, list[Tuple[float, float, float]], bool, str]:
        with QMutexLocker(self._mutex):
            q_data = list(self.data_queue)
            self.data_queue.clear()
            return self.latest_data, self.latest_updated_at, q_data, self.connected, self.last_error

    def status_snapshot(self) -> tuple[Optional[Tuple[float, float, float]], float, bool, str]:
        with QMutexLocker(self._mutex):
            return self.latest_data, self.latest_updated_at, self.connected, self.last_error

    def _set_status(self, *, connected: Optional[bool] = None, error: Optional[str] = None) -> None:
        with QMutexLocker(self._mutex):
            if connected is not None:
                self.connected = connected
            if error is not None:
                self.last_error = error

    def _update_latest(self, data: Tuple[float, float, float]) -> None:
        with QMutexLocker(self._mutex):
            self.latest_data = data
            self.latest_updated_at = time.time()
            self.data_queue.append(data)

    def _close_conn(self) -> None:
        try:
            if self._ser:
                self._ser.close()
        except Exception:
            pass
        self._ser = None
        self._set_status(connected=False)

    def run(self) -> None:
        last_data_t = 0.0
        last_warn_t = 0.0

        try:
            self._ser = serial.Serial(self.port, self.baudrate, timeout=0.5)
            self._set_status(connected=True, error=f"CONNECTED {self.port}@{self.baudrate}")
            self._parser = ProtocolParser()
        except Exception as e:
            self._set_status(connected=False, error=f"串口打开失败: {e}")
            return

        while self._running and self._ser and self._ser.is_open:
            try:
                waiting = self._ser.in_waiting
                chunk = self._ser.read(waiting if waiting > 0 else 1)
                if not chunk:
                    # Timeout
                    now = time.time()
                    if last_data_t and (now - last_data_t > self.no_data_warn_s) and (now - last_warn_t > self.no_data_warn_s):
                        self._set_status(error="已连接但一段时间未收到数据")
                        last_warn_t = now
                    if last_data_t and (now - last_data_t > self.no_data_reconnect_s):
                        self._set_status(error="长时间无数据，断开连接")
                        break
                    continue
                
                # 正常收到数据
                last_data_t = time.time()
                self._parser.feed_data(chunk)
                while True:
                    parsed = self._parser.parse()
                    if parsed is None:
                        break
                    self._update_latest(parsed)
            except Exception as e:
                self._set_status(connected=False, error=f"读取失败: {e}")
                break

        self._close_conn()
