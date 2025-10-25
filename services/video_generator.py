import ffmpeg
from pathlib import Path
import logging
import os
import shutil
from typing import List, Dict, Any
from services.pdf_processor import cleanup_page_images
from services.tts_service import cleanup_audio_files

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

def get_audio_duration(audio_path: Path) -> float:
    """Get duration of audio file in seconds using ffmpeg probe."""
    try:
        probe = ffmpeg.probe(str(audio_path))
        duration = float(probe['format']['duration'])
        logging.info(f"Detected audio duration: {duration:.2f} seconds")
        return duration
    except Exception as e:
        logging.error(f"Failed to probe audio file {audio_path}: {str(e)}")
        raise

def collect_panel_paths(analysis_results: Dict[str, Any]) -> List[Path]:
    """Extract and validate panel paths in reading order."""
    panel_paths = []
    
    for page in analysis_results["pages"]:
        for panel in sorted(page["panels"], key=lambda p: p["reading_order"]):
            panel_path = Path(panel["panel_path"])
            if panel_path.exists():
                panel_paths.append(panel_path)
            else:
                logging.warning(f"Panel image not found: {panel_path}")
    
    if not panel_paths:
        raise ValueError("No valid panel images found in analysis results")
    
    logging.info(f"Collected {len(panel_paths)} panel paths in reading order")
    return panel_paths

def generate_video(panel_paths: List[Path], audio_path: Path, output_path: Path) -> bool:
    """Generate video from panel images synchronized with audio."""
    try:
        # Validate inputs
        if not panel_paths:
            raise ValueError("No panel paths provided")
        if not audio_path.exists():
            raise ValueError(f"Audio file not found: {audio_path}")
        
        # Get audio duration and calculate timing
        audio_duration = get_audio_duration(audio_path.resolve().as_posix())
        per_panel_duration = round(audio_duration / len(panel_paths), 3)
        per_panel_duration = max(per_panel_duration, 0.05)  # Ensure minimum duration

        # Create video segments for each panel
        video_segments = []
        for i, panel_path in enumerate(panel_paths):
            panel_posix = panel_path.resolve().as_posix()
            # For last panel, absorb any rounding residue
            if i == len(panel_paths) - 1:
                segment_duration = max(per_panel_duration, 
                                    audio_duration - per_panel_duration * (len(panel_paths) - 1))
            else:
                segment_duration = per_panel_duration
            # Create input stream with scaling and padding
            segment = (
                ffmpeg
                .input(panel_posix, loop=1, t=segment_duration)
                .filter('scale', VIDEO_WIDTH, VIDEO_HEIGHT, force_original_aspect_ratio='decrease')
                .filter('pad', VIDEO_WIDTH, VIDEO_HEIGHT, '(ow-iw)/2', '(oh-ih)/2', color='black')
            )
            video_segments.append(segment)

        # Concatenate video segments and add audio
        concat_node = ffmpeg.concat(*video_segments, v=1, a=0, n=len(video_segments)).node
        video = concat_node[0]
        audio = ffmpeg.input(audio_path.resolve().as_posix()).audio

        # Generate final video with audio
        (
            ffmpeg
            .output(
                video,
                audio,
                output_path.resolve().as_posix(),
                vcodec=VIDEO_CODEC,
                pix_fmt=PIXEL_FORMAT,
                r=VIDEO_FPS,
                acodec=AUDIO_CODEC,
                shortest=None,  # Stop when audio ends
                movflags='+faststart',  # Enable streaming
                **{'b:a': AUDIO_BITRATE}
            )
            .overwrite_output()
            .run(quiet=False)
        )
        
        logging.info(f"Successfully generated video: {output_path}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to generate video: {str(e)}")
        return False

def cleanup_temporary_files(job_id: str, keep_merged_audio: bool = True) -> None:
    """Clean up temporary files after successful video generation."""
    try:
        cleanup_page_images(job_id)
        cleanup_audio_files(job_id, keep_merged=keep_merged_audio)
        logging.info(f"Cleaned up temporary files for job {job_id}")
    except Exception as e:
        logging.error(f"Error during cleanup for job {job_id}: {str(e)}")

def create_manga_video(analysis_results: Dict[str, Any], job_id: str) -> str:
    """Create video from manga panels with synchronized audio."""
    try:
        # Prepare output directory
        job_videos_dir = VIDEOS_DIR / job_id
        job_videos_dir.mkdir(parents=True, exist_ok=True)
        video_path = job_videos_dir / 'final_video.mp4'
        
        logging.info(f"Starting video generation for job {job_id}")
        
        # Collect resources
        panel_paths = collect_panel_paths(analysis_results)
        merged_audio_path = Path(analysis_results['merged_audio_path'])
        if not merged_audio_path.exists():
            raise ValueError(f"Merged audio file not found: {merged_audio_path}")
        
        # Generate video
        if not generate_video(panel_paths, merged_audio_path, video_path):
            raise RuntimeError("Video generation failed")
        
        # Clean up temporary files
        cleanup_temporary_files(job_id, keep_merged_audio=True)
        
        # Return relative path for database storage
        relative_path = f'static/videos/{job_id}/final_video.mp4'
        logging.info(f"Video generation completed. Path: {relative_path}")
        return relative_path
        
    except Exception as e:
        error_msg = f"Failed to create video for job {job_id}: {str(e)}"
        logging.error(error_msg)
        raise RuntimeError(error_msg)