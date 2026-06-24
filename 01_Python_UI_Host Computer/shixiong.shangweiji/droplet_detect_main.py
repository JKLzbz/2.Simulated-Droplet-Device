import sys
import threading  # 用于创建和管理多线程
import socket  # 用于创建TCP服务器来监听客户端连接并接收数据
import csv  # 用于将接收到的数据保存到CSV文件
import struct  # 用于将接收到的二进制数据解析成浮动数据（float）
import time  # 用于延时和控制程序的执行时间
import queue  # 用于在多个线程之间传递数据
import subprocess
import serial.tools.list_ports
import re
import pyqtgraph as pg
from PyQt6 import uic
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QApplication, QLabel, QStatusBar, QLineEdit, QComboBox, QPushButton, QTextEdit


# 状态栏初始化
def mystatusbar_init(myStatusBar: QStatusBar):
    myStatusBarLabel = QLabel()
    myStatusBarLabel.setText("西南交通大学智能传感与微系统实验室")
    font = QFont("微软雅黑", 10, QFont.Weight.Bold)  # QFont.Weight.Bold 表示粗体
    myStatusBarLabel.setFont(font)
    myStatusBar.addPermanentWidget(myStatusBarLabel)


# 串口栏初始化
def serial_init(SerialBaud: QComboBox, SerialPort: QComboBox, SerialStopBit: QComboBox, SerialCheckBit: QComboBox):
    Baud = ["9600", "38400", "57600", "115200", "256000", "921600"]
    Port = ["COM3", "COM4", "COM13", "COM14"]
    StopBit = ["1", "2"]
    CheckBit = ["None","Odd","Even"]
    SerialBaud.addItems(Baud)
    SerialPort.addItems(Port)
    SerialStopBit.addItems(StopBit)
    SerialCheckBit.addItems(CheckBit)


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
def update_serialport(SerialPort: QComboBox, port: str):
    # 如果port为None，直接返回
    if port is None:
        print("当前串口的端口无效，请检查计算机与串口链接状况")
        SerialPort.setCurrentText(port) # 设置端口单行文本框为空
        return
    # 获取下拉框中所有的项
    existing_ports = [SerialPort.itemText(i) for i in range(SerialPort.count())]
    if port not in existing_ports:
        # 如果port不在下拉框中且不为空，添加它并设置为当前项
        SerialPort.addItem(port)
        SerialPort.setCurrentText(port)
    else:
        # 如果 port 已经在下拉框中，移除所有重复项
        for i in range(SerialPort.count()):
            if SerialPort.itemText(i) == port:
                SerialPort.removeItem(i)
        # 重新将 port 添加到下拉框并设置为当前文本
        SerialPort.addItem(port)
        SerialPort.setCurrentText(port)


# 建立串口连接
def setup_serial_connection(baud:str, port:str, stopbit:str, checkbit:str):
    print("This is serial setupfunction.")


# 断开串口连接
def close_serial_connection(baud:str, port:str, stopbit:str, checkbit:str):
    print("This is serial closefunction.")


