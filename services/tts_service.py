from elevenlabs.client import ElevenLabs
import ffmpeg
from pathlib import Path
import logging
import os
import time
import tempfile
from typing import List, Dict, Any
import functools

# Configure paths and directories
AUDIO_DIR = Path(__file__).resolve().parent.parent / 'static' / 'audio'
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Constants
DEFAULT_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")  # Sarah voice
MODEL_ID = "eleven_multilingual_v2"

def map_emotion_to_text_prefix(emotion: str, speaker: str) -> str:
    """Map emotion labels to bracketed emotion markers."""
    emotion_map = {
        "happy": "[happily] ",
        "sad": "[sadly] ",
        "angry": "[angrily] ",
        "surprised": "[surprised] ",
        "excited": "[excitedly] ",
        "scared": "[fearfully] ",
        "neutral": ""  # No marker for neutral emotion
    }
    
    return emotion_map.get(emotion.lower(), "")

def initialize_elevenlabs():
    """Initialize and validate ElevenLabs API."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        raise ValueError("ELEVENLABS_API_KEY environment variable is not set")
    
    try:
        return ElevenLabs(api_key=api_key)
    except Exception as e:
        logging.error(f"Failed to initialize ElevenLabs: {str(e)}")
        raise

def get_voice_settings(emotion_data: Dict[str, Any], character: str) -> dict:
    """
    Get emotion and character-tuned voice settings.
    
    Args:
        emotion_data: Dictionary containing emotion parameters
        character: The character speaking (e.g., 'Naruto', 'Sasuke', 'Narrator')
    """
    # Base settings from emotion type
    emotion_type = emotion_data.get('type', 'neutral').lower()
    base_settings = {
        "happy": {"stability": 0.4, "style": 0.3, "speed": 1.1},
        "excited": {"stability": 0.4, "style": 0.3, "speed": 1.1},
        "sad": {"stability": 0.6, "style": 0.2, "speed": 0.9},
        "scared": {"stability": 0.6, "style": 0.2, "speed": 0.9},
        "angry": {"stability": 0.3, "style": 0.4, "speed": 1.0},
        "neutral": {"stability": 0.5, "style": 0.0, "speed": 1.0},
        "surprised": {"stability": 0.5, "style": 0.0, "speed": 1.0}
    }.get(emotion_type, {"stability": 0.5, "style": 0.0, "speed": 1.0})
    
    # Character-specific modifiers
    character_mods = {
        "Naruto": {
            "stability_mod": -0.1,  # More variation
            "style_mod": 0.2,      # Stronger emotion
            "speed_mod": 0.1       # Slightly faster
        },
        "Sasuke": {
            "stability_mod": 0.1,   # More stable
            "style_mod": -0.1,     # Subtle emotion
            "speed_mod": -0.05     # Slightly slower
        },
        "Narrator": {
            "stability_mod": 0.2,   # Very stable
            "style_mod": -0.2,     # Minimal emotion
            "speed_mod": 0         # Standard speed
        }
    }.get(character, {"stability_mod": 0, "style_mod": 0, "speed_mod": 0})
    
    # Apply emotion intensity and stability from the data
    intensity = emotion_data.get('intensity', 0.5)
    stability = emotion_data.get('stability', 0.8)
    style_value = emotion_data.get('style', 0.3)
    
    # Calculate final values with character modifications
    final_stability = min(0.9, max(0.1, 
        base_settings['stability'] * stability + character_mods['stability_mod']))
    final_style = min(1.0, max(0.0, 
        base_settings['style'] * style_value + character_mods['style_mod']))
    final_speed = min(2.0, max(0.5, 
        base_settings['speed'] + character_mods['speed_mod']))
    
    return {
        "stability": final_stability,
        "similarity_boost": 0.75,
        "style": final_style,
        "speed": final_speed,
        "use_speaker_boost": True
    }

def retry_with_backoff(max_retries=3, initial_delay=1):
    """Decorator for retry logic with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for retry in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Check if the exception is from ElevenLabs by its module path
                    if not str(type(e).__module__).startswith('elevenlabs'):
                        raise
                    if retry == max_retries - 1:
                        raise
                    logging.warning(f"ElevenLabs API error (attempt {retry + 1}): {str(e)}. Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2
        return wrapper
    return decorator

CHARACTER_VOICES = {
    "Naruto": {
        "voice_id": "pNInz6obpgDQGcFmaJgB",  # Adam, energetic, young male voice
        "name": "Adam"
    },
    "Sasuke": {
        "voice_id": "VR6AewLTigWG4xSOukaG",  # Sam, deep, serious male voice
        "name": "Sam"
    },
    "Narrator": {
        "voice_id": "ThT5KcBeYPX3keUQqHPh",  # Daniel, clear narrative voice
        "name": "Daniel"
    }
}

@retry_with_backoff()
def generate_dialogue_audio(dialogue: Dict[str, Any], output_path: Path) -> bool:
    """Generate audio for a single dialogue with character-specific voice."""
    try:
        text = dialogue["text"]
        speaker = dialogue["speaker"]
        emotion_data = dialogue["emotion"]
        
        # Get character voice settings
        character_voice = CHARACTER_VOICES.get(speaker, CHARACTER_VOICES["Narrator"])
        voice_id = character_voice["voice_id"]
        
        # Add emotion prefix if not neutral
        if emotion_data["type"].lower() != "neutral":
            prefixed_text = f"[{emotion_data['description']}] {text}"
        else:
            prefixed_text = text
        
        # Get voice settings tuned for both emotion and character
        settings = get_voice_settings(emotion_data, speaker)
        
        client = initialize_elevenlabs()
        
        # Get voice settings for the API
        voice_settings = {
            "stability": settings["stability"],
            "similarity_boost": settings["similarity_boost"],
            "style": settings["style"]
        }
        
        # Generate audio
        audio_stream = client.text_to_speech.convert(
            text=prefixed_text,
            voice_id=voice_id,
            model_id=MODEL_ID,
            voice_settings=voice_settings,
            output_format="mp3_44100_128"
        )
        
        # Save audio to file
        with open(str(output_path), 'wb') as f:
            # Handle streaming response
            for chunk in audio_stream:
                if isinstance(chunk, bytes):
                    f.write(chunk)
        logging.info(f"Generated audio for dialogue: {text[:50]}...")
        return True
    
    except Exception as e:
        logging.error(f"Failed to generate audio for dialogue: {str(e)}")
        return False

def concatenate_audio_files(audio_paths: List[Path], output_path: Path) -> bool:
    """Concatenate multiple audio files using ffmpeg."""
    try:
        # Create temporary file list for concat demuxer
        with tempfile.NamedTemporaryFile('w', suffix='.txt', delete=False) as f:
            for path in audio_paths:
                f.write(f"file '{path.resolve().as_posix()}'\n")
            list_path = f.name
        
        try:
            # Concatenate using stream copy (no re-encode)
            ffmpeg.input(list_path, f='concat', safe=0)\
                .output(str(output_path), c='copy')\
                .overwrite_output()\
                .run(quiet=True)
            
            logging.info(f"Successfully concatenated {len(audio_paths)} audio files to {output_path}")
            return True
        
        finally:
            # Clean up temporary file
            os.unlink(list_path)
            
    except Exception as e:
        logging.error(f"Failed to concatenate audio files: {str(e)}")
        return False

def generate_audio_tracks(analysis_results: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """Generate audio tracks for all dialogues in the manga."""
    job_audio_dir = AUDIO_DIR / job_id
    job_audio_dir.mkdir(parents=True, exist_ok=True)
    
    initialize_elevenlabs()
    voice_id = DEFAULT_VOICE_ID
    
    total_dialogues = 0
    successful_dialogues = 0
    audio_paths = []
    
    logging.info(f"Starting audio generation for job {job_id} using voice {voice_id}")
    
    # Process each dialogue
    for page_idx, page in enumerate(analysis_results["pages"]):
        for panel in sorted(page["panels"], key=lambda p: p["reading_order"]):
            for dialogue_idx, dialogue in enumerate(panel.get("dialogues", [])):
                total_dialogues += 1
                
                # Generate unique filename for this dialogue
                filename = f"dialogue_p{page_idx:03d}_r{panel['reading_order']:02d}_d{dialogue_idx:02d}.mp3"
                audio_path = job_audio_dir / filename
                
                if generate_dialogue_audio(dialogue, audio_path):
                    successful_dialogues += 1
                    dialogue["audio_path"] = str(audio_path)
                    audio_paths.append(audio_path)
                    
                    # Add small delay between API calls
                    time.sleep(0.3)
    
    # Generate merged audio file if we have any successful generations
    if audio_paths:
        merged_path = job_audio_dir / "merged_audio.mp3"
        if concatenate_audio_files(audio_paths, merged_path):
            analysis_results["merged_audio_path"] = str(merged_path)
        else:
            raise Exception("Failed to create merged audio file")
    else:
        raise Exception("No audio files were successfully generated")
    
    # Add processing metadata
    analysis_results.update({
        "total_dialogues_processed": total_dialogues,
        "successful_dialogues": successful_dialogues,
        "failed_dialogues": total_dialogues - successful_dialogues
    })
    
    logging.info(f"Completed audio generation for job {job_id}. "
                f"Success: {successful_dialogues}/{total_dialogues} dialogues")
    
    return analysis_results

def cleanup_audio_files(job_id: str, keep_merged: bool = True) -> None:
    """Clean up audio files for a job."""
    job_audio_dir = AUDIO_DIR / job_id
    if not job_audio_dir.exists():
        return
    
    if keep_merged:
        # Keep merged audio, delete individual files
        merged_path = job_audio_dir / "merged_audio.mp3"
        for file in job_audio_dir.glob("dialogue_*.mp3"):
            file.unlink()
    else:
        # Remove entire directory
        import shutil
        shutil.rmtree(job_audio_dir)