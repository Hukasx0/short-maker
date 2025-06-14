@echo off
echo ========================================
echo Short Maker - GUI Launcher (Windows)
echo ========================================
echo.

REM Change to the script's directory (handles double-click from Windows Explorer)
cd /d "%~dp0"
echo Current directory: %CD%
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
    echo Virtual environment activated!
    echo.
)

REM Check if required Python packages are installed
echo Checking dependencies...

REM Create temporary Python script for dependency check
echo import sys > temp_check.py
echo missing_packages = [] >> temp_check.py
echo try: >> temp_check.py
echo     import moviepy >> temp_check.py
echo except ImportError: >> temp_check.py
echo     missing_packages.append('moviepy') >> temp_check.py
echo try: >> temp_check.py
echo     import gtts >> temp_check.py
echo except ImportError: >> temp_check.py
echo     missing_packages.append('gtts') >> temp_check.py
echo try: >> temp_check.py
echo     import numpy >> temp_check.py
echo except ImportError: >> temp_check.py
echo     missing_packages.append('numpy') >> temp_check.py
echo try: >> temp_check.py
echo     import tkinter >> temp_check.py
echo except ImportError: >> temp_check.py
echo     missing_packages.append('tkinter') >> temp_check.py
echo if missing_packages: >> temp_check.py
echo     print('Missing packages:', ', '.join(missing_packages)) >> temp_check.py
echo     sys.exit(1) >> temp_check.py
echo else: >> temp_check.py
echo     print('All packages available') >> temp_check.py
echo     sys.exit(0) >> temp_check.py

python temp_check.py >nul 2>&1
set DEPS_CHECK_RESULT=%errorLevel%
del temp_check.py >nul 2>&1

if %DEPS_CHECK_RESULT% neq 0 (
    echo.
    echo Some dependencies are missing. Running setup...
    echo.
    
    REM Check if setup script exists
    if not exist "setup_windows.bat" (
        echo ERROR: setup_windows.bat not found!
        echo Please download the complete Short Maker package.
        pause
        exit /b 1
    )
    
    echo Running setup_windows.bat...
    echo NOTE: Setup requires Administrator privileges.
    echo.
    
    REM Check if current session has admin rights
    net session >nul 2>&1
    if %errorLevel% neq 0 (
        echo This GUI launcher is not running as Administrator.
        echo Please close this window and:
        echo 1. Right-click on run_gui_windows.bat
        echo 2. Select "Run as administrator"
        echo 3. Or manually run setup_windows.bat as administrator first
        pause
        exit /b 1
    )
    
    echo Current session has Administrator privileges - proceeding with setup...
    call setup_windows.bat
    
    if %errorLevel% neq 0 (
        echo.
        echo Setup failed. Please check the error messages above.
        pause
        exit /b 1
    )
    
    echo.
    echo Setup completed! Now launching GUI...
    echo.
)

REM Check if short-maker.py exists
if not exist "short-maker.py" (
    echo ERROR: short-maker.py not found!
    echo Please make sure you're running this script from the Short Maker directory.
    pause
    exit /b 1
)

REM Launch GUI
echo Launching Short Maker GUI...
python short-maker.py --gui

if %errorLevel% neq 0 (
    echo.
    echo An error occurred while running Short Maker.
    echo Please check the error messages above.
    pause
)

echo.
echo Short Maker GUI closed.
pause 