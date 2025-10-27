# AI Manga Dubbing Platform

An automated platform that converts manga PDFs into dubbed videos using state-of-the-art AI technologies. The platform leverages Google's Gemini Vision for unified manga analysis and ElevenLabs for emotional text-to-speech generation.

## Project Structure

```
manga-dubbing-backend/
├── input/                  # Place your manga PDFs here
├── database/              # Database related files
├── services/              # Core service modules
├── static/               # Generated files and web assets
│   ├── audio/           # Generated audio files
│   ├── manga_pages/     # Extracted manga pages
│   ├── videos/          # Final output videos
│   └── config/          # Configuration files
├── process_manga.py      # Main processing script
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Setup Instructions

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your API keys:
     - `GEMINI_API_KEY`: Google Gemini Vision API key
     - `ELEVEN_API_KEY`: ElevenLabs API key

## Usage

1. Place your manga PDF file in the `input/` directory
2. Run the processing script:
   ```bash
   python process_manga.py "input/your-manga.pdf"
   ```
3. The script will:
   - Extract pages from the PDF
   - Analyze each page for dialogs
   - Generate voice lines for each dialog
   - Create a final video with synchronized audio
4. Find the output video in `static/videos/`

## API Endpoints

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

Visit `http://localhost:8000/docs` for interactive API documentation.

- SQLite Database

### Frontend

- Vanilla JavaScript
- HTML5 Video Player
- Responsive CSS

### AI Services

- **Google Gemini 2.5 Flash**: Unified vision analysis for manga panels including:
  - Zero-shot panel detection with bounding boxes
  - Reading order determination (R-to-L for Japanese manga)
  - Speech bubble dialogue extraction
  - Emotion classification for dialogue
- **ElevenLabs Text-to-Speech API**: Emotional text-to-speech generation with voice settings tuning. Uses Multilingual v2 model with contextual emotion prefixes for expressive dialogue delivery. Output format: MP3 at 44.1 kHz, 128 kbps for optimal quality and compatibility.

### Media Processing

- PyMuPDF (fitz) - High-performance PDF rendering and page-to-image conversion
- **FFmpeg (via ffmpeg-python)**: Video generation with slideshow creation, audio synchronization, H.264 encoding, and web-optimized output (faststart flag). Outputs MP4 with H.264 video (1920x1080, 30fps) and AAC audio (192kbps)

### Deployment

- Render/Railway compatible

## Project Structure

```
manga-dubbing-backend/
├── static/               # Static file storage
│   ├── uploads/         # Temporary PDF storage
│   ├── pages/          # Converted PDF pages (temporary)
│   ├── panels/         # Extracted manga panels
│   ├── audio/          # Generated audio files
│   └── videos/         # Final dubbed videos
├── routers/             # API route handlers
├── services/            # Business logic modules
│   ├── db_service.py      # Database operations
│   ├── gemini_service.py  # Gemini AI manga analysis
│   ├── pdf_processor.py   # PDF to image conversion
│   ├── tts_service.py     # ElevenLabs TTS integration
│   └── video_generator.py # FFmpeg-based video generation service
├── main.py             # Application entry point
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
└── README.md           # Project documentation
```

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- pip package manager
- FFmpeg installed on your system

### Installation

1. Clone the repository:

   ```bash
   git clone [repository-url]
   cd manga-dubbing-backend
   ```

