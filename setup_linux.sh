#!/bin/bash

echo "========================================"
echo "Short Maker - Linux Setup Script"
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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_warning "Running as root. This is not recommended but will continue..."
fi

# Detect Linux distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VER=$VERSION_ID
elif type lsb_release >/dev/null 2>&1; then
    OS=$(lsb_release -si)
    VER=$(lsb_release -sr)
else
    OS=$(uname -s)
    VER=$(uname -r)
fi

print_status "Detected OS: $OS"

# Update package manager
print_status "Updating package manager..."
if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    sudo apt-get update -y
elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"Fedora"* ]]; then
    if command -v dnf &> /dev/null; then
        sudo dnf update -y
    else
        sudo yum update -y
    fi
elif [[ "$OS" == *"Arch"* ]]; then
    sudo pacman -Sy --noconfirm
fi

# Install FFmpeg and ImageMagick
print_status "Installing FFmpeg and ImageMagick..."
if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
    sudo apt-get install -y ffmpeg imagemagick python3-pip
elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"Fedora"* ]]; then
    if command -v dnf &> /dev/null; then
        sudo dnf install -y ffmpeg imagemagick python3-pip
    else
        # Enable EPEL repository for CentOS/RHEL
        sudo yum install -y epel-release
        sudo yum install -y ffmpeg imagemagick python3-pip
    fi
elif [[ "$OS" == *"Arch"* ]]; then
    sudo pacman -S --noconfirm ffmpeg imagemagick python-pip
else
    print_warning "Unknown distribution. Please install ffmpeg, imagemagick, and python3-pip manually."
fi

# Install Python packages
print_status "Installing Python packages..."
if command -v pip3 &> /dev/null; then
    pip3 install -r requirements.txt --upgrade --user
elif command -v pip &> /dev/null; then
    pip install -r requirements.txt --upgrade --user
else
    print_error "pip not found. Please install pip manually."
    exit 1
fi

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
else
    print_error "Installation test failed. Please check the error messages above."
    exit 1
fi

echo 
