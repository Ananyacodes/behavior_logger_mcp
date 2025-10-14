# Behavior Logger UI

A Java Swing interface for viewing and managing behavior logger data.

## Features

- View data from any table in the database
- Filter data based on column values
- Start and stop behavior logging directly from the UI
- View data analytics (coming soon)

## Prerequisites

- Java JDK 8 or higher
- MySQL Connector/J JAR file
- MySQL database with behavior logger tables
- Python behavior logger script

## Setup

1. Make sure your MySQL database is properly configured
2. Update the database connection settings in `BehaviorLoggerUI.java` if needed:
   ```java
   private String dbUrl = "jdbc:mysql://localhost:3306/neurolock";
   private String dbUser = "root";
   private String dbPassword = "JoeMama@25"; // Update with your actual password
   ```
3. Ensure the MySQL Connector JAR path in the build scripts matches your system:
   - In `build_and_run.bat`:
     ```
     set MYSQL_JAR=D:\Downloads\mysql-connector-j-9.4.0\mysql-connector-j-9.4.0\mysql-connector-j-9.4.0.jar
     ```
   - In `build_and_run.ps1`:
     ```
     $MYSQL_JAR = "D:\Downloads\mysql-connector-j-9.4.0\mysql-connector-j-9.4.0\mysql-connector-j-9.4.0.jar"
     ```

## Running the UI

### Using Windows Command Prompt:

1. Open Command Prompt in the `java` directory
2. Run: `build_and_run.bat`

### Using PowerShell:

1. Open PowerShell in the `java` directory
2. Run: `.\build_and_run.ps1`

## Usage

1. Select a table from the dropdown menu to view its data
2. Click "Refresh" to reload data from the selected table
3. Click "Filter" to filter data based on column values
4. Use "Start Logging" to begin collecting behavior data
5. Click "Stop Logging" to stop the data collection process

## Troubleshooting

- If you see database connection errors, verify your MySQL server is running
- Make sure the behavior_log.py path is correct in the startLogging() method
- Ensure the MySQL Connector JAR path is correct in the build scripts