2. Create a virtual environment:

   ```bash
   # Windows CMD
   python -m venv venv
   .\venv\Scripts\activate

   # Windows Git Bash
   python -m venv venv
   source venv/Scripts/activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

## ElevenLabs TTS Setup

1. Visit [ElevenLabs](https://elevenlabs.io/) and sign up for a free account
2. Navigate to Profile → API Keys
3. Create a new API key
4. Add to `.env` file as `ELEVENLABS_API_KEY=your-key-here`

### Voice Customization

- Default voice: Sarah (EXAVITQu4vr4xnSDxMaL)
- Browse the [voice library](https://elevenlabs.io/voice-library) for alternatives
- Update `ELEVENLABS_VOICE_ID` in `.env` with your preferred voice
- Different voices work better for different manga genres

Note: Free tier includes 10,000 characters/month, sufficient for testing and small manga chapters.

### Audio Processing Details

#### Emotion Mapping Strategy

- Emotion labels from Gemini (happy, sad, angry, etc.) are mapped to contextual text prefixes
- Example: "She said sadly: I can't believe it's over."
- ElevenLabs models infer emotion from text context and voice settings

#### Voice Settings Tuning

- Different emotions use different stability, style, and speed parameters:
  - Happy/excited: faster speed, higher style
  - Sad/scared: slower speed, higher stability
  - Angry: lower stability, higher style
  - All use speaker boost for clarity

#### Audio Generation

- Individual MP3 files for each dialogue (44.1 kHz, 128 kbps)
- ffmpeg-python concat demuxer for fast, lossless concatenation
- Organized in job-specific directories for easy management

## FFmpeg Installation

FFmpeg is required for video generation. Install it on your system:

- **macOS**: `brew install ffmpeg`
- **Ubuntu/Debian**: `sudo apt-get update && sudo apt-get install ffmpeg`
- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
- Verify installation: `ffmpeg -version`

Note: The Python package `ffmpeg-python` (in requirements.txt) is just a wrapper; the actual ffmpeg binary must be installed separately.

## Video Output Specifications

- **Resolution**: 1920x1080 (Full HD)
- **Frame Rate**: 30 fps
- **Video Codec**: H.264 (libx264)
- **Audio Codec**: AAC at 192 kbps
- **Pixel Format**: yuv420p (maximum compatibility)
- **Container**: MP4 with faststart flag (web-optimized)
- **Timing**: Equal duration per panel, total duration matches audio
- **Aspect Ratio Handling**: Letterboxing with black padding

These settings ensure broad compatibility across browsers, devices, and video players.

## Storage and Cleanup

### Temporary Files (cleaned up after video generation)

- Page images: `static/pages/{job_id}/`
- Individual audio files: `static/audio/{job_id}/dialogue_*.mp3`

### Preserved Files

- Uploaded PDF: `static/uploads/{job_id}.pdf`
- Panel images: `static/panels/{job_id}/` (optional, can be cleaned up)
- Merged audio: `static/audio/{job_id}/merged_audio.mp3`
- Final video: `static/videos/{job_id}/final_video.mp4`

Cleanup happens automatically after successful video generation. Temporary files are preserved if video generation fails (useful for debugging).

## Performance Notes

Expected processing times:

- PDF to images: ~1-2 seconds per page
- Gemini analysis: ~2-5 seconds per page (depends on API response time)
- TTS generation: ~1-2 seconds per dialogue line (depends on text length)
- Video generation: ~5-15 seconds (depends on panel count and video duration)
- Total: ~30-60 seconds for a typical 10-page manga chapter

Processing is asynchronous and doesn't block the upload endpoint. Rate limiting recommended for production deployments.

## Troubleshooting

- **FFmpeg not found**: Ensure ffmpeg binary is installed and accessible in PATH
- **Video generation fails**: Check ffmpeg logs, verify panel images and audio file exist
- **Video duration mismatch**: Verify merged audio file is valid and has correct duration
- **Out of disk space**: Implement periodic cleanup of old completed jobs
- **Video won't play in browser**: Verify H.264 codec and yuv420p pixel format are used
- **Panel images distorted**: Check letterboxing settings and aspect ratio preservation

## Gemini API Setup

### Getting Started with Gemini

1. Visit [Google AI Studio](https://ai.google.dev/)
2. Create a new API key (free tier available)
3. Add to `.env` file: `GEMINI_API_KEY=your-key-here`

### API Usage Notes

- Free tier limits:
  - 15 requests per minute
  - 1 million tokens per day (sufficient for MVP)
- Using Gemini 2.5 Flash Experimental for best vision performance
- Automatic fallback to Gemini 1.5 Flash if experimental API unavailable

### Unified Analysis Approach

The platform uses a single API call per page to perform four unified tasks:

1. Panel Detection with pixel-accurate bounding boxes
2. Reading Order determination (right-to-left for Japanese manga)
3. Dialogue Extraction from speech bubbles
4. Emotion Detection for each dialogue line

This unified approach improves efficiency and reduces API costs while ensuring consistent analysis across all tasks.

## Running the Application

### Development Mode

```bash
python main.py
# or
uvicorn main:app --reload
```

The API will be available at:

- API Documentation: http://localhost:8000/docs
- ReDoc Documentation: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## Environment Variables

| Variable           | Description           | Example                                                     |
| ------------------ | --------------------- | ----------------------------------------------------------- |
| GEMINI_API_KEY     | Google Gemini API key | Get from [Google AI Studio](https://ai.google.dev/)         |
| ELEVENLABS_API_KEY | ElevenLabs API key    | Get from [ElevenLabs Dashboard](https://elevenlabs.io/docs) |
| HOST               | Server host address   | 0.0.0.0                                                     |
| PORT               | Server port           | 8000                                                        |
| ALLOWED_ORIGINS    | CORS allowed origins  | \*                                                          |

## API Endpoints

### POST /api/upload

Upload a manga PDF file for dubbing processing.

**Request:**

- Method: POST
- Content-Type: multipart/form-data
- Body: PDF file (max 50MB)

**Response:**

```json
{
  "job_id": "uuid-string",
  "filename": "original.pdf",
  "status": "queued",
  "message": "Processing started"
}
```

**Example:**

```bash
curl -X POST -F "file=@manga.pdf" http://localhost:8000/api/upload
```

### GET /api/status/{job_id}

Query the processing status of a manga dubbing job.

**Parameters:**

- job_id (path): Unique identifier of the job

**Response:**

```json
{
  "job_id": "uuid-string",
  "filename": "manga.pdf",
  "status": "processing",
  "video_path": null,
  "error_message": null,
  "created_at": "2025-10-25T10:30:00Z",
  "updated_at": "2025-10-25T10:30:05Z"
}
```

**Status Values:**

- queued: Job is waiting to be processed
- processing: Job is currently being processed
- completed: Job is finished, video is ready
- failed: Job failed with error message

**Example:**

```bash
curl http://localhost:8000/api/status/your-job-id
```

### GET /api/download/{job_id}

Download the completed manga dubbing video.

**Parameters:**

- job_id (path): Unique identifier of the job
- download (query, optional): Set to true to force download, false for inline viewing

**Response:**

- Content-Type: video/mp4
- Headers for download/streaming

**Example:**

```bash
# Download video
curl -O http://localhost:8000/api/download/your-job-id

