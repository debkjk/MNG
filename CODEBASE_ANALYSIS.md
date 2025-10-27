# Manga Dubbing Backend - Codebase Analysis & Refactoring Plan

## Executive Summary

**Project Goal**: Convert manga PDFs into dubbed videos with emotion-based TTS and synchronized audio/video.

**Current Status**: 
- ✅ Single-page video generation works
- ❌ Multi-page PDF processing has errors
- ⚠️ Code duplication and structural issues present

---

## 1. Critical Issues Found

### 1.1 Code Duplication in `main.py`

**Problem**: Multiple duplicate definitions causing conflicts

```python
# Lines 16-24: First lifespan definition
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

# Lines 96-104: DUPLICATE lifespan definition (UNUSED)
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

# Lines 61-64: First root endpoint
@app.get("/")
async def root():
    return FileResponse(static_path / "index.html")

# Lines 71-81: DUPLICATE root endpoint (OVERRIDES first one)
@app.get("/")
async def root():
    return {"service": "AI Manga Dubbing Platform API", ...}

# Lines 53-54: First static mount
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Lines 67-68: DUPLICATE static mount (CONFLICTS)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Lines 57-59: First router includes
from routers import upload, process
app.include_router(upload.router)
app.include_router(process.router)

# Lines 107-110: DUPLICATE router includes (CONFLICTS)
from routers import upload, process, download
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(process.router, prefix="/api", tags=["status"])
app.include_router(download.router, prefix="/api", tags=["download"])
```

**Impact**: 
- Routing conflicts (some endpoints may not work)
- Static files served from wrong location
- Confusion about which code is active

---

### 1.2 Video Generator Service Issues

**Problem**: Two different video generation functions with incompatible signatures

```python
# Function 1: create_manga_video (lines 23-142)
def create_manga_video(analysis_results: Dict[str, Any], job_id: str) -> str:
    # Used by upload.py pipeline
    # Processes multiple pages/panels
    # Returns string path

# Function 2: generate_manga_video (lines 310-349) 
async def generate_manga_video(
    page_image_path: Path,
    dialogs_json_path: Path,
    audio_dir: Path,
    output_dir: Path = VIDEOS_DIR
) -> Path:
    # ASYNC function (not used anywhere)
    # Single page processing
    # Returns Path object
```

**Impact**:
- `generate_manga_video` is NEVER called (dead code)
- `generate_video.py` script tries to use the wrong function
- Confusion about which function to use

---

### 1.3 Multi-Page Processing Logic Issues

**Problem**: Video generation doesn't properly handle multi-page scenarios

In `video_generator.py` `create_manga_video()`:
```python
# Lines 42-110: Processes pages and panels
for page in analysis_results.get("pages", []):
    panels = page.get("panels", [])
    for panel in sorted_panels:
        # Creates individual clips for each panel
        # BUT: Audio handling is per-dialogue, not per-panel
        # ISSUE: Multiple dialogues in one panel create overlapping audio
```

**Issues**:
1. Audio clips are created per dialogue but should be concatenated per panel
2. No silence/padding between panels from different pages
3. Panel duration calculation doesn't account for multiple dialogues properly
4. Missing error handling for panels without images

---

### 1.4 Database Path Inconsistency

**Problem**: Database file location confusion

```python
# database/database.py line 7
DATABASE_PATH = Path(__file__).resolve().parent.parent / 'database' / 'manga_dubbing.db'
# Results in: manga-dubbing-backend/database/manga_dubbing.db

# But manga_dubbing.db exists at ROOT level (from ls output)
# manga-dubbing-backend/manga_dubbing.db
```

**Impact**: May create duplicate databases or fail to find existing data

---

## 2. Architecture Analysis

### 2.1 Current Structure

```
manga-dubbing-backend/
├── main.py                    # FastAPI app (HAS DUPLICATES)
├── generate_video.py          # CLI script (BROKEN - wrong function call)
├── routers/
│   ├── upload.py             # Upload + background processing ✅
│   ├── process.py            # Status check + extract-dialogs ✅
│   └── download.py           # Video download ✅
├── services/
│   ├── pdf_processor.py      # PDF → Images ✅
│   ├── gemini_service.py     # AI analysis ✅
│   ├── tts_service.py        # Audio generation ✅
│   ├── video_generator.py    # Video creation (HAS ISSUES)
│   └── db_service.py         # Database ops ✅
├── database/
│   ├── database.py           # DB connection ✅
│   ├── init_db.py            # Schema init
│   └── migrate_db.py         # Migrations
└── static/
    ├── uploads/              # PDF storage
    ├── pages/                # Extracted page images
    ├── panels/               # Cropped panel images
    ├── audio/                # Generated audio
    └── videos/               # Final videos
```

