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
    """Create the comprehensive analysis prompt for Gemini with advanced dubbing features."""
    return """You are an expert Manga Analysis and Dubbing Orchestration AI. Analyze the provided manga page image and generate a comprehensive JSON object with ALL dialogues, emotional context, timing, visual synchronization, and highlighting data.

**CRITICAL RULES FOR RELIABLE DUBBING:**
1.  **Dialogue Completeness:** Include ALL text from ALL balloons and narration boxes on the page.
2.  **Panel Synchronization:** For EVERY dialogue, assign a **panel_id** (e.g., "page_000_panel_01", "page_000_panel_02"). This ID is used to identify which panel/area the dialogue belongs to for video synchronization.
3.  **Voice Assignment:** You MUST infer and include the **speaker_gender** (Male, Female, Narrator, Unknown) based on the character's visual appearance, name, and dialogue context.
4.  **Pacing/Realism:** To ensure natural local TTS output, keep the **speech.speed** tightly constrained between **0.95 and 1.05** (1.0 is default pace). Only use extreme values (0.8 or 1.2+) for very dramatic moments.
5.  **Text Highlighting (CRITICAL):** You MUST infer and include the exact pixel **bounding_box** of the text balloon or narration box in the format "x:y:w:h" (e.g., "100:200:300:50"). Coordinates should be relative to the full page image dimensions.
6.  **Timing (`time_gap_before_s`):** Estimate based on visual cues (character reactions, panel density, dialogue length, dramatic pauses). Range: 0.0 to 3.0 seconds.
7.  **Emotion (`type`, `intensity`):** Infer from facial expressions, body language, text bubble style (spikes for yelling, waves for thinking), and font size/style.

**STRICT OUTPUT CONSTRAINTS:**
1.  **NO EXTRA TEXT:** Output must be *only* the raw JSON object. **Do not** include markdown code block delimiters (e.g., ```json), explanations, or any conversational text.
2.  **READING ORDER (CRITICAL):** Process all dialogue strictly in the CORRECT reading order. For Western manga (English text): LEFT-TO-RIGHT, TOP-TO-BOTTOM. Read each panel's text bubbles from left to right, then move to the next panel. The sequence numbers MUST reflect the actual reading order. If a sentence is split across multiple bubbles, keep them in order!
3.  **ALL PAGES:** If analyzing multiple pages, output data for ALL pages, even if a page has no dialogue (use empty "dialogs": []).
4.  **BOUNDING BOX (MANDATORY):** Every dialogue MUST have a bounding_box. Estimate the pixel coordinates of the text balloon/box. This is REQUIRED for highlighting.

**JSON SCHEMA MANDATE:**
The output JSON must strictly adhere to the following schema. **All fields are mandatory** and must be populated. Use the specified value ranges for all numerical fields.

{
  "page_type": "story" | "cover" | "info" | "blank",
  "page_number": 1,
  "page_file_name": "page_000.png",
  "dialogs": [
    {
      "sequence": 1,
      "panel_id": "page_000_panel_01",
      "text": "[Exact dialogue or SFX text from the bubble/area]",
      "speaker": "Character Name" | "Narrator" | "SFX" | "UNKNOWN",
      "speaker_gender": "Male" | "Female" | "Narrator" | "Unknown",
      "time_gap_before_s": 0.5,
      "emotion": {
        "type": "calm" | "angry" | "yell" | "sad" | "excitement" | "narration" | "neutral" | "whisper" | "fear" | "surprise" | "awe" | "determination",
        "intensity": 0.8,
        "stability": 0.8,
        "style": 0.3,
        "description": "Visual-cue-based description of the emotional state."
      },
      "speech": {
        "speed": 1.0,
        "volume": 1.0,
        "pitch": "medium" | "high" | "low"
      },
      "position": {
        "vertical": "top" | "middle" | "bottom",
        "horizontal": "left" | "center" | "right"
      },
      "bounding_box": "x:y:w:h"
    }
  ]
}

**VALUE RANGES (MANDATORY):**
- time_gap_before_s: 0.0 to 3.0 seconds
- emotion.intensity: 0.1 to 1.0
- emotion.stability: 0.1 to 1.0
- emotion.style: 0.1 to 1.0
- speech.speed: 0.95 to 1.05 (constrained for natural TTS)
- speech.volume: 0.9 to 1.1 (constrained for natural TTS)
- bounding_box: "x:y:w:h" format (e.g., "100:200:300:50" means x=100px, y=200px, width=300px, height=50px)

**EXAMPLE bounding_box VALUES:**
- Top-right narration: "1400:100:400:50"
- Middle-left dialogue: "100:450:600:80"
- Bottom-center dialogue: "700:900:500:100"

**REMEMBER:** Output ONLY the JSON object. No markdown, no explanations, no extra text.
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
