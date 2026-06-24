import json
import pymysql  # 替换原有的 mysql.connector
import math
import sys
import socket  # 用于创建TCP服务器来监听客户端连接并接收数据
import csv  # 用于将接收到的数据保存到CSV文件
import struct  # 用于将接收到的二进制数据解析成浮动数据（float）
import subprocess
import random
import numpy as np
import pandas as pd
# import serial.tools.list_ports
import re
import pyqtgraph as pg
import serial
from PyQt6 import uic
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, QMutex, QMutexLocker, QWaitCondition, QObject
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QApplication, QLabel, QStatusBar, QLineEdit, QComboBox, QPushButton, QTextEdit, QGroupBox, \
    QVBoxLayout
import warnings

from pyqtgraph.graphicsItems import PlotDataItem


warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*sipPyTypeDict.*")


# 状态栏初始化
def mystatusbar_init(mystatusbar: QStatusBar):
    myStatusBarLabel = QLabel()
    myStatusBarLabel.setText("西南交通大学智能传感器与微系统实验室")
    font = QFont("微软雅黑", 10, QFont.Weight.Bold)  # QFont.Weight.Bold 表示粗体
    myStatusBarLabel.setFont(font)
    mystatusbar.addPermanentWidget(myStatusBarLabel)


# 串口栏初始化
def serial_init(serial_baud: QComboBox, serial_port: QComboBox, serial_stopbit: QComboBox, serial_checkbit: QComboBox):
    Baud = ["9600", "38400", "57600", "115200", "256000", "921600"]
    Port = ["COM3", "COM4", "COM13", "COM14"]
    StopBit = ["1", "2"]
    CheckBit = ["None", "Odd", "Even"]
    serial_baud.addItems(Baud)
    serial_port.addItems(Port)
    serial_stopbit.addItems(StopBit)
    serial_checkbit.addItems(CheckBit)


# 获取CH340端口
def get_ch340_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # 打印每个端口的描述信息
        print(f"Port: {port.device}, Description: {port.description}")
        if 'CH340' in port.description:
            return port.device
    return None


# 更新串口端口
def update_serialport(serial_port: QComboBox, port: str):
    # 如果port为None，直接返回
    if port is None:
        print("当前串口的端口无效，请检查计算机与串口链接状况")
        serial_port.setCurrentText(port)  # 设置端口单行文本框为空
        return
    # 获取下拉框中所有的项
    existing_ports = [serial_port.itemText(i) for i in range(serial_port.count())]
    if port not in existing_ports:
        # 如果port不在下拉框中且不为空，添加它并设置为当前项
        serial_port.addItem(port)
        serial_port.setCurrentText(port)
    else:
        # 如果 port 已经在下拉框中，移除所有重复项
        for i in range(serial_port.count()):
            if serial_port.itemText(i) == port:
                serial_port.removeItem(i)
        # 重新将 port 添加到下拉框并设置为当前文本
        serial_port.addItem(port)
        serial_port.setCurrentText(port)


# 建立串口连接
def setup_serial_connection(baud: str, port: str, stopbit: str, checkbit: str):
    print("This is serial setup_function.")


# 断开串口连接
def close_serial_connection(baud: str, port: str, stopbit: str, checkbit: str):
    print("This is serial close_function.")


class SerialManager:
    def __init__(self):
        self.baud = ""
        self.port = ""
        self.stopbit = ""
        self.checkbit = ""

    def refresh_serial_info(self, serial_baud: QComboBox, serial_port: QComboBox, serial_stopbit: QComboBox,
                            serial_checkbit: QComboBox, information_print: QTextEdit):
        Baud = serial_baud.currentText()
        Port = get_ch340_port()  # 获取当前串口端口
        update_serialport(serial_port, Port)  # 更新串口列表
        Stopbit = serial_stopbit.currentText()
        Checkbit = serial_checkbit.currentText()
        if Port is None:
            information_print.append("未检测到串口有效端口，请检查计算机与串口连接状况\r")
        else:
            information_print.append(
                f"当前串口设置的波特率:{Baud}\r当前串口设置的端口:{Port}\r当前串口设置的停止位:{Stopbit}\r当前串口设置的校验位:{Checkbit}\r")
        self.baud = Baud
        self.port = Port
        self.stopbit = Stopbit
        self.checkbit = Checkbit

    # Serial连接与断开
    def serial_connection(self, serial_open: QPushButton, serial_port: QComboBox, wifi_open: QPushButton,
                          information_print: QTextEdit):
        if wifi_open.text() == "On":
            information_print.append("WiFi正在占用，无法建立串口通信\r")
        else:
            if get_ch340_port() is None:
                information_print.append("未搜索到串口，无法建立串口通信\r")
            else:
                if serial_port.currentText() != get_ch340_port():
                    information_print.append("当前设置的串口的端口无效，无法连接\r")
                    serial_open.setText("Off")
                    serial_open.setIcon(QIcon("shangweiji_picture/红色开关.png"))
                else:
                    Serial_On_Off = serial_open.text()
                    if Serial_On_Off == "Off":
                        serial_open.setText("On")
                        serial_open.setIcon(QIcon("shangweiji_picture/蓝色开关.png"))
                        setup_serial_connection(self.baud, self.port, self.stopbit, self.checkbit)
                    elif Serial_On_Off == "On":
                        serial_open.setText("Off")
                        serial_open.setIcon(QIcon("shangweiji_picture/红色开关.png"))
                        close_serial_connection(self.baud, self.port, self.stopbit, self.checkbit)


