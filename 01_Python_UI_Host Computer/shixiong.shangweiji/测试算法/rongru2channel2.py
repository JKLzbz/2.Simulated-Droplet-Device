import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

class ChannelAttention(nn.Module):
    def __init__(self, in_channels):
        super(ChannelAttention, self).__init__()
        self.fc1 = nn.Linear(in_channels, in_channels // 2)
        self.fc2 = nn.Linear(in_channels // 2, in_channels)

    def forward(self, x):
        avg_pool = torch.mean(x, dim=1)  # Global Average Pooling
        max_pool, _ = torch.max(x, dim=1)  # Global Max Pooling
        pooled = torch.cat([avg_pool, max_pool], dim=1)
        attention = torch.sigmoid(self.fc2(F.relu(self.fc1(pooled))))
        attention = attention.unsqueeze(2).expand_as(x)
        return x * attention

class ResidualBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv1d(in_channels, out_channels, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(out_channels, out_channels, kernel_size=3, padding=1)
        self.shortcut = nn.Conv1d(in_channels, out_channels, kernel_size=1)
        self.relu = nn.ReLU()

    def forward(self, x):
        shortcut = self.shortcut(x)
        out = self.relu(self.conv1(x))
        out = self.conv2(out)
        return self.relu(out + shortcut)

class TimeSeriesModel(nn.Module):
    def __init__(self, input_size=7, num_classes=3):
        super(TimeSeriesModel, self).__init__()
        self.conv1 = nn.Conv1d(input_size, 64, kernel_size=3, padding=1)
        self.res_block1 = ResidualBlock(64, 128)
        self.res_block2 = ResidualBlock(128, 256)
        self.gru = nn.GRU(256, 128, batch_first=True)
        self.attention = ChannelAttention(128)
        self.fc = nn.Linear(128, num_classes)

    def forward(self, x):
        x = x.permute(0, 2, 1)  # Change shape to (batch_size, channels, time_steps)
        x = F.relu(self.conv1(x))  # Apply Conv1d
        x = self.res_block1(x)
        x = self.res_block2(x)
        x, _ = self.gru(x)
        x = self.attention(x)  # Apply Channel Attention
        x = torch.mean(x, dim=1)  # Global Average Pooling across time dimension
        x = self.fc(x)
        return x

# 训练示例
model = TimeSeriesModel(input_size=7, num_classes=3)
optimizer = optim.Adam(model.parameters(), lr=0.001)
criterion = nn.CrossEntropyLoss()

# 输入数据的形状: (batch_size, 512, 7)
input_data = torch.randn(32, 512, 7)  # 假设batch_size=32
target = torch.randint(0, 3, (32,))  # 假设3个分类标签

# 训练步骤
optimizer.zero_grad()
output = model(input_data)
loss = criterion(output, target)
loss.backward()
optimizer.step()

print("Loss:", loss.item())
