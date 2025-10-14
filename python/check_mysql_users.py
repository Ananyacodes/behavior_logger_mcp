import subprocess
import sys
import os

print("MySQL User Check")
print("===============")

def run_command(command):
    """Run a command and return its output"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=False,
            capture_output=True,
            text=True
        )
        return result.stdout, result.stderr, result.returncode
    except Exception as e:
        return "", str(e), -1

# Try to check MySQL using the mysql command-line client
print("\nTrying to use MySQL client to check users...")
stdout, stderr, code = run_command("mysql --version")
if code == 0:
    print(f"MySQL client found: {stdout.strip()}")
    
    # Try to connect without password
    print("\nAttempting connection without password...")
    stdout, stderr, code = run_command("mysql -u root -e \"SELECT 'Connection successful'\" 2>&1")
    if code == 0:
        print("✅ Successfully connected to MySQL without password!")
        
        # List users
        print("\nListing MySQL users...")
        stdout, stderr, code = run_command("mysql -u root -e \"SELECT user, host FROM mysql.user\" 2>&1")
        if code == 0:
            print(stdout)
        else:
            print(f"❌ Failed to list users: {stderr}")
            
        # Get MySQL version
        print("\nChecking MySQL version...")
        stdout, stderr, code = run_command("mysql -u root -e \"SELECT VERSION()\" 2>&1")
        if code == 0:
            print(stdout)
        else:
            print(f"❌ Failed to get version: {stderr}")
            
        # Check if neurolock database exists
        print("\nChecking if 'neurolock' database exists...")
        stdout, stderr, code = run_command("mysql -u root -e \"SHOW DATABASES LIKE 'neurolock'\" 2>&1")
        if code == 0:
            if 'neurolock' in stdout:
                print("✅ Database 'neurolock' exists!")
            else:
                print("❌ Database 'neurolock' does not exist")
                
                # Create the database
                print("\nCreating 'neurolock' database...")
                stdout, stderr, code = run_command("mysql -u root -e \"CREATE DATABASE neurolock\" 2>&1")
                if code == 0:
                    print("✅ Successfully created 'neurolock' database!")
                else:
                    print(f"❌ Failed to create database: {stderr}")
        else:
            print(f"❌ Failed to check databases: {stderr}")
    else:
        # Try with password prompt
        print("\nFailed without password. Attempting with password prompt...")
        print("Please enter your MySQL root password when prompted.")
        cmd = "mysql -u root -p -e \"SELECT 'Connection successful'\""
        os.system(cmd)
else:
    print("❌ MySQL client not found in PATH")
    print("Please install MySQL client or add it to your PATH")

print("\nRecommendations:")
print("1. If you can connect with the MySQL command-line client, update your connection parameters in the code")
print("2. If you can't connect, check your MySQL installation and credentials")
print("3. You might need to reset your MySQL root password if you don't know it")