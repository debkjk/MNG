"""
Local Text-to-Speech service using pyttsx3
High-quality, offline TTS with emotion and timing control
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import time
import pyttsx3
import json
from pydub import AudioSegment
from pydub.generators import Sine
import tempfile
import wave
import io

# Configuration
AUDIO_DIR = Path(__file__).resolve().parent.parent / 'static' / 'audio'
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# --- Configuration ---
# TTS Configuration
BASE_WPM = 180  # Base Words Per Minute for speech rate
SILENCE_SAMPLE_RATE = 22050  # Sample rate for silence generation

# Voice Indices - UPDATE THESE after running check_voices.py
MALE_VOICE_INDEX = 0      # Default: First male voice
FEMALE_VOICE_INDEX = 1    # Default: First female voice
NARRATOR_VOICE_INDEX = 0  # Default: Same as male voice

# Voice mapping dictionary (uses indices above)
VOICE_INDICES = {
    'male': MALE_VOICE_INDEX,
    'female': FEMALE_VOICE_INDEX,
    'narrator': NARRATOR_VOICE_INDEX,
    'default': MALE_VOICE_INDEX
}

def initialize_tts_engine():
    """Initialize pyttsx3 TTS engine with optimal settings."""
    try:
        engine = pyttsx3.init()
        
        # List available voices for logging
        voices = engine.getProperty('voices')
        logging.info(f"🎤 Available TTS voices: {len(voices)}")
        for idx, voice in enumerate(voices):
            logging.info(f"   Voice {idx}: {voice.name}")
        
        # Auto-detect voice indices
        for idx, voice in enumerate(voices):
            voice_name = voice.name.lower()
            if 'female' in voice_name or 'zira' in voice_name:
                VOICE_INDICES['female'] = idx
            elif 'male' in voice_name or 'david' in voice_name:
                VOICE_INDICES['male'] = idx
        
        logging.info(f"🎤 Voice mapping: {VOICE_INDICES}")
        return engine
    except Exception as e:
        logging.error(f"❌ Failed to initialize TTS engine: {e}")
        raise

def get_voice_id(engine, speaker_name: str) -> str:
    """
    Select appropriate voice based on speaker name.
    
    Args:
        engine: pyttsx3 engine instance
        speaker_name: Name of the speaker
    
    Returns:
        Voice ID string
    """
    voices = engine.getProperty('voices')
    
    # Rule-based voice selection
    speaker_lower = speaker_name.lower()
    
    if speaker_name in ["Narrator", "SFX", "UNKNOWN"]:
        return voices[VOICE_INDICES['narrator']].id
    
    # Gender detection from name
    if any(word in speaker_lower for word in ['woman', 'girl', 'female', 'lady', 'mother', 'sister']):
        return voices[VOICE_INDICES['female']].id
    
    # Default to male voice
    return voices[VOICE_INDICES['male']].id

def create_silence(duration_seconds: float, output_path: Path) -> bool:
    """
    Create a silent audio file for timing gaps.
    
    Args:
        duration_seconds: Duration of silence in seconds
        output_path: Path to save the silence audio file
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create silence using pydub
        silence = AudioSegment.silent(duration=int(duration_seconds * 1000))  # Convert to milliseconds
        silence.export(str(output_path), format="mp3")
        return True
    except Exception as e:
        logging.error(f"❌ Failed to create silence: {e}")
        return False

