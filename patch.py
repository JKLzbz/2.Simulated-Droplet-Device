import glob, os, re

files = glob.glob(r'D:\02Projects\01Simulated-Droplet-Device\01_Python_UI_Host Computer\shangweiji_20250504\*\droplet_detect_main_0327.py')
if not files:
    print('File not found')
    exit()
file_path = files[0]

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace length check and struct unpack
pattern = re.compile(r'if len\(data\) != 29:.*?return \{\n.*?\n.*?\n.*?\n.*?\n.*?\n\s+\}', re.DOTALL)

replacement = '''if len(data) != 13:
            self.update_signal.emit("数据长度不对，丢弃当前帧数据！")
            return None  # 长度不对，返回空值
        header1, header2 = struct.unpack('BB', data[0:2])
        if header1 != 0xAA or header2 != 0xFF:
            self.update_signal.emit("帧头不对，当前帧无效")
            return None
        try:
            droplet = struct.unpack('f', data[2:6])[0]
            distance = struct.unpack('H', data[6:8])[0]
            temp = struct.unpack('f', data[8:12])[0]
            checksum = struct.unpack('B', data[12:13])[0]
        except struct.error as e:
            self.update_signal.emit(f"数据解包失败: {e}")
            return None
        # 校验和验证
        data_to_check = data[:-1]
        calculated_checksum = self.calculate_checksum(data_to_check)
        if calculated_checksum != checksum:
            self.update_signal.emit(f"校验和错!计算:{calculated_checksum},接收:{checksum}")
            return None
        
        # 保留虚拟的acc和gyro，确保旧UI不报错
        sum_acc = 0.0
        sum_gyro = 0.0

        droplet = round(droplet, 4)
        distance = round(distance / 10, 1)

        return {
            'droplet': droplet,
            'acc': sum_acc,
            'gyro': sum_gyro,
            'distance': distance,
            'temp': temp
        }'''

new_content = pattern.sub(replacement, content)

# 2. Disable kalman filter updates in Thread since we do it on MCU
pattern_kalman = re.compile(r'with QMutexLocker\(self\.filter_mutex\):\s+filtered_acc = self\.kalman_acc\.update\(raw_acc\)\s+filtered_gyro = self\.kalman_gyro\.update\(raw_gyro\)')
replacement_kalman = '''with QMutexLocker(self.filter_mutex):
                filtered_acc = raw_acc
                filtered_gyro = raw_gyro'''
new_content = pattern_kalman.sub(replacement_kalman, new_content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Updated successfully')
