# Complete Logging Guide - See What's Happening

## ✅ Enhanced Logging is Now Active!

I've added comprehensive logging to your backend. Here's what you'll see:

---

## 📺 Terminal Logs (What You'll See)

### When You Upload a PDF:

```
============================================================
🚀 STARTING JOB: 81323e4b-d2d8-44ba-8af2-a400a5098490
📄 PDF File: MangaTest_removed.pdf
============================================================

✅ Step 1/4: Validating PDF...
✅ PDF validation successful

📸 Step 2/4: Converting PDF to images...
✅ Extracted 5 pages from PDF

🤖 Step 3/4: Analyzing pages with Gemini AI...
   📄 Analyzing page 1/5...
   ✅ Page 1: Found 3 panels, 8 dialogues
   📄 Analyzing page 2/5...
   ✅ Page 2: Found 4 panels, 12 dialogues
   📄 Analyzing page 3/5...
   ✅ Page 3: Found 2 panels, 6 dialogues
   📄 Analyzing page 4/5...
   ✅ Page 4: Found 3 panels, 9 dialogues
   📄 Analyzing page 5/5...
   ✅ Page 5: Found 2 panels, 5 dialogues

✅ Gemini analysis completed!
   📊 Total: 14 panels, 40 dialogues

🎤 Step 4/4: Generating audio with ElevenLabs...
      🎙️  Narrator: "Welcome to the story..."
      🎙️  Hero: "I will protect everyone!"
      🎙️  Villain: "You cannot stop me!"
      ... (continues for each dialogue)

✅ TTS generation completed!
   🎵 Generated 40/40 audio files
   📁 Merged audio: static/audio/job_id/merged_audio.mp3

🎬 Step 5/5: Creating final video...

✅ Video generation completed!
   🎥 Video saved: static/videos/job_id_manga_dubbed.mp4

============================================================
🎉 JOB COMPLETED SUCCESSFULLY: 81323e4b-d2d8-44ba-8af2-a400a5098490
============================================================
```

---

## ❌ If ElevenLabs API Fails:

```
🎤 Step 4/4: Generating audio with ElevenLabs...
      🎙️  Narrator: "Welcome to the story..."
ERROR:root:Failed to generate audio for dialogue: status_code: 401
ERROR:root:Failed to generate audio for dialogue: status_code: 401
ERROR:root:Failed to generate audio for dialogue: status_code: 401

============================================================
❌ JOB FAILED: 81323e4b-d2d8-44ba-8af2-a400a5098490
============================================================
Error: Processing failed: No audio files were successfully generated

Full traceback:
  File "routers/upload.py", line 127, in process_manga_pipeline
    tts_results = generate_audio_tracks(all_analysis_results, job_id)
  File "services/tts_service.py", line 309, in generate_audio_tracks
    raise Exception("No audio files were successfully generated")
============================================================
```

**This tells you**: ElevenLabs API is blocking your requests (401 = Unauthorized)

---

## 🌐 Web Interface Logs

The web interface now shows:

### Progress Bar
```
Processing: 60%
Page 3 of 5
```

### Current Operation
```
Analyzing page 3/5 with Gemini
```

### Log Viewer (New!)
```
📋 Processing Log:
[10:45:23] Validating PDF
[10:45:24] Converting PDF to images
[10:45:26] ✅ Extracted 5 pages from PDF
[10:45:27] Analyzing page 1/5 with Gemini
[10:45:30] 📄 Processing page 1/5
[10:45:32] Analyzing page 2/5 with Gemini
[10:45:35] 📄 Processing page 2/5
[10:45:37] Generating audio with ElevenLabs
[10:45:40] Creating video with subtitles
[10:45:45] 🎉 Processing completed successfully!
```

---

## 🔍 How to Monitor Your Job

### Option 1: Watch Terminal (Recommended)

Just keep your terminal open where you ran `python main.py`. You'll see:
- ✅ Green checkmarks for successful steps
- ❌ Red X marks for failures
- 📊 Statistics (panels found, dialogues extracted)
- 🎙️ Each dialogue being processed
- 🎉 Success message or ❌ error details

