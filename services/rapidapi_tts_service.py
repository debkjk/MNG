"""
RapidAPI Streamlined Edge TTS service for high-quality speech synthesis
"""
import os
import logging
import requests
from pathlib import Path
from typing import Dict, Any, List
from pydub import AudioSegment

# Configuration
AUDIO_DIR = Path(__file__).resolve().parent.parent / 'static' / 'audio'
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

TEMP_AUDIO_DIR = Path(__file__).resolve().parent.parent / 'temp_tts'
TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# RapidAPI Configuration
RAPIDAPI_KEY = "1f8a9baf1amsha9c5a90765fa87fp1aa69fjsn338b83111f9e"
RAPIDAPI_HOST = "streamlined-edge-tts.p.rapidapi.com"
API_URL = f"https://{RAPIDAPI_HOST}/tts"

# Voice mapping for different genders/speakers
VOICE_MAP = {
    'Male': 'en-US-GuyNeural',
    'Female': 'en-US-JennyNeural',
    'Narrator': 'en-US-AriaNeural',
    'Unknown': 'en-US-GuyNeural',
    # Additional voices for variety
    'Male2': 'en-US-ChristopherNeural',
    'Female2': 'en-CA-ClaraNeural',
}

def generate_speech(text: str, voice: str, output_path: Path, max_retries: int = 3) -> bool:
    """
    Generate speech using RapidAPI Streamlined Edge TTS with retry logic.
    
    Args:
        text: Text to convert to speech
        voice: Voice name (e.g., 'en-US-GuyNeural')
        output_path: Path to save the audio file
        max_retries: Maximum number of retry attempts
    
    Returns:
        True if successful, False otherwise
    """
    import time
    
    payload = {
        "text": text,
        "voice": voice
    }
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
        "Content-Type": "application/json"
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(API_URL, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # Save audio directly
                output_path.write_bytes(response.content)
                return True
            elif response.status_code == 502 and attempt < max_retries - 1:
                # Retry on 502 (API unreachable)
                wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                logging.warning(f"⚠️  API unreachable (502), retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                logging.error(f"❌ TTS API error {response.status_code}: {response.text[:200]}")
                return False
                
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                logging.warning(f"⚠️  Request timeout, retrying... (attempt {attempt + 1}/{max_retries})")
                time.sleep(2)
                continue
            else:
                logging.error(f"❌ TTS request timeout after {max_retries} attempts")
                return False
        except Exception as e:
            logging.error(f"❌ TTS request failed: {e}")
            return False
    
    return False

def get_voice_for_speaker(dialogue: Dict[str, Any], speaker_voice_map: Dict[str, str]) -> str:
    """
    Select appropriate voice based on speaker with consistent assignment.
    
    Args:
        dialogue: Dialogue dictionary containing speaker and speaker_gender
        speaker_voice_map: Dictionary mapping speaker names to voice IDs
    
    Returns:
        Voice ID string
    """
    speaker_name = dialogue.get('speaker', 'UNKNOWN')
    
    # Check if this speaker already has an assigned voice
    if speaker_name in speaker_voice_map:
        return speaker_voice_map[speaker_name]
    
    # Assign new voice based on speaker_gender
    speaker_gender = dialogue.get('speaker_gender', 'Unknown')
    
    # Count how many speakers of each type we already have
    male_count = sum(1 for v in speaker_voice_map.values() if v in [VOICE_MAP['Male'], VOICE_MAP.get('Male2')])
    female_count = sum(1 for v in speaker_voice_map.values() if v in [VOICE_MAP['Female'], VOICE_MAP.get('Female2')])
    
    if speaker_gender == 'Female':
        # Alternate between female voices
        voice = VOICE_MAP['Female'] if female_count % 2 == 0 else VOICE_MAP.get('Female2', VOICE_MAP['Female'])
    elif speaker_gender == 'Male':
        # Alternate between male voices
        voice = VOICE_MAP['Male'] if male_count % 2 == 0 else VOICE_MAP.get('Male2', VOICE_MAP['Male'])
    elif speaker_gender == 'Narrator':
        voice = VOICE_MAP['Narrator']
    else:
        # For UNKNOWN, assign unique voice based on sequence
        # Use different voices for each UNKNOWN speaker
        unknown_count = sum(1 for k, v in speaker_voice_map.items() if k.startswith('UNKNOWN'))
        voices_pool = [VOICE_MAP['Male'], VOICE_MAP['Female'], VOICE_MAP.get('Male2', VOICE_MAP['Male']), VOICE_MAP.get('Female2', VOICE_MAP['Female'])]
        voice = voices_pool[unknown_count % len(voices_pool)]
    
    # Store assignment for consistency
    speaker_voice_map[speaker_name] = voice
    logging.info(f"      🎭 Assigned voice '{voice}' to speaker '{speaker_name}' (gender: {speaker_gender})")
    return voice

def generate_audio_tracks(analysis_results: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """
    Generate audio tracks using RapidAPI TTS.
    
    Args:
        analysis_results: Dictionary containing pages with dialogues
        job_id: Unique job identifier
    
    Returns:
        Updated analysis_results with audio paths and timing data
    """
    job_audio_dir = AUDIO_DIR / job_id
    job_audio_dir.mkdir(parents=True, exist_ok=True)
    
    job_temp_dir = TEMP_AUDIO_DIR / job_id
    job_temp_dir.mkdir(parents=True, exist_ok=True)
    
    speaker_voice_map = {}  # Track voice assignments per speaker
    temp_files = []
    total_dialogues = 0
    successful_dialogues = 0
    
    logging.info(f"\n🎤 Step 4/5: Generating audio with RapidAPI TTS...")
    
    # Generate audio for each dialogue
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
            
            # Select voice
            voice = get_voice_for_speaker(dialogue, speaker_voice_map)
            
            # Generate audio file
            temp_audio_file = job_temp_dir / f"dialogue_p{page_num:03d}_seq{sequence:03d}.mp3"
            
            logging.info(f"   🎤 Generating: [{speaker}] using voice '{voice}'")
            logging.info(f"      Text: {text[:60]}{'...' if len(text) > 60 else ''}")
            
            if generate_speech(text, voice, temp_audio_file):
                temp_files.append({
                    "file": temp_audio_file,
                    "dialogue": dialogue,
                    "page_num": page_num,
                    "sequence": sequence
                })
                successful_dialogues += 1
                logging.info(f"      ✅ Generated successfully")
            else:
                # Create silent audio as fallback (estimate 2 seconds per dialogue)
                logging.warning(f"      ⚠️  Failed to generate audio, using silent placeholder")
                silent_audio = AudioSegment.silent(duration=2000)  # 2 seconds
                silent_audio.export(str(temp_audio_file), format='mp3')
                temp_files.append({
                    "file": temp_audio_file,
                    "dialogue": dialogue,
                    "page_num": page_num,
                    "sequence": sequence,
                    "is_silent": True
                })
    
    if successful_dialogues == 0:
        raise RuntimeError("No audio files were generated successfully")
    
    logging.info(f"\n   ✅ Generated {successful_dialogues}/{total_dialogues} audio files")
    
    # Merge audio files with timing gaps
    logging.info(f"\n   🔗 Merging audio files with timing gaps and injecting timing data...")
    
    final_audio = AudioSegment.silent(duration=100)  # Start with 0.1s silence
    current_time_s = 0.1
    
    for item in temp_files:
        dialogue = item["dialogue"]
        sequence = item["sequence"]
        
        # Add silence gap
        time_gap_s = dialogue.get("time_gap_before_s", 0.0)
        if time_gap_s > 0.1:
            time_gap_ms = int(time_gap_s * 1000)
            final_audio += AudioSegment.silent(duration=time_gap_ms)
            current_time_s += time_gap_s
            logging.info(f"   ⏱️  Added {time_gap_s:.1f}s pause before dialogue {sequence}")
        
        # Add speech audio
        try:
            if item["file"].exists():
                speech_audio = AudioSegment.from_mp3(str(item["file"]))
                audio_duration_s = len(speech_audio) / 1000.0
                
                # CRITICAL: Inject timing data for video highlighting
                dialogue["audio_start_s"] = round(current_time_s, 2)
                dialogue["audio_duration_s"] = round(audio_duration_s, 2)
                
                final_audio += speech_audio
                current_time_s += audio_duration_s
                successful_dialogues += 1
                
                logging.info(f"   🎬 Dialogue {sequence}: start={dialogue['audio_start_s']}s, duration={dialogue['audio_duration_s']}s")
        except Exception as e:
            logging.error(f"   ❌ Error processing audio file {item['file']}: {e}")
    
    # Export merged audio
    merged_audio_path = job_audio_dir / 'merged_audio.mp3'
    final_audio.export(str(merged_audio_path), format='mp3', bitrate='192k')
    
    total_duration = len(final_audio) / 1000.0
    logging.info(f"\n   ✅ Merged audio created: {merged_audio_path}")
    logging.info(f"   ⏱️  Total duration: {total_duration:.2f} seconds")
    
    # Update analysis results
    analysis_results['merged_audio_path'] = str(merged_audio_path)
    analysis_results['total_audio_duration'] = total_duration
    analysis_results['successful_dialogues'] = successful_dialogues
    
    # Cleanup temp files
    logging.info(f"\n   🧹 Cleaning up temporary files...")
    for item in temp_files:
        try:
            if item["file"].exists():
                item["file"].unlink()
        except Exception as e:
            logging.warning(f"   ⚠️  Could not delete {item['file']}: {e}")
    
    return analysis_results
