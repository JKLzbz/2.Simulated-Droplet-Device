
import torch
import torch.nn as nn
class ChannelAttention(nn.Module):
    def __init__(self, in_channels, reduction_ratio=16):
        super(ChannelAttention, self).__init__()
        self.avg_pool = nn.AdaptiveAvgPool1d(1)
        self.fc = nn.Sequential(
            nn.Linear(in_channels, in_channels // reduction_ratio),
            nn.ReLU(),
            nn.Linear(in_channels // reduction_ratio, in_channels),
            nn.Sigmoid()
        )

    def forward(self, x):
        b, c, _ = x.size()
        y = self.avg_pool(x).view(b, c)
        y = self.fc(y).view(b, c, 1)
        return x * y.expand_as(x)

class GRUModel(nn.Module):
    def __init__(self):
        super(GRUModel, self).__init__()
        self.gru = nn.GRU(3, 128, batch_first=True)
        self.ca = ChannelAttention(128)
        self.fc_aux = nn.Linear(2, 64)
        self.fc = nn.Linear(128 + 64, 10)

    def forward(self, x_seq, x_aux):
        out, _ = self.gru(x_seq)
        out = out[:, -1, :]  # 取最后一个时间步的输出
        out = self.ca(out.unsqueeze(1)).squeeze(1)
        x_aux = self.fc_aux(x_aux)
        x = torch.cat((out, x_aux), dim=1)
        x = self.fc(x)
        return x

# 示例输入
x_seq = torch.randn(32, 3, 512)  # 32个样本，3个通道，每个样本512个时间步
x_aux = torch.randn(32, 2)  # 32个样本，2个辅助特征（距离和温度）
model = GRUModel()
output = model(x_seq, x_aux)