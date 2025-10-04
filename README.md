# Neurolock 

An intelligent behavior monitoring and anomaly detection system that leverages machine learning to identify suspicious user patterns in real-time.

## Overview

Neurolock captures user interactions (keystrokes, mouse movements, system metrics), processes them through cryptographic hashing, and uses neural networks to detect anomalous behavior patterns that could indicate security threats or unauthorized access.

##  Features

- **Real-time Behavior Capture**: Monitors keystrokes, mouse clicks, and system metrics
- **Cryptographic Hashing**: Rust-powered secure data hashing for privacy
- **Neural Network Detection**: GRU-based deep learning for pattern recognition
- **Enterprise Integration**: JDBC connectivity with SQL Server
- **Live Monitoring**: Real-time anomaly detection and alerting
- **Privacy-First**: All behavioral data is hashed before storage

##  Project Structure

├── python/ │ ├── behavior_log.py 
            # Main data collection │ ├── realtime_infer.py 
            # Live anomaly detection │ └── test_jdbc_simple.py 
            # Database connectivity tests ├── models/ 
                │ └── train_gru.py 
            # Neural network training ├── utils/ 
                │ └── preprocess.py 
    # Data preprocessing 
├── rust_hasher/ │ ├── src/ 
                    │ │ ├── main.rs # Rust hashing implementation 
                    │ │ └── hasher.rs # Cryptographic functions 
| └── Cargo.toml └── README.md

