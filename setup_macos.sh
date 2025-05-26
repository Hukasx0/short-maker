#!/bin/bash

echo "========================================"
echo "Short Maker - macOS Setup Script"
echo "========================================"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    print_status "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" < /dev/null
    
    # Add Homebrew to PATH for Apple Silicon Macs
    if [[ $(uname -m) == 'arm64' ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/usr/local/bin/brew shellenv)"
    fi
else
    print_status "Homebrew is already installed"
fi

# Update Homebrew
print_status "Updating Homebrew..."
brew update

# Install FFmpeg and ImageMagick
print_status "Installing FFmpeg and ImageMagick..."
brew install ffmpeg imagemagick

# Install Python if not present
if ! command -v python3 &> /dev/null; then
    print_status "Installing Python..."
    brew install python
else
    print_status "Python is already installed"
fi

# Upgrade pip
print_status "Upgrading pip..."
python3 -m pip install --upgrade pip

# Install Python packages
print_status "Installing Python packages..."
python3 -m pip install -r requirements.txt --upgrade --user

# Test installation
print_status "Testing installation..."
python3 -c "
try:
    from moviepy.editor import VideoFileClip
    from gtts import gTTS
    import numpy as np
    print('✓ All Python packages imported successfully!')
except ImportError as e:
    print(f'✗ Import error: {e}')
    exit(1)
" 2>/dev/null

if [ $? -eq 0 ]; then
    echo
    echo "========================================"
    echo -e "${GREEN}Setup completed successfully!${NC}"
    echo "========================================"
    echo "You can now use Short Maker with:"
    echo "python3 short-maker.py video1.mp4 video2.mp4 -o output.mp4"
    echo
    echo "Note: You may need to restart your terminal or run:"
    echo "source ~/.zprofile"
    echo "to ensure all PATH changes take effect."
else
    print_error "Installation test failed. Please check the error messages above."
    exit 1
fi

echo 
