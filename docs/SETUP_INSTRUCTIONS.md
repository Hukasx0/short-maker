# Setup Instructions for Short Maker

This document provides detailed instructions for setting up Short Maker on different operating systems using the automated setup scripts.

## 🪟 Windows Setup

### Requirements
- Windows 10 or later
- Administrator privileges

### Steps
1. **Download the repository:**
   - Download as ZIP from GitHub and extract, OR
   - Clone using Git: `git clone https://github.com/Hukasx0/short-maker.git`

2. **Run the setup script (choose one option):**
   - Navigate to the `short-maker` folder
   - **Option A (Recommended):** 
     - Right-click on `setup_windows.ps1`
     - Select **"Run with PowerShell as administrator"**
   - **Option B (Alternative):**
     - Right-click on `setup_windows.bat`
     - Select **"Run as administrator"**
   - Wait for the installation to complete (this may take 5-15 minutes)

### What the scripts do:

#### PowerShell Script (`setup_windows.ps1`) - **Recommended**:
- ✅ Checks Python version (recommends Python 3.10.11)
- ✅ Installs Chocolatey package manager (if not present)
- ✅ Installs FFmpeg for video processing
- ✅ Installs ImageMagick for image processing
- ✅ Automatically detects and configures ImageMagick paths
- ✅ Installs Python packages from requirements.txt
- ✅ Configures MoviePy to work with ImageMagick (`magick.exe`)
- ✅ Tests ImageMagick integration with text clip creation
- ✅ Provides colored output and better error handling
- ✅ Automatically handles environment variables

#### Batch Script (`setup_windows.bat`) - **Alternative**:
- ✅ Checks Python version (recommends Python 3.10.11)
- ✅ Installs Chocolatey package manager (if not present)
- ✅ Installs FFmpeg for video processing
- ✅ Installs ImageMagick for image processing
- ✅ Installs Python packages from requirements.txt
- ✅ Configures MoviePy to work with ImageMagick
- ✅ Tests the installation

**Recommendation:** Use the PowerShell script for better reliability and error reporting.

### Troubleshooting:

#### Common Issues:
- **"This script must be run as Administrator"**: 
  - For `.ps1`: Right-click PowerShell and "Run as administrator", then navigate to the script
  - For `.bat`: Right-click the .bat file and select "Run as administrator"
- **"Execution Policy" error (PowerShell)**: The script automatically sets the execution policy, but if it fails, run:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
  ```
- **Chocolatey installation fails**: Check your internet connection and Windows version
- **FFmpeg/ImageMagick not found**: The scripts will add them to PATH automatically, but you may need to restart your terminal
- **ImageMagick `convert` vs `magick` issue**: Both scripts automatically configure MoviePy to use `magick.exe` instead of `convert`

#### Script-Specific Issues:

**PowerShell Script Issues:**
- **Script won't run**: Ensure you're running PowerShell as Administrator
- **ImageMagick configuration fails**: The script will show detailed error messages and fallback options

**Batch Script Issues:**
- **PATH not updated**: Restart your command prompt/terminal after installation
- **MoviePy config fails**: The main script will auto-configure ImageMagick at runtime as fallback

#### Advanced Troubleshooting:
If both automated scripts fail, you can manually verify ImageMagick:
1. Open Command Prompt and run: `magick -version`
2. If it shows "convert.exe", ImageMagick is not properly configured
3. If it shows ImageMagick version info, it's working correctly

---

## 🐧 Linux Setup

### Requirements
- Ubuntu/Debian, CentOS/RHEL/Fedora, or Arch Linux
- sudo privileges
- Internet connection

### Steps
1. **Download and run:**
   ```bash
   git clone https://github.com/Hukasx0/short-maker.git
   cd short-maker
   chmod +x setup_linux.sh
   ./setup_linux.sh
   ```

### What the script does:
- ✅ Detects your Linux distribution automatically
- ✅ Updates package manager
- ✅ Installs FFmpeg, ImageMagick, and Python3-pip
- ✅ Installs Python packages from requirements.txt
- ✅ Tests the installation

### Virtual Environment Management:
After running the setup script, you can use the virtual environment activation script:

```bash
# Activate the virtual environment for Short Maker
chmod +x activate_venv.sh
./activate_venv.sh
```

**What `activate_venv.sh` does:**
- ✅ Checks if the virtual environment exists
- ✅ Activates the virtual environment automatically
- ✅ Shows Python version information
- ✅ Provides usage instructions
- ✅ Starts a new shell with the environment activated

This is useful when you want to:
- Run Short Maker manually with `python short-maker.py`
- Install additional Python packages
- Debug or develop with the exact environment used by Short Maker

**Note:** The GUI launcher scripts (`run_gui_linux.sh`) automatically handle virtual environment activation, so you typically don't need to use `activate_venv.sh` for normal usage.

### Supported distributions:
- **Ubuntu/Debian**: Uses `apt-get`
- **CentOS/RHEL/Fedora**: Uses `dnf` or `yum`
- **Arch Linux**: Uses `pacman`

### Troubleshooting:
- **Permission denied**: Make sure you have sudo privileges
- **Package not found**: The script enables EPEL repository for CentOS/RHEL
- **Unknown distribution**: Install ffmpeg, imagemagick, and python3-pip manually

---

## 🍎 macOS Setup

### Requirements
- macOS 10.14 or later
- Internet connection
- Xcode Command Line Tools (will be installed automatically if needed)

### Steps
1. **Download and run:**
   ```bash
   git clone https://github.com/Hukasx0/short-maker.git
   cd short-maker
   chmod +x setup_macos.sh
   ./setup_macos.sh
   ```

### What the script does:
- ✅ Installs Homebrew package manager (if not present)
- ✅ Installs FFmpeg, ImageMagick, and Python-Tk via Homebrew
- ✅ Checks Python version and installs Python 3.10.11 if needed (via pyenv)
- ✅ Creates a Python virtual environment for better package management
- ✅ Installs Python packages from requirements.txt in the virtual environment
- ✅ Tests the installation

### Virtual Environment Management:
After running the setup script, you can use the virtual environment activation script:

```bash
# Activate the virtual environment for Short Maker
chmod +x activate_venv_macos.sh
./activate_venv_macos.sh
```

**What `activate_venv_macos.sh` does:**
- ✅ Checks if the virtual environment exists
- ✅ Activates the virtual environment automatically
- ✅ Shows Python version information
- ✅ Provides usage instructions
- ✅ Starts a new shell with the environment activated

This is useful when you want to:
- Run Short Maker manually with `python short-maker.py`
- Install additional Python packages
- Debug or develop with the exact environment used by Short Maker

**Note:** The GUI launcher scripts (`run_gui_macos.sh`) automatically handle virtual environment activation, so you typically don't need to use `activate_venv_macos.sh` for normal usage.

### Apple Silicon vs Intel:
The script automatically detects your Mac type and configures Homebrew accordingly:
- **Apple Silicon (M1/M2/M3)**: Installs to `/opt/homebrew/`
- **Intel Macs**: Installs to `/usr/local/`

### Troubleshooting:
- **Homebrew installation fails**: Check your internet connection and macOS version
- **Command not found after installation**: Restart your terminal or run `source ~/.zprofile`
- **Permission issues**: The script installs packages to user directory to avoid permission problems
- **GUI not visible on ARM64**: The script automatically installs `python-tk` and configures Tk properly
- **Tk deprecation warning**: This is automatically suppressed on macOS ARM64 systems

---

## 🛠️ ImageMagick Configuration (Windows)

Short Maker automatically handles ImageMagick configuration on Windows to solve the common `convert` vs `magick.exe` issue:

### Automatic Detection:
1. **Runtime Detection**: The main script automatically detects ImageMagick when starting
2. **PATH Search**: Looks for `magick.exe` in system PATH
3. **Common Paths**: Checks standard installation directories if not in PATH
4. **MoviePy Configuration**: Automatically configures MoviePy to use the correct binary

### Manual Verification:
If you want to verify ImageMagick is properly configured:

```cmd
# Test ImageMagick command (should show version info, not Windows convert.exe)
magick -version

