"""
Short Maker
by Hubert "Hukasx0" Kasperek
https://github.com/Hukasx0/short-maker

Create vertical video compositions with narration, subtitles, and audio mixing.

Windows Setup Instructions:
1. Install FFmpeg: https://www.ffmpeg.org/download.html#build-windows
2. Install ImageMagick: https://imagemagick.org/script/download.php
   (Select "Win64 dynamic at 16 bits-per-pixel component")
3. Add FFmpeg and ImageMagick to system PATH
4. Edit moviepy config:
   - Locate config.py (typically in PythonXX\Lib\site-packages\moviepy)
   - Replace 'convert' with 'magick.exe' in IMAGEMAGICK_BINARY
"""

# Standard library imports
import os
import re
import math
import argparse
import tempfile
import subprocess

# Third-party imports
from moviepy.editor import *
from moviepy.audio.AudioClip import AudioClip, concatenate_audioclips
from gtts import gTTS
import numpy as np

def process_clip(clip: VideoClip, target_width: int, target_height: int) -> VideoClip:
    """
    Process video clip to fit target dimensions while maintaining aspect ratio.
    
    Args:
        clip: Input video clip
        target_width: Desired output width in pixels
        target_height: Desired output height in pixels
        
    Returns:
        VideoClip: Processed clip with exact target dimensions
    """
    original_aspect = clip.w / clip.h
    target_aspect = target_width / target_height

    # Scale while maintaining aspect ratio
    if original_aspect > target_aspect:
        resized = clip.resize(height=target_height)
    else:
        resized = clip.resize(width=target_width)

    # Center cropping to target dimensions
    if resized.w > target_width:
        cropped = resized.crop(
            x_center=resized.w/2,
            y_center=resized.h/2,
            width=target_width,
            height=target_height
        )
    elif resized.h > target_height:
        cropped = resized.crop(
            x_center=resized.w/2,
            y_center=resized.h/2,
            width=target_width,
            height=target_height
        )
    else:
        cropped = resized
    
    return cropped

def loop_audio(audio_clip: AudioClip, duration: float) -> AudioClip:
    """
    Loop audio to match specified duration.
    
    Args:
        audio_clip: Input audio clip
        duration: Target duration in seconds
        
    Returns:
        AudioClip: Looped audio matching target duration
    """
    loops = []
    current_duration = 0
    while current_duration < duration:
        loops.append(audio_clip)
        current_duration += audio_clip.duration
    return concatenate_audioclips(loops).subclip(0, duration)

def create_video_short(args: argparse.Namespace) -> VideoClip:
    """
    Create vertical video composition from input videos.
    
    Args:
        args: Command-line arguments containing input parameters
        
    Returns:
        VideoClip: Processed video clip with combined elements
    """
    # Load video clips
    top_clip = VideoFileClip(args.top_video)
    bottom_clip = VideoFileClip(args.bottom_video) if args.bottom_video else None

    # Parse resolution
    target_width, target_height = map(int, args.resolution.split('x'))

    if args.bottom_video:
        # Two-video vertical composition
        half_height = target_height // 2

        # Process both clips
        processed_top = process_clip(top_clip, target_width, half_height)
        processed_bottom = process_clip(bottom_clip, target_width, half_height)

        # Loop bottom video if needed
        top_duration = processed_top.duration
        loops_needed = math.ceil(top_duration / processed_bottom.duration)
        looped_bottom = concatenate_videoclips([processed_bottom]*loops_needed)
        looped_bottom = looped_bottom.subclip(0, top_duration)

        # Combine vertically
        final_video = clips_array([[processed_top], [looped_bottom]])
        total_duration = top_duration
    else:
        # Single video processing
        processed_top = process_clip(top_clip, target_width, target_height)
        final_video = processed_top
        total_duration = processed_top.duration

    # Audio mixing
    audio_tracks = []

    # Original video audio
    if args.audio and processed_top.audio:
        top_audio = loop_audio(processed_top.audio, total_duration)
        audio_tracks.append(top_audio)

    # Background music
    if args.music:
        music = AudioFileClip(args.music)
        music_looped = loop_audio(music, total_duration)
        music_looped = music_looped.volumex(args.music_volume / 100.0)
        audio_tracks.append(music_looped)

    # Combine audio tracks
    if audio_tracks:
        final_audio = CompositeAudioClip(audio_tracks)
        final_video = final_video.set_audio(final_audio)
    else:
        final_video = final_video.without_audio()

    return final_video