# Stream video
curl http://localhost:8000/api/download/your-job-id?download=false
```

### Root Endpoints

- `GET /` - API information
- `GET /health` - Service health check

## Background Processing Pipeline

The platform processes manga PDFs in several phases:

1. PDF upload and validation
2. Job record creation with 'queued' status
3. Background task triggered immediately
4. Status updated to 'processing'
5. PDF converted to high-resolution PNG images (300 DPI)
6. **Gemini AI Analysis Phase:**
   - Process each page with unified prompt
   - Detect panels with pixel-accurate bounding boxes
   - Determine right-to-left reading order
   - Extract dialogue text and speaker names
   - Classify emotions for each dialogue line
   - Extract individual panel images
   - Store structured analysis results
7. TTS generation using analysis results (ElevenLabs)
8. Video assembly with panels and audio (FFmpeg)

### Edge Cases Handled

- Panels without dialogue (empty dialogues array)
- Overlapping panels (visual separation)
- Sound effects (excluded from dialogue)
- Invalid PDFs (early validation)
- API rate limits (exponential backoff)

### Coming Soon

- `GET /api/process/{job_id}` - Check processing status
- `GET /api/download/{job_id}` - Download dubbed video

## Database Schema

### Jobs Table

| Column           | Type | Description                                     |
| ---------------- | ---- | ----------------------------------------------- |
| job_id           | TEXT | Primary key (UUID4)                             |
| filename         | TEXT | Original uploaded PDF filename                  |
| storage_filename | TEXT | Unique filename used to store the file          |
| status           | TEXT | Job status (queued/processing/completed/failed) |
| video_path       | TEXT | Path to generated video (NULL until complete)   |
| error_message    | TEXT | Error details if failed (NULL otherwise)        |
| created_at       | TEXT | ISO 8601 creation timestamp                     |
| updated_at       | TEXT | ISO 8601 last update timestamp                  |

Note: Status values are enforced by a CHECK constraint in the database.

Indexes:

- `idx_jobs_status` on `status` column
- `idx_jobs_created_at` on `created_at` column

## Background Processing Pipeline

The application uses FastAPI's BackgroundTasks for asynchronous processing of uploaded manga PDFs:

1. PDF Upload and Validation

   - File size and format validation
   - Storage in `static/uploads/` directory
   - Job record creation with 'queued' status

2. Asynchronous Processing

   - Background task triggered immediately after upload
   - Status updated to 'processing'
   - PDF converted to high-resolution PNG images (300 DPI)
   - Images stored in `static/pages/{job_id}/`

This approach prevents HTTP timeouts during long-running operations and provides a better user experience.

## Development Workflow

### Phase 1 (Completed)

- ✅ Project foundation
- ✅ FastAPI setup
- ✅ Directory structure
- ✅ Configuration management

### Phase 2 (Completed)

- ✅ Upload endpoint
- ✅ SQLite persistence
- ✅ Job tracking

### Phase 3 (Current)

- ✅ Background processing
- ✅ PDF to image conversion
- ✅ Asynchronous execution

### Completed Phases

- PDF processing and panel extraction
- Gemini AI integration
- ElevenLabs TTS integration
- Video generation service

### Next Steps

- Status and download API endpoints
- Frontend development

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Troubleshooting

### Common Issues

1. **Gemini API Related**

   - "Rate limit exceeded": Wait or upgrade to paid tier
   - "Missing GEMINI_API_KEY": Check .env configuration
   - "Panel detection inaccurate": Ensure high-quality PDF input
   - "JSON parsing errors": Indicates prompt needs refinement
   - "Content safety block": Manga content flagged by Gemini

2. **Image Processing**

   - "Invalid panel dimensions": Usually from poor quality scans
   - "Failed to extract panels": Check PDF resolution
   - "Memory error": Large PDFs may need batching

3. **Job Stuck in 'processing' Status**

   - Check application logs for errors
   - Verify PDF file is accessible
   - Ensure sufficient disk space for image conversion

4. **PDF Conversion Fails**

   - Verify PDF is not corrupted
   - Check if PDF is password-protected
   - Ensure PDF contains valid page content

5. **Out of Disk Space**
   - Regular cleanup of `/static/pages/{job_id}` directories
   - Monitor disk usage during high-volume processing
   - Implement automated cleanup of completed jobs

### Debugging

- Application logs contain detailed error messages and stack traces
- Each processing step logs its progress with job_id context
- Background task errors are captured and stored in job records

## Using the Web Interface

1. Start the server:

   ```bash
   python main.py
   ```

   The server will start at `http://localhost:8000`.

