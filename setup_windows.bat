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
echo Adding tools to system PATH...
REM Add Chocolatey bin directory to PATH
set "PATH=%PATH%;%ALLUSERSPROFILE%\chocolatey\bin"

REM Try to add ImageMagick to PATH if it's not already there
for /f "delims=" %%i in ('where magick 2^>nul') do set MAGICK_FOUND=%%i
if "%MAGICK_FOUND%"=="" (
    echo Adding ImageMagick to PATH...
    setx PATH "%PATH%;C:\Program Files\ImageMagick-7.1.1-Q16-HDRI" /M 2>nul
    if errorlevel 1 (
        echo Warning: Could not add ImageMagick to system PATH automatically.
        echo Please add ImageMagick directory to your PATH manually.
    )
) else (
    echo ImageMagick already in PATH: %MAGICK_FOUND%
)

echo.
echo Installing Python packages...
pip install -r requirements.txt --upgrade

echo.
echo Configuring MoviePy for ImageMagick...
python -c "
import os
import sys
import shutil
try:
    # First, try to configure using MoviePy's change_settings
    from moviepy.config import change_settings
    
    # Try to find magick.exe in PATH
    magick_path = shutil.which('magick')
    if magick_path:
        change_settings({'IMAGEMAGICK_BINARY': magick_path})
        print(f'MoviePy configured with ImageMagick: {magick_path}')
    else:
        print('Warning: magick.exe not found in PATH')
        
    # Also try the old config file method as backup
    import moviepy
    config_path = os.path.join(os.path.dirname(moviepy.__file__), 'config.py')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace convert with magick.exe
        content = content.replace('IMAGEMAGICK_BINARY = \"convert\"', 'IMAGEMAGICK_BINARY = \"magick.exe\"')
        content = content.replace('IMAGEMAGICK_BINARY = \'convert\'', 'IMAGEMAGICK_BINARY = \'magick.exe\'')
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print('MoviePy config file also updated as backup!')
    else:
        print('MoviePy config file not found.')
        
except Exception as e:
    print(f'Warning: Could not update MoviePy config: {e}')
    print('Short Maker will try to auto-configure ImageMagick at runtime.')
"

echo.
echo Testing installation...
echo Checking ImageMagick...
magick -version >nul 2>&1
if %errorLevel% == 0 (
    echo ✓ ImageMagick is accessible via 'magick' command
    magick -version | findstr /C:"Version:"
) else (
    echo ✗ ImageMagick 'magick' command not found
    echo Please ensure ImageMagick is installed and in your PATH
)

echo.
echo Testing Python packages...
python -c "
import sys
import shutil
try:
    from moviepy.editor import VideoFileClip, TextClip
    from gtts import gTTS
    import numpy as np
    print('✓ All Python packages imported successfully!')
    
    # Test ImageMagick integration
    magick_path = shutil.which('magick')
    if magick_path:
        print(f'✓ ImageMagick found at: {magick_path}')
        try:
            # Try to create a simple text clip to test ImageMagick integration
            test_clip = TextClip('Test', fontsize=50, color='white', duration=1)
            print('✓ Text clip creation works - ImageMagick integration successful!')
        except Exception as e:
            print(f'⚠ Text clip creation failed: {e}')
            print('  This may indicate ImageMagick configuration issues.')
    else:
        print('⚠ ImageMagick (magick.exe) not found in PATH')
        print('  Text features may not work properly.')
    
except ImportError as e:
    print(f'✗ Import error: {e}')
    sys.exit(1)
except Exception as e:
    print(f'⚠ Test warning: {e}')
"

echo.
echo ========================================
echo Setup completed successfully!
echo ========================================
echo You can now use Short Maker with:
echo python short-maker.py --gui
echo or
echo python short-maker.py video1.mp4 video2.mp4 -o output.mp4
echo.
echo Note: If you encounter issues, try the PowerShell version:
echo setup_windows.ps1 (run in Administrator PowerShell)
echo.
pause 
