"""
Local Text-to-Speech service using pyttsx3
OPTIMIZED: Efficient queued batch processing to eliminate blocking delays
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pyttsx3
from pydub import AudioSegment

# Configuration
AUDIO_DIR = Path(__file__).resolve().parent.parent / 'static' / 'audio'
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Temporary directory for WAV files before conversion
TEMP_AUDIO_DIR = Path(__file__).resolve().parent.parent / 'temp_tts'
TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# --- Configuration ---
# TTS Configuration
BASE_WPM = 130  # Base Words Per Minute for speech rate (slower for clearer, more natural speech)

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
        
        logging.info(f"🎤 Voice mapping: {VOICE_INDICES}")
        return engine
    except Exception as e:
        logging.error(f"❌ Failed to initialize TTS engine: {e}")
        raise

def get_voice_id(engine, dialogue: Dict[str, Any]) -> str:
    """
    Select appropriate voice based on speaker_gender field from Gemini.
    
    Args:
        engine: pyttsx3 engine instance
        dialogue: Dialogue dictionary containing speaker_gender field
    
    Returns:
        Voice ID string
    """
    voices = engine.getProperty('voices')
    
    # CRITICAL: Use speaker_gender field from Gemini analysis
    speaker_gender = dialogue.get('speaker_gender', 'Unknown')
    
    # Direct gender-based voice selection
    if speaker_gender == 'Female':
        return voices[VOICE_INDICES['female']].id
    elif speaker_gender == 'Male':
        return voices[VOICE_INDICES['male']].id
    elif speaker_gender == 'Narrator':
        return voices[VOICE_INDICES['narrator']].id
    else:
        # Fallback: try to infer from speaker name if gender unknown
        speaker_name = dialogue.get('speaker', 'UNKNOWN')
        speaker_lower = speaker_name.lower()
        
        if speaker_name in ["Narrator", "SFX", "UNKNOWN"]:
            return voices[VOICE_INDICES['narrator']].id
        
        if any(word in speaker_lower for word in ['woman', 'girl', 'female', 'lady', 'mother', 'sister']):
            return voices[VOICE_INDICES['female']].id
        
        # Default to male voice
        return voices[VOICE_INDICES['male']].id

def generate_audio_tracks(analysis_results: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """
    OPTIMIZED: Generate audio tracks using efficient queued batch processing.
    This eliminates the 4-5 minute blocking delay by queuing all commands first,
    then running them in a single batch.
    
    Args:
        analysis_results: Dictionary containing pages with dialogues
        job_id: Unique job identifier
    
    Returns:
        Dictionary with generation results and statistics
    """
    job_audio_dir = AUDIO_DIR / job_id
    job_audio_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize TTS engine ONCE
    try:
        engine = initialize_tts_engine()
    except Exception as e:
        logging.error(f"❌ Error initializing pyttsx3 engine: {e}")
        raise
    
    voices = engine.getProperty('voices')
    temp_files = []
    total_dialogues = 0
    
    logging.info(f"\n🎤 Step 4/5: Generating audio with local TTS (OPTIMIZED)...")
    logging.info(f"   📝 Queuing audio generation commands (fast)...")
    
    # STEP 1: Queue all audio generation commands (FAST - no blocking)
    for page in analysis_results.get("pages", []):
        page_num = page.get("page_number", 1)
        dialogues = page.get("dialogs", [])
        
        for dialogue in dialogues:
            total_dialogues += 1
            sequence = dialogue.get("sequence", total_dialogues)
            speaker = dialogue.get("speaker", "UNKNOWN")
            text = dialogue.get("text", "")
            
            if not text:
                logging.warning(f"⚠️  Empty text for speaker: {speaker}")
                continue
            
            try:
                # Set voice based on speaker_gender from Gemini
                voice_id = get_voice_id(engine, dialogue)
                engine.setProperty('voice', voice_id)
                
                # Set speed
                speech = dialogue.get("speech", {})
                speed_factor = speech.get("speed", 1.0)
                new_rate = int(BASE_WPM * speed_factor)
                engine.setProperty('rate', new_rate)
                
                # Set volume (capped at 1.0 for pyttsx3)
                volume = min(speech.get("volume", 1.0), 1.0)
                engine.setProperty('volume', volume)
                
                # Define output path
                temp_wav_file = TEMP_AUDIO_DIR / f"dialogue_p{page_num:03d}_seq{sequence:03d}.wav"
                
                # CRITICAL FIX: Use save_to_file instead of say()
                engine.save_to_file(text, str(temp_wav_file))
                
                # Store metadata for later processing
                temp_files.append({
                    "file": temp_wav_file,
                    "dialogue": dialogue,
                    "page_num": page_num,
                    "sequence": sequence
                })
                
                emotion = dialogue.get("emotion", {})
                emotion_type = emotion.get("type", "neutral")
                logging.info(f"   ✓ Queued: [{speaker}] ({emotion_type}) - Rate: {new_rate}, Vol: {volume:.2f}")
                
            except IndexError:
                logging.warning(f"⚠️  Voice index not found. Skipping audio for '{speaker}'.")
                continue
    
    # STEP 2: Generate all files in a single batch (THE FIX FOR THE 4-5 MINUTE DELAY)
    logging.info(f"\n   ⚡ Running batch audio generation for {len(temp_files)} dialogues...")
    logging.info(f"   ⏳ This should complete in seconds, not minutes...")
    
    try:
        engine.runAndWait()
        logging.info(f"   ✅ Batch generation complete!")
    except Exception as e:
        logging.error(f"❌ Error during runAndWait: {e}")
        raise
    
    # STEP 3: Convert WAV to MP3 and merge with timing gaps
    # CRITICAL: Track timing data for video highlighting
    logging.info(f"\n   🔗 Merging audio files with timing gaps and injecting timing data...")
    
    final_audio = AudioSegment.silent(duration=100)  # Start with small buffer
    successful_dialogues = 0
    current_time_s = 0.1  # Start time in seconds (after initial buffer)
    
    for item in temp_files:
        dialogue = item["dialogue"]
        page_num = item["page_num"]
        sequence = item["sequence"]
        
        # Add silence (time gap)
        time_gap_s = dialogue.get("time_gap_before_s", 0.0)
        if time_gap_s > 0.1:
            time_gap_ms = int(time_gap_s * 1000)
            final_audio += AudioSegment.silent(duration=time_gap_ms)
            current_time_s += time_gap_s
            logging.info(f"   ⏱️  Added {time_gap_s:.1f}s pause before dialogue {sequence}")
        
        # Add speech audio
        try:
            if item["file"].exists():
                speech_audio = AudioSegment.from_wav(str(item["file"]))
                audio_duration_s = len(speech_audio) / 1000.0  # Convert ms to seconds
                
                # CRITICAL: Inject timing data for video highlighting
                dialogue["audio_start_s"] = round(current_time_s, 2)
                dialogue["audio_duration_s"] = round(audio_duration_s, 2)
                
                final_audio += speech_audio
                current_time_s += audio_duration_s
                successful_dialogues += 1
                
                # Store audio path in dialogue metadata
                dialogue["audio_path"] = str(item["file"])
                
                logging.info(f"   🎬 Dialogue {sequence}: start={dialogue['audio_start_s']}s, duration={dialogue['audio_duration_s']}s")
            else:
                logging.warning(f"⚠️  Audio file not created: {item['file']}")
        except Exception as e:
            logging.error(f"❌ Error loading {item['file']}: {e}. Skipping this segment.")
    
    # STEP 4: Export final merged audio
    merged_path = job_audio_dir / "merged_audio.mp3"
    logging.info(f"\n   💾 Exporting final merged audio...")
    final_audio.export(str(merged_path), format="mp3")
    
    # STEP 5: Cleanup temporary files
    logging.info(f"   🧹 Cleaning up temporary files...")
    for item in temp_files:
        if item["file"].exists():
            try:
                item["file"].unlink()
            except Exception as e:
                logging.warning(f"⚠️  Could not delete {item['file']}: {e}")
    
    # Try to remove temp directory if empty
    try:
        if TEMP_AUDIO_DIR.exists() and not any(TEMP_AUDIO_DIR.iterdir()):
            TEMP_AUDIO_DIR.rmdir()
    except Exception:
        pass  # Directory not empty or other issue
    
    # Add results to analysis
    analysis_results["merged_audio_path"] = str(merged_path)
    analysis_results.update({
        "total_dialogues_processed": total_dialogues,
        "successful_dialogues": successful_dialogues,
        "failed_dialogues": total_dialogues - successful_dialogues
    })
    
    logging.info(f"\n✅ TTS generation completed!")
    logging.info(f"   🎵 Generated {successful_dialogues}/{total_dialogues} audio files")
    logging.info(f"   📁 Merged audio: {merged_path}")
    
    return analysis_results
