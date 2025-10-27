# 🎤 Local TTS Implementation Guide

## ✅ Complete Migration to pyttsx3

Your manga dubbing system now uses **local, offline Text-to-Speech** with pyttsx3 - no more API costs or blocking issues!

---

## 🎉 What Changed

### Before (ElevenLabs):
- ❌ Required API key
- ❌ Cost per character
- ❌ Account blocking issues
- ❌ Internet dependency
- ❌ Rate limits

### After (pyttsx3):
- ✅ Completely offline
- ✅ No API costs
- ✅ No account needed
- ✅ No rate limits
- ✅ Works anywhere

---

## 📦 Installation

### Install Required Packages:
```bash
pip install pyttsx3 pydub
```

### System Requirements:

**Windows:**
- Built-in SAPI5 voices (already installed)
- No additional setup needed

**Linux:**
```bash
sudo apt-get install espeak
```

**macOS:**
- Built-in NSSpeechSynthesizer (already installed)
- No additional setup needed

---

## 🎯 How It Works

### 1. Voice Selection
Automatically selects appropriate voice based on speaker:
- **Male characters** → Male voice
- **Female characters** → Female voice  
- **Narrator/SFX** → Narrator voice

### 2. Speech Parameters
Maps JSON metadata to TTS properties:

| JSON Field | pyttsx3 Property | Effect |
|------------|------------------|--------|
| `speech.speed` (0.8-1.3) | `rate` (WPM) | Speaking speed |
| `speech.volume` (0.8-1.2) | `volume` (0-1.0) | Audio volume |
| `speech.pitch` | Voice selection | High/medium/low |

### 3. Timing Intelligence
- **`time_gap_before_s`** → Creates silence audio files
- Automatically inserted between dialogues
- Natural pacing and dramatic pauses

### 4. Emotion Mapping
Speech parameters automatically adjusted based on emotion:

**YELL/EXCITEMENT:**
- Speed: > 1.0 (faster)
- Volume: > 1.0 (louder)
- Pitch: high

**CALM/SADNESS:**
- Speed: < 1.0 (slower)
- Volume: ≈ 1.0 (normal)
- Pitch: medium/low

**WHISPER:**
- Speed: ≈ 1.0 (normal)
- Volume: < 1.0 (quieter)
- Pitch: low

---

## 📊 Audio Generation Flow

```
1. For each dialogue:
   ├─ Check time_gap_before_s
   ├─ Create silence audio if gap > 0.1s
   ├─ Select voice based on speaker
   ├─ Set rate (WPM) from speech.speed
   ├─ Set volume from speech.volume
   ├─ Generate audio file
   └─ Add to audio list

2. Merge all audio files:
   ├─ Silence files (pauses)
   ├─ Dialogue files (speech)
   └─ Create merged_audio.mp3
```

---

## 🎤 Voice Configuration

### Check Available Voices:
```python
import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty('voices')

for idx, voice in enumerate(voices):
    print(f"Voice {idx}: {voice.name}")
```

### Typical Windows Voices:
```
Voice 0: Microsoft David Desktop (Male)
Voice 1: Microsoft Zira Desktop (Female)
```

### Voice Mapping (Auto-detected):
```python
VOICE_INDICES = {
    'male': 0,      # David
    'female': 1,    # Zira
    'narrator': 0,  # David
    'default': 0    # David
}
```

---

## 📝 Example: Dialogue Processing

### Input JSON:
```json
{
  "sequence": 1,
  "text": "I will protect everyone!",
  "speaker": "Hero",
  "time_gap_before_s": 0.5,
  "emotion": {
    "type": "yell",
    "intensity": 0.9
  },
  "speech": {
    "speed": 1.3,
    "volume": 1.2,
    "pitch": "high"
  }
}
```

### Processing:
```
1. Create 0.5s silence → silence_p001_seq001.mp3
2. Select male voice (Hero)
3. Set rate: 180 * 1.3 = 234 WPM (fast)
4. Set volume: min(1.2, 1.0) = 1.0 (max)
5. Generate speech → dialogue_p001_seq001.mp3
6. Add both to merge list
```

### Output:
```
silence_p001_seq001.mp3 (0.5s pause)
dialogue_p001_seq001.mp3 (speech)
```

---

## 🔧 Customization

### Adjust Base Speed:
Edit `services/tts_service.py`:
```python
BASE_WPM = 180  # Change this (default: 180)
```

