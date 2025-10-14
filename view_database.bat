@echo off
echo Running Behavior Logger MySQL Viewer
echo ===================================

REM Set paths
set SCRIPT_DIR=%~dp0
set PYTHON_SCRIPT=%SCRIPT_DIR%python\mysql_viewer.py

REM Run Python script
python "%PYTHON_SCRIPT%"

pause