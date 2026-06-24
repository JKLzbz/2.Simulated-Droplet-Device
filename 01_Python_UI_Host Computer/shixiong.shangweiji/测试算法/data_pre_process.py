import pandas as pd
import numpy as np
import torch
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from torch.utils.data import TensorDataset, DataLoader


def read_csv_data(filename):
    # 读取CSV文件
    df = pd.read_csv(filename, header=None)
    # 获取数据列的数量，假设每行有1539列
    num_columns = df.shape[1]
    num_row = df.shape[0]
    print(f'数据集共有{num_row}条数据，每条数据共有{num_columns}列')
    # 分割数据列
    droplet_data = df.iloc[:, 0:512].values  # 第1到512列是droplet_data
    acc_data = df.iloc[:, 512:1024].values  # 第513到1024列是acc_data
    gyro_data = df.iloc[:, 1024:1536].values  # 第1025到1536列是gyro_data
    temp_data = df.iloc[:, 1536].values  # 第1537列是temp_data
    distance_data = df.iloc[:, 1537].values  # 第1538列是distance_data
    labels = df.iloc[:, 1538].values  # 第1539列是标签

    return droplet_data, acc_data, gyro_data, temp_data, distance_data, labels


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


def split_data(time_series_data, distance_indices, temperature_indices, labels, num_batch_size):
    # 转换为PyTorch张量
    time_series_data = torch.tensor(time_series_data, dtype=torch.float32)
    labels = torch.tensor(labels, dtype=torch.long)
    distance_indices = torch.tensor(distance_indices, dtype=torch.float32)
    temperature_indices = torch.tensor(temperature_indices, dtype=torch.float32)
    # 使用7:1.5:1.5比例划分训练集、验证集和测试集
    train_data, temp_data, train_labels, temp_labels = train_test_split(time_series_data, labels, test_size=0.3,
                                                                        random_state=42)
    val_data, test_data, val_labels, test_labels = train_test_split(temp_data, temp_labels, test_size=0.5,
                                                                    random_state=42)
    # 创建数据加载器
    train_dataset = TensorDataset(train_data, train_labels)
    val_dataset = TensorDataset(val_data, val_labels)
    test_dataset = TensorDataset(test_data, test_labels)

    train_loader = DataLoader(train_dataset, batch_size=num_batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=num_batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=num_batch_size, shuffle=False)

    print('训练集样本数:', len(train_dataset))
    print('验证集样本数:', len(val_dataset))
    print('测试集样本数:', len(test_dataset))

    return train_loader, val_loader, test_loader


def process_data(filename, num_batch_size):
    # 步骤1：读取和处理数据
    droplet_data, acc_data, gyro_data, temp_data, distance_data, labels = read_csv_data(filename)

    # 步骤2：标准化数据
    droplet_data_std, acc_data_std, gyro_data_std = standardize_data(droplet_data, acc_data, gyro_data)

    # 步骤3：构造3通道时间序列数据
    time_series_data = create_3channel_data(droplet_data_std, acc_data_std, gyro_data_std)

    # 步骤4：距离及温度范围映射
    distance_indices, temperature_indices = process_range_data(temp_data, distance_data)

    # 步骤4：划分数据集
    train_loader, val_loader, test_loader = split_data(time_series_data, labels, num_batch_size)

    return train_loader, val_loader, test_loader


def main():
    process_data('G:\desktop_access\code\shangweiji_20250107\sample_data.csv', 64)


if __name__ == "__main__":
    main()
