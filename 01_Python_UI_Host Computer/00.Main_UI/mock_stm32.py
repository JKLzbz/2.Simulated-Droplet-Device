import socket
import time
import struct
import math

# 配置
HOST = "127.0.0.1"
PORT = 8080
INTERVAL = 0.01  # 100Hz

def main():
    print(f"正在尝试连接上位机 TCP Server {HOST}:{PORT}...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        print("连接成功！正在以 100Hz 发送模拟遥测数据...")
    except Exception as e:
        print(f"连接失败: {e}\n请先在上位机界面点击“连接”以启动 TCP 监听，然后重新运行本脚本。")
        return

    frame_count = 0
    try:
        while True:
            # 基础模拟值
            droplet = 0.1 + 0.05 * math.sin(frame_count * 0.1)
            distance = 150  # 15.0 cm (150 mm)
            temp = 25.4

            # 每隔 5 秒（500 帧）产生一次大电容突变（飞沫冲击）
            cycle = frame_count % 500
            if 300 <= cycle < 450:
                # 模拟一个典型的咳嗽/飞沫冲击波形 (Gupta 曲线形状的峰)
                t_cough = (cycle - 300) / 100.0  # 0 到 1.5 秒
                # 双 gamma 近似
                wave = 30.0 * (t_cough ** 2.5 * math.exp(-t_cough / 0.03) + 0.2 * t_cough ** 1.5 * math.exp(-t_cough / 0.2))
                droplet += wave
                distance = int(150 + 20 * math.sin(t_cough * math.pi))  # 距离有些波动
                temp = 25.4 + 0.2 * math.sin(t_cough * math.pi)

            # 打包成 13 字节协议：<BBfHfB
            # header1(0xAA), header2(0xFF), droplet(float), distance(u16), temp(float), checksum(0)
            packet = struct.pack("<BBfHfB", 0xAA, 0xFF, droplet, int(distance), temp, 0)
            s.sendall(packet)

            frame_count += 1
            time.sleep(INTERVAL)

    except KeyboardInterrupt:
        print("\n模拟器被用户终止")
    except Exception as e:
        print(f"发送数据异常: {e}")
    finally:
        s.close()
        print("连接已关闭")

if __name__ == "__main__":
    main()
