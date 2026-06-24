import torch
import torch.nn as nn
import torch.nn.functional as F


class AttentionBlock(nn.Module):
    def __init__(self, in_channels):
        super(AttentionBlock, self).__init__()
        self.attention = nn.Sequential(
            nn.Conv1d(in_channels, in_channels // 8, 1),
            nn.ReLU(),
            nn.Conv1d(in_channels // 8, in_channels, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        attention_weights = self.attention(x)
        return x * attention_weights


class SensorFusionCNNGRU(nn.Module):
    def __init__(self, input_size_time_series, hidden_size_gru, num_classes):
        super(SensorFusionCNNGRU, self).__init__()

        # CNN for time-series data
        self.conv1 = nn.Conv1d(input_size_time_series, 64, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv1d(64, 128, kernel_size=3, stride=1, padding=1)
        self.pool = nn.MaxPool1d(2)

        # GRU for time-series data
        self.gru = nn.GRU(128, hidden_size_gru, batch_first=True)

        # Fully connected layer for static sensors (temperature, distance)
        self.fc_static = nn.Sequential(
            nn.Linear(2, 64),
            nn.ReLU(),
            nn.Linear(64, 64)
        )

        # Attention block
        self.attention = AttentionBlock(128)

        # Final classification layer
        self.fc_out = nn.Linear(hidden_size_gru + 64, num_classes)

    def forward(self, x_time_series, x_static):
        # Process time-series data
        x = self.conv1(x_time_series)
        x = self.pool(F.relu(x))
        x = self.conv2(x)
        x = self.pool(F.relu(x))
        x = x.view(x.size(0), x.size(2), -1)  # Flatten the conv output for GRU

        # GRU to capture time dependencies
        x, _ = self.gru(x)
        x = x[:, -1, :]  # Take the output of the last time step

        # Apply attention mechanism to the output of GRU
        x = self.attention(x.unsqueeze(2))  # Add channel dimension

        # Process static sensor data (temperature, distance)
        x_static = self.fc_static(x_static)

        # Concatenate features from time-series and static sensors
        x_combined = torch.cat((x.squeeze(2), x_static), dim=1)

        # Final classification output
        x_out = self.fc_out(x_combined)

        return x_out


# Example usage:
# Assume input size for time series is (batch_size, 3, 512), and static input is (batch_size, 2)
model = SensorFusionCNNGRU(input_size_time_series=3, hidden_size_gru=128, num_classes=10)

# Random input for demonstration
x_time_series = torch.randn(32, 3, 512)  # 32 samples, 3 channels, 512 time steps
x_static = torch.randn(32, 2)  # 32 samples, 2 static sensors (temperature and distance)

output = model(x_time_series, x_static)
print(output.shape)  # Output shape will be (32, 10) for 10 classes


# 模型2
class TransformerGRUNetwork(nn.Module):
    def __init__(self, input_size_time_series, hidden_size_gru, num_classes, num_heads=8):
        super(TransformerGRUNetwork, self).__init__()

        # Transformer Encoder
        self.encoder_layer = nn.TransformerEncoderLayer(d_model=input_size_time_series, nhead=num_heads)
        self.transformer_encoder = nn.TransformerEncoder(self.encoder_layer, num_layers=6)

        # GRU
        self.gru = nn.GRU(input_size_time_series, hidden_size_gru, batch_first=True)

        # Fully connected layer for static sensors (temperature, distance)
        self.fc_static = nn.Sequential(
            nn.Linear(2, 64),
            nn.ReLU(),
            nn.Linear(64, 64)
        )

        # Final classification layer
        self.fc_out = nn.Linear(hidden_size_gru + 64, num_classes)

    def forward(self, x_time_series, x_static):
        # Transformer for time-series data
        x = self.transformer_encoder(x_time_series)
        x = x[:, -1, :]  # Take the last time step's output

        # GRU
        x, _ = self.gru(x.unsqueeze(1))  # GRU expects the input shape (batch_size, seq_len, input_size)
        x = x[:, -1, :]  # Last hidden state

        # Process static sensor data (temperature, distance)
        x_static = self.fc_static(x_static)

        # Concatenate features from time-series and static sensors
        # Concatenate features from time-series and static sensors
        x_combined = torch.cat((x, x_static), dim=1)
        # Pass the combined features through the final classification layer
        out = self.fc_out(x_combined)
        return out
