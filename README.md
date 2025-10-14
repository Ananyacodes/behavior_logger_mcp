# Behavior Logger System

An intelligent behavior monitoring and anomaly detection system that leverages machine learning to identify suspicious user patterns in real-time.

## Overview

It captures user interactions (keystrokes, mouse movements, system metrics), processes them through cryptographic hashing, and uses neural networks to detect anomalous behavior patterns that could indicate security threats or unauthorized access.

## Features

- **Real-time Behavior Capture**: Monitors keystrokes, mouse clicks, and system metrics
- **Cryptographic Hashing**: Rust-powered secure data hashing for privacy
- **Neural Network Detection**: GRU-based deep learning for pattern recognition
- **Enterprise Integration**: JDBC connectivity with MySQL database
- **Live Monitoring**: Real-time anomaly detection and alerting
- **Privacy-First**: All behavioral data is hashed before storage
- **Multiple UI Options**: Java Swing and Python Tkinter interfaces for data visualization

## Components

### Python Components

- `behavior_log.py` - Core logging application that captures user behavior data
- `realtime_infer.py` - Analyzes behavior data for patterns and anomalies
- `ensure_database_mode.py` - Helper script to ensure database mode is enabled
- `mysql_viewer.py` - Python-based UI for viewing database content

### Java Components

- `BehaviorLoggerUI.java` - Basic Java UI for viewing and managing behavior data
- `BehaviorLoggerUIEnhanced.java` - Extended UI with JFreeChart visualizations
- `BehaviorLoggerUIMain.java` - Entry point that selects the appropriate UI version

### Rust Components

- `hasher.rs` - Helper library for data processing
- `main.rs` - Rust entry point for integration with the behavior logger

## Project Structure

```
├── python/
│   ├── behavior_log.py          # Main data collection
│   ├── behavior_log.csv         # Local data storage (when DB unavailable)
│   ├── realtime_infer.py        # Live anomaly detection
│   ├── ensure_database_mode.py  # Database setup helper
│   └── mysql_viewer.py          # Python UI for database viewing
├── java/
│   ├── BehaviorLoggerUI.java    # Basic Java UI
│   ├── BehaviorLoggerUIEnhanced.java # Advanced Java UI with charts
│   ├── BehaviorLoggerUIMain.java     # UI launcher
│   └── build_and_run.bat        # Compilation and execution script
├── rust_hasher/
│   ├── src/
│   │   ├── main.rs              # Rust hashing implementation
│   │   └── hasher.rs            # Cryptographic functions
│   └── Cargo.toml
├── view_database.bat            # Quick database viewer launcher
└── README.md
```

## Usage Instructions

### Running the Behavior Logger

1. Run `behavior_log.py` to start collecting behavior data
   ```
   python python\behavior_log.py
   ```

2. Data will be stored in the MySQL database under the `behavior_logs` table.

### Viewing the Data

#### Option 1: Using Java UI (recommended)

1. Run the Java UI by executing `build_and_run.bat` in the `java` directory.
   ```
   cd java
   build_and_run.bat
   ```

2. This will compile and launch the UI application. It will automatically attempt to load the enhanced version with JFreeChart visualizations if available.

#### Option 2: Using Python Viewer

1. Run the MySQL viewer by executing:
   ```
   python python\mysql_viewer.py
   ```
   
   Or use the batch script:
   ```
   view_database.bat
   ```

2. This will open a tkinter-based UI for viewing and querying the database.

### Analyzing the Data

1. In either UI, navigate to the Analytics/Statistics tab.

2. You can see various metrics like:
   - Event type distribution
   - Activity patterns by hour
   - Application usage statistics
   - Keystroke patterns

### Database Configuration

Both UIs connect to the MySQL database using these settings:
- Host: localhost
- Port: 3306
- Database: neurolock
- Username: root
- Password: JoeMama@25

## Requirements

### Python Requirements
- Python 3.8+
- pandas
- jaydebeapi
- jpype
- tkinter
- pynput (for behavior logging)

### Java Requirements
- JDK 16+
- MySQL Connector JAR (mysql-connector-j-9.4.0.jar)
- JFreeChart 1.5.3 (optional, for enhanced visualizations)

### Other Requirements
- MySQL 8.0+
- Java JVM for JDBC connections

## from the repo root
cd C:\Users\Ananya\behavior_logger\java

# compile (include connector + chart jars)
javac -cp ".;lib\mysql-connector-j-9.4.0.jar;lib\jfreechart-1.5.3.jar;lib\jcommon-1.0.24.jar" *.java

# run UI
powershell -NoProfile -ExecutionPolicy Bypass -Command "& 'C:\Users\Ananya\behavior_logger\java\build_and_run.ps1' -compileOnly"
