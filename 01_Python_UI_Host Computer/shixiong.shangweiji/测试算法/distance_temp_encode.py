import torch
import torch.nn as nn

# 定义距离和温度的范围编码
distance_bins = [0, 60, 80, 100, 120, 140, 160, 200, float('inf')]
temperature_bins = [-float('inf'), 35.9, 36.8, 41, float('inf')]


# 编码函数
def encode_value(value, bins):
    for i, bin_edge in enumerate(bins):
        if value < bin_edge:
            return i
    return len(bins) - 1

# 示例数据
distance_value = 170  # cm
temperature_value = 37.2  # degrees

# 编码
distance_encoded = encode_value(distance_value, distance_bins)
temperature_encoded = encode_value(temperature_value, temperature_bins)

print(f"Distance encoded: {distance_encoded}")
print(f"Temperature encoded: {temperature_encoded}")