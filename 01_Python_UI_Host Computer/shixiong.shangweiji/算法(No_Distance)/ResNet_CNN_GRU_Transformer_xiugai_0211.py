import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.nn import Mish
from data_pre_process0110 import process_data

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


class ECA_Attention(nn.Module):
    def __init__(self, channels, k_size=3):
        super(ECA_Attention, self).__init__()
        # 计算kernel_size的值
        self.avg_pool = nn.AdaptiveAvgPool1d(1)
        self.conv = nn.Conv1d(channels, channels, kernel_size=k_size, padding=(k_size - 1) // 2, bias=False)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        # 输入x的形状为(batch_size, channels, length)
        b, c, _ = x.size()
        y = self.avg_pool(x)  # 平均池化
        y = y.view(b, 1, c)  # 调整为(batch_size, 1, channels)
        y = self.conv(y)  # 1D卷积
        y = self.sigmoid(y)  # 通道加权系数
        return x * y  # 通道加权


# 残差块定义
class ResidualBlock(nn.Module):
    def __init__(self, in_channels, out_channels, stride=1, eca_k_size=3):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv1d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1)
        self.bn1 = nn.BatchNorm1d(out_channels)
        self.mish = Mish(inplace=True)  # 使用Mish代替ReLU
        self.conv2 = nn.Conv1d(out_channels, out_channels, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm1d(out_channels)

        # ECA模块
        self.eca = ECA_Attention(out_channels, k_size=eca_k_size)

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

        # 加入ECA通道注意力机制
        out = self.eca(out)  # 加权通道

        out += self.shortcut(x)  # 添加跳跃连接
        out = self.mish(out)  # 使用Mish
        return out


# 残差网络
class ResidualNetwork(nn.Module):
    def __init__(self, input_channels, out_channels, num_residual_layers, eca_k_size=3):
        super(ResidualNetwork, self).__init__()
        # 输入层(7*7卷积层+3*3最大池化层)
        self.conv1 = nn.Conv1d(input_channels, out_channels, kernel_size=7, stride=2, padding=3)
        self.bn1 = nn.BatchNorm1d(out_channels)
        self.mish = Mish(inplace=True)  # 使用Mish代替ReLU
        self.maxpool = nn.MaxPool1d(kernel_size=3, stride=2, padding=1)

        # 残差块
        self.residual_layers = self.make_residual_layers(out_channels, num_residual_layers, 2, eca_k_size)

        # 平均池化层
        self.avg_pool = nn.AdaptiveAvgPool1d(1)  # 自适应池化到1

    def make_residual_layers(self, input_channels, num_residual_layers, num_blocks_per_layer, eca_k_size):
        layers = []
        in_channels = input_channels
        for i in range(num_residual_layers):
            out_channels = in_channels if i == 0 else in_channels * 2
            layers.append(self.make_residual_block(in_channels, out_channels, num_blocks_per_layer, stride=2 if i > 0 else 1, eca_k_size=eca_k_size))
            in_channels = out_channels
        return nn.Sequential(*layers)

    def make_residual_block(self, in_channels, out_channels, num_blocks, stride, eca_k_size):
        layers = []
        layers.append(ResidualBlock(in_channels, out_channels, stride, eca_k_size))
        for _ in range(1, num_blocks):
            layers.append(ResidualBlock(out_channels, out_channels, eca_k_size=eca_k_size))
        return nn.Sequential(*layers)

    def forward(self, x):
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.mish(out)
        out = self.maxpool(out)
        out = self.residual_layers(out)
        out = self.avg_pool(out)
        out = out.squeeze(-1)  # 去掉最后一个维度
        # out = out.mean(dim=2)  # 全局平均池化
        return out


class BI_GRU(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, dropout_rate):
        super(BI_GRU, self).__init__()
        self.bi_gru = nn.GRU(input_size, hidden_size, num_layers, batch_first=True, bidirectional=True, dropout=dropout_rate)
        # self.fc = nn.Linear(hidden_size * 2, hidden_size * 2)  # 全连接层用于进一步处理特征(可以增加或去掉)

    def forward(self, x):
        # 输入x形状：(batch_size, input_channel, seq_length) -> 需要转换为 (batch_size, seq_length, input_channel)
        x = x.permute(0, 2, 1)
        out, _ = self.bi_gru(x)  # (batch_size, seq_length, 2*hidden_size)
        out = out.mean(dim=1)  # 对时间步进行平均池化 (batch_size, 2*hidden_size)
        # out = self.fc(out)  # 进一步处理特征（可以增加或去掉）
        return out


# 特征融合模块
class FeatureFusion(nn.Module):
    def __init__(self, resnet_dim, gru_dim, fusion_dim=256):
        super().__init__()
        self.resnet_fc = nn.Linear(resnet_dim, fusion_dim)
        self.gru_fc = nn.Linear(gru_dim, fusion_dim)
        self.layer_norm = nn.LayerNorm(fusion_dim)
        self.mish = Mish(inplace=True)  # 使用Mish代替ReLU

    def forward(self, res_feat, gru_feat):
        res_feat = self.mish(self.resnet_fc(res_feat))
        gru_feat = self.mish(self.gru_fc(gru_feat))
        fused = res_feat + gru_feat  # 特征相加融合
        return self.layer_norm(fused)


class TransformerEncoder(nn.Module):
    def __init__(self, d_model=256, num_heads=8, num_layers=2):
        super().__init__()
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=num_heads,
            dim_feedforward=d_model * 4,
            activation='relu'
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.pos_embedding = nn.Parameter(torch.randn(1, 1, d_model))

    def forward(self, x):
        # x形状: (batch_size, fusion_dim)
        x = x.unsqueeze(1)  # (batch_size, 1, fusion_dim)
        x = x + self.pos_embedding
        return self.transformer(x).squeeze(1)


class Classifier(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_classes):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.mish = Mish()
        self.dropout = nn.Dropout(0.3)
        self.fc2 = nn.Linear(hidden_dim, num_classes)

    def forward(self, x):
        x = self.mish(self.fc1(x))
        x = self.dropout(x)
        x = self.fc2(x)
        return x


# 主模型
class CombinedModel(nn.Module):
    def __init__(self, input_channels, out_channels, num_residual_layers, gru_input_size, gru_hidden_size, gru_num_layers, gru_dropout_rate):
        super(CombinedModel, self).__init__()
        self.residual_network = ResidualNetwork(input_channels, out_channels, num_residual_layers)
        self.bi_gru = BI_GRU(gru_input_size, gru_hidden_size, gru_num_layers, gru_dropout_rate)
        # 特征融合
        self.fusion = FeatureFusion(
            resnet_dim=out_channels * (2 ** (num_residual_layers - 1)),
            gru_dim=gru_hidden_size * 2,
            fusion_dim=256
        )
        # Transformer编码器
        self.transformer = TransformerEncoder(d_model=256)
        # 分类层
        self.classifier = Classifier(input_dim=256, hidden_dim=128, num_classes=4)

    def forward(self, x):
        res_features = self.residual_network(x)
        gru_features = self.bi_gru(x)
        fused_features = self.fusion(res_features, gru_features)
        trans_features = self.transformer(fused_features)
        out = self.classifier(trans_features)
        return out


# 麻雀优化算法
class SparrowSearchAlgorithm:
    def __init__(self, n_sparrows, n_iter, bounds):
        self.n_sparrows = n_sparrows
        self.n_iter = n_iter
        self.bounds = bounds
        self.sparrows = np.random.uniform(bounds[0], bounds[1], (n_sparrows, len(bounds[0])))
        self.best_sparrow = None
        self.best_fitness = float('inf')

    def optimize(self, fitness_func):
        for i in range(self.n_iter):
            for j in range(self.n_sparrows):
                fitness = fitness_func(self.sparrows[j])
                if fitness < self.best_fitness:
                    self.best_fitness = fitness
                    self.best_sparrow = self.sparrows[j]
            self.sparrows = self.update_sparrows()
        return self.best_sparrow

    def update_sparrows(self):
        new_sparrows = np.zeros_like(self.sparrows)
        for i in range(self.n_sparrows):
            new_sparrows[i] = self.sparrows[i] + np.random.uniform(-1, 1, len(self.bounds[0])) * (self.best_sparrow - self.sparrows[i])
            new_sparrows[i] = np.clip(new_sparrows[i], self.bounds[0], self.bounds[1])
        return new_sparrows


def main():
    process_data('data_sheet.csv', 32)


if __name__ == "__main__":
    main()

