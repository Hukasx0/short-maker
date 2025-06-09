#!/bin/bash

echo "========================================"
echo "Short Maker - GUI Launcher (macOS)"
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

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed!"
    print_status "Please install Python 3:"
    echo "  Option 1: Download from https://www.python.org/downloads/"
    echo "  Option 2: Install via Homebrew: brew install python"
    echo "  Option 3: Install via Xcode Command Line Tools: xcode-select --install"
    exit 1
fi

print_status "Using Python: $(python3 --version)"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    print_status "Activating virtual environment..."
    source venv/bin/activate
    # Update to use the virtual environment's python
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

# Check if required Python packages are installed
print_status "Checking dependencies..."
$PYTHON_CMD -c "
import sys
import platform
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
    # Check for macOS ARM64 specific issue
    if platform.system() == 'Darwin' and platform.machine() == 'arm64':
        import os
        os.environ['TK_SILENCE_DEPRECATION'] = '1'
        print('Note: Using system Tk on macOS ARM64')
        print('For better GUI performance, consider: brew install python-tk')
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
    if [ ! -f "setup_macos.sh" ]; then
        print_error "setup_macos.sh not found!"
        print_error "Please download the complete Short Maker package."
        exit 1
    fi
    
    # Make setup script executable
    chmod +x setup_macos.sh
    
    print_status "Running setup_macos.sh..."
    ./setup_macos.sh
    
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
    
    # Source profile to ensure PATH is updated
    if [ -f ~/.zprofile ]; then
        source ~/.zprofile
    fi
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
    print_status "You may need to restart your terminal or run: source ~/.zprofile"
    exit 1
fi

echo
print_status "Short Maker GUI closed." 