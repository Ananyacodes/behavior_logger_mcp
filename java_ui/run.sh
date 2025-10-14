#!/bin/bash
# Build and Run the Java Swing Interface for Behavior Logger

echo "Building Behavior Logger UI..."

# Check if Java is installed
if ! command -v java &> /dev/null; then
    echo "Error: Java not found. Please install Java JDK."
    exit 1
fi

# Check if MySQL connector JAR exists
if [ ! -f "lib/mysql-connector-j-9.4.0.jar" ]; then
    echo "Error: MySQL connector JAR not found in lib directory."
    echo "Checking original location..."
    
    if [ -f "D:/Downloads/mysql-connector-j-9.4.0/mysql-connector-j-9.4.0/mysql-connector-j-9.4.0.jar" ]; then
        echo "Found JAR file in downloads folder. Copying to lib directory..."
        mkdir -p lib
        cp "D:/Downloads/mysql-connector-j-9.4.0/mysql-connector-j-9.4.0/mysql-connector-j-9.4.0.jar" "lib/"
    else
        echo "Error: MySQL connector JAR not found."
        echo "Please download it and place in the lib directory."
        exit 1
    fi
fi

echo "Compiling Java files..."
javac -cp ".:lib/mysql-connector-j-9.4.0.jar" BehaviorLoggerUI.java

if [ $? -ne 0 ]; then
    echo "Error: Compilation failed."
    exit 1
fi

echo "Running Behavior Logger UI..."
java -cp ".:lib/mysql-connector-j-9.4.0.jar" BehaviorLoggerUI

echo "Done."