def split_phrases(text: str, max_chars: int = 50) -> list:
    """
    Split text into subtitle phrases using smart punctuation detection.
    
    Args:
        text: Input text to split
        max_chars: Maximum characters per subtitle phrase
        
    Returns:
        list: List of phrase chunks for subtitles
    """
    pattern = r'(?<=[.!?]) +|(?<=\.,) +|(?<=,) +(?=\w{3,})'
    phrases = re.split(pattern, text)
    chunks = []
    current_chunk = ""
    
    for phrase in phrases:
        clean_phrase = re.sub(r'[\\@$%^&*()\[\]{};:"/<>#]', '', phrase.strip())
        if not clean_phrase:
            continue
            
        if len(current_chunk) + len(clean_phrase) + 1 <= max_chars:
            current_chunk += " " + clean_phrase if current_chunk else clean_phrase
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = clean_phrase
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def calculate_phrase_durations(text_chunks: list, lang: str) -> list:
    """
    Calculate duration for each text chunk using Text-to-Speech.
    
    Args:
        text_chunks: List of text phrases
        lang: Language code for TTS
        
    Returns:
        list: Durations for each phrase in seconds
    """
    durations = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        for i, chunk in enumerate(text_chunks):
            try:
                tts = gTTS(text=chunk, lang=lang, slow=False)
                tmp_file = os.path.join(tmp_dir, f"temp_{i}.mp3")
                tts.save(tmp_file)
                audio = AudioFileClip(tmp_file)
                durations.append(audio.duration)
                audio.close()
            except Exception as e:
                print(f"Error processing phrase '{chunk}': {str(e)}")
                durations.append(0)
    return durations

