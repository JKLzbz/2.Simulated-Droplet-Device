import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from matplotlib import pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
from torch.nn import Mish
from torch.nn.utils import weight_norm
from torch.optim.lr_scheduler import ReduceLROnPlateau

from signal_data_process import process_data

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


class TCN(nn.Module):
    def __init__(self, input_size, num_channels, kernel_size, dropout_rate, num_classes):
        """
        Args:
            input_size (int): 输入特征的维度（通道数）
            num_channels (list): 各层的通道数，例如 [64, 64, 64] 表示 3 层 TCN，每层 64 通道
            kernel_size (int): 卷积核大小
            dropout_rate (float): Dropout 概率
            num_classes (int): 分类类别数
        """
        super(TCN, self).__init__()
        self.tcn = nn.Sequential(
            TemporalBlock(
                input_size,
                num_channels[0],
                kernel_size,
                stride=1,
                dilation=1,
                dropout=dropout_rate
            ),
            *[TemporalBlock(
                num_channels[i-1],
                num_channels[i],
                kernel_size,
                stride=1,
                dilation=2**i,  # 扩张率按指数增长（1, 2, 4, ...）
                dropout=dropout_rate
            ) for i in range(1, len(num_channels))]
        )
        self.fc = nn.Linear(num_channels[-1], num_classes)
        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv1d):
                nn.init.kaiming_normal_(m.weight, nonlinearity='relu')
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, x):
        # 输入形状: [batch_size, input_channels, seq_length]
        out = self.tcn(x)  # [batch_size, num_channels[-1], seq_length]
        out = out.mean(dim=2)  # 沿时间维度全局平均池化 [batch_size, num_channels[-1]]
        out = self.fc(out)
        return out


class TemporalBlock(nn.Module):
    """TCN 基本块（含残差连接）"""

    def __init__(self, in_channels, out_channels, kernel_size, stride, dilation, dropout):
        super(TemporalBlock, self).__init__()
        padding = (kernel_size - 1) * dilation  # 因果卷积所需的左侧填充量
        self.pad = nn.ConstantPad1d((padding, 0), 0)  # 仅在左侧填充

        # 移除 Conv1d 的 padding 参数，改为手动填充
        self.conv1 = weight_norm(nn.Conv1d(
            in_channels,
            out_channels,
            kernel_size,
            stride=stride,
            dilation=dilation
        ))
        self.conv2 = weight_norm(nn.Conv1d(
            out_channels,
            out_channels,
            kernel_size,
            stride=stride,
            dilation=dilation
        ))
        self.downsample = nn.Conv1d(in_channels, out_channels, 1) if in_channels != out_channels else None
        self.dropout = nn.Dropout(dropout)
        self.activation = Mish()

    def forward(self, x):
        residual = x
        # 手动左侧填充
        x_padded = self.pad(x)
        # 第一层卷积 + 激活
        out = self.conv1(x_padded)
        out = self.activation(out)
        out = self.dropout(out)
        # 第二层卷积 + 激活
        out_padded = self.pad(out)  # 第二层卷积前同样需要填充
        out = self.conv2(out_padded)
        out = self.activation(out)
        out = self.dropout(out)
        # 残差连接
        if self.downsample is not None:
            residual = self.downsample(residual)
        return self.activation(residual + out)

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
            torch.save(model.state_dict(), 'TCN_best_model.pth')

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
    model.load_state_dict(torch.load('TCN_best_model.pth'))
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
    model = TCN(
        input_size=1,  # 输入特征维度（通道数）
        num_channels=[64, 64],  # 2 层 TCN，每层 64 通道
        kernel_size=3,  # 卷积核大小（推荐 3 或 5）
        dropout_rate=0.2,  # Dropout 概率
        num_classes=4
    ).to(device)
    # 定义损失函数和优化器
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-3)
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
    df.to_excel('TCN_training_results.xlsx', index=False)
    draw_loss_acc(train_loss, val_loss, train_acc, val_acc)
    # 测试模型
    test_model(model, test_loader)


if __name__ == "__main__":
    main()