### 2.2 Processing Pipeline

```
1. Upload PDF → /api/upload
   ├── Save to static/uploads/
   ├── Create job in DB (status: queued)
   └── Trigger background task

2. Background Processing (process_manga_pipeline)
   ├── Validate PDF
   ├── Convert PDF → Images (static/pages/{job_id}/)
   ├── For each page:
   │   ├── Gemini analysis (panels, dialogues, emotions)
   │   └── Extract panel images (static/panels/{job_id}/)
   ├── Generate TTS audio (static/audio/{job_id}/)
   └── Create video (static/videos/{job_id}/)

3. Download Video → /api/download/{job_id}
```

---

## 3. Reusable vs. Duplicate Components

### 3.1 ✅ Well-Designed Reusable Components

| Component | Purpose | Reusability |
|-----------|---------|-------------|
| `pdf_processor.py` | PDF → Images conversion | ✅ Excellent - clean interface |
| `gemini_service.py` | AI manga analysis | ✅ Good - handles single/multi pages |
| `tts_service.py` | Audio generation | ✅ Good - processes dialogue lists |
| `db_service.py` | Database operations | ✅ Excellent - CRUD operations |
| `download.py` router | Video download | ✅ Good - standalone |

### 3.2 ❌ Components Needing Refactoring

| Component | Issues | Action Needed |
|-----------|--------|---------------|
| `main.py` | Duplicate code blocks | Remove duplicates |
| `video_generator.py` | Two incompatible functions | Remove dead code, fix audio handling |
| `generate_video.py` | Wrong function signature | Update to use correct function |
| `utils.py` | Unused utilities | Remove or integrate |

---

## 4. Multi-Page PDF Error Analysis

### 4.1 Likely Error Scenarios

Based on the code analysis, when processing 5-page PDFs, errors likely occur at:

**Error Point 1: Video Generation - Audio Overlap**
```python
# video_generator.py lines 84-100
# Problem: Multiple dialogues in one panel create separate audio clips
# but they're added to the same image clip, causing conflicts
```

**Error Point 2: Memory Issues**
```python
# MoviePy keeps all clips in memory
# 5 pages × multiple panels × audio clips = high memory usage
# No cleanup between pages
```

**Error Point 3: Panel Path Issues**
```python
# gemini_service.py lines 318-321
# Panels without dialogue are skipped
# But video generator expects all panels to have paths
# Missing panel_path causes KeyError or FileNotFoundError
```

### 4.2 Missing Features for Multi-Page Support

1. **No progress tracking per page** (partially implemented but not used)
2. **No intermediate cleanup** (memory accumulation)
3. **No page transition handling** (abrupt cuts between pages)
4. **No error recovery** (one page fails = entire job fails)

---

## 5. Refactoring Plan

### Phase 1: Fix Critical Duplicates (IMMEDIATE)

**Priority: HIGH - Blocking functionality**

1. **Clean up `main.py`**
   - Remove duplicate `lifespan` function (lines 96-104)
   - Remove duplicate `root()` endpoint (choose one)
   - Remove duplicate static mount (lines 67-68)
   - Remove duplicate router includes (lines 57-59)
   - Keep only the versions with proper prefixes

2. **Fix `video_generator.py`**
   - Remove `generate_manga_video()` async function (dead code)
   - Remove `create_video_for_page()` function (unused)
   - Keep only `create_manga_video()` and fix it

3. **Fix database path**
   - Ensure consistent database location
   - Update path if needed

### Phase 2: Fix Multi-Page Video Generation (HIGH PRIORITY)

**Priority: HIGH - Core feature**

1. **Fix audio handling in `create_manga_video()`**
   ```python
   # Current: Audio clips overlap
   # Fix: Concatenate dialogues per panel sequentially
   ```

