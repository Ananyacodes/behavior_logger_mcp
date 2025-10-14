import jaydebeapi
import jpype
import mysql.connector
import time
import subprocess
import psutil
from pynput import keyboard, mouse
from threading import Thread
import os
import json
import win32gui
import win32process

# Global variables
STOP_AFTER = 45  # Run for 45 seconds
start_time = time.time()
stop_flag = False

# Add the missing functions
def hash_with_rust(input_str):
    """Hash input string using Rust hasher"""
    try:
        result = subprocess.run(
            [r"C:\Users\Ananya\behavior_logger\rust_hasher\target\release\rust_hasher.exe", input_str],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip()
    except Exception as e:
        # If the Rust binary isn't available, fall back to a Python SHA-256 hash
        try:
            import hashlib
            h = hashlib.sha256()
            h.update(input_str.encode('utf-8'))
            digest = h.hexdigest()
            print(f"Rust hasher unavailable, using sha256 fallback: {digest[:16]}...")
            return digest
        except Exception:
            print(f"Rust hasher error and Python fallback failed: {e}")
            return None

def get_active_app():
    """Get information about the currently active application"""
    try:
        active_window = win32gui.GetForegroundWindow()
        window_title = win32gui.GetWindowText(active_window)
        process_id = win32process.GetWindowThreadProcessId(active_window)[1]
        
        try:
            process = psutil.Process(process_id)
            return {
                'name': process.name(),
                'title': window_title,
                'pid': process_id,
                'cpu_percent': process.cpu_percent(),
                'memory_percent': process.memory_percent(),
                'status': process.status(),
                'num_threads': process.num_threads()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {'name': 'Unknown', 'pid': process_id, 'title': window_title}
            
    except Exception:
        return {'name': 'Unknown', 'pid': -1, 'title': 'Unknown'}

def get_system_metrics():
    """Get system performance metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('C:')
        
        # Network metrics
        net = psutil.net_io_counters()
        
        return {
            'timestamp': time.time(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': round(memory.available / (1024**3), 2),
            'disk_free_gb': round(disk.free / (1024**3), 2),
            'network_bytes_sent': net.bytes_sent,
            'network_bytes_recv': net.bytes_recv,
            'network_packets_sent': net.packets_sent,
            'network_packets_recv': net.packets_recv
        }
    except:
        return {'cpu_percent': 0, 'memory_percent': 0}

print("DEBUG: This is the MySQL JDBC version - timestamp:", time.time())

# JDBC configuration for MySQL
JAR_PATH = r"D:\Downloads\mysql-connector-j-9.4.0\mysql-connector-j-9.4.0\mysql-connector-j-9.4.0.jar"
JDBC_DRIVER = "com.mysql.cj.jdbc.Driver"
DB_HOST = "localhost"
DB_PORT = "3306"
DB_NAME = "neurolock"
DB_USER = "root"
DB_PASS = "JoeMama@25"  # Using the password from realtime_infer.py

JDBC_URL = f"jdbc:mysql://{DB_HOST}:{DB_PORT}/{DB_NAME}"

def ensure_jvm_started():
    """Ensure JVM is started with correct JDBC driver"""
    if not jpype.isJVMStarted():
        try:
            # Try different common paths for Java installations
            common_java_paths = [
                os.environ.get('JAVA_HOME'),
                r"C:\Program Files\Java",
                r"C:\Program Files\Microsoft\jdk-17.0.16-LTS", 
                r"C:\Program Files\Eclipse Adoptium\jdk-17.0.16.8-hotspot",
                r"C:\Program Files (x86)\Java"
            ]
            
            # Try to find the jvm.dll file
            jvm_path = None
            for path in common_java_paths:
                if path and os.path.exists(path):
                    print(f"Checking Java path: {path}")
                    for root, dirs, files in os.walk(path):
                        if "jvm.dll" in files:
                            jvm_path = os.path.join(root, "jvm.dll")
                            print(f"Found jvm.dll at: {jvm_path}")
                            break
                    if jvm_path:
                        break
            
            if jvm_path:
                try:
                    print(f"Starting JVM with: {jvm_path}")
                    jpype.startJVM(jvm_path, "-Djava.class.path=" + JAR_PATH)
                    print("[OK] JVM started successfully")
                    return True
                except Exception as e:
                    print("[WARN] Failed to start JVM with jvm.dll:", e)
                    return False
            else:
                print("[WARN] Could not find jvm.dll in common locations")
                try:
                    jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.class.path=" + JAR_PATH)
                    return True
                except Exception as e:
                    print("[WARN] Failed to start default JVM:", e)
                    return False
        except Exception as e:
            print("[ERROR] JVM start failed:", str(e))
            return False
    else:
        return True

def get_jdbc_connection():
    """Get JDBC connection to MySQL"""
    ok = ensure_jvm_started()
    if not ok:
        return None
    try:
        return jaydebeapi.connect(JDBC_DRIVER, JDBC_URL, [DB_USER, DB_PASS], JAR_PATH)
    except Exception as e:
        print("[WARN] Failed to create JDBC connection:", e)
        return None


def get_py_connection():
    """Return a mysql.connector connection (pure Python)"""
    try:
        return mysql.connector.connect(host=DB_HOST, port=int(DB_PORT), database=DB_NAME, user=DB_USER, password=DB_PASS, autocommit=True)
    except Exception as e:
        print("[ERROR] mysql.connector connection failed:", e)
        return None

# Global flag to indicate if we're running without database
SKIP_DB_MODE = False  # Default to using database

def setup_database(skip_db=False):
    """Create MySQL database table via JDBC"""
    global SKIP_DB_MODE
    if skip_db:
        SKIP_DB_MODE = True
        print("[WARN] Skipping database setup - running in no-database mode")
        return True
        
    # Try JDBC first, but fall back to mysql-connector if JDBC unavailable
    conn = get_jdbc_connection()
    if conn:
        try:
            cursor = conn.cursor()
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
            cursor.close(); conn.close()
            print("[OK] MySQL Database table ready (JDBC)")
            return True
        except Exception as e:
            print("[WARN] JDBC table creation failed:", e)

    # Try pure-Python connector
    pyc = get_py_connection()
    if pyc:
        try:
            cur = pyc.cursor()
            cur.execute("""
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
            cur.close(); pyc.close()
            print("[OK] MySQL Database table ready (mysql.connector)")
            return True
        except Exception as e:
            print("[ERROR] mysql.connector table creation failed:", e)

    print("[WARN] Running in no-database mode instead")
    SKIP_DB_MODE = True
    return False

def log_event(event_type, event_data):
    timestamp = time.time()
    event_string = f"{event_type}:{json.dumps(event_data)}"
    hashed_event = hash_with_rust(event_string)
    
    if not hashed_event:
        return
    
    # When running in no-database mode, just print the event
    if 'SKIP_DB_MODE' in globals() and SKIP_DB_MODE:
        print(f"Event logged (no DB): {timestamp} - {event_type} - {hashed_event[:20]}...")
        return

    # Try JDBC insert first if available
    conn = get_jdbc_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Use parameterized insert where possible
            try:
                cursor.execute("INSERT INTO behavior_logs (timestamp, event_type, hashed_event, raw_data) VALUES (?, ?, ?, ?)", (timestamp, event_type, hashed_event, json.dumps(event_data)))
            except Exception:
                # jaydebeapi may use different paramstyle; fall back to string formatting
                et = event_type.replace("'", "''")
                he = hashed_event.replace("'", "''")
                rd = json.dumps(event_data).replace("'", "''")
                sql = f"INSERT INTO behavior_logs (timestamp, event_type, hashed_event, raw_data) VALUES ({timestamp}, '{et}', '{he}', '{rd}')"
                cursor.execute(sql)
            cursor.close(); conn.close()
            print("[OK] MySQL Logged (JDBC):", event_type)
            return
        except Exception as e:
            print("[WARN] JDBC insert failed:", e)

    # Fall back to pure-Python mysql.connector
    pyc = get_py_connection()
    if pyc:
        try:
            cur = pyc.cursor()
            cur.execute("INSERT INTO behavior_logs (timestamp, event_type, hashed_event, raw_data) VALUES (%s, %s, %s, %s)", (timestamp, event_type, hashed_event, json.dumps(event_data)))
            cur.close(); pyc.close()
            print("[OK] MySQL Logged (mysql.connector):", event_type)
            return
        except Exception as e:
            print("[ERROR] mysql.connector insert failed:", e)

    # If we reach here, no DB method worked; print the event
    print(f"Event logged (no DB available): {timestamp} - {event_type} - {hashed_event[:20]}...")

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

    # Setup database - using database mode
    db_setup_result = setup_database(skip_db=False)
    
    # Test database connection only if we're not in no-database mode
    if not SKIP_DB_MODE:
        try:
            conn = get_jdbc_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM behavior_logs")
            count = cursor.fetchone()[0]
            print(f"[OK] JDBC Database connection successful! Table has {count} rows.")
            cursor.close()
            conn.close()
        except Exception as e:
            print("[ERROR] JDBC Database connection failed:", str(e))
            print("[WARN] Running in no-database mode instead")
            SKIP_DB_MODE = True

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