### Option 2: Check Web Interface

1. Upload PDF
2. Watch the "Processing Log" section
3. See real-time updates every 5 seconds

### Option 3: Check Database

```bash
sqlite3 database/manga_dubbing.db "SELECT job_id, status, current_operation, error_message FROM jobs ORDER BY created_at DESC LIMIT 1;"
```

---

## 📊 Understanding the Logs

### Step 1: PDF Validation
```
✅ Step 1/4: Validating PDF...
✅ PDF validation successful
```
**What it means**: PDF file is valid and can be processed

**If it fails**: PDF is corrupted or not a valid PDF file

### Step 2: PDF to Images
```
📸 Step 2/4: Converting PDF to images...
✅ Extracted 5 pages from PDF
```
**What it means**: PDF converted to 5 image files

**If it fails**: PDF might be encrypted or have unsupported format

### Step 3: Gemini Analysis
```
🤖 Step 3/4: Analyzing pages with Gemini AI...
   📄 Analyzing page 1/5...
   ✅ Page 1: Found 3 panels, 8 dialogues
```
**What it means**: 
- Gemini AI is reading the manga
- Found 3 speech bubbles/panels
- Extracted 8 lines of dialogue
- Detected emotions and speakers

**If it fails**: 
- Gemini API key invalid
- Gemini API quota exceeded
- Image quality too low

### Step 4: TTS Generation
```
🎤 Step 4/4: Generating audio with ElevenLabs...
      🎙️  Narrator: "Welcome to the story..."
      🎙️  Hero: "I will protect everyone!"
```
**What it means**: 
- Each dialogue is being converted to audio
- You can see which character is speaking
- Shows first 60 characters of each dialogue

**If it fails**:
- ❌ `status_code: 401` = API key invalid or account blocked
- ❌ `status_code: 429` = Rate limit exceeded
- ❌ `status_code: 402` = Quota exceeded

### Step 5: Video Creation
```
🎬 Step 5/5: Creating final video...
✅ Video generation completed!
   🎥 Video saved: static/videos/job_id_manga_dubbed.mp4
```
**What it means**: 
- Combining images + audio + subtitles
- Creating final MP4 video

**If it fails**: 
- FFmpeg not installed
- Disk space full
- Audio files missing

---

## 🚨 Common Error Messages & Solutions

### Error: "401 Unauthorized" (ElevenLabs)
```
ERROR:root:Failed to generate audio for dialogue: status_code: 401
```
**Problem**: ElevenLabs API key is invalid or account is blocked

**Solutions**:
1. Check `.env` file has correct API key
2. Verify API key at https://elevenlabs.io/app/settings
3. Account might be flagged - see `ELEVENLABS_BLOCKED_SOLUTION.md`

### Error: "No audio files were successfully generated"
```
Exception: No audio files were successfully generated
```
**Problem**: All TTS requests failed

**Solutions**:
1. Check ElevenLabs API key
2. Check internet connection
3. Enable Mock TTS for testing (see `ELEVENLABS_BLOCKED_SOLUTION.md`)

### Error: "Invalid PDF format"
```
❌ PDF validation failed
```
**Problem**: PDF file is corrupted or encrypted

**Solutions**:
1. Try a different PDF
2. Ensure PDF is not password-protected
3. Re-download the PDF file

### Error: "Gemini API error"
```
ERROR:root:Gemini API error: ...
```
**Problem**: Gemini API issue

**Solutions**:
1. Check `.env` file has `GEMINI_API_KEY`
2. Verify API key at https://makersuite.google.com/app/apikey
3. Check Gemini API quota

---

## 📝 Log Files Location

### Terminal Logs
- Displayed in real-time in your terminal
- Not saved to file by default