- Lower = slower speech (e.g., 150)
- Higher = faster speech (e.g., 200)

### Adjust Voice Mapping:
```python
VOICE_INDICES = {
    'male': 0,      # Change to your preferred male voice index
    'female': 1,    # Change to your preferred female voice index
    'narrator': 0,  # Change to your preferred narrator voice
    'default': 0
}
```

---

## 📊 Quality Comparison

| Feature | ElevenLabs | pyttsx3 |
|---------|------------|---------|
| **Quality** | Very High | Good |
| **Naturalness** | Excellent | Moderate |
| **Emotion** | Advanced | Basic |
| **Cost** | $5-$22/month | Free |
| **Speed** | Slow (API) | Fast (local) |
| **Offline** | ❌ No | ✅ Yes |
| **Setup** | Complex | Simple |

---

## 🚀 Testing

### Test TTS Generation:
```bash
python test_pipeline.py
```

**Expected Output:**
```
🎤 Available TTS voices: 2
   Voice 0: Microsoft David Desktop
   Voice 1: Microsoft Zira Desktop

🎤 Voice mapping: {'male': 0, 'female': 1, 'narrator': 0, 'default': 0}

🎤 Step 4/5: Generating audio with local TTS...
      ⏱️  Added 0.5s pause
      🎙️  [Hero] (yell): "I will protect everyone!"
          Rate: 234 WPM, Volume: 1.00, Pitch: high
      ⏱️  Added 1.0s pause
      🎙️  [Villain] (angry): "You cannot stop me!"
          Rate: 216 WPM, Volume: 1.00, Pitch: medium

✅ TTS generation completed!
   🎵 Generated 10/10 audio files
   📁 Merged audio: static/audio/job_id/merged_audio.mp3
```

---

## 🎯 Advantages of Local TTS

### 1. **No API Costs**
- Completely free
- Unlimited usage
- No character limits

### 2. **No Account Issues**
- No API keys needed
- No account blocking
- No rate limits

### 3. **Offline Capability**
- Works without internet
- Faster processing
- More reliable

### 4. **Privacy**
- All processing local
- No data sent to cloud
- Complete control

### 5. **Customizable**
- Adjust any parameter
- Add custom voices
- Full control over output

---

## ⚙️ Advanced Configuration

### Add Custom Voices:
1. Install additional SAPI5 voices (Windows)
2. Update `VOICE_INDICES` mapping
3. Restart application

### Adjust Emotion Mapping:
Edit `generate_dialogue_audio()` function to customize how emotions affect speech parameters.

### Custom Timing:
Modify `time_gap_before_s` interpretation in the generation loop.

---

## 🆘 Troubleshooting

### No voices available?
**Windows:** SAPI5 voices should be built-in
**Linux:** Install espeak: `sudo apt-get install espeak`
**macOS:** Voices should be built-in

### Audio quality too low?
- Increase `BASE_WPM` for faster, clearer speech
- Use higher quality system voices
- Adjust `speech.speed` values in Gemini output

### Voices sound robotic?
- This is expected with pyttsx3
- For better quality, consider:
  - Installing premium SAPI5 voices (Windows)
  - Using festival voices (Linux)
  - Adjusting speech parameters

### Merge fails?
- Ensure ffmpeg is installed
- Check all audio files were generated
- Verify pydub is installed correctly

---

## 📝 File Structure

```
static/audio/job_id/
├── silence_p001_seq001.mp3    ← Timing gaps
├── dialogue_p001_seq001.mp3   ← Speech
├── silence_p001_seq002.mp3
├── dialogue_p001_seq002.mp3
├── ...
└── merged_audio.mp3            ← Final merged audio
```

---

## ✅ Summary

### What You Have Now:
- ✅ Local, offline TTS with pyttsx3
- ✅ No API costs or dependencies
- ✅ Automatic voice selection
- ✅ Emotion-based speech adjustment
- ✅ Timing intelligence with pauses
- ✅ Audio merging with pydub
- ✅ Fast, reliable processing

### No Longer Needed:
- ❌ ElevenLabs API key
- ❌ Internet connection
- ❌ API cost concerns
- ❌ Account blocking worries

---

## 🚀 Ready to Use!

```bash
# Install dependencies
pip install pyttsx3 pydub

# Test the system
python test_pipeline.py

# Start server
python main.py

# Upload PDF and generate dubbed video!
```

**Your manga dubbing system is now completely self-contained and free!** 🎉
