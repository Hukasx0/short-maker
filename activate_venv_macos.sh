#!/bin/bash

echo "========================================"
echo "Short Maker - Virtual Environment (macOS)"
echo "========================================"
echo

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

if [ ! -d "venv" ]; then
    echo -e "${RED}[ERROR]${NC} Virtual environment not found!"
    echo "Please run setup_macos.sh first to create the virtual environment."
    exit 1
fi

echo -e "${GREEN}[INFO]${NC} Activating virtual environment..."

# Activate virtual environment
source venv/bin/activate

# Show Python version info
echo -e "${YELLOW}[INFO]${NC} Python version in virtual environment:"
python --version
echo ""
echo -e "${GREEN}[INFO]${NC} Virtual environment activated!"
echo "To deactivate later, type: deactivate"
echo ""
echo "You can now run Short Maker with:"
echo "python short-maker.py --gui"
echo ""

# Start a new shell with the virtual environment activated
exec zsh 