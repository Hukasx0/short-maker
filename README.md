# Short Maker 🎬  

*"in the future entertainment will be randomly generated". Automate vertical video creation with zero AI*  

**Create professional short vertical videos** by combining videos, adding narration (TTS), dynamic subtitles, and audio mixing. Perfect for content creators who want to streamline their workflow. (Or if you want to make the [Dead Internet Theory](https://en.wikipedia.org/wiki/Dead_Internet_theory) real)

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://github.com/Hukasx0/short-maker/blob/main/LICENSE)

### Example Created Video:
Check out an example video created using Short Maker:  
[Watch the video on Twitter](https://x.com/hukasx0/status/1883965580702802214)

Created using two video files and a text file 
```
python short-maker.py video1.mp4 video2.mp4 -t script.txt -a --duck-volume 5 -vv 100
```

## Features ✨  
- 📼 Create vertical (9:16) video compositions  
- 🔊 Text-to-Speech narration with sync subtitles  
- 🎵 Background music mixing with volume control  
- 🦆 Audio ducking during narration  
- 🖼️ Smart video cropping/resizing  
- 🐍 Pure Python, FFmpeg and ImageMagick - no AI/ML dependencies  

## Installation 📦  

### Prerequisites  
- Python 3.8+  
- FFmpeg  
- ImageMagick  

**Windows:**  
```powershell
# 1. Install dependencies  
choco install ffmpeg imagemagick  

# 2. Add to PATH (search for Environment Variables)  
#    Add paths to ffmpeg.exe and magick.exe  

# 3. Edit moviepy config  
#    Locate config.py in PythonXX\Lib\site-packages\moviepy  
#    Change IMAGEMAGICK_BINARY to "magick.exe"
```

**Linux:**  
```bash
sudo apt-get install ffmpeg imagemagick
```

**macOS:**  
```bash
brew install ffmpeg imagemagick
```

**All Systems:**  
```bash
pip install -r requirements.txt
```

## Preparation 🛠️  
1. Install required tools from above  
2. Prepare your video file/files
3. (Optional) For narration: create text file with script  
4. (Optional) Find background music  

## Usage 🚀  

### Basic Example  
```bash
# Two videos with background music  
python short-maker.py top.mp4 bottom.mp4 -m music.mp3 -o output.mp4  

# Single video with narration  
python short-maker.py input.mp4 -t script.txt -o narrated.mp4
```

### Advanced Example  
```bash
python short-maker.py top.mp4 bottom.mp4 \  
  -m music.mp3 -t script.txt \  
  -o final.mp4 -r 1080x1920 \  
  -mv 20 -vv 100 --duck-volume 40 \  
  -a \
  --animate-text \
  --fade-duration 0.3 \
  --text-color "#00FF00" \
  --text-border-color black \
  --no-bg-box \
  --use-video-length
```

### All Flags Explained 🏁  
| Flag | Description | Default |  
|------|-------------|---------|  
| **Video Composition** | |  
| `top_video` | Path to main video file | **Required** |  
| `bottom_video` | Secondary video (optional) | None |  
| `-m`, `--music` | Background music file | None |  
| `-o`, `--output` | Output filename | output.mp4 |  
| `-r`, `--resolution` | Target resolution | 1080x1920 |  
| `-mv`, `--music-volume` | Music volume (0-100) | 100 |  
| `-a`, `--audio` | Keep original video audio | False |
| `-vv`, `--video-volume` | Original video volume (requires `-a` to work) | 0 |  
| **Narration** | |  
| `-t`, `--text` | Narration script file | None |  
| `-l`, `--lang` | TTS language code | en |  
| `-ns`, `--no-subtitles` | Disable subtitles | Enabled |  
| `--duck-volume` | Lower background audio during TTS speech | Off |  
| `--use-video-length` | Match video duration | False |  
| `-s`, `--speed` | Narration speed multiplier | 1.0 |
| `--animate-text` |	Enable subtitle fade-in animation |	False
| `--fade-duration` |	Text fade-in animation duration (seconds) |	0.5
| `--text-color` |	Subtitle text color (name/hex) |	white
| `--no-bg-box` |	Disable semi-transparent background box |	Enabled
| `--text-border-color` |	Text border/shadow color |	black

## Why No AI? 🤖  
This script intentionally uses simple TTS (gTTS) instead of AI voice generation:  
1. No API keys required  
2. Faster processing  
3. Smaller footprint  

## License & Author 📜  
**Author:** [Hubert Kasperek](https://github.com/Hukasx0)

**License:** [GNU Affero General Public License v3.0](https://github.com/Hukasx0/short-maker/blob/main/LICENSE)
