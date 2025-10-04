import torch
import torch.nn as nn
import torch.optim as optim
import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.preprocess import load_logs, prepare_sequences

class GRUModel(nn.Module):
    def __init__(self, vocab_size=16, embed_dim=32, hidden_dim=64, num_layers=1):
        super(GRUModel, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.gru = nn.GRU(embed_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, 2)

    def forward(self, x):
        x = self.embedding(x)
        out, _ = self.gru(x)
        out = self.fc(out[:, -1, :])
        return out

def train():
    print("Training GRU Model for Behavior Anomaly Detection")
    print("================================================")
    
    # Load logs from SQLite database
    df = load_logs()
    if len(df) == 0:
        print(" No data found in database. Please run data collection first.")
        print("Run: python behavior_log.py")
        return
        
    print(f" Loaded {len(df)} behavioral events")
    
    X = prepare_sequences(df)
    print(f" Prepared sequences with shape: {X.shape}")

    # Dummy labels for now (0=normal, 1=anomaly)
    # In a real scenario, you'd have labeled data
    y = torch.zeros(X.size(0), dtype=torch.long)
    
    # Add some random anomalies for demonstration (10% of data)
    num_anomalies = max(1, X.size(0) // 10)
    anomaly_indices = torch.randperm(X.size(0))[:num_anomalies]
    y[anomaly_indices] = 1
    print(f" Created labels: {(y == 0).sum()} normal, {(y == 1).sum()} anomaly")

    # Model
    model = GRUModel()
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    print("\n Starting training...")
    
    # Training loop
    for epoch in range(10):
        model.train()
        optimizer.zero_grad()
        outputs = model(X)
        loss = criterion(outputs, y)
        loss.backward()
        optimizer.step()
        
        # Calculate accuracy
        with torch.no_grad():
            predictions = torch.argmax(outputs, dim=1)
            accuracy = (predictions == y).float().mean()
        
        print(f"Epoch {epoch+1}/10, Loss: {loss.item():.4f}, Accuracy: {accuracy:.4f}")

    # Save model
    model_path = "behavior_gru_model.pth"
    torch.save(model.state_dict(), model_path)
    print(f"\n Model saved as {model_path}")
    print(" Training completed successfully!")

if __name__ == "__main__":
    train()