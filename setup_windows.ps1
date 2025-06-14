# Short Maker - Windows Setup Script (PowerShell)
# This script must be run as Administrator

param(
    [switch]$Force
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Short Maker - Windows Setup Script (PowerShell)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Change to the script's directory (handles double-click from Windows Explorer)
Set-Location -Path $PSScriptRoot
Write-Host "Current directory: $(Get-Location)" -ForegroundColor Gray
Write-Host ""

# Check if running as administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click on PowerShell and select 'Run as administrator', then run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host "Running as Administrator - Good!" -ForegroundColor Green

Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
try {
    $pythonVersion = & python --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Found: $pythonVersion" -ForegroundColor Green
        
        # Extract version numbers
        $versionMatch = $pythonVersion -match "Python (\d+)\.(\d+)\."
        if ($versionMatch) {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            
            if ($major -eq 3 -and $minor -eq 10) {
                Write-Host "✓ Python 3.10.x detected - perfect for Short Maker!" -ForegroundColor Green
            } else {
                Write-Host "⚠ Warning: Python $major.$minor detected. Recommended version is 3.10.x" -ForegroundColor Yellow
                Write-Host "  Short Maker was tested on Python 3.10.11" -ForegroundColor Yellow
                Write-Host "  Current version may work but could cause compatibility issues." -ForegroundColor Yellow
            }
        }
    } else {
        throw "Python command failed"
    }
} catch {
    Write-Host "✗ Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.10.x from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Recommended version: Python 3.10.11" -ForegroundColor Yellow
    Write-Host "Press any key to exit..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}
Write-Host ""

# Set execution policy temporarily
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force

# Install Chocolatey if not present
if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Chocolatey package manager..." -ForegroundColor Yellow
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
    
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    # Add Chocolatey to current session
    $env:Path += ";$env:ALLUSERSPROFILE\chocolatey\bin"
} else {
    Write-Host "Chocolatey already installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "Installing FFmpeg..." -ForegroundColor Yellow
choco install ffmpeg -y --force

Write-Host ""
Write-Host "Installing ImageMagick..." -ForegroundColor Yellow
choco install imagemagick -y --force

Write-Host ""
Write-Host "Refreshing environment variables..." -ForegroundColor Yellow
# Refresh PATH for current session
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Check if magick.exe is accessible
$magickPath = Get-Command magick -ErrorAction SilentlyContinue
if ($magickPath) {
    Write-Host "✓ ImageMagick found at: $($magickPath.Source)" -ForegroundColor Green
} else {
    Write-Host "⚠ ImageMagick not found in PATH, checking common locations..." -ForegroundColor Yellow
    
    # Try to find ImageMagick in common locations
    $commonPaths = @(
        "${env:ProgramFiles}\ImageMagick-*\magick.exe",
        "${env:ProgramFiles(x86)}\ImageMagick-*\magick.exe",
        "${env:ALLUSERSPROFILE}\chocolatey\bin\magick.exe"
    )
    
    $foundPath = $null
    foreach ($pathPattern in $commonPaths) {
        $matches = Get-ChildItem -Path $pathPattern -ErrorAction SilentlyContinue
        if ($matches) {
            $foundPath = $matches[0].FullName
            break
        }
    }
    
    if ($foundPath) {
        Write-Host "✓ Found ImageMagick at: $foundPath" -ForegroundColor Green
        # Add to PATH for current session
        $env:Path += ";$(Split-Path $foundPath -Parent)"
    } else {
        Write-Host "✗ ImageMagick not found. Please install manually." -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Setting up Python virtual environment..." -ForegroundColor Yellow

# Remove old virtual environment if it exists
if (Test-Path "venv") {
    Write-Host "Removing old virtual environment..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "venv"
}

# Create virtual environment
python -m venv venv
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
    Write-Host "Please ensure Python venv module is available." -ForegroundColor Yellow
    Write-Host "Press any key to exit..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Activate virtual environment
try {
    & .\venv\Scripts\Activate.ps1
} catch {
    Write-Host "⚠ Warning: Could not activate virtual environment using PowerShell script" -ForegroundColor Yellow
    Write-Host "  Trying alternative activation method..." -ForegroundColor Yellow
    & .\venv\Scripts\activate.bat
}

Write-Host ""
Write-Host "Installing Python packages in virtual environment..." -ForegroundColor Yellow
python -m pip install -r requirements.txt --upgrade

Write-Host ""
Write-Host "Configuring MoviePy for ImageMagick..." -ForegroundColor Yellow

# Configure MoviePy with ImageMagick
python -c @"
import os
import sys
import shutil
import platform

try:
    print('Configuring MoviePy for ImageMagick...')
    
    # Try to configure using MoviePy's change_settings
    from moviepy.config import change_settings
    
    # Try to find magick.exe in PATH
    magick_path = shutil.which('magick')
    if magick_path:
        change_settings({'IMAGEMAGICK_BINARY': magick_path})
        print(f'✓ MoviePy configured with ImageMagick: {magick_path}')
    else:
        print('⚠ magick.exe not found in PATH, trying common paths...')
        
        # Try common installation paths
        import glob
        common_paths = [
            r'C:\Program Files\ImageMagick-*\magick.exe',
            r'C:\Program Files (x86)\ImageMagick-*\magick.exe',
            r'C:\ProgramData\chocolatey\bin\magick.exe',
            r'C:\tools\ImageMagick\magick.exe'
        ]
        
        for path_pattern in common_paths:
            matches = glob.glob(path_pattern)
            if matches:
                magick_path = matches[0]
                change_settings({'IMAGEMAGICK_BINARY': magick_path})
                print(f'✓ MoviePy configured with ImageMagick: {magick_path}')
                break
        else:
            print('⚠ Could not find ImageMagick automatically')
    
    # Also try the old config file method as backup
    try:
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
            print('✓ MoviePy config file also updated!')
    except Exception as e:
        print(f'Note: Config file update failed: {e}')
        
except Exception as e:
    print(f'Warning: Could not configure MoviePy: {e}')
    print('Short Maker will try to auto-configure ImageMagick at runtime.')
"@

Write-Host ""
Write-Host "Testing installation..." -ForegroundColor Yellow

# Test ImageMagick
Write-Host "Checking ImageMagick..." -ForegroundColor Cyan
try {
    $magickVersion = & magick -version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ ImageMagick is accessible via 'magick' command" -ForegroundColor Green
        $version = ($magickVersion | Select-String "Version:").Line
        Write-Host "  $version" -ForegroundColor Gray
    } else {
        throw "Command failed"
    }
} catch {
    Write-Host "✗ ImageMagick 'magick' command not found" -ForegroundColor Red
    Write-Host "  Please ensure ImageMagick is installed and in your PATH" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Testing Python packages..." -ForegroundColor Cyan

# Test Python packages
python -c @"
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
"@

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup completed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Short Maker is ready to use!" -ForegroundColor White
Write-Host "Tested and optimized for Python 3.10.11" -ForegroundColor Gray
Write-Host ""
Write-Host "The GUI launcher will automatically activate" -ForegroundColor White
Write-Host "the virtual environment when needed." -ForegroundColor White
Write-Host ""
Write-Host "You can also manually activate it with:" -ForegroundColor White
Write-Host "activate_venv_windows.bat" -ForegroundColor Yellow
Write-Host ""
Write-Host "Then use Short Maker with:" -ForegroundColor White
Write-Host "python short-maker.py --gui" -ForegroundColor Yellow
Write-Host "or" -ForegroundColor White
Write-Host "python short-maker.py video1.mp4 video2.mp4 -o output.mp4" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 