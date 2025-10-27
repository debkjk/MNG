# 🎯 Project Finalization Guide

## Complete Setup & Testing Instructions

---

## 📋 Step 1: Install Dependencies and Verify FFmpeg

### A. Install Python Packages

```bash
# Install pyttsx3 and pydub for local TTS
pip install pyttsx3 pydub

# Or install all dependencies
pip install -r requirements.txt
```

### B. **CRITICAL:** Verify FFmpeg Installation

FFmpeg is required for video generation. Verify it's installed:

```bash
ffmpeg -version
```

**If this command fails:**

#### Windows:
1. Download FFmpeg from: https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to your system PATH
4. Restart terminal and verify: `ffmpeg -version`

#### Linux:
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

#### macOS:
```bash
brew install ffmpeg
```

---

## 🎤 Step 2: Configure Local Voices (Mandatory)

The pyttsx3 library uses different voice indices on different operating systems. You **must** run this script to find the correct indices.

### A. Run Voice Checker

```bash
python check_voices.py
```

**Expected Output:**
```
--- Available Local TTS Voices ---
Index: 0
  Name: Microsoft David Desktop
  Gender/Age: UNKNOWN/Driver Dependent / N/A
  ID: HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_DAVID_11.0

Index: 1
  Name: Microsoft Zira Desktop
  Gender/Age: UNKNOWN/Driver Dependent / N/A
  ID: HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0
----------------------------------

--- Suggested Voice Mapping ---
Male voice detected: Index 0 - Microsoft David Desktop
Female voice detected: Index 1 - Microsoft Zira Desktop

Recommended configuration:
MALE_VOICE_INDEX = 0
FEMALE_VOICE_INDEX = 1
NARRATOR_VOICE_INDEX = 0
----------------------------------
```

### B. Update services/tts_service.py

Open `services/tts_service.py` and update lines 28-30 with the indices from above:

```python
# Voice Indices - UPDATE THESE after running check_voices.py
MALE_VOICE_INDEX = 0      # [e.g., 0 for your male voice]
FEMALE_VOICE_INDEX = 1    # [e.g., 1 for your female voice]
NARRATOR_VOICE_INDEX = 0  # [e.g., 2 for a different, suitable voice]
```

**Example:**
```python
# Voice Indices - UPDATE THESE after running check_voices.py
MALE_VOICE_INDEX = 0      # Microsoft David Desktop
FEMALE_VOICE_INDEX = 1    # Microsoft Zira Desktop
NARRATOR_VOICE_INDEX = 0  # Microsoft David Desktop
```

---

## 🎬 Step 3: Understand the Video Generation

The system now uses a **slideshow approach** for video generation:

### How It Works:

```
1. Extract pages from PDF → static/pages/job_id/page_001.png
2. Analyze with Gemini → Extract dialogues with metadata
3. Generate audio with pyttsx3 → static/audio/job_id/dialogue_*.mp3
4. Merge all audio → static/audio/job_id/merged_audio.mp3
5. Create slideshow video:
   - Each page displays for: total_audio_duration / num_pages
   - FFmpeg stitches pages into video
6. Merge slideshow + audio → static/videos/job_id/final_video.mp4
```

### File Structure:

```
static/
├── pages/
│   └── job_id/
│       ├── page_001.png
│       ├── page_002.png
│       └── ...
├── audio/
│   └── job_id/
│       ├── silence_p001_seq001.mp3
│       ├── dialogue_p001_seq001.mp3
│       ├── silence_p001_seq002.mp3
│       ├── dialogue_p001_seq002.mp3
│       └── merged_audio.mp3
└── videos/
    └── job_id/
        └── final_video.mp4
```

---

## 🧪 Step 4: Run End-to-End Test

### A. Prepare Test Data

Ensure you have a PDF in the `static/uploads/` directory:

```bash
# Check if PDF exists
ls static/uploads/*.pdf
```

### B. Run Complete Pipeline Test

```bash
python test_pipeline.py
```

**Expected Output:**

