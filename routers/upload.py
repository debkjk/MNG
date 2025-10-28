from fastapi import APIRouter, UploadFile, File, HTTPException, status, BackgroundTasks
from services.db_service import create_job, update_job_status
from services.pdf_processor import convert_pdf_to_images, validate_pdf
from services.gemini_service import process_manga_pages
from services.rapidapi_tts_service import generate_audio_tracks  # Using RapidAPI TTS (high quality)
# Old services (backup):
# from services.tts_service import generate_audio_tracks  # pyttsx3 (robotic)
# from services.tts_service_mock import generate_audio_tracks_mock as generate_audio_tracks  # Mock
from services.video_generator import create_manga_video
from pathlib import Path
import shutil
import uuid
import logging
import os
import re
import traceback

router = APIRouter()

# Configure upload directory
UPLOAD_DIR = Path(__file__).resolve().parent.parent / 'static' / 'uploads'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Maximum file size (50MB in bytes)
MAX_FILE_SIZE = 50 * 1024 * 1024

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    """Handle manga PDF upload and initiate processing."""
    try:
        # Validate file size
        file_size = 0
        contents = await file.read()
        file_size = len(contents)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds maximum limit (50MB)"
            )
            
        # Generate storage filename and save file
        storage_filename = f"{uuid.uuid4()}.pdf"
        pdf_path = UPLOAD_DIR / storage_filename
        
        with open(pdf_path, "wb") as f:
            f.write(contents)
            
        # Create job record
        job_id = create_job(file.filename or "unknown.pdf", storage_filename)
        
        # Start background processing
        if background_tasks:
            background_tasks.add_task(process_manga_pipeline, job_id, pdf_path)
        
        return {"job_id": job_id}
        
    except Exception as e:
        logging.error(f"Upload failed: {str(e)}")
        logging.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

def process_manga_pipeline(job_id: str, pdf_path: Path):
    """Process manga PDF in background."""
    try:
        logging.info(f"\n{'='*60}")
        logging.info(f"🚀 STARTING JOB: {job_id}")
        logging.info(f"📄 PDF File: {pdf_path.name}")
        logging.info(f"{'='*60}\n")
        
        update_job_status(job_id, "processing", current_operation="Validating PDF")
        logging.info(f"✅ Step 1/4: Validating PDF...")
        
        if not validate_pdf(pdf_path):
            logging.error(f"❌ PDF validation failed for {pdf_path}")
            update_job_status(job_id, "failed", error_message="Invalid PDF format")
            return
        
        logging.info(f"✅ PDF validation successful")
            
        # Phase 1: Convert PDF to images
        logging.info(f"\n📸 Step 2/4: Converting PDF to images...")
        update_job_status(job_id, "processing", current_operation="Converting PDF to images")
        image_paths = convert_pdf_to_images(pdf_path, job_id)
        total_pages = len(image_paths)
        logging.info(f"✅ Extracted {total_pages} pages from PDF")
        
        # Update job with total pages
        update_job_status(job_id, "processing", total_pages=total_pages, current_page=0)
        
        # Phase 2: Process each page
        logging.info(f"\n🤖 Step 3/4: Analyzing pages with Gemini AI...")
        all_analysis_results = {
            "pages": [],
            "total_dialogues": 0
        }
        
        for idx, image_path in enumerate(image_paths, 1):
            logging.info(f"   📄 Analyzing page {idx}/{total_pages}...")
            update_job_status(
                job_id, 
                "processing",
                current_operation=f"Analyzing page {idx}/{total_pages} with Gemini",
                current_page=idx
            )
            
            # Extract dialogs using Gemini
            page_analysis = process_manga_pages([image_path], job_id)
            page_dialogues = page_analysis["total_dialogues"]
            logging.info(f"   ✅ Page {idx}: Found {page_dialogues} dialogues")
            
            all_analysis_results["pages"].extend(page_analysis["pages"])
            all_analysis_results["total_dialogues"] += page_dialogues
            
        logging.info(f"\n✅ Gemini analysis completed!")
        logging.info(f"   📊 Total: {all_analysis_results['total_dialogues']} dialogues")
        
        # Phase 3 - TTS generation
        logging.info(f"\n🎤 Step 4/4: Generating audio with ElevenLabs...")
        update_job_status(job_id, "processing", current_operation="Generating audio with ElevenLabs")
        
        tts_results = generate_audio_tracks(all_analysis_results, job_id)
        
        logging.info(f"\n✅ TTS generation completed!")
        logging.info(f"   🎵 Generated {tts_results['successful_dialogues']}/{tts_results['total_dialogues']} audio files")
        logging.info(f"   📁 Merged audio: {tts_results['merged_audio_path']}")
        
        # Phase 4 - Video generation
        logging.info(f"\n🎬 Step 5/5: Creating final video...")
        update_job_status(job_id, "processing", current_operation="Creating video with subtitles")
        
        video_path = create_manga_video(tts_results, job_id)
        
        logging.info(f"\n✅ Video generation completed!")
        logging.info(f"   🎥 Video saved: {video_path}")
        
        update_job_status(job_id, "completed", video_path=video_path)
        
        logging.info(f"\n{'='*60}")
        logging.info(f"🎉 JOB COMPLETED SUCCESSFULLY: {job_id}")
        logging.info(f"{'='*60}\n")
        
    except Exception as e:
        error_msg = f"Processing failed: {str(e)}"
        logging.error(f"\n{'='*60}")
        logging.error(f"❌ JOB FAILED: {job_id}")
        logging.error(f"{'='*60}")
        logging.error(f"Error: {error_msg}")
        logging.error(f"\nFull traceback:")
        logging.error(traceback.format_exc())
        logging.error(f"{'='*60}\n")
        update_job_status(job_id, "failed", error_message=error_msg)

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and ensure safe characters.
    Only allows letters, numbers, dash, underscore, and dot.
    """
    # Extract base name to remove any path components
    base_name = os.path.basename(filename)
    
    # Remove any characters that aren't in our safe set
    safe_name = re.sub(r'[^a-zA-Z0-9\-_.]', '', base_name)
    
    # Ensure the name ends with .pdf
    if not safe_name.lower().endswith('.pdf'):
        safe_name = f"{safe_name}.pdf"
    
    return safe_name
