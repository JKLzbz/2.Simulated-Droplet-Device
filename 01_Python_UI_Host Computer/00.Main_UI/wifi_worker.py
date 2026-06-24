"""
wifi_worker.py

监测端 WiFi 子线程（TCP Server）：
- 监听指定端口，等待监测下位机连接
- recv(1024) 流式接收，喂给 ProtocolParser（AA FF + 29字节）
- 解析出 (droplet, distance) 后只更新线程安全变量 latest_data/latest_updated_at
- 绝对禁止高频 pyqtSignal 每帧 emit（UI 用 30Hz QTimer 拉取）
"""

from __future__ import annotations

import socket
import time
from collections import deque
from typing import Optional, Tuple

from PyQt6.QtCore import QMutex, QMutexLocker, QThread

from protocol_parser import ProtocolParser


class WiFiWorker(QThread):
    """
    TCP Server 接收线程（读写分离版本）
    - latest_data: (droplet, distance)
    - latest_updated_at: 最近一次有效帧的时间戳（time.time()）
    - connected: 是否已有客户端连接
    - last_error: 最近一次错误/状态信息
    """

    def __init__(
        self,
        listen_host: str = "0.0.0.0",
        listen_port: int = 8080,
        no_data_warn_s: float = 86400.0,
        no_data_reconnect_s: float = 86400.0,
        parent=None,
    ):
        super().__init__(parent)
        self.listen_host = listen_host
        self.listen_port = listen_port
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
        self._server: Optional[socket.socket] = None
        self._conn: Optional[socket.socket] = None

    def stop(self) -> None:
        self._running = False
        try:
            if self._conn:
                self._conn.close()
        except Exception:
            pass
        try:
            if self._server:
                self._server.close()
        except Exception:
            pass

    def _throttle_emit(self):
        now = time.time()
        if not hasattr(self, '_last_emit'):
            self._last_emit = 0
        if now - self._last_emit > 0.033:  # Max ~30Hz
            self._last_emit = now
            self.data_received.emit()

    def snapshot(self) -> tuple[Optional[Tuple[float, float, float]], float, list[Tuple[float, float, float]], bool, str]:
        with QMutexLocker(self._mutex):
            q_data = list(self.data_queue)
            self.data_queue.clear()
            return self.latest_data, self.latest_updated_at, q_data, self.connected, self.last_error

    def status_snapshot(self) -> tuple[Optional[Tuple[float, float, float]], float, bool, str]:
        """只读状态，绝不碰数据队列！专供 status_timer 使用。"""
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
            # deque(maxlen=1000) 会自动丢弃最旧的数据，无需手动 pop

    def _close_conn(self) -> None:
        try:
            if self._conn:
                self._conn.close()
        except Exception:
            pass
        self._conn = None
        self._set_status(connected=False)

    def run(self) -> None:
        last_data_t = 0.0
        last_warn_t = 0.0

        try:
            self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server.bind((self.listen_host, int(self.listen_port)))
            self._server.listen(1)
            self._server.settimeout(0.5)
            self._set_status(connected=False, error=f"LISTENING {self.listen_host}:{self.listen_port}")
        except Exception as e:
            self._set_status(connected=False, error=f"监听失败: {e}")
            return

        while self._running:
            # 1) 没有连接则 accept
            if not self._conn:
                try:
                    conn, addr = self._server.accept()
                    conn.settimeout(0.5)
                    self._conn = conn
                    self._parser = ProtocolParser()  # 新连接清空解析缓冲
                    last_data_t = 0.0
                    last_warn_t = 0.0
                    self._set_status(connected=True, error=f"CONNECTED {addr}")
                except socket.timeout:
                    continue
                except Exception as e:
                    self._set_status(connected=False, error=f"accept 失败: {e}")
                    time.sleep(0.2)
                    continue

            # 2) 已连接：接收数据
            try:
                timed_out = False
                try:
                    chunk = self._conn.recv(4096) if self._conn else b""
                except socket.timeout:
                    timed_out = True
                    chunk = None

                if chunk == b"":
                    # 对端断开
                    self._set_status(connected=False, error="客户端断开")
                    self._close_conn()
                    continue

                if timed_out:
                    now = time.time()
                    if last_data_t and (now - last_data_t > self.no_data_warn_s) and (now - last_warn_t > self.no_data_warn_s):
                        self._set_status(error="已连接但一段时间未收到数据")
                        last_warn_t = now
                    if last_data_t and (now - last_data_t > self.no_data_reconnect_s):
                        # 长时间无数据：断开等待重连
                        self._set_status(error="长时间无数据，等待重连...")
                        self._close_conn()
                    continue

                # 正常收到数据
                if chunk:
                    last_data_t = time.time()
                    self._parser.feed_data(chunk)
                    while True:
                        parsed = self._parser.parse()
                        if parsed is None:
                            break
                        self._update_latest(parsed)
                    # 不sleep！数据到了就立刻全部吃完，绝不拖延
            except Exception as e:
                self._set_status(connected=False, error=f"recv/parse 失败: {e}")
                self._close_conn()
                time.sleep(0.2)

        self._close_conn()
        try:
            if self._server:
                self._server.close()
        except Exception:
            pass

