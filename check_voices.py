# check_voices.py

import pyttsx3

def list_voices():
    """Prints all available voices and their corresponding index, gender, and name."""
    try:
        engine = pyttsx3.init()
    except Exception as e:
        print(f"Error initializing pyttsx3: {e}. Ensure all dependencies are installed.")
        return

    voices = engine.getProperty('voices')
    print("\n--- Available Local TTS Voices ---")
    
    if not voices:
        print("No TTS voices found. Check your OS Text-to-Speech settings.")
        return

    for index, voice in enumerate(voices):
        gender = getattr(voice, 'gender', 'UNKNOWN/Driver Dependent') 
        age = getattr(voice, 'age', 'N/A')
        print(f"Index: {index}")
        print(f"  Name: {voice.name}")
        print(f"  Gender/Age: {gender} / {age}")
        print(f"  ID: {voice.id}\n")
    print("----------------------------------")
    
    # Auto-detect and suggest indices
    print("\n--- Suggested Voice Mapping ---")
    male_idx = 0
    female_idx = 1
    narrator_idx = 0
    
    for index, voice in enumerate(voices):
        voice_name = voice.name.lower()
        if 'female' in voice_name or 'zira' in voice_name or 'hazel' in voice_name:
            female_idx = index
            print(f"Female voice detected: Index {index} - {voice.name}")
        elif 'male' in voice_name or 'david' in voice_name or 'mark' in voice_name:
            male_idx = index
            print(f"Male voice detected: Index {index} - {voice.name}")
    
    print(f"\nRecommended configuration:")
    print(f"MALE_VOICE_INDEX = {male_idx}")
    print(f"FEMALE_VOICE_INDEX = {female_idx}")
    print(f"NARRATOR_VOICE_INDEX = {narrator_idx}")
    print("----------------------------------\n")

if __name__ == '__main__':
    list_voices()
