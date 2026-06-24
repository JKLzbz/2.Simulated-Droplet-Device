import pandas as pd

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
    labels = df.iloc[:, 2112].values  # 第2113列是标签

    return droplet_data, labels


def standardize_data(train_droplet, val_droplet, test_droplet):
    # 创建并拟合训练集的标准化器
    scaler_droplet = StandardScaler().fit(train_droplet)

    # 转换所有数据集
    train_droplet_std = scaler_droplet.transform(train_droplet)

    val_droplet_std = scaler_droplet.transform(val_droplet)

    test_droplet_std = scaler_droplet.transform(test_droplet)

    return train_droplet_std, val_droplet_std, test_droplet_std


# 数据集划分并生成 DataLoader
def create_dataloaders(droplet_data, labels, batch_size, test_size=0.197, val_size=0.103):
    # 首先划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(droplet_data, labels, test_size=test_size,stratify=labels, random_state=42)


    # 再从训练集中划分出验证集
    X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=val_size, stratify=y_train, random_state=42)

    # 标准化数据
    X_train_std, X_val_std, X_test_std = standardize_data(X_train, X_val, X_test)

    # 转换为 PyTorch 的张量
    train_data = TensorDataset(torch.tensor(X_train_std, dtype=torch.float32).unsqueeze(1), torch.tensor(y_train, dtype=torch.long))
    val_data = TensorDataset(torch.tensor(X_val_std, dtype=torch.float32).unsqueeze(1), torch.tensor(y_val, dtype=torch.long))
    test_data = TensorDataset(torch.tensor(X_test_std, dtype=torch.float32).unsqueeze(1), torch.tensor(y_test, dtype=torch.long))

    # 创建 DataLoader
    train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_data, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_data, batch_size=batch_size, shuffle=False)

    print('训练集样本数:', len(train_data))
    print('训练集形状:', X_train_std.shape)  # 新增行
    print('验证集样本数:', len(val_data))
    print('测试集样本数:', len(test_data))

    return train_loader, val_loader, test_loader


def process_data(filename, num_batch_size):
    # 步骤1：读取和处理数据
    droplet_data, labels = read_csv_data(filename)
    train_loader, val_loader, test_loader = create_dataloaders(droplet_data, labels, num_batch_size)

    return train_loader, val_loader, test_loader


def main():
    train_loader, val_loader, test_loader = process_data('data_sheet_0318.csv', 32)


if __name__ == "__main__":
    main()
