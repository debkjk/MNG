"""
Gemini Vision API service for manga page analysis
Extracts dialogues in reading order with detailed emotion and speech settings
"""
import google.generativeai as genai
from google.api_core import exceptions
import PIL.Image
from pathlib import Path
import json
import logging
import os
import re
from typing import List, Dict, Any
import time
import functools

# Configuration
MANGA_PAGES_DIR = Path(__file__).resolve().parent.parent / 'static' / 'manga_pages'
MANGA_PAGES_DIR.mkdir(parents=True, exist_ok=True)

def retry_with_backoff(max_retries=3, initial_delay=1):
    """Decorator for retrying with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= 2
            return func(*args, **kwargs)
        return wrapper
    return decorator

def initialize_gemini_client():
    """Initialize Gemini API client with configuration."""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    genai.configure(api_key=api_key)
    
    generation_config = {
        "temperature": 0.4,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    }
    
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
    ]
    
    try:
        model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            generation_config=generation_config,
            safety_settings=safety_settings
        )
    except Exception:
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config=generation_config,
            safety_settings=safety_settings
        )
    
    return model

def create_analysis_prompt() -> str:
    """Create the analysis prompt for Gemini."""
    return """Analyze this manga page and extract ALL dialogue/text in EXACT READING ORDER (top to bottom, left to right).

📖 READING ORDER RULES:
1. Read the page naturally - TOP to BOTTOM, LEFT to RIGHT
2. Number dialogues in exact sequence (1, 2, 3...) as they should be read
3. DO NOT group by panels - just extract dialogues in reading flow
4. Include narration boxes, speech bubbles, thought bubbles

🎭 EMOTION & SPEECH ANALYSIS:
For each dialogue, analyze:
- **Emotion type**: calm, angry, yell, sad, whisper, excitement, amusement, scared, surprised, neutral, determined, hopeful, reflective, melancholic
- **Intensity**: 0.0-1.0 (how strong the emotion is)
- **Stability**: 0.0-1.0 (how controlled/stable the emotion is)  
- **Style**: 0.0-1.0 (formality level)
- **Description**: Brief description of the emotional tone
- **Speed**: 0.5-1.5 (speaking speed multiplier)
- **Volume**: 0.5-1.5 (volume level)
- **Pitch**: "low", "medium", "high"
- **Position**: vertical (top/middle/bottom), horizontal (left/center/right)

🎯 OUTPUT FORMAT (STRICT JSON):
{
  "page_type": "story",
  "page_number": 1,
  "dialogs": [
    {
      "sequence": 1,
      "text": "exact dialogue text here",
      "speaker": "Character Name or Narrator",
      "emotion": {
        "type": "neutral",
        "intensity": 0.5,
        "stability": 0.8,
        "style": 0.3,
        "description": "Brief emotional description"
      },
      "speech": {
        "speed": 1.0,
        "volume": 1.0,
        "pitch": "medium"
      },
      "position": {
        "vertical": "top",
        "horizontal": "left"
      }
    }
  ]
}

⚠️ CRITICAL RULES:
- Return ONLY valid JSON (no markdown, no code blocks, no explanations)
- Every dialogue MUST have ALL fields
- Sequence numbers must be continuous (1, 2, 3...)
- If page has no dialogues, return empty "dialogs": []
- Page types: story (main content), cover, title, credits, blank
"""

@retry_with_backoff()
def analyze_manga_page(page_image_path: Path, page_number: int, job_id: str) -> Dict[str, Any]:
    """Analyze a single manga page using Gemini Vision API."""
    
    # Load image
    image = PIL.Image.open(page_image_path)
    
    # Initialize Gemini
    model = initialize_gemini_client()
    prompt = create_analysis_prompt()
    
    try:
        # Generate analysis
        response = model.generate_content([prompt, image])
        json_text = response.text
        
        # Clean response
        if '```json' in json_text:
            json_text = json_text.split('```json')[1].split('```')[0].strip()
        elif '```' in json_text:
            json_text = json_text.split('```')[1].split('```')[0].strip()
        
        # Parse JSON
        result = json.loads(json_text)
        
        # Ensure page_number is set
        result['page_number'] = page_number
        
        # Convert old format if needed
        if 'panels' in result and 'dialogs' not in result:
            # Convert panels format to dialogs format
            dialogs = []
            sequence = 1
            for panel in result.get('panels', []):
                for dialogue in panel.get('dialogues', []):
                    dialogs.append({
                        'sequence': sequence,
                        'text': dialogue.get('text', ''),
                        'speaker': dialogue.get('speaker', 'Unknown'),
                        'emotion': {
                            'type': dialogue.get('emotion', 'neutral'),
                            'intensity': 0.5,
                            'stability': 0.8,
                            'style': 0.3,
                            'description': f"{dialogue.get('emotion', 'neutral')} tone"
                        },
                        'speech': {
                            'speed': 1.0,
                            'volume': 1.0,
                            'pitch': 'medium'
                        },
                        'position': {
                            'vertical': 'middle',
                            'horizontal': 'center'
                        }
                    })
                    sequence += 1
            result['dialogs'] = dialogs
            del result['panels']
        
        logging.info(f"✅ Page {page_number}: Found {len(result.get('dialogs', []))} dialogues")
        return result
        
    except json.JSONDecodeError as e:
        logging.error(f"JSON parsing error for page {page_number}: {e}")
        logging.error(f"Response: {response.text}")
        raise
    except Exception as e:
        logging.error(f"Error analyzing page {page_number}: {e}")
        raise

def process_manga_pages(image_paths: List[Path], job_id: str) -> Dict[str, Any]:
    """Process multiple manga pages."""
    
    all_results = {
        "pages": [],
        "total_dialogues": 0
    }
    
    for idx, image_path in enumerate(image_paths, 1):
        try:
            logging.info(f"📄 Analyzing page {idx}/{len(image_paths)}...")
            
            result = analyze_manga_page(image_path, idx, job_id)
            
            # Save individual page JSON
            json_filename = image_path.stem + '.json'
            json_path = MANGA_PAGES_DIR / json_filename
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            all_results["pages"].append(result)
            all_results["total_dialogues"] += len(result.get('dialogs', []))
            
        except Exception as e:
            logging.error(f"Failed to process page {idx} for job {job_id}: {e}")
            # Continue with next page
            continue
    
    if not all_results["pages"]:
        raise Exception(f"Failed to process any pages for job {job_id}")
    
    return all_results
