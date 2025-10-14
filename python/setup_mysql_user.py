import jaydebeapi
import jpype
import os
import time
import getpass
import sys
import random
import string

print("MySQL Setup Tool for Behavior Logger")
print("==================================")

# JDBC configuration for MySQL
JAR_PATH = r"D:\Downloads\mysql-connector-j-9.4.0\mysql-connector-j-9.4.0\mysql-connector-j-9.4.0.jar"
JDBC_DRIVER = "com.mysql.cj.jdbc.Driver"
DB_CONFIG = {
    'host': 'localhost',
    'port': '3306',
    'database': 'mysql',  # Use the MySQL system database
}

# Function to initialize JVM
def ensure_jvm_started():
    if not jpype.isJVMStarted():
        try:
            # Try different common paths for Java installations
            common_java_paths = [
                os.environ.get('JAVA_HOME'),
                r"C:\Program Files\Java",
                r"C:\Program Files\Microsoft\jdk-17.0.16-LTS"
            ]
            
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
                print(f"Starting JVM with: {jvm_path}")
                jpype.startJVM(jvm_path, "-Djava.class.path=" + JAR_PATH)
                print("✅ JVM started successfully")
                return True
            else:
                print("❌ Could not find jvm.dll in common locations")
                return False
        except Exception as e:
            print(f"❌ JVM start failed: {e}")
            return False
    return True

# Main function
# Generate a random password
def generate_password(length=12):
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(chars) for _ in range(length))

# Update config files with new credentials
def update_config_files(username, password, database):
    # Update behavior_log.py
    try:
        print("\n⏳ Updating behavior_log.py with new credentials...")
        with open('behavior_log.py', 'r') as file:
            content = file.read()
            
        # Find the section with database configuration
        db_section = content.find('# JDBC configuration for MySQL')
        if db_section >= 0:
            # Find the lines to replace
            user_line_start = content.find('DB_USER = ', db_section)
            pass_line_start = content.find('DB_PASS = ', db_section)
            
            if user_line_start >= 0 and pass_line_start >= 0:
                # Find line ends
                user_line_end = content.find('\n', user_line_start)
                pass_line_end = content.find('\n', pass_line_start)
                
                # Replace lines
                content = content[:user_line_start] + f'DB_USER = "{username}"' + content[user_line_end:]
                content = content[:pass_line_start] + f'DB_PASS = "{password}"' + content[pass_line_end:]
                
                # Find skip_db line
                skip_db_line = content.find('db_setup_result = setup_database(skip_db=True)')
                if skip_db_line >= 0:
                    skip_db_line_end = content.find('\n', skip_db_line)
                    content = content[:skip_db_line] + 'db_setup_result = setup_database(skip_db=False)' + content[skip_db_line_end:]
                
                # Write back to file
                with open('behavior_log.py', 'w') as file:
                    file.write(content)
                print("✅ behavior_log.py updated")
        
        # Update realtime_infer.py
        print("\n⏳ Updating realtime_infer.py with new credentials...")
        with open('realtime_infer.py', 'r') as file:
            content = file.read()
            
        # Find the section with database configuration
        db_section = content.find('DB_CONFIG = {')
        if db_section >= 0:
            # Find the lines to replace
            user_line_start = content.find("'user': ", db_section)
            pass_line_start = content.find("'password': ", db_section)
            
            if user_line_start >= 0 and pass_line_start >= 0:
                # Find line ends
                user_line_end = content.find(',', user_line_start)
                pass_line_end = content.find('\n', pass_line_start)
                
                # Replace lines
                content = content[:user_line_start] + f"'user': '{username}'" + content[user_line_end:]
                content = content[:pass_line_start] + f"'password': '{password}'" + content[pass_line_end:]
                
                # Find skip_db line
                skip_db_line = content.find('SKIP_DB_MODE = True')
                if skip_db_line >= 0:
                    skip_db_line_end = content.find('\n', skip_db_line)
                    content = content[:skip_db_line] + 'SKIP_DB_MODE = False  # Using database mode' + content[skip_db_line_end:]
                
                # Write back to file
                with open('realtime_infer.py', 'w') as file:
                    file.write(content)
                print("✅ realtime_infer.py updated")
                
        return True
    except Exception as e:
        print(f"❌ Error updating config files: {e}")
        return False

