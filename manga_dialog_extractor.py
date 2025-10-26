import cv2
import numpy as np
from pathlib import Path
import argparse
import os
import json
from PIL import Image
from dotenv import load_dotenv
from services.gemini_service import initialize_gemini_client
from services.tts_service import (
    initialize_elevenlabs_client, 
    generate_dialogue_audio,
    AUDIO_DIR
)

# Load environment variables from .env file
load_dotenv()

def analyze_manga_page(image_path, output_dir=None, page_number=None):
    """
    Analyze a manga page to determine its type and extract content.
    
    Args:
        image_path: Path to the manga page image
        output_dir: Optional directory for audio output files
        page_number: Optional page number for context
        
    Returns:
        dict: Page analysis results including type and content
    """
    # Read image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    # Convert to RGB for Gemini
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(rgb_img)
    
    print("\nAnalyzing manga page...")
    
    # Initialize Gemini client
    model = initialize_gemini_client()
    
    # Initialize text-to-speech client if needed
    tts_client = None
    if output_dir:
        tts_client = initialize_elevenlabs_client()
    
    # Create prompt for page type and dialog analysis
    prompt = """Analyze this manga page and determine its type and content. Return a JSON object with page classification and dialogs.

First, determine the page type:
1. "story" - Normal story page with panels and dialogs
2. "title" - Title page or chapter cover
3. "credits" - Credits or author information
4. "toc" - Table of contents
5. "ad" - Advertisement
6. "blank" - Blank or filler page

Then analyze the page content. For story pages, extract all dialogs in proper reading order (right-to-left, top-to-bottom for manga).
Each dialog should have:
{
    "page_type": "story|title|credits|toc|ad|blank",
    "page_number": number (if visible),
    "chapter_info": {  // Only for title pages
        "title": "Chapter title if present",
        "number": "Chapter number if present",
        "summary": "Brief chapter summary or tagline if present"
    },
    "credits_info": {  // Only for credits pages
        "author": "Author name if present",
        "artist": "Artist name if present",
        "other_credits": ["Other credited roles"]
    },
    "dialogs": [  // For story pages
        {
            "sequence": number (1, 2, 3, etc. - reading order),
            "text": "The actual dialog text",
            "speaker": "Character name or 'Narrator'",
            "emotion": {
                "type": "happy|sad|angry|surprised|excited|scared|neutral|shouting|whispering|crying|laughing",
                "intensity": number (0.1 to 1.0 - how strong the emotion is),
                "stability": number (0 to 1.0 - voice stability, lower means more emotional variation),
                "style": number (0 to 1.0 - how much emotion affects the voice),
                "description": "Brief description of the emotional state and how it should sound"
            },
            "speech": {
                "speed": number (0.5 to 2.0 - speaking speed multiplier, 1.0 is normal),
                "volume": number (0.5 to 2.0 - volume multiplier, 1.0 is normal),
                "pitch": "high|medium|low" (relative pitch of voice)
            },
            "position": {
                "vertical": "top|middle|bottom",
                "horizontal": "left|center|right"
            }
        }
    ]
}

Example response formats:

For a story page:
{
    "page_type": "story",
    "page_number": 1,
    "dialogs": [
        {
            "sequence": 1,
            "text": "WHAT'S GOING ON HERE?!",
            "speaker": "Character1",
            "emotion": {
                "type": "surprised",
                "intensity": 0.8,
                "stability": 0.3,
                "style": 0.9,
                "description": "Shocked and alarmed, voice should be higher pitched with emphasis"
            },
            "position": {
                "vertical": "top",
                "horizontal": "right"
            },
            "speech": {
                "speed": 1.2,
                "volume": 1.5,
                "pitch": "high"
            }
        }
    ]
}

For a title page:
{
    "page_type": "title",
    "page_number": null,
    "chapter_info": {
        "title": "A New Beginning",
        "number": "Chapter 1",
        "summary": "Our journey begins..."
    },
    "dialogs": []
}

For a credits page:
{
    "page_type": "credits",
    "page_number": null,
    "credits_info": {
        "author": "John Doe",
        "artist": "Jane Smith",
        "other_credits": ["Editor: Bob Wilson"]
    },
    "dialogs": []
}

Important:
1. Return ONLY the JSON, no other text
2. Keep dialogs in proper reading order
3. Include ALL text on the page
4. Maintain story flow and context"""

    # Send to Gemini for analysis
    print("Sending to Gemini API...")
    response = model.generate_content([prompt, pil_img])
    result = response.text.strip()
    
    try:
        # Parse the JSON response
        result = result.replace("'", '"')  # Replace single quotes
        result = result.strip('`')  # Remove any markdown formatting
        # Remove any prefix like 'json' before the actual JSON content
        if 'json' in result.lower():
            result = result[result.find('{'):]
            
        # Fix curly quotes that might cause JSON parsing issues
        result = result.replace('"', '"').replace('"', '"')
        
        data = json.loads(result)
        print("\nExtracted dialogs in reading order:")
        print(json.dumps(data, indent=2))
        
        # Generate audio if output directory specified
        if output_dir and tts_client:
            print("\nGenerating audio files...")
            for dialog in data['dialogs']:
                audio_path = Path(output_dir) / f"dialog_{dialog['sequence']:02d}.mp3"
                generate_dialogue_audio(
                    tts_client,
                    dialog,
                    os.getenv("ELEVENLABS_VOICE_ID"),
                    audio_path
                )
                print(f"Generated: dialog_{dialog['sequence']:02d}.mp3")
        
            # Generate audio if output directory specified
            if output_dir:
                audio_path = Path(output_dir) / f"dialog_{dialog['sequence']:02d}.mp3"
                generate_dialogue_audio(
                    tts_client,
                    dialog,
                    os.getenv("ELEVENLABS_VOICE_ID"),
                    audio_path
                )
                print(f"Generated audio: {audio_path}")
        
        # Save the extracted data
        output_json = Path(image_path).with_suffix('.json')
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\nSaved dialog data to: {output_json}")
        
        return data
        
    except json.JSONDecodeError as e:
        print("Error parsing Gemini response:")
        print(f"Error: {str(e)}")
        print(f"Raw response: {result}")
        return None

