import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.nn import Mish
from data_pre_process0110 import process_data

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


# 残差块定义
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


# 残差网络
class ResidualNetwork(nn.Module):
    def __init__(self, input_channels, out_channels, num_residual_layers):
        super(ResidualNetwork, self).__init__()
        # 输入层(7*7卷积层+3*3最大池化层)
        self.conv1 = nn.Conv1d(input_channels, out_channels, kernel_size=7, stride=2, padding=3)
        self.bn1 = nn.BatchNorm1d(out_channels)
        self.mish = Mish(inplace=True)  # 使用Mish代替ReLU
        self.maxpool = nn.MaxPool1d(kernel_size=3, stride=2, padding=1)

        # 残差块
        self.residual_layers = self.make_residual_layers(out_channels, num_residual_layers, 2)

        # 平均池化层
        self.avg_pool = nn.AdaptiveAvgPool1d(1)  # 自适应池化到1

    def make_residual_layers(self, input_channels, num_residual_layers, num_blocks_per_layer):
        layers = []
        in_channels = input_channels
        for i in range(num_residual_layers):
            out_channels = in_channels if i == 0 else in_channels * 2
            layers.append(self.make_residual_block(in_channels, out_channels, num_blocks_per_layer, stride=2 if i > 0 else 1))
            in_channels = out_channels
        return nn.Sequential(*layers)

    def make_residual_block(self, in_channels, out_channels, num_blocks, stride):
        layers = []
        layers.append(ResidualBlock(in_channels, out_channels, stride))
        for _ in range(1, num_blocks):
            layers.append(ResidualBlock(out_channels, out_channels))
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

    def forward(self, x):
        # 输入x形状：(batch_size, input_channel, seq_length) -> 需要转换为 (batch_size, seq_length, input_channel)
        x = x.permute(0, 2, 1)
        out, _ = self.bi_gru(x)  # (batch_size, seq_length, 2H)
        out = out.mean(dim=1)  # 对时间步进行平均池化 (batch_size, 2H)
        return out


# 特征融合模块一
class FeatureFusionModule(nn.Module):
    def __init__(self, input_size_1, input_size_2, output_size):
        super(FeatureFusionModule, self).__init__()
        self.fc1 = nn.Linear(input_size_1, output_size)
        self.fc2 = nn.Linear(input_size_2, output_size)
        self.fc3 = nn.Linear(output_size * 2, output_size)  # 融合后的特征

    def forward(self, x1, x2):
        x1 = self.fc1(x1)
        x2 = self.fc2(x2)
        fused = torch.cat([x1, x2], dim=1)
        fused = self.fc3(fused)
        return fused

# # 特征融合模块二
# class FeatureFusion(nn.Module):
#     def __init__(self, resnet_dim, gru_dim, fusion_dim=256):
#         super().__init__()
#         self.resnet_fc = nn.Linear(resnet_dim, fusion_dim)
#         self.gru_fc = nn.Linear(gru_dim, fusion_dim)
#         self.layer_norm = nn.LayerNorm(fusion_dim)
#         self.mish = Mish(inplace=True)  # 使用Mish代替ReLU
#
#     def forward(self, res_feat, gru_feat):
#         res_feat = self.mish(self.resnet_fc(res_feat))
#         gru_feat = self.mish(self.gru_fc(gru_feat))
#         fused = res_feat + gru_feat  # 特征相加融合
#         return self.layer_norm(fused)


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
        pos = self.pos_encoder(torch.arange(0, x.size(1)).unsqueeze(0).repeat(x.size(0), 1).to(x.device))
        x = x + pos
        x = self.transformer_encoder(x)
        x = x.mean(dim=1)  # 对时间步进行平均池化
        return x


# 主模型
class CombinedModel(nn.Module):
    def __init__(self, input_channels, out_channels, num_residual_layers, gru_input_size, gru_hidden_size, gru_num_layers, gru_dropout_rate):
        super(CombinedModel, self).__init__()
        self.residual_network = ResidualNetwork(input_channels, out_channels, num_residual_layers)
        self.bi_gru = BI_GRU(gru_input_size, gru_hidden_size, gru_num_layers, gru_dropout_rate)
        self.fusion = FeatureFusionModule(out_channels, gru_hidden_size * 2, 128)  # 融合特征
        # self.fusion = FeatureFusionModule(out_channels, gru_hidden_size * 2, 128)  # 融合特征
        self.fc = nn.Linear(128, 4)  # 最终分类层，假设分类数量为4

    def forward(self, x_res, x_gru):
        res_features = self.residual_network(x_res)
        gru_features = self.bi_gru(x_gru)
        gru_features = gru_features.mean(dim=1)  # 对GRU输出做池化处理
        fused_features = self.fusion(res_features, gru_features)
        out = self.fc(fused_features)
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

