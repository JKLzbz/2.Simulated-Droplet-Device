import threading
import socket
import csv
import struct
import time
import queue
import matplotlib.pyplot as plt
import numpy as np
import warnings
warnings.filterwarnings("ignore", category=UserWarning, message="Glyph.*missing from current font")


# 共享数据和锁
data_lock = threading.Lock()
# 变量初始化定义
recv_data = []
Host_Name = "192.168.186.80"
Port = 8080
filename = 'droplet_data_1126_ceshi.csv'
flag = 0
recv_num = 0
# 全局队列用于线程间传递数据
data_queue = queue.Queue()


def save_to_csv(arr):
    with data_lock:
        with open(filename, 'a', newline='') as csvfile:
            # 创建csv.writer对象
            csv_writer = csv.writer(csvfile)
            # 将每个一维数组写入CSV文件
            csv_writer.writerow(arr)


def tcp_listener():
    global flag
    global recv_num
    # 设置为IPV4,TCP模式
    Server_Socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 端口监听
    Server_Socket.bind((Host_Name, Port))
    # 最大监听数，允许最多客户端数
    Server_Socket.listen(1)
    print("Waiting for a connection...")
    connection, address = Server_Socket.accept()
    with connection:
        print(f"Connected to {address}")
        while True:
            try:
                data = connection.recv(1024)
                if not data:
                    break
                with data_lock:
                    flag = flag + 1
                    for i in range(0, len(data), 4):
                        # 根据数据的顺序和长度，将数据进行分组解析
                        if i + 4 <= len(data):
                            float_value = struct.unpack_from('<f', data, i)[0]
                            recv_data.append(float_value)
                    if flag == 3:
                        flag = 0
                        recv_num = recv_num + 1
                        print(recv_num)  # 打印接收次数
                        # 数据存入队列
                        data_queue.put(recv_data.copy())  # 使用copy以防修改
                        recv_data.clear()  # 清空旧数据
            except Exception as e:
                print(f"Error receiving data: {e}")
                break


# 主线程：绘图和CSV写入
def plot_and_save():
    plt.ion()  # 开启交互模式
    fig, ax = plt.subplots()
    x_data = np.arange(768)
    while True:
        if not data_queue.empty():
            y_data = np.array(data_queue.get())
            ax.clear()
            ax.plot(x_data[:len(y_data)], y_data)
            ax.set_title('droplet signal')
            ax.set_xlabel('Number of Samples')
            ax.set_ylabel('Cap(unit:pF)')
            plt.draw()
            plt.pause(0.1)
            save_to_csv(y_data)
        time.sleep(0.1)  # Reduce CPU usage


if __name__ == "__main__":
    # 创建线程
    listener_thread = threading.Thread(target=tcp_listener, daemon=True)
    # 启动线程
    listener_thread.start()
    # 主线程保持运行
    try:
        # while True:
            plot_and_save()
            # time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        plt.ioff()  # 关闭交互模式
        plt.show()  # 显示最后图形
