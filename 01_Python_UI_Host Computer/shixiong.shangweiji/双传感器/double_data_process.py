import joblib
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
    droplet_data = df.iloc[:, 0:704].values  # 第1到704列是droplet_data
    acc_data = df.iloc[:, 704:1408].values  # 第704到1408列是acc_data
    gyro_data = df.iloc[:, 1408:2112].values  # 第1408到2112列是gyro_data
    labels = df.iloc[:, 2112].values  # 第2113列是标签

    return droplet_data, acc_data, gyro_data, labels


def standardize_data(train_droplet, train_acc, train_gyro, val_droplet, val_acc, val_gyro, test_droplet, test_acc,
                     test_gyro):
    # 创建并拟合训练集的标准化器
    scaler_droplet = StandardScaler().fit(train_droplet)
    scaler_acc = StandardScaler().fit(train_acc)
    scaler_gyro = StandardScaler().fit(train_gyro)

    # 转换所有数据集
    train_droplet_std = scaler_droplet.transform(train_droplet)
    train_acc_std = scaler_acc.transform(train_acc)
    train_gyro_std = scaler_gyro.transform(train_gyro)

    val_droplet_std = scaler_droplet.transform(val_droplet)
    val_acc_std = scaler_acc.transform(val_acc)
    val_gyro_std = scaler_gyro.transform(val_gyro)

    test_droplet_std = scaler_droplet.transform(test_droplet)
    test_acc_std = scaler_acc.transform(test_acc)
    test_gyro_std = scaler_gyro.transform(test_gyro)

    return (train_droplet_std, train_acc_std, train_gyro_std,
            val_droplet_std, val_acc_std, val_gyro_std,
            test_droplet_std, test_acc_std, test_gyro_std)


def create_3channel_data(droplet_data_std, acc_data_std, gyro_data_std):
    # 将droplet_data, acc_data和gyro_data分别标准化后组合成3通道时间序列数据
    # 每一行构成一个3通道的时间序列数据
    time_series_data = np.stack([droplet_data_std, acc_data_std, gyro_data_std], axis=-1)
    # 转置数组，交换第二维和第三维
    time_series_data = np.transpose(time_series_data, (0, 2, 1))
    return time_series_data


def convert_dataloader(time_series_train, train_labels, time_series_val, val_labels, time_series_test, test_labels, num_batch_size):
    # 转换为PyTorch张量
    time_series_train = torch.tensor(time_series_train, dtype=torch.float32)
    time_series_val = torch.tensor(time_series_val, dtype=torch.float32)
    time_series_test = torch.tensor(time_series_test, dtype=torch.float32)
    # print(time_series_train.shape)
    train_labels = torch.tensor(train_labels, dtype=torch.long)
    val_labels = torch.tensor(val_labels, dtype=torch.long)
    test_labels = torch.tensor(test_labels, dtype=torch.long)
    # 创建数据加载器
    train_dataset = TensorDataset(time_series_train, train_labels)
    val_dataset = TensorDataset(time_series_val, val_labels)
    test_dataset = TensorDataset(time_series_test, test_labels)

    train_loader = DataLoader(train_dataset, batch_size=num_batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=num_batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=num_batch_size, shuffle=False)

    print('训练集样本数:', len(train_dataset))
    print('验证集样本数:', len(val_dataset))
    print('测试集样本数:', len(test_dataset))

    return train_loader, val_loader, test_loader


def process_data(filename, num_batch_size):
    # 步骤1：读取和处理数据
    droplet_data, acc_data, gyro_data, labels = read_csv_data(filename)
    # 步骤2：先划分数据集
    train_data, temp_data, train_labels, temp_labels = train_test_split(
        np.arange(len(labels)), labels, test_size=0.3, stratify=labels, random_state=42
    )
    val_data, test_data, val_labels, test_labels = train_test_split(
        temp_data, temp_labels, test_size=0.66, stratify=temp_labels, random_state=42
    )
    # 步骤3：再进行标准化（仅在训练集拟合）
    (train_droplet_std, train_acc_std, train_gyro_std,
     val_droplet_std, val_acc_std, val_gyro_std,
     test_droplet_std, test_acc_std, test_gyro_std) = standardize_data(
        droplet_data[train_data], acc_data[train_data], gyro_data[train_data],
        droplet_data[val_data], acc_data[val_data], gyro_data[val_data],
        droplet_data[test_data], acc_data[test_data], gyro_data[test_data]
    )

    # 保存标准化器
    joblib.dump(StandardScaler().fit(droplet_data[train_data]), 'scaler_droplet.pkl')
    joblib.dump(StandardScaler().fit(acc_data[train_data]), 'scaler_acc.pkl')
    joblib.dump(StandardScaler().fit(gyro_data[train_data]), 'scaler_gyro.pkl')

    # 步骤4：构造3通道数据
    time_series_train = create_3channel_data(train_droplet_std, train_acc_std, train_gyro_std)
    time_series_val = create_3channel_data(val_droplet_std, val_acc_std, val_gyro_std)
    time_series_test = create_3channel_data(test_droplet_std, test_acc_std, test_gyro_std)

    # 步骤5：转换为DataLoader
    train_loader, val_loader, test_loader = convert_dataloader(time_series_train, train_labels, time_series_val, val_labels, time_series_test, test_labels, num_batch_size)

    return train_loader, val_loader, test_loader


def main():
    train_loader, val_loader, test_loader = process_data('data_sheet.csv', 32)


if __name__ == "__main__":
    main()
