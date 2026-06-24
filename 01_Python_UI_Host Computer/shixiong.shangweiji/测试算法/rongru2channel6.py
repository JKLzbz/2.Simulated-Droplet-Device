import torch
import torch.nn as nn

class ResidualBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv1d(in_channels, out_channels, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm1d(out_channels)
        self.conv2 = nn.Conv1d(out_channels, out_channels, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm1d(out_channels)

    def forward(self, x):
        residual = x
        out = F.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out += residual
        out = F.relu(out)
        return out

class TransformerModel(nn.Module):
    def __init__(self):
        super(TransformerModel, self).__init__()
        self.cnn = nn.Sequential(
            ResidualBlock(3, 64),
            nn.MaxPool1d(kernel_size=2),
            ResidualBlock(64, 128),
            nn.MaxPool1d(kernel_size=2)
        )
        self.transformer = nn.TransformerEncoderLayer(d_model=128, nhead=8)
        self.fc_aux = nn.Linear(2, 64)
        self.fc = nn.Linear(128 * 128 + 64, 10)

    def forward(self, x_seq, x_aux):
        x_seq = self.cnn(x_seq)
        x_seq = x_seq.permute(1, 0, 2)  # (seq_len, batch_size, d_model)
        x_seq = self.transformer(x_seq)
        x_seq = x_seq.permute(1, 2, 0).view(x_seq.size(0), -1)
        x_aux = self.fc_aux(x_aux)
        x = torch.cat((x_seq, x_aux), dim=1)
        x = self.fc(x)
        return x

# 示例输入
x_seq = torch.randn(32, 3, 512)  # 32个样本，3个通道，每个样本512个时间步
x_aux = torch.randn(32, 2)  # 32个样本，2个辅助特征（距离和温度）
model = TransformerModel()
output = model(x_seq, x_aux)