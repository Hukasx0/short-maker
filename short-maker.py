"""
Short Maker
by Hubert "Hukasx0" Kasperek
https://github.com/Hukasx0/short-maker

Create vertical video compositions with narration, subtitles, and audio mixing.

Windows Setup Instructions:
1. Run setup_windows.bat as Administrator (RECOMMENDED - automates everything below)
   OR follow manual steps:
2. Install FFmpeg: https://www.ffmpeg.org/download.html#build-windows
3. Install ImageMagick: https://imagemagick.org/script/download.php
   (Select "Win64 dynamic at 16 bits-per-pixel component")
4. Add FFmpeg and ImageMagick to system PATH
5. Ensure 'magick.exe' (not 'convert') is accessible from command line

Note: This script automatically detects and configures ImageMagick on Windows.
"""

# Standard library imports
import os
import re
import math
import argparse
import tempfile
import subprocess

# Monkey-patch for FFMPEG_AudioReader to ignore errors when closing the process.
try:
    from moviepy.audio.io import readers
except ImportError:
    readers = None

if readers is not None and hasattr(readers, "FFMPEG_AudioReader"):
    original_del = readers.FFMPEG_AudioReader.__del__

    def safe_del(self):
        try:
            original_del(self)
        except Exception:
            pass  # Ignore any exceptions during process termination.

    readers.FFMPEG_AudioReader.__del__ = safe_del

# Third-party imports
from moviepy.editor import *
from moviepy.audio.AudioClip import AudioClip, concatenate_audioclips
from gtts import gTTS
import numpy as np

# Configure ImageMagick for Windows
import platform
if platform.system() == "Windows":
    try:
        from moviepy.config import change_settings
        import shutil
        
        # Try to find magick.exe in PATH
        magick_path = shutil.which("magick")
        if magick_path:
            change_settings({"IMAGEMAGICK_BINARY": magick_path})
            print(f"ImageMagick configured: {magick_path}")
        else:
            # Try common installation paths
            common_paths = [
                r"C:\Program Files\ImageMagick-7.*\magick.exe",
                r"C:\Program Files (x86)\ImageMagick-7.*\magick.exe",
                r"C:\ProgramData\chocolatey\bin\magick.exe",
                r"C:\tools\ImageMagick\magick.exe"
            ]
            
            import glob
            for path_pattern in common_paths:
                matches = glob.glob(path_pattern)
                if matches:
                    magick_path = matches[0]  # Use first match
                    change_settings({"IMAGEMAGICK_BINARY": magick_path})
                    print(f"ImageMagick configured: {magick_path}")
                    break
            else:
                print("Warning: ImageMagick (magick.exe) not found. Text clips may not work properly.")
                print("Please install ImageMagick from: https://imagemagick.org/script/download.php")
    
    except Exception as e:
        print(f"Warning: Could not configure ImageMagick: {e}")
        print("Some text features may not work properly.")
        print("Please ensure ImageMagick is installed and 'magick.exe' is in your PATH.")

# GUI imports
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False

def is_image_file(filepath: str) -> bool:
    """
    Check if file is an image based on extension.
    
    Args:
        filepath: Path to the file
        
    Returns:
        bool: True if file is an image, False otherwise
    """
    if not filepath:
        return False
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp'}
    return os.path.splitext(filepath.lower())[1] in image_extensions

def parse_media_input(media_input: str) -> list:
    """
    Parse media input which can be:
    - Single file path
    - Multiple file paths separated by semicolons
    - Directory path (will use all images/videos in directory)
    
    Args:
        media_input: Input string containing file path(s) or directory
        
    Returns:
        list: List of file paths
    """
    if not media_input:
        return []
    
    # Check if it's a directory
    if os.path.isdir(media_input):
        # Get all image and video files from directory
        supported_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.webp', 
                              '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
        files = []
        for file in sorted(os.listdir(media_input)):
            if os.path.splitext(file.lower())[1] in supported_extensions:
                files.append(os.path.join(media_input, file))
        return files
    
    # Check if it contains semicolons (multiple files)
    if ';' in media_input:
        files = [f.strip() for f in media_input.split(';') if f.strip()]
        # Validate all files exist
        for file in files:
            if not os.path.exists(file):
                raise ValueError(f"File not found: {file}")
        return files
    
    # Single file
    if not os.path.exists(media_input):
        raise ValueError(f"File not found: {media_input}")
    return [media_input]

def load_media_clip(filepath: str, default_duration: float = 5.0) -> VideoClip:
    """
    Load either video or image file as VideoClip.
    
    Args:
        filepath: Path to video or image file
        default_duration: Duration for image clips in seconds
        
    Returns:
        VideoClip: Loaded clip (video or image converted to video)
    """
    if is_image_file(filepath):
        # Load image and convert to video clip
        image_clip = ImageClip(filepath, duration=default_duration)
        return image_clip
    else:
        # Load video file
        return VideoFileClip(filepath)

def load_media_sequence(file_paths: list, default_duration: float = 5.0, transition_type: str = "none", transition_duration: float = 0.5) -> VideoClip:
    """
    Load multiple media files and concatenate them into a single clip with transitions.
    
    Args:
        file_paths: List of file paths to load
        default_duration: Duration for image clips in seconds
        transition_type: Type of transition ("none", "fade", "slide_left", "slide_right", "slide_up", "slide_down", "zoom_in", "zoom_out")
        transition_duration: Duration of transition effect in seconds
        
    Returns:
        VideoClip: Concatenated clip from all input files with transitions
    """
    if not file_paths:
        raise ValueError("No files provided")
    
    if len(file_paths) == 1:
        return load_media_clip(file_paths[0], default_duration)
    
    clips = []
    for filepath in file_paths:
        clip = load_media_clip(filepath, default_duration)
        clips.append(clip)
    
    if transition_type == "none" or transition_duration <= 0:
        # Simple concatenation without transitions
        return concatenate_videoclips(clips)
    
    # Apply transitions between clips
    return apply_transitions(clips, transition_type, transition_duration)

def apply_transitions(clips: list, transition_type: str, transition_duration: float) -> VideoClip:
    """
    Apply transitions between video clips.
    
    Args:
        clips: List of video clips
        transition_type: Type of transition effect
        transition_duration: Duration of transition in seconds
        
    Returns:
        VideoClip: Clips with transitions applied
    """
    if len(clips) <= 1:
        return clips[0] if clips else None
    
    # Ensure transition duration doesn't exceed clip duration
    min_clip_duration = min(clip.duration for clip in clips)
    actual_transition_duration = min(transition_duration, min_clip_duration / 3)
    
    if transition_type == "fade":
        # For fade transitions, use crossfadein
        result_clips = []
        current_time = 0
        
        for i, clip in enumerate(clips):
            if i == 0:
                # First clip - no fade in, but fade out at the end
                if len(clips) > 1:
                    processed_clip = clip.fadeout(actual_transition_duration)
                else:
                    processed_clip = clip
                processed_clip = processed_clip.set_start(current_time)
                result_clips.append(processed_clip)
                current_time += clip.duration - actual_transition_duration
            else:
                # Subsequent clips - fade in and fade out (except last)
                if i == len(clips) - 1:
                    # Last clip - only fade in
                    processed_clip = clip.fadein(actual_transition_duration)
                else:
                    # Middle clips - fade in and out
                    processed_clip = clip.fadein(actual_transition_duration).fadeout(actual_transition_duration)
                
                processed_clip = processed_clip.set_start(current_time)
                result_clips.append(processed_clip)
                
                if i == len(clips) - 1:
                    current_time += clip.duration
                else:
                    current_time += clip.duration - actual_transition_duration
        
        return CompositeVideoClip(result_clips)
    
    else:
        # For other transitions, apply entrance effects
        result_clips = []
        current_time = 0
        
        for i, clip in enumerate(clips):
            if i == 0:
                # First clip - no entrance effect
                processed_clip = clip.set_start(current_time)
                result_clips.append(processed_clip)
                current_time += clip.duration - (actual_transition_duration if len(clips) > 1 else 0)
            else:
                # Apply entrance transition
                processed_clip = apply_entrance_transition(clip, transition_type, actual_transition_duration)
                processed_clip = processed_clip.set_start(current_time)
                result_clips.append(processed_clip)
                
                if i == len(clips) - 1:
                    current_time += clip.duration
                else:
                    current_time += clip.duration - actual_transition_duration
        
        return CompositeVideoClip(result_clips)

