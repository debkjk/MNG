from fastapi import APIRouter, UploadFile, File, HTTPException, status, BackgroundTasks
from services.db_service import create_job, update_job_status
from services.pdf_processor import convert_pdf_to_images, validate_pdf
from services.gemini_service import process_manga_pages
from services.tts_service import generate_audio_tracks
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

def process_manga_pipeline(job_id: str, pdf_path: Path):
    """
    Background task to process uploaded manga PDF.
    Converts PDF to images and prepares for subsequent processing phases.
    
    Args:
        job_id: Unique identifier for the job
        pdf_path: Path to the uploaded PDF file
    """
    try:
        # Update status to processing
        update_job_status(job_id, "processing")
        logging.info(f"Starting background processing for job {job_id}")
        
        # Validate PDF before processing
        if not validate_pdf(pdf_path):
            logging.error(f"Invalid PDF format for job {job_id}")
            update_job_status(job_id, "failed", error_message="Invalid or corrupted PDF")
            return
        
        # Convert PDF to images
        image_paths = convert_pdf_to_images(pdf_path, job_id)
        logging.info(f"Successfully converted PDF to {len(image_paths)} images for job {job_id}")
        
        # Phase 4 - Gemini AI analysis
        logging.info(f"Starting Gemini AI analysis for job {job_id}")
        analysis_results = process_manga_pages(image_paths, job_id)
        logging.info(f"Gemini analysis completed for job {job_id}. Found {analysis_results['total_panels']} panels with {analysis_results['total_dialogues']} dialogues")
        
        # Phase 5 - TTS generation
        logging.info(f"Starting TTS generation for job {job_id}")
        tts_results = generate_audio_tracks(analysis_results, job_id)
        logging.info(f"TTS generation completed for job {job_id}. Generated {tts_results['successful_dialogues']} audio files. Merged audio: {tts_results['merged_audio_path']}")
        analysis_results = tts_results
        
        # Phase 6 - Video generation
        logging.info(f"Starting video generation for job {job_id}")
        video_path = create_manga_video(analysis_results, job_id)
        logging.info(f"Video generation completed for job {job_id}. Video saved to: {video_path}")
        update_job_status(job_id, "completed", video_path=video_path)
        logging.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        error_msg = f"Processing failed: {str(e)}"
        logging.error(f"Error processing job {job_id}: {error_msg}\n{traceback.format_exc()}")
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

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_manga(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload a manga PDF file for dubbing processing.
    
    Args:
        file: PDF file uploaded through multipart/form-data
        
    Returns:
        dict: Job information including job_id, filename, status, and message
        
    Raises:
        HTTPException: If file validation fails or processing errors occur
    """
    # Validate file extension
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed"
        )
    
    # Validate content type
    if file.content_type not in ['application/pdf', 'application/x-pdf']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only PDF files are allowed"
        )
    
    try:
        # Generate storage filename using UUID only
        storage_filename = f"{uuid.uuid4()}.pdf"
        file_path = UPLOAD_DIR / storage_filename
        
        # Track file size while copying
        size = 0
        is_pdf_verified = False
        
        with file_path.open("wb") as buffer:
            # Read first chunk to verify PDF header
            first_chunk = await file.read(8192)
            if not first_chunk.startswith(b'%PDF-'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid PDF file. File does not have a valid PDF header."
                )
            
            # Process first chunk
            size = len(first_chunk)
            if size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File too large. Maximum size is {MAX_FILE_SIZE/(1024*1024):.1f}MB"
                )
            buffer.write(first_chunk)
            is_pdf_verified = True
            
            # Process remaining chunks
            while chunk := await file.read(8192):
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"File too large. Maximum size is {MAX_FILE_SIZE/(1024*1024):.1f}MB"
                    )
                buffer.write(chunk)
        
        # Create job record with original filename
        original_filename = sanitize_filename(file.filename)
        job_id = create_job(original_filename, storage_filename)
        
        # Schedule background processing
        pdf_path = UPLOAD_DIR / storage_filename
        background_tasks.add_task(process_manga_pipeline, job_id, pdf_path)
        logging.info(f"Background processing scheduled for job {job_id}")
        
        # Close the upload file to release resources
        await file.close()
        
        return {
            "job_id": job_id,
            "filename": original_filename,
            "status": "queued",
            "message": "File uploaded successfully. Processing has started in the background."
        }
        
    except HTTPException as http_exc:
        # Clean up uploaded file if it was created
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        await file.close()
        raise http_exc
        
    except Exception as e:
        # Clean up uploaded file if it was created
        if 'file_path' in locals() and file_path.exists():
            file_path.unlink()
        await file.close()
        
        logging.error(f"Upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process upload"
        )