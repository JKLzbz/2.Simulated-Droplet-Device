import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader

class SensorDataDataset(torch.utils.data.Dataset):
    def __init__(self, time_series_data, temperature_data, distance_data, labels):
        self.time_series_data = time_series_data
        self.temperature_data = temperature_data
        self.distance_data = distance_data
        self.labels = labels

    def __len__(self):
        return len(self.time_series_data)

    def __getitem__(self, idx):
        time_series = self.time_series_data[idx]
        temp = self.temperature_data[idx]
        distance = self.distance_data[idx]
        label = self.labels[idx]

        # 将温度和距离数据与每个时间步的时间序列数据拼接
        extended_time_series = np.concatenate([time_series, np.repeat([temp, distance], time_series.shape[0], axis=0)],
                                              axis=1)
        return torch.tensor(extended_time_series, dtype=torch.float32), torch.tensor(label, dtype=torch.long)

class AttentionBlock(nn.Module):
    def __init__(self, in_channels):
        super(AttentionBlock, self).__init__()
        self.attn = nn.MultiheadAttention(embed_dim=in_channels, num_heads=4)

    def forward(self, x):
        # 由于MultiheadAttention要求输入是 [seq_len, batch_size, features]
        x = x.permute(1, 0, 2)  # 转置到 [batch_size, seq_len, features]
        attn_output, _ = self.attn(x, x, x)  # 计算注意力
        return attn_output.permute(1, 0, 2)  # 恢复到 [batch_size, seq_len, features]


class SensorClassifier(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(SensorClassifier, self).__init__()

        # 卷积层
        self.conv1 = nn.Conv1d(input_dim, 64, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv1d(64, 128, kernel_size=3, stride=1, padding=1)

        # GRU层
        self.gru = nn.GRU(128, 256, batch_first=True)

        # 自注意力层
        self.attn_block = AttentionBlock(256)

        # 残差连接
        self.residual = nn.Conv1d(256, 256, kernel_size=1)

        # 全连接层（分类层）
        self.fc = nn.Linear(256, output_dim)

    def forward(self, x):
        # 卷积部分
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))

        # GRU部分
        x, _ = self.gru(x.permute(0, 2, 1))  # GRU的输入是 [batch, seq_len, features]

        # 自注意力部分
        x = self.attn_block(x)

        # 残差连接
        x_residual = self.residual(x)
        x = x + x_residual

        # 取最后一个时间步的输出作为特征
        x = x[:, -1, :]  # [batch_size, features]

        # 全连接层输出
        x = self.fc(x)

        return x


# 训练模型
model = SensorClassifier(input_dim=5, output_dim=10)  # 假设有5个特征，10个分类


# 假设你已经准备好训练数据和标签
train_dataset = SensorDataDataset(time_series_data, temperature_data, distance_data, labels)
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

model = SensorClassifier(input_dim=5, output_dim=10)  # 5个输入特征，10个类别
criterion = nn.CrossEntropyLoss()  # 多分类交叉熵损失
optimizer = optim.Adam(model.parameters(), lr=0.001)

# 训练循环
for epoch in range(10):
    model.train()
    running_loss = 0.0
    for inputs, labels in train_loader:
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item()
    print(f"Epoch {epoch + 1}, Loss: {running_loss / len(train_loader)}")

