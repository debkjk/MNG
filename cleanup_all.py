"""
Complete cleanup script - removes all generated files and resets database
"""
import os
import shutil
import sqlite3
from pathlib import Path

def cleanup_all():
    """Clean up all generated files and reset database."""
    
    print("🧹 Starting complete cleanup...")
    
    # Directories to clean
    dirs_to_clean = [
        "static/uploads",
        "static/manga_pages", 
        "static/audio",
        "static/videos",
        "static/pages",      # Old folder - remove completely
        "static/panels",     # Old folder - remove completely
        "static/cached_responses"  # Old cache - remove completely
    ]
    
    # Clean directories
    for dir_path in dirs_to_clean:
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                os.makedirs(dir_path, exist_ok=True)
                # Create .gitkeep to preserve directory
                with open(os.path.join(dir_path, ".gitkeep"), "w") as f:
                    f.write("")
                print(f"✅ Cleaned: {dir_path}")
            except Exception as e:
                print(f"❌ Error cleaning {dir_path}: {e}")
        else:
            os.makedirs(dir_path, exist_ok=True)
            print(f"✅ Created: {dir_path}")
    
    # Reset database
    db_path = "database/manga_dubbing.db"
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Delete all jobs
            cursor.execute("DELETE FROM jobs")
            conn.commit()
            
            count = cursor.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
            conn.close()
            
            print(f"✅ Database reset: {count} jobs remaining")
        except Exception as e:
            print(f"❌ Error resetting database: {e}")
    
    print("\n🎉 Cleanup complete!")
    print("   All uploads, images, audio, and videos removed")
    print("   Database reset")
    print("   Ready for fresh start!\n")

if __name__ == "__main__":
    cleanup_all()
