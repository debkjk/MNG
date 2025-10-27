import logging
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Any, Optional
import json
import moviepy
from moviepy.video.VideoClip import ColorClip, ImageClip, VideoClip, TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import CompositeAudioClip

# Configure paths and directories
VIDEOS_DIR = Path(__file__).resolve().parent.parent / 'static' / 'videos'
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

# Video output constants
VIDEO_WIDTH = 1920  # Full HD width
VIDEO_HEIGHT = 1080  # Full HD height
VIDEO_FPS = 30  # Standard frame rate
VIDEO_CODEC = 'libx264'  # H.264 encoding for broad compatibility

def create_manga_video(analysis_results: Dict[str, Any], job_id: str) -> str:
    """
    Create a video from manga panels and audio files.
    
    Args:
        analysis_results: Dictionary containing panel and audio information
        job_id: Unique identifier for the job
    
    Returns:
        str: Path to the generated video file
    """
    try:
        # Create job-specific video directory
        job_video_dir = VIDEOS_DIR / job_id
        job_video_dir.mkdir(parents=True, exist_ok=True)
        
        clips = []
        current_time = 0
        
        # Process each page
        for page in analysis_results.get("pages", []):
            panels = page.get("panels", [])
            
            # Sort panels by reading order
            sorted_panels = sorted(panels, key=lambda p: p.get("reading_order", 0))
            
            for panel in sorted_panels:
                panel_path = panel.get("panel_path")
                if not panel_path or not Path(panel_path).exists():
                    logging.warning(f"Panel image not found: {panel_path}")
                    continue
                
                # Get dialogues for this panel
                dialogues = panel.get("dialogues", [])
                if not dialogues:
                    logging.info(f"Skipping panel without dialogues: {panel_path}")
                    continue
                
                # Collect audio clips for this panel and calculate duration
                panel_audio_clips = []
                panel_duration = 0
                
                for dialogue in dialogues:
                    audio_path = dialogue.get("audio_path")
                    if audio_path and Path(audio_path).exists():
                        try:
                            audio_clip = AudioFileClip(str(audio_path))
                            panel_audio_clips.append(audio_clip)
                            panel_duration += audio_clip.duration
                        except Exception as e:
                            logging.warning(f"Failed to load audio {audio_path}: {e}")
                            panel_duration += 2.0  # Default duration
                    else:
                        logging.warning(f"Audio file not found for dialogue: {audio_path}")
                        panel_duration += 2.0  # Default duration
                
                # Skip panel if no valid duration
                if panel_duration <= 0:
                    logging.warning(f"Skipping panel with zero duration: {panel_path}")
                    continue
                
                # Create image clip for this panel
                try:
                    image_clip: Optional[ImageClip] = ImageClip(str(panel_path))
                    if image_clip is not None:
                        image_clip = image_clip.with_duration(panel_duration)  # type: ignore
                        image_clip = image_clip.resize(width=VIDEO_WIDTH)  # type: ignore
                        image_clip = image_clip.with_position('center')  # type: ignore
                        image_clip = image_clip.with_start(current_time)  # type: ignore
                        
                        # Concatenate audio clips sequentially (not overlapping)
                        if panel_audio_clips:
                            from moviepy.audio.AudioClip import concatenate_audioclips
                            concatenated_audio = concatenate_audioclips(panel_audio_clips)
                            concatenated_audio = concatenated_audio.with_start(current_time)  # type: ignore
                            image_clip = image_clip.with_audio(concatenated_audio)  # type: ignore
                        
                        clips.append(image_clip)
                        
                        # Create subtitles for each dialogue in this panel
                        dialogue_start = current_time
                        for dialogue in dialogues:
                            audio_path = dialogue.get("audio_path")
                            if audio_path and Path(audio_path).exists():
                                try:
                                    audio_clip = AudioFileClip(str(audio_path))
                                    dialogue_duration = audio_clip.duration
                                    audio_clip.close()
                                    
                                    # Create subtitle for this dialogue
                                    subtitle_text = dialogue.get("text", "")
                                    if subtitle_text:
                                        subtitle_clip = create_subtitle_clip(
                                            subtitle_text,
                                            dialogue_duration,
                                            dialogue_start
                                        )
                                        if subtitle_clip:
                                            clips.append(subtitle_clip)
                                    
                                    dialogue_start += dialogue_duration
                                except Exception as e:
                                    logging.warning(f"Failed to create subtitle for dialogue: {e}")
                        
                        current_time += panel_duration
                    else:
                        logging.warning(f"Failed to create ImageClip for {panel_path}")
                        continue
                    
                except Exception as e:
                    logging.error(f"Failed to create clip for panel {panel_path}: {e}")
                    continue
        
        if not clips:
            raise ValueError("No valid clips to create video")
        
        # Create the final composite video
        final_video = CompositeVideoClip(clips, size=(VIDEO_WIDTH, VIDEO_HEIGHT))
        
        # Generate output path
        output_path = job_video_dir / "final_video.mp4"
        
        # Write the video file
        final_video.write_videofile(
            str(output_path),
            fps=VIDEO_FPS,
            codec=VIDEO_CODEC,
            audio_codec=AUDIO_CODEC,
            audio_bitrate=AUDIO_BITRATE
        )
        
        # Clean up clips
        for clip in clips:
            if hasattr(clip, 'audio') and clip.audio is not None:
                clip.audio.close()
            clip.close()
        final_video.close()
        
        logging.info(f"Successfully created video: {output_path}")
        return str(output_path)
        
    except Exception as e:
        logging.error(f"Error creating video: {str(e)}")
        raise e

