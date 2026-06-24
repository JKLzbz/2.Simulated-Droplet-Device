import time
from typing import Optional, Tuple

import serial
from PyQt6.QtCore import QThread, QMutex, QMutexLocker

from protocol_parser import ProtocolParser


class SerialWorker(QThread):
    """
    串口子线程（读写分离：读+解析在子线程，UI 线程只拉取 latest_data）

    关键约束：
    - 绝对禁止对每一帧数据使用高频 pyqtSignal emit
    - 子线程只维护线程安全变量 latest_data / last_update_monotonic
    - 主线程用 30Hz QTimer 读取 latest_data 并刷新曲线
    """

    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        parent=None,
        stall_timeout_s: float = 1.0,
        reconnect_interval_s: float = 1.0,
        read_chunk_bytes: int = 4096,
    ):
        super().__init__(parent)
        self._port = port
        self._baudrate = baudrate
        self._stall_timeout_s = float(stall_timeout_s)
        self._reconnect_interval_s = float(reconnect_interval_s)
        self._read_chunk_bytes = int(read_chunk_bytes)

        self._parser = ProtocolParser()

        self._ser: Optional[serial.Serial] = None
        self._running = True

        self._mutex = QMutex()
        self.latest_data: Optional[Tuple[float, int]] = None
        self.last_update_monotonic: Optional[float] = None

        # 线程内部状态（用于 UI 判定 LIVE/STALL/NO DATA）
        self.connected: bool = False
        self.last_rx_monotonic: Optional[float] = None

    def update_config(self, port: str, baudrate: int):
        """在启动前或断开状态下更新串口参数。"""
        with QMutexLocker(self._mutex):
            self._port = port
            self._baudrate = int(baudrate)

    def stop(self):
        """请求线程停止并尽快释放串口。"""
        self._running = False
        self._close_serial()
        self.quit()

    def _open_serial(self) -> bool:
        try:
            self._ser = serial.Serial(
                port=self._port,
                baudrate=self._baudrate,
                timeout=0,  # 非阻塞
                write_timeout=0,
            )
            self.connected = True
            return True
        except Exception:
            self._ser = None
            self.connected = False
            return False

    def _close_serial(self):
        try:
            if self._ser is not None:
                self._ser.close()
        except Exception:
            pass
        finally:
            self._ser = None
            self.connected = False

    def _read_available(self) -> bytes:
        if self._ser is None:
            return b""
        try:
            n = self._ser.in_waiting
            if n <= 0:
                return b""
            return self._ser.read(min(n, self._read_chunk_bytes))
        except Exception:
            # 串口异常通常意味着断开
            self._close_serial()
            return b""

    def run(self):
        """
        线程主循环：
        - 自动连接/重连
        - 非阻塞读取 -> feed_data -> parse 多帧
        - 有有效帧时更新 latest_data（线程安全）
        - 断流检测：长时间无数据则主动重连
        """
        while self._running:
            if self._ser is None:
                ok = self._open_serial()
                if not ok:
                    time.sleep(self._reconnect_interval_s)
                    continue

            now = time.monotonic()
            chunk = self._read_available()
            if chunk:
                self.last_rx_monotonic = now
                self._parser.feed_data(chunk)

                # 尽可能多解析出缓冲区里的帧（抗粘包）
                while True:
                    parsed = self._parser.parse()
                    if parsed is None:
                        break
                    droplet, distance = parsed
                    with QMutexLocker(self._mutex):
                        self.latest_data = (droplet, distance)
                        self.last_update_monotonic = time.monotonic()

            # 断流检测：连接着但长期没收到任何字节 -> 认为卡死/线断，触发重连
            if self.connected and self.last_rx_monotonic is not None:
                if (now - self.last_rx_monotonic) > self._stall_timeout_s:
                    self._close_serial()
                    time.sleep(self._reconnect_interval_s)
                    continue

            # 小睡避免空转占满 CPU（关键：timeout=0 + in_waiting 轮询会非常快）
            time.sleep(0.002)

        self._close_serial()

    def snapshot_latest(self) -> Tuple[Optional[Tuple[float, int]], Optional[float], bool, Optional[float]]:
        """
        提供一个“主线程读取快照”的入口，避免 UI 直接碰内部锁结构。

        返回：
        - latest_data: (droplet, distance) 或 None
        - last_update_monotonic: 最后一次成功解析帧的时间戳（monotonic）或 None
        - connected: 当前串口是否处于打开状态
        - last_rx_monotonic: 最后一次收到任何字节的时间戳（monotonic）或 None
        """
        with QMutexLocker(self._mutex):
            return self.latest_data, self.last_update_monotonic, self.connected, self.last_rx_monotonic
