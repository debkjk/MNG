# services/video_generator_slideshow.py

import subprocess
import os
import glob
import logging
from pathlib import Path
from pydub import AudioSegment
from typing import Dict, Any

# Configure paths
STATIC_DIR = Path(__file__).resolve().parent.parent / 'static'
OUTPUT_DIR = STATIC_DIR / 'videos'
PANEL_DIR = STATIC_DIR / 'panels'
AUDIO_DIR = STATIC_DIR / 'audio'

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def generate_dubbed_video(job_id: str, page_images: list = None) -> str:
    """
    Generates the final video by stitching manga page images and merging the final audio track.
    Requires FFmpeg and pydub to be installed.
    
    Args:
        job_id: Unique job identifier
        page_images: Optional list of page image paths. If None, will search for panels.
    
    Returns:
        Path to the generated video file
    """
    
    logging.info(f"\n🎬 Step 5/5: Generating final video...")
    
    # 1. Define paths
    audio_file = AUDIO_DIR / job_id / "merged_audio.mp3"
    output_video = OUTPUT_DIR / job_id / "final_video.mp4"
    temp_list_file = OUTPUT_DIR / job_id / "concat_list.txt"
    slideshow_video = OUTPUT_DIR / job_id / "slideshow.mp4"
    
    # Create output directory
    (OUTPUT_DIR / job_id).mkdir(parents=True, exist_ok=True)
    
    # Clean up previous runs
    for f in [output_video, slideshow_video, temp_list_file]:
        if Path(f).exists():
            os.remove(f)

    if not audio_file.exists():
        error_msg = f"❌ Error: Final audio file not found at {audio_file}. Run the TTS service first."
        logging.error(error_msg)
        raise FileNotFoundError(error_msg)

    # 2. Get Audio Duration
    try:
        audio = AudioSegment.from_file(str(audio_file))
        audio_duration_s = audio.duration_seconds
        logging.info(f"   🎵 Audio duration: {audio_duration_s:.2f} seconds")
    except Exception as e:
        error_msg = f"❌ Error reading audio file with pydub: {e}"
        logging.error(error_msg)
        raise

    # 3. Find and sort all page/panel images
    if page_images is None:
        # Try to find page images first, then panel images
        page_pattern = str(STATIC_DIR / 'pages' / job_id / '*.png')
        panel_pattern = str(PANEL_DIR / job_id / '*.png')
        
        image_files = sorted(glob.glob(page_pattern))
        if not image_files:
            image_files = sorted(glob.glob(panel_pattern))
        
        if not image_files:
            error_msg = f"❌ Error: No images found in {STATIC_DIR / 'pages' / job_id} or {PANEL_DIR / job_id}"
            logging.error(error_msg)
            raise FileNotFoundError(error_msg)
    else:
        image_files = page_images
    
    num_images = len(image_files)
    logging.info(f"   📸 Found {num_images} images to process")
    
    # 4. Calculate Duration per Image
    # Each image gets an equal slice of the total audio duration.
    single_image_duration = audio_duration_s / num_images
    logging.info(f"   ⏱️  Each image will display for {single_image_duration:.2f} seconds")

    # 5. Create a temporary FFmpeg concat demuxer file
    logging.info(f"   📝 Creating FFmpeg concat file...")
    with open(temp_list_file, "w") as f:
        for image_path in image_files:
            # Use absolute path for FFmpeg
            abs_path = os.path.abspath(image_path)
            # Escape single quotes in path for FFmpeg
            escaped_path = abs_path.replace("'", "'\\''")
            f.write(f"file '{escaped_path}'\n")
            f.write(f"duration {single_image_duration}\n")
        # Add the last one again to ensure total video duration exactly matches
        last_path = os.path.abspath(image_files[-1])
        escaped_last = last_path.replace("'", "'\\''")
        f.write(f"file '{escaped_last}'\n")
        
    # 6. Command to create the video slideshow
    logging.info(f"\n   🎬 Step 1/2: Generating video slideshow from images...")
    slideshow_cmd = [
        "ffmpeg", 
        "-f", "concat",
        "-safe", "0", 
        "-i", str(temp_list_file), 
        "-vf", f"scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", 
        "-pix_fmt", "yuv420p", 
        "-r", "25",  # Framerate
        "-y",  # Overwrite output file
        str(slideshow_video)
    ]
    
    try:
        result = subprocess.run(
            slideshow_cmd, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        logging.info(f"   ✅ Slideshow created successfully")
    except subprocess.CalledProcessError as e:
        error_msg = f"❌ FFmpeg Slideshow Error (Code {e.returncode}):\n{e.stderr}"
        logging.error(error_msg)
        if temp_list_file.exists():
            os.remove(temp_list_file)
        raise RuntimeError(error_msg)
    
    # 7. Merge the slideshow video and the audio
    logging.info(f"\n   🎬 Step 2/2: Merging video and audio tracks...")
    merge_cmd = [
        "ffmpeg", 
        "-i", str(slideshow_video), 
        "-i", str(audio_file), 
        "-c:v", "copy",        
        "-c:a", "aac",         # Encode audio to aac
        "-b:a", "192k",        # Audio bitrate
        "-map", "0:v:0",       # Map video stream 
        "-map", "1:a:0",       # Map audio stream 
        "-shortest",           # End when shortest stream ends
        "-y",                  
        str(output_video)
    ]
    
    try:
        result = subprocess.run(
            merge_cmd, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        logging.info(f"\n✅ Video generation completed!")
        logging.info(f"   🎥 Final video: {output_video}")
        logging.info(f"   📊 Duration: {audio_duration_s:.2f}s, Images: {num_images}")
    except subprocess.CalledProcessError as e:
        error_msg = f"❌ FFmpeg Merge Error (Code {e.returncode}):\n{e.stderr}"
        logging.error(error_msg)
        raise RuntimeError(error_msg)
    finally:
        # Cleanup temporary files
        if temp_list_file.exists():
            os.remove(temp_list_file)
        if slideshow_video.exists():
            os.remove(slideshow_video)
    
    return str(output_video)


def generate_dubbed_video_from_analysis(analysis_results: Dict[str, Any], job_id: str) -> str:
    """
    Generate video from analysis results dictionary.
    
    Args:
        analysis_results: Dictionary containing pages with image paths
        job_id: Unique job identifier
    
    Returns:
        Path to the generated video file
    """
    # SIMPLIFIED: Let generate_dubbed_video() auto-discover images
    # It will search in static/pages/job_id/ for page_*.png files
    # This is where the PDF processor saves them
    
    return generate_dubbed_video(job_id, page_images=None)
