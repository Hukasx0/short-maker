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

# Install FFmpeg, ImageMagick and Python-Tk for better GUI support
print_status "Installing FFmpeg, ImageMagick and Python-Tk..."
brew install ffmpeg imagemagick python-tk

# Additional setup for macOS ARM64 GUI support
if [[ $(uname -m) == 'arm64' ]]; then
    print_status "Configuring additional GUI support for Apple Silicon..."
    
    # Install python-tk for better GUI compatibility
    if ! brew list python-tk &> /dev/null; then
        print_status "Installing python-tk for better macOS GUI support..."
        brew install python-tk
    fi
    
    # Install tcl-tk for better tkinter support
    if ! brew list tcl-tk &> /dev/null; then
        print_status "Installing tcl-tk for enhanced tkinter support..."
        brew install tcl-tk
    fi
    
    print_status "Setting environment variables for GUI compatibility..."
    
    # Set environment variable to suppress Tk deprecation warnings
    export TK_SILENCE_DEPRECATION=1
    echo 'export TK_SILENCE_DEPRECATION=1' >> ~/.zprofile
    
    print_warning "For optimal GUI performance on Apple Silicon, consider rebuilding Python 3.10.11:"
    print_warning "export PYTHON_CONFIGURE_OPTS=\"--with-tcltk-includes='-I/opt/homebrew/include' --with-tcltk-libs='-L/opt/homebrew/lib -ltcl9.0 -ltk9.0'\""
    print_warning "pyenv install --force 3.10.11"
    print_warning ""
    print_warning "This step is optional but recommended for best GUI compatibility."
fi

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

# Check current Python version and install Python 3.10.11 if needed
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
    if [[ "$current_version" != "unknown" ]]; then
        print_warning "Current Python version ($current_version) may cause compatibility issues."
    fi
    print_status "Installing Python 3.10.11 for better compatibility..."
    
    # Install pyenv if not present
    if [ ! -d "$HOME/.pyenv" ]; then
        print_status "Installing pyenv for Python version management..."
        brew install pyenv
        
        # Add pyenv to shell profile
        if [[ $(uname -m) == 'arm64' ]]; then
            echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zprofile
            echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zprofile
            echo 'eval "$(pyenv init -)"' >> ~/.zprofile
        else
            echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zprofile
            echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zprofile
            echo 'eval "$(pyenv init -)"' >> ~/.zprofile
        fi
        
        # Load pyenv for current session
        export PYENV_ROOT="$HOME/.pyenv"
        export PATH="$PYENV_ROOT/bin:$PATH"
        eval "$(pyenv init -)"
    else
        print_status "pyenv already installed"
        # Load pyenv for current session
        export PYENV_ROOT="$HOME/.pyenv"
        export PATH="$PYENV_ROOT/bin:$PATH"
        eval "$(pyenv init -)"
    fi
    
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

# Upgrade pip
print_status "Upgrading pip..."
$PYTHON_CMD -m pip install --upgrade pip

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
    print_status "Try installing required packages:"
    echo "  brew install python"
    echo "  or"
    echo "  xcode-select --install"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip in virtual environment
print_status "Upgrading pip in virtual environment..."
pip install --upgrade pip

# Install Python packages in virtual environment
print_status "Installing Python packages in virtual environment..."
pip install -r requirements.txt --upgrade

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
    echo "Short Maker is ready to use!"
    echo "Using Python: $($PYTHON_CMD --version)"
    echo "Tested and optimized for Python 3.10.11"
    echo ""
    echo "The GUI launcher will automatically activate"
    echo "the virtual environment when needed."
    echo ""
    echo "You can also manually activate it with:"
    echo "source venv/bin/activate"
    echo ""
    echo "Then use Short Maker with:"
    echo "python short-maker.py video1.mp4 video2.mp4 -o output.mp4"
    echo
    if [[ $(uname -m) == 'arm64' ]]; then
        echo "========================================"
        echo -e "${YELLOW}macOS ARM64 GUI Notes:${NC}"
        echo "========================================"
        echo "• GUI now supports both light and dark modes"
        echo "• TK_SILENCE_DEPRECATION=1 has been set to reduce warnings"
        echo "• If GUI controls are still not visible, try:"
        echo "  1. Restart the terminal application"
        echo "  2. Run: source ~/.zprofile"
        echo "  3. For best results, rebuild Python with better Tk support:"
        echo "     export PYTHON_CONFIGURE_OPTS=\"--with-tcltk-includes='-I/opt/homebrew/include' --with-tcltk-libs='-L/opt/homebrew/lib -ltcl9.0 -ltk9.0'\""
        echo "     pyenv install --force 3.10.11"
        echo ""
    fi
    echo "Note: You may need to restart your terminal or run:"
    echo "source ~/.zprofile"
    echo "to ensure all PATH changes take effect."
else
    print_error "Installation test failed. Please check the error messages above."
    exit 1
fi

echo 
