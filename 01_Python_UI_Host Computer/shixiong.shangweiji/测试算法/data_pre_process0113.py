import pandas as pd
import numpy as np
import torch
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from torch import nn
from torch.utils.data import TensorDataset, DataLoader


def read_csv_data(filename):
    # 读取CSV文件
    df = pd.read_csv(filename, header=None)
    # 获取数据列的数量，假设每行有1539列
    num_columns = df.shape[1]
    num_row = df.shape[0]
    print(f'数据集中共有{num_row}条数据，每条数据共有{num_columns}列')
    labels = df.iloc[:, 1538].values  # 第1539列是标签
    data = df.iloc[:, 0:1538].values  # 第1列到第1538列为所有传感器数据

    return data, labels


def standardize_data(droplet_data, acc_data, gyro_data):
    # 创建StandardScaler对象
    scaler_droplet = StandardScaler()
    scaler_acc = StandardScaler()
    scaler_gyro = StandardScaler()
    # 标准化数据
    droplet_data_std = scaler_droplet.fit_transform(droplet_data)
    acc_data_std = scaler_acc.fit_transform(acc_data)
    gyro_data_std = scaler_gyro.fit_transform(gyro_data)

    return droplet_data_std, acc_data_std, gyro_data_std


def create_3channel_data(droplet_data_std, acc_data_std, gyro_data_std):
    # 将droplet_data, acc_data和gyro_data分别标准化后组合成3通道时间序列数据
    # 每一行构成一个3通道的时间序列数据
    time_series_data = np.stack([droplet_data_std, acc_data_std, gyro_data_std], axis=-1)

    return time_series_data


# 将单值数据映射到范围
def map_to_range(value, ranges):
    for idx, (low, high) in enumerate(ranges):
        if low <= value < high:
            return idx
    return len(ranges) - 1


# 处理范围映射
def process_range_data(temp_data, distance_data):
    # 定义范围编码
    distance_ranges = [
        (0, 40), (40, 60), (60, 80), (80, 100), (100, 120),
        (120, 160), (160, 200), (200, float('inf'))
    ]
    temperature_ranges = [
        (-float('inf'), 35.9), (35.9, 36.8), (36.8, 41), (41, float('inf'))
    ]

    # 映射到索引
    distance_indices = np.array([map_to_range(val, distance_ranges) for val in distance_data])
    temperature_indices = np.array([map_to_range(val, temperature_ranges) for val in temp_data])

    return distance_indices, temperature_indices


def split_data(time_series_data, time_series_labels):
    # 使用7:1.5:1.5比例划分训练集、验证集和测试集
    train_data, temp_data, train_labels, temp_labels = train_test_split(time_series_data, time_series_labels,test_size=0.3, random_state=42)
    val_data, test_data, val_labels, test_labels = train_test_split(temp_data, temp_labels, test_size=0.5, random_state=42)
    # 分割数据列
    # 训练集
    train_droplet_data = train_data[:, 0:512]
    train_acc_data = train_data[:, 512:1024]
    train_gyro_data = train_data[:, 1024:1536]  # 第1025到1536列是gyro_data
    train_temp_data = train_data[:, 1536]  # 第1537列是temp_data
    train_distance_data = train_data[:, 1537]  # 第1538列是distance_data

    # 验证集
    val_droplet_data = val_data[:, 0:512]
    val_acc_data = val_data[:, 512:1024]
    val_gyro_data = val_data[:, 1024:1536]  # 第1025到1536列是gyro_data
    val_temp_data = val_data[:, 1536]  # 第1537列是temp_data
    val_distance_data = val_data[:, 1537]  # 第1538列是distance_data

    # 测试集
    test_droplet_data = test_data[:, 0:512]
    test_acc_data = test_data[:, 512:1024]
    test_gyro_data = test_data[:, 1024:1536]  # 第1025到1536列是gyro_data
    test_temp_data = test_data[:, 1536]  # 第1537列是temp_data
    test_distance_data = test_data[:, 1537]  # 第1538列是distance_data

    return train_droplet_data, train_acc_data, train_gyro_data, train_temp_data, train_distance_data,\
        val_droplet_data, val_acc_data, val_gyro_data, val_temp_data, val_distance_data,\
        test_droplet_data, test_acc_data, test_gyro_data, test_temp_data, test_distance_data,\
        train_labels, val_labels, test_labels


