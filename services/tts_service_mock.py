"""
TEMPORARY Mock TTS Service - For Testing Without ElevenLabs
This creates silent audio files so you can test the rest of the pipeline.
"""
import logging
from pathlib import Path
from typing import Dict, Any, List
import subprocess
import json

def generate_dialogue_audio_mock(dialogue: Dict[str, Any], output_path: Path) -> bool:
    """Generate a mock (silent) audio file for testing."""
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Get dialogue text for duration calculation
        text = dialogue.get("text", "")
        # Estimate duration: ~150 words per minute, ~5 characters per word
        estimated_duration = max(1.0, len(text) / (150 * 5 / 60))
        
        # Create silent audio using FFmpeg
        # This requires FFmpeg to be installed
        cmd = [
            'ffmpeg',
            '-f', 'lavfi',
            '-i', f'anullsrc=r=44100:cl=stereo',
            '-t', str(estimated_duration),
            '-q:a', '9',
            '-acodec', 'libmp3lame',
            '-y',  # Overwrite
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info(f"✅ MOCK: Generated {estimated_duration:.1f}s silent audio for: {text[:50]}...")
            return True
        else:
            logging.error(f"FFmpeg failed: {result.stderr}")
            # Fallback: create empty file
            output_path.touch()
            logging.warning(f"⚠️ MOCK: Created empty audio file for: {text[:50]}...")
            return True
            
    except Exception as e:
        logging.error(f"Failed to create mock audio: {e}")
        # Last resort: create empty file
        try:
            output_path.touch()
            return True
        except:
            return False

def generate_audio_tracks_mock(analysis_results: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """Generate mock audio tracks for all dialogues."""
    from services.tts_service import AUDIO_DIR
    
    job_audio_dir = AUDIO_DIR / job_id
    job_audio_dir.mkdir(parents=True, exist_ok=True)
    
    successful_dialogues = 0
    total_dialogues = 0
    
    logging.info(f"🧪 MOCK TTS: Generating silent audio for job {job_id}")
    
    # Process each page
    for page in analysis_results.get("pages", []):
        for panel in page.get("panels", []):
            for dialogue in panel.get("dialogues", []):
                total_dialogues += 1
                
                # Generate unique filename
                panel_id = panel.get("panel_number", 0)
                dialogue_id = dialogue.get("sequence", total_dialogues)
                audio_filename = f"dialogue_p{page.get('page_number', 0):03d}_r{panel_id:02d}_d{dialogue_id:02d}.mp3"
                audio_path = job_audio_dir / audio_filename
                
                # Generate mock audio
                if generate_dialogue_audio_mock(dialogue, audio_path):
                    dialogue["audio_path"] = str(audio_path)
                    successful_dialogues += 1
    
    if successful_dialogues == 0:
        raise Exception("No audio files were successfully generated")
    
    logging.info(f"✅ MOCK TTS: Generated {successful_dialogues}/{total_dialogues} silent audio files")
    
    # Create mock merged audio
    merged_audio_path = job_audio_dir / "merged_audio.mp3"
    merged_audio_path.touch()
    
    return {
        "successful_dialogues": successful_dialogues,
        "total_dialogues": total_dialogues,
        "merged_audio_path": str(merged_audio_path),
        "analysis_results": analysis_results
    }
