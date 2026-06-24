import torch
import torch.nn as nn
import torch.nn.functional as F


class ChannelAttention(nn.Module):
    def __init__(self, in_channels):
        super(ChannelAttention, self).__init__()
        self.fc = nn.Sequential(
            nn.Linear(in_channels, in_channels // 2),
            nn.ReLU(),
            nn.Linear(in_channels // 2, in_channels),
            nn.Sigmoid()
        )

    def forward(self, x):
        att = self.fc(x)
        return x * att


class CNN_GRU_Network(nn.Module):
    def __init__(self, input_channels=3, seq_len=512, output_classes=10):
        super(CNN_GRU_Network, self).__init__()

        # CNN layer for feature extraction
        self.conv1 = nn.Conv1d(input_channels, 64, kernel_size=5, stride=1, padding=2)
        self.conv2 = nn.Conv1d(64, 128, kernel_size=5, stride=1, padding=2)

        # GRU layer for temporal dependencies
        self.gru = nn.GRU(128, 128, batch_first=True, bidirectional=True)

        # Channel Attention layer
        self.channel_attention = ChannelAttention(128 * 2)  # bidirectional GRU

        # Fully connected layer for classification
        self.fc = nn.Linear(128 * 2, output_classes)

    def forward(self, x, constant_features):
        # CNN part
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))

        # GRU part
        x, _ = self.gru(x)

        # Channel Attention
        x = self.channel_attention(x)

        # Combine constant features (e.g., temperature, distance)
        constant_features = constant_features.unsqueeze(1).expand_as(x)  # Align constants with sequence length
        x = torch.cat((x, constant_features), dim=-1)  # Concatenate along feature dimension

        # Classification
        x = x.mean(dim=1)  # Global average pooling
        x = self.fc(x)
        return x


# Example usage
seq_len = 512
input_channels = 3  # Number of time series channels
output_classes = 10  # Number of output classes
batch_size = 32

# Random data to simulate
x_data = torch.randn(batch_size, input_channels, seq_len)  # Shape: (batch_size, input_channels, seq_len)
constant_features = torch.randn(batch_size, 2)  # Shape: (batch_size, 2) for constant features (temp, distance)

model = CNN_GRU_Network(input_channels=input_channels, seq_len=seq_len, output_classes=output_classes)
output = model(x_data, constant_features)
print(output.shape)  # Should print: torch.Size([batch_size, output_classes])
