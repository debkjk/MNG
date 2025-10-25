from fastapi import APIRouter, HTTPException, status
from services.db_service import get_job
import logging

router = APIRouter()

@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Query the processing status of a manga dubbing job.
    
    Parameters:
        job_id (str): Unique identifier of the job
        
    Returns:
        dict: Job record with status, video_path, and other details
        
    Example responses:
        - {"job_id": "123", "status": "queued", "filename": "manga.pdf", ...}
        - {"job_id": "123", "status": "processing", "filename": "manga.pdf", ...}
        - {"job_id": "123", "status": "completed", "filename": "manga.pdf", "video_path": "static/videos/123/final_video.mp4", ...}
        - {"job_id": "123", "status": "failed", "filename": "manga.pdf", "error_message": "Error details", ...}
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