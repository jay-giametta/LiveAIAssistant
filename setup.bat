@echo off
echo Starting setup for Live AI Assistant...
echo.

:: Check if Python is installed
python --version > nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7 or later from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check if config file exists
if not exist "config\config.json" (
    echo Error: config.json not found in config directory
    echo Please create config\config.json with your AWS credentials
    echo Example format:
    echo {
    echo     "aws_access_key_id": "your_access_key",
    echo     "aws_secret_access_key": "your_secret_key",
    echo     "region": "your_region"
    echo }
    pause
    exit /b 1
)

:: Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
)

:: Activate virtual environment and install requirements
echo Activating virtual environment and installing requirements...
call venv\Scripts\activate
if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

:: Upgrade pip
python -m pip install --upgrade pip
if errorlevel 1 (
    echo Error: Failed to upgrade pip
    pause
    exit /b 1
)

:: Install requirements
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install requirements
    pause
    exit /b 1
)

:: Create output directory
if not exist "output\transcripts" (
    echo Creating output directory...
    mkdir "output\transcripts"
)

echo.
echo Setup completed successfully!
echo.
echo To start the application:
echo 1. Double-click start_transcription.bat
echo   or
echo 2. Run these commands:
echo    .\venv\Scripts\activate
echo    python -m src.main
echo.
pause