def apply_entrance_transition(clip: VideoClip, transition_type: str, duration: float) -> VideoClip:
    """
    Apply entrance transition effect to a clip.
    
    Args:
        clip: Video clip to apply transition to
        transition_type: Type of transition
        duration: Duration of transition
        
    Returns:
        VideoClip: Clip with entrance transition applied
    """
    if transition_type == "fade":
        return clip.fadein(duration)
    
    elif transition_type == "slide_left":
        # Slide in from right
        return clip.set_position(lambda t: (max(0, clip.w * (1 - t/duration)) if t < duration else 0, 'center'))
    
    elif transition_type == "slide_right":
        # Slide in from left
        return clip.set_position(lambda t: (min(0, -clip.w * (1 - t/duration)) if t < duration else 0, 'center'))
    
    elif transition_type == "slide_up":
        # Slide in from bottom
        return clip.set_position(lambda t: ('center', max(0, clip.h * (1 - t/duration)) if t < duration else 'center'))
    
    elif transition_type == "slide_down":
        # Slide in from top
        return clip.set_position(lambda t: ('center', min(0, -clip.h * (1 - t/duration)) if t < duration else 'center'))
    
    elif transition_type == "zoom_in":
        # Zoom in effect with proper scaling and positioning
        def zoom_effect(t):
            if t < duration:
                scale = 0.3 + 0.7 * (t / duration)  # Scale from 30% to 100%
                return scale
            return 1.0
        
        def zoom_position(t):
            if t < duration:
                # Keep centered during zoom
                return ('center', 'center')
            return ('center', 'center')
        
        return clip.resize(zoom_effect).set_position(zoom_position)
    
    elif transition_type == "zoom_out":
        # Zoom out effect (start big, shrink to normal) with proper scaling
        def zoom_effect(t):
            if t < duration:
                scale = 1.5 - 0.5 * (t / duration)  # Scale from 150% to 100%
                return scale
            return 1.0
        
        def zoom_position(t):
            if t < duration:
                # Keep centered during zoom
                return ('center', 'center')
            return ('center', 'center')
        
        return clip.resize(zoom_effect).set_position(zoom_position)
    
    else:
        return clip

def apply_single_clip_transitions(clip: VideoClip, start_transition: str, end_transition: str, transition_duration: float) -> VideoClip:
    """
    Apply start and end transitions to a single clip
    
    Args:
        clip: Video clip to apply transitions to
        start_transition: Type of start transition
        end_transition: Type of end transition
        transition_duration: Duration of transition effects
        
    Returns:
        VideoClip: Clip with start/end transitions applied
    """
    if not clip or clip.duration <= 0:
        return clip
        
    result_clip = clip
    
    # Ensure transition duration doesn't exceed clip duration and is reasonable
    max_transition_duration = min(transition_duration, clip.duration / 3, 2.0)  # Max 2 seconds
    actual_transition_duration = max(0.1, max_transition_duration)  # Min 0.1 seconds
    
    # Apply start transition
    if start_transition and start_transition != "none":
        try:
            if start_transition == "fade":
                result_clip = result_clip.fadein(actual_transition_duration)
            
            elif start_transition == "zoom_in":
                # Create zoom-in effect using resize with proper error handling
                def zoom_in_func(get_frame, t):
                    if t < actual_transition_duration:
                        # Scale from 50% to 100%
                        progress = t / actual_transition_duration
                        scale = 0.5 + 0.5 * progress
                        # Create a temporary clip with scaling
                        try:
                            frame = get_frame(t)
                            temp_clip = ImageClip(frame, duration=0.1).resize(scale)
                            return temp_clip.get_frame(0)
                        except:
                            return get_frame(t)
                    return get_frame(t)
                
                result_clip = result_clip.fl(zoom_in_func, apply_to=['mask'])
            
            elif start_transition == "zoom_out":
                # Create zoom-out effect (start big, end normal)
                def zoom_out_func(get_frame, t):
                    if t < actual_transition_duration:
                        # Scale from 150% to 100%
                        progress = t / actual_transition_duration
                        scale = 1.5 - 0.5 * progress
                        try:
                            frame = get_frame(t)
                            temp_clip = ImageClip(frame, duration=0.1).resize(scale)
                            return temp_clip.get_frame(0)
                        except:
                            return get_frame(t)
                    return get_frame(t)
                
                result_clip = result_clip.fl(zoom_out_func, apply_to=['mask'])
            
            elif start_transition.startswith("slide_"):
                # For slide transitions, use position-based effects with fade fallback
                if start_transition == "slide_left":
                    # Slide in from right side
                    def slide_pos(t):
                        if t < actual_transition_duration:
                            progress = t / actual_transition_duration
                            # Start off-screen to the right, slide to center
                            x_offset = result_clip.w * (1 - progress)
                            return (x_offset, 'center')
                        return ('center', 'center')
                    
                    result_clip = result_clip.set_position(slide_pos)
                
                elif start_transition == "slide_right":
                    # Slide in from left side
                    def slide_pos(t):
                        if t < actual_transition_duration:
                            progress = t / actual_transition_duration
                            # Start off-screen to the left, slide to center
                            x_offset = -result_clip.w * (1 - progress)
                            return (x_offset, 'center')
                        return ('center', 'center')
                    
                    result_clip = result_clip.set_position(slide_pos)
                
                elif start_transition == "slide_up":
                    # Slide in from bottom
                    def slide_pos(t):
                        if t < actual_transition_duration:
                            progress = t / actual_transition_duration
                            # Start off-screen at bottom, slide to center
                            y_offset = result_clip.h * (1 - progress)
                            return ('center', y_offset)
                        return ('center', 'center')
                    
                    result_clip = result_clip.set_position(slide_pos)
                
                elif start_transition == "slide_down":
                    # Slide in from top
                    def slide_pos(t):
                        if t < actual_transition_duration:
                            progress = t / actual_transition_duration
                            # Start off-screen at top, slide to center
                            y_offset = -result_clip.h * (1 - progress)
                            return ('center', y_offset)
                        return ('center', 'center')
                    
                    result_clip = result_clip.set_position(slide_pos)
                
                # Add fade for smoother effect
                result_clip = result_clip.fadein(actual_transition_duration * 0.5)
            
        except Exception as e:
            print(f"Warning: Start transition '{start_transition}' failed: {e}. Using fade instead.")
            result_clip = result_clip.fadein(actual_transition_duration)
    
    # Apply end transition
    if end_transition and end_transition != "none":
        try:
            if end_transition == "fade":
                result_clip = result_clip.fadeout(actual_transition_duration)
            
            elif end_transition == "zoom_in":
                # Zoom in at the end (shrink to 30%)
                end_start_time = result_clip.duration - actual_transition_duration
                
                def zoom_in_end_func(get_frame, t):
                    if t > end_start_time:
                        # Scale from 100% to 30%
                        progress = (t - end_start_time) / actual_transition_duration
                        scale = 1.0 - 0.7 * progress
                        try:
                            frame = get_frame(t)
                            temp_clip = ImageClip(frame, duration=0.1).resize(scale)
                            return temp_clip.get_frame(0)
                        except:
                            return get_frame(t)
                    return get_frame(t)
                
                result_clip = result_clip.fl(zoom_in_end_func, apply_to=['mask'])
            
            elif end_transition == "zoom_out":
                # Zoom out at the end (expand to 150%)
                end_start_time = result_clip.duration - actual_transition_duration
                
                def zoom_out_end_func(get_frame, t):
                    if t > end_start_time:
                        # Scale from 100% to 150%
                        progress = (t - end_start_time) / actual_transition_duration
                        scale = 1.0 + 0.5 * progress
                        try:
                            frame = get_frame(t)
                            temp_clip = ImageClip(frame, duration=0.1).resize(scale)
                            return temp_clip.get_frame(0)
                        except:
                            return get_frame(t)
                    return get_frame(t)
                
                result_clip = result_clip.fl(zoom_out_end_func, apply_to=['mask'])
            
            elif end_transition.startswith("slide_"):
                # For slide-out transitions at the end
                end_start_time = result_clip.duration - actual_transition_duration
                
                if end_transition == "slide_left":
                    # Slide out to the left
                    def slide_out_pos(t):
                        if t > end_start_time:
                            progress = (t - end_start_time) / actual_transition_duration
                            x_offset = -result_clip.w * progress
                            return (x_offset, 'center')
                        return ('center', 'center')
                    
                    result_clip = result_clip.set_position(slide_out_pos)
                
                elif end_transition == "slide_right":
                    # Slide out to the right
                    def slide_out_pos(t):
                        if t > end_start_time:
                            progress = (t - end_start_time) / actual_transition_duration
                            x_offset = result_clip.w * progress
                            return (x_offset, 'center')
                        return ('center', 'center')
                    
                    result_clip = result_clip.set_position(slide_out_pos)
                
                elif end_transition == "slide_up":
                    # Slide out to the top
                    def slide_out_pos(t):
                        if t > end_start_time:
                            progress = (t - end_start_time) / actual_transition_duration
                            y_offset = -result_clip.h * progress
                            return ('center', y_offset)
                        return ('center', 'center')
                    
                    result_clip = result_clip.set_position(slide_out_pos)
                
                elif end_transition == "slide_down":
                    # Slide out to the bottom
                    def slide_out_pos(t):
                        if t > end_start_time:
                            progress = (t - end_start_time) / actual_transition_duration
                            y_offset = result_clip.h * progress
                            return ('center', y_offset)
                        return ('center', 'center')
                    
                    result_clip = result_clip.set_position(slide_out_pos)
                
                # Add fade for smoother effect
                result_clip = result_clip.fadeout(actual_transition_duration * 0.5)
            
        except Exception as e:
            print(f"Warning: End transition '{end_transition}' failed: {e}. Using fade instead.")
            result_clip = result_clip.fadeout(actual_transition_duration)
    
    return result_clip

