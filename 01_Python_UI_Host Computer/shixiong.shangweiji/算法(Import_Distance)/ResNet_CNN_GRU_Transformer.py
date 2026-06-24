import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.nn import Mish


class ResidualBlock(nn.Module):
    def __init__(self, in_channels, out_channels, stride=1):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv1d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1)
        self.bn1 = nn.BatchNorm1d(out_channels)
        self.mish = Mish(inplace=True)  # 使用Mish代替ReLU
        self.conv2 = nn.Conv1d(out_channels, out_channels, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm1d(out_channels)

        # 为了匹配输入和输出的维度，需要在跳跃连接中添加合适的卷积
        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv1d(in_channels, out_channels, kernel_size=1, stride=stride),
                nn.BatchNorm1d(out_channels)
            )

    def forward(self, x):
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.mish(out)  # 使用Mish
        out = self.conv2(out)
        out = self.bn2(out)
        out += self.shortcut(x)  # 添加跳跃连接
        out = self.mish(out)  # 使用Mish
        return out


class ResidualNetwork(nn.Module):
    def __init__(self, input_channels, out_channels, num_residual_blocks, num_classes):
        super(ResidualNetwork, self).__init__()
        # 输入层
        self.conv1 = nn.Conv1d(input_channels, 64, kernel_size=5, stride=1, padding=2)
        self.bn1 = nn.BatchNorm1d(64)
        # 残差块
        self.residual_blocks = self._make_residual_layers(64, out_channels, num_residual_blocks, stride=1)
        # 全连接层
        self.avg_pool = nn.AdaptiveAvgPool1d(1)  # 自适应池化到1
        self.fc = nn.Linear(out_channels, num_classes)  # 输出类别数

    @staticmethod
    def make_residual_layers(in_channels, out_channels, num_blocks, stride=1):
        layers = []
        for _ in range(num_blocks):
            layers.append(ResidualBlock(in_channels, out_channels, stride))
        return nn.Sequential(*layers)

    def forward(self, x):
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.mish(out)
        out = self.maxpool(out)
        out = self.residual_blocks(out)
        out = out.mean(dim=2)  # 全局平均池化
        out = self.fc(out)
        return out


class BI_GRU(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers=1):
        super(BI_GRU, self).__init__()
        self.bi_gru = nn.GRU(input_size, hidden_size, num_layers, batch_first=True, bidirectional=True)

    def forward(self, x):
        out, _ = self.bi_gru(x)
        return out


class TransformerEncoder(nn.Module):
    def __init__(self, input_dim, model_dim, n_heads, n_layers):
        super(TransformerEncoder, self).__init__()
        self.embedding = nn.Linear(input_dim, model_dim)
        self.pos_encoder = nn.Embedding(5000, model_dim)
        self.transformer_encoder = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d_model=model_dim, nhead=n_heads),
            num_layers=n_layers
        )

    def forward(self, x):
        x = self.embedding(x)
        x = self.pos_encoder(torch.arange(0, x.size(1)).unsqueeze(0).repeat(x.size(0), 1).to(x.device))
        x = x + self.pos_encoder
        x = self.transformer_encoder(x)
        return x


