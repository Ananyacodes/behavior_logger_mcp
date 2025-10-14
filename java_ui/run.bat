@echo off
REM Build and Run the Java Swing Interface for Behavior Logger

echo Building Behavior Logger UI...

REM Check if Java is installed
where java >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Java not found. Please install Java JDK.
    exit /b 1
)

REM Check if MySQL connector JAR exists
if not exist "lib\mysql-connector-j-9.4.0.jar" (
    echo Error: MySQL connector JAR not found in lib directory.
    echo Checking original location...
    
    if exist "D:\Downloads\mysql-connector-j-9.4.0\mysql-connector-j-9.4.0\mysql-connector-j-9.4.0.jar" (
        echo Found JAR file in downloads folder. Copying to lib directory...
        if not exist "lib" mkdir lib
        copy "D:\Downloads\mysql-connector-j-9.4.0\mysql-connector-j-9.4.0\mysql-connector-j-9.4.0.jar" "lib\"
    ) else (
        echo Error: MySQL connector JAR not found.
        echo Please download it and place in the lib directory.
        exit /b 1
    )
)

echo Compiling Java files...
javac -cp ".;lib\mysql-connector-j-9.4.0.jar" BehaviorLoggerUI.java

if %ERRORLEVEL% NEQ 0 (
    echo Error: Compilation failed.
    exit /b 1
)

echo Running Behavior Logger UI...
java -cp ".;lib\mysql-connector-j-9.4.0.jar" BehaviorLoggerUI

echo Done.