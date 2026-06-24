"""
esp32_controller.py

发生端控制模块：
- 负责向 ESP32 发送 TCP 短连接控制指令
- 与 UI 解耦，UI 只调用 send_cmd()
"""

from __future__ import annotations

import socket


class Esp32Controller:
    def __init__(self, ip: str = "172.20.10.2", port: int = 80, timeout_s: float = 1.0):
        self.ip = ip
        self.port = port
        self.timeout_s = timeout_s

    def send_cmd(self, cmd: str) -> tuple[bool, str]:
        """
        发送控制指令给 ESP32。使用短连接，避免界面被网络阻塞。

        返回 (ok, message) 便于 UI 提示。
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(self.timeout_s)
                s.connect((self.ip, self.port))
                # 帧头 '$' + 指令 + 帧尾 '#'，防止噪声/粘包误触发
                s.sendall(("$" + cmd + "#\r").encode("utf-8"))
            return True, "OK"
        except Exception as e:
            return False, str(e)
