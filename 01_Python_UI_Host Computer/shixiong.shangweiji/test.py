import socket
import struct
import time
import numpy as np
from threading import Thread


class TestClient:
    def __init__(self, server_ip: str, server_port: int):
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_socket = None
        self.running = False
        self.send_thread = None

    @staticmethod
    def calculate_checksum(data: bytes) -> int:
        return sum(data) & 0xFF

    def pack_test_data(self) -> bytes:
        # 模拟测试数据
        header = struct.pack('BB', 0xAA, 0xFF)  # 帧头
        # 模拟传感器数据
        droplet = struct.pack('f', np.sin(time.time()))  # 使用正弦波模拟液滴数据
        distance = struct.pack('H', int(np.random.uniform(0, 4000)))  # 距离
        acc = struct.pack('d', np.random.uniform(5, 25))  # 加速度
        gyro = struct.pack('d', np.random.uniform(0, 10))  # 陀螺仪
        temp = struct.pack('f', np.random.uniform(36, 37))  # 温度
        # 组合所有数据
        data = header + droplet + distance + acc + gyro + temp
        # 计算校验和
        checksum = struct.pack('B', self.calculate_checksum(data))
        print(len(data + checksum))
        return data + checksum

    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_ip, self.server_port))
            print(f"已连接到服务器 {self.server_ip}:{self.server_port}")
            self.running = True
            self.send_thread = Thread(target=self.send_data)
            self.send_thread.start()
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            return False

    def send_data(self):
        while self.running:
            try:
                data = self.pack_test_data()
                self.client_socket.send(data)
                time.sleep(0.005)  # 每100ms发送一次数据
            except Exception as e:
                print(f"发送数据失败: {e}")
                break
        self.disconnect()

    def disconnect(self):
        self.running = False
        if self.client_socket:
            self.client_socket.close()
        if self.send_thread and self.send_thread.is_alive():
            self.send_thread.join()
        print("已断开连接")


# 使用示例
if __name__ == "__main__":
    client = TestClient("192.168.152.80", 8080)
    try:
        if client.connect():
            # 运行60秒后断开
            time.sleep(600)
    finally:
        client.disconnect()
