@echo off
echo ========================================
echo Short Maker - Windows Setup Script
echo ========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running as Administrator - Good!
) else (
    echo ERROR: This script must be run as Administrator!
    echo Right-click on this file and select "Run as administrator"
    pause
    exit /b 1
)

echo Installing Chocolatey package manager...
powershell -NoProfile -InputFormat None -ExecutionPolicy Bypass -Command "iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))" && SET "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"

REM Refresh environment variables
call refreshenv

echo.
echo Installing FFmpeg...
choco install ffmpeg -y --force

echo.
echo Installing ImageMagick...
choco install imagemagick -y --force

echo.
echo Installing Python packages...
pip install -r requirements.txt --upgrade

echo.
echo Configuring MoviePy for ImageMagick...
python -c "
import os
import sys
try:
    import moviepy
    config_path = os.path.join(os.path.dirname(moviepy.__file__), 'config.py')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Replace convert with magick.exe
        content = content.replace('IMAGEMAGICK_BINARY = \"convert\"', 'IMAGEMAGICK_BINARY = \"magick.exe\"')
        content = content.replace('IMAGEMAGICK_BINARY = \'convert\'', 'IMAGEMAGICK_BINARY = \'magick.exe\'')
        
        with open(config_path, 'w') as f:
            f.write(content)
        print('MoviePy configuration updated successfully!')
    else:
        print('MoviePy config file not found, but installation should work.')
except Exception as e:
    print(f'Warning: Could not update MoviePy config: {e}')
"

echo.
echo Testing installation...
python -c "
try:
    from moviepy.editor import VideoFileClip
    from gtts import gTTS
    import numpy as np
    print('✓ All Python packages imported successfully!')
except ImportError as e:
    print(f'✗ Import error: {e}')
    exit(1)
"

echo.
echo ========================================
echo Setup completed successfully!
echo ========================================
echo You can now use Short Maker with:
echo python short-maker.py video1.mp4 video2.mp4 -o output.mp4
echo.
pause 