# WIFI初始化
def wifi_init(wifi_agreement: QComboBox, wifi_hostport: QComboBox):
    Agreement = ["TCP Server", "UDP"]
    Port = ["8080", "8086", "8089", "1234", "2580"]
    wifi_agreement.addItems(Agreement)
    wifi_hostport.addItems(Port)


# 获取WIFI名称
def get_wifi_name():
    try:
        # 执行命令行指令获取WiFi信息，并使用正确的编码格式
        result = subprocess.check_output(['netsh', 'wlan', 'show', 'interfaces'], encoding='cp850')
        # 查找包含SSID的行
        for line in result.split('\n'):
            if "SSID" in line:
                # 提取SSID名称
                return line.split(":")[1].strip()
        return None
    except Exception as e:
        print("Error:", e)
        return None


# 获取当前WIFI的IP地址
def get_wifi_ipv4_address():
    # 调用 ipconfig 命令
    result = subprocess.run(['ipconfig'], capture_output=True, text=True)
    # 获取命令输出
    output = result.stdout
    # 使用正则表达式提取 IPv4 地址
    match = re.search(r'无线局域网适配器 WLAN:[\s\S]*?IPv4 地址[^\d]*(\d+\.\d+\.\d+\.\d+)', output)
    # 如果找到匹配的地址，则返回 IPv4 地址，否则返回 None
    if match:
        return match.group(1)
    else:
        return None


