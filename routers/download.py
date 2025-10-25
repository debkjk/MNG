from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from services.db_service import get_job
from pathlib import Path
import logging

router = APIRouter()

@router.get("/download/{job_id}")
async def download_video(job_id: str, download: bool = True):
    """
    Download or stream the completed manga dubbing video.
    
    Parameters:
        job_id (str): Unique identifier of the job
        download (bool): If True, force download; if False, allow inline viewing
        
    Returns:
        FileResponse: Video file with appropriate headers for download/streaming
    """
    try:
        job = get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found"
            )
            
        if job["status"] != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Video not ready. Current status: {job['status']}"
            )
            
        if not job["video_path"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video path not found in job record"
            )
            
        video_path = Path(job["video_path"])
        if not video_path.is_absolute():
            video_path = Path(__file__).resolve().parent.parent / video_path
            
        if not video_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Video file not found"
            )
            
        filename = f"{Path(job['filename']).stem}_dubbed.mp4"
        disposition = "attachment" if download else "inline"
            
        return FileResponse(
            path=str(video_path),
            media_type="video/mp4",
            filename=filename,
            headers={"Content-Disposition": f"{disposition}; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error processing video download for job_id={job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process video download"
        )