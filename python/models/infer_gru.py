import torch
import sqlite3
import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.preprocess import load_logs, prepare_sequences
from models.train_gru import GRUModel

def get_db_connection():
    return sqlite3.connect("behavior_logs.db")

def infer():
    print("Behavior Anomaly Detection - Inference")
    print("=====================================")
    
    # Load new logs from database
    df = load_logs()
    if len(df) == 0:
        print(" No data found in database for inference.")
        return
        
    print(f" Loaded {len(df)} events for inference")
    
    X = prepare_sequences(df)

    # Load model
    model_path = "behavior_gru_model.pth"
    if not os.path.exists(model_path):
        print(f" Model file {model_path} not found. Please train the model first.")
        print("Run: python -m models.train_gru")
        return
        
    model = GRUModel()
    model.load_state_dict(torch.load(model_path))
    model.eval()
    print(" Model loaded successfully")

    with torch.no_grad():
        outputs = model(X)
        predictions = torch.argmax(outputs, dim=1)

    df["prediction"] = predictions.numpy()
    
    # Show results
    normal_count = (df["prediction"] == 0).sum()
    anomaly_count = (df["prediction"] == 1).sum()
    
    print(f"\n Inference Results:")
    print(f"   Normal events: {normal_count}")
    print(f"   Anomalous events: {anomaly_count}")
    print(f"   Total events: {len(df)}")
    
    # Show sample predictions
    print(f"\n Sample predictions:")
    for i, row in df.head(10).iterrows():
        status = " ANOMALY" if row["prediction"] == 1 else " NORMAL"
        print(f"   Event {row['id']}: {status}")

    # Calculate anomaly percentage and flag if above threshold
    total = len(df)
    anomaly_percent = anomaly_count / total if total > 0 else 0

    print(f"\n  Anomaly rate: {anomaly_percent:.2%}")
    
    if anomaly_percent > 0.8:
        print(" SYSTEM ALERT: More than 80% of events are anomalies!")
        print(" Potential security threat detected!")
    elif anomaly_percent > 0.3:
        print("  WARNING: High anomaly rate detected")
    else:
        print(" System behavior appears normal")

    # Clear hashed data from database after processing
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE behavior_logs SET hashed_event = NULL WHERE hashed_event IS NOT NULL")
    conn.commit()
    cursor.close()
    conn.close()
    print(" Processed data cleared from database")

if __name__ == "__main__":
    infer()