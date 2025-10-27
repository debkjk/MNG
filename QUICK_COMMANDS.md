# 🚀 Quick Commands Reference

## Essential Commands

### 🧪 Test Gemini Extraction
```bash
python test_pipeline.py
```
Tests PDF processing and Gemini analysis. Shows extracted dialogues with timing, emotions, and speech settings.

### 🌐 Start Server
```bash
python main.py
```
Starts the web server at http://localhost:8000

### 🧹 Clean Everything
```bash
python cleanup_all.py
```
Removes all static files and resets database to fresh state.

### 📊 Check Database
```bash
sqlite3 database/manga_dubbing.db "SELECT job_id, status, current_operation FROM jobs ORDER BY created_at DESC LIMIT 5;"
```
Shows last 5 jobs with their status.

---

## 📋 Expected JSON Structure

```json
{
  "page_type": "story",
  "page_number": 1,
  "dialogs": [
    {
      "sequence": 1,
      "text": "dialogue text",
      "speaker": "Character Name",
      "time_gap_before_s": 0.5,
      "emotion": {
        "type": "neutral",
        "intensity": 0.5,
        "stability": 0.8,
        "style": 0.3,
        "description": "description"
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

## ✅ Verification Checklist

After running `python test_pipeline.py`, verify:

- ✅ `dialogs` array exists (not `panels`)
- ✅ `time_gap_before_s` field present
- ✅ `emotion` object has all fields
- ✅ `speech` object has speed, volume, pitch
- ✅ `position` object has vertical, horizontal
- ✅ Sequential numbering (1, 2, 3...)
- ❌ NO panel references anywhere

---

## 🎯 TTS Optimization Rules

### YELL/EXCITEMENT:
- `speed`: > 1.0 (e.g., 1.2)
- `volume`: > 1.0 (e.g., 1.1)
- `pitch`: "high"

### CALM/SADNESS:
- `speed`: < 1.0 (e.g., 0.9)
- `volume`: ≈ 1.0
- `pitch`: "medium" or "low"

### WHISPER:
- `speed`: ≈ 1.0
- `volume`: < 1.0 (e.g., 0.8)
- `pitch`: "low"

---

## 📁 File Locations

### Generated Files:
- **Images**: `static/manga_pages/page_001.png`
- **JSON**: `static/manga_pages/page_001.json`
- **Audio**: `static/audio/job_id/dialogue_p001_seq001.mp3`
- **Video**: `static/videos/job_id_manga_dubbed.mp4`

### Test Output:
- **Gemini Test**: `test_gemini_output.json`

---

## 🆘 Troubleshooting

### No dialogues extracted?
- Check if page has text
- Try different PDF with clear English text
- Verify Gemini API key in `.env`

### ElevenLabs blocked?
- Upgrade to paid ($5/month)
- OR use Mock TTS (edit `routers/upload.py` line 7)

### Server won't start?
- Check if port 8000 is available
- Verify `.env` file exists
- Check all dependencies installed

---

## 📊 Value Ranges

| Field | Range | Example |
|-------|-------|---------|
| `time_gap_before_s` | 0.0 - 3.0 | 0.5 |
| `emotion.intensity` | 0.1 - 1.0 | 0.8 |
| `emotion.stability` | 0.1 - 1.0 | 0.8 |
| `emotion.style` | 0.1 - 1.0 | 0.3 |
| `speech.speed` | 0.8 - 1.3 | 1.0 |
| `speech.volume` | 0.8 - 1.2 | 1.0 |
| `speech.pitch` | low/medium/high | medium |

---

## 🎉 Quick Start

```bash
# 1. Clean everything
python cleanup_all.py

# 2. Test Gemini
python test_pipeline.py

# 3. Check output
cat test_gemini_output.json

# 4. Start server
python main.py

# 5. Upload PDF at http://localhost:8000
```

---

**That's it! You're ready to go!** 🚀
