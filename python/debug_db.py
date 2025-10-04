import pyodbc
import time

def debug_database():
    print("Debugging database connection and data...")
    print("=" * 50)
    
    # First, check what ODBC drivers are available
    print("Available ODBC drivers:")
    try:
        drivers = pyodbc.drivers()
        for driver in drivers:
            if 'SQL Server' in driver:
                print(f"  ✅ {driver}")
    except Exception as e:
        print(f"  ❌ Error getting drivers: {e}")
    
    print("\n" + "=" * 50)
    
    try:
        # Use the same connection string as your behavior_log.py
        connection_strings = [
            "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=behavior_db;Trusted_Connection=yes;",
            "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=behavior_db;Trusted_Connection=yes;",
            "DRIVER={ODBC Driver 17 for SQL Server};SERVER=.\\SQLEXPRESS;DATABASE=behavior_db;Trusted_Connection=yes;",
            "DRIVER={SQL Server};SERVER=localhost\\SQLEXPRESS;DATABASE=behavior_db;Trusted_Connection=yes;",
            "DRIVER={SQL Server Native Client 11.0};SERVER=localhost\\SQLEXPRESS;DATABASE=behavior_db;Trusted_Connection=yes;",
        ]
        
        connected = False
        for i, conn_str in enumerate(connection_strings, 1):
            try:
                print(f"Trying connection {i}: {conn_str[:50]}...")
                conn = pyodbc.connect(conn_str, timeout=10)
                cursor = conn.cursor()
                
                # Get server info
                cursor.execute("SELECT @@VERSION")
                version = cursor.fetchone()[0]
                print(f"✅ Connected! SQL Server version: {version[:100]}...")
                
                # Check current database
                cursor.execute("SELECT DB_NAME()")
                current_db = cursor.fetchone()[0]
                print(f"✅ Current database: {current_db}")
                
                # Check table exists
                cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'behavior_logs'")
                table_exists = cursor.fetchone()[0]
                print(f"✅ Table 'behavior_logs' exists: {table_exists}")
                
                if table_exists:
                    # Check record count
                    cursor.execute("SELECT COUNT(*) FROM behavior_logs")
                    count = cursor.fetchone()[0]
                    print(f"📊 Current record count: {count}")
                    
                    # Show recent records if any
                    if count > 0:
                        cursor.execute("SELECT TOP 5 id, timestamp, LEFT(ISNULL(hashed_event, 'NULL'), 50) as hash_preview FROM behavior_logs ORDER BY id DESC")
                        rows = cursor.fetchall()
                        print("Recent records:")
                        for row in rows:
                            print(f"  ID {row[0]}: {row[1]} - {row[2]}")
                else:
                    print("❌ Table 'behavior_logs' does not exist")
                
                # Test inserting a record
                print("\n🧪 Testing manual insert...")
                test_timestamp = time.time()
                cursor.execute("""
                    INSERT INTO behavior_logs (timestamp, hashed_event)
                    VALUES (?, ?)
                """, (test_timestamp, "TEST_HASH_123"))
                conn.commit()
                
                # Check if it was inserted
                cursor.execute("SELECT COUNT(*) FROM behavior_logs WHERE hashed_event = 'TEST_HASH_123'")
                test_count = cursor.fetchone()[0]
                print(f"✅ Test insert successful: {test_count} test record found")
                
                # Show the inserted record
                cursor.execute("SELECT id, timestamp, hashed_event FROM behavior_logs WHERE hashed_event = 'TEST_HASH_123'")
                test_record = cursor.fetchone()
                print(f"✅ Test record: ID={test_record[0]}, Timestamp={test_record[1]}, Hash={test_record[2]}")
                
                # Clean up test record
                cursor.execute("DELETE FROM behavior_logs WHERE hashed_event = 'TEST_HASH_123'")
                conn.commit()
                print("✅ Test record cleaned up")
                
                cursor.close()
                conn.close()
                connected = True
                break
                
            except Exception as e:
                print(f"❌ Connection {i} failed: {e}")
                continue
        
        if not connected:
            print("❌ Could not connect to database with any connection string")
            print("\n🔧 Troubleshooting suggestions:")
            print("1. SQL Server Express might not be installed")
            print("2. SQL Server service might not be running")
            print("3. Instance name might be different")
            print("4. Windows Authentication might not be enabled")
            
    except Exception as e:
        print(f"❌ Debug failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_database()