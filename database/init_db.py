import sqlite3
from pathlib import Path
import logging

def init_database():
    """Initialize the database with required tables."""
    db_path = Path(__file__).resolve().parent / 'manga_dubbing.db'
    
    try:
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            
            # Create jobs table with proper schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    storage_filename TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('queued', 'processing', 'completed', 'failed')),
                    video_path TEXT,
                    error_message TEXT,
                    current_operation TEXT,
                    current_page INTEGER DEFAULT 0,
                    total_pages INTEGER,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Create indexes for efficient querying
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_status 
                ON jobs(status)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_created_at 
                ON jobs(created_at)
            """)
            
            # Create pages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pages (
                    page_id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    dialog_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
                )
            """)
            
            conn.commit()
            logging.info("Database initialized successfully")
            
    except sqlite3.Error as e:
        logging.error(f"Failed to initialize database: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database()