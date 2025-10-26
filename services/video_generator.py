import logging
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw
from typing import List, Dict, Any
import json
import moviepy
from moviepy.video.VideoClip import ColorClip, ImageClip, VideoClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.audio.io.AudioFileClip import AudioFileClip

# Configure paths and directories
VIDEOS_DIR = Path(__file__).resolve().parent.parent / 'static' / 'videos'
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

# Video output constants
VIDEO_WIDTH = 1920  # Full HD width
VIDEO_HEIGHT = 1080  # Full HD height
VIDEO_FPS = 30  # Standard frame rate
VIDEO_CODEC = 'libx264'  # H.264 encoding for broad compatibility
AUDIO_CODEC = 'aac'  # AAC audio codec
AUDIO_BITRATE = '192k'  # High quality audio
PIXEL_FORMAT = 'yuv420p'  # Standard pixel format for compatibility

# Dialog visual settings
HIGHLIGHT_OPACITY = 0.3  # Opacity of dialog highlight
HIGHLIGHT_COLOR = (255, 255, 0)  # Yellow highlight
DIALOG_PADDING = 0.2  # Seconds of padding between dialogs

def get_audio_duration(audio_path: Path) -> float:
    """Get duration of audio file in seconds."""
    try:
        with AudioFileClip(str(audio_path)) as audio:
            return audio.duration
    except Exception as e:
        logging.error(f"Failed to get audio duration for {audio_path}: {str(e)}")
        raise

def create_dialog_highlight(image: Image, dialog_position: Dict[str, str], opacity: float = HIGHLIGHT_OPACITY) -> Image:
    """Create a semi-transparent highlight for the current dialog."""
    highlight = Image.new('RGBA', image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(highlight)
    
    # Calculate highlight position based on dialog position
    w, h = image.size
    if dialog_position['vertical'] == 'top':
        y1, y2 = 0, h//3
    elif dialog_position['vertical'] == 'middle':
        y1, y2 = h//3, 2*h//3
    else:  # bottom
        y1, y2 = 2*h//3, h
        
    if dialog_position['horizontal'] == 'left':
        x1, x2 = 0, w//3
    elif dialog_position['horizontal'] == 'center':
        x1, x2 = w//3, 2*w//3
    else:  # right
        x1, x2 = 2*w//3, w
        
    # Draw highlight rectangle
    color = (*HIGHLIGHT_COLOR, int(255 * opacity))
    draw.rectangle([x1, y1, x2, y2], fill=color)
    
    return Image.alpha_composite(image.convert('RGBA'), highlight)

def create_video_for_page(
    page_image_path: Path,
    dialogs: List[Dict[str, Any]],
    audio_dir: Path,
    output_path: Path
) -> None:
    """
    Create a video from a manga page with timed dialog highlights and audio.
    
    Args:
        page_image_path: Path to the manga page image
        dialogs: List of dialog entries with timing and position info
        audio_dir: Directory containing generated audio files
        output_path: Path where the output video will be saved
    """
    try:
        # Load the page image
        page_image = Image.open(page_image_path)
        
        # Resize image to maintain aspect ratio within VIDEO_WIDTH/HEIGHT
        aspect_ratio = page_image.width / page_image.height
        if aspect_ratio > VIDEO_WIDTH / VIDEO_HEIGHT:
            new_width = VIDEO_WIDTH
            new_height = int(VIDEO_WIDTH / aspect_ratio)
        else:
            new_height = VIDEO_HEIGHT
            new_width = int(VIDEO_HEIGHT * aspect_ratio)
            
        page_image = page_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Background is already created above
        
        # Calculate image position to center it
        x_offset = (VIDEO_WIDTH - new_width) // 2
        y_offset = (VIDEO_HEIGHT - new_height) // 2
        
        # Create base clip with the page image
        base_image = np.array(page_image)
        current_time = 0
        
        # Calculate total duration from all dialogs
        total_duration = sum([get_audio_duration(audio_dir / f"dialog_{d['sequence']:03d}.mp3") + DIALOG_PADDING for d in dialogs])
        
        # Create base clip with the page image
        base_clip = ImageClip(base_image).with_position((x_offset, y_offset)).with_duration(total_duration)
        background = ColorClip((VIDEO_WIDTH, VIDEO_HEIGHT), color=(0, 0, 0)).with_duration(total_duration)
        
        # Process each dialog
        clips = [background, base_clip]
        
        for dialog in dialogs:
            # Get audio file for this dialog
            audio_path = audio_dir / f"dialog_{dialog['sequence']:03d}.mp3"
            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            # Get audio duration
            duration = get_audio_duration(audio_path)
            
            # Create highlighted image for this dialog
            highlighted_image = create_dialog_highlight(page_image, dialog['position'])
            highlighted_array = np.array(highlighted_image)
            
            # Create clip for this dialog
            dialog_clip = (ImageClip(highlighted_array)
                         .with_start(current_time)
                         .with_duration(duration)
                         .with_position((x_offset, y_offset)))
            
            # Add audio
            audio = AudioFileClip(str(audio_path)).with_start(current_time)
            dialog_clip = dialog_clip.with_audio(audio)
            
            clips.append(dialog_clip)
            current_time += duration + DIALOG_PADDING
        
        # Background is already added to clips with correct duration
        
        # Combine all clips
        final_clip = CompositeVideoClip(clips)
        
        # Write the final video
        final_clip.write_videofile(
            str(output_path),
            fps=VIDEO_FPS,
            codec=VIDEO_CODEC,
            audio_codec=AUDIO_CODEC,
            audio_bitrate=AUDIO_BITRATE,
            logger=None  # Disable moviepy's verbose logging
        )
        
        logging.info(f"Successfully created video: {output_path}")
        
    except Exception as e:
        logging.error(f"Failed to create video: {str(e)}")
        raise
    finally:
        # Clean up moviepy clips
        try:
            for clip in clips:
                # If the clip has audio, close it first
                if hasattr(clip, 'audio') and clip.audio is not None:
                    clip.audio.close()
                clip.close()
        except Exception as e:
            logging.error(f"Error during cleanup: {str(e)}")

def generate_manga_video(
    page_image_path: Path,
    dialogs_json_path: Path,
    audio_dir: Path,
    output_dir: Path = VIDEOS_DIR
) -> Path:
    """
    Generate a video from a manga page with synchronized audio and visual dialog indicators.
    
    Args:
        page_image_path: Path to the manga page image
        dialogs_json_path: Path to the JSON file containing dialog data
        audio_dir: Directory containing the generated audio files
        output_dir: Directory where the output video will be saved
    
    Returns:
        Path to the generated video file
    """
    try:
        # Load dialog data
        with open(dialogs_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create output filename based on page number or image name
        output_filename = f"manga_page_{Path(page_image_path).stem}.mp4"
        output_path = output_dir / output_filename
        
        # Generate the video
        create_video_for_page(
            page_image_path=page_image_path,
            dialogs=data['dialogs'],
            audio_dir=audio_dir,
            output_path=output_path
        )
        
        return output_path
        
    except Exception as e:
        logging.error(f"Failed to generate manga video: {str(e)}")
        raise

# End of video generation functions