# Additional constants
AUDIO_CODEC = 'aac'  # AAC audio codec
AUDIO_BITRATE = '192k'  # High quality audio
PIXEL_FORMAT = 'yuv420p'  # Standard pixel format for compatibility

# Subtitle settings
SUBTITLE_FONT_SIZE = 32
SUBTITLE_COLOR = 'white'
SUBTITLE_BG_COLOR = 'black'
SUBTITLE_POSITION = ('center', 'bottom')
SUBTITLE_MARGIN = 50  # pixels from bottom

# Panel highlighting settings
HIGHLIGHT_COLOR = (255, 255, 0, 80)  # Yellow with transparency
HIGHLIGHT_BORDER_WIDTH = 5

def create_subtitle_clip(text: str, duration: float, start_time: float) -> Optional[TextClip]:
    """Create a subtitle text clip with background."""
    try:
        subtitle = TextClip(
            text,
            fontsize=SUBTITLE_FONT_SIZE,
            color=SUBTITLE_COLOR,
            bg_color=SUBTITLE_BG_COLOR,
            size=(VIDEO_WIDTH - 100, None),  # Leave margins
            method='caption',
            align='center'
        )
        subtitle = subtitle.with_duration(duration)  # type: ignore
        subtitle = subtitle.with_start(start_time)  # type: ignore
        subtitle = subtitle.with_position(('center', VIDEO_HEIGHT - SUBTITLE_MARGIN))  # type: ignore
        return subtitle
    except Exception as e:
        logging.warning(f"Failed to create subtitle: {e}")
        return None

def create_panel_highlight(panel_image: Image.Image, bounding_box: Dict[str, int]) -> Image.Image:
    """Add a highlight border to the active panel area."""
    try:
        # Create a copy with RGBA mode
        highlighted = panel_image.convert('RGBA')
        overlay = Image.new('RGBA', highlighted.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Draw semi-transparent rectangle over the panel
        x, y = bounding_box.get('x', 0), bounding_box.get('y', 0)
        w, h = bounding_box.get('width', highlighted.width), bounding_box.get('height', highlighted.height)
        
        # Draw border
        for i in range(HIGHLIGHT_BORDER_WIDTH):
            draw.rectangle(
                [x + i, y + i, x + w - i, y + h - i],
                outline=HIGHLIGHT_COLOR,
                width=1
            )
        
        # Composite the overlay
        return Image.alpha_composite(highlighted, overlay)
    except Exception as e:
        logging.warning(f"Failed to create panel highlight: {e}")
        return panel_image