# Quick Start Guide - After Refactoring

## What Was Fixed

### ✅ Critical Issues Resolved:
1. **Code Duplicates in `main.py`** - Removed conflicting route definitions
2. **Audio Overlap Bug** - Fixed dialogue audio to play sequentially instead of overlapping
3. **Dead Code Removed** - Cleaned up 200+ lines of unused functions
4. **Error Handling** - Added graceful handling for missing panels/audio

---

## How to Test Multi-Page PDF Processing

### Step 1: Start the Server

```bash
cd c:\Users\ASUS\OneDrive\Desktop\Manga\manga-dubbing-backend
python main.py
```

You should see:
```
Database initialized successfully
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Open Web Interface

Open your browser to: **http://localhost:8000**

### Step 3: Upload a Test PDF

1. Click "Choose PDF File"
2. Select a manga PDF (start with 2-3 pages)
3. Click "Upload and Process"
4. Watch the status updates

### Step 4: Monitor Progress

The interface will show:
- **Queued** → **Processing** → **Completed**
- Current operation (e.g., "Analyzing page 2/5")
- Progress updates every 5 seconds

### Step 5: Download and Verify

1. When status shows "Completed", video player appears
2. Play the video in browser
3. **Check**: Audio should play sequentially (not overlapping)
4. Click "Download Video" to save

---

## What to Look For

### ✅ Good Signs:
- Status updates smoothly from queued → processing → completed
- Logs show: "Gemini analysis completed... Found X panels with Y dialogues"
- Logs show: "TTS generation completed... Generated X audio files"
- Logs show: "Video generation completed"
- Video plays with sequential audio

### ⚠️ Warning Signs (Non-Critical):
- "Panel image not found" - Panel skipped, processing continues
- "Skipping panel without dialogues" - Expected for action-only panels
- "Audio file not found for dialogue" - Uses default duration, continues

### ❌ Error Signs (Critical):
- Job status stuck in "processing" for >5 minutes
- Status changes to "failed" with error message
- Server crashes or restarts
- No video file generated

---

## Console Logs to Monitor

### Expected Log Flow:

```
1. Upload Phase:
   "Upload failed" or success message

2. PDF Processing:
   "Converted page 1/5 for job {id}"
   "Converted page 2/5 for job {id}"
   ...

3. Gemini Analysis:
   "Page 1 analyzed in 2.5s for job {id}"
   "Processed page 1/5 with 3 panels for job {id}"
   "Gemini analysis completed for job {id}. Found 15 panels with 42 dialogues"

4. TTS Generation:
   "Starting audio generation for job {id}"
   "Generated audio for dialogue: Hello..."
   "TTS generation completed for job {id}. Generated 42 audio files"

5. Video Creation:
   "Starting video generation for job {id}"
   "Video generation completed for job {id}. Video saved to: ..."
   "Job {id} completed successfully"
```

---

## Troubleshooting

### Problem: Job Stuck in "Processing"

**Check**:
1. Look at console logs for errors
2. Check if Gemini API key is valid
3. Check if ElevenLabs API key is valid
4. Verify internet connection

**Solution**:
- Restart server
- Check `.env` file has correct API keys
- Try with smaller PDF (1-2 pages)

### Problem: "Audio file not found" Warnings

**This is OK** - The system will:
- Use default 2-second duration
- Continue processing other dialogues
- Still generate video

**Only worry if ALL dialogues fail**

### Problem: Video Has No Audio

**Check**:
1. ElevenLabs API key is valid
2. Logs show "TTS generation completed"
3. Files exist in `static/audio/{job_id}/`

**Solution**:
- Verify API key in `.env`
- Check API quota (free tier: 10,000 chars/month)

### Problem: Video Quality is Poor

**Expected**: 
- Resolution: 1920x1080
- Frame rate: 30 fps
- Audio: AAC 192kbps

**If quality is bad**:
- Check source PDF quality
- Verify FFmpeg is installed correctly

---

## File Structure After Processing

```
static/
├── uploads/
│   └── {job_id}.pdf          # Original PDF
├── pages/
│   └── {job_id}/
│       ├── page_000.png      # Extracted pages
│       ├── page_001.png
│       └── ...
├── panels/
│   └── {job_id}/
│       ├── panel_p001_r01.png  # Cropped panels
│       ├── panel_p001_r02.png
│       └── ...
├── audio/
│   └── {job_id}/
│       ├── dialogue_p000_r01_d00.mp3  # Individual audio
│       ├── dialogue_p000_r01_d01.mp3
│       ├── ...
│       └── merged_audio.mp3           # Concatenated audio
└── videos/
    └── {job_id}/
        └── final_video.mp4    # Final output ✅