### Database Logs
```bash
# Check job status
sqlite3 database/manga_dubbing.db "SELECT * FROM jobs WHERE job_id='your-job-id';"

# See all jobs
sqlite3 database/manga_dubbing.db "SELECT job_id, status, current_operation, created_at FROM jobs ORDER BY created_at DESC;"
```

### Application Logs (If Enabled)
If you want to save logs to a file, add this to `main.py`:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('manga_dubbing.log'),
        logging.StreamHandler()
    ]
)
```

---

## 🎯 What to Watch For

### ✅ Success Indicators:
- Green checkmarks (✅) at each step
- "COMPLETED SUCCESSFULLY" message
- Video file path shown
- No error messages

### ⚠️ Warning Signs:
- Yellow warnings (⚠️)
- "Using default voice for unknown speaker"
- "Character config not loaded"
- These are OK - job will still complete

### ❌ Failure Indicators:
- Red X marks (❌)
- "FAILED" message
- Error tracebacks
- "status_code: 401" or "status_code: 429"

---

## 🔧 Testing Your New API Key

### Step 1: Restart Server
```bash
# Stop server (CTRL+C)
python main.py
```

### Step 2: Upload Test PDF
- Use a 1-page PDF first
- Watch terminal for logs

### Step 3: Check for Success
Look for these messages:
```
✅ PDF validation successful
✅ Extracted 1 pages from PDF
✅ Page 1: Found X panels, Y dialogues
✅ Gemini analysis completed!
🎤 Step 4/4: Generating audio with ElevenLabs...
      🎙️  Character: "Dialogue text..."
✅ TTS generation completed!
🎉 JOB COMPLETED SUCCESSFULLY
```

### Step 4: If You See Errors
```
ERROR:root:Failed to generate audio for dialogue: status_code: 401
```
**This means**: New API key is also blocked or invalid

**Next steps**:
1. Double-check API key in `.env` file
2. Verify key works at https://elevenlabs.io/app/settings
3. Try the "Test Voice" button on ElevenLabs website
4. If still blocked, consider:
   - Upgrading to paid plan ($5/month)
   - Using Mock TTS for testing
   - Switching to Google Cloud TTS

---

## 💡 Pro Tips

### 1. Keep Terminal Visible
Always keep the terminal window visible while processing. You'll see exactly what's happening.

### 2. Test with 1-Page PDF First
Don't start with a 50-page manga. Test with 1 page to verify everything works.

### 3. Check Logs Immediately
If job fails, scroll up in terminal to see where it failed.

### 4. Save Important Logs
If you get an error, copy the terminal output and save it. Useful for debugging.

### 5. Monitor API Usage
- ElevenLabs: https://elevenlabs.io/app/usage
- Gemini: https://makersuite.google.com/app/apikey

---

## 🆘 Quick Troubleshooting

### Job Status Shows "Processing" Forever
**Check terminal** - might have failed but status not updated

### No Logs Appearing
**Restart server** - `python main.py`

### "Internal Server Error" on Upload
**Check terminal** - will show the actual error

### Can't See Emoji in Terminal
**Windows**: Use Windows Terminal (not CMD)
**Mac/Linux**: Should work by default

---

## 📞 Current Status Check

Run this now to see your current jobs:

```bash
sqlite3 database/manga_dubbing.db "SELECT job_id, status, current_operation, error_message, created_at FROM jobs ORDER BY created_at DESC LIMIT 5;"
```

This shows your last 5 jobs with their status and any error messages.

---

## ✅ Summary

**You now have**:
- ✅ Detailed terminal logs with emojis
- ✅ Step-by-step progress tracking
- ✅ Real-time dialogue processing logs
- ✅ Clear error messages with solutions
- ✅ Success/failure indicators
- ✅ Web interface progress updates

**To test**:
1. Restart server: `python main.py`
2. Upload a 1-page PDF
3. Watch terminal for detailed logs
4. Check if ElevenLabs API works

**If ElevenLabs still blocked**:
See `ELEVENLABS_BLOCKED_SOLUTION.md` for solutions

---

**Your logging is now production-ready!** 🎉