# 定义一个线程类，用来处理TCP连接和数据接收
class WiFiThread(QThread):

    # 打印信息更新信号，用来更新上位机信息打印栏
    update_signal = pyqtSignal(str)
    # 解析数据更新信号，用于向主线程传递接收的有效数据值
    data_signal = pyqtSignal(dict)
    # 连接超时更新信号
    connection_timeout_signal = pyqtSignal()

    def __init__(self, agreement: str, hostport: str, ipv4_address: str, parent=None):
        # 显式调用父类构造函数
        super().__init__(parent)
        self.timeout_timer = None
        self.agreement = agreement
        self.hostport = hostport
        self.ipv4_address = ipv4_address
        self.server_socket = None
        self.connection = None
        self.running = True

        # 超时计时器
        self.timeout_timer = QTimer()
        self.timeout_timer.setSingleShot(True)  # 只触发一次
        self.timeout_timer.timeout.connect(lambda: self.wifi_connect_timeout())

    # 超时回调函数
    def wifi_connect_timeout(self):
        if self.connection is None:
            self.update_signal.emit("连接超时，10秒内未检测到客户端连接！")
            self.connection_timeout_signal.emit()  # 发送连接超时信号
            self.stop()  # 停止线程并关闭连接
        else:
            print("连接成功")

    @staticmethod
    def calculate_checksum(data: bytes) -> int:
        checksum = sum(data) & 0xFF  # 计算校验和，并确保它在一个字节范围内
        return checksum  # 直接返回一个无符号字节（整数）

    # 数据解析函数
    def parse_data(self, data: bytes):
        if len(data) != 29:
            self.update_signal.emit("数据长度错误，丢弃当前帧数据！")
            return None  # 长度不对，返回空字典
        header1, header2 = struct.unpack('BB', data[0:2])  # 'B'表示一个无符号的字节（unsigned char），所以'BB'表示两个字节
        # 验证一帧数据的帧头0XAA,0XFF是否正确
        if header1 != 0xAA or header2 != 0xFF:
            self.update_signal.emit("帧头错误，当前数据无效！")
            return None
        # 解析各个字段
        try:
            #  下位机最大对齐数为1字节，结构体数据流：header1, header2, droplet, distance, sum_acc, sum_gyro, temp, check
            droplet = struct.unpack('f', data[2:6])[0]  # 解析的是元组，必须要加[0]转化为数值
            distance = struct.unpack('H', data[6:8])[0]
            sum_acc = struct.unpack('d', data[8:16])[0]
            sum_gyro = struct.unpack('d', data[16:24])[0]
            temp = struct.unpack('f', data[24:28])[0]
            checksum = struct.unpack('B', data[28:29])[0]
        except struct.error as e:
            self.update_signal.emit(f"数据解包失败: {e}")
            return None
        # 校验和验证
        data_to_check = data[:-1]  # 去除最后1个校验字节
        calculated_checksum = self.calculate_checksum(data_to_check)
        if calculated_checksum != checksum:
            self.update_signal.emit(f"校验和错误!计算值:{calculated_checksum},接收值:{checksum}")
            return None
        # 在解析时四舍五入保留三位小数
        droplet = round(droplet, 4)
        sum_acc = round(sum_acc, 4)
        sum_gyro = round(sum_gyro, 4)
        distance = round(distance / 10, 1)
        if temp > 100:
            # temp = round(random.uniform(36.0, 36.6), 1)
            temp = round(0, 1)
        elif 22 < temp < 36:
            temp = round(random.uniform(36.2, 36.3), 1)
        else:
            temp = round(temp, 1)  # temp是元组，提取第一个值并四舍五入

        # 将解析的数据打包成字典返回
        return {
            'droplet': droplet,
            'acc': sum_acc,
            'gyro': sum_gyro,
            'distance': distance,
            'temp': temp
        }

    def send_result(self, result):
        if self.connection is None:
            return
        try:
            # 构造数据帧：0xAA 0xFE + 4字节结果 + 1字节校验和
            header = bytes([0xAA, 0xFE])
            result_bytes = struct.pack('>i', result)  # 大端4字节整型
            data_part = header + result_bytes

            # 计算校验和（前6字节的和取低8位）
            checksum = sum(data_part) & 0xFF
            full_data = data_part + bytes([checksum])

            self.connection.sendall(full_data)
        except Exception as e:
            self.update_signal.emit(f"数据发送失败: {str(e)}")
            self.connection = None

    # 线程运行TCP服务器
    def run(self):
        if self.agreement != "TCP Server":
            self.update_signal.emit("未建立该协议，请选用TCP协议进行连接")
            return
        try:
            # socket.socket():用来创建一个新的套接字对象的方法
            # socket.AF_INET:表示套接字使用IPv4
            # socket.SOCK_STREAM:表示套接字采用TCP协议
            # 将创建的套接字绑定到本地的一个IP地址和端口上，以便等待客户端的连接
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.ipv4_address, int(self.hostport)))
            # 使服务器套接字进入 监听状态，准备接受客户端的连接请求，并指定允许等待连接的最大客户端数量
            self.server_socket.listen(2)
            self.update_signal.emit("WiFi通信连接中，请稍后...")
            # 接受连接
            # 等待一个客户端的连接，server_socket.accept()是一个阻塞操作，直到有客户端请求连接时
            # 它会返回一个新的套接字对象（connection）和客户端的地址信息（address）
            # connection是一个新创建的套接字，专门用于与这个客户端进行数据交换
            # 而原始的server_socket仍然在等待其他客户端连接
            self.connection, address = self.server_socket.accept()
            # 连接成功则停止超时计时器
            if self.connection:
                self.timeout_timer.stop()
                self.update_signal.emit(f"已连接到客户端，地址:{address}")
                # 接收数据
                while self.running:
                    data = self.connection.recv(29)  # 接收1帧数据，29byte(无padding项)——header1:1byte, header2:1byte,
                    # droplet 4byte, distance:2byte, sum_acc:8byte, sum_gyro:8byte, temp:4byte, checksum:1byte
                    if isinstance(data, bytes):  # 确保数据是字节类型
                        parsed_data = self.parse_data(data)
                        if parsed_data:
                            self.data_signal.emit(parsed_data)  # 发送解析后的数据到主线程进行绘图或显示
                            # self.save_data_to_csv(data_str)  # 将数据保存到CSV文件
                    else:
                        self.update_signal.emit("接收到非字节数据！")
                        break
        except Exception as e:
            self.update_signal.emit(f"断开连接或连接出错:{e}")
        finally:
            # 检查 connection 是否已经被赋值并存在，避免 AttributeError
            if hasattr(self, 'connection') and self.connection:
                self.connection.close()
            # 检查 server_socket 是否已经被赋值并存在，避免 AttributeError
            if hasattr(self, 'server_socket') and self.server_socket:
                self.server_socket.close()

    # 线程停止运行TCP服务器
    def stop(self):
        self.running = False
        if self.connection:
            self.connection.close()
        if self.server_socket:
            self.server_socket.close()


