import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Literal
import sqlite3
from database import get_db_connection

# Define valid job statuses
JobStatus = Literal['queued', 'processing', 'completed', 'failed']
VALID_STATUSES: set[JobStatus] = {'queued', 'processing', 'completed', 'failed'}

def create_job(filename: str, storage_filename: str) -> str:
    """
    Create a new job record in the database.
    
    Args:
        filename: The original name of the uploaded PDF file
        storage_filename: The actual filename used to store the file
        
    Returns:
        str: The generated job_id
        
    Raises:
        Exception: If database operation fails
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            job_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()
            
            cursor.execute('''
                INSERT INTO jobs (job_id, filename, storage_filename, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (job_id, filename, storage_filename, 'queued', now, now))
            
            conn.commit()
            return job_id
    except sqlite3.Error as e:
        raise Exception(f"Failed to create job: {e}")

def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a job record by its ID.
    
    Args:
        job_id: The unique identifier of the job
        
    Returns:
        Optional[Dict[str, Any]]: Job record as a dictionary or None if not found
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM jobs WHERE job_id = ?', (job_id,))
            row = cursor.fetchone()
            
            return dict(row) if row else None
    except sqlite3.Error as e:
        raise Exception(f"Failed to retrieve job: {e}")

def update_job_status(
    job_id: str, 
    status: JobStatus,
    video_path: Optional[str] = None, 
    error_message: Optional[str] = None
) -> bool:
    """
    Update the status and optional fields of a job.
    
    Args:
        job_id: The unique identifier of the job
        status: New status value (must be one of VALID_STATUSES)
        video_path: Optional path to the generated video file
        error_message: Optional error message if job failed
        
    Returns:
        bool: True if job was updated, False if job not found
        
    Raises:
        ValueError: If status is not valid
    """
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}")
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            updated_at = datetime.utcnow().isoformat()
            
            cursor.execute('''
                UPDATE jobs 
                SET status = ?, 
                    video_path = ?, 
                    error_message = ?,
                    updated_at = ?
                WHERE job_id = ?
            ''', (status, video_path, error_message, updated_at, job_id))
            
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error as e:
        raise Exception(f"Failed to update job status: {e}")

def list_jobs(limit: int = 50, offset: int = 0) -> list[Dict[str, Any]]:
    """
    List jobs with pagination, ordered by creation date descending.
    
    Args:
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip
        
    Returns:
        list[Dict[str, Any]]: List of job records
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM jobs 
                ORDER BY created_at DESC 
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        raise Exception(f"Failed to list jobs: {e}")