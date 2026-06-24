import joblib
import pandas as pd
import numpy as np
import torch
from torch.utils.data import TensorDataset, DataLoader
from Res_1DCNN_BiGRU_Attention_Muti import CombinedModel  # 假设你的模型定义在这个文件中
import torch.nn as nn
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 1. 加载标准化器
scaler_droplet = joblib.load('scaler_droplet.pkl')
scaler_acc = joblib.load('scaler_acc.pkl')
scaler_gyro = joblib.load('scaler_gyro.pkl')

# 2. 加载模型
model = CombinedModel(
    input_channels=3,
    out_channels=32,
    num_residual_layers=2,
    gru_input_size=3,
    gru_hidden_size=64,
    gru_num_layers=2,
    gru_dropout_rate=0.5
).to(device)
model.load_state_dict(torch.load('Res_1DCNN_BiGRU_Attention_Multi_zengqiang_best_model.pth'))
model.eval()

# 3. 读取新数据
new_data_filename = 'yanzheng_data_200.csv'  # 替换为新数据的文件名
df = pd.read_csv(new_data_filename, header=None)
droplet_data = df.iloc[:, 0:704].values
acc_data = df.iloc[:, 704:1408].values
gyro_data = df.iloc[:, 1408:2112].values
labels = df.iloc[:, 2112].values  # 如果新数据有标签，这里可以读取标签

# 4. 标准化新数据
droplet_data_std = scaler_droplet.transform(droplet_data)
acc_data_std = scaler_acc.transform(acc_data)
gyro_data_std = scaler_gyro.transform(gyro_data)

# 5. 创建测试数据加载器
time_series_data = np.stack([droplet_data_std, acc_data_std, gyro_data_std], axis=-1)
time_series_data = np.transpose(time_series_data, (0, 2, 1))
print("新数据预处理后的形状:", time_series_data.shape)  # 应为 (n_samples, 3, 704)
time_series_data = torch.tensor(time_series_data, dtype=torch.float32).to(device)
labels = torch.tensor(labels, dtype=torch.long).to(device)
test_dataset = TensorDataset(time_series_data, labels)
test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)  # 假设batch_size为32

# 6. 进行测试
criterion = nn.CrossEntropyLoss()
all_predicts = []
all_labels = []
correct = 0
total = 0
with torch.no_grad():
    for inputs, labels in test_loader:
        outputs = model(inputs)
        _, predicted = torch.max(outputs, 1)
        all_predicts.extend(predicted.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

# 计算准确率
accuracy = correct / total
print(f'新测试集上的准确率: {accuracy * 100:.4f}%')
print("New Test Classification Report:")
print(classification_report(all_labels, all_predicts, digits=4, zero_division=0))
# 计算混淆矩阵
cm = confusion_matrix(all_labels, all_predicts)
disp = ConfusionMatrixDisplay(confusion_matrix=cm)
disp.plot(cmap=plt.cm.Blues)
plt.title("Confusion Matrix")
plt.show()