import torch
import torch.nn as nn
import torch.nn.functional as F


# 定义基本的残差块（Residual Block）
class ResidualBlock(nn.Module):
    def __init__(self, in_channels, out_channels, stride=1):
        super(ResidualBlock, self).__init__()

        # 定义两个卷积层和跳跃连接
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)

        # 用于匹配输入和输出的维度（如果需要的话）
        self.shortcut = nn.Sequential()
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(out_channels)
            )

    def forward(self, x):
        out = F.relu(self.bn1(self.conv1(x)))  # 第一个卷积层加 ReLU 激活
        out = self.bn2(self.conv2(out))  # 第二个卷积层
        out += self.shortcut(x)  # 加入跳跃连接
        out = F.relu(out)  # 再次应用 ReLU 激活
        return out


# 定义ResNet-14
class ResNet14(nn.Module):
    def __init__(self, num_classes=10):
        super(ResNet14, self).__init__()

        # 定义网络的初始卷积层
        self.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(64)

        # 第一层残差块，64个通道
        self.layer1 = self._make_layer(64, 64, 2)  # 2个残差块

        # 第二层残差块，128个通道
        self.layer2 = self._make_layer(64, 128, 2, stride=2)  # 2个残差块

        # 第三层残差块，256个通道
        self.layer3 = self._make_layer(128, 256, 2, stride=2)  # 2个残差块

        # 全局平均池化
        self.avgpool = nn.AdaptiveAvgPool2d(1)

        # 全连接层，用于分类
        self.fc = nn.Linear(256, num_classes)

    def _make_layer(self, in_channels, out_channels, num_blocks, stride=1):
        layers = []
        layers.append(ResidualBlock(in_channels, out_channels, stride))  # 第一个残差块
        for _ in range(1, num_blocks):
            layers.append(ResidualBlock(out_channels, out_channels))  # 后续残差块
        return nn.Sequential(*layers)

    def forward(self, x):
        x = F.relu(self.bn1(self.conv1(x)))  # 初始卷积层
        x = self.layer1(x)  # 第一层残差块
        x = self.layer2(x)  # 第二层残差块
        x = self.layer3(x)  # 第三层残差块
        x = self.avgpool(x)  # 全局平均池化
        x = torch.flatten(x, 1)  # 展平为一维
        x = self.fc(x)  # 分类
        return x


# 初始化网络
model = ResNet14(num_classes=10)  # 假设是 CIFAR-10 数据集

# 打印网络结构
print(model)
