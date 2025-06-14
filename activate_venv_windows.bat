@echo off
echo ========================================
echo Short Maker - Virtual Environment (Windows)
echo ========================================
echo.

REM Change to the script's directory (handles double-click from Windows Explorer)
cd /d "%~dp0"
echo Current directory: %CD%
echo.

if not exist "venv\" (
    echo [ERROR] Virtual environment not found!
    echo Please run setup_windows.bat or setup_windows.ps1 first to create the virtual environment.
    pause
    exit /b 1
)

echo [INFO] Activating virtual environment...

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Show Python version info
echo [INFO] Python version in virtual environment:
python --version
echo.
echo [INFO] Virtual environment activated!
echo To deactivate later, type: deactivate
echo.
echo You can now run Short Maker with:
echo python short-maker.py --gui
echo.

REM Start a new command prompt with the virtual environment activated
cmd /k 