# Test Python integration
python -c "from moviepy.editor import TextClip; print('✓ ImageMagick working')"
```

### Common Issues Resolved:
- ❌ **Old Issue**: `OSError: [WinError 2] The system cannot find the file specified` when creating text clips
- ✅ **New Solution**: Automatic detection and configuration of `magick.exe` vs `convert.exe`
- ❌ **Old Issue**: Manual MoviePy config file editing required
- ✅ **New Solution**: Runtime configuration using MoviePy's `change_settings()`

## 🧪 Testing Your Installation

After running any setup script, you can test if everything works:

```bash
# Test basic functionality
python short-maker.py --help

# Test with sample files (replace with your own video files)
python short-maker.py video1.mp4 video2.mp4 -o test_output.mp4

# Test text clip creation (ImageMagick integration)
python -c "
from moviepy.editor import TextClip
try:
    clip = TextClip('Test', fontsize=50, color='white', duration=1)
    print('✓ Text clips work - ImageMagick properly configured!')
except Exception as e:
    print(f'✗ Text clip error: {e}')
"
```

## 🚀 Quick GUI Launch

For the easiest experience, use the GUI launcher scripts that automatically check dependencies and run setup if needed:

### Windows
Simply double-click `run_gui_windows.bat` or run in Command Prompt:
```cmd
run_gui_windows.bat
```

### Linux
```bash
chmod +x run_gui_linux.sh
./run_gui_linux.sh
```

### macOS
```bash
chmod +x run_gui_macos.sh
./run_gui_macos.sh
```

These launcher scripts will:
- ✅ Check if Python is installed
- ✅ Verify all required packages are available
- ✅ Automatically run the appropriate setup script if dependencies are missing
- ✅ Launch the GUI once everything is ready
- ✅ Provide helpful error messages if something goes wrong

## 🆘 Getting Help

If you encounter issues:

1. **Check the error messages** - the scripts provide detailed error information
2. **Try the PowerShell script** (Windows) - if the batch script fails, try `setup_windows.ps1` for better error handling
3. **Verify prerequisites** - make sure you have the required OS version and permissions
4. **Manual installation** - if automated scripts fail, follow the manual installation instructions in README.md
5. **Check ImageMagick** (Windows) - run `magick -version` to verify it's properly installed
6. **Create an issue** - report bugs on the GitHub repository with:
   - Your operating system and version
   - Which script you used (`setup_windows.bat` or `setup_windows.ps1`)
   - The complete error message
   - What step failed
   - Output of `magick -version` (Windows only)

## 📝 What Gets Installed

All setup scripts install the same core components:

### System Dependencies:
- **FFmpeg**: Video and audio processing
- **ImageMagick**: Image processing and text rendering
- **Python 3.8+**: Runtime environment

### Python Packages:
- **moviepy==1.0.3**: Video editing library
- **gtts==2.4.0**: Google Text-to-Speech
- **pydub==0.25.1**: Audio processing
- **numpy>=1.21.0**: Numerical computing
- **Pillow==9.5.0**: Image processing (compatible version)

The total download size is approximately 200-500 MB depending on your system. 