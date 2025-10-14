@echo off
echo Behavior Logger UI - Build and Run Script
echo =======================================

REM Set Java environment variables if needed
set JAVA_HOME=C:\Program Files\Java\jdk-16.0.2
set PATH=%JAVA_HOME%\bin;%PATH%

REM Create lib directory if it doesn't exist
set LIB_DIR=lib
if not exist "%LIB_DIR%" mkdir "%LIB_DIR%"

REM Set MySQL connector JAR path
set MYSQL_JAR=D:\Downloads\mysql-connector-j-9.4.0\mysql-connector-j-9.4.0\mysql-connector-j-9.4.0.jar

REM Check if JFreeChart library exists, download if not
set JFREECHART_JAR=%LIB_DIR%\jfreechart-1.5.3.jar
if not exist "%JFREECHART_JAR%" (
    echo Downloading JFreeChart library...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://repo1.maven.org/maven2/org/jfree/jfreechart/1.5.3/jfreechart-1.5.3.jar' -OutFile '%JFREECHART_JAR%'}"
    if not exist "%JFREECHART_JAR%" (
        echo Failed to download JFreeChart library.
        echo Please download it manually from: https://repo1.maven.org/maven2/org/jfree/jfreechart/1.5.3/jfreechart-1.5.3.jar
        pause
        exit /b 1
    )
)

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Create class directory if it doesn't exist
if not exist "classes" mkdir classes

echo Java version:
java -version
echo.

echo Compiling Java files...
javac -d classes -cp "%MYSQL_JAR%;%JFREECHART_JAR%" BehaviorLoggerUI.java BehaviorLoggerUIEnhanced.java BehaviorLoggerUIMain.java

if %ERRORLEVEL% NEQ 0 (
    echo Error: Compilation failed
    pause
    exit /b 1
)

echo.
echo Running application...
java -cp "classes;%MYSQL_JAR%;%JFREECHART_JAR%" BehaviorLoggerUIMain

pause