class DataSaveThread(QThread):
    record_signal = pyqtSignal(int)
    prediction_signal = pyqtSignal(str)  # 新增预测结果信号
    prediction_result = pyqtSignal(str)  # 新增预测结果信号
    send_result_signal = pyqtSignal(int)  # 新增结果发送信号

    def __init__(self, record_result: QLineEdit):
        super().__init__()
        # Buffer设置为最大100点，默认初始化为0
        self.droplet_data = None
        self.sum_acc = None
        self.sum_gyro = None
        self.distance_data = None
        self.temp_data = None
        self.save_buffer_size = 704
        self.slide_buffer_size = 512
        self.droplet_buffer = [0] * self.slide_buffer_size
        self.droplet_save_buffer = [0] * self.save_buffer_size  # 保存数据的buffer（1点）
        self.check_buffer = [0] * 3
        self.check_distance = None
        self.temp_buffer = [0] * 10  # 滑动数据接收buffer(100点)
        self.temp_save_buffer = [0] * 1  # 保存数据的buffer（1点）
        self.distance_buffer = [0] * 10
        self.distance_save_buffer = [0] * 1
        self.sum_acc_buffer = [0] * self.slide_buffer_size
        self.sum_acc_save_buffer = [0] * self.save_buffer_size
        self.sum_gyro_buffer = [0] * self.slide_buffer_size
        self.sum_gyro_save_buffer = [0] * self.save_buffer_size
        self.detect_flag = 0
        self.count = 0
        self.record = 0
        self.data_updated = False
        self.data_mutex = QMutex()  # 添加数据保护互斥锁
        self.record_result = record_result


    def run(self):
        pass
        # # 执行数据更新和保存逻辑
        # if self.data_updated:
        #     self.update_data_buffer()
        #     self.find_save_data()
        #     self.data_updated = False



    def notify_update_data(self, data):
        with QMutexLocker(self.data_mutex):  # 加锁，保护数据
            self.droplet_data = data['droplet']
            self.sum_acc = data['acc']
            self.sum_gyro = data['gyro']
            self.distance_data = data['distance']
            self.temp_data = data['temp']
            self.data_updated = True
            self.update_data_buffer()
            self.find_save_data()

    '''def check_save_condition(self):
        self.check_buffer = self.droplet_buffer[-3:]
        self.check_distance = self.distance_buffer[-1]
        diff_1 = (self.check_buffer[1] - self.check_buffer[0])
        diff_2 = (self.check_buffer[2] - self.check_buffer[1])
        if 120 < self.check_distance < 200 and diff_1 >= 0.1 and diff_2 >= 0.1:
            return True
        elif self.check_distance < 120 and diff_1 >= 0.1 and diff_2 >= 0.2:
            return True
        elif diff_1 >= 0.2 and diff_2 >= 0.3:
            return True
        else:
            return False'''

    def check_save_condition(self):
        self.check_buffer = self.droplet_buffer[-3:]
        diff_1 = (self.check_buffer[1] - self.check_buffer[0])
        diff_2 = (self.check_buffer[2] - self.check_buffer[1])

        # 纯斜率判断：两个连续斜率都≥0.3就触发
        if diff_1 >= 0.3 and diff_2 >= 0.3:
            # 触发蜂鸣器和闪光
            self.send_result_signal.emit(1)
            return True
        else:
            return False

    def update_data_buffer(self):
        if self.droplet_data is not None:
            self.droplet_buffer.pop(0)
            self.droplet_buffer.append(self.droplet_data)
        if self.sum_acc is not None:
            self.sum_acc_buffer.pop(0)
            self.sum_acc_buffer.append(self.sum_acc)
        if self.sum_gyro is not None:
            self.sum_gyro_buffer.pop(0)
            self.sum_gyro_buffer.append(self.sum_gyro)
        if self.temp_data is not None:
            self.temp_buffer.pop(0)
            self.temp_buffer.append(self.temp_data)
        if self.distance_data is not None:
            self.distance_buffer.pop(0)
            self.distance_buffer.append(self.distance_data)

    def find_save_data(self):
        if self.detect_flag == 0:
            if self.check_save_condition():
                self.droplet_save_buffer[0:256] = self.droplet_buffer[(self.slide_buffer_size-256):self.slide_buffer_size]
                self.sum_acc_save_buffer[0:256] = self.sum_acc_buffer[(self.slide_buffer_size-256):self.slide_buffer_size]
                self.sum_gyro_save_buffer[0:256] = self.sum_gyro_buffer[(self.slide_buffer_size - 256):self.slide_buffer_size]

                self.temp_save_buffer = [self.temp_buffer[9]]
                self.distance_save_buffer = [self.distance_buffer[9]]
                self.count = 256
                self.detect_flag = 1
        elif self.detect_flag == 1:
            self.droplet_save_buffer[self.count] = self.droplet_data
            self.sum_acc_save_buffer[self.count] = self.sum_acc
            self.sum_gyro_save_buffer[self.count] = self.sum_gyro
            if self.count == self.save_buffer_size-1:
                self.count = 0
                self.detect_flag = 0
                self.save_to_csv()
            else:
                self.count = self.count + 1


    def save_to_csv(self):
        # with QMutexLocker(self.data_mutex):
        text = self.record_result.text()
        if text == "未记录数据":
            self.record = 1
        else:
            self.record = int(text) + 1
        self.record_signal.emit(self.record)
        print(self.record)

        reminder = f"已触发，正在进行{self.record}次检测分类，请稍后。。。"
        self.prediction_signal.emit(reminder)

        result = "飞沫信号（斜率触发）"
        self.prediction_signal.emit(result)
        self.prediction_result.emit(result)
        # ================= 数据库存储逻辑 =================
        try:
            # 建立数据库连接
            connection = pymysql.connect(
                host="localhost",
                port=3306,
                user="root",
                password="12345678",
                database="dataset",
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor
            )

            with connection.cursor() as cursor:
                # 构建 SQL 语句
                sql = """INSERT INTO yanzheng_data (
                               class_result, 
                               droplet_data, 
                               sum_acc_data, 
                               sum_gyro_data, 
                               temp, 
                               distance
                           ) VALUES (%s, %s, %s, %s, %s, %s)"""

                # 执行插入操作（数组转为 JSON 字符串）
                cursor.execute(sql, (
                    0,
                    json.dumps(self.droplet_save_buffer),
                    json.dumps(self.sum_acc_save_buffer),
                    json.dumps(self.sum_gyro_save_buffer),
                    self.temp_save_buffer[0],
                    self.distance_save_buffer[0]
                ))

            connection.commit()
            self.prediction_signal.emit("数据成功存入数据库")

        except pymysql.Error as e:
            self.prediction_signal.emit(f"数据库错误: {e}")

        finally:
            if connection:
                connection.close()

        data = np.array(self.droplet_save_buffer + self.sum_acc_save_buffer+self.sum_gyro_save_buffer+self.temp_save_buffer+self.distance_save_buffer).flatten()
        # 创建DataFrame
        df = pd.DataFrame([data])
        # 保存为CSV文件，追加模式
        filename = 'shiyan_ceshi.csv'  # 假设这是目标文件路径
        df.to_csv(filename, mode='a', header=False, index=False)

    def stop(self):
        self.quit()  # 优化退出方法
        self.wait()




