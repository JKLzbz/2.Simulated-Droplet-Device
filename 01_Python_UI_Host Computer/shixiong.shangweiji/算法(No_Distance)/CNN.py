# %%
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, classification_report
from data_pre_process0110 import process_data

# 超参数设置
num_epochs = 150
learning_rate = 0.0005
test_size = 0.3  # 验证集与测试集总比例
val_size = 0.5  # 验证集比例
random_seed = 42  # 随机种子，用于结果复现
batch_size = 64
dropout_rate = 0.2  # Dropout 概率调整
weight_decay = 0.0001  # L2正则化的权重衰减


# %% 模型定义，增加Dropout和简化模型架构
class CNN1D(nn.Module):
    def __init__(self, in_channel=3, num_classes=4, dropout_rate=0.5, input_size=704):
        super(CNN1D, self).__init__()
        # 第一层卷积层
        self.conv1 = nn.Conv1d(in_channels=in_channel, out_channels=32, kernel_size=3, padding=1)
        # 第二层卷积层
        self.conv2 = nn.Conv1d(in_channels=32, out_channels=64, kernel_size=3, padding=1)
        # 第三层卷积层
        self.conv3 = nn.Conv1d(in_channels=64, out_channels=128, kernel_size=3, padding=1)

        # 最大池化层
        self.pool = nn.MaxPool1d(kernel_size=2, stride=2)

        # 全连接层
        self.fc1 = nn.Linear(128 * (704 // 8), 128)  # 假设池化操作缩小了8倍
        self.fc2 = nn.Linear(128, num_classes)

        # Dropout层
        self.dropout = nn.Dropout(p=dropout_rate)

    def forward(self, x):
        # 第一层卷积 + ReLU + 池化
        x = F.relu(self.conv1(x))
        x = self.pool(x)

        # 第二层卷积 + ReLU + 池化
        x = F.relu(self.conv2(x))
        x = self.pool(x)

        # 第三层卷积 + ReLU + 池化
        x = F.relu(self.conv3(x))
        x = self.pool(x)

        # 展平操作
        x = x.view(x.size(0), -1)

        # 第一个全连接层 + ReLU + Dropout
        x = F.relu(self.fc1(x))
        x = self.dropout(x)

        # 第二个全连接层
        x = self.fc2(x)
        return x


# %% 训练函数
def train_model(model, train_loader, val_loader, criterion, optimizer, num_epochs=80, early_stopping_patience=10):
    """
    训练模型

    :param model: 模型
    :param train_loader: 训练集数据加载器
    :param val_loader: 验证集数据加载器
    :param criterion: 损失函数
    :param optimizer: 优化器
    :param num_epochs: 训练轮数，default=20
    :return: 训练损失、验证损失、训练准确率、验证准确率的历史记录
    """
    train_loss_history = []  # 训练损失历史记录
    val_loss_history = []  # 验证损失历史记录
    train_acc_history = []  # 训练准确率历史记录
    val_acc_history = []  # 验证准确率历史记录

    best_val_loss = float('inf')
    epochs_no_improve = 0  # 用于早停

    # 训练模型
    for epoch in range(num_epochs):
        model.train()  # 设置模型为训练模式
        running_loss = 0.0  # 当前epoch的损失总和
        correct = 0  # 当前epoch的正确个数
        total = 0  # 当前epoch的总个数

        # 训练阶段
        for inputs, labels in train_loader:
            optimizer.zero_grad()  # 清除优化器的梯度缓存
            outputs = model(inputs)  # 前向传播
            loss = criterion(outputs, labels)  # 计算损失
            loss.backward()  # 反向传播
            optimizer.step()  # 更新参数

            running_loss += loss.item()  # 累加损失
            _, predicted = torch.max(outputs, 1)  # 获得预测结果
            total += labels.size(0)  # 累加总个数
            correct += (predicted == labels).sum().item()  # 累加正确个数

        train_loss = running_loss / len(train_loader)  # 计算当前epoch的平均损失
        train_acc = correct / total  # 计算当前epoch的准确率
        train_loss_history.append(train_loss)  # 记录当前epoch的损失
        train_acc_history.append(train_acc)  # 记录当前epoch的准确率

        # 验证阶段
        model.eval()  # 设置模型为评估模式
        running_loss = 0.0  # 当前epoch的损失总和
        correct = 0  # 当前epoch的正确个数
        total = 0  # 当前epoch的总个数
        with torch.no_grad():  # 不计算梯度
            for inputs, labels in val_loader:
                outputs = model(inputs)  # 前向传播
                loss = criterion(outputs, labels)  # 计算损失
                running_loss += loss.item()  # 累加损失
                _, predicted = torch.max(outputs, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

        val_loss = running_loss / len(val_loader)
        val_acc = correct / total
        val_loss_history.append(val_loss)
        val_acc_history.append(val_acc)

        print(
            f'Epoch [{epoch + 1}/{num_epochs}], Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.4f}, Val_Loss: {val_loss:.4f}, Val_Acc: {val_acc:.4f}')

        # 早停法
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1

        if epochs_no_improve == early_stopping_patience:
            print(f'早停触发！在第 {epoch + 1} 轮停止训练。')
            break

    return train_loss_history, val_loss_history, train_acc_history, val_acc_history


train_loader, val_loader, test_loader = process_data('data_sheet.csv', 32)
# %% 模型初始化

model = CNN1D( in_channel=3, num_classes=4, dropout_rate=dropout_rate, input_size=704)

# 定义损失函数和优化器
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=learning_rate, weight_decay=weight_decay)

# 训练模型
train_loss_history, val_loss_history, train_acc_history, val_acc_history = train_model(
    model, train_loader, val_loader, criterion, optimizer, num_epochs, early_stopping_patience=20
)

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


# %% 混淆矩阵
def evaluate_model(model, test_loader):
    model.eval()
    y_true = []
    y_pred = []
    correct = 0
    total = 0
    with torch.no_grad():
        for inputs, labels in test_loader:
            outputs = model(inputs)
            _, predicted = torch.max(outputs, 1)
            y_true.extend(labels.cpu().numpy())
            y_pred.extend(predicted.cpu().numpy())
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    # 计算准确率
    accuracy = correct / total
    print(f'测试集上的准确率: {accuracy * 100:.4f}%')
    # 计算混淆矩阵
    cm = confusion_matrix(y_true, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm)
    disp.plot(cmap=plt.cm.Blues)
    plt.title("Confusion Matrix")
    plt.show()

    # 打印分类报告
    print('\nClassification Report:')
    print(classification_report(y_true, y_pred))


evaluate_model(model, test_loader)

# %% 保存模型
torch.save(model.state_dict(), 'cnn_model.pth')
print("模型已保存为 cnn_model.pth")
