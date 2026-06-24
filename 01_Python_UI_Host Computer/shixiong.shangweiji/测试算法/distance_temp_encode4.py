import torch
import torch.nn as nn
import torch.optim as optim


class FeatureExtractor(nn.Module):
    def __init__(self, input_size):
        super(FeatureExtractor, self).__init__()
        self.conv1 = nn.Conv1d(input_size, 64, kernel_size=3, stride=1, padding=1)
        self.conv2 = nn.Conv1d(64, 128, kernel_size=3, stride=1, padding=1)
        self.pool = nn.MaxPool1d(kernel_size=2, stride=2)
        self.gru = nn.GRU(128, 128, batch_first=True)
        self.fc = nn.Linear(128, 256)

    def forward(self, x):
        # CNN feature extraction
        x = self.conv1(x)
        x = torch.relu(x)
        x = self.pool(x)
        x = self.conv2(x)
        x = torch.relu(x)
        x = self.pool(x)

        # GRU for temporal sequences
        x, _ = self.gru(x)

        # Global feature extraction
        x = x[:, -1, :]  # Only use the last time step
        x = self.fc(x)
        return x


class AttentionBlock(nn.Module):
    def __init__(self, channel):
        super(AttentionBlock, self).__init__()
        self.attention = nn.Sequential(
            nn.Conv1d(channel, channel, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.Conv1d(channel, 1, kernel_size=1)
        )

    def forward(self, x):
        # Attention scores
        attention_weights = torch.softmax(self.attention(x), dim=-1)
        # Weighted sum
        x = x * attention_weights
        return x


class Model(nn.Module):
    def __init__(self, seq_length, temperature_dim, distance_dim, num_classes):
        super(Model, self).__init__()
        self.feature_extractor = FeatureExtractor(seq_length)

        # Embedding layers for temperature and distance
        self.temp_embedding = nn.Embedding(4, 32)  # 4 temperature categories
        self.dist_embedding = nn.Embedding(8, 32)  # 8 distance categories

        # Attention mechanism
        self.attention_block = AttentionBlock(128)

        # Final classification layer
        self.fc1 = nn.Linear(256 + 64 + 64, 128)
        self.fc2 = nn.Linear(128, num_classes)

    def forward(self, time_series, temperature, distance):
        # Feature extraction from time series
        time_series_features = self.feature_extractor(time_series)

        # Embedding for temperature and distance
        temp_embed = self.temp_embedding(temperature)
        dist_embed = self.dist_embedding(distance)

        # Combine all features
        combined_features = torch.cat((time_series_features, temp_embed, dist_embed), dim=-1)

        # Apply attention
        attention_out = self.attention_block(combined_features)

        # Fully connected layers
        x = torch.relu(self.fc1(attention_out))
        x = self.fc2(x)
        return x


# Example of input data
batch_size = 32
seq_length = 512  # Length of time series
num_classes = 10  # Number of classes for classification

# Time series data (5 sensors, seq_length=512)
time_series_data = torch.randn(batch_size, 3, seq_length)  # Shape: [batch_size, 3, 512]

# Temperature and Distance data (single value per sample)
temperature_data = torch.randint(0, 4, (batch_size,))  # Temperature categories (4 categories)
distance_data = torch.randint(0, 8, (batch_size,))  # Distance categories (8 categories)

# Create the model
model = Model(seq_length=seq_length, temperature_dim=4, distance_dim=8, num_classes=num_classes)

# Forward pass
output = model(time_series_data, temperature_data, distance_data)
print(output.shape)  # Output shape: [batch_size, num_classes]
