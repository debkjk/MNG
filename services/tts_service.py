from elevenlabs.client import ElevenLabs
import ffmpeg
from pathlib import Path
import logging
import os
import time
import tempfile
from typing import List, Dict, Any
import functools
import json

# Configure paths and directories
AUDIO_DIR = Path(__file__).resolve().parent.parent / 'static' / 'audio'
CONFIG_DIR = Path(__file__).resolve().parent.parent / 'static' / 'config'
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Constants
DEFAULT_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")  # Sarah voice
MODEL_ID = "eleven_multilingual_v2"

# Load character configuration
def load_character_config():
    config_path = CONFIG_DIR / 'characters.json'
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load character config: {str(e)}")
        return None

CHARACTER_CONFIG = load_character_config()

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

def get_voice_settings(emotion_data: Dict[str, Any], speaker: str) -> dict:
    """
    Get emotion and character-tuned voice settings.
    
    Args:
        emotion_data: Dictionary containing emotion parameters
        speaker: The character speaking
    """
    if not CHARACTER_CONFIG:
        logging.warning("Character config not loaded, using default settings")
        return {"stability": 0.5, "style": 0.0, "similarity_boost": 0.75}

    # Get character info
    character_info = CHARACTER_CONFIG["characters"].get(speaker, CHARACTER_CONFIG["characters"].get("Narrator"))
    character_type = character_info["type"]
    type_settings = CHARACTER_CONFIG["character_types"][character_type]

    # Get emotion settings
    emotion_type = emotion_data.get('type', 'neutral').lower()
    emotion_mods = CHARACTER_CONFIG["emotion_modifiers"].get(
        emotion_type, 
        CHARACTER_CONFIG["emotion_modifiers"]["neutral"]
    )

    # Base stability from character type
    base_stability = type_settings["voice_stability"]
    base_style = type_settings["style_intensity"]
    emotion_intensity = type_settings["emotion_intensity"]

    # Apply emotion modifiers scaled by character's emotion intensity
    final_stability = min(0.9, max(0.1,
        base_stability + (emotion_mods["stability_mod"] * emotion_intensity)))
    final_style = min(1.0, max(0.0,
        base_style + (emotion_mods["style_mod"] * emotion_intensity)))
    
    # Get speed and other modifiers from emotion data
    speed_mod = emotion_mods.get("speed_mod", 0)
    
    # Calculate final speed
    final_speed = min(2.0, max(0.5, 1.0 + speed_mod))
    
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
        
        # Log the dialogue being processed
        logging.info(f"      🎙️  {speaker}: \"{text[:60]}{'...' if len(text) > 60 else ''}\"\")")
        
        # Handle emotion - can be string or dict
        if isinstance(dialogue["emotion"], str):
            emotion_type = dialogue["emotion"]
            emotion_data = {"type": emotion_type, "description": emotion_type}
        else:
            emotion_data = dialogue["emotion"]
            emotion_type = emotion_data.get("type", "neutral")
        
        # Get character info with fallback to default voices
        if not CHARACTER_CONFIG:
            logging.warning("Character config not loaded, using default voice")
            character_info = {
                "voice_id": DEFAULT_VOICE_ID,
                "personality": "",
                "type": "narrator"
            }
        else:
            # Try to get character, fallback to default voices, then Narrator
            character_info = CHARACTER_CONFIG["characters"].get(speaker)
            if not character_info:
                # Try default voices for unknown characters
                default_voices = CHARACTER_CONFIG.get("default_voices", {})
                if "male" in speaker.lower() or "man" in speaker.lower() or "boy" in speaker.lower():
                    character_info = default_voices.get("UNKNOWN_MALE")
                elif "female" in speaker.lower() or "woman" in speaker.lower() or "girl" in speaker.lower():
                    character_info = default_voices.get("UNKNOWN_FEMALE")
                else:
                    character_info = default_voices.get("UNKNOWN")
                
                # Final fallback to Narrator
                if not character_info:
                    character_info = CHARACTER_CONFIG["characters"]["Narrator"]
                    logging.info(f"Using Narrator voice for unknown speaker: {speaker}")
        
        # Get voice settings tuned for both emotion and character
        settings = get_voice_settings(emotion_data, speaker)
        
        # Add emotion context for ElevenLabs
        # Format: [emotion] text - ElevenLabs models understand emotion tags
        emotion_prefix = ""
        if emotion_type.lower() not in ["neutral", "narration", "calm"]:
            # Map emotion to natural language descriptor
            emotion_map = {
                "angry": "angrily",
                "yell": "shouting",
                "sad": "sadly",
                "whisper": "whispering",
                "excitement": "excitedly",
                "amusement": "with amusement",
                "scared": "fearfully",
                "surprised": "with surprise"
            }
            emotion_word = emotion_map.get(emotion_type.lower(), emotion_type)
            emotion_prefix = f"[{emotion_word}] "
        
        prefixed_text = f"{emotion_prefix}{text}"
        
        client = initialize_elevenlabs()
        
        # Get voice settings for the API
        from elevenlabs.types import VoiceSettings
        
        voice_settings = VoiceSettings(
            stability=settings["stability"],
            similarity_boost=settings["similarity_boost"],
            style=settings["style"]
        )
        
        # Generate audio
        audio_stream = client.text_to_speech.convert(
            text=prefixed_text,
            voice_id=character_info["voice_id"],
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
        # Only log once per error type, not for every dialogue
        error_msg = str(e)
        if "status_code: 401" in error_msg or "detected_unusual_activity" in error_msg:
            # Don't spam logs - just log once
            if not hasattr(generate_dialogue_audio, '_elevenlabs_blocked_logged'):
                logging.error(f"⚠️ ElevenLabs API BLOCKED: Account flagged for unusual activity (status 401)")
                logging.error(f"   Solution: Upgrade to paid plan or use Mock TTS")
                generate_dialogue_audio._elevenlabs_blocked_logged = True
        else:
            logging.error(f"Failed to generate audio: {error_msg}")
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
    
    # Process each page's dialogues (new structure: pages -> dialogs)
    for page in analysis_results["pages"]:
        page_num = page.get("page_number", 1)
        
        # Get dialogues from new structure
        dialogues = page.get("dialogs", [])
        
        for dialogue in dialogues:
            total_dialogues += 1
            sequence = dialogue.get("sequence", total_dialogues)
            
            # Generate unique filename for this dialogue
            filename = f"dialogue_p{page_num:03d}_seq{sequence:03d}.mp3"
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