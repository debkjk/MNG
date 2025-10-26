from fastapi import APIRouter, HTTPException, status, UploadFile, File
from services.db_service import get_job, update_job_status
from manga_dialog_extractor import analyze_manga_page
from services.gemini_service import process_manga_pages
import logging
from pathlib import Path
import shutil
import os
import json

router = APIRouter()

@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Query the processing status of a manga dubbing job.
    """
    try:
        job = get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
        return job
    except Exception as e:
        logging.error(f"Error retrieving job status for job_id={job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job status"
        )

@router.post("/extract-dialogs")
async def extract_dialogs(
    file: UploadFile,
    generate_audio: bool = False
):
    """
    Extract dialogs from a manga page image.
    
    Parameters:
        file: The manga page image file
        generate_audio: Whether to generate audio files for the dialogs
        
    Returns:
        dict: Extracted dialogs with emotion and speech information
    """
    try:
        # Create temp directory if it doesn't exist
        temp_dir = Path("static/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Save uploaded file
        temp_file = temp_dir / file.filename
        with temp_file.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Create audio output directory if needed
        audio_dir = None
        if generate_audio:
            audio_dir = Path("static/audio") / temp_file.stem
            audio_dir.mkdir(parents=True, exist_ok=True)
            
        # Extract dialogs
        result = analyze_manga_page(str(temp_file), str(audio_dir) if audio_dir else None)
        
        # Clean up temp file
        temp_file.unlink()
        
        if result:
            return {
                "status": "success",
                "data": result,
                "audio_dir": str(audio_dir) if audio_dir else None
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Failed to extract dialogs from image"
            )
            
    except Exception as e:
        logging.error(f"Error extracting dialogs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image: {str(e)}"
        )