def adjust_media_duration_for_narration(args: argparse.Namespace, narration_duration: float = None) -> tuple:
    """
    Reload media clips with appropriate duration when narration is used.
    
    Args:
        args: Command-line arguments
        narration_duration: Duration of narration audio
        
    Returns:
        tuple: (top_clip, bottom_clip) with adjusted durations
    """
    if narration_duration is None:
        # Use default duration
        duration = getattr(args, 'image_duration', 5.0)
    else:
        # Use narration duration for images (only for single images, not sequences)
        duration = narration_duration
    
    # Parse media inputs
    top_files = parse_media_input(args.top_video)
    bottom_files = parse_media_input(args.bottom_video) if args.bottom_video else []
    
    # Get transition settings from args
    transition_type = getattr(args, 'transition_type', 'none')
    transition_duration = getattr(args, 'transition_duration', 0.5)
    start_transition = getattr(args, 'start_transition', 'none')
    end_transition = getattr(args, 'end_transition', 'none')
    
    # For sequences with narration, we need to handle duration differently
    if narration_duration and len(top_files) > 1:
        # For multiple files with narration, distribute narration time across all files
        duration_per_file = narration_duration / len(top_files)
        top_clip = load_media_sequence(top_files, duration_per_file, transition_type, transition_duration)
    else:
        # Single file or no narration - use normal duration
        top_clip = load_media_sequence(top_files, duration, transition_type, transition_duration)
        
        # Note: Start/end transitions will be applied to final video in create_video_short
    
    if bottom_files:
        if narration_duration and len(bottom_files) > 1:
            duration_per_file = narration_duration / len(bottom_files)
            bottom_clip = load_media_sequence(bottom_files, duration_per_file, transition_type, transition_duration)
        else:
            bottom_clip = load_media_sequence(bottom_files, duration, transition_type, transition_duration)
            
        # Note: Start/end transitions will be applied to final video in create_video_short
    else:
        bottom_clip = None
    
    return top_clip, bottom_clip

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
    Create vertical video composition from input videos and/or images.
    
    Args:
        args: Command-line arguments containing input parameters
        
    Returns:
        VideoClip: Processed video clip with combined elements
    """
    # Determine default duration for images based on narration or fallback
    default_image_duration = getattr(args, 'image_duration', 5.0)
    
    # Parse media inputs and load clips
    top_files = parse_media_input(args.top_video)
    bottom_files = parse_media_input(args.bottom_video) if args.bottom_video else []
    
    # Get transition settings
    transition_type = getattr(args, 'transition_type', 'none')
    transition_duration = getattr(args, 'transition_duration', 0.5)
    start_transition = getattr(args, 'start_transition', 'none')
    end_transition = getattr(args, 'end_transition', 'none')
    
    # Load media clips (video or image sequences)
    top_clip = load_media_sequence(top_files, default_image_duration, transition_type, transition_duration)
    bottom_clip = load_media_sequence(bottom_files, default_image_duration, transition_type, transition_duration) if bottom_files else None
    
    # Note: Start/end transitions will be applied to the final composed video later

    # Parse resolution
    target_width, target_height = map(int, args.resolution.split('x'))

    if args.bottom_video:
        # Two-media vertical composition
        half_height = target_height // 2

        # Process both clips
        processed_top = process_clip(top_clip, target_width, half_height)
        processed_bottom = process_clip(bottom_clip, target_width, half_height)

        # Determine duration - use longer clip or default for images
        top_duration = processed_top.duration
        bottom_duration = processed_bottom.duration
        
        # If both are images with same duration, use that duration
        # If one is longer, use the longer duration
        final_duration = max(top_duration, bottom_duration)
        
        # Adjust clips to match final duration
        if processed_top.duration < final_duration:
            loops_needed = math.ceil(final_duration / processed_top.duration)
            processed_top = concatenate_videoclips([processed_top]*loops_needed).subclip(0, final_duration)
            
        if processed_bottom.duration < final_duration:
            loops_needed = math.ceil(final_duration / processed_bottom.duration)
            processed_bottom = concatenate_videoclips([processed_bottom]*loops_needed).subclip(0, final_duration)

        # Combine vertically
        final_video = clips_array([[processed_top], [processed_bottom]])
        total_duration = final_duration
    else:
        # Single video processing
        processed_top = process_clip(top_clip, target_width, target_height)
        final_video = processed_top
        total_duration = processed_top.duration

    # Audio mixing
    audio_tracks = []

    # Original video audio (only if top clip has audio and contains videos, not just images)
    top_files = parse_media_input(args.top_video)
    has_video_files = any(not is_image_file(f) for f in top_files)
    if args.audio and processed_top.audio and has_video_files:
        top_audio = loop_audio(processed_top.audio, total_duration)
        audio_tracks.append(top_audio)

    # Background music
    if args.music and not args.text:
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

    # Apply start/end transitions to the final composed video
    if start_transition != 'none' or end_transition != 'none':
        final_video = apply_single_clip_transitions(final_video, start_transition, end_transition, transition_duration)

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
    if args.speed != 1.0:
        phrase_durations = [d / args.speed for d in phrase_durations]

    total_duration = sum(phrase_durations)
    
    # Normalize durations to match audio length
    if abs(total_duration - audio_clip.duration) > 1:
        ratio = audio_clip.duration / total_duration
        phrase_durations = [d * ratio for d in phrase_durations]

    # ADJUST IMAGE DURATIONS FOR NARRATION
    # If we have images, reload them with narration duration
    top_files = parse_media_input(args.top_video)
    bottom_files = parse_media_input(args.bottom_video) if args.bottom_video else []
    has_images = any(is_image_file(f) for f in top_files) or any(is_image_file(f) for f in bottom_files)
    
    if has_images:
        # Reload media clips with narration duration
        new_top_clip, new_bottom_clip = adjust_media_duration_for_narration(args, audio_clip.duration)
        
        # Parse resolution for reprocessing
        target_width, target_height = map(int, args.resolution.split('x'))
        
        if args.bottom_video:
            # Two-media composition - reprocess with narration duration
            half_height = target_height // 2
            processed_top = process_clip(new_top_clip, target_width, half_height)
            processed_bottom = process_clip(new_bottom_clip, target_width, half_height)
            video_clip = clips_array([[processed_top], [processed_bottom]])
        else:
            # Single media - reprocess with narration duration
            video_clip = process_clip(new_top_clip, target_width, target_height)

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

    # LOOP VIDEO HANDLING FOR SINGLE VIDEO CASE
    if args.bottom_video is None and not args.use_video_length:
        # Calculate required total duration from narration
        total_duration = audio_clip.duration
        
        # Check if video needs looping
        if video_clip.duration < total_duration:
            # Calculate number of loops needed
            loops_needed = math.ceil(total_duration / video_clip.duration)
            # Create looped video
            looped_video = concatenate_videoclips([video_clip] * loops_needed)
            looped_video = looped_video.subclip(0, total_duration)
            video_clip = looped_video

    # AUDIO PROCESSING WITH MUSIC HANDLING
    audio_tracks = []

    # Original video audio (if requested)
    if args.audio and video_clip.audio is not None:
        video_audio = video_clip.audio.volumex(args.video_volume / 100.0)
        audio_tracks.append(video_audio)

    # Add narration audio
    audio_tracks.append(audio_clip)

    # BACKGROUND MUSIC HANDLING (added here when narration is present)
    if args.music:
        music = AudioFileClip(args.music)
        music_looped = loop_audio(music, total_duration)
        music_looped = music_looped.volumex(args.music_volume / 100.0)
        audio_tracks.append(music_looped)

    # Ducking implementation (lower background during narration)
    if args.duck_volume is not None and len(audio_tracks) > 1:
        duck_factor = args.duck_volume / 100.0
        narration_duration = original_audio_duration
        
        if args.use_video_length:
            narration_duration = min(narration_duration, video_clip.duration)
        
        # Separate music tracks from original audio
        music_tracks = [track for track in audio_tracks if track is not audio_clip]
        original_audio = [track for track in audio_tracks if track is audio_clip]

        # Apply ducking to music tracks
        ducked_tracks = []
        for track in music_tracks:
            if track.duration > narration_duration:
                ducked = track.subclip(0, narration_duration).volumex(duck_factor)
                unducked = track.subclip(narration_duration)
                ducked_tracks.append(concatenate_audioclips([ducked, unducked]))
            else:
                ducked_tracks.append(track.volumex(duck_factor))
        
        # Rebuild audio tracks
        audio_tracks = original_audio + ducked_tracks

    # Combine audio tracks
    final_audio = CompositeAudioClip(audio_tracks)

    # Subtitle generation
    text_clips = []
    if args.subtitles and phrases:
        current_time = 0
        FONT_SIZE = 60
        MAX_TEXT_WIDTH = 1000
        
        for i, (phrase, duration) in enumerate(zip(phrases, phrase_durations)):
            try:
                # Create text clip with background box
                try:
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
                except Exception as text_error:
                    # If TextClip fails, provide helpful error message
                    if platform.system() == "Windows" and "convert" in str(text_error).lower():
                        raise Exception(
                            f"ImageMagick configuration error: {text_error}\n\n"
                            "This error typically occurs when ImageMagick is not properly configured.\n"
                            "Solutions:\n"
                            "1. Run the setup script: setup_windows.bat (as Administrator)\n"
                            "2. Install ImageMagick manually from: https://imagemagick.org/script/download.php\n"
                            "3. Ensure 'magick.exe' is in your system PATH\n"
                            "4. Restart your terminal/command prompt after installation"
                        )
                    else:
                        raise Exception(f"Text clip creation failed: {text_error}")
                        
                    # Create simple text clip without effects as fallback
                    txt_clip = TextClip(
                        phrase,
                        fontsize=FONT_SIZE,
                        color=args.text_color,
                        duration=duration
                    )

                # Add fade-in and fade-out animation if requested
                if args.animate_text:
                    txt_clip = (txt_clip
                              .fadein(args.fade_duration)  # Fade in
                              .fadeout(args.fade_duration / 2))  # Fade out
                
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

    return final_video, tts_temp_files

class ShortMakerGUI:
    """Graphical User Interface for Short Maker"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Short Maker - Video Creator")
        self.root.geometry("595x995")
        self.root.resizable(True, True)
        
        # Variables
        self.top_video_var = tk.StringVar()
        self.bottom_video_var = tk.StringVar()
        self.music_var = tk.StringVar()
        self.text_var = tk.StringVar()
        self.output_var = tk.StringVar(value="output.mp4")
        self.resolution_var = tk.StringVar(value="1080x1920")
        self.lang_var = tk.StringVar(value="en")
        self.music_volume_var = tk.DoubleVar(value=100.0)
        self.video_volume_var = tk.DoubleVar(value=0.0)
        self.speed_var = tk.DoubleVar(value=1.0)
        self.fade_duration_var = tk.DoubleVar(value=0.15)
        self.duck_volume_var = tk.DoubleVar(value=50.0)
        self.text_color_var = tk.StringVar(value="white")
        self.text_border_color_var = tk.StringVar(value="black")
        self.image_duration_var = tk.DoubleVar(value=5.0)
        self.transition_type_var = tk.StringVar(value="none")
        self.transition_duration_var = tk.DoubleVar(value=0.5)
        self.start_transition_var = tk.StringVar(value="none")
        self.end_transition_var = tk.StringVar(value="none")
        
        # Boolean variables
        self.audio_var = tk.BooleanVar(value=False)
        self.subtitles_var = tk.BooleanVar(value=True)
        self.duck_enabled_var = tk.BooleanVar(value=False)
        self.use_video_length_var = tk.BooleanVar(value=False)
        self.animate_text_var = tk.BooleanVar(value=False)
        self.bg_box_var = tk.BooleanVar(value=True)
        
        self.create_widgets()
        
    def create_widgets(self):
        """Create and arrange GUI widgets"""
        # Main container with scrollbar
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=10)
        
        # Canvas and scrollbar for scrolling
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Title
        title_label = ttk.Label(scrollable_frame, text="Short Maker - Video Creator", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Media Files Section
        video_frame = ttk.LabelFrame(scrollable_frame, text="📹 Media Files", padding=10)
        video_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Top media
        ttk.Label(video_frame, text="Main Media File(s):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.create_file_selector(video_frame, self.top_video_var, "Select main video or image file", 
                                 "Media files", "*.mp4 *.avi *.mov *.mkv *.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp", row=0, col=1, callback=self.update_image_duration_visibility)
        self.create_tooltip(video_frame, "Single file, multiple files (for image sequences), or directory path", row=0, col=3)
        
        # Bottom media
        ttk.Label(video_frame, text="Secondary Media (Optional):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.create_file_selector(video_frame, self.bottom_video_var, "Select secondary video or image file", 
                                 "Media files", "*.mp4 *.avi *.mov *.mkv *.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp", row=1, col=1, callback=self.update_image_duration_visibility)
        self.create_tooltip(video_frame, "Optional second media for split-screen layout (supports multiple files)", row=1, col=3)
        
        # Image duration (initially hidden)
        self.image_duration_label = ttk.Label(video_frame, text="Image Duration (seconds):")
        self.image_duration_scale = ttk.Scale(video_frame, from_=1.0, to=30.0, variable=self.image_duration_var, orient=tk.HORIZONTAL)
        self.image_duration_value_label = ttk.Label(video_frame, textvariable=self.image_duration_var)
        self.image_duration_tooltip = ttk.Label(video_frame, text="ℹ️", foreground="blue")
        
        # Transition controls (initially hidden)
        self.transition_label = ttk.Label(video_frame, text="Transition Type:")
        self.transition_combo = ttk.Combobox(video_frame, textvariable=self.transition_type_var,
                                           values=["none", "fade", "slide_left", "slide_right", "slide_up", "slide_down", "zoom_in", "zoom_out"],
                                           state="readonly")
        self.transition_duration_label = ttk.Label(video_frame, text="Transition Duration (seconds):")
        self.transition_duration_scale = ttk.Scale(video_frame, from_=0.1, to=2.0, variable=self.transition_duration_var, orient=tk.HORIZONTAL)
        self.transition_duration_value_label = ttk.Label(video_frame, textvariable=self.transition_duration_var)
        self.transition_tooltip = ttk.Label(video_frame, text="ℹ️", foreground="blue")
        
        # Start/End transition controls (initially hidden)
        self.start_transition_label = ttk.Label(video_frame, text="Start Transition:")
        self.start_transition_combo = ttk.Combobox(video_frame, textvariable=self.start_transition_var,
                                                 values=["none", "fade", "slide_left", "slide_right", "slide_up", "slide_down", "zoom_in", "zoom_out"],
                                                 state="readonly")
        self.end_transition_label = ttk.Label(video_frame, text="End Transition:")
        self.end_transition_combo = ttk.Combobox(video_frame, textvariable=self.end_transition_var,
                                               values=["none", "fade", "slide_left", "slide_right", "slide_up", "slide_down", "zoom_in", "zoom_out"],
                                               state="readonly")
        self.start_end_tooltip = ttk.Label(video_frame, text="ℹ️", foreground="blue")
        
        # Initially hide image duration controls
        self.image_duration_widgets = [
            self.image_duration_label,
            self.image_duration_scale, 
            self.image_duration_value_label,
            self.image_duration_tooltip
        ]
        
        # Initially hide transition controls
        self.transition_widgets = [
            self.transition_label,
            self.transition_combo,
            self.transition_duration_label,
            self.transition_duration_scale,
            self.transition_duration_value_label,
            self.transition_tooltip
        ]
        
        # Initially hide start/end transition controls
        self.start_end_transition_widgets = [
            self.start_transition_label,
            self.start_transition_combo,
            self.end_transition_label,
            self.end_transition_combo,
            self.start_end_tooltip
        ]
        
        # Audio Section
        audio_frame = ttk.LabelFrame(scrollable_frame, text="🎵 Audio Settings", padding=10)
        audio_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Background music
        ttk.Label(audio_frame, text="Background Music:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.create_file_selector(audio_frame, self.music_var, "Select background music", 
                                 "Audio files", "*.mp3 *.wav *.aac *.m4a", row=0, col=1)
        self.create_tooltip(audio_frame, "Background music to play during the video", row=0, col=3)
        
        # Audio options
        ttk.Checkbutton(audio_frame, text="Keep original video audio", 
                       variable=self.audio_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)
        self.create_tooltip(audio_frame, "Include audio from the original video files", row=1, col=3)
        
        # Volume controls
        ttk.Label(audio_frame, text="Music Volume (%):").grid(row=2, column=0, sticky=tk.W, pady=2)
        music_vol_scale = ttk.Scale(audio_frame, from_=0, to=200, variable=self.music_volume_var, orient=tk.HORIZONTAL)
        music_vol_scale.grid(row=2, column=1, sticky=tk.EW, padx=5)
        ttk.Label(audio_frame, textvariable=self.music_volume_var).grid(row=2, column=2, padx=5)
        
        ttk.Label(audio_frame, text="Video Volume (%):").grid(row=3, column=0, sticky=tk.W, pady=2)
        video_vol_scale = ttk.Scale(audio_frame, from_=0, to=200, variable=self.video_volume_var, orient=tk.HORIZONTAL)
        video_vol_scale.grid(row=3, column=1, sticky=tk.EW, padx=5)
        ttk.Label(audio_frame, textvariable=self.video_volume_var).grid(row=3, column=2, padx=5)
        
        # Audio ducking
        duck_frame = ttk.Frame(audio_frame)
        duck_frame.grid(row=4, column=0, columnspan=3, sticky=tk.EW, pady=5)
        ttk.Checkbutton(duck_frame, text="Enable audio ducking during narration", 
                       variable=self.duck_enabled_var).pack(side=tk.LEFT)
        ttk.Label(duck_frame, text="Duck Volume (%):").pack(side=tk.LEFT, padx=(10, 5))
        duck_scale = ttk.Scale(duck_frame, from_=0, to=100, variable=self.duck_volume_var, 
                              orient=tk.HORIZONTAL, length=100)
        duck_scale.pack(side=tk.LEFT, padx=5)
        ttk.Label(duck_frame, textvariable=self.duck_volume_var).pack(side=tk.LEFT, padx=5)
        
        # Narration Section
        narration_frame = ttk.LabelFrame(scrollable_frame, text="🎤 Narration & Subtitles", padding=10)
        narration_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Text file
        ttk.Label(narration_frame, text="Text File for Narration:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.create_file_selector(narration_frame, self.text_var, "Select text file", 
                                 "Text files", "*.txt", row=0, col=1)
        self.create_tooltip(narration_frame, "Text file containing the script for narration", row=0, col=3)
        
        # Language
        ttk.Label(narration_frame, text="Language:").grid(row=1, column=0, sticky=tk.W, pady=2)
        lang_combo = ttk.Combobox(narration_frame, textvariable=self.lang_var, 
                                 values=["en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "pl"])
        lang_combo.grid(row=1, column=1, sticky=tk.EW, padx=5)
        self.create_tooltip(narration_frame, "Language code for text-to-speech", row=1, col=3)
        
        # Speed
        ttk.Label(narration_frame, text="Narration Speed:").grid(row=2, column=0, sticky=tk.W, pady=2)
        speed_scale = ttk.Scale(narration_frame, from_=0.5, to=2.0, variable=self.speed_var, orient=tk.HORIZONTAL)
        speed_scale.grid(row=2, column=1, sticky=tk.EW, padx=5)
        ttk.Label(narration_frame, textvariable=self.speed_var).grid(row=2, column=2, padx=5)
        
        # Subtitle options
        ttk.Checkbutton(narration_frame, text="Enable subtitles", 
                       variable=self.subtitles_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)
        ttk.Checkbutton(narration_frame, text="Use original video length", 
                       variable=self.use_video_length_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Subtitle Styling Section
        subtitle_frame = ttk.LabelFrame(scrollable_frame, text="✨ Subtitle Styling", padding=10)
        subtitle_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Text animation
        ttk.Checkbutton(subtitle_frame, text="Animate text (fade in/out)", 
                       variable=self.animate_text_var).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        ttk.Label(subtitle_frame, text="Fade Duration (seconds):").grid(row=1, column=0, sticky=tk.W, pady=2)
        fade_scale = ttk.Scale(subtitle_frame, from_=0.0, to=1.0, variable=self.fade_duration_var, orient=tk.HORIZONTAL)
        fade_scale.grid(row=1, column=1, sticky=tk.EW, padx=5)
        ttk.Label(subtitle_frame, textvariable=self.fade_duration_var).grid(row=1, column=2, padx=5)
        
        # Text colors
        ttk.Label(subtitle_frame, text="Text Color:").grid(row=2, column=0, sticky=tk.W, pady=2)
        color_combo = ttk.Combobox(subtitle_frame, textvariable=self.text_color_var, 
                                  values=["white", "black", "red", "blue", "green", "yellow", "cyan", "magenta"])
        color_combo.grid(row=2, column=1, sticky=tk.EW, padx=5)
        
        ttk.Label(subtitle_frame, text="Border Color:").grid(row=3, column=0, sticky=tk.W, pady=2)
        border_combo = ttk.Combobox(subtitle_frame, textvariable=self.text_border_color_var, 
                                   values=["black", "white", "red", "blue", "green", "yellow", "cyan", "magenta"])
        border_combo.grid(row=3, column=1, sticky=tk.EW, padx=5)
        
        ttk.Checkbutton(subtitle_frame, text="Show background box behind text", 
                       variable=self.bg_box_var).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Output Section
        output_frame = ttk.LabelFrame(scrollable_frame, text="📤 Output Settings", padding=10)
        output_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Output file
        ttk.Label(output_frame, text="Output File:").grid(row=0, column=0, sticky=tk.W, pady=2)
        output_entry = ttk.Entry(output_frame, textvariable=self.output_var)
        output_entry.grid(row=0, column=1, sticky=tk.EW, padx=5)
        ttk.Button(output_frame, text="Browse", 
                  command=self.select_output_file).grid(row=0, column=2, padx=5)
        
        # Resolution
        ttk.Label(output_frame, text="Resolution:").grid(row=1, column=0, sticky=tk.W, pady=2)
        res_combo = ttk.Combobox(output_frame, textvariable=self.resolution_var, 
                                values=["1080x1920", "720x1280", "1920x1080", "1280x720", "640x480"])
        res_combo.grid(row=1, column=1, sticky=tk.EW, padx=5)
        self.create_tooltip(output_frame, "Video resolution (width x height)", row=1, col=3)
        
        # Progress and Control Section
        control_frame = ttk.LabelFrame(scrollable_frame, text="🎬 Create Video", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Progress bar
        self.progress_var = tk.StringVar(value="Ready to create video...")
        ttk.Label(control_frame, textvariable=self.progress_var).pack(pady=5)
        self.progress_bar = ttk.Progressbar(control_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="🎬 Create Video", 
                  command=self.create_video, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📋 Preview Settings", 
                  command=self.preview_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📤 Export Command", 
                  command=self.export_command).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 Reset", 
                  command=self.reset_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ Exit", 
                  command=self.root.quit).pack(side=tk.RIGHT, padx=5)
        
        # Configure grid weights
        for frame in [video_frame, audio_frame, narration_frame, subtitle_frame, output_frame]:
            frame.columnconfigure(1, weight=1)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Initialize image duration visibility
        self.update_image_duration_visibility()
        
    def create_file_selector(self, parent, var, title, file_type, extensions, row, col, callback=None):
        """Create a file selector with entry and browse button"""
        entry = ttk.Entry(parent, textvariable=var)
        entry.grid(row=row, column=col, sticky=tk.EW, padx=5)
        
        def browse():
            # Check if this is for media files (support multiple selection)
            if "Media files" in file_type:
                # Ask user if they want single or multiple files
                choice = messagebox.askyesnocancel(
                    "File Selection", 
                    "Do you want to select multiple files?\n\n"
                    "Yes = Multiple files (for image sequences)\n"
                    "No = Single file\n"
                    "Cancel = Cancel selection"
                )
                
                if choice is None:  # Cancel
                    return
                elif choice:  # Multiple files
                    filenames = filedialog.askopenfilenames(
                        title=title + " (Multiple)",
                        filetypes=[(file_type, extensions), ("All files", "*.*")]
                    )
                    if filenames:
                        # Join multiple files with semicolons
                        var.set(';'.join(filenames))
                        if callback:
                            callback()
                else:  # Single file
                    filename = filedialog.askopenfilename(
                        title=title,
                        filetypes=[(file_type, extensions), ("All files", "*.*")]
                    )
                    if filename:
                        var.set(filename)
                        if callback:
                            callback()
            else:
                # Non-media files - single selection only
                filename = filedialog.askopenfilename(
                    title=title,
                    filetypes=[(file_type, extensions), ("All files", "*.*")]
                )
                if filename:
                    var.set(filename)
                    if callback:
                        callback()
        
        # Also add callback to entry changes
        if callback:
            var.trace('w', lambda *args: callback())
        
        ttk.Button(parent, text="Browse", command=browse).grid(row=row, column=col+1, padx=5)
        
    def update_image_duration_visibility(self):
        """Show/hide image duration and transition controls based on selected files"""
        top_input = self.top_video_var.get()
        bottom_input = self.bottom_video_var.get()
        
        # Parse inputs to check for images and multiple files
        try:
            top_files = parse_media_input(top_input) if top_input else []
            bottom_files = parse_media_input(bottom_input) if bottom_input else []
            
            # Check if any files are images
            has_images = any(is_image_file(f) for f in top_files) or any(is_image_file(f) for f in bottom_files)
            # Check if there are multiple files (for transitions)
            has_multiple_files = len(top_files) > 1 or len(bottom_files) > 1
            # Check if there are any files (for start/end transitions)
            has_any_files = len(top_files) > 0
            
            should_show_duration = has_images
            should_show_transitions = has_multiple_files
            should_show_start_end_transitions = has_any_files
        except:
            # If parsing fails, check simple case
            should_show_duration = (top_input and is_image_file(top_input))
            should_show_transitions = False
            should_show_start_end_transitions = bool(top_input)
            top_files = []
        
        # Show/hide image duration controls
        if should_show_duration:
            self.image_duration_label.grid(row=2, column=0, sticky=tk.W, pady=2)
            self.image_duration_scale.grid(row=2, column=1, sticky=tk.EW, padx=5)
            self.image_duration_value_label.grid(row=2, column=2, padx=5)
            self.image_duration_tooltip.grid(row=2, column=3, padx=5)
            
            # Bind tooltip
            def show_duration_tooltip(event):
                tooltip = tk.Toplevel()
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                
                # Update tooltip text for multiple files
                tooltip_text = "Duration per image file. For multiple images: total duration = count × duration"
                if len(top_files) > 1:
                    tooltip_text += f"\nTop files: {len(top_files)} images × {self.image_duration_var.get():.1f}s = {len(top_files) * self.image_duration_var.get():.1f}s total"
                
                label = ttk.Label(tooltip, text=tooltip_text, 
                                 background="lightyellow", relief="solid", borderwidth=1, wraplength=250)
                label.pack()
                
                def hide_tooltip():
                    tooltip.destroy()
                
                tooltip.after(4000, hide_tooltip)
                
            self.image_duration_tooltip.bind("<Button-1>", show_duration_tooltip)
        else:
            # Hide image duration controls
            for widget in self.image_duration_widgets:
                widget.grid_remove()
        
        # Show/hide transition controls
        if should_show_transitions:
            row_offset = 3 if should_show_duration else 2
            
            self.transition_label.grid(row=row_offset, column=0, sticky=tk.W, pady=2)
            self.transition_combo.grid(row=row_offset, column=1, sticky=tk.EW, padx=5)
            self.transition_tooltip.grid(row=row_offset, column=3, padx=5)
            
            self.transition_duration_label.grid(row=row_offset+1, column=0, sticky=tk.W, pady=2)
            self.transition_duration_scale.grid(row=row_offset+1, column=1, sticky=tk.EW, padx=5)
            self.transition_duration_value_label.grid(row=row_offset+1, column=2, padx=5)
            
            # Bind transition tooltip
            def show_transition_tooltip(event):
                tooltip = tk.Toplevel()
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                
                tooltip_text = "Transition effects between multiple media files:\n"
                tooltip_text += "• none: No transition\n"
                tooltip_text += "• fade: Fade in/out\n"
                tooltip_text += "• slide_*: Slide from direction\n"
                tooltip_text += "• zoom_*: Zoom in/out effect"
                
                label = ttk.Label(tooltip, text=tooltip_text, 
                                 background="lightyellow", relief="solid", borderwidth=1, wraplength=300)
                label.pack()
                
                def hide_tooltip():
                    tooltip.destroy()
                
                tooltip.after(5000, hide_tooltip)
                
            self.transition_tooltip.bind("<Button-1>", show_transition_tooltip)
        else:
            # Hide transition controls
            for widget in self.transition_widgets:
                widget.grid_remove()
        
        # Show/hide start/end transition controls (always show when any file is selected)
        if should_show_start_end_transitions:
            row_offset = 3 if should_show_duration else 2
            if should_show_transitions:
                row_offset += 2  # Account for transition controls
            
            self.start_transition_label.grid(row=row_offset, column=0, sticky=tk.W, pady=2)
            self.start_transition_combo.grid(row=row_offset, column=1, sticky=tk.EW, padx=5)
            
            self.end_transition_label.grid(row=row_offset+1, column=0, sticky=tk.W, pady=2)
            self.end_transition_combo.grid(row=row_offset+1, column=1, sticky=tk.EW, padx=5)
            self.start_end_tooltip.grid(row=row_offset+1, column=3, padx=5)
            
            # Bind start/end transition tooltip
            def show_start_end_tooltip(event):
                tooltip = tk.Toplevel()
                tooltip.wm_overrideredirect(True)
                tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                
                tooltip_text = "Start/End transitions for the entire video:\n"
                tooltip_text += "• Start: Effect at beginning of the short\n"
                tooltip_text += "• End: Effect at end of the short\n"
                tooltip_text += "• Works with any video/image file(s)\n"
                tooltip_text += "• Complex transitions fallback to fade if they fail\n"
                tooltip_text += "• For best results, use 'fade' transitions\n"
                tooltip_text += "• May impact performance on very long videos"
                
                label = ttk.Label(tooltip, text=tooltip_text, 
                                 background="lightyellow", relief="solid", borderwidth=1, wraplength=300)
                label.pack()
                
                def hide_tooltip():
                    tooltip.destroy()
                
                tooltip.after(6000, hide_tooltip)
                
            self.start_end_tooltip.bind("<Button-1>", show_start_end_tooltip)
        else:
            # Hide start/end transition controls
            for widget in self.start_end_transition_widgets:
                widget.grid_remove()
        
    def create_tooltip(self, parent, text, row, col):
        """Create a tooltip/help icon"""
        help_label = ttk.Label(parent, text="ℹ️", foreground="blue")
        help_label.grid(row=row, column=col, padx=5)
        
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = ttk.Label(tooltip, text=text, background="lightyellow", 
                             relief="solid", borderwidth=1, wraplength=200)
            label.pack()
            
            def hide_tooltip():
                tooltip.destroy()
            
            tooltip.after(3000, hide_tooltip)  # Auto-hide after 3 seconds
            
        help_label.bind("<Button-1>", show_tooltip)
        
    def select_output_file(self):
        """Select output file location"""
        filename = filedialog.asksaveasfilename(
            title="Save video as...",
            defaultextension=".mp4",
            filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")]
        )
        if filename:
            self.output_var.set(filename)
            
    def preview_settings(self):
        """Show a preview of current settings"""
        settings = self.get_settings_dict()
        
        preview_window = tk.Toplevel(self.root)
        preview_window.title("Settings Preview")
        preview_window.geometry("500x600")
        
        text_widget = scrolledtext.ScrolledText(preview_window, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        preview_text = "Current Settings:\n\n"
        for key, value in settings.items():
            preview_text += f"{key}: {value}\n"
            
        text_widget.insert(tk.END, preview_text)
        text_widget.config(state=tk.DISABLED)
        
    def get_settings_dict(self):
        """Get current settings as dictionary"""
        return {
            "Main Media": self.top_video_var.get() or "Not selected",
            "Secondary Media": self.bottom_video_var.get() or "None",
            "Background Music": self.music_var.get() or "None",
            "Text File": self.text_var.get() or "None",
            "Output File": self.output_var.get(),
            "Resolution": self.resolution_var.get(),
            "Language": self.lang_var.get(),
            "Music Volume": f"{self.music_volume_var.get():.1f}%",
            "Video Volume": f"{self.video_volume_var.get():.1f}%",
            "Narration Speed": f"{self.speed_var.get():.1f}x",
            "Keep Original Audio": self.audio_var.get(),
            "Enable Subtitles": self.subtitles_var.get(),
            "Audio Ducking": self.duck_enabled_var.get(),
            "Duck Volume": f"{self.duck_volume_var.get():.1f}%",
            "Use Video Length": self.use_video_length_var.get(),
            "Animate Text": self.animate_text_var.get(),
            "Fade Duration": f"{self.fade_duration_var.get():.2f}s",
            "Text Color": self.text_color_var.get(),
            "Border Color": self.text_border_color_var.get(),
            "Background Box": self.bg_box_var.get(),
            "Image Duration": f"{self.image_duration_var.get():.1f}s",
            "Transition Type": self.transition_type_var.get(),
            "Transition Duration": f"{self.transition_duration_var.get():.1f}s",
            "Start Transition": self.start_transition_var.get(),
            "End Transition": self.end_transition_var.get()
        }
        
    def reset_form(self):
        """Reset all form fields to defaults"""
        if messagebox.askyesno("Reset Form", "Are you sure you want to reset all settings?"):
            self.top_video_var.set("")
            self.bottom_video_var.set("")
            self.music_var.set("")
            self.text_var.set("")
            self.output_var.set("output.mp4")
            self.resolution_var.set("1080x1920")
            self.lang_var.set("en")
            self.music_volume_var.set(100.0)
            self.video_volume_var.set(0.0)
            self.speed_var.set(1.0)
            self.fade_duration_var.set(0.15)
            self.duck_volume_var.set(50.0)
            self.text_color_var.set("white")
            self.text_border_color_var.set("black")
            self.audio_var.set(False)
            self.subtitles_var.set(True)
            self.duck_enabled_var.set(False)
            self.use_video_length_var.set(False)
            self.animate_text_var.set(False)
            self.bg_box_var.set(True)
            self.image_duration_var.set(5.0)
            self.transition_type_var.set("none")
            self.transition_duration_var.set(0.5)
            self.start_transition_var.set("none")
            self.end_transition_var.set("none")
            
    def export_command(self):
        """Export current settings as CLI command"""
        # Validate required fields
        if not self.top_video_var.get():
            messagebox.showerror("Error", "Please select a main video file first!")
            return
            
        # Validate main media files exist
        try:
            top_files = parse_media_input(self.top_video_var.get())
            if not top_files:
                messagebox.showerror("Error", "No valid main media files found!")
                return
            
            missing_files = [f for f in top_files if not os.path.exists(f)]
            if missing_files:
                messagebox.showerror("Error", f"Main media files not found:\n" + "\n".join(missing_files))
                return
        except Exception as e:
            messagebox.showerror("Error", f"Error parsing main media input: {str(e)}")
            return
            
        # Build command
        cmd_parts = ["python", "short-maker.py"]
        
        # Add main video (required)
        cmd_parts.append(f'"{self.top_video_var.get()}"')
        
        # Add secondary video if specified
        if self.bottom_video_var.get():
            cmd_parts.append(f'"{self.bottom_video_var.get()}"')
        
        # Add optional parameters
        if self.music_var.get():
            cmd_parts.extend(["-m", f'"{self.music_var.get()}"'])
            
        if self.text_var.get():
            cmd_parts.extend(["-t", f'"{self.text_var.get()}"'])
            
        if self.output_var.get() != "output.mp4":
            cmd_parts.extend(["-o", f'"{self.output_var.get()}"'])
            
        if self.resolution_var.get() != "1080x1920":
            cmd_parts.extend(["-r", self.resolution_var.get()])
            
        if self.lang_var.get() != "en":
            cmd_parts.extend(["-l", self.lang_var.get()])
            
        if self.music_volume_var.get() != 100.0:
            cmd_parts.extend(["-mv", str(self.music_volume_var.get())])
            
        if self.video_volume_var.get() != 0.0:
            cmd_parts.extend(["-vv", str(self.video_volume_var.get())])
            
        if self.speed_var.get() != 1.0:
            cmd_parts.extend(["-s", str(self.speed_var.get())])
            
        if self.fade_duration_var.get() != 0.15:
            cmd_parts.extend(["--fade-duration", str(self.fade_duration_var.get())])
            
        if self.text_color_var.get() != "white":
            cmd_parts.extend(["--text-color", self.text_color_var.get()])
            
        if self.text_border_color_var.get() != "black":
            cmd_parts.extend(["--text-border-color", self.text_border_color_var.get()])
            
        if self.image_duration_var.get() != 5.0:
            cmd_parts.extend(["--image-duration", str(self.image_duration_var.get())])
            
        if self.transition_type_var.get() != "none":
            cmd_parts.extend(["--transition-type", self.transition_type_var.get()])
            
        if self.transition_duration_var.get() != 0.5:
            cmd_parts.extend(["--transition-duration", str(self.transition_duration_var.get())])
            
        if self.start_transition_var.get() != "none":
            cmd_parts.extend(["--start-transition", self.start_transition_var.get()])
            
        if self.end_transition_var.get() != "none":
            cmd_parts.extend(["--end-transition", self.end_transition_var.get()])
        
        # Add boolean flags
        if self.audio_var.get():
            cmd_parts.append("-a")
            
        if not self.subtitles_var.get():
            cmd_parts.append("-ns")
            
        if self.duck_enabled_var.get():
            cmd_parts.extend(["--duck-volume", str(self.duck_volume_var.get())])
            
        if self.use_video_length_var.get():
            cmd_parts.append("--use-video-length")
            
        if self.animate_text_var.get():
            cmd_parts.append("--animate-text")
            
        if not self.bg_box_var.get():
            cmd_parts.append("--no-bg-box")
        
        # Join command parts
        command = " ".join(cmd_parts)
        
        # Show export window
        export_window = tk.Toplevel(self.root)
        export_window.title("Export CLI Command")
        export_window.geometry("800x500")
        export_window.resizable(True, True)
        
        # Instructions
        instructions = ttk.Label(export_window, 
                                text="Copy the command below to run Short Maker from command line:",
                                font=("Arial", 12, "bold"))
        instructions.pack(pady=10)
        
        # Command text area
        text_frame = ttk.Frame(export_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        command_text = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, height=15)
        command_text.pack(fill=tk.BOTH, expand=True)
        
        # Insert command with nice formatting
        formatted_command = self.format_command_for_display(cmd_parts)
        command_text.insert(tk.END, formatted_command)
        command_text.config(state=tk.DISABLED)
        
        # Buttons
        button_frame = ttk.Frame(export_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def copy_to_clipboard():
            self.root.clipboard_clear()
            self.root.clipboard_append(command)
            messagebox.showinfo("Copied", "Command copied to clipboard!")
            
        def save_to_file():
            filename = filedialog.asksaveasfilename(
                title="Save command to file",
                defaultextension=".bat" if os.name == 'nt' else ".sh",
                filetypes=[
                    ("Batch files", "*.bat") if os.name == 'nt' else ("Shell scripts", "*.sh"),
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ]
            )
            if filename:
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        if filename.endswith('.bat'):
                            f.write("@echo off\n")
                            f.write("REM Short Maker command generated from GUI\n")
                            f.write(command + "\n")
                            f.write("pause\n")
                        elif filename.endswith('.sh'):
                            f.write("#!/bin/bash\n")
                            f.write("# Short Maker command generated from GUI\n")
                            f.write(command + "\n")
                        else:
                            f.write(command)
                    messagebox.showinfo("Saved", f"Command saved to: {filename}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save file: {str(e)}")
        
        ttk.Button(button_frame, text="📋 Copy to Clipboard", 
                  command=copy_to_clipboard).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💾 Save to File", 
                  command=save_to_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="❌ Close", 
                  command=export_window.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Center the export window
        export_window.update_idletasks()
        x = (export_window.winfo_screenwidth() // 2) - (export_window.winfo_width() // 2)
        y = (export_window.winfo_screenheight() // 2) - (export_window.winfo_height() // 2)
        export_window.geometry(f"+{x}+{y}")
        
    def format_command_for_display(self, cmd_parts):
        """Format command for better readability"""
        if len(cmd_parts) <= 5:
            return " ".join(cmd_parts)
        
        # Multi-line format for long commands
        result = cmd_parts[0] + " " + cmd_parts[1]  # python short-maker.py
        
        # Add main video file
        if len(cmd_parts) > 2:
            result += " " + cmd_parts[2]
            
        # Add secondary video if present
        if len(cmd_parts) > 3 and not cmd_parts[3].startswith('-'):
            result += " " + cmd_parts[3]
            start_idx = 4
        else:
            start_idx = 3
        
        # Add other parameters with line breaks
        i = start_idx
        while i < len(cmd_parts):
            if cmd_parts[i].startswith('-'):
                result += " \\\n    " + cmd_parts[i]
                # Add parameter value if it exists and doesn't start with -
                if i + 1 < len(cmd_parts) and not cmd_parts[i + 1].startswith('-'):
                    result += " " + cmd_parts[i + 1]
                    i += 2
                else:
                    i += 1
            else:
                result += " " + cmd_parts[i]
                i += 1
        
        return result
            
    def create_video(self):
        """Create video with current settings"""
        # Validate required fields
        if not self.top_video_var.get():
            messagebox.showerror("Error", "Please select a main video file!")
            return
            
        # Validate main media files exist
        try:
            top_files = parse_media_input(self.top_video_var.get())
            if not top_files:
                messagebox.showerror("Error", "No valid main media files found!")
                return
            
            # Check if all files exist
            missing_files = [f for f in top_files if not os.path.exists(f)]
            if missing_files:
                messagebox.showerror("Error", f"Main media files not found:\n" + "\n".join(missing_files))
                return
        except Exception as e:
            messagebox.showerror("Error", f"Error parsing main media input: {str(e)}")
            return
            
        # Validate secondary media files if provided
        if self.bottom_video_var.get():
            try:
                bottom_files = parse_media_input(self.bottom_video_var.get())
                missing_files = [f for f in bottom_files if not os.path.exists(f)]
                if missing_files:
                    messagebox.showerror("Error", f"Secondary media files not found:\n" + "\n".join(missing_files))
                    return
            except Exception as e:
                messagebox.showerror("Error", f"Error parsing secondary media input: {str(e)}")
                return
            
        # Start processing in a separate thread to avoid freezing GUI
        import threading
        
        def process_video():
            try:
                self.progress_var.set("Processing video...")
                self.progress_bar.start()
                
                # Create arguments object similar to argparse
                args = self.create_args_object()
                
                # Create video
                video_clip = create_video_short(args)
                
                # Add narration if text file is provided
                if args.text and os.path.exists(args.text):
                    final_clip, tts_temp_files = add_narration(video_clip, args)
                else:
                    final_clip = video_clip
                    tts_temp_files = []
                
                # Export video
                self.progress_var.set("Exporting video...")
                final_clip.write_videofile(
                    args.output,
                    fps=30,
                    codec="libx264",
                    audio_codec="aac",
                    threads=4,
                    preset="fast",
                    ffmpeg_params=["-crf", "23"]
                )
                
                # Cleanup
                if video_clip:
                    video_clip.close()
                if final_clip:
                    final_clip.close()
                for temp_file in tts_temp_files:
                    if os.path.exists(temp_file):
                        try:
                            os.remove(temp_file)
                        except Exception:
                            pass
                
                self.progress_bar.stop()
                self.progress_var.set("Video created successfully!")
                messagebox.showinfo("Success", f"Video saved as: {args.output}")
                
            except Exception as e:
                self.progress_bar.stop()
                self.progress_var.set("Error occurred during processing")
                messagebox.showerror("Error", f"An error occurred: {str(e)}")
                
        thread = threading.Thread(target=process_video)
        thread.daemon = True
        thread.start()
        
    def create_args_object(self):
        """Create an arguments object from GUI settings"""
        class Args:
            pass
            
        args = Args()
        args.top_video = self.top_video_var.get()
        args.bottom_video = self.bottom_video_var.get() if self.bottom_video_var.get() else None
        args.music = self.music_var.get() if self.music_var.get() else None
        args.text = self.text_var.get() if self.text_var.get() else None
        args.output = self.output_var.get()
        args.resolution = self.resolution_var.get()
        args.lang = self.lang_var.get()
        args.music_volume = self.music_volume_var.get()
        args.video_volume = self.video_volume_var.get()
        args.speed = self.speed_var.get()
        args.fade_duration = self.fade_duration_var.get()
        args.duck_volume = self.duck_volume_var.get() if self.duck_enabled_var.get() else None
        args.text_color = self.text_color_var.get()
        args.text_border_color = self.text_border_color_var.get()
        args.audio = self.audio_var.get()
        args.subtitles = self.subtitles_var.get()
        args.use_video_length = self.use_video_length_var.get()
        args.animate_text = self.animate_text_var.get()
        args.bg_box = self.bg_box_var.get()
        args.image_duration = self.image_duration_var.get()
        args.transition_type = self.transition_type_var.get()
        args.transition_duration = self.transition_duration_var.get()
        args.start_transition = self.start_transition_var.get()
        args.end_transition = self.end_transition_var.get()
        
        return args

def launch_gui():
    """Launch the graphical user interface"""
    if not GUI_AVAILABLE:
        print("Error: GUI not available. tkinter is not installed.")
        print("Please install tkinter or use the command-line interface.")
        return
        
    root = tk.Tk()
    
    # Set up modern styling
    style = ttk.Style()
    
    # Try to use a modern theme
    available_themes = style.theme_names()
    if 'clam' in available_themes:
        style.theme_use('clam')
    elif 'alt' in available_themes:
        style.theme_use('alt')
    
    # Configure custom styles
    style.configure("Accent.TButton", foreground="white", background="#007ACC")
    
    app = ShortMakerGUI(root)
    
    # Center window on screen
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    root.mainloop()

def main():
    """Main function handling command-line interface and processing pipeline"""
    parser = argparse.ArgumentParser(
        description='Create short videos with narration and subtitles',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # GUI option
    parser.add_argument('--gui', action='store_true',
                      help='Launch graphical user interface')
    
    # Video composition arguments
    parser.add_argument('top_video', nargs='?', 
                      help='Path to top video/image file, multiple files separated by semicolons, or directory path')
    parser.add_argument('bottom_video', nargs='?', 
                      help='Path to bottom video/image file, multiple files separated by semicolons, or directory path (optional)', default=None)
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
    parser.add_argument('--image-duration', type=float, default=5.0,
                      help='Default duration for image files in seconds (ignored if narration is used)')
    parser.add_argument('--transition-type', type=str, default='none',
                      choices=['none', 'fade', 'slide_left', 'slide_right', 'slide_up', 'slide_down', 'zoom_in', 'zoom_out'],
                      help='Transition effect between multiple media files')
    parser.add_argument('--transition-duration', type=float, default=0.5,
                      help='Duration of transition effects in seconds')
    parser.add_argument('--start-transition', type=str, default='none',
                      choices=['none', 'fade', 'slide_left', 'slide_right', 'slide_up', 'slide_down', 'zoom_in', 'zoom_out'],
                      help='Transition effect at the start of video (fade recommended)')
    parser.add_argument('--end-transition', type=str, default='none',
                      choices=['none', 'fade', 'slide_left', 'slide_right', 'slide_up', 'slide_down', 'zoom_in', 'zoom_out'],
                      help='Transition effect at the end of video (fade recommended)')

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
                    help='Enable fade-in and fade-out animation for subtitles')
    parser.add_argument('--fade-duration', type=float, default=0.15,
                    help='Duration of text fade-in and fade-out (fade out is divided by 2) animation in seconds')
    parser.add_argument('--text-color', type=str, default='white',
                        help='Text color for subtitles (name or hex code)')
    parser.add_argument('--no-bg-box', action='store_false', dest='bg_box',
                        help='Disable semi-transparent background box behind text')
    parser.add_argument('--text-border-color', type=str, default='black',
                        help='Add border/shadow to text using specified color')

    args = parser.parse_args()

    # Launch GUI if requested
    if args.gui:
        launch_gui()
        return

    # Validate required arguments for CLI mode
    if not args.top_video:
        parser.error("top_video is required when not using --gui")

    # Validate resolution format
    if not re.match(r'\d+x\d+', args.resolution):
        raise ValueError("Invalid resolution format. Use WIDTHxHEIGHT (e.g., 1080x1920)")

    # Validate speed parameter
    if args.speed <= 0:
        raise ValueError("Speed factor must be greater than 0")

    # Validate fade duration
    if args.fade_duration < 0:
        raise ValueError("Fade duration must be greater than or equal to 0")

    tts_temp_files = []
    video_clip = None
    final_clip = None

    try:
        # Create video composition
        video_clip = create_video_short(args)
        
        # Add narration if requested
        if args.text:
            final_clip, tts_temp_files = add_narration(video_clip, args)
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
        for temp_file in tts_temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    print(f"Error deleting temporary file: {e}")

if __name__ == "__main__":
    """
    Example Usage:
    
    # Launch GUI (recommended for beginners)
    python short-maker.py --gui
    
    # Basic vertical composition (CLI)
    python short-maker.py top.mp4 bottom.mp4 -m music.mp3 -o output.mp4
    
    # Full narration example with text animations (CLI)
    python short-maker.py input.mp4 -t script.txt --animate-text --fade-duration 0.15 -l en -o narrated.mp4
    
    # Advanced parameters (CLI)
    python short-maker.py top.mp4 bottom.mp4 \  
        -m music.mp3 -t script.txt \  
        -o final.mp4 -r 1080x1920 \  
        -mv 20 -vv 100 --duck-volume 40 \  
        -a \
        --use-video-length

    # Custom subtitle appearance example (CLI)
    python short-maker.py input.mp4 -t script.txt \
        --animate-text \
        --fade-duration 0.15 \
        --text-color "#00FF00" \
        --text-border-color black \
        --no-bg-box \
        -o styled.mp4
    
    # IMAGE SUPPORT EXAMPLES:
    
    # Single image with narration (image duration matches narration)
    python short-maker.py image.jpg -t script.txt -m music.mp3 -o image_video.mp4
    
    # Two images split-screen with custom duration
    python short-maker.py top_image.png bottom_image.jpg --image-duration 10 -m music.mp3 -o dual_image.mp4
    
    # Mix video and image (top video, bottom image)
    python short-maker.py video.mp4 image.jpg -t script.txt -o mixed_media.mp4
    
    # Image with background music only (no narration)
    python short-maker.py photo.jpg -m background.mp3 --image-duration 15 -o slideshow.mp4
    
    # MULTIPLE IMAGES SUPPORT:
    
    # Multiple images as sequence (3 images - 5 seconds = 15 second video)
    python short-maker.py "image1.jpg;image2.jpg;image3.jpg" --image-duration 5 -m music.mp3 -o slideshow.mp4
    
    # Directory of images (automatically sorted)
    python short-maker.py /path/to/images/ --image-duration 3 -t script.txt -o gallery.mp4
    
    # Multiple images with narration (duration distributed across images)
    python short-maker.py "photo1.jpg;photo2.jpg;photo3.jpg" -t script.txt -o narrated_slideshow.mp4
    
    # TRANSITION EFFECTS EXAMPLES:
    
    # Fade transitions between images
    python short-maker.py "img1.jpg;img2.jpg;img3.jpg" --transition-type fade --transition-duration 1.0 -o fade_slideshow.mp4
    
    # Slide transitions with custom duration
    python short-maker.py "photo1.jpg;photo2.jpg" --transition-type slide_left --transition-duration 0.8 -m music.mp3 -o slide_show.mp4
    
    # Zoom effects between multiple videos
    python short-maker.py "video1.mp4;video2.mp4;video3.mp4" --transition-type zoom_in --transition-duration 0.5 -o zoom_compilation.mp4
    
    # Mixed media with transitions and narration
    python short-maker.py "intro.jpg;main_video.mp4;outro.jpg" --transition-type fade --transition-duration 0.7 -t script.txt -o complete_video.mp4
    
    # START/END TRANSITIONS EXAMPLES:
    
    # Single video with fade in and zoom out at start/end of entire short
    python short-maker.py video.mp4 --start-transition fade --end-transition zoom_out --transition-duration 1.0 -o enhanced_video.mp4
    
    # Image with slide in from left at start of the short
    python short-maker.py photo.jpg --start-transition slide_left -m music.mp3 --image-duration 10 -o slide_intro.mp4
    
    # Video with zoom in start and slide out end of entire short, plus narration
    python short-maker.py main_video.mp4 --start-transition zoom_in --end-transition slide_right -t script.txt -o dynamic_video.mp4
    
    # Multiple images with start/end effects on the entire final video
    python short-maker.py "img1.jpg;img2.jpg;img3.jpg" --start-transition zoom_in --end-transition fade --transition-type slide_left -m background.mp3 -o complete_slideshow.mp4
    
    # Two-video composition with start/end transitions on the final result
    python short-maker.py top.mp4 bottom.mp4 --start-transition fade --end-transition zoom_out -t script.txt -o composed_video.mp4
    """
    main()
