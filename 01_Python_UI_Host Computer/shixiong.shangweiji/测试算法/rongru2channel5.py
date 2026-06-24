import torch
import torch.nn as nn
import torch.nn.functional as F

class MultiInputModel(nn.Module):
    def __init__(self):
        super(MultiInputModel, self).__init__()
        # CNN部分处理时间序列数据
        self.cnn = nn.Sequential(
            nn.Conv1d(3, 64, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2),
            nn.Conv1d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2)
        )
        # 全连接层处理距离和温度传感器的值
        self.fc_aux = nn.Linear(2, 64)
        # 合并后的全连接层
        self.fc = nn.Linear(128 * 128 + 64, 10)  # 假设有10个类别

    def forward(self, x_seq, x_aux):
        x_seq = self.cnn(x_seq)
        x_seq = x_seq.view(x_seq.size(0), -1)
        x_aux = self.fc_aux(x_aux)
        x = torch.cat((x_seq, x_aux), dim=1)
        x = self.fc(x)
        return x


# 示例输入
x_seq = torch.randn(32, 3, 512)  # 32个样本，3个通道，每个样本512个时间步
x_aux = torch.randn(32, 2)  # 32个样本，2个辅助特征（距离和温度）
model = MultiInputModel()
output = model(x_seq, x_aux)