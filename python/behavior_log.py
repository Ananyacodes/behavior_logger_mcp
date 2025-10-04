import jaydebeapi
import time
import subprocess
import psutil
from pynput import keyboard, mouse
from threading import Thread
import os
import json

print("DEBUG: This is the JDBC version - timestamp:", time.time())

# JDBC configuration
JAR_PATH = os.path.join(os.path.dirname(__file__), "mssql-jdbc-12.4.2.jre8.jar")
JDBC_DRIVER = "com.microsoft.sqlserver.jdbc.SQLServerDriver"
JDBC_URL = "jdbc:sqlserver://localhost\\SQLEXPRESS;databaseName=behavior_db;integratedSecurity=true;trustServerCertificate=true;"

STOP_AFTER = 45
start_time = time.time()
stop_flag = False

def get_jdbc_connection():
    """Get JDBC connection to SQL Server"""
    return jaydebeapi.connect(JDBC_DRIVER, JDBC_URL, ["", ""], JAR_PATH)

def setup_database():
    """Create SQL Server database table via JDBC"""
    try:
        conn = get_jdbc_connection()
        cursor = conn.cursor()
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'behavior_logs')
            BEGIN
                CREATE TABLE behavior_logs (
                    id int IDENTITY(1,1) PRIMARY KEY,
                    timestamp float NOT NULL,
                    hashed_event nvarchar(max),
                    prediction int DEFAULT NULL,
                    created_at datetime DEFAULT GETDATE()
                )
            END
        """)
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ JDBC Database table ready")
    except Exception as e:
        print(f"❌ JDBC Database setup failed: {e}")
        raise

# Call Rust hasher
def hash_with_rust(input_str):
    try:
        result = subprocess.run(
            [r"C:\Users\Ananya\behavior_logger\rust_hasher\target\release\rust_hasher.exe", input_str],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"Rust hasher error: {e}")
        return None

# Get active application details
def get_active_app():
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                proc_info = proc.info
                if proc_info['cpu_percent'] and proc_info['cpu_percent'] > 0:
                    processes.append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if processes:
            active_proc = max(processes, key=lambda x: x['cpu_percent'])
            return {
                'name': active_proc['name'],
                'pid': active_proc['pid'],
                'cpu_percent': active_proc['cpu_percent']
            }
        else:
            return {'name': 'Unknown', 'pid': -1, 'cpu_percent': 0}
    except:
        return {'name': 'Unknown', 'pid': -1, 'cpu_percent': 0}

# Get system resource usage
def get_system_metrics():
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('C:')
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': round(memory.available / (1024**3), 2),
            'disk_free_gb': round(disk.free / (1024**3), 2)
        }
    except:
        return {'cpu_percent': 0, 'memory_percent': 0, 'memory_available_gb': 0, 'disk_free_gb': 0}

# Log event to database via JDBC
def log_event(event_type, event_data):
    timestamp = time.time()
    event_string = f"{event_type}:{json.dumps(event_data)}"
    hashed_event = hash_with_rust(event_string)
    
    if not hashed_event:
        return

    try:
        conn = get_jdbc_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO behavior_logs (timestamp, hashed_event)
            VALUES (?, ?)
        """, (timestamp, hashed_event))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ JDBC Logged: {event_type}")
    except Exception as e:
        print(f"❌ JDBC Error logging to database: {e}")

# Keyboard event handlers
def on_key_press(key):
    global stop_flag
    if stop_flag:
        return False
    
    try:
        key_data = {'key': str(key.char), 'type': 'char'}
    except AttributeError:
        key_data = {'key': str(key), 'type': 'special'}
    
    log_event("KEYSTROKE", key_data)

def on_key_release(key):
    global stop_flag
    if stop_flag or key == keyboard.Key.esc:
        return False

# Mouse event handlers
def on_mouse_click(x, y, button, pressed):
    global stop_flag
    if stop_flag:
        return False
    
    if pressed:
        mouse_data = {'x': x, 'y': y, 'button': str(button), 'action': 'click'}
        log_event("MOUSE_CLICK", mouse_data)

# Log active application periodically
def log_active_app():
    global stop_flag
    last_app = None
    
    while not stop_flag:
        current_app = get_active_app()
        
        if current_app != last_app:
            log_event("APP_ACTIVITY", current_app)
            last_app = current_app
        
        time.sleep(3)

# Log system metrics periodically
def log_system_metrics():
    global stop_flag
    
    while not stop_flag:
        metrics = get_system_metrics()
        log_event("SYSTEM_METRICS", metrics)
        time.sleep(10)

if __name__ == "__main__":
    print("Enhanced Behavior Logger Started (JDBC)")
    print("======================================")
    print("Logging comprehensive behavioral data via JDBC...")
    print(f"Running for {STOP_AFTER} seconds")
    print()

    # Check JAR file
    if not os.path.exists(JAR_PATH):
        print(f"❌ JDBC JAR file not found: {JAR_PATH}")
        print("Please download mssql-jdbc-12.4.2.jre8.jar and put it in the python directory")
        exit(1)

    # Setup database
    setup_database()

    # Test database connection
    try:
        conn = get_jdbc_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM behavior_logs")
        count = cursor.fetchone()[0]
        print(f"✅ JDBC Database connection successful! Table has {count} rows.")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ JDBC Database connection failed: {e}")
        exit(1)

    # Start monitoring threads
    app_thread = Thread(target=log_active_app, daemon=True)
    app_thread.start()
    
    metrics_thread = Thread(target=log_system_metrics, daemon=True)
    metrics_thread.start()

    # Start input listeners
    keyboard_listener = keyboard.Listener(
        on_press=on_key_press, 
        on_release=on_key_release
    )
    keyboard_listener.start()
    
    mouse_listener = mouse.Listener(
        on_click=on_mouse_click
    )
    mouse_listener.start()

    print("All JDBC monitoring started. Press ESC to stop early.")

    # Wait for STOP_AFTER seconds
    while time.time() - start_time < STOP_AFTER and not stop_flag:
        time.sleep(1)

    # Stop everything
    stop_flag = True
    keyboard_listener.stop()
    mouse_listener.stop()
    
    print(f"JDBC Enhanced logging stopped after {STOP_AFTER} seconds.")
    
    # Show final count
    try:
        conn = get_jdbc_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM behavior_logs")
        final_count = cursor.fetchone()[0]
        print(f"Total JDBC events logged: {final_count}")
        cursor.close()
        conn.close()
    except:
        pass