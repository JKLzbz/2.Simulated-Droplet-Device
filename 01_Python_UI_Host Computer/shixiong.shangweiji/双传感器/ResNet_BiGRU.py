import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from matplotlib import pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
from torch.nn import Mish
from torch.optim.lr_scheduler import ReduceLROnPlateau

from double_data_process import process_data

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


# 修改后的残差块（移除ECA）
class ResidualBlock(nn.Module):
    def __init__(self, in_channels, out_channels, stride=1):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv1d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1)
        self.bn1 = nn.BatchNorm1d(out_channels)
        self.mish = Mish(inplace=True)
        self.conv2 = nn.Conv1d(out_channels, out_channels, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm1d(out_channels)

        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv1d(in_channels, out_channels, kernel_size=1, stride=stride),
                nn.BatchNorm1d(out_channels))

            self._init_weights()

    def _init_weights(self):
        for conv in [self.conv1, self.conv2]:
            nn.init.xavier_normal_(conv.weight)
        nn.init.constant_(self.bn1.weight, 1)
        nn.init.constant_(self.bn1.bias, 0)
        nn.init.constant_(self.bn2.weight, 1)
        nn.init.constant_(self.bn2.bias, 0)
        for layer in self.shortcut:
            if isinstance(layer, nn.Conv1d):
                nn.init.xavier_normal_(layer.weight)
            elif isinstance(layer, nn.BatchNorm1d):
                nn.init.constant_(layer.weight, 1)
                nn.init.constant_(layer.bias, 0)

    def forward(self, x):
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.mish(out)
        out = self.conv2(out)
        out = self.bn2(out)
        out += self.shortcut(x)  # 直接相加
        out = self.mish(out)
        return out


# 修改后的残差网络（移除ECA相关参数）
class ResidualNetwork(nn.Module):
    def __init__(self, input_channels, out_channels, num_residual_layers):
        super(ResidualNetwork, self).__init__()
        self.conv1 = nn.Conv1d(input_channels, out_channels, kernel_size=7, stride=2, padding=3)
        self.bn1 = nn.BatchNorm1d(out_channels)
        self.mish = Mish(inplace=True)
        self.maxpool = nn.MaxPool1d(kernel_size=3, stride=2, padding=1)
        self.residual_layers = self.make_residual_layers(out_channels, num_residual_layers, 2)
        self.avg_pool = nn.AdaptiveAvgPool1d(1)

    def make_residual_layers(self, input_channels, num_residual_layers, num_blocks_per_layer):
        layers = []
        in_channels = input_channels
        for i in range(num_residual_layers):
            out_channels = in_channels if i == 0 else in_channels * 2
            layers.append(
                self.make_residual_block(in_channels, out_channels, num_blocks_per_layer, stride=2 if i > 0 else 1))
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
        return out.squeeze(-1)


# 修改后的Bi-GRU（移除注意力机制）
class BI_GRU(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, dropout_rate):
        super(BI_GRU, self).__init__()
        self.bi_gru = nn.GRU(input_size, hidden_size, num_layers,
                             batch_first=True, bidirectional=True, dropout=dropout_rate)
        self._init_gru_weights()

    def _init_gru_weights(self):
        for name, param in self.bi_gru.named_parameters():
            if 'weight_ih' in name:
                nn.init.xavier_uniform_(param.data)
            elif 'weight_hh' in name:
                nn.init.orthogonal_(param.data)
            elif 'bias' in name:
                nn.init.zeros_(param.data)

    def forward(self, x):
        x = x.permute(0, 2, 1)
        out, _ = self.bi_gru(x)
        # 使用均值池化代替注意力
        return out.mean(dim=1)


# 特征融合模块
class FeatureFusion(nn.Module):
    def __init__(self, resnet_dim, gru_dim, fusion_dim=256):
        super().__init__()
        self.resnet_fc = nn.Sequential(
            nn.Linear(resnet_dim, fusion_dim),
            Mish(),
            nn.Dropout(0.3))
        self.gru_fc = nn.Sequential(
            nn.Linear(gru_dim, fusion_dim),
            Mish(),
            nn.Dropout(0.3))
        self.fusion_gate = nn.Sequential(
            nn.Linear(fusion_dim*2, fusion_dim),
            Mish(),
            nn.Linear(fusion_dim, 2),
            nn.Softmax(dim=1))
        # 初始化权重
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def forward(self, res_feat, gru_feat):
        res_feat = self.resnet_fc(res_feat)
        gru_feat = self.gru_fc(gru_feat)
        combined = torch.cat([res_feat, gru_feat], dim=1)  # (B,fusion_dim*2)
        gate = self.fusion_gate(combined)  # (B,2)
        fused = gate[:, 0:1] * res_feat + gate[:, 1:2] * gru_feat  # (B,512)
        return fused


