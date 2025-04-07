@echo off
echo Starting Python dependency installation...

REM Check if Python is installed
python --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Python is not installed. Please install Python 3.6 or higher.
    echo https://www.python.org/downloads/
    exit /b 1
)

REM Check if pip is installed
pip --version > nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo pip is not installed. Please install pip with Python.
    exit /b 1
)

echo Installing required Python packages...
pip install notion-client notion2md

if %ERRORLEVEL% neq 0 (
    echo Error occurred during package installation.
    exit /b 1
) else (
    echo Notion MCP Python dependency installation completed.
    exit /b 0
) 