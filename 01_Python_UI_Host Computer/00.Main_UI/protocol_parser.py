"""
protocol_parser.py

纯解析模块：维护流式缓冲区，负责从 TCP/串口等原始字节流中提取有效帧并解包。

协议（物理事实）：
- 帧头：0xAA 0xFF
- 帧长：13 字节
- 解包：struct.unpack('<BBfHfB', ...)
- 布局：header1(B) header2(B) droplet(f) distance(H) temp(f) checksum(B)
"""

from __future__ import annotations

import struct
from typing import Optional, Tuple


class ProtocolParser:
    FRAME_HEADER = b"\xAA\xFF"
    FRAME_LEN = 13
    _UNPACK_FMT = "<BBfHfB"
    _UNPACK_LEN = struct.calcsize(_UNPACK_FMT)  # 13

    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed_data(self, data: bytes) -> None:
        """喂入任意长度的原始字节流。"""
        if not data:
            return
        self._buffer.extend(data)

    def parse(self) -> Optional[Tuple[float, float, float]]:
        """
        尝试从缓冲区解析 1 帧。
        返回 (droplet, distance_cm, temp_celsius) 或 None
        """
        while True:
            if len(self._buffer) < self.FRAME_LEN:
                return None

            idx = self._buffer.find(self.FRAME_HEADER)
            if idx == -1:
                self._buffer[:] = self._buffer[-1:] if self._buffer[-1:] == self.FRAME_HEADER[:1] else b""
                return None

            if idx > 0:
                del self._buffer[:idx]
                if len(self._buffer) < self.FRAME_LEN:
                    return None

            frame = bytes(self._buffer[: self.FRAME_LEN])
            if frame[:2] != self.FRAME_HEADER:
                del self._buffer[:1]
                continue

            del self._buffer[: self.FRAME_LEN]

            # 按 C 结构体 #pragma pack(1) 的真实布局解包
            header1, header2, droplet, distance, temp, _checksum = struct.unpack(
                self._UNPACK_FMT, frame[: self._UNPACK_LEN]
            )
            if header1 != 0xAA or header2 != 0xFF:
                continue

            # VL53L1X 原始单位 mm → cm
            return (float(droplet), float(distance) / 10.0, float(temp))
