import torch
import time
import threading
import jaydebeapi
import jpype
from pynput import keyboard
import sys
import os
import urllib.request
import traceback
from datetime import datetime
import json

# Add utils directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.preprocess import hash_to_vector
from models.train_gru import GRUModel

# MySQL JDBC configuration
JAR_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'java', 'lib', 'mysql-connector-j-9.4.0.jar'))
JDBC_DRIVER = "com.mysql.cj.jdbc.Driver"
DB_CONFIG = {
    'host': 'localhost',
    'port': '3306',
    'database': 'neurolock',
    'user': 'root',
    'password': 'JoeMama@25'  # Replace with your actual MySQL password
}

JDBC_URL = f"jdbc:mysql://{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
MODEL_PATH = "behavior_gru_model.pth"
PROCESS_INTERVAL = 5  # Process new logs every 5 seconds

stop_flag = False
data_lock = threading.Lock()

def setup_database():
    """Create required tables if they don't exist"""
    try:
        conn = get_jdbc_connection()
        cursor = conn.cursor()

        # Create behavior_logs table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS behavior_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                timestamp DOUBLE PRECISION NOT NULL,
                event_type VARCHAR(50),
                hashed_event TEXT,
                raw_data JSON,
                prediction INTEGER,
                processed_at TIMESTAMP NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create anomaly_stats table for tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anomaly_stats (
                id INT AUTO_INCREMENT PRIMARY KEY,
                date DATE NOT NULL,
                total_events INTEGER DEFAULT 0,
                anomaly_count INTEGER DEFAULT 0,
                normal_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                average_confidence FLOAT DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # No need to call commit() when autocommit is true
        cursor.close()
        conn.close()
        print("[OK] Database schema verified")
        return True
    except Exception as e:
        print(f"[FAIL] Database setup failed: {e}")
        return False

# Global flag to indicate if we're running without database
SKIP_DB_MODE = False  # Default to using database

def ensure_jvm_started():
    """Ensure JVM is started with correct JDBC driver"""
    global SKIP_DB_MODE
    
    if not jpype.isJVMStarted():
        try:
            if not os.path.exists(JAR_PATH):
                print(f"[ERROR] JDBC JAR file not found: {JAR_PATH}")
                print("[WARN] Running in no-database mode instead")
                SKIP_DB_MODE = True
                return False

            # Start JVM using the default JVM path and set the classpath to our connector jar
            try:
                jvm_path = jpype.getDefaultJVMPath()
            except Exception:
                jvm_path = None

            if jvm_path and os.path.exists(jvm_path):
                jpype.startJVM(jvm_path, f"-Djava.class.path={JAR_PATH}")
                print("[OK] JVM started successfully")
                return True
            else:
                print("[ERROR] Could not find a valid JVM path; running in no-database mode")
                SKIP_DB_MODE = True
                return False
        except Exception as e:
            print(f"[FAIL] JVM start failed: {e}")
            print("[WARN] Running in no-database mode instead")
            SKIP_DB_MODE = True
            return False

    return True

def get_jdbc_connection():
    """Get JDBC connection to MySQL"""
    ensure_jvm_started()
    return jaydebeapi.connect(
        JDBC_DRIVER,
        JDBC_URL,
        [DB_CONFIG['user'], DB_CONFIG['password']],
        JAR_PATH
    )

def update_anomaly_stats(total, anomalies, normal, errors, confidence):
    """Update daily anomaly statistics"""
    try:
        conn = get_jdbc_connection()
        cursor = conn.cursor()
        
        today = datetime.now().date()
        
        # Check if record for today exists
        cursor.execute("""
            SELECT id, total_events, average_confidence
            FROM anomaly_stats
            WHERE date = ?
        """, (today,))
        
        existing = cursor.fetchone()
        
        if existing:
            # Record exists, update it
            record_id, existing_total, existing_confidence = existing
            new_total = existing_total + total
            new_confidence = ((existing_confidence * existing_total) + (confidence * total)) / new_total if new_total > 0 else 0
            
            cursor.execute("""
                UPDATE anomaly_stats 
                SET total_events = total_events + ?,
                    anomaly_count = anomaly_count + ?,
                    normal_count = normal_count + ?,
                    error_count = error_count + ?,
                    average_confidence = ?
                WHERE date = ?
            """, (total, anomalies, normal, errors, new_confidence, today))
        else:
            # Insert new record
            cursor.execute("""
                INSERT INTO anomaly_stats 
                    (date, total_events, anomaly_count, normal_count, error_count, average_confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (today, total, anomalies, normal, errors, confidence))
        
        # No need to call commit() when autocommit is true
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[ERROR] Error updating statistics: {e}")

def process_unprocessed_logs():
    """Process logs that don't have predictions yet"""
    
    # Skip if in no-database mode
    if SKIP_DB_MODE:
        print("Simulating event processing in no-database mode...")
        time.sleep(2)  # Just simulate some work being done
        return
        
    with data_lock:
        try:
            conn = get_jdbc_connection()
            cursor = conn.cursor()
            
            # Get unprocessed rows with batch limit
            cursor.execute("""
                SELECT id, timestamp, event_type, hashed_event, raw_data
                FROM behavior_logs 
                WHERE prediction IS NULL AND hashed_event IS NOT NULL
                ORDER BY timestamp ASC
                LIMIT 100
            """)
            
            unprocessed_rows = cursor.fetchall()
            
            if not unprocessed_rows:
                cursor.close()
                conn.close()
                return
            
            print(f"\nProcessing batch of {len(unprocessed_rows)} events...")
            
            # Load model
            model = None
            model_available = False
            if os.path.exists(MODEL_PATH):
                try:
                    model = GRUModel()
                    model.load_state_dict(torch.load(MODEL_PATH))
                    model.eval()
                    model_available = True
                    print(f"[OK] Loaded model from {MODEL_PATH}")
                except Exception as e:
                    print(f"[WARN] Failed to load model: {e}")
                    model = None
                    model_available = False
            else:
                print(f"[WARN] Model not found: {MODEL_PATH} - using rule-based fallback")
            
            anomaly_count = 0
            normal_count = 0
            error_count = 0
            confidence_sum = 0
            
            for row in unprocessed_rows:
                row_id, timestamp, event_type, hashed_event, raw_data = row
                
                try:
                    # Prepare input
                    hash_vector = hash_to_vector(hashed_event, max_len=16)
                    hash_tensor = torch.tensor([hash_vector], dtype=torch.long)
                    
                    # Get prediction and confidence
                    if model_available and model is not None:
                        with torch.no_grad():
                            output = model(hash_tensor)
                            probabilities = torch.softmax(output, dim=1)
                            prediction = torch.argmax(output, dim=1).item()
                            confidence = probabilities[0][prediction].item()
                    else:
                        # Simple fallback rule: if event_type contains 'KEY' or 'MOUSE', treat as normal (0)
                        # if event_type contains 'SYSTEM' or raw_data has high cpu, mark as anomaly (1)
                        prediction = 0
                        confidence = 0.65
                        if event_type and 'SYSTEM' in str(event_type).upper():
                            prediction = 1
                            confidence = 0.7
                        elif raw_data and isinstance(raw_data, (str,)):
                            # try to inspect JSON for cpu_percent
                            try:
                                rd = json.loads(raw_data)
                                cpu = rd.get('cpu_percent') if isinstance(rd, dict) else None
                                if cpu and float(cpu) > 90:
                                    prediction = 1
                                    confidence = 0.8
                            except Exception:
                                pass
                    
                    # Update database
                    cursor.execute("""
                        UPDATE behavior_logs 
                        SET prediction = ?,
                            processed_at = CURRENT_TIMESTAMP,
                            hashed_event = NULL
                        WHERE id = ?
                    """, (prediction, row_id))
                    
                    # Update counts
                    if prediction == 1:
                        status = "ANOMALY"
                        anomaly_count += 1
                    else:
                        status = "NORMAL"
                        normal_count += 1
                    
                    confidence_sum += confidence
                    print(f"[{event_type}] {status} (confidence: {confidence:.2%})")
                    
                except Exception as e:
                    print(f"[ERROR] Error processing event {row_id}: {e}")
                    error_count += 1
                    cursor.execute("""
                        UPDATE behavior_logs 
                        SET prediction = -1,
                            processed_at = CURRENT_TIMESTAMP,
                            hashed_event = NULL
                        WHERE id = ?
                    """, (row_id,))
            
            total_processed = len(unprocessed_rows)
            avg_confidence = confidence_sum / total_processed if total_processed > 0 else 0
            
            # Update statistics
            update_anomaly_stats(
                total_processed, 
                anomaly_count,
                normal_count,
                error_count,
                avg_confidence
            )
            
            # Show summary
            print(f"\nBatch Summary:")
            print(f"   Total processed: {total_processed}")
            print(f"   Normal events: {normal_count}")
            print(f"   Anomalies: {anomaly_count}")
            print(f"   Errors: {error_count}")
            print(f"   Average confidence: {avg_confidence:.2%}")
            
            if total_processed > 0:
                anomaly_rate = anomaly_count / total_processed
                if anomaly_rate > 0.8:
                    print("\nCRITICAL: Extremely high anomaly rate!")
                elif anomaly_rate > 0.3:
                    print("\nWARNING: Elevated anomaly rate")
                elif anomaly_rate > 0:
                    print("\nNormal anomaly levels detected")
            
            # No need to call commit() when autocommit is true
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"[ERROR] Processing error: {e}")
            traceback.print_exc()

def processing_loop():
    """Continuous processing loop"""
    while not stop_flag:
        process_unprocessed_logs()
        time.sleep(PROCESS_INTERVAL)

def on_release(key):
    """Handle key release events"""
    global stop_flag
    if key == keyboard.Key.esc:
        stop_flag = True
        print("Stopping system...")
        return False

def test_connection():
    """Test MySQL JDBC connection and setup"""
    print("\nTesting MySQL Connection")
    print("============================")

    # Skip if in no-database mode
    if SKIP_DB_MODE:
        print("[WARN] Running in no-database mode - connection test skipped")
        return True

    try:
        conn = get_jdbc_connection()
        cursor = conn.cursor()

        # Version check
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"[OK] Connected to: {version}")

        # Table checks
        cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN prediction IS NULL THEN 1 END) as unprocessed,
                   COUNT(CASE WHEN hashed_event IS NOT NULL THEN 1 END) as pending
            FROM behavior_logs
        """)
        total, unprocessed, pending = cursor.fetchone()

        print(f"\nDatabase Status:")
        print(f"   Total logs: {total:,}")
        print(f"   Unprocessed: {unprocessed:,}")
        print(f"   Pending processing: {pending:,}")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"[ERROR] Connection test failed: {e}")
        traceback.print_exc()
        return False

def main():
    global stop_flag
    global SKIP_DB_MODE
    
    print("*** Neurolock Behavior Monitor ***")
    print("===================================")
    
    # Set to use database mode
    SKIP_DB_MODE = False
    print("=> Running in database mode")
    
    # Setup database
    if not setup_database():
        print("❌ Database setup failed")
        return
    
    # Test connection
    if not test_connection():
        print("❌ Connection test failed")
        return
    
    # Start keyboard listener
    listener = keyboard.Listener(on_release=on_release)
    listener.start()
    
    # Start processing thread
    processing_thread = threading.Thread(target=processing_loop)
    processing_thread.daemon = True
    processing_thread.start()
    
    print("\nSystem Ready!")
    print("   - Processing logs every 5 seconds")
    print("   - Press ESC to stop")
    
    try:
        while not stop_flag:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_flag = True
    
    print("\nNeurolock stopped")

if __name__ == "__main__":
    main()