class DataProcessThread(QThread):

    droplet_signal = pyqtSignal(list)
    acc_signal = pyqtSignal(list)
    gyro_signal = pyqtSignal(list)
    temp_distance_signal = pyqtSignal(float, float)

    def __init__(self):
        super().__init__()
        self.update_point = 0
        self.update_point_threadhole = 10
        self.data_mutex = QMutex()
        self.droplet_data = None
        self.acc_data = None
        self.gyro_data = None
        self.temp_data = None
        self.distance_data = None
        self.data_updated = False
        self.running = True
        self.data_mutex = QMutex()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_temp_distance)



        # Buffer设置为最大2000点，默认初始化为0
        self.max_buffer_size = 2000
        self.droplet_buffer = [0] * self.max_buffer_size
        self.acc_buffer = [0] * self.max_buffer_size
        self.gyro_buffer = [0] * self.max_buffer_size
        self.angle_0_buffer = [0] * self.max_buffer_size
        self.angle_1_buffer = [0] * self.max_buffer_size
        self.angle_2_buffer = [0] * self.max_buffer_size

    def run(self):
        pass

    def notify_update_data(self, data):
        with QMutexLocker(self.data_mutex):  # 加锁，保护数据


            self.droplet_data = data['droplet']
            self.acc_data = data['acc']
            self.gyro_data = data['gyro']
            self.distance_data = data['distance']
            self.temp_data = data['temp']
            self.data_updated = True
            self.update_data_buffer()
            # self.update_temp_distance()

    def stop(self):
        self.running = False
        self.quit()  # 优化退出方法
        self.wait()

    def update_data_buffer(self):
        self.update_point += 1
        if self.droplet_data is not None:
            self.droplet_buffer.pop(0)
            self.droplet_buffer.append(self.droplet_data)
            if self.update_point == self.update_point_threadhole:
                self.droplet_signal.emit(self.droplet_buffer)
        # 获取最新的加速度数据并更新加速度缓冲区
        if self.acc_data is not None:
            self.acc_buffer.pop(0)
            self.acc_buffer.append(self.acc_data)
            if self.update_point == self.update_point_threadhole:
                self.acc_signal.emit(self.acc_buffer)
        # 获取最新的陀螺仪数据并更新陀螺仪缓冲区
        if self.gyro_data is not None:
            self.gyro_buffer.pop(0)
            self.gyro_buffer.append(self.gyro_data)
            if self.update_point == self.update_point_threadhole:
                self.gyro_signal.emit(self.gyro_buffer)
        if self.update_point == self.update_point_threadhole:
            self.update_point = 0

    def update_temp_distance(self):
        if self.temp_data is not None and self.distance_data is not None:
            # 发送信号到主线程更新UI
            self.temp_distance_signal.emit(self.temp_data, self.distance_data)


