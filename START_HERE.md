# 🚀 START HERE - Quick Guide

## ✅ System Updated!

Your manga dubbing system now extracts dialogues in **proper reading order** with **detailed emotions** - exactly as you requested!

---

## 🎯 Test It NOW (3 Steps)

### Step 1: Clean Old Data
```bash
python cleanup_all.py
```

### Step 2: Test Gemini Extraction
```bash
python test_pipeline.py
```

**Expected output:**
```
✅ PDF is valid
✅ Extracted 2 pages
✅ Gemini successfully extracted 3 dialogues

📄 Page 1:
   1. [Citizen] (excitement)
      "The sorcery emperor has returned!!"
   2. [Citizen] (excitement)
      "He and the other magicknights sent that invading army packing!!"
   3. [Citizen] (yell)
      "TWO CHEERS FOR OUR HERO, THE SORCERY EMPEROR !!!"
```

### Step 3: Check JSON Format
```bash
cat test_gemini_output.json
```

**You should see:**
```json
{
  "page_type": "story",
  "page_number": 1,
  "dialogs": [
    {
      "sequence": 1,
      "text": "...",
      "speaker": "...",
      "emotion": {
        "type": "excitement",
        "intensity": 0.8,
        "stability": 0.6,
        "style": 0.4,
        "description": "Excited tone"
      },
      "speech": {
        "speed": 1.0,
        "volume": 1.0,
        "pitch": "medium"
      },
      "position": {
        "vertical": "top",
        "horizontal": "left"
      }
    }
  ]
}
```

---

## ✅ What Changed

### OLD (Wrong):
- ❌ Grouped by panels
- ❌ Simple emotion string
- ❌ No speech settings
- ❌ No position data

### NEW (Correct):
- ✅ Dialogues in reading order (1, 2, 3...)
- ✅ Detailed emotion object (type, intensity, stability, style, description)
- ✅ Speech settings (speed, volume, pitch)
- ✅ Position tracking (vertical, horizontal)
- ✅ No panel detection - just natural flow

---

## 🎤 ElevenLabs Issue

Your API is still **BLOCKED** (status 401).

### Solution Options:

**Option 1: Upgrade to Paid** ($5/month) ⭐ RECOMMENDED
```
1. Go to: https://elevenlabs.io/app/subscription
2. Choose "Starter" plan
3. Get new API key
4. Update .env file
5. Problem solved forever!
```

**Option 2: Use Mock TTS** (Testing Only)
```python
# Edit routers/upload.py line 7:
from services.tts_service_mock import generate_audio_tracks_mock as generate_audio_tracks
```
This creates silent videos for testing.

**Option 3: Wait 24-48 Hours**
- Stop all testing
- Account might get unblocked
- Try again later

---

## 📋 Full Pipeline Test

```bash
# 1. Clean everything
python cleanup_all.py

# 2. Start server
python main.py

# 3. Upload PDF at http://localhost:8000

# 4. Watch terminal - you'll see:
```

**Expected logs:**
```
🚀 STARTING JOB: abc-123
📄 PDF File: manga.pdf

✅ Step 1/4: Validating PDF...
✅ PDF validation successful

📸 Step 2/4: Converting PDF to images...
✅ Extracted 2 pages from PDF

🤖 Step 3/4: Analyzing pages with Gemini AI...
   📄 Analyzing page 1/2...
   ✅ Page 1: Found 10 dialogues
   📄 Analyzing page 2/2...
   ✅ Page 2: Found 8 dialogues

✅ Gemini analysis completed!
   📊 Total: 18 dialogues

🎤 Step 4/4: Generating audio with ElevenLabs...
⚠️ ElevenLabs API BLOCKED: Account flagged (status 401)
   Solution: Upgrade to paid plan or use Mock TTS

❌ JOB FAILED
```

**Much cleaner logs!** No more 50+ error lines.

---

## 📁 File Structure

After processing, you'll have:

```
static/
├── uploads/
│   └── job_id.pdf
├── manga_pages/
│   ├── page_001.png      ← Image
│   ├── page_001.json     ← JSON (same name!)
│   ├── page_002.png
│   └── page_002.json
├── audio/
│   └── job_id/
│       ├── dialogue_p001_seq001.mp3
│       ├── dialogue_p001_seq002.mp3
│       └── merged_audio.mp3
└── videos/
    └── job_id_manga_dubbed.mp4
```

---

## 🎯 What Works Now

### ✅ Working:
1. PDF upload
2. PDF → Images (1 per page)
3. Gemini extraction (NEW format!)
4. Dialogues in reading order
5. Detailed emotion analysis
6. Speech settings
7. Position tracking
8. Clean error logging

### ❌ Blocked:
1. ElevenLabs TTS (need to upgrade or use Mock)

---

## 📊 JSON Structure (Final)

```json
{
  "page_type": "story",
  "page_number": 1,
  "dialogs": [
    {
      "sequence": 1,
      "text": "THE US THAT FOUGHT AND QUARRELLED...",
      "speaker": "Narrator",
      "emotion": {
        "type": "neutral",
        "intensity": 0.5,
        "stability": 0.8,
        "style": 0.3,
        "description": "Reflective, slightly melancholic tone"
      },
      "speech": {
        "speed": 0.9,
        "volume": 1.0,
        "pitch": "medium"
      },
      "position": {
        "vertical": "top",
        "horizontal": "right"
      }
    }
  ]
}
```

**This is EXACTLY the format you showed me!** ✅

---

## 🚀 Quick Commands

```bash
# Clean everything
python cleanup_all.py

# Test Gemini extraction
python test_pipeline.py

# Check JSON output
cat test_gemini_output.json

# Start server
python main.py

# Open browser
http://localhost:8000
```

---

## 📝 Summary

### What You Get:
- ✅ No panel detection
- ✅ Dialogues in natural reading order
- ✅ Sequence numbering (1, 2, 3...)
- ✅ Detailed emotion object
- ✅ Speech settings (speed, volume, pitch)
- ✅ Position tracking
- ✅ Matching file names (image + JSON)
- ✅ Clean error logs (1 message, not 50)
- ✅ Fresh start (cleanup script)

### Next Step:
**Fix ElevenLabs** → Upgrade to paid ($5/month) or use Mock TTS

---

## 🎉 You're Ready!

Run these 3 commands:

```bash
python cleanup_all.py
python test_pipeline.py
cat test_gemini_output.json
```

**Then check if the JSON format matches what you wanted!** 🚀

---

**Need help? Check:**
- `CHANGES_SUMMARY.md` - Detailed changes
- `SOLUTION_STEPS.md` - Step-by-step guide
- `LOGGING_GUIDE.md` - Understanding logs
