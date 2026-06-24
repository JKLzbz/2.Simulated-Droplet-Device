import struct


class ProtocolParser:
    """
    纯协议解析模块（无 Qt / 无串口依赖）

    物理事实（严格遵守）：
    - 帧头：AA FF
    - 固定帧长：29 字节
    - 解包：struct.unpack('<BBfddHfB', frame)
      取 values[2] -> droplet (float)
      取 values[5] -> distance (uint16)
    """

    HEADER = b"\xAA\xFF"
    FRAME_LEN = 29
    UNPACK_FMT = "<BBfddHfB"

    def __init__(self):
        self._buf = bytearray()

    def feed_data(self, data: bytes) -> None:
        """向内部流式缓冲区追加新数据。"""
        if not data:
            return
        self._buf.extend(data)

    def parse(self):
        """
        从缓冲区中解析 1 帧（若存在）。

        - 在缓冲区中寻找 AA FF
        - 若剩余长度 >= 29，则截取 29 字节作为一帧并移出缓冲区
        - 若解包失败/帧头不匹配，则丢弃 1 字节继续寻找（抗粘包/半包/错位）

        返回：
        - (droplet, distance) 或 None
        """
        while True:
            if len(self._buf) < 2:
                return None

            idx = self._buf.find(self.HEADER)
            if idx < 0:
                # 缓冲区内没有帧头：保留最后 1 个字节（避免 AA 在边界被吞）
                if len(self._buf) > 1:
                    self._buf = self._buf[-1:]
                return None

            # 丢弃帧头前的垃圾数据
            if idx > 0:
                del self._buf[:idx]

            if len(self._buf) < self.FRAME_LEN:
                return None

            frame = bytes(self._buf[: self.FRAME_LEN])
            del self._buf[: self.FRAME_LEN]

            # 再次确认帧头（理论上一定是 AA FF）
            if frame[0:2] != self.HEADER:
                # 极端情况下（并发写/异常）兜底：丢弃 1 字节重试
                self._buf = bytearray(frame[1:]) + self._buf
                continue

            try:
                values = struct.unpack(self.UNPACK_FMT, frame)
            except struct.error:
                # 解包失败：将帧后移 1 字节再试（错位粘包时更稳）
                self._buf = bytearray(frame[1:]) + self._buf
                continue

            droplet = float(values[2])
            distance = int(values[5])
            return droplet, distance
