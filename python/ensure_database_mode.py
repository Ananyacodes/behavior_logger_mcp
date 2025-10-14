#!/usr/bin/env python
"""
Behavior Logger Database Integration Script
This script ensures that behavior_log.py writes to the database by setting the
correct configuration parameters.
"""

import os
import sys
import fileinput
import subprocess
import time

def update_behavior_log_script():
    """Update behavior_log.py to use database mode"""
    script_path = "C:\\Users\\Ananya\\behavior_logger\\python\\behavior_log.py"
    
    print("Updating behavior_log.py to use database mode...")
    
    # Check if file exists
    if not os.path.exists(script_path):
        print(f"Error: {script_path} not found!")
        return False
        
    # Parameters to change
    changes = [
        ("setup_database(skip_db=True)", "setup_database(skip_db=False)"),
        ("SKIP_DB_MODE = True", "SKIP_DB_MODE = False"),
        ("# SKIP_DB_MODE = False", "SKIP_DB_MODE = False")
    ]
    
    try:
        # Read the file
        with open(script_path, 'r') as file:
            content = file.read()
            
        # Make changes
        for old_str, new_str in changes:
            if old_str in content:
                content = content.replace(old_str, new_str)
                print(f"  Changed '{old_str}' to '{new_str}'")
                
        # Write back to file
        with open(script_path, 'w') as file:
            file.write(content)
            
        print("✅ Updated behavior_log.py successfully!")
        return True
        
    except Exception as e:
        print(f"Error updating file: {e}")
        return False

def update_realtime_infer_script():
    """Update realtime_infer.py to use database mode"""
    script_path = "C:\\Users\\Ananya\\behavior_logger\\python\\realtime_infer.py"
    
    print("Updating realtime_infer.py to use database mode...")
    
    # Check if file exists
    if not os.path.exists(script_path):
        print(f"Error: {script_path} not found!")
        return False
        
    # Parameters to change
    changes = [
        ("SKIP_DB_MODE = True", "SKIP_DB_MODE = False"),
        ("# if not setup_database():", "if not setup_database():"),
        ("#     print", "    print"),
        ("#     return", "    return"),
        ("print(\"⚠️ Running in no-database mode", "print(\"✅ Running in database mode")
    ]
    
    try:
        # Read the file
        with open(script_path, 'r') as file:
            content = file.read()
            
        # Make changes
        for old_str, new_str in changes:
            if old_str in content:
                content = content.replace(old_str, new_str)
                print(f"  Changed '{old_str}' to '{new_str}'")
                
        # Write back to file
        with open(script_path, 'w') as file:
            file.write(content)
            
        print("✅ Updated realtime_infer.py successfully!")
        return True
        
    except Exception as e:
        print(f"Error updating file: {e}")
        return False

def test_database_connection():
    """Test database connection"""
    print("Testing database connection...")
    try:
        import jaydebeapi
        import jpype
        
        # JDBC configuration for MySQL
        JAR_PATH = r"D:\Downloads\mysql-connector-j-9.4.0\mysql-connector-j-9.4.0\mysql-connector-j-9.4.0.jar"
        JDBC_DRIVER = "com.mysql.cj.jdbc.Driver"
        
        # Database connection parameters
        DB_HOST = "localhost"
        DB_PORT = "3306"
        DB_NAME = "neurolock"
        DB_USER = "root"
        DB_PASS = "JoeMama@25"
        
        JDBC_URL = f"jdbc:mysql://{DB_HOST}:{DB_PORT}/{DB_NAME}"
        
        # Initialize JVM
        if not jpype.isJVMStarted():
            # Find JVM path
            for path in [r"C:\Program Files\Java"]:
                if os.path.exists(path):
                    for root, dirs, files in os.walk(path):
                        if "jvm.dll" in files:
                            jvm_path = os.path.join(root, "jvm.dll")
                            print(f"Found JVM at: {jvm_path}")
                            
                            # Start JVM
                            jpype.startJVM(jvm_path, "-Djava.class.path=" + JAR_PATH)
                            break
                    if jpype.isJVMStarted():
                        break
        
        # Check if JVM started
        if not jpype.isJVMStarted():
            print("❌ Failed to start JVM")
            return False
        
        # Connect to database
        conn = jaydebeapi.connect(
            JDBC_DRIVER,
            JDBC_URL,
            [DB_USER, DB_PASS],
            JAR_PATH
        )
        
        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"✅ Connected to MySQL version: {version}")
        
        # Count rows in behavior_logs
        cursor.execute("SELECT COUNT(*) FROM behavior_logs")
        count = cursor.fetchone()[0]
        print(f"✅ behavior_logs table has {count} rows")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    print("Behavior Logger Database Integration")
    print("===================================")
    
    # Update scripts
    update_behavior_log_script()
    update_realtime_infer_script()
    
    # Test connection
    test_database_connection()
    
    print("\nAll setup complete! You can now run the Java UI to view and manage your data.")
    print("To start the UI, go to the java directory and run: build_and_run.bat")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()