if __name__ == "__main__":
    # Initialize JVM
    if not ensure_jvm_started():
        print("❌ JVM initialization failed")
        exit(1)
    
    print("\n🔍 MySQL Connection Setup")
    print("======================")
    print("This tool will help you set up MySQL for the Behavior Logger.")
    print("Options:")
    print("1. Create new MySQL user and database")
    print("2. Use existing MySQL user and database")
    print("3. Test connection only")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ")
    
    if choice == '4':
        print("Exiting setup.")
        sys.exit(0)
        
    # Get MySQL connection details
    if choice in ['1', '2', '3']:
        print("\nEnter MySQL connection details:")
        mysql_user = input("MySQL username (default: root): ") or "root"
        mysql_pass = getpass.getpass(f"MySQL password for {mysql_user}: ")
        
        # Try to connect
        print(f"\n⏳ Connecting to MySQL as {mysql_user}...")
        url = f"jdbc:mysql://{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        
        try:
            conn = jaydebeapi.connect(
                JDBC_DRIVER,
                url,
                [mysql_user, mysql_pass],
                JAR_PATH
            )
            print("✅ Connected to MySQL successfully!")
            
            if choice == '1':
                # Create new user and database
                print("\n⏳ Setting up new database and user...")
                
                # Ask for database name or use default
                db_name = input("Enter database name (default: neurolock): ") or "neurolock"
                
                # Generate username and password or ask for them
                use_generated = input("Generate random username and password? (y/n, default: y): ").lower() != 'n'
                
                if use_generated:
                    username = f"neurolock_{random.randint(1000, 9999)}"
                    password = generate_password()
                else:
                    username = input("Enter new MySQL username: ")
                    password = getpass.getpass("Enter password for new user: ")
                
                cursor = conn.cursor()
                
                # Create database
                try:
                    print(f"Creating database '{db_name}'...")
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
                    
                    # Create user
                    print(f"Creating user '{username}'...")
                    cursor.execute(f"CREATE USER '{username}'@'localhost' IDENTIFIED BY '{password}'")
                    
                    # Grant privileges
                    print(f"Granting privileges to '{username}'...")
                    cursor.execute(f"GRANT ALL PRIVILEGES ON {db_name}.* TO '{username}'@'localhost'")
                    cursor.execute("FLUSH PRIVILEGES")
                    
                    print("\n✅ Database setup completed successfully!")
                    print(f"Database: {db_name}")
                    print(f"Username: {username}")
                    print(f"Password: {password}")
                    
                    # Update config files
                    update_config_files(username, password, db_name)
                    
                except Exception as e:
                    print(f"❌ Error creating database/user: {e}")
                
                cursor.close()
                
            elif choice == '2':
                # Use existing user and database
                print("\n⏳ Using existing database and user...")
                
                db_name = input("Enter existing database name: ")
                username = input("Enter existing MySQL username: ")
                password = getpass.getpass("Enter password for the user: ")
                
                # Test connection with provided credentials
                try:
                    test_url = f"jdbc:mysql://{DB_CONFIG['host']}:{DB_CONFIG['port']}/{db_name}"
                    test_conn = jaydebeapi.connect(
                        JDBC_DRIVER,
                        test_url,
                        [username, password],
                        JAR_PATH
                    )
                    test_conn.close()
                    print("✅ Connection test successful with provided credentials!")
                    
                    # Update config files
                    update_config_files(username, password, db_name)
                    
                except Exception as e:
                    print(f"❌ Connection test failed with provided credentials: {e}")
                
            elif choice == '3':
                # Just test connection
                print("✅ Connection test completed successfully!")
                
            # Close the admin connection
            conn.close()
            
        except Exception as e:
            print(f"❌ MySQL connection failed: {e}")
            print("Please check your MySQL credentials and try again.")
    else:
        print("Invalid choice. Exiting.")
        sys.exit(1)