def process_sequential_pages(directory_path, output_dir=None):
    """
    Process multiple manga pages in sequence.
    
    Args:
        directory_path: Directory containing manga page images
        output_dir: Optional directory for audio output files
    
    Returns:
        list: List of analysis results for each page
    """
    # Get all image files in order
    image_files = sorted([
        f for f in os.listdir(directory_path) 
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ])
    
    results = []
    for page_num, image_file in enumerate(image_files, 1):
        image_path = os.path.join(directory_path, image_file)
        print(f"\nProcessing page {page_num}/{len(image_files)}: {image_file}")
        
        # Create page-specific audio directory if needed
        page_audio_dir = None
        if output_dir:
            page_audio_dir = os.path.join(output_dir, f"page_{page_num:03d}")
            os.makedirs(page_audio_dir, exist_ok=True)
        
        # Analyze page
        result = analyze_manga_page(image_path, page_audio_dir, page_num)
        if result:
            results.append(result)
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Manga Dialog Extractor")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-f", "--file", help="Path to single manga page image")
    group.add_argument("-d", "--directory", help="Directory containing manga pages in sequence")
    parser.add_argument("-o", "--output", default=None,
                       help="Output directory for audio files")
    
    args = parser.parse_args()
    
    # Create output directory if specified
    if args.output:
        os.makedirs(args.output, exist_ok=True)
    
    if args.file:
        # Process single page
        result = analyze_manga_page(args.file, args.output)
        if result:
            print("\nFinal Analysis:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # Process directory of pages
        results = process_sequential_pages(args.directory, args.output)
        output_json = os.path.join(args.directory, 'manga_analysis.json')
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nAnalysis saved to: {output_json}")

if __name__ == "__main__":
    main()