2. Access the web interface:

   - Open your browser to `http://localhost:8000/static/index.html`
   - The interface provides a simple, intuitive way to interact with the manga dubbing system

3. Upload and Process:

   - Click "Choose PDF File" to select your manga PDF (max 50MB)
   - The interface will show the selected file name and size
   - Click "Upload and Process" to begin
   - A progress bar will show the upload progress
   - Once uploaded, you'll see the job ID and current status

4. Monitor Progress:

   - The status badge will update automatically every 5 seconds
   - You'll see different status indicators:
     - Queued (gray): Waiting to start
     - Processing (yellow): Converting manga to video
     - Completed (green): Ready to watch
     - Failed (red): Error occurred

5. Watch and Download:
   - When processing completes, the video player appears automatically
   - Use the player controls to watch the dubbed manga
   - Click "Download Video" to save the file
   - Use "Process Another Manga" to start over

### Troubleshooting Common Issues

1. Upload Problems:

   - Ensure your PDF is under 50MB
   - Check your internet connection if upload fails
   - Try refreshing the page if the upload button remains disabled

2. Status Updates:

   - If status stops updating, check your network connection
   - The system will automatically retry up to 5 times
   - Refresh the page if status remains stuck

3. Video Playback:

   - If video doesn't play, try refreshing the page
   - Ensure your browser supports H.264 video
   - Use the download option if streaming isn't smooth

4. Browser Compatibility:
   - Use a modern browser (Chrome, Firefox, Safari, Edge)
   - Enable JavaScript if it's disabled
   - Clear browser cache if you experience issues

## Portfolio Project

This is a portfolio demonstration project showcasing AI integration, media processing, and modern Python web development practices.