2. **Add proper error handling**
   - Skip panels without images (log warning)
   - Continue processing if one panel fails
   - Provide partial results

3. **Add memory management**
   - Close clips after processing each page
   - Clear temporary data
   - Use generators where possible

4. **Add page transitions**
   - Optional fade between pages
   - Configurable transition duration

### Phase 3: Code Cleanup (MEDIUM PRIORITY)

1. **Remove unused code**
   - `utils.py` (OpenCV functions not used)
   - `generate_video.py` (or fix to work with new architecture)

2. **Consolidate configuration**
   - Move all constants to config file
   - Environment variable validation

3. **Improve logging**
   - Structured logging with context
   - Progress percentage tracking

### Phase 4: Enhanced Features (LOW PRIORITY)

1. **Batch processing optimization**
   - Process multiple pages in parallel (with rate limiting)
   - Cache Gemini responses

2. **Quality improvements**
   - Better panel detection filtering
   - Voice cloning per character
   - Background music support

3. **Error recovery**
   - Resume failed jobs
   - Retry mechanism for API failures

---

## 6. Next Steps - Immediate Actions

### Step 1: Fix `main.py` Duplicates
```python
# Remove lines 57-59, 61-68, 96-104
# Keep only lines 107-110 for router includes
# Keep only one root endpoint (suggest the JSON one)
# Keep only one static mount
```

### Step 2: Fix `video_generator.py`
```python
# Remove lines 147-351 (unused functions)
# Fix create_manga_video() audio handling:
#   - Concatenate dialogue audio per panel
#   - Add proper timing
#   - Handle missing panel paths gracefully
```

### Step 3: Test Multi-Page Processing
```python
# Test with 2-page PDF first
# Then 5-page PDF
# Monitor memory usage
# Check video output quality
```

### Step 4: Add Better Error Messages
```python
# Log which page/panel failed
# Provide actionable error messages
# Don't fail entire job on single panel error
```

---

## 7. File Structure Recommendations

### Current Issues:
- `manga_dubbing.db` at root level (should be in `database/`)
- No `.gitignore` for generated files
- Mixed concerns in routers

### Recommended Structure:
```
manga-dubbing-backend/
├── config/
│   ├── settings.py          # Centralized config
│   └── characters.json      # Character voices
├── database/
│   ├── manga_dubbing.db     # Move here
│   └── ...
├── static/                  # Generated files (gitignored)
├── logs/                    # Application logs
└── tests/                   # Unit tests (MISSING)
```

---

## 8. Testing Strategy

### Unit Tests Needed:
1. PDF processing with various page counts
2. Gemini response parsing edge cases
3. Audio concatenation
4. Video generation with missing panels
5. Database operations

### Integration Tests Needed:
1. Full pipeline with 1, 2, 5, 10 page PDFs
2. Error recovery scenarios
3. Concurrent job processing

---

## 9. Performance Considerations

### Current Bottlenecks:
1. **Gemini API**: 2-5s per page (rate limited)
2. **TTS Generation**: 1-2s per dialogue (rate limited)
3. **Video Encoding**: 5-15s (CPU intensive)

### Optimization Opportunities:
1. Parallel page processing (with rate limit respect)
2. Audio pre-generation while analyzing next page
3. Streaming video encoding (reduce memory)
4. Response caching for repeated content

---

## 10. Summary

### What Works Well:
✅ PDF to image conversion
✅ Gemini AI integration
✅ TTS with emotion mapping
✅ Database tracking
✅ API structure

### What Needs Fixing:
❌ Code duplicates in main.py
❌ Video generation audio handling
❌ Multi-page error handling
❌ Memory management
❌ Dead code removal

### Recommended Priority:
1. **IMMEDIATE**: Fix main.py duplicates
2. **HIGH**: Fix video_generator.py audio handling
3. **HIGH**: Add error handling for multi-page
4. **MEDIUM**: Remove dead code
5. **LOW**: Add tests and optimizations

---

## Conclusion

The codebase has a solid foundation with good separation of concerns. The main issues are:
1. Code duplication causing routing conflicts
2. Video generation not properly handling multi-page scenarios
3. Missing error handling for edge cases

These can be fixed with targeted refactoring without major architectural changes. The pipeline design is sound - it just needs cleanup and bug fixes for production use.