def process_data(filename, num_batch_size):
    # 步骤1：读取和处理数据
    time_series_data, time_series_labels = read_csv_data(filename)

    # 步骤2：# 数据集划分
    train_droplet_data, train_acc_data, train_gyro_data, train_temp_data, train_distance_data,\
        val_droplet_data, val_acc_data, val_gyro_data, val_temp_data, val_distance_data,\
        test_droplet_data, test_acc_data, test_gyro_data, test_temp_data, test_distance_data,\
        train_labels, val_labels, test_labels = split_data(time_series_data, time_series_labels)
    # 步骤2：标准化训练集、测试集和验证集 飞沫信号、合加速度和合角速度数据
    train_droplet_data_std, train_acc_data_std, train_gyro_data_std = standardize_data(train_droplet_data,
                                                                                       train_acc_data, train_gyro_data)
    val_droplet_data_std, val_acc_data_std, val_gyro_data_std = standardize_data(val_droplet_data,
                                                                                 val_acc_data, val_gyro_data)
    test_droplet_data_std, test_acc_data_std, test_gyro_data_std = standardize_data(test_droplet_data,
                                                                                    test_acc_data, test_gyro_data)
    # 步骤3：构造3通道时间序列数据
    train_time_series_data = create_3channel_data(train_droplet_data_std, train_acc_data_std, train_gyro_data_std)
    val_time_series_data = create_3channel_data(val_droplet_data_std, val_acc_data_std, val_gyro_data_std)
    test_time_series_data = create_3channel_data(test_droplet_data_std, test_acc_data_std, test_gyro_data_std)

    # 步骤4：距离及温度范围映射
    train_distance_indices, train_temperature_indices = process_range_data(train_temp_data, train_distance_data)
    val_distance_indices, val_temperature_indices = process_range_data(val_temp_data, val_distance_data)
    test_distance_indices, test_temperature_indices = process_range_data(test_temp_data, test_distance_data)

    # 转换为PyTorch张量
    train_time_series_data = torch.tensor(train_time_series_data, dtype=torch.float32)
    val_time_series_data = torch.tensor(val_time_series_data, dtype=torch.float32)
    test_time_series_data = torch.tensor(test_time_series_data, dtype=torch.float32)
    train_labels = torch.tensor(train_labels, dtype=torch.long)
    val_labels = torch.tensor(val_labels, dtype=torch.long)
    test_labels = torch.tensor(test_labels, dtype=torch.long)

    train_distance_indices = torch.tensor(train_distance_indices, dtype=torch.float32)
    train_temperature_indices = torch.tensor(train_temperature_indices, dtype=torch.float32)
    val_distance_indices = torch.tensor(val_distance_indices, dtype=torch.float32)
    val_temperature_indices = torch.tensor(val_temperature_indices, dtype=torch.float32)
    test_distance_indices = torch.tensor(test_distance_indices, dtype=torch.float32)
    test_temperature_indices = torch.tensor(test_temperature_indices, dtype=torch.float32)
    print(train_time_series_data.shape)

    # 创建数据加载器
    train_dataset = TensorDataset(train_time_series_data, train_labels, train_distance_indices, train_temperature_indices)
    val_dataset = TensorDataset(val_time_series_data, val_labels, val_distance_indices, val_temperature_indices)
    test_dataset = TensorDataset(test_time_series_data, test_labels, test_distance_indices, test_temperature_indices)

    train_loader = DataLoader(train_dataset, batch_size=num_batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=num_batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=num_batch_size, shuffle=False)

    print('训练集样本数:', len(train_dataset))
    print('验证集样本数:', len(val_dataset))
    print('测试集样本数:', len(test_dataset))

    return train_loader, val_loader, test_loader


class CNN_GRU_Attention(nn.Module):
    def __init__(self):
        super().__init__()


def main():
    process_data('G:\desktop_access\code\shangweiji_20250107\ceshi.csv', 64)


if __name__ == "__main__":
    main()
