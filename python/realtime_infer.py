import torch
import time
import threading
import pyodbc
from pynput import keyboard
import sys
import os

# Add utils directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.preprocess import hash_to_vector
from models.train_gru import GRUModel

# SQL Server JDBC configuration
DB_CONFIG = {
    'server': 'localhost\\SQLEXPRESS',
    'database': 'behavior_db',
    'driver': '{ODBC Driver 17 for SQL Server}'
}

MODEL_PATH = "behavior_gru_model.pth"
PROCESS_INTERVAL = 5  # Process new logs every 5 seconds

stop_flag = False
data_lock = threading.Lock()

def get_db_connection():
    """Try multiple SQL Server connection strings"""
    connection_strings = [
        f"DRIVER={DB_CONFIG['driver']};SERVER=localhost\\SQLEXPRESS;DATABASE={DB_CONFIG['database']};Trusted_Connection=yes;",
        f"DRIVER={DB_CONFIG['driver']};SERVER=localhost;DATABASE={DB_CONFIG['database']};Trusted_Connection=yes;",
        f"DRIVER={DB_CONFIG['driver']};SERVER=.;DATABASE={DB_CONFIG['database']};Trusted_Connection=yes;",
        f"DRIVER={{SQL Server}};SERVER=localhost\\SQLEXPRESS;DATABASE={DB_CONFIG['database']};Trusted_Connection=yes;",
    ]
    
    for i, conn_str in enumerate(connection_strings, 1):
        try:
            return pyodbc.connect(conn_str)
        except Exception as e:
            if i == len(connection_strings):
                raise e
            continue

def on_release(key):
    """Handle key release events"""
    global stop_flag
    if key == keyboard.Key.esc:
        stop_flag = True
        print("ESC pressed. Stopping system...")
        return False

def process_unprocessed_logs():
    """Process logs that don't have predictions yet"""
    with data_lock:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get unprocessed rows
            cursor.execute("""
                SELECT id, timestamp, hashed_event
                FROM behavior_logs 
                WHERE prediction IS NULL AND hashed_event IS NOT NULL
                ORDER BY id ASC
            """)
            
            unprocessed_rows = cursor.fetchall()
            
            if len(unprocessed_rows) == 0:
                cursor.close()
                conn.close()
                return
            
            print(f" Processing {len(unprocessed_rows)} new events...")
            
            # Load model once for all predictions
            model = GRUModel()
            model.load_state_dict(torch.load(MODEL_PATH))
            model.eval()
            
            anomaly_count = 0
            total_processed = 0
            error_count = 0
            
            for row_id, timestamp, hashed_event in unprocessed_rows:
                try:
                    # Convert hash to tensor - MATCH TRAINING FORMAT EXACTLY
                    hash_vector = hash_to_vector(hashed_event, max_len=16)
                    # Create tensor matching training: (batch_size=1, sequence_length=16)
                    hash_tensor = torch.tensor([hash_vector], dtype=torch.long)  # Shape: (1, 16)
                    
                    # Make prediction
                    with torch.no_grad():
                        output = model(hash_tensor)
                        prediction = torch.argmax(output, dim=1).item()
                    
                    # Update database with prediction and clear hashed_event
                    cursor.execute("""
                        UPDATE behavior_logs 
                        SET prediction = ?, hashed_event = NULL 
                        WHERE id = ?
                    """, (prediction, row_id))
                    
                    status = " ANOMALY" if prediction == 1 else " NORMAL"
                    print(f"[{timestamp:.2f}] {status}")
                    
                    if prediction == 1:
                        anomaly_count += 1
                    total_processed += 1
                    
                except Exception as e:
                    print(f" Error processing row {row_id}: {e}")
                    error_count += 1
                    # Mark as error
                    cursor.execute("""
                        UPDATE behavior_logs 
                        SET prediction = -1, hashed_event = NULL 
                        WHERE id = ?
                    """, (row_id,))
            
            # ALWAYS show batch summary
            print(f"\n BATCH SUMMARY:")
            print(f"   Total events processed: {total_processed}")
            print(f"   Normal events: {total_processed - anomaly_count}")
            print(f"   Anomalous events: {anomaly_count}")
            print(f"   Errors: {error_count}")
            
            # Calculate anomaly percentage for this batch
            if total_processed > 0:
                anomaly_percent = anomaly_count / total_processed
                print(f"   Anomaly rate: {anomaly_percent:.1%}")
                
                if anomaly_percent > 0.8:
                    print(" SYSTEM ALERT: More than 80% of events are anomalies!")
                elif anomaly_percent > 0.3:
                    print("  WARNING: High anomaly rate in this batch")
                elif anomaly_percent > 0:
                    print("  Some anomalies detected")
                else:
                    print(" All events appear normal")
            elif error_count > 0:
                print(" All events had processing errors")
            
            print("-" * 50)  # Separator line
            
            # Commit changes and close connection
            conn.commit()
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f" Error in processing: {e}")

def processing_loop():
    """Continuous processing loop"""
    while not stop_flag:
        process_unprocessed_logs()
        time.sleep(PROCESS_INTERVAL)

def main():
    global stop_flag
    
    print("Real-time Behavior Anomaly Monitor (SQL Server JDBC)")
    print("===================================================")
    print("- Monitors SQL Server database for new behavior logs")
    print("- Processes and clears hashed data every 5 seconds") 
    print("- Press ESC to stop")
    print()
    
    # Check if model exists
    if not os.path.exists(MODEL_PATH):
        print(f" Model file {MODEL_PATH} not found!")
        print("Please train the model first: python -m models.train_gru")
        return
    
    # Test database connection
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM behavior_logs")
        conn.close()
        print(" Database connection successful")
    except Exception as e:
        print(f" Database connection failed: {e}")
        return
    
    # Start keyboard listener for ESC
    listener = keyboard.Listener(on_release=on_release)
    listener.start()
    
    # Start processing thread
    processing_thread = threading.Thread(target=processing_loop)
    processing_thread.daemon = True
    processing_thread.start()
    
    print(" Real-time monitoring started. Press ESC to stop.")
    
    try:
        while not stop_flag:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_flag = True
    
    print(" Monitoring stopped.")

if __name__ == "__main__":
    main()