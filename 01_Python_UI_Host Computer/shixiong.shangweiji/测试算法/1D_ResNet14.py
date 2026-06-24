import torch
import torch.nn as nn
import torch.optim as optim

# 定义 1D 残差块
class ResBlock1D(nn.Module):
    def __init__(self, in_channels, out_channels, stride=1):
        super(ResBlock1D, self).__init__()
        self.conv1 = nn.Conv1d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1)
        self.bn1 = nn.BatchNorm1d(out_channels)
        self.relu = nn.ReLU(inplace=True)
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
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)
        out += self.shortcut(x)  # 添加跳跃连接
        out = self.relu(out)
        return out

# 定义 ResNet14
class ResNet14_1D(nn.Module):
    def __init__(self, input_channels, num_classes):
        super(ResNet14_1D, self).__init__()
        # 输入层
        self.conv1 = nn.Conv1d(input_channels, 64, kernel_size=7, stride=2, padding=3)
        self.bn1 = nn.BatchNorm1d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool1d(kernel_size=3, stride=2, padding=1)

        # 残差层（ResBlock1D）定义
        self.layer1 = self._make_layer(64, 64, 2)   # 2个残差块
        self.layer2 = self._make_layer(64, 128, 2, stride=2)  # 2个残差块
        self.layer3 = self._make_layer(128, 256, 2, stride=2) # 2个残差块
        self.layer4 = self._make_layer(256, 512, 2, stride=2) # 2个残差块

        # 全连接层
        self.avgpool = nn.AdaptiveAvgPool1d(1)  # 自适应池化到1
        self.fc = nn.Linear(512, num_classes)  # 输出类别数

    def _make_layer(self, in_channels, out_channels, blocks, stride=1):
        layers = []
        layers.append(ResBlock1D(in_channels, out_channels, stride))
        for _ in range(1, blocks):
            layers.append(ResBlock1D(out_channels, out_channels))
        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.avgpool(x)
        x = x.view(x.size(0), -1)  # Flatten
        x = self.fc(x)
        return x


# 模型参数设置
input_channels = 1  # 输入是1D时间序列，通道数为1
num_classes = 10    # 假设有10个类别
model = ResNet14_1D(input_channels, num_classes)

# 测试模型
x = torch.randn(32, 1, 128)  # 假设输入 batch_size=32, 通道数=1, 序列长度=128
output = model(x)
print(output.shape)  # 输出类别预测，应该是 (32, 10)

# 优化器和损失函数
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# 示例训练步骤
# optimizer.zero_grad()
# loss = criterion(output, labels)
# loss.backward()
# optimizer.step()