# class TransformerEncoder(nn.Module):
#     def __init__(self, d_model=256, num_heads=8, num_layers=2):
#         super().__init__()
#         encoder_layer = nn.TransformerEncoderLayer(
#             d_model=d_model,
#             nhead=num_heads,
#             dim_feedforward=d_model * 4,
#             activation='relu'
#         )
#         self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
#         self.pos_embedding = nn.Parameter(torch.randn(1, 1, d_model))
#
#     def forward(self, x):
#         # x形状: (batch_size, fusion_dim)
#         x = x.unsqueeze(1)  # (batch_size, 1, fusion_dim)
#         x = x + self.pos_embedding
#         return self.transformer(x).squeeze(1)


class Classifier(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_classes):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.mish = Mish()
        self.dropout = nn.Dropout(0.3)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim//2)
        self.fc3 = nn.Linear(hidden_dim//2, num_classes)
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    # 多层感知机
    def forward(self, x):
        x = self.mish(self.fc1(x))
        x = self.dropout(x)
        x = self.mish(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
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
def train_model(model, train_loader, val_loader, criterion, optimizer, num_epochs, early_stopping_patience):
    train_loss_history = []  # 训练损失历史记录
    train_acc_history = []  # 训练准确率历史记录
    val_loss_history = []  # 验证损失历史记录
    val_acc_history = []  # 验证准确率历史记录

    scheduler = ReduceLROnPlateau(optimizer, 'max', patience=early_stopping_patience // 2)
    epochs_no_improve = 0  # 用于早停

    best_val_acc = 0.0


    for epoch in range(num_epochs):
        val_loss, val_acc = evaluate_model(model, val_loader, criterion)
        val_loss_history.append(val_loss)  # 记录当前 epoch 开始时的验证损失
        val_acc_history.append(val_acc)  # 记录当前 epoch 开始时的验证准确率
        scheduler.step(val_acc)

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

            total_loss += loss.item() #* inputs.size(0)
            _, predicted = torch.max(outputs, 1)  # 获得预测结果
            total += labels.size(0)  # 累加总个数
            correct += predicted.eq(labels).sum().item()  # 累加正确个数

        train_loss = total_loss / len(train_loader)  # 计算当前epoch的平均损失
        train_acc = correct / total  # 计算当前epoch的准确率
        train_loss_history.append(train_loss)  # 记录当前epoch的损失
        train_acc_history.append(train_acc)  # 记录当前epoch的准确率



        print(f'Epoch [{epoch + 1}/{num_epochs}], Train_Loss: {train_loss:.4f} Train_Acc: {train_acc:.4f}, Val_Loss: {val_loss:.4f} Val_Acc: {val_acc:.4f}')

        # 保存最佳模型
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), 'Res_1DCNN_BiGRU_best_model.pth')
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= early_stopping_patience:
                print("Early stopping!")
                break
    print(f'Best Validation Accuracy: {best_val_acc:.4f}')
    return train_loss_history, val_loss_history, train_acc_history, val_acc_history


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
    model.load_state_dict(torch.load('Res_1DCNN_BiGRU_best_model.pth'))
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
    print(classification_report(all_labels, all_predicts, digits=4, zero_division=0))
    # 计算混淆矩阵
    cm = confusion_matrix(all_labels, all_predicts)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm)
    disp.plot(cmap=plt.cm.Blues)
    plt.title("Confusion Matrix")
    plt.show()


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
    # 定义损失函数和优化器
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.0005, weight_decay=1e-2)
    # 训练模型
    train_loss_history, val_loss_history, train_acc_history, val_acc_history = train_model(model, train_loader, val_loader, criterion, optimizer, 100, 30)
    df = pd.DataFrame({
        'Train Loss': train_loss_history,
        'Validation Loss': val_loss_history,
        'Train Accuracy': train_acc_history,
        'Validation Accuracy': val_acc_history
    })
    df.to_excel('Res_1DCNN_BiGRU_training_results.xlsx', index=False)

    draw_loss_acc(train_loss_history, val_loss_history, train_acc_history, val_acc_history)
    # 测试模型
    test_model(model, test_loader)



if __name__ == "__main__":
    main()