def add_narration(video_clip: VideoClip, args: argparse.Namespace) -> tuple:
    """
    Add narrated audio and subtitles to video clip with speed adjustment.
    
    Args:
        video_clip: Input video clip
        args: Command-line arguments
        
    Returns:
        tuple: (Final video clip, List of TTS temp file paths)
    """
    # Load and clean text
    with open(args.text, 'r', encoding='utf-8') as f:
        text_content = f.read().replace('\n', ' ')
    cleaned_text = re.sub(r'[\\@$%^&*()\[\]{};:"/<>#]', '', text_content)
    phrases = split_phrases(cleaned_text)

    if not phrases and args.subtitles:
        raise ValueError("No text available for subtitles!")

    # Generate TTS audio with temporary file
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tts_temp:
        tts_temp_filename = tts_temp.name

    tts = gTTS(text=" ".join(phrases), lang=args.lang, slow=False)
    tts.save(tts_temp_filename)
    tts_temp_files = [tts_temp_filename]  # Track all temporary audio files

    # Process speed adjustment with FFmpeg's atempo filter
    if args.speed != 1.0:
        # Create temporary file for speed-adjusted audio
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as speed_temp:
            speed_temp_filename = speed_temp.name
        
        # Apply atempo filter to change speed without pitch alteration
        ffmpeg_cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file without prompting
            '-i', tts_temp_filename,
            '-filter:a', f'atempo={args.speed}',
            speed_temp_filename
        ]
        
        try:
            subprocess.run(ffmpeg_cmd, check=True)
            audio_clip = AudioFileClip(speed_temp_filename)
            tts_temp_files.append(speed_temp_filename)
        except Exception as e:
            print(f"Error processing audio speed: {e}")
            audio_clip = AudioFileClip(tts_temp_filename)
    else:
        audio_clip = AudioFileClip(tts_temp_filename)

    # Calculate phrase durations from original speed audio
    original_audio_duration = audio_clip.duration
    phrase_durations = calculate_phrase_durations(phrases, args.lang)
    
    # Adjust subtitle durations based on speed parameter
    # (Durations already handled by FFmpeg processing, but need to match subtitle timing)
    if args.speed != 1.0:
        phrase_durations = [d / args.speed for d in phrase_durations]

    total_duration = sum(phrase_durations)
    
    # Normalize durations to match audio length
    if abs(total_duration - audio_clip.duration) > 1:
        ratio = audio_clip.duration / total_duration
        phrase_durations = [d * ratio for d in phrase_durations]

    # Handle video duration requirements
    if args.use_video_length:
        video_duration = video_clip.duration
        if audio_clip.duration > video_duration:
            audio_clip = audio_clip.subclip(0, video_duration)
        else:
            # Add silence pad if narration is shorter than video
            silence = AudioClip(
                lambda t: np.zeros((np.size(t), 2), dtype=np.float32),
                duration=video_duration - audio_clip.duration,
                fps=44100
            )
            audio_clip = concatenate_audioclips([audio_clip, silence])

    # Audio mixing with ducking effect
    final_audio = audio_clip
    if args.video_volume > 0 and video_clip.audio is not None:
        bg_audio = video_clip.audio.volumex(args.video_volume / 100.0)
        target_duration = video_clip.duration if args.use_video_length else audio_clip.duration
        
        # Ducking implementation (lower background during narration)
        if args.duck_volume is not None:
            duck_factor = args.duck_volume / 100.0
            narration_duration = original_audio_duration
            
            if args.use_video_length:
                narration_duration = min(narration_duration, video_clip.duration)
            
            if bg_audio.duration > narration_duration:
                # Split and duck only during narration
                ducked = bg_audio.subclip(0, narration_duration).volumex(duck_factor)
                unducked = bg_audio.subclip(narration_duration)
                bg_audio = concatenate_audioclips([ducked, unducked])
            else:
                # Duck entire audio if shorter than narration
                bg_audio = bg_audio.volumex(duck_factor)
        
        final_audio = CompositeAudioClip([audio_clip, bg_audio])

    # Subtitle generation
    text_clips = []
    if args.subtitles and phrases:
        current_time = 0
        FONT_SIZE = 60
        MAX_TEXT_WIDTH = 1000
        
        for i, (phrase, duration) in enumerate(zip(phrases, phrase_durations)):
            try:
                # Create text clip with background box
                txt_clip = TextClip(
                    phrase,
                    fontsize=FONT_SIZE,
                    color=args.text_color,  # Use user-specified color
                    font='Arial-Bold',
                    stroke_color=args.text_border_color if args.text_border_color else 'black',  # Default to black if not specified
                    stroke_width=1.5,  # Always have border
                    size=(MAX_TEXT_WIDTH, None),
                    method='caption',
                    align='center'
                ).set_duration(duration)

                # Add fade-in animation if requested
                if args.animate_text:
                    txt_clip = txt_clip.fadein(args.fade_duration) # use user-specified fade duration
                
                # Position text clip at center and set timing
                txt_clip = txt_clip.set_position('center').set_start(current_time)
                
                # Conditional semi transparent background box creation
                if args.bg_box:  # Only create if enabled (default)
                    bg_clip = ColorClip(
                        (txt_clip.size[0] + 40, txt_clip.size[1] + 40),
                        color=(0, 0, 0)
                    ).set_opacity(0.6).set_duration(duration)
                    bg_clip = bg_clip.set_position('center').set_start(current_time)
                    text_clips.append(bg_clip)

                text_clips.append(txt_clip)
                current_time += duration

            except Exception as e:
                print(f"Error in phrase {i+1}: '{phrase}'")
                raise

    # Compose final video with subtitles
    final_video = CompositeVideoClip([video_clip] + text_clips)
    final_video = final_video.set_audio(final_audio)

    # Set final duration based on user preference
    if args.use_video_length:
        final_video = final_video.set_duration(video_clip.duration)
    else:
        final_video = final_video.set_duration(audio_clip.duration)

    return final_video, tts_temp_filename

