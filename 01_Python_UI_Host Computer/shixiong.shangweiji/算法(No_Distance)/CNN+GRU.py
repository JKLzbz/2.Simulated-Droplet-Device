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

# 读取数据
df = pd.read_excel('data_1006.xlsx')
df
# %%
# 超参数设置
num_epochs = 150
learning_rate = 0.0001
test_size = 0.2
batch_size = 64
hidden_size = 64  # GRU的隐藏层大小
# %%
# 假设最后一列为标签
X = df.iloc[:, :-1].values  # 特征列
y = df.iloc[:, -1].values  # 标签列

# 标签需要转为整数格式
y = pd.Categorical(y).codes

# 数据标准化
scaler = StandardScaler()
X = scaler.fit_transform(X)

# 划分训练集和验证集 (80%训练，20%验证)
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=test_size, random_state=42)

# 转换为PyTorch张量
X_train_tensor = torch.tensor(X_train, dtype=torch.float32)
y_train_tensor = torch.tensor(y_train, dtype=torch.long)
X_val_tensor = torch.tensor(X_val, dtype=torch.float32)
y_val_tensor = torch.tensor(y_val, dtype=torch.long)
# %%
# 创建数据集和数据加载器
train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
val_dataset = TensorDataset(X_val_tensor, y_val_tensor)

train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

print('训练集样本数:', len(train_dataset))
print('验证集样本数:', len(val_dataset))


# %%
class CNN_GRU(nn.Module):
    
    def __init__(self, input_size, num_classes, hidden_size, num_layers=1):
        super(CNN_GRU, self).__init__()
        # CNN部分
        self.conv1 = nn.Conv1d(in_channels=1, out_channels=16, kernel_size=3, padding=1)
        self.conv2 = nn.Conv1d(in_channels=16, out_channels=32, kernel_size=3, padding=1)
        self.pool = nn.MaxPool1d(2)

        # GRU部分
        self.gru = nn.GRU(input_size=32, hidden_size=hidden_size, num_layers=num_layers, batch_first=True)

        # 全连接层
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        # CNN部分
        x = x.unsqueeze(1)  # (batch_size, 1, input_size)
        x = F.relu(self.conv1(x))  # (batch_size, 16, input_size)
        x = self.pool(x)  # (batch_size, 16, input_size // 2)
        x = F.relu(self.conv2(x))  # (batch_size, 32, input_size // 2)
        x = self.pool(x)  # (batch_size, 32, input_size // 4)

        # 调整维度以适应GRU的输入 (batch_size, sequence_length, input_size)
        x = x.permute(0, 2, 1)  # (batch_size, input_size // 4, 32)

        # GRU部分
        h0 = torch.zeros(1, x.size(0), hidden_size).to(x.device)  # 初始隐藏状态
        out, _ = self.gru(x, h0)  # out: (batch_size, seq_length, hidden_size)
        out = out[:, -1, :]  # 取最后一个时间步的输出

        # 全连接层
        out = self.fc(out)  # (batch_size, num_classes)
        return out


# %%
def train_model(model, train_loader, val_loader, criterion, optimizer, num_epochs=20):
    train_loss_history = []  # 训练损失历史记录
    val_loss_history = []  # 验证损失历史记录
    train_acc_history = []  # 训练准确率历史记录
    val_acc_history = []  # 验证准确率历史记录

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
                _, predicted = torch.max(outputs, 1)  # 获得预测结果
                total += labels.size(0)  # 累加总个数
                correct += (predicted == labels).sum().item()  # 累加正确个数

        val_loss = running_loss / len(val_loader)  # 计算当前epoch的平均损失
        val_acc = correct / total  # 计算当前epoch的准确率
        val_loss_history.append(val_loss)  # 记录当前epoch的损失
        val_acc_history.append(val_acc)  # 记录当前epoch的准确率

        print(
            f'Epoch [{epoch + 1}/{num_epochs}], Loss: {train_loss:.4f}, Acc: {train_acc:.4f}, Val_Loss: {val_loss:.4f}, Val_Acc: {val_acc:.4f}')

    return train_loss_history, val_loss_history, train_acc_history, val_acc_history


# %%
# 模型初始化
input_size = X_train.shape[1]
num_classes = len(np.unique(y))

model = CNN_GRU(input_size=input_size, num_classes=num_classes, hidden_size=hidden_size)

# 定义损失函数和优化器
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=learning_rate, weight_decay=0.0001)

# 训练模型
train_loss_history, val_loss_history, train_acc_history, val_acc_history = train_model(
    model, train_loader, val_loader, criterion, optimizer, num_epochs
)
# %%
# 可视化训练过程
epochs = range(1, num_epochs + 1)

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

# %%
# 保存模型
torch.save(model.state_dict(), 'cnn_gru_model.pth')
print("模型已保存为 cnn_gru_model.pth")


# %%
def evaluate_model(model, val_loader):
    model.eval()
    y_true = []
    y_pred = []
    total = 0
    correct = 0
    with torch.no_grad():
        for inputs, labels in val_loader:
            outputs = model(inputs)
            _, predicted = torch.max(outputs, 1)
            y_true.extend(labels.cpu().numpy())
            y_pred.extend(predicted.cpu().numpy())
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

    # 计算准确率
    accuracy = correct / total
    print(f'验证集上的准确率: {accuracy * 100:.2f}%')
    # 计算混淆矩阵
    cm = confusion_matrix(y_true, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm)
    # 打印分类报告
    print('\nClassification Report:')
    print(classification_report(y_true, y_pred))
    # 绘制混淆矩阵
    disp.plot(cmap=plt.cm.Blues)
    plt.title("Confusion Matrix")
    plt.show()


# 在验证集上评估并绘制混淆矩阵
evaluate_model(model, val_loader)

