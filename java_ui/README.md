# Behavior Logger UI

A Java Swing interface for viewing and managing your MySQL Behavior Logger database.

## Features

- **Data Explorer:** View and filter data from different tables in the database
- **Dashboard:** See system metrics and activity summary
- **Log Viewer:** Review application logs
- **Settings:** Configure database connection and application settings

## Requirements

- Java JDK 8 or later
- MySQL database with the Behavior Logger schema
- MySQL Connector/J JAR file (included in the lib directory)

## Running the Application

### Windows

1. Open Command Prompt in this directory
2. Run the application:
   ```
   run.bat
   ```

### Linux/macOS

1. Open Terminal in this directory
2. Make the run script executable:
   ```
   chmod +x run.sh
   ```
3. Run the application:
   ```
   ./run.sh
   ```

## Troubleshooting

### Database Connection Issues

- Make sure your MySQL server is running
- Verify the database connection settings in BehaviorLoggerUI.java:
  ```java
  private static final String JDBC_URL = "jdbc:mysql://localhost:3306/neurolock";
  private static final String USERNAME = "root";
  private static final String PASSWORD = "JoeMama@25"; // Update with your password
  ```
- Ensure the neurolock database exists

### MySQL Connector JAR Issues

- If you get ClassNotFoundException for MySQL classes, make sure mysql-connector-j-9.4.0.jar is in the lib directory
- You may need to download the JAR from: https://dev.mysql.com/downloads/connector/j/

## Working with the Behavior Logger

1. Run the Python script to collect data:
   ```
   python behavior_log.py
   ```

2. Open the Java UI to view the collected data:
   ```
   run.bat  # Windows
   ./run.sh  # Linux/macOS
   ```

3. Use the Data Explorer tab to see the events stored in your database