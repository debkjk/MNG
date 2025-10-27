# ⚡ Quick Start Guide

## 🚀 Get Started in 3 Minutes

---

## Step 1: Install Dependencies (30 seconds)

```bash
# Install Python packages
pip install pyttsx3 pydub

# Verify FFmpeg
ffmpeg -version
```

**If FFmpeg not found:** Download from https://ffmpeg.org/download.html and add to PATH

---

## Step 2: Configure Voices (1 minute)

```bash
# Check available voices
python check_voices.py
```

**Copy the recommended indices** and update `services/tts_service.py` lines 28-30:

```python
MALE_VOICE_INDEX = 0      # Your male voice index
FEMALE_VOICE_INDEX = 1    # Your female voice index
NARRATOR_VOICE_INDEX = 0  # Your narrator voice index
```

---

## Step 3: Test Pipeline (1 minute)

```bash
# Run complete test
python test_pipeline.py
```

**Expected:** Video file created at `static/videos/test_pipeline/final_video.mp4`

---

## Step 4: Start Server (30 seconds)

```bash
# Start the server
python main.py
```

**Open browser:** http://localhost:8000

---

## 🎯 That's It!

Upload a PDF → Wait for processing → Download dubbed video!

---

## 📋 Essential Commands

### Development:
```bash
# Test pipeline
python test_pipeline.py

# Check voices
python check_voices.py

# Clean up files
python cleanup_all.py

# Start server
python main.py
```

### Verification:
```bash
# Check FFmpeg
ffmpeg -version

# Check dependencies
pip list | grep -E "pyttsx3|pydub|google-generativeai"

# Check generated files
ls static/videos/*/final_video.mp4
ls static/audio/*/merged_audio.mp3
```

### Troubleshooting:
```bash
# Reinstall dependencies
pip install --upgrade pyttsx3 pydub

# Clear cache
python cleanup_all.py

# Check logs
python test_pipeline.py 2>&1 | tee test.log
```

---

## 🎤 Voice Configuration Quick Reference

| OS | Default Voices | Command |
|----|----------------|---------|
| **Windows** | David (M), Zira (F) | Built-in SAPI5 |
| **Linux** | espeak voices | `sudo apt-get install espeak` |
| **macOS** | Alex, Samantha | Built-in |

---

## 📊 File Structure

```
static/
├── uploads/        ← Upload PDFs here
├── pages/          ← Extracted page images
├── audio/          ← Generated audio files
└── videos/         ← Final dubbed videos
```

---

## ⚠️ Common Issues

| Issue | Solution |
|-------|----------|
| FFmpeg not found | Install and add to PATH |
| No voices found | Install espeak (Linux) or check OS settings |
| Audio quality low | Increase `BASE_WPM` in `tts_service.py` |
| Video fails | Check FFmpeg and image files exist |

---

## 🎯 Success Checklist

- [ ] FFmpeg installed: `ffmpeg -version` ✅
- [ ] Voices configured: `python check_voices.py` ✅
- [ ] Test passes: `python test_pipeline.py` ✅
- [ ] Video plays: Open `static/videos/test_pipeline/final_video.mp4` ✅
- [ ] Server runs: `python main.py` ✅

---

## 📚 Full Documentation

- **Complete Guide:** `FINALIZATION_GUIDE.md`
- **Local TTS Details:** `LOCAL_TTS_GUIDE.md`
- **Project Structure:** `FINAL_STRUCTURE.md`

---

**Ready to dub some manga!** 🎉