```
============================================================
🧪 TESTING MANGA DUBBING PIPELINE
============================================================
📄 PDF: MangaTest.pdf

Step 1: Validating PDF...
✅ PDF is valid

Step 2: Converting PDF to images...
✅ Extracted 5 pages
   Page 1: page_001.png
   Page 2: page_002.png
   ...

Step 3: Analyzing with Gemini AI...
   Processing page 1/5...

📊 GEMINI ANALYSIS RESULTS:
============================================================
Total Dialogues: 8

📄 Page 1:
   Type: story
   Dialogues: 8

   1. [Hero] (excitement - intensity: 0.9)
      "Let's go! We can't waste any time!"
      ⏱️  Gap before: 0.5s
      🎤 Speech: speed=1.2, volume=1.1, pitch=high
      📍 Position: top-left

   2. [Narrator] (narration - intensity: 0.5)
      "Meanwhile, in the distant kingdom..."
      ⏱️  Gap before: 2.0s
      🎤 Speech: speed=0.9, volume=0.8, pitch=medium
      📍 Position: middle-center
   ...

💾 Full results saved to: test_gemini_output.json

Step 4: Generating audio with local TTS...

🎤 Available TTS voices: 2
   Voice 0: Microsoft David Desktop
   Voice 1: Microsoft Zira Desktop

🎤 Voice mapping: {'male': 0, 'female': 1, 'narrator': 0, 'default': 0}

🎤 Step 4/5: Generating audio with local TTS...
      ⏱️  Added 0.5s pause
      🎙️  [Hero] (excitement): "Let's go! We can't waste any time!"
          Rate: 216 WPM, Volume: 1.00, Pitch: high
      ⏱️  Added 2.0s pause
      🎙️  [Narrator] (narration): "Meanwhile, in the distant kingdom..."
          Rate: 162 WPM, Volume: 0.80, Pitch: medium
      ...

✅ TTS generation completed!
   🎵 Generated 8/8 audio files
   📁 Merged audio: static/audio/test_pipeline/merged_audio.mp3

✅ Generated 8 audio files
   Merged audio: static/audio/test_pipeline/merged_audio.mp3

Step 5: Generating final video...

🎬 Step 5/5: Generating final video...
   🎵 Audio duration: 45.32 seconds
   📸 Found 1 images to process
   ⏱️  Each image will display for 45.32 seconds
   📝 Creating FFmpeg concat file...

   🎬 Step 1/2: Generating video slideshow from images...
   ✅ Slideshow created successfully

   🎬 Step 2/2: Merging video and audio tracks...

✅ Video generation completed!
   🎥 Final video: static/videos/test_pipeline/final_video.mp4
   📊 Duration: 45.32s, Images: 1

✅ Video created: static/videos/test_pipeline/final_video.mp4

============================================================
📋 SUMMARY:
============================================================
✅ Gemini successfully extracted 8 dialogues
✅ Local TTS audio generation completed
✅ Final video created with slideshow + audio
============================================================

✅ Pipeline test complete!
```

---

## 🎯 Step 5: Verify Output

### Check Generated Files:

```bash
# Check audio files
ls static/audio/test_pipeline/

# Check video file
ls static/videos/test_pipeline/final_video.mp4

# Play the video (Windows)
start static/videos/test_pipeline/final_video.mp4

# Play the video (Linux)
xdg-open static/videos/test_pipeline/final_video.mp4

# Play the video (macOS)
open static/videos/test_pipeline/final_video.mp4
```

### Expected Files:

```
static/audio/test_pipeline/
├── silence_p001_seq001.mp3
├── dialogue_p001_seq001.mp3
├── silence_p001_seq002.mp3
├── dialogue_p001_seq002.mp3
├── ...
└── merged_audio.mp3

static/videos/test_pipeline/
└── final_video.mp4
```

---

## 🚀 Step 6: Run Full Server

Once testing is successful, start the full server:

```bash
python main.py
```

**Expected Output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### Access the Web Interface:

1. Open browser: http://localhost:8000
2. Upload a PDF
3. Wait for processing
4. Download the final dubbed video!

---

## 🔧 Troubleshooting

### Issue: "No TTS voices found"

**Windows:**
- SAPI5 voices should be built-in
- Check: Settings → Time & Language → Speech

**Linux:**
```bash
sudo apt-get install espeak
```

**macOS:**
- Voices should be built-in
- Check: System Preferences → Accessibility → Speech

### Issue: "FFmpeg not found"

```bash
# Verify FFmpeg is in PATH
ffmpeg -version

# If not found, reinstall and add to PATH
```

### Issue: "Audio quality too low"

Edit `services/tts_service.py`:
```python
BASE_WPM = 200  # Increase for faster, clearer speech (default: 180)
```

### Issue: "Video generation fails"

Check FFmpeg is working:
```bash
ffmpeg -version
```

Verify audio file exists:
```bash
ls static/audio/job_id/merged_audio.mp3
```

Verify image files exist:
```bash
ls static/pages/job_id/*.png
```

### Issue: "Voices sound robotic"

This is expected with pyttsx3. For better quality:
- **Windows:** Install premium SAPI5 voices
- **Linux:** Use festival voices
- **macOS:** Built-in voices are already good quality

---

## 📊 Performance Benchmarks

### Typical Processing Times:

| Step | Duration | Notes |
|------|----------|-------|
| PDF → Images | 1-2s per page | Fast |
| Gemini Analysis | 5-10s per page | API dependent |
| TTS Generation | 0.5-1s per dialogue | Very fast (local) |
| Video Merge | 2-5s | FFmpeg dependent |

### Example: 10-page manga with 50 dialogues

```
PDF Processing:    ~15 seconds
Gemini Analysis:   ~60 seconds
TTS Generation:    ~30 seconds
Video Generation:  ~5 seconds
------------------------
Total:             ~110 seconds (~2 minutes)
```

---

## ✅ Checklist

Before deploying, ensure:

- [ ] FFmpeg is installed and accessible
- [ ] pyttsx3 and pydub are installed
- [ ] Voice indices are configured in `tts_service.py`
- [ ] `check_voices.py` runs successfully
- [ ] `test_pipeline.py` completes without errors
- [ ] Final video plays correctly
- [ ] Gemini API key is set in `.env`
- [ ] All directories have proper permissions

---

## 🎉 Success Criteria

Your system is ready when:

1. ✅ `check_voices.py` shows available voices
2. ✅ `test_pipeline.py` generates a complete video
3. ✅ Video file exists and plays correctly
4. ✅ Audio is synchronized with page display
5. ✅ No errors in console output

---

## 📝 Next Steps

Once finalized:

1. **Test with multiple PDFs** - Verify robustness
2. **Adjust timing** - Fine-tune `time_gap_before_s` in Gemini prompt
3. **Optimize quality** - Adjust `BASE_WPM` and voice settings
4. **Add features** - Subtitles, transitions, effects
5. **Deploy** - Host on server for production use

---

## 🆘 Support

If you encounter issues:

1. Check logs in console output
2. Verify all dependencies are installed
3. Ensure FFmpeg is accessible
4. Check file permissions
5. Review error messages carefully

**Common fixes:**
- Restart terminal after installing FFmpeg
- Update pip: `pip install --upgrade pip`
- Clear cache: Delete `static/` folders and retry
- Check API quota: Gemini API limits

---

## 🎯 Summary

### What You Have:
- ✅ Local, offline TTS with pyttsx3
- ✅ Automatic voice selection
- ✅ Emotion-based speech adjustment
- ✅ Timing intelligence with pauses
- ✅ FFmpeg-based video generation
- ✅ Complete end-to-end pipeline
- ✅ No API costs for TTS

### What You Need:
- ✅ FFmpeg installed
- ✅ Voice indices configured
- ✅ Gemini API key (for analysis only)

**Your manga dubbing system is production-ready!** 🎉
