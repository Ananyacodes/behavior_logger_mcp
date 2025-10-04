import jaydebeapi
import os
import jpype

def test_basic_jdbc():
    print("Testing basic JDBC connection...")
    
    jar_path = "mssql-jdbc-12.4.2.jre8.jar"
    
    if not os.path.exists(jar_path):
        print(f"❌ JAR file not found: {jar_path}")
        return
    
    try:
        # Set the correct Java path
        java_home = "C:\\Program Files\\Microsoft\\jdk-17.0.16.8-hotspot"
        os.environ['JAVA_HOME'] = java_home
        
        print(f"Using Java at: {java_home}")
        
        # Start JVM manually
        if not jpype.isJVMStarted():
            jvm_path = os.path.join(java_home, "bin", "server", "jvm.dll")
            print(f"Starting JVM with: {jvm_path}")
            jpype.startJVM(jvm_path, "-Djava.class.path=" + jar_path)
        
        driver = "com.microsoft.sqlserver.jdbc.SQLServerDriver"
        
        # Try different connection URLs
        urls = [
            # Force Named Pipes - this should work
            "jdbc:sqlserver://localhost\\SQLEXPRESS;databaseName=behavior_db;integratedSecurity=true;trustServerCertificate=true;encrypt=false;",
            # Named Pipes explicit
            "jdbc:sqlserver://localhost;instanceName=SQLEXPRESS;databaseName=behavior_db;integratedSecurity=true;trustServerCertificate=true;encrypt=false;",
            # Simple local connection
            "jdbc:sqlserver://.\\SQLEXPRESS;databaseName=behavior_db;integratedSecurity=true;trustServerCertificate=true;encrypt=false;",
        ]
        
        for i, url in enumerate(urls, 1):
            try:
                print(f"Attempt {i}: Trying connection...")
                print(f"URL: {url}")
                conn = jaydebeapi.connect(driver, url, ["", ""], jar_path)
                print("✅ JDBC connection successful!")
                
                cursor = conn.cursor()
                cursor.execute("SELECT 'JDBC works!' as test, @@SERVERNAME as server")
                result = cursor.fetchone()
                print(f"✅ Query result: {result[0]} from server: {result[1]}")
                
                # Test actual database query
                cursor.execute("SELECT COUNT(*) FROM behavior_logs")
                count = cursor.fetchone()[0]
                print(f"✅ behavior_logs table has {count} rows")
                
                cursor.close()
                conn.close()
                print("✅ JDBC test complete!")
                return
                
            except Exception as e:
                print(f"❌ Attempt {i} failed: {str(e)[:150]}...")
                continue
        
        print("❌ All connection attempts failed")
        
    except Exception as e:
        print(f"❌ JDBC test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_basic_jdbc()