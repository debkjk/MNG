"""
Test RapidAPI Realistic TTS service
"""
import requests
import base64
from pathlib import Path

# API Configuration - Streamlined Edge TTS
RAPIDAPI_KEY = "1f8a9baf1amsha9c5a90765fa87fp1aa69fjsn338b83111f9e"
RAPIDAPI_HOST = "streamlined-edge-tts.p.rapidapi.com"
API_URL = f"https://{RAPIDAPI_HOST}/tts"

def test_tts_voice(text: str, voice: str, output_file: str):
    """Test a single voice with given text."""
    
    print(f"\n🎤 Testing voice: {voice}")
    print(f"   Text: {text[:50]}...")
    
    # Streamlined Edge TTS format
    payload = {
        "text": text,
        "voice": voice
    }
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST,
        "Content-Type": "application/json"
    }
    
    print(f"   📤 Sending POST request...")
    
    try:
        # Try POST first
        response = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            # Check content type
            content_type = response.headers.get('Content-Type', '')
            print(f"   📦 Content-Type: {content_type}")
            
            # If it's audio, save directly
            if 'audio' in content_type or 'octet-stream' in content_type:
                output_path = Path(output_file)
                output_path.write_bytes(response.content)
                print(f"   ✅ Audio received! Saved to: {output_file}")
                return True
            
            # Try to parse as JSON
            try:
                result = response.json()
                print(f"   ✅ JSON Response: {result}")
                
                # Check if audio data is in response
                if 'audio' in result:
                    # Decode base64 audio if present
                    audio_data = base64.b64decode(result['audio'])
                    output_path = Path(output_file)
                    output_path.write_bytes(audio_data)
                    print(f"   💾 Saved to: {output_file}")
                    return True
                elif 'url' in result:
                    # Download from URL if provided
                    audio_response = requests.get(result['url'])
                    output_path = Path(output_file)
                    output_path.write_bytes(audio_response.content)
                    print(f"   💾 Saved to: {output_file}")
                    return True
                else:
                    print(f"   ⚠️  Unknown response format: {result}")
                    return False
            except:
                print(f"   ⚠️  Response is not JSON, saving raw content")
                output_path = Path(output_file)
                output_path.write_bytes(response.content)
                print(f"   💾 Saved to: {output_file}")
                return True
        else:
            print(f"   ❌ Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("🧪 TESTING RAPIDAPI REALISTIC TTS")
    print("="*60)
    
    # Test different voices (Streamlined Edge TTS voices)
    test_cases = [
        ("The sorcery emperor has returned!", "en-US-GuyNeural", "test_guy.mp3"),
        ("Why are they having a parade in the royal city?", "en-US-JennyNeural", "test_jenny.mp3"),
        ("He and the other magicknights sent that invading army packing!", "en-CA-Clara", "test_clara.mp3"),
    ]
    
    success_count = 0
    for text, voice, output_file in test_cases:
        if test_tts_voice(text, voice, output_file):
            success_count += 1
    
    print("\n" + "="*60)
    print(f"📊 RESULTS: {success_count}/{len(test_cases)} tests passed")
    print("="*60)
    
    if success_count > 0:
        print("\n✅ RapidAPI TTS is working!")
        print("   Listen to the generated files to check quality.")
    else:
        print("\n❌ RapidAPI TTS failed. Check API key and endpoint.")
