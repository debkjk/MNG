# ElevenLabs API Quota Issue - URGENT FIX NEEDED

## ⚠️ Current Error

```
ERROR: Unusual activity detected. Free Tier usage disabled.
Exception: No audio files were successfully generated
```

## Root Cause

**ElevenLabs detected unusual activity** and disabled your free tier access. This happens when:

1. **Too many requests in short time** (rate limiting)
2. **Using VPN/Proxy** (triggers abuse detection)
3. **Free tier quota exceeded** (10,000 characters/month)
4. **Account flagged** for suspicious activity

## Immediate Solutions

### Option 1: Check Your Quota (Recommended)

1. Go to **https://elevenlabs.io/app/usage**
2. Log in with your account
3. Check remaining characters
4. If quota is 0, you need to:
   - Wait until next month (free tier resets)
   - Upgrade to paid plan ($5/month for 30,000 chars)

### Option 2: Use Different API Key

If you have another ElevenLabs account:

1. Create new account at https://elevenlabs.io
2. Get new API key from Settings → API Keys
3. Update `.env` file:
   ```env
   ELEVENLABS_API_KEY=your_new_key_here
   ```
4. Restart server

### Option 3: Disable VPN/Proxy

If you're using a VPN:
1. Disconnect VPN
2. Restart server
3. Try again

### Option 4: Use Mock TTS (For Testing)

Temporarily bypass TTS for testing:

**Edit `services/tts_service.py`:**
```python
# Add at the top of generate_dialogue_audio()
def generate_dialogue_audio(dialogue: Dict[str, Any], output_path: Path) -> bool:
    # TEMPORARY: Mock audio generation for testing
    import shutil
    from pathlib import Path
    
    # Create a silent audio file (you need a sample silent.mp3)
    # Or just create empty file for now
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.touch()  # Create empty file
    
    logging.info(f"MOCK: Generated audio for: {dialogue['text'][:50]}")
    return True
    
    # Comment out the rest of the function
```

**Note**: This won't produce actual audio, but lets you test the pipeline.

## Long-Term Solutions

### Solution 1: Upgrade to Paid Plan

**ElevenLabs Pricing:**
- **Starter**: $5/month - 30,000 characters
- **Creator**: $22/month - 100,000 characters
- **Pro**: $99/month - 500,000 characters

**Recommendation**: Starter plan is enough for testing.

### Solution 2: Use Alternative TTS

Replace ElevenLabs with:

#### **Google Cloud TTS** (Free tier: 1M chars/month)
```python
from google.cloud import texttospeech
```

#### **Amazon Polly** (Free tier: 5M chars/month for 12 months)
```python
import boto3
```

#### **Azure Speech** (Free tier: 500K chars/month)
```python
from azure.cognitiveservices.speech import SpeechSynthesizer
```

### Solution 3: Implement Caching

Cache generated audio to avoid regenerating:

```python
# Check if audio already exists
if output_path.exists():
    logging.info(f"Using cached audio: {output_path}")
    return True
```

## Quick Check Commands

### Check ElevenLabs API Status
```bash
curl -H "xi-api-key: YOUR_API_KEY" https://api.elevenlabs.io/v1/user
```

### Check Quota
```bash
curl -H "xi-api-key: YOUR_API_KEY" https://api.elevenlabs.io/v1/user/subscription
```

## What Happened in Your Case

Looking at the logs:
1. ✅ Upload worked (`POST /api/upload HTTP/1.1 200 OK`)
2. ✅ PDF processing started
3. ✅ Gemini analysis likely completed
4. ❌ TTS generation failed (ElevenLabs quota/abuse detection)
5. ❌ Job failed, server crashed

## Verify Job Status

Check the database:
```bash
sqlite3 database/manga_dubbing.db "SELECT job_id, status, error_message FROM jobs ORDER BY created_at DESC LIMIT 1;"
```

## Recovery Steps

1. **Check your ElevenLabs account** at https://elevenlabs.io/app/usage
2. **If quota is 0**: Wait or upgrade
3. **If flagged**: Contact ElevenLabs support
4. **For testing**: Use mock TTS (Option 4 above)

## Prevention

### Rate Limiting
Add delays between TTS requests:

```python
import time

for dialogue in dialogues:
    generate_dialogue_audio(dialogue, output_path)
    time.sleep(0.5)  # 500ms delay between requests
```

### Batch Processing
Process multiple dialogues in one request (if API supports it)

### Caching
Store generated audio and reuse for identical text

## Current Status

🔴 **BLOCKED**: Cannot generate audio until ElevenLabs issue is resolved

**Next Steps:**
1. Check your ElevenLabs account quota
2. Consider upgrading to paid plan ($5/month)
3. Or use mock TTS for testing the rest of the pipeline

---

**Note**: This is why the upload worked but processing failed. The pipeline is working correctly up to the TTS step.
