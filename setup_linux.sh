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

# Function to check Python version
check_python_version() {
    local python_cmd=$1
    if command -v $python_cmd &> /dev/null; then
        local version=$($python_cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
        local major=$(echo $version | cut -d. -f1)
        local minor=$(echo $version | cut -d. -f2)
        
        # Check if version is 3.10.x
        if [[ $major -eq 3 && $minor -eq 10 ]]; then
            echo "suitable"
            return 0
        else
            echo "unsuitable"
            return 1
        fi
    else
        echo "missing"
        return 1
    fi
}

# Check current Python version
print_status "Checking Python version..."
PYTHON_CMD="python3"
PYTHON_STATUS=$(check_python_version $PYTHON_CMD)

if [[ $PYTHON_STATUS == "suitable" ]]; then
    print_status "Python 3.10.x detected - perfect!"
elif command -v python3.10 &> /dev/null; then
    print_status "Found python3.10 command"
    PYTHON_CMD="python3.10"
    PYTHON_STATUS="suitable"
else
    current_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "unknown")
    print_warning "Current Python version ($current_version) may cause compatibility issues."
    print_status "Installing Python 3.10 for better compatibility..."
    
    # Install pyenv if not present
    if [ ! -d "$HOME/.pyenv" ]; then
        print_status "Installing pyenv..."
        curl https://pyenv.run | bash
    fi
    
    # Setup pyenv environment
    export PATH="$HOME/.pyenv/bin:$PATH"
    eval "$(pyenv init -)"
    
    # Install Python 3.10.11 if not already installed
    if [ ! -d "$HOME/.pyenv/versions/3.10.11" ]; then
        print_status "Installing Python 3.10.11 via pyenv..."
        pyenv install 3.10.11
    fi
    
    # Set PYTHON_CMD to use pyenv Python 3.10.11
    PYTHON_CMD="$HOME/.pyenv/versions/3.10.11/bin/python"
    print_status "Python 3.10.11 installed successfully via pyenv!"
fi

print_status "Using Python command: $PYTHON_CMD"

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
    sudo apt-get install -y ffmpeg imagemagick python3-pip python3-venv python3-tk
elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"Fedora"* ]]; then
    if command -v dnf &> /dev/null; then
        sudo dnf install -y ffmpeg imagemagick python3-pip python3-venv python3-tkinter
    else
        # Enable EPEL repository for CentOS/RHEL
        sudo yum install -y epel-release
        sudo yum install -y ffmpeg imagemagick python3-pip python3-venv python3-tkinter
    fi
elif [[ "$OS" == *"Arch"* ]]; then
    sudo pacman -S --noconfirm ffmpeg imagemagick python python-pip tk
    
    # Fix libxml2 compatibility for ImageMagick on Arch Linux
    print_status "Fixing ImageMagick dependencies for Arch Linux..."
    if [ ! -f "/usr/lib/libxml2.so.16" ]; then
        sudo ln -sf /usr/lib/libxml2.so.2 /usr/lib/libxml2.so.16
        print_status "Created libxml2 compatibility link"
    fi
    
    # Set ImageMagick to use magick instead of convert (ImageMagick 7)
    export IMAGEMAGICK_BINARY=/usr/bin/magick
else
    print_warning "Unknown distribution. Please install ffmpeg, imagemagick, python3-pip, and tkinter manually."
fi

# Setup Python virtual environment
print_status "Setting up Python virtual environment..."

# Remove old virtual environment if it exists
if [ -d "venv" ]; then
    print_status "Removing old virtual environment..."
    rm -rf venv
fi

# Create virtual environment with the appropriate Python version
$PYTHON_CMD -m venv venv
if [ $? -ne 0 ]; then
    print_error "Failed to create virtual environment"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip in virtual environment
pip install --upgrade pip

# Install Python packages in virtual environment
print_status "Installing Python packages in virtual environment..."
pip install -r requirements.txt

# Test installation
print_status "Testing installation..."

python -c "
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
    echo "Using Python: $($PYTHON_CMD --version)"
    echo ""
    echo "The GUI launcher will automatically activate"
    echo "the virtual environment when needed."
    echo ""
    echo "You can also manually activate it with:"
    echo "source venv/bin/activate"
    echo ""
    echo "Then use Short Maker with:"
    echo "python short-maker.py video1.mp4 video2.mp4 -o output.mp4"
else
    print_error "Installation test failed. Please check the error messages above."
    exit 1
fi

echo
