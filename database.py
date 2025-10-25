import sqlite3
from pathlib import Path
from datetime import datetime
import logging

# Configure database path in backend root directory
DATABASE_PATH = Path(__file__).resolve().parent / 'manga_dubbing.db'

class DBConnection:
    """Context manager for database connections."""
    def __init__(self):
        self.conn = None

    def __enter__(self):
        try:
            self.conn = sqlite3.connect(str(DATABASE_PATH))
            self.conn.row_factory = sqlite3.Row
            return self.conn
        except sqlite3.Error as e:
            logging.error(f"Database connection error: {e}")
            if self.conn is not None:
                self.conn.close()
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # If an error occurred, roll back
            if self.conn is not None:
                self.conn.rollback()
        if self.conn is not None:
            self.conn.close()
        return False  # Propagate exceptions

def get_db_connection():
    """Create a database connection with Row factory for dictionary-like access."""
    return DBConnection()

def init_db():
    """Initialize the database schema if it doesn't exist."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Create jobs table with status check constraint
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    storage_filename TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('queued', 'processing', 'completed', 'failed')),
                    video_path TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')

            # Create indexes for efficient querying
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_jobs_status 
                ON jobs(status)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_jobs_created_at 
                ON jobs(created_at)
            ''')

            conn.commit()
            logging.info("Database initialized successfully")
    except sqlite3.Error as e:
        logging.error(f"Database initialization error: {e}")
        raise