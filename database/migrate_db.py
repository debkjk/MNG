#!/usr/bin/env python3
"""
Database migration script to add new columns for multi-page processing support.
This script safely adds the new columns to existing databases.
"""

import sqlite3
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Migrate existing database to support multi-page processing."""
    db_path = Path(__file__).resolve().parent / 'manga_dubbing.db'
    
    if not db_path.exists():
        logger.info("Database doesn't exist yet, will be created with new schema")
        return
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if new columns already exist
        cursor.execute("PRAGMA table_info(jobs)")
        columns = [row[1] for row in cursor.fetchall()]
        
        new_columns = [
            ('current_operation', 'TEXT'),
            ('current_page', 'INTEGER DEFAULT 0'),
            ('total_pages', 'INTEGER')
        ]
        
        for column_name, column_type in new_columns:
            if column_name not in columns:
                logger.info(f"Adding column: {column_name}")
                cursor.execute(f"ALTER TABLE jobs ADD COLUMN {column_name} {column_type}")
            else:
                logger.info(f"Column {column_name} already exists")
        
        conn.commit()
        logger.info("Database migration completed successfully")
        
    except sqlite3.Error as e:
        logger.error(f"Database migration failed: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_database()
