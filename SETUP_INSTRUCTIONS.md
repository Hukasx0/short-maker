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

2. **Run the setup script:**
   - Navigate to the `short-maker` folder
   - Right-click on `setup_windows.bat`
   - Select **"Run as administrator"**
   - Wait for the installation to complete (this may take 5-15 minutes)

### What the script does:
- ✅ Installs Chocolatey package manager (if not present)
- ✅ Installs FFmpeg for video processing
- ✅ Installs ImageMagick for image processing
- ✅ Installs Python packages from requirements.txt
- ✅ Configures MoviePy to work with ImageMagick
- ✅ Tests the installation

### Troubleshooting:
- **"This script must be run as Administrator"**: Right-click the .bat file and select "Run as administrator"
- **Chocolatey installation fails**: Check your internet connection and Windows version
- **FFmpeg/ImageMagick not found**: The script will add them to PATH automatically, but you may need to restart your terminal

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
- ✅ Installs FFmpeg and ImageMagick via Homebrew
- ✅ Installs Python3 (if not present)
- ✅ Installs Python packages from requirements.txt
- ✅ Tests the installation

### Apple Silicon vs Intel:
The script automatically detects your Mac type and configures Homebrew accordingly:
- **Apple Silicon (M1/M2/M3)**: Installs to `/opt/homebrew/`
- **Intel Macs**: Installs to `/usr/local/`

### Troubleshooting:
- **Homebrew installation fails**: Check your internet connection and macOS version
- **Command not found after installation**: Restart your terminal or run `source ~/.zprofile`
- **Permission issues**: The script installs packages to user directory to avoid permission problems

---

## 🧪 Testing Your Installation

After running any setup script, you can test if everything works:

```bash
# Test basic functionality
python short-maker.py --help

# Test with sample files (replace with your own video files)
python short-maker.py video1.mp4 video2.mp4 -o test_output.mp4
```

## 🆘 Getting Help

If you encounter issues:

1. **Check the error messages** - the scripts provide detailed error information
2. **Verify prerequisites** - make sure you have the required OS version and permissions
3. **Manual installation** - if automated scripts fail, follow the manual installation instructions in README.md
4. **Create an issue** - report bugs on the GitHub repository with:
   - Your operating system and version
   - The complete error message
   - What step failed

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