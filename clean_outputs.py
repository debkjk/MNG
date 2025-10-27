import shutil
from pathlib import Path

def clean_directory(dir_path):
    if dir_path.exists():
        for item in dir_path.iterdir():
            if item.is_file() and item.name != ".gitkeep":
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

base_dir = Path(__file__).resolve().parent / "static"
dirs_to_clean = ["audio", "videos", "pages", "manga_pages", "cached_responses", "panels"]

for dir_name in dirs_to_clean:
    clean_directory(base_dir / dir_name)
print("Cleaned output directories successfully!")