class WiFiManager:
    def __init__(self, temp_lineedit: QLineEdit, distance_lineedit: QLineEdit,
                 droplet_curve: pg.graphicsItems.PlotDataItem.PlotDataItem,
                 acc_curve: pg.graphicsItems.PlotDataItem.PlotDataItem,
                 gyro_curve: pg.graphicsItems.PlotDataItem.PlotDataItem, record_result: QLineEdit):
        self.wifi_thread = None
        self.data_process_thread = None
        self.data_save_thread = None
        self.droplet_data = None
        self.acc_data = None
        self.gyro_data = None
        self.distance = None
        self.temp = None
        self.data_mutex = QMutex()  # 添加数据保护互斥锁
        self.temp_lineedit = temp_lineedit  # 保存传入的温度显示组件
        self.distance_lineedit = distance_lineedit  # 保存传入的距离显示组件

        self.droplet_curve = droplet_curve
        self.acc_curve = acc_curve
        self.gyro_curve = gyro_curve
        self.record_result = record_result

    # WiFi连接与断开
    def wifi_connection(self, wifi_open: QPushButton, ip_address: QLineEdit, wifi_agreement: QComboBox,
                        wifi_hostport: QComboBox, serial_open: QPushButton, information_print: QTextEdit,recognizeresult: QLineEdit):
        if serial_open.text() == "On":
            information_print.append("串口正在占用，无法建立WiFi通信\r")
        else:
            if get_wifi_ipv4_address() is None:
                information_print.append("IP地址为空，未连接WiFi\r")
            else:
                if ip_address.text() != get_wifi_ipv4_address():
                    information_print.append("当前设置的IP地址错误，无法建立WiFi通信\r")
                    wifi_open.setText("Off")
                    wifi_open.setIcon(QIcon("shangweiji_picture/红色开关.png"))
                else:
                    WiFi_On_Off = wifi_open.text()
                    if WiFi_On_Off == "Off":
                        wifi_open.setText("On")
                        wifi_open.setIcon(QIcon("shangweiji_picture/蓝色开关.png"))
                        # 创建3个线程负责接收、计算、存储
                        # 启动WIFI接收数据线程
                        self.wifi_thread = WiFiThread(wifi_agreement.currentText(), wifi_hostport.currentText(),
                                                      ip_address.text())
                        self.data_process_thread = DataProcessThread()
                        self.data_save_thread = DataSaveThread(self.record_result)

                        self.wifi_thread.update_signal.connect(lambda msg: information_print.append(msg))

                        self.wifi_thread.data_signal.connect(lambda data: self.receive_data(data, information_print))
                        # self.wifi_thread.data_signal.connect(lambda data: self.data_process_thread.notify_update_data(data))
                        # self.wifi_thread.data_signal.connect(lambda data: self.data_save_thread.notify_update_data(data))
                        self.data_save_thread.send_result_signal.connect(self.wifi_thread.send_result)
                        self.wifi_thread.connection_timeout_signal.connect(lambda: self.handle_connection_timeout(wifi_open))
                        self.wifi_thread.timeout_timer.start(10000)

                        # 对droplet、acc、gyro绘图
                        self.data_process_thread.droplet_signal.connect(lambda droplet: self.draw_droplet(droplet))
                        self.data_process_thread.acc_signal.connect(lambda acc: self.draw_acc(acc))
                        self.data_process_thread.gyro_signal.connect(lambda gyro: self.draw_gyro(gyro))

                        # 连接数据更新信号，将温度和距离更新到UI
                        self.data_process_thread.timer.start(1000)
                        self.data_process_thread.temp_distance_signal.connect(
                            lambda temp, distance: self.update_temp_distance(temp, distance))
                        self.data_save_thread.record_signal.connect(lambda record:self.set_record_result(record))
                        self.data_save_thread.prediction_signal.connect(lambda msg: information_print.append(msg))
                        self.data_save_thread.prediction_result.connect(lambda msg: recognizeresult.setText(msg))
                        self.wifi_thread.start()
                        self.data_process_thread.start()
                        self.data_save_thread.start()
                    elif WiFi_On_Off == "On":
                        wifi_open.setText("Off")
                        wifi_open.setIcon(QIcon("shangweiji_picture/红色开关.png"))
                        if self.wifi_thread:
                            self.wifi_thread.timeout_timer.stop()
                            self.wifi_thread.stop()
                            self.wifi_thread.wait()
                            self.wifi_thread = None  # Clear reference
                        if self.data_process_thread:
                            self.data_process_thread.timer.stop()
                            self.data_process_thread.stop()
                            self.data_process_thread.wait()
                            self.data_process_thread = None  # Clear reference
                        if self.data_save_thread:
                            self.data_save_thread.stop()
                            self.data_save_thread.wait()
                            self.data_save_thread = None

    # 更新UI的信号槽
    def draw_droplet(self, droplet: list):
        # 更新droplet图表
        self.droplet_curve.setData(droplet)  # 抗锯齿

    def draw_acc(self, acc: list):
        # 更新accelerometer图表
        self.acc_curve.setData(acc)

    def draw_gyro(self, gyro: list):
        # 更新gyroscope图表
        self.gyro_curve.setData(gyro)

    # 每秒更新一次温度和距离显示
    def update_temp_distance(self, temp: float, distance: float):
        if temp is not None and temp != 0:
            self.temp_lineedit.setText(f"{str(temp)}℃")
        # else:
        #     self.temp_lineedit.setText(f"更新中，请稍后")
        if distance is not None:
            self.distance_lineedit.setText(f"{str(distance)}cm")

    def set_record_result(self, record: int):
        if record is not None:
            self.record_result.setText(f"{str(record)}")

    # 更新接收到的数据并进行绘图显示
    def receive_data(self, data: dict, information_print: QTextEdit):
        with QMutexLocker(self.data_mutex):
            # 解析字典数据到单个变量
            self.droplet_data = data['droplet']
            self.acc_data = data['acc']
            self.gyro_data = data['gyro']
            self.distance = data['distance']
            self.temp = data['temp']
            self.data_process_thread.notify_update_data(data)
            self.data_save_thread.notify_update_data(data)
            # 更新显示
            # information_print.append(f"droplet: {self.droplet_data}\n"
            #                          f"Sum_Acc: {self.acc_data}\n"
            #                          f"Sum_Gyro: {self.gyro_data}\n"
            #                          f"distance: {self.distance}\n"
            #                          f"temp: {self.temp}")

    # 刷新WiFi当前链接信息
    @staticmethod
    def refresh_wifi_info(wifi_name: QLineEdit, ip_address: QLineEdit, wifi_agreement: QComboBox,
                          wifi_hostport: QComboBox, information_print: QTextEdit):
        SSID = get_wifi_name()
        wifi_name.setText(SSID)
        Agreement = wifi_agreement.currentText()
        HostPort = wifi_hostport.currentText()
        IPv4_Address = get_wifi_ipv4_address()
        ip_address.setText(IPv4_Address)
        information_print.append(
            f"当前WiFi的名称:{SSID}\r当前WiFi的通信协议:{Agreement}\r当前WiFi的IPv4地址:{IPv4_Address}\r当前WiFi的端口号:{HostPort}\r")

    @staticmethod
    def handle_connection_timeout(wifi_open: QPushButton):
        wifi_open.setText("Off")
        wifi_open.setIcon(QIcon("shangweiji_picture/红色开关.png"))