class SerialManager:
    def __init__(self):
        self.baud = ""
        self.port = ""
        self.stopbit = ""
        self.checkbit = ""

    def refresh_serial_info(self, SerialBaud: QComboBox, SerialPort: QComboBox, SerialStopBit: QComboBox,
                            SerialCheckBit: QComboBox, Information_print: QTextEdit):
        Baud = SerialBaud.currentText()
        Port = get_ch340_port()  # 获取当前串口端口
        update_serialport(SerialPort, Port)  # 更新串口列表
        Stopbit = SerialStopBit.currentText()
        Checkbit = SerialCheckBit.currentText()
        if Port is None:
            Information_print.append("未检测到串口有效端口，请检查计算机与串口连接状况\r")
        else:
            Information_print.append(f"当前串口设置的波特率:{Baud}\r当前串口设置的端口:{Port}\r当前串口设置的停止位:{Stopbit}\r当前串口设置的校验位:{Checkbit}\r")
        self.baud = Baud
        self.port = Port
        self.stopbit = Stopbit
        self.checkbit = Checkbit

    # Serial连接与断开
    def serial_connection(self, SerialOpen:QPushButton, SerialPort: QComboBox, WiFiOpen:QPushButton, Information_print: QTextEdit):
        if WiFiOpen.text() == "On":
            Information_print.append("WiFi正在占用，无法建立串口通信\r")
        else:
            if get_ch340_port() is None:
                Information_print.append("未搜索到串口，无法建立串口通信\r")
            else:
                if SerialPort.currentText() != get_ch340_port():
                    Information_print.append("当前设置的串口的端口无效，无法连接\r")
                    SerialOpen.setText("Off")
                    SerialOpen.setIcon(QIcon("shangweiji_picture/红色开关.png"))
                else:
                    Serial_On_Off = SerialOpen.text()
                    if Serial_On_Off == "On":
                        SerialOpen.setText("Off")
                        SerialOpen.setIcon(QIcon("shangweiji_picture/红色开关.png"))
                        close_serial_connection(self.baud, self.port, self.stopbit, self.checkbit)
                    else:
                        SerialOpen.setText("On")
                        SerialOpen.setIcon(QIcon("shangweiji_picture/蓝色开关.png"))
                        setup_serial_connection(self.baud, self.port, self.stopbit, self.checkbit)


# WIFI初始化
def wifi_init(WiFiAgreement: QComboBox, WiFiHostPort: QComboBox):
    Agreement = ["TCP Server", "UDP"]
    Port = ["1234", "8080", "8086", "8089"]
    WiFiAgreement.addItems(Agreement)
    WiFiHostPort.addItems(Port)


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


# 建立WIFI连接
def setup_wifi_connection(agreement:str, hostport:str, ipv4_address:str, Information_print: QTextEdit):
    if agreement != "TCP Server":
        Information_print.append("TCP协议不匹配，请重选WiFi通信协议")
    else:
        # socket.socket():用来创建一个新的套接字对象的方法
        # socket.AF_INET:表示套接字使用IPv4
        # socket.SOCK_STREAM:表示套接字采用TCP协议
        # 将创建的套接字绑定到本地的一个IP地址和端口上，以便等待客户端的连接
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((ipv4_address, int(hostport)))
        # 使服务器套接字进入 监听状态，准备接受客户端的连接请求，并指定允许等待连接的最大客户端数量
        server_socket.listen(2)
        Information_print.append("WiFi通信连接中，请稍后...")
        # 等待一个客户端的连接，Server_Socket.accept()是一个阻塞操作，直到有客户端请求连接时
        # 它会返回一个新的套接字对象（connection）和客户端的地址信息（address）
        # connection是一个新创建的套接字，专门用于与这个客户端进行数据交换
        # 而原始的server_socket仍然在等待其他客户端连接
        connection, address = server_socket.accept()
        # with语句确保在代码块结束时，connection会自动关闭，不需要显式地调用connection.close()
        # 这样可以简化代码并避免潜在的资源泄漏问题
        with connection:
            print(f"已连接到地址:{address}")


# 断开WIFI连接
def close_wifi_connection(agreement:str, hostport:str, ipv4_address:str, Information_print: QTextEdit):
    print("This is wifi closefunction.")


