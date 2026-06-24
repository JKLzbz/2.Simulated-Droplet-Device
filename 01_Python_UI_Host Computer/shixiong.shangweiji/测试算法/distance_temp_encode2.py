# 范围编码 + 嵌入层：
# 将距离和温度值映射到预定义的范围。
# 使用嵌入层将这些范围编码转换为高维向量。

import torch
import torch.nn as nn
import torch.nn.functional as F
# 定义范围编码
distance_ranges = [
    (0, 60), (60, 80), (80, 100), (100, 120), (120, 140),
    (140, 160), (160, 200), (200, float('inf'))
]
temperature_ranges = [
    (-float('inf'), 35.9), (35.9, 36.8), (36.8, 41), (41, float('inf'))
]

# 将值映射到范围索引
def map_to_range(value, ranges):
    for idx, (low, high) in enumerate(ranges):
        if low <= value < high:
            return idx
    return len(ranges) - 1

# 嵌入层
distance_embedding = nn.Embedding(len(distance_ranges), 16)
temperature_embedding = nn.Embedding(len(temperature_ranges), 16)

# 示例数据
distance_value = 170
temperature_value = 37.5

# 映射到范围索引
distance_idx = map_to_range(distance_value, distance_ranges)
temperature_idx = map_to_range(temperature_value, temperature_ranges)

# 转换为嵌入向量
distance_embed = distance_embedding(torch.tensor(distance_idx))
temperature_embed = temperature_embedding(torch.tensor(temperature_idx))

print(distance_embed, temperature_embed)

# CNN + GRU + Attention：
#
# 使用CNN处理时间序列数据。
# 使用GRU捕捉时间依赖性。
# 结合自注意力机制和通道注意力机制。
# Transformer模型：
#
# 使用Transformer处理时间序列数据和单一值数据的组合。

class CNN_GRU_Attention(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, n_layers=1):
        super(CNN_GRU_Attention, self).__init__()
        self.conv1 = nn.Conv1d(input_dim, 64, kernel_size=3, padding=1)
        self.gru = nn.GRU(64, hidden_dim, n_layers, batch_first=True)
        self.attention = nn.MultiheadAttention(hidden_dim, num_heads=4)
        self.fc = nn.Linear(hidden_dim, output_dim)
        self.distance_embedding = nn.Embedding(len(distance_ranges), hidden_dim)
        self.temperature_embedding = nn.Embedding(len(temperature_ranges), hidden_dim)

    def forward(self, x, distance_idx, temperature_idx):
        # x: (batch_size, seq_len, input_dim)
        x = x.permute(0, 2, 1)  # (batch_size, input_dim, seq_len)
        x = F.relu(self.conv1(x))  # (batch_size, 64, seq_len)
        x = x.permute(0, 2, 1)  # (batch_size, seq_len, 64)
        gru_out, _ = self.gru(x)  # (batch_size, seq_len, hidden_dim)

        distance_embed = self.distance_embedding(torch.tensor(distance_idx))
        temperature_embed = self.temperature_embedding(torch.tensor(temperature_idx))
        combined_embed = torch.cat((distance_embed, temperature_embed), dim=1).unsqueeze(1)

        attn_output, _ = self.attention(gru_out, combined_embed, combined_embed)
        out = self.fc(attn_output[:, -1, :])  # 取最后一个时间步的输出
        return out


# 示例参数
input_dim = 3  # 三个传感器的时间序列数据
hidden_dim = 128
output_dim = 10  # 分类类别数

model = CNN_GRU_Attention(input_dim, hidden_dim, output_dim)

class TransformerModel(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, n_heads, n_layers):
        super(TransformerModel, self).__init__()
        self.embedding = nn.Linear(input_dim + 2, hidden_dim)  # +2 for distance and temperature
        self.transformer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d_model=hidden_dim, nhead=n_heads),
            num_layers=n_layers
        )
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x, distance_idx, temperature_idx):
        # x: (batch_size, seq_len, input_dim)
        distance_embed = self.distance_embedding(torch.tensor(distance_idx))
        temperature_embed = self.temperature_embedding(torch.tensor(temperature_idx))
        combined_embed = torch.cat((x, distance_embed.unsqueeze(1), temperature_embed.unsqueeze(1)), dim=2)
        embedded = self.embedding(combined_embed.permute(1, 0, 2))  # (seq_len, batch_size, hidden_dim)
        transformer_out = self.transformer(embedded)
        out = self.fc(transformer_out[-1, :, :])  # 取最后一个时间步的输出
        return out

# 示例参数
input_dim = 3
hidden_dim = 128
output_dim = 10
n_heads = 4
n_layers = 2

transformer_model = TransformerModel(input_dim, hidden_dim, output_dim, n_heads, n_layers)