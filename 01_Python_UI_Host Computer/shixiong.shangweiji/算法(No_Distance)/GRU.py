#%%
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from data_pre_process0110 import process_data


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


class Params:
    # 数据参数
    data_file = 'data_1006.xlsx'  # 数据文件名
    batch_size = 64  # 批次大小
    test_size = 0.3  # 测试集比例
    val_size = 0.5  # 验证集比例（相对于剩余数据）

    # 模型参数
    input_size = 704  # 输入特征维度
    hidden_size = 128  # GRU隐藏层大小
    num_layers = 2  # GRU层数
    num_classes = 4  # 分类类别数
    dropout = 0.5  # Dropout比率

    # 训练参数
    num_epochs = 100  # 训练轮数
    learning_rate = 0.0001  # 学习率
    weight_decay = 1e-4  # 权重衰减（L2正则化）

    random_seed = 42  # 随机种子，用于结果复现


#%%
# 定义GRU分类器
class GRUClassifier(nn.Module):
    def __init__(self, params):
        super(GRUClassifier, self).__init__()
        # 定义GRU层
        # input_size: 输入特征的维度（这里是3，表示3个通道）
        # hidden_size: GRU隐藏层的大小
        # num_layers: GRU的层数
        # batch_first=True: 输入数据的形状为 (batch_size, seq_len, input_size)
        # dropout: 在GRU层之间应用的dropout比率，防止过拟合
        self.gru = nn.GRU(3, params.hidden_size, params.num_layers,
                          batch_first=True, dropout=params.dropout)

        # 定义全连接层，将GRU的输出映射到最终的分类结果
        # hidden_size: GRU隐藏层的输出大小
        # num_classes: 分类任务中的类别数
        self.fc = nn.Linear(params.hidden_size, params.num_classes)

        # 定义Dropout层，用于在全连接层之前随机丢弃部分神经元
        self.dropout = nn.Dropout(params.dropout)
        # 初始化 GRU 的权重
        self._init_gru_weights()

    def _init_gru_weights(self):
        for name, param in self.gru.named_parameters():
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
        # 初始化GRU的初始隐状态 h0
        # 形状为 (num_layers, batch_size, hidden_size)
        x = x.permute(0, 2, 1)
        out, _ = self.gru(x)  # (batch_size, seq_length, 2*hidden_size)

        # 获取GRU的最后一个时间步的输出，用于分类
        # out[:, -1, :] 表示获取最后一个时间步的输出，形状为 (batch_size, hidden_size)
        out = self.dropout(out[:, -1, :])  # 应用Dropout

        # 通过全连接层，将GRU的输出映射到分类结果
        # 输出的形状为 (batch_size, num_classes)
        out = self.fc(out)

        return out


def train_model(model, train_loader, val_loader, criterion, optimizer, num_epochs, early_stopping_patience):
    train_loss_history = []  # 训练损失历史记录
    train_acc_history = []  # 训练准确率历史记录
    val_loss_history = []  # 验证损失历史记录
    val_acc_history = []  # 验证准确率历史记录

    scheduler = ReduceLROnPlateau(optimizer, 'max', patience=early_stopping_patience // 2)
    epochs_no_improve = 0  # 用于早停

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
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)  # 梯度裁剪
            optimizer.step()  # 更新参数

            total_loss += loss.item() * inputs.size(0)
            _, predicted = torch.max(outputs, 1)  # 获得预测结果
            total += labels.size(0)  # 累加总个数
            correct += predicted.eq(labels).sum().item()  # 累加正确个数

        train_loss = total_loss / len(train_loader)  # 计算当前epoch的平均损失
        train_acc = correct / total  # 计算当前epoch的准确率
        train_loss_history.append(train_loss)  # 记录当前epoch的损失
        train_acc_history.append(train_acc)  # 记录当前epoch的准确率

        # 验证
        val_loss, val_acc = evaluate_model(model, val_loader, criterion)
        val_loss_history.append(val_loss)  # 记录当前epoch的损失
        val_acc_history.append(val_acc)  # 记录当前epoch的准确率
        scheduler.step(val_acc)

        print(f'Epoch [{epoch + 1}/{num_epochs}], Train_Loss: {train_loss:.4f} Train_Acc: {train_acc:.4f}, Val_Loss: {val_loss:.4f} Val_Acc: {val_acc:.4f}')

        # 保存最佳模型
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), 'best_model.pth')
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
    
  
#%%
def main():
    # 初始化参数配置
    params = Params()  # 创建包含所有参数的 Params 类实例

    train_loader, val_loader, test_loader = process_data('data_sheet.csv', 32)

    # 创建 GRU 模型实例，并将模型移动到指定设备 (GPU或CPU)
    model = GRUClassifier(params).to(device)

    # 定义损失函数，使用交叉熵损失
    criterion = nn.CrossEntropyLoss()

    # 定义优化器，使用 Adam 优化器，学习率和权重衰减由参数设定
    optimizer = optim.Adam(model.parameters(), lr=params.learning_rate, weight_decay=params.weight_decay)

    # 开始训练模型，使用训练集和验证集
    train_loss_history, val_loss_history, train_acc_history, val_acc_history = train_model(model, train_loader, val_loader, criterion, optimizer, params.num_epochs, 30)
    draw_loss_acc(train_loss_history, val_loss_history, train_acc_history, val_acc_history)
    # 测试模型
    test_model(model, test_loader)
    

# 检查是否以脚本方式运行，若是则调用 main 函数
if __name__ == "__main__":
    main()

