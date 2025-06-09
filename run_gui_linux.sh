#!/bin/bash

echo "========================================"
echo "Short Maker - GUI Launcher (Linux)"
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

# Function to find the best Python version
find_python_cmd() {
    # Try pyenv Python 3.10.11 first (best option)
    if [ -f "$HOME/.pyenv/versions/3.10.11/bin/python" ]; then
        echo "$HOME/.pyenv/versions/3.10.11/bin/python"
        return 0
    fi
    
    # Try python3.10 command
    if command -v python3.10 &> /dev/null; then
        echo "python3.10"
        return 0
    fi
    
    # Check if default python3 is version 3.10.x
    if command -v python3 &> /dev/null; then
        local version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
        if [[ "$version" == "3.10" ]]; then
            echo "python3"
            return 0
        fi
    fi
    
    # Fall back to python3
    if command -v python3 &> /dev/null; then
        echo "python3"
        return 0
    fi
    
    echo ""
    return 1
}

# Detect if we're on Arch Linux
ARCH_LINUX=false
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ "$NAME" == *"Arch"* ]]; then
        ARCH_LINUX=true
        # Set ImageMagick binary for Arch Linux (ImageMagick 7)
        export IMAGEMAGICK_BINARY=/usr/bin/magick
    fi
fi

# Find the best Python command
PYTHON_CMD=$(find_python_cmd)
if [ -z "$PYTHON_CMD" ]; then
    print_error "Python 3 is not installed!"
    print_status "Please install Python 3 using your package manager:"
    echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    echo "  CentOS/RHEL/Fedora: sudo dnf install python3 python3-pip"
    echo "  Arch Linux: sudo pacman -S python python-pip"
    exit 1
fi

print_status "Using Python: $($PYTHON_CMD --version)"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    print_status "Activating virtual environment..."
    source venv/bin/activate
    # Update PYTHON_CMD to use the virtual environment's python
    PYTHON_CMD="python"
fi

# Check if required Python packages are installed
print_status "Checking dependencies..."
$PYTHON_CMD -c "
import sys
missing_packages = []
try:
    import moviepy
except ImportError:
    missing_packages.append('moviepy')
try:
    import gtts
except ImportError:
    missing_packages.append('gtts')
try:
    import numpy
except ImportError:
    missing_packages.append('numpy')
try:
    import tkinter
except ImportError:
    missing_packages.append('tkinter')

if missing_packages:
    print('Missing packages:', ', '.join(missing_packages))
    sys.exit(1)
else:
    print('All packages available')
    sys.exit(0)
" 2>/dev/null

if [ $? -ne 0 ]; then
    echo
    print_warning "Some dependencies are missing. Running setup..."
    echo
    
    # Check if setup script exists
    if [ ! -f "setup_linux.sh" ]; then
        print_error "setup_linux.sh not found!"
        print_error "Please download the complete Short Maker package."
        exit 1
    fi
    
    # Make setup script executable
    chmod +x setup_linux.sh
    
    print_status "Running setup_linux.sh..."
    ./setup_linux.sh
    
    if [ $? -ne 0 ]; then
        echo
        print_error "Setup failed. Please check the error messages above."
        exit 1
    fi
    
    # Activate virtual environment after setup
    if [ -d "venv" ]; then
        print_status "Activating virtual environment after setup..."
        source venv/bin/activate
        PYTHON_CMD="python"
    fi
    
    echo
    print_status "Setup completed! Now launching GUI..."
    echo
fi

# Check if short-maker.py exists
if [ ! -f "short-maker.py" ]; then
    print_error "short-maker.py not found!"
    print_error "Please make sure you're running this script from the Short Maker directory."
    exit 1
fi

# Launch GUI
print_status "Launching Short Maker GUI..."
$PYTHON_CMD short-maker.py --gui

if [ $? -ne 0 ]; then
    echo
    print_error "An error occurred while running Short Maker."
    print_error "Please check the error messages above."
    exit 1
fi

echo
print_status "Short Maker GUI closed." 