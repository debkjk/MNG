import argparse
from pathlib import Path
from services.video_generator import generate_manga_video

def main():
    parser = argparse.ArgumentParser(description='Generate a video from manga page with audio')
    parser.add_argument('-i', '--image', required=True, help='Path to manga page image')
    parser.add_argument('-j', '--json', required=True, help='Path to dialog JSON file')
    parser.add_argument('-a', '--audio', required=True, help='Path to audio files directory')
    parser.add_argument('-o', '--output', help='Output directory for video', default='static/videos')
    
    args = parser.parse_args()
    
    # Convert paths
    image_path = Path(args.image)
    json_path = Path(args.json)
    audio_dir = Path(args.audio)
    output_dir = Path(args.output)
    
    # Validate paths
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    if not json_path.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    if not audio_dir.is_dir():
        raise NotADirectoryError(f"Audio directory not found: {audio_dir}")
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate video
    output_path = generate_manga_video(
        page_image_path=image_path,
        dialogs_json_path=json_path,
        audio_dir=audio_dir,
        output_dir=output_dir
    )
    
    print(f"\nVideo generated successfully: {output_path}")

if __name__ == "__main__":
    main()