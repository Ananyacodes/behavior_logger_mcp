#!/usr/bin/env python
"""
Simple Behavior Analysis Tool - ASCII Only Version
Analyzes behavior data without Unicode characters that cause encoding issues.
"""

import os
import sys
import jaydebeapi
import jpype
import pandas as pd
from datetime import datetime, timedelta
import time

# Database connection parameters
DB_CONFIG = {
    "host": "localhost",
    "port": "3306", 
    "database": "neurolock",
    "user": "root",
    "password": "JoeMama@25"
}

# JDBC configuration
JDBC_CONFIG = {
    "driver": "com.mysql.cj.jdbc.Driver",
    "jar_path": r"D:\Downloads\mysql-connector-j-9.4.0\mysql-connector-j-9.4.0\mysql-connector-j-9.4.0.jar",
    "url": f"jdbc:mysql://{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
}

def init_jvm():
    """Initialize JVM for JDBC connection"""
    if not jpype.isJVMStarted():
        # Find JVM path
        jvm_path = None
        for path in [r"C:\Program Files\Java"]:
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    if "jvm.dll" in files:
                        jvm_path = os.path.join(root, "jvm.dll")
                        break
                if jvm_path:
                    break
        
        if jvm_path:
            jpype.startJVM(jvm_path, "-Djava.class.path=" + JDBC_CONFIG["jar_path"])
            print("[OK] JVM initialized successfully")
            return True
        else:
            print("[ERROR] Could not find JVM path")
            return False
    return True

def connect_to_database():
    """Connect to the MySQL database"""
    try:
        connection = jaydebeapi.connect(
            JDBC_CONFIG["driver"],
            JDBC_CONFIG["url"],
            [DB_CONFIG["user"], DB_CONFIG["password"]],
            JDBC_CONFIG["jar_path"]
        )
        print("[OK] Connected to database successfully")
        return connection
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return None

def analyze_behavior_data(connection):
    """Analyze the current behavior data"""
    try:
        cursor = connection.cursor()
        
        # Get basic statistics
        cursor.execute("SELECT COUNT(*) FROM behavior_logs")
        total_events = cursor.fetchone()[0]
        print(f"Total events in database: {total_events}")
        
        # Get event type distribution
        cursor.execute("""
            SELECT event_type, COUNT(*) as count 
            FROM behavior_logs 
            GROUP BY event_type 
            ORDER BY count DESC
        """)
        
        print("\nEvent Type Distribution:")
        print("-" * 30)
        event_types = cursor.fetchall()
        for event_type, count in event_types:
            percentage = (count / total_events) * 100 if total_events > 0 else 0
            print(f"{event_type}: {count} ({percentage:.1f}%)")
        
        # Get recent activity (last hour)
        cursor.execute("""
            SELECT COUNT(*) FROM behavior_logs 
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """)
        recent_events = cursor.fetchone()[0]
        print(f"\nEvents in last hour: {recent_events}")
        
        # Get top applications
        cursor.execute("""
            SELECT application, COUNT(*) as count 
            FROM behavior_logs 
            WHERE application IS NOT NULL AND application != ''
            GROUP BY application 
            ORDER BY count DESC 
            LIMIT 5
        """)
        
        print("\nTop 5 Applications:")
        print("-" * 30)
        apps = cursor.fetchall()
        for app, count in apps:
            print(f"{app}: {count} events")
        
        # Activity pattern analysis
        cursor.execute("""
            SELECT HOUR(timestamp) as hour, COUNT(*) as count 
            FROM behavior_logs 
            WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY)
            GROUP BY HOUR(timestamp) 
            ORDER BY hour
        """)
        
        print("\nActivity by Hour (Last 24 hours):")
        print("-" * 40)
        hourly_data = cursor.fetchall()
        for hour, count in hourly_data:
            bar = "#" * min(50, count // 2)  # Simple text bar chart
            print(f"{hour:02d}:00 [{count:4d}] {bar}")
        
        cursor.close()
        return True
        
    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")
        return False

def main():
    print("Behavior Data Analysis Tool")
    print("=" * 30)
    
    # Initialize JVM
    if not init_jvm():
        return
    
    # Connect to database
    connection = connect_to_database()
    if not connection:
        return
    
    try:
        # Run analysis
        print("\nAnalyzing behavior data...")
        analyze_behavior_data(connection)
        
        print("\nAnalysis complete!")
        
    finally:
        # Clean up
        if connection:
            connection.close()
            print("\nDatabase connection closed.")

if __name__ == "__main__":
    main()