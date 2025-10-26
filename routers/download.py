from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from services.db_service import get_job
from pathlib import Path
import logging

# Define base directory for path resolution
BASE_DIR = Path(__file__).resolve().parent.parent

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
        # Validate job exists and is completed
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
        
        # Resolve video path (handle both absolute and relative paths)
        try:
            video_path = Path(job["video_path"])
            # If path is relative, resolve it against BASE_DIR
            if not video_path.is_absolute():
                video_path = BASE_DIR / video_path
            
            # Normalize path to resolve any .. or . components
            video_path = video_path.resolve()
            
            # Security check: ensure the path is within BASE_DIR if it was relative
            if not video_path.is_absolute() or not str(video_path).startswith(str(BASE_DIR)):
                raise ValueError("Invalid path location")
                
            if not video_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Video file not found"
                )
                
            if not video_path.is_file():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Video path exists but is not a file"
                )
        except ValueError as ve:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid video path"
            )
            
        # Prepare response
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