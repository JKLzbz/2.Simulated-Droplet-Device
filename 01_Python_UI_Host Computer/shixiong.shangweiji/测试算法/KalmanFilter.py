import socket
import numpy as np
import threading
import time


# 卡尔曼滤波器实现
class KalmanFilter:
    def __init__(self, process_variance, measurement_variance, initial_estimate=0, initial_error_estimate=1):
        self.process_variance = process_variance
        self.measurement_variance = measurement_variance
        self.estimate = initial_estimate
        self.error_estimate = initial_error_estimate
        self.kalman_gain = 0

    def update(self, measurement):
        # 计算卡尔曼增益
        self.kalman_gain = self.error_estimate / (self.error_estimate + self.measurement_variance)
        # 更新估计
        self.estimate = self.estimate + self.kalman_gain * (measurement - self.estimate)
        # 更新误差估计
        self.error_estimate = (1 - self.kalman_gain) * self.error_estimate + abs(
            self.estimate - measurement) * self.process_variance
        return self.estimate


# TCP服务器处理每个客户端连接
def handle_client(client_socket):
    kalman_accel = KalmanFilter(process_variance=0.1, measurement_variance=0.5)
    kalman_gyro = KalmanFilter(process_variance=0.1, measurement_variance=0.5)

    while True:
        try:
            # 接收客户端发送的数据
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break

            # 假设数据格式是：加速度,角速度，数据用逗号分隔
            accel, gyro = map(float, data.split(','))

            # 对接收到的加速度和角速度数据进行卡尔曼滤波
            filtered_accel = kalman_accel.update(accel)
            filtered_gyro = kalman_gyro.update(gyro)

            # 输出处理后的数据
            print(f"Filtered Accel: {filtered_accel}, Filtered Gyro: {filtered_gyro}")

        except Exception as e:
            print(f"Error: {e}")
            break

    # 关闭连接
    client_socket.close()


# 设置TCP服务器
def start_server(host, port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)
    print(f"Server listening on {host}:{port}")

    while True:
        client_socket, addr = server.accept()
        print(f"Connection from {addr}")

        # 使用多线程处理每个连接
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()


# 启动服务器
if __name__ == "__main__":
    start_server('0.0.0.0', 8888)