class WiFiManager:
    def __init__(self):
        self.agreement = ""
        self.hostport = ""
        self.ipv4_address = ""

    # 刷新WiFi当前链接信息
    def refresh_wifi_info(self, WiFiName: QLineEdit, IPAddress: QLineEdit, WiFiAgreement: QComboBox, WiFiHostPort: QComboBox, Information_print: QTextEdit):
        SSID = get_wifi_name()
        WiFiName.setText(SSID)
        print(f"当前WiFi的名称:{SSID}")

        Agreement = WiFiAgreement.currentText()
        print(f"当前WiFi的通信协议:{Agreement}")

        HostPort = WiFiHostPort.currentText()
        print(f"当前WiFi的端口号:{HostPort}")

        IPv4_Address = get_wifi_ipv4_address()
        IPAddress.setText(IPv4_Address)
        print(f"当前WiFi的IPv4地址:{IPv4_Address}")

        Information_print.append(f"当前WiFi的名称:{SSID}\r当前WiFi的通信协议:{Agreement}\r当前WiFi的IPv4地址:{IPv4_Address}\r当前WiFi的端口号:{HostPort}\r")
        # 存储WiFi信息
        self.agreement = Agreement
        self.hostport = HostPort
        self.ipv4_address = IPv4_Address

    # WiFi连接与断开
    def wifi_connection(self, WiFiOpen:QPushButton, IPAddress: QLineEdit, SerialOpen:QPushButton, Information_print: QTextEdit):
        if SerialOpen.text() == "On":
            Information_print.append("串口正在占用，无法建立WiFi通信\r")
        else:
            if get_wifi_ipv4_address() is None:
                Information_print.append("IP地址为空，未连接WiFi\r")
            else:
                if IPAddress.text() != get_wifi_ipv4_address():
                    Information_print.append("当前设置的IP地址错误，无法建立WiFi通信\r")
                    WiFiOpen.setText("Off")
                    WiFiOpen.setIcon(QIcon("shangweiji_picture/红色开关.png"))
                else:
                    WiFi_On_Off = WiFiOpen.text()
                    if WiFi_On_Off == "On":
                        WiFiOpen.setText("Off")
                        WiFiOpen.setIcon(QIcon("shangweiji_picture/红色开关.png"))
                        close_wifi_connection(self.agreement, self.hostport, self.ipv4_address, Information_print)
                    else:
                        WiFiOpen.setText("On")
                        WiFiOpen.setIcon(QIcon("shangweiji_picture/蓝色开关.png"))
                        setup_wifi_connection(self.agreement, self.hostport, self.ipv4_address, Information_print)


def clear_datainfo(Information_print: QTextEdit, TempData: QLineEdit, DistanceData: QLineEdit, RecognizeResult: QLineEdit, RiskGrade: QLineEdit):
    Information_print.clear()
    TempData.clear()
    DistanceData.clear()
    RecognizeResult.clear()
    RiskGrade.clear()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = uic.loadUi("./droplet_detect_shangweiji.ui")
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
    RiskGrade: QLineEdit = ui.lineEdit_4  # 定义风险评估等级
    # 定义配置信息栏
    Configure_clear: QPushButton = ui.ConfigureButton_qc  # 定义清除信息按钮
    Configure_export: QPushButton = ui.ConfigureButton_dc  # 定义导出信息按钮
    Information_print: QTextEdit = ui.textEdit  # 定义信息打印窗口

    # 状态栏初始化
    mystatusbar_init(myStatusBar)
    # 串口初始化
    serial_init(SerialBaud, SerialPort, SerialStopBit, SerialCheckBit)
    # 创建SerialManager实例
    serial_manager = SerialManager()
    # 串口状态刷新
    SerialRefresh.clicked.connect(lambda: serial_manager.refresh_serial_info(SerialBaud, SerialPort, SerialStopBit, SerialCheckBit, Information_print))
    # 建立串口链接
    SerialOpen.clicked.connect(lambda: serial_manager.serial_connection(SerialOpen, SerialPort, WiFiOpen, Information_print))

    # WiFi初始化
    wifi_init(WiFiAgreement, WiFiHostPort)
    # 创建WiFiManager实例
    wifi_manager = WiFiManager()
    # WiFi状态刷新
    WiFiRefresh.clicked.connect(lambda: wifi_manager.refresh_wifi_info(WiFiName, IPAddress, WiFiAgreement, WiFiHostPort, Information_print))
    # 建立WiFi链接
    WiFiOpen.clicked.connect(lambda: wifi_manager.wifi_connection(WiFiOpen,IPAddress, SerialOpen, Information_print))

    # 清除所有数据和信息
    Configure_clear.clicked.connect(lambda: clear_datainfo(Information_print, TempData, DistanceData, RecognizeResult, RiskGrade))

    ui.show()
    sys.exit(app.exec())
