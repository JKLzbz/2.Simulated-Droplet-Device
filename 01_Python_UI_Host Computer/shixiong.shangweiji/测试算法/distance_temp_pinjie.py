# 假设飞沫传感器、加速度传感器、角速度传感器的数据已经以numpy数组的形式存储
# time_series_data: (batch_size, 3, 512)
# distance_data: (batch_size, 1)
# temperature_data: (batch_size, 1)
import numpy as np

batch_size = 64  # 假设有10个样本
time_series_data = np.random.rand(batch_size, 3, 512)  # 随机生成数据
distance_data = np.random.rand(batch_size, 1) * 200  # 随机生成距离数据，范围0-200
temperature_data = np.random.rand(batch_size, 1) * 10  # 随机生成温度数据，范围0-10（假设单位是摄氏度）

# 拼接
combined_data = np.concatenate((time_series_data, distance_data, temperature_data), axis=1)
combined_data = np.reshape(combined_data, (batch_size, -1))  # 展平为二维数组