def generate_dialogue_audio(dialogue: Dict[str, Any], output_path: Path, engine: pyttsx3.Engine) -> bool:
    """
    Generate audio for a single dialogue using pyttsx3.
    
    Args:
        dialogue: Dialogue dictionary with text, speaker, emotion, and speech parameters
        output_path: Path to save the generated audio
        engine: pyttsx3 engine instance
    
    Returns:
        True if successful, False otherwise
    """
    try:
        text = dialogue.get('text', '')
        speaker = dialogue.get('speaker', 'UNKNOWN')
        
        if not text:
            logging.warning(f"⚠️  Empty text for speaker: {speaker}")
            return False
        
        # Get speech parameters
        speech = dialogue.get('speech', {})
        speed_factor = speech.get('speed', 1.0)
        volume = speech.get('volume', 1.0)
        pitch = speech.get('pitch', 'medium')
        
        # Get emotion for logging
        emotion = dialogue.get('emotion', {})
        emotion_type = emotion.get('type', 'neutral')
        
        # Set voice based on speaker
        try:
            voice_id = get_voice_id(engine, speaker)
            engine.setProperty('voice', voice_id)
        except IndexError:
            logging.warning(f"⚠️  Voice not found for {speaker}, using default")
        
        # Set speech rate (WPM)
        new_rate = int(BASE_WPM * speed_factor)
        engine.setProperty('rate', new_rate)
        
        # Set volume (pyttsx3 max is 1.0)
        new_volume = min(volume, 1.0)
        engine.setProperty('volume', new_volume)
        
        # Log the generation
        logging.info(f"      🎙️  [{speaker}] ({emotion_type}): \"{text[:50]}{'...' if len(text) > 50 else ''}\"")
        logging.info(f"          Rate: {new_rate} WPM, Volume: {new_volume:.2f}, Pitch: {pitch}")
        
        # Save to file
        engine.save_to_file(text, str(output_path))
        engine.runAndWait()
        
        # Verify file was created
        if output_path.exists() and output_path.stat().st_size > 0:
            return True
        else:
            logging.error(f"❌ Audio file not created or empty: {output_path}")
            return False
            
    except Exception as e:
        logging.error(f"❌ Failed to generate audio for dialogue: {e}")
        return False

def concatenate_audio_files(audio_paths: List[Path], output_path: Path) -> bool:
    """
    Concatenate multiple audio files using pydub.
    
    Args:
        audio_paths: List of audio file paths to concatenate
        output_path: Path to save the merged audio
    
    Returns:
        True if successful, False otherwise
    """
    try:
        if not audio_paths:
            logging.error("❌ No audio files to concatenate")
            return False
        
        logging.info(f"🔗 Merging {len(audio_paths)} audio files...")
        
        # Load first audio file
        combined = AudioSegment.from_file(str(audio_paths[0]))
        
        # Concatenate remaining files
        for audio_path in audio_paths[1:]:
            audio = AudioSegment.from_file(str(audio_path))
            combined += audio
        
        # Export merged audio
        combined.export(str(output_path), format="mp3")
        
        logging.info(f"✅ Merged audio saved: {output_path}")
        return True
        
    except Exception as e:
        logging.error(f"❌ Failed to concatenate audio files: {e}")
        return False

def generate_audio_tracks(analysis_results: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """
    Generate audio tracks for all dialogues in the manga using local TTS.
    
    Args:
        analysis_results: Dictionary containing pages with dialogues
        job_id: Unique job identifier
    
    Returns:
        Dictionary with generation results and statistics
    """
    job_audio_dir = AUDIO_DIR / job_id
    job_audio_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize TTS engine
    engine = initialize_tts_engine()
    
    total_dialogues = 0
    successful_dialogues = 0
    audio_paths = []
    
    logging.info(f"\n🎤 Step 4/5: Generating audio with local TTS...")
    
    # Process each page's dialogues
    for page in analysis_results["pages"]:
        page_num = page.get("page_number", 1)
        dialogues = page.get("dialogs", [])
        
        for dialogue in dialogues:
            total_dialogues += 1
            sequence = dialogue.get("sequence", total_dialogues)
            time_gap = dialogue.get("time_gap_before_s", 0.0)
            
            # Generate silence for timing gap if needed
            if time_gap > 0.1:  # Only create silence if gap is significant
                silence_filename = f"silence_p{page_num:03d}_seq{sequence:03d}.mp3"
                silence_path = job_audio_dir / silence_filename
                
                if create_silence(time_gap, silence_path):
                    audio_paths.append(silence_path)
                    logging.info(f"      ⏱️  Added {time_gap:.1f}s pause")
            
            # Generate dialogue audio
            filename = f"dialogue_p{page_num:03d}_seq{sequence:03d}.mp3"
            audio_path = job_audio_dir / filename
            
            if generate_dialogue_audio(dialogue, audio_path, engine):
                successful_dialogues += 1
                dialogue["audio_path"] = str(audio_path)
                audio_paths.append(audio_path)
    
    # Generate merged audio file if we have any successful generations
    if audio_paths:
        merged_path = job_audio_dir / "merged_audio.mp3"
        if concatenate_audio_files(audio_paths, merged_path):
            analysis_results["merged_audio_path"] = str(merged_path)
            logging.info(f"\n✅ TTS generation completed!")
            logging.info(f"   🎵 Generated {successful_dialogues}/{total_dialogues} audio files")
            logging.info(f"   📁 Merged audio: {merged_path}")
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
    
    return analysis_results