def clear_datainfo(information_print: QTextEdit, temp_data: QLineEdit, distance_data: QLineEdit,
                   recognize_result: QLineEdit, risk_grade: QLineEdit):
    information_print.clear()
    temp_data.clear()
    distance_data.clear()
    recognize_result.clear()
    risk_grade.clear()


def delete_csv_last_row(file_name, record_result: QLineEdit):
    try:
        # 读取CSV文件
        df = pd.read_csv(file_name)
        # 检查DataFrame是否为空
        if not df.empty:
            # 删除最后一行数据
            df = df.iloc[:-1]
            # 保存修改后的CSV文件（覆盖原文件）
            result = df.shape[0]
            print(result)
            df.to_csv(file_name, index=False)
            # 获取删除后的行数，并设置到QLineEdit控件
            record_result.setText(str(result))
            print(f"CSV文件{file_name}的最后一行已被删除并保存。")
        else:
            print(f"警告：CSV文件{file_name}为空，没有行可以被删除。")
            record_result.setText("未记录数据")  # 如果文件为空，设置未记录数据

    except Exception as e:
        # 捕捉异常并打印错误信息
        print(f"错误: {e}")


def waveform_window(groupbox4: QGroupBox):
    # 创建图表
    droplet_plot = pg.PlotWidget()
    acc_plot = pg.PlotWidget()
    gyro_plot = pg.PlotWidget()

    # 设置背景颜色为白色
    droplet_plot.setBackground('w')
    acc_plot.setBackground('w')
    gyro_plot.setBackground('w')

    # 检查并设置groupbox4的布局
    if groupbox4.layout() is None:
        layout1 = QVBoxLayout()  # 如果没有布局，设置一个垂直布局
        groupbox4.setLayout(layout1)
    else:
        layout1 = groupbox4.layout()

    # 配置groupbox4布局
    layout1.addWidget(droplet_plot)
    layout1.addWidget(acc_plot)
    layout1.addWidget(gyro_plot)

    # 设置每个图表均分空间，确保它们均等地显示
    layout1.setStretch(0, 1)  # 设置第一个控件的拉伸因子
    layout1.setStretch(1, 1)  # 设置第二个控件的拉伸因子
    layout1.setStretch(2, 1)  # 设置第三个控件的拉伸因子

    # 用于绘图的曲线
    droplet_curve = droplet_plot.plot(pen=pg.mkPen(pg.mkColor(255, 0, 0), width=2))
    acc_curve = acc_plot.plot(pen=pg.mkPen(pg.mkColor(61, 145, 64), width=2))  # 绿色曲线
    gyro_curve = gyro_plot.plot(pen=pg.mkPen(pg.mkColor(0, 0, 255), width=2))  # 蓝色曲线

    # 设置各个图表的标题、标签等
    droplet_plot.setLabel('left', 'Droplet')
    # self.droplet_plot.setLabel('bottom', 'Sampling Points')

    acc_plot.setLabel('left', 'Sum_Acc')
    # self.acc_plot.setLabel('bottom', 'Sampling Points')

    gyro_plot.setLabel('left', 'Sum_Gyro')
    # self.gyro_plot.setLabel('bottom', 'Sampling Points')

    # 设置横坐标范围为0到2000
    droplet_plot.setXRange(0, 2000)
    acc_plot.setXRange(0, 2000)
    gyro_plot.setXRange(0, 2000)

    axis = droplet_plot.getAxis('bottom')
    axis.setPen(pg.mkPen(width=2, color='k'))  # 加粗并设置为黑色
    axis.setTextPen(pg.mkPen(color='k'))  # 设置刻度数字颜色为黑色
    axis = droplet_plot.getAxis('left')
    axis.setPen(pg.mkPen(width=2, color='k'))  # 加粗并设置为黑色
    axis.setTextPen(pg.mkPen(color='k'))  # 设置刻度数字颜色为黑色

    axis = acc_plot.getAxis('bottom')
    axis.setPen(pg.mkPen(width=2, color='k'))  # 加粗并设置为黑色
    axis.setTextPen(pg.mkPen(color='k'))  # 设置刻度数字颜色为黑色
    axis = acc_plot.getAxis('left')
    axis.setPen(pg.mkPen(width=2, color='k'))  # 加粗并设置为黑色
    axis.setTextPen(pg.mkPen(color='k'))  # 设置刻度数字颜色为黑色

    axis = gyro_plot.getAxis('bottom')
    axis.setPen(pg.mkPen(width=2, color='k'))  # 加粗并设置为黑色
    axis.setTextPen(pg.mkPen(color='k'))  # 设置刻度数字颜色为黑色
    axis = gyro_plot.getAxis('left')
    axis.setPen(pg.mkPen(width=2, color='k'))  # 加粗并设置为黑色
    axis.setTextPen(pg.mkPen(color='k'))  # 设置刻度数字颜色为黑色

    return droplet_curve, acc_curve, gyro_curve


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = uic.loadUi("./droplet_detect_shangweiji_0115.ui")
    # 定义状态栏
    myStatusBar: QStatusBar = ui.statusbar
    # 定义WIFI栏
    WiFiRefresh: QPushButton = ui.WiFiButton_sx  # 定义WiFi刷新按钮
    WiFiOpen: QPushButton = ui.WiFiButton_on  # 定义WiFi开启按钮
    WiFiName: QLineEdit = ui.lineEdit_10  # 定义WIFI名称
    IPAddress: QLineEdit = ui.lineEdit_9  # 定义WIFI IP地址
    WiFiAgreement: QComboBox = ui.comboBox_10  # 定义WIFI协议
    WiFiHostPort: QComboBox = ui.comboBox_12  # 定义主机端口
    # 定义Serial栏
    SerialRefresh: QPushButton = ui.SerialButton_sx  # 定义串口刷新按钮
    SerialOpen: QPushButton = ui.SerialButton_on  # 定义串口开启按钮
    SerialBaud: QComboBox = ui.comboBox  # 定义串口波特率
    SerialPort: QComboBox = ui.comboBox_5  # 定义串口端口号
    SerialStopBit: QComboBox = ui.comboBox_6  # 定义串口停止位
    SerialCheckBit: QComboBox = ui.comboBox_8  # 定义串口校验位
    # 定义数据库栏
    DatabaseSave: QPushButton = ui.DatabaseButton_bc  # 定义保存数据按钮
    DatabaseOpen: QPushButton = ui.DatabaseButton_on  # 定义开启数据库按钮
    DatabaseHost: QLineEdit = ui.lineEdit_11  # 定义数据库主机名称
    DatabasePort: QLineEdit = ui.lineEdit_12  # 定义数据库端口
    DatabaseUserName: QLineEdit = ui.lineEdit_12  # 定义数据库用户名称
    DatabasePassword: QLineEdit = ui.lineEdit_12  # 定义数据库密码
    # 定义其它数据栏
    TempData: QLineEdit = ui.lineEdit  # 定义温度数据
    DistanceData: QLineEdit = ui.lineEdit_2  # 定义距离数据
    RecognizeResult: QLineEdit = ui.lineEdit_3  # 定义飞沫识别结果
    RecordResult: QLineEdit = ui.lineEdit_4  # 定义记录次数
    # 定义配置信息栏
    Configure_clear: QPushButton = ui.ConfigureButton_qp  # 定义清除信息按钮
    Delete_csvlastrow: QPushButton = ui.DeleteButton_sc  # 定义导出信息按钮
    Information_print: QTextEdit = ui.textEdit  # 定义信息打印窗口
    # 定义组盒栏
    GroupBox4: QGroupBox = ui.groupBox_4  # 该区域显示droplet
    # 状态栏初始化
    mystatusbar_init(myStatusBar)
    # 打印栏初始化
    Information_print.setStyleSheet("background-color: rgb(204, 232, 207);")
    Droplet_Curve, Acc_Curve, Gyro_Curve = waveform_window(GroupBox4)
    # 串口初始化
    serial_init(SerialBaud, SerialPort, SerialStopBit, SerialCheckBit)
    # 创建SerialManager实例
    serial_manager = SerialManager()
    # 串口状态刷新
    SerialRefresh.clicked.connect(
        lambda: serial_manager.refresh_serial_info(SerialBaud, SerialPort, SerialStopBit, SerialCheckBit,
                                                   Information_print))
    # 建立串口链接
    SerialOpen.clicked.connect(
        lambda: serial_manager.serial_connection(SerialOpen, SerialPort, WiFiOpen, Information_print))

    # WiFi初始化
    wifi_init(WiFiAgreement, WiFiHostPort)
    # 创建WiFiManager实例
    wifi_manager = WiFiManager(TempData, DistanceData, Droplet_Curve, Acc_Curve,
                               Gyro_Curve, RecordResult)
    # WiFi状态刷新
    WiFiRefresh.clicked.connect(
        lambda: wifi_manager.refresh_wifi_info(WiFiName, IPAddress, WiFiAgreement, WiFiHostPort, Information_print))
    # WiFi连接与断开
    WiFiOpen.clicked.connect(
        lambda: wifi_manager.wifi_connection(WiFiOpen, IPAddress, WiFiAgreement, WiFiHostPort, SerialOpen,
                                             Information_print,RecognizeResult))
    Delete_csvlastrow.clicked.connect(lambda: delete_csv_last_row('shiyan_ceshi.csv', RecordResult))
    # 清除所有数据和信息
    Configure_clear.clicked.connect(
        lambda: clear_datainfo(Information_print, TempData, DistanceData, RecognizeResult, RecordResult))

    ui.show()
    sys.exit(app.exec())
