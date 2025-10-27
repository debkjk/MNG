"""
Script to reset the database - removes old DB and creates new one with correct schema.
Run this to fix database schema issues.
"""
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)

# Define database paths
DB_PATH_1 = Path(__file__).resolve().parent / 'manga_dubbing.db'
DB_PATH_2 = Path(__file__).resolve().parent / 'database' / 'manga_dubbing.db'

def reset_database():
    """Remove old database files and reinitialize with correct schema."""
    
    # Remove old database files if they exist
    for db_path in [DB_PATH_1, DB_PATH_2]:
        if db_path.exists():
            logging.info(f"Removing old database: {db_path}")
            os.remove(db_path)
            logging.info(f"✅ Removed: {db_path}")
        else:
            logging.info(f"Database not found (OK): {db_path}")
    
    # Initialize new database
    logging.info("\n🔄 Initializing new database with correct schema...")
    from database.init_db import init_database
    init_database()
    
    logging.info("\n✅ Database reset complete!")
    logging.info(f"New database created at: {DB_PATH_2}")
    logging.info("\nYou can now start the server with: python main.py")

if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE RESET SCRIPT")
    print("=" * 60)
    print("\nThis will:")
    print("1. Delete old database files")
    print("2. Create new database with correct schema")
    print("\n⚠️  WARNING: All existing job data will be lost!")
    print("=" * 60)
    
    response = input("\nContinue? (yes/no): ").strip().lower()
    
    if response == 'yes':
        reset_database()
    else:
        print("\n❌ Database reset cancelled.")