def main():
    """Main function handling command-line interface and processing pipeline"""
    parser = argparse.ArgumentParser(
        description='Create short videos with narration and subtitles',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Video composition arguments
    parser.add_argument('top_video', help='Path to top video file')
    parser.add_argument('bottom_video', nargs='?', 
                      help='Path to bottom video file (optional)', default=None)
    parser.add_argument('-m', '--music', help='Background music file', default=None)
    parser.add_argument('-o', '--output', help='Output filename', default='output.mp4')
    parser.add_argument('-r', '--resolution', help='Target resolution WIDTHxHEIGHT', 
                      default='1080x1920')
    parser.add_argument('-mv', '--music-volume', type=float,
                      help='Music volume (0-100%)', default=100.0)
    parser.add_argument('-a', '--audio', action='store_true',
                      help='Include audio from top video')
    parser.add_argument('-vv', '--video-volume', type=float,
                      help='Original video volume (0-100%)', default=0.0)

    # Narration arguments
    parser.add_argument('-t', '--text', help='Text file for narration', default=None)
    parser.add_argument('-l', '--lang', help='Narration language code', default='en')
    parser.add_argument('-ns', '--no-subtitles', action='store_false', dest='subtitles',
                      help='Disable subtitles')
    parser.add_argument('--duck-volume', type=float, nargs='?', const=50,
                      help='Lower background audio during narration (0-100% volume)', default=None)
    parser.add_argument('--use-video-length', action='store_true',
                      help='Use original video length instead of narration length')
    parser.add_argument('-s', '--speed', type=float, default=1.0,
                      help='Narration speed multiplier (0.5 = slower, 1.0 = default, 2.0 = faster)')
    parser.add_argument('--animate-text', action='store_true',
                    help='Enable subtle fade-in animation for subtitles')
    parser.add_argument('--fade-duration', type=float, default=0.5,
                    help='Duration of text fade-in animation in seconds')
    parser.add_argument('--text-color', type=str, default='white',
                        help='Text color for subtitles (name or hex code)')
    parser.add_argument('--no-bg-box', action='store_false', dest='bg_box',
                        help='Disable semi-transparent background box behind text')
    parser.add_argument('--text-border-color', type=str, default='black',
                        help='Add border/shadow to text using specified color')

    args = parser.parse_args()

    # Validate resolution format
    if not re.match(r'\d+x\d+', args.resolution):
        raise ValueError("Invalid resolution format. Use WIDTHxHEIGHT (e.g., 1080x1920)")

    # Validate speed parameter
    if args.speed <= 0:
        raise ValueError("Speed factor must be greater than 0")

    # Validate fade duration
    if args.fade_duration < 0:
        raise ValueError("Fade duration must be greater than or equal to 0")

    tts_temp_file = None
    video_clip = None
    final_clip = None

    try:
        # Create video composition
        video_clip = create_video_short(args)
        
        # Add narration if requested
        if args.text:
            final_clip, tts_temp_file = add_narration(video_clip, args)
        else:
            final_clip = video_clip

        # Export final video
        final_clip.write_videofile(
            args.output,
            fps=30,
            codec="libx264",
            audio_codec="aac",
            threads=4,
            preset="fast",
            ffmpeg_params=["-crf", "23"]
        )
    finally:
        # Cleanup resources
        if video_clip:
            video_clip.close()
        if final_clip:
            final_clip.close()
        if tts_temp_file and os.path.exists(tts_temp_file):
            try:
                os.remove(tts_temp_file)
            except Exception as e:
                print(f"Error deleting temporary file: {e}")

if __name__ == "__main__":
    """
    Example Usage:
    
    # Basic vertical composition
    python short-maker.py top.mp4 bottom.mp4 -m music.mp3 -o output.mp4
    
    # Full narration example
    python short-maker.py input.mp4 -t script.txt --animate-text -l en -o narrated.mp4
    
    # Advanced parameters
    python short-maker.py top.mp4 bottom.mp4 \  
        -m music.mp3 -t script.txt \  
        -o final.mp4 -r 1080x1920 \  
        -mv 20 -vv 100 --duck-volume 40 \  
        -a \
        --use-video-length

    # Custom subtitle appearance example
    python short-maker.py input.mp4 -t script.txt \
        --animate-text \
        --fade-duration 0.8 \
        --text-color "#00FF00" \
        --text-border-color black \
        --no-bg-box \
        -o styled.mp4
    """
    main()
