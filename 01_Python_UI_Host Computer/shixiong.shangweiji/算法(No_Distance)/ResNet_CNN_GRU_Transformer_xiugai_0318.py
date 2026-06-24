import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from matplotlib import pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
from torch.nn import Mish
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torchinfo import summary

from data_pre_process0110 import process_data

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


class ECA_Attention(nn.Module):
    def __init__(self, channels, k_size=3):
        super(ECA_Attention, self).__init__()
        # 计算kernel_size的值
        self.avg_pool = nn.AdaptiveAvgPool1d(1)
        self.conv = nn.Conv1d(channels, channels, kernel_size=k_size, padding=(k_size - 1) // 2, bias=False)
        self.sigmoid = nn.Sigmoid()
        # 初始化卷积层权重
        self._init_weights()

    def _init_weights(self):
        # 使用 Xavier 初始化
        nn.init.xavier_normal_(self.conv.weight)

    def forward(self, x):
        # 输入x的形状为(batch_size, channels, length)
        b, c, _ = x.size()
        y = self.avg_pool(x)  # 平均池化
        y = y.view(b, c, 1)  # 调整为(batch_size, channels, 1)
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

        # 参数初始化
        self._init_weights()

    def _init_weights(self):
        # 使用 Xavier 初始化卷积层权重
        for conv in [self.conv1, self.conv2]:
            nn.init.xavier_normal_(conv.weight)
        # 初始化 BatchNorm 层的权重和偏置
        nn.init.constant_(self.bn1.weight, 1)
        nn.init.constant_(self.bn1.bias, 0)
        nn.init.constant_(self.bn2.weight, 1)
        nn.init.constant_(self.bn2.bias, 0)
        # 初始化跳跃连接的卷积层（如果存在）
        if isinstance(self.shortcut, nn.Sequential):
            for layer in self.shortcut:
                if isinstance(layer, nn.Conv1d):
                    nn.init.xavier_normal_(layer.weight)
                elif isinstance(layer, nn.BatchNorm1d):
                    nn.init.constant_(layer.weight, 1)
                    nn.init.constant_(layer.bias, 0)

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
        # 输入层(7*1卷积层+3*1最大池化层)
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
        # out = out.squeeze(-1)  # 去掉最后一个维度
        out = out.view(out.size(0), -1)  # 正确展平操作 [B, C]
        # out = out.mean(dim=2)  # 全局平均池化
        return out


class Attention(nn.Module):
    def __init__(self, hidden_size):
        super(Attention, self).__init__()
        self.hidden_size = hidden_size
        self.attention_weights = nn.Parameter(torch.randn(hidden_size * 2, 1))  # 2*hidden_size because GRU is bidirectional
        # 初始化权重
        self._init_weights()

    def _init_weights(self):
        # 使用 Xavier/Glorot 初始化，适用于线性层和注意力权重
        nn.init.xavier_uniform_(self.attention_weights)

    def forward(self, gru_out):
        # gru_out shape: (batch_size, seq_length, 2 * hidden_size)
        attention_scores = torch.matmul(gru_out, self.attention_weights)  # (batch_size, seq_length, 1)
        attention_scores = attention_scores.squeeze(-1)  # (batch_size, seq_length)
        attention_weights = F.softmax(attention_scores, dim=1)  # Normalize the scores
        weighted_sum = torch.sum(gru_out * attention_weights.unsqueeze(-1), dim=1)  # (batch_size, 2 * hidden_size)
        # 对 GRU 输出进行加权平均(上下两段代码二选一)
        # weighted_sum = torch.bmm(attention_weights.unsqueeze(1), gru_out).squeeze(1)  # (batch_size, hidden_size * 2)
        return weighted_sum


class BI_GRU(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, dropout_rate):
        super(BI_GRU, self).__init__()
        self.bi_gru = nn.GRU(input_size, hidden_size, num_layers, batch_first=True, bidirectional=True, dropout=dropout_rate)
        self.attention = Attention(hidden_size)  # Adding attention layer
        # 初始化 GRU 的权重
        self._init_gru_weights()

    def _init_gru_weights(self):
        for name, param in self.bi_gru.named_parameters():
            if 'weight_ih' in name:
                # 输入到隐藏层的权重
                nn.init.xavier_uniform_(param.data)
            elif 'weight_hh' in name:
                # 隐藏层到隐藏层的权重
                nn.init.orthogonal_(param.data)
            elif 'bias' in name:
                # 偏置项初始化为 0
                nn.init.zeros_(param.data)

    def forward(self, x):
        # 输入x形状：(batch_size, input_channel, seq_length) -> 需要转换为 (batch_size, seq_length, input_channel)
        x = x.permute(0, 2, 1)
        out, _ = self.bi_gru(x)  # (batch_size, seq_length, 2*hidden_size)
        # Apply attention mechanism
        attention_out = self.attention(out)  # (batch_size, 2 * hidden_size)
        return attention_out


# # 特征融合模块
# class FeatureFusion(nn.Module): #原始的代码
#     def __init__(self, resnet_dim, gru_dim, fusion_dim=256):
#         super().__init__()
#         self.resnet_fc = nn.Sequential(
#             nn.Linear(resnet_dim, fusion_dim),
#             Mish(),
#             nn.Dropout(0.3))
#         self.gru_fc = nn.Sequential(
#             nn.Linear(gru_dim, fusion_dim),
#             Mish(),
#             nn.Dropout(0.3))
#         self.fusion_gate = nn.Sequential(
#             nn.Linear(fusion_dim*2, fusion_dim),
#             Mish(),
#             nn.Linear(fusion_dim, 2),
#             nn.Softmax(dim=1))
#         # 初始化权重
#         self._init_weights()
#
#     def _init_weights(self):
#         for m in self.modules():
#             if isinstance(m, nn.Linear):
#                 nn.init.xavier_uniform_(m.weight)
#                 if m.bias is not None:
#                     nn.init.constant_(m.bias, 0)
#
#     def forward(self, res_feat, gru_feat):
#         res_feat = self.resnet_fc(res_feat)
#         gru_feat = self.gru_fc(gru_feat)
#         combined = torch.cat([res_feat, gru_feat], dim=1)  # (B,fusion_dim*2)
#         gate = self.fusion_gate(combined)  # (B,2)
#         fused = gate[:, 0:1] * res_feat + gate[:, 1:2] * gru_feat  # (B,512)
#         return fused

class FeatureFusion(nn.Module):
    def __init__(self, resnet_dim, gru_dim, fusion_dim=256):
        super().__init__()
        # ResNet特征映射
        self.resnet_fc = nn.Sequential(
            nn.Linear(resnet_dim, fusion_dim),
            nn.LayerNorm(fusion_dim),  # 增加LayerNorm
            Mish(),
            nn.Dropout(0.3)
        )

        # GRU特征映射
        self.gru_fc = nn.Sequential(
            nn.Linear(gru_dim, fusion_dim),
            nn.LayerNorm(fusion_dim),
            Mish(),
            nn.Dropout(0.3)
        )

        # 交叉特征生成（双线性交互）
        self.cross_proj = nn.Sequential(
            nn.Linear(fusion_dim, fusion_dim * 2),  # 更高维映射
            Mish(),
            nn.Linear(fusion_dim * 2, fusion_dim),
            nn.LayerNorm(fusion_dim)
        )

        # 三权重门控网络（动态学习交叉特征权重）
        self.fusion_gate = nn.Sequential(
            nn.Linear(fusion_dim * 3, fusion_dim * 2),
            Mish(),
            nn.Linear(fusion_dim * 2, 3),  # 输出3个权重
            nn.Softmax(dim=1)
        )

    def forward(self, res_feat, gru_feat):
        # 特征映射
        res = self.resnet_fc(res_feat)  # (B,256)
        gru = self.gru_fc(gru_feat)  # (B,256)

        # 生成交叉特征
        cross = self.cross_proj(res * gru)  # (B,256)

        # 拼接所有特征
        combined = torch.cat([res, gru, cross], dim=1)  # (B,768)

        # 计算三权重门控
        gate = self.fusion_gate(combined)  # (B,3)

        # 加权融合（动态学习交叉特征贡献）
        fused = gate[:, 0:1] * res + gate[:, 1:2] * gru + gate[:, 2:3] * cross
        return fused


# class FeatureFusion(nn.Module): # 方案1增加交叉注意力层
#     def __init__(self, resnet_dim, gru_dim, fusion_dim=256):
#         super().__init__()
#         self.resnet_fc = nn.Sequential(
#             nn.Linear(resnet_dim, fusion_dim),
#             Mish(),
#             nn.Dropout(0.3))
#         self.gru_fc = nn.Sequential(
#             nn.Linear(gru_dim, fusion_dim),
#             Mish(),
#             nn.Dropout(0.3))
#         self.fusion_gate = nn.Sequential(
#             nn.Linear(fusion_dim * 2, fusion_dim),
#             Mish(),
#             nn.Linear(fusion_dim, 2),
#             nn.Softmax(dim=1))
#         # 新增交叉交互层
#         self.cross_interaction = nn.Sequential(
#             nn.Linear(fusion_dim * 2, fusion_dim),
#             Mish(),
#             nn.Dropout(0.3)
#         )
#         # 初始化权重
#         self._init_weights()
#
#     def _init_weights(self):
#         for m in self.modules():
#             if isinstance(m, nn.Linear):
#                 nn.init.xavier_uniform_(m.weight)
#                 if m.bias is not None:
#                     nn.init.constant_(m.bias, 0)
#
#     def forward(self, res_feat, gru_feat):
#         res_feat = self.resnet_fc(res_feat)  # (B,256)
#         gru_feat = self.gru_fc(gru_feat)  # (B,256)
#
#         # 新增交叉交互
#         cross_feat = self.cross_interaction(
#             torch.cat([res_feat, gru_feat], dim=1)  # (B,512)
#         )  # (B,256)
#
#         # 增强门控输入
#         combined = torch.cat([res_feat, gru_feat, cross_feat], dim=1)  # (B,768)
#         gate = self.fusion_gate(combined)  # (B,2)
#
#         # 残差连接保留原始信息
#         fused = gate[:, 0:1] * (res_feat + cross_feat) + gate[:, 1:2] * (gru_feat + cross_feat)
#         return fused


# class FeatureFusion(nn.Module):# 方案2增加多头注意力机制
#     def __init__(self, resnet_dim, gru_dim, fusion_dim=256):
#         super().__init__()
#         self.resnet_fc = nn.Sequential(
#             nn.Linear(resnet_dim, fusion_dim),
#             Mish(),
#             nn.Dropout(0.3))
#         self.gru_fc = nn.Sequential(
#             nn.Linear(gru_dim, fusion_dim),
#             Mish(),
#             nn.Dropout(0.3))
#         self.fusion_gate = nn.Sequential(
#             nn.Linear(fusion_dim*2, fusion_dim),
#             Mish(),
#             nn.Linear(fusion_dim, 2),
#             nn.Softmax(dim=1))
#         # 新增注意力交互
#         self.attention = nn.MultiheadAttention(
#             embed_dim=fusion_dim,
#             num_heads=4,  # 4头注意力
#             dropout=0.3
#         )
#         self.norm = nn.LayerNorm(fusion_dim)
#         # 初始化权重
#         self._init_weights()
#
#     def _init_weights(self):
#         for m in self.modules():
#             if isinstance(m, nn.Linear):
#                 nn.init.xavier_uniform_(m.weight)
#                 if m.bias is not None:
#                     nn.init.constant_(m.bias, 0)
#
#     def forward(self, res_feat, gru_feat):
#         res_feat = self.resnet_fc(res_feat)  # (B,256)
#         gru_feat = self.gru_fc(gru_feat)  # (B,256)
#
#         # 注意力交互
#         combined = torch.stack([res_feat, gru_feat], dim=1)  # (B,2,256)
#         attn_out, _ = self.attention(combined, combined, combined)  # (B,2,256)
#         attn_out = self.norm(combined + attn_out)  # 残差连接
#
#         # 分离特征
#         attn_res = attn_out[:, 0, :]  # (B,256)
#         attn_gru = attn_out[:, 1, :]  # (B,256)
#
#         # 门控融合
#         combined = torch.cat([attn_res, attn_gru], dim=1)  # (B,512)
#         gate = self.fusion_gate(combined)
#         fused = gate[:, 0:1] * attn_res + gate[:, 1:2] * attn_gru
#         return fused

class Classifier(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_classes):
        super().__init__()
        # 动态计算中间层数（hidden_dim≥128时用3层）
        self.layers = nn.ModuleList()
        self.layers.append(self._make_block(input_dim, hidden_dim))

        if hidden_dim >= 128:
            self.layers.append(self._make_block(hidden_dim, hidden_dim // 2))
            self.layers.append(self._make_block(hidden_dim // 2, hidden_dim // 4))
            final_dim = hidden_dim // 4
        else:
            self.layers.append(self._make_block(hidden_dim, hidden_dim // 2))
            final_dim = hidden_dim // 2

        # 最终分类层
        self.final_fc = nn.Linear(final_dim, num_classes)
        self._init_weights()

    def _make_block(self, in_dim, out_dim):
        """构建带残差连接的块"""
        return nn.Sequential(
            nn.Linear(in_dim, out_dim),
            nn.BatchNorm1d(out_dim),  # 添加BatchNorm
            Mish(),
            nn.Dropout(0.3)
        )

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='leaky_relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def forward(self, x):
        identity = x
        for i, layer in enumerate(self.layers):
            x = layer(x)
            # 添加残差连接（当维度匹配时）
            if i > 0 and x.shape == identity.shape:
                x = x + identity
                identity = x  # 更新identity用于下一层
        return self.final_fc(x)


# class Classifier(nn.Module):
#     def __init__(self, input_dim, hidden_dim, num_classes):
#         super().__init__()
#         self.fc1 = nn.Linear(input_dim, hidden_dim)
#         self.mish = Mish()
#         self.dropout = nn.Dropout(0.3)
#         self.fc2 = nn.Linear(hidden_dim, hidden_dim//2)
#         self.fc3 = nn.Linear(hidden_dim//2, num_classes)
#         self._init_weights()
#
#     def _init_weights(self):
#         for m in self.modules():
#             if isinstance(m, nn.Linear):
#                 nn.init.xavier_uniform_(m.weight)
#                 if m.bias is not None:
#                     nn.init.constant_(m.bias, 0)
#
#     # 多层感知机
#     def forward(self, x):
#         x = self.mish(self.fc1(x))
#         x = self.dropout(x)
#         x = self.mish(self.fc2(x))
#         x = self.dropout(x)
#         x = self.fc3(x)
#         return x


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
        # # Transformer编码器
        # self.transformer = TransformerEncoder(d_model=256)
        # 分类层
        self.classifier = Classifier(input_dim=256, hidden_dim=128, num_classes=4)

    def forward(self, x):
        res_features = self.residual_network(x)
        gru_features = self.bi_gru(x)
        fused_features = self.fusion(res_features, gru_features)
        # trans_features = self.transformer(fused_features)
        # out = self.classifier(trans_features)
        out = self.classifier(fused_features)
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


# 训练和评估函数
def train_model(model, train_loader, val_loader, criterion, optimizer, num_epochs):
    train_loss_history = []  # 训练损失历史记录
    train_acc_history = []  # 训练准确率历史记录
    val_loss_history = []  # 验证损失历史记录
    val_acc_history = []  # 验证准确率历史记录
    lr_history = []  # 学习率历史记录

    scheduler = ReduceLROnPlateau(
        optimizer,
        mode='max',  # 监控验证准确率
        patience=10,  # 10个epoch无改善后调整
        factor=0.5,  # 学习率衰减因子
        verbose=True  # 显示调整信息
    )
    best_val_acc = 0.0

    for epoch in range(num_epochs):
        model.train()
        total_loss = 0.0  # 当前epoch的损失总和
        correct = 0  # 当前epoch的正确个数
        total = 0  # 当前epoch的总个数

        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)  # 将输入数据、标签移动到指定的设备
            optimizer.zero_grad()  # 清除优化器的梯度缓存

            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()  # 反向传播
            nn.utils.clip_grad_norm_(model.parameters(), 5.0)  # 梯度裁剪
            optimizer.step()  # 更新参数

            total_loss += loss.item()
            _, predicted = torch.max(outputs, 1)  # 获得预测结果
            total += labels.size(0)  # 累加总个数
            correct += predicted.eq(labels).sum().item()  # 累加正确个数

        train_loss = total_loss / len(train_loader)  # 计算当前epoch的平均损失
        train_acc = correct / total  # 计算当前epoch的准确率
        train_loss_history.append(train_loss)  # 记录当前epoch的损失
        train_acc_history.append(train_acc)  # 记录当前epoch的准确率

        val_loss, val_acc = evaluate_model(model, val_loader, criterion)
        val_loss_history.append(val_loss)  # 记录当前 epoch 开始时的验证损失
        val_acc_history.append(val_acc)  # 记录当前 epoch 开始时的验证准确率
        scheduler.step(val_acc)

        # 记录当前学习率
        current_lr = optimizer.param_groups[0]['lr']
        lr_history.append(current_lr)

        print(f'Epoch [{epoch + 1}/{num_epochs}], Train_Loss: {train_loss:.4f} Train_Acc: {train_acc:.4f}, Val_Loss: {val_loss:.4f}, Val_Acc: {val_acc:.4f}', f'LR: {current_lr:.2e}')

        # 保存最佳模型
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), 'best_model.pth')

    print(f'Best Validation Accuracy: {best_val_acc:.4f}')
    return train_loss_history, val_loss_history, train_acc_history, val_acc_history, lr_history


def evaluate_model(model, data_loader, criterion):
    model.eval()
    val_running_loss, correct, total = 0.0, 0, 0
    with torch.no_grad():
        for inputs, labels in data_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            loss = criterion(outputs, labels)  # 计算损失
            val_running_loss += loss.item() # 累加损失
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
    val_loss = val_running_loss / len(data_loader)
    val_acc = correct / total
    return val_loss, val_acc


def draw_loss_acc(train_loss_history, val_loss_history, train_acc_history, val_acc_history):
    # %% 可视化训练过程
    epochs = range(1, len(train_loss_history) + 1)

    plt.figure(figsize=(12, 5))
    # Loss曲线
    plt.subplot(1, 2, 1)
    plt.plot(epochs, train_loss_history, 'b', label='Training loss')
    plt.plot(epochs, val_loss_history, 'r', label='Validation loss')
    plt.title('Training and Validation Loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()

    # 准确率曲线
    plt.subplot(1, 2, 2)
    plt.plot(epochs, train_acc_history, 'b', label='Training accuracy')
    plt.plot(epochs, val_acc_history, 'r', label='Validation accuracy')
    plt.title('Training and Validation Accuracy')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.show()


def test_model(model, test_loader):
    model.load_state_dict(torch.load('best_model.pth'))
    model.eval()
    all_predicts = []
    all_labels = []
    correct = 0
    total = 0
    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            _, predicted = torch.max(outputs, 1)
            all_predicts.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
    # 计算准确率
    accuracy = correct / total
    print(f'测试集上的准确率: {accuracy * 100:.4f}%')
    print("Test Classification Report:")
    print(classification_report(all_labels, all_predicts))
    # 计算混淆矩阵
    cm = confusion_matrix(all_labels, all_predicts)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm)
    disp.plot(cmap=plt.cm.Blues)
    plt.title("Confusion Matrix")
    plt.show()


def print_model_architecture(model, input_shapes):
    """打印完整模型结构信息"""
    print("\n" + "="*50)
    print("模型完整结构信息（含各层参数）")
    print("="*50)
    summary(model, input_shapes, depth=10)  # depth控制展开层级


def print_submodules_details(model):
    """打印各子模块参数详情"""
    print("\n" + "="*50)
    print("各子模块参数详细信息")
    print("="*50)
    for name, module in model.named_children():
        print(f"\n子模块: {name}")
        print("-"*50)
        for sub_name, sub_module in module.named_modules():
            if isinstance(sub_module, (nn.Conv1d, nn.Linear, nn.GRU)):
                print(f"  Layer: {sub_name}")
                print(f"  Type: {sub_module.__class__.__name__}")
                if isinstance(sub_module, nn.Conv1d):
                    print(f"  Kernel: {sub_module.kernel_size[0]}")
                    print(f"  Channels: {sub_module.in_channels}→{sub_module.out_channels}")
                elif isinstance(sub_module, nn.Linear):
                    print(f"  Units: {sub_module.in_features}→{sub_module.out_features}")
                elif isinstance(sub_module, nn.GRU):
                    print(f"  Hidden Size: {sub_module.hidden_size}")
                    print(f"  Layers: {sub_module.num_layers}")
                print(f"  Parameters: {sum(p.numel() for p in sub_module.parameters())}")
                print("-"*30)

def main():
    train_loader, val_loader, test_loader = process_data('data_sheet_0318.csv', 32)
    # 初始化模型
    model = CombinedModel(
        input_channels=3,
        out_channels=32,
        num_residual_layers=2,
        gru_input_size=3,
        gru_hidden_size=64,
        gru_num_layers=2,
        gru_dropout_rate=0.3
    ).to(device)

    # 打印模型结构信息
    print_model_architecture(model, (1, 3, 704))  # 输入形状为 (channels=3, seq_len=704)
    print_submodules_details(model)

    # 定义损失函数和优化器
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.0001, weight_decay=1e-3)
    # 训练模型
    train_loss, val_loss, train_acc, val_acc, lr_history = train_model(model, train_loader, val_loader, criterion, optimizer, 100)
    # 保存训练结果到Excel（新增部分）
    df = pd.DataFrame({
        'Train Loss': train_loss,
        'Validation Loss': val_loss,
        'Train Accuracy': train_acc,
        'Validation Accuracy': val_acc,
        'Learning Rate': lr_history
    })
    df.to_excel('training_results.xlsx', index=False)
    draw_loss_acc(train_loss, val_loss, train_acc, val_acc)
    # 测试模型
    test_model(model, test_loader)


if __name__ == "__main__":
    main()