```

---

## API Endpoints

### Upload PDF
```bash
curl -X POST -F "file=@manga.pdf" http://localhost:8000/api/upload
# Returns: {"job_id": "uuid-string"}
```

### Check Status
```bash
curl http://localhost:8000/api/status/{job_id}
# Returns: {"status": "processing", "current_page": 2, "total_pages": 5, ...}
```

### Download Video
```bash
curl -O http://localhost:8000/api/download/{job_id}
# Downloads: final_video.mp4
```

---

## Performance Benchmarks

### Expected Processing Time (5-page manga):

| Phase | Time | Notes |
|-------|------|-------|
| PDF → Images | 5-10s | Fast |
| Gemini Analysis | 10-25s | 2-5s per page |
| TTS Audio | 20-50s | 1-2s per dialogue |
| Video Creation | 10-20s | Depends on panels |
| **Total** | **45-105s** | ~1-2 minutes |

### Memory Usage:
- Small PDF (1-3 pages): ~300-500 MB
- Medium PDF (5-10 pages): ~500 MB - 1 GB
- Large PDF (20+ pages): 1-2 GB

---

## Next Steps After Testing

### If Everything Works:
1. ✅ Test with larger PDFs (10+ pages)
2. ✅ Test edge cases (title pages, no dialogue, etc.)
3. ✅ Monitor memory usage with large files
4. ✅ Consider adding unit tests
5. ✅ Deploy to production

### If Issues Found:
1. Check `CODEBASE_ANALYSIS.md` for detailed architecture
2. Check `REFACTORING_SUMMARY.md` for what was changed
3. Review logs for specific error messages
4. Open issue with:
   - PDF page count
   - Error message
   - Console logs
   - Job ID

---

## Documentation Files

1. **`CODEBASE_ANALYSIS.md`** - Detailed analysis of structure and issues
2. **`REFACTORING_SUMMARY.md`** - What was changed and why
3. **`QUICK_START.md`** (this file) - How to test and use
4. **`README.md`** - Original project documentation

---

## Support

### Common Questions:

**Q: Can I process multiple PDFs at once?**
A: Yes, each upload creates a separate job that processes in background.

**Q: How do I know which character voice is used?**
A: Check `static/config/characters.json` for voice mappings.

**Q: Can I customize emotions or voices?**
A: Yes, edit `static/config/characters.json` and restart server.

**Q: What manga formats are supported?**
A: Only PDF format. Images must be embedded in PDF.

**Q: Is there a page limit?**
A: No hard limit, but memory usage increases with page count.

---

## Quick Commands

```bash
# Start server
python main.py

# Check if server is running
curl http://localhost:8000/health

# View logs in real-time (if using systemd)
journalctl -u manga-dubbing -f

# Clean up old jobs (manual)
python clean_outputs.py

# Check database
sqlite3 manga_dubbing.db "SELECT * FROM jobs ORDER BY created_at DESC LIMIT 5;"
```

---

## Success! 🎉

If you can:
- ✅ Upload a 5-page PDF
- ✅ See it process through all pages
- ✅ Download a video with sequential audio
- ✅ Play the video without issues

**Then the refactoring was successful!**

The main goal was to fix multi-page PDF processing, and that should now work correctly.
