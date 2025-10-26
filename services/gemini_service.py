import google.generativeai as genai
from google.api_core import exceptions
import PIL.Image
from pathlib import Path
import json
import logging
import os
import re
from typing import List, Dict, Any, Optional
import time
import functools

# Configuration
PANELS_DIR = Path(__file__).resolve().parent.parent / 'static' / 'panels'
PANELS_DIR.mkdir(parents=True, exist_ok=True)

def normalize_json_string(json_str):
    """
    Normalize JSON string by converting all quotes to double quotes and fixing newlines.
    """
    # First pass - normalize all basic quote patterns
    patterns = [
        (r"'([^']*)':", r'"\1":'),  # Keys
        (r":\s*'([^']*)'([,}])", r':"\1"\2'),  # Values
        (r"'([^']*)'", r'"\1"'),  # Any remaining quotes
    ]
    
    normalized = json_str
    for pattern, replacement in patterns:
        normalized = re.sub(pattern, replacement, normalized)
    
    # Second pass - handle any nested structures
    try:
        # Test if it's valid JSON now
        json.loads(normalized)
    except json.JSONDecodeError:
        # If still invalid, try more aggressive normalization
        normalized = normalized.replace("'", '"')
        normalized = re.sub(r'"([^"]*)":', r'"\1":', normalized)  # Fix any doubled quotes in keys
        normalized = re.sub(r':\s*"([^"]*)"([,}])', r':"\1"\2', normalized)  # Fix any doubled quotes in values
        
    # Clean up newlines and whitespace
    normalized = re.sub(r'\s+', ' ', normalized)
    normalized = normalized.replace('\\n', ' ')
    
    return normalized

def retry_with_backoff(max_retries=3, initial_delay=1):
    """Decorator for API call retry logic with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_error = None
            for retry in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions.ResourceExhausted as e:
                    last_error = e
                    if retry == max_retries - 1:
                        raise
                    time.sleep(delay)
                    delay *= 2
            raise last_error  # Re-raise the last error if all retries failed
        return wrapper
    return decorator

def initialize_gemini_client():
    """Initialize and configure the Gemini API client."""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set")
    
    genai.configure(api_key=api_key)
    
    # Configure generation parameters
    generation_config = genai.types.GenerationConfig(
        temperature=0.1,  # Low temperature for consistent structured output
        top_p=0.95,
        top_k=40,
    )
    
    # Configure safety settings for manga content
    safety_settings = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_ONLY_HIGH",
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_ONLY_HIGH",
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_ONLY_HIGH",
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_ONLY_HIGH",
        },
    ]
    
    try:
        # Try Gemini 2.0 Flash Experimental first
        model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            generation_config=generation_config,
            safety_settings=safety_settings
        )
    except Exception:
        # Fallback to Gemini 1.5 Flash
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config=generation_config,
            safety_settings=safety_settings
        )
    
    return model

def create_analysis_prompt() -> str:
    """Create the comprehensive prompt for manga page analysis."""
    return """Your task is to analyze this manga page and return ONLY a JSON object. First, determine if this is a story page or a title/intro/outro page.

PAGE CLASSIFICATION:
1. Story pages: Contains sequential narrative panels with character dialogue/action
2. Non-story pages: Title pages, chapter covers, credits, advertisements, etc.

For non-story pages, return:
{
    "page_type": "non_story",
    "type_details": "title_page|chapter_cover|credits|advertisement",
    "panels": []
}

For story pages, analyze the following:
1. Story Panel Detection: 
   - Only include panels that advance the story
   - Must contain character actions, dialogue, or important plot elements
   - Ignore decorative borders, background elements, or non-story art
2. Reading Order: Japanese manga reads right-to-left, top-to-bottom
3. Dialogue Extraction: From speech bubbles, thought bubbles, and narration
4. Emotion Detection: For character dialogue

Critical Requirements:
- Return pure JSON without any markdown or extra text
- Use integer coordinates for bounding boxes
- Only extract actual story panels
- Skip purely decorative elements

For story pages, use this JSON structure:
{
  "panels": [
    {
      "panel_number": 1,
      "reading_order": 1,
      "bounding_box": {"x": 0, "y": 0, "width": 500, "height": 600},
      "dialogues": [
        {
          "text": "dialogue text here",
          "speaker": "character name or 'narrator'",
          "emotion": "happy|sad|angry|surprised|neutral|excited|scared"
        }
      ]
    }
  ]
}"""

@retry_with_backoff()
def analyze_manga_page(page_image_path: Path, page_number: int, job_id: str) -> Dict[str, Any]:
    """Analyze a single manga page using Gemini Vision API."""
    start_time = time.time()
    
    # Load and prepare image
    image = PIL.Image.open(page_image_path)
    width, height = image.size
    
    # Initialize Gemini client
    model = initialize_gemini_client()
    prompt = create_analysis_prompt()
    
    try:
        # Generate analysis
        response = model.generate_content([prompt, image])
        
        # Print response for debugging
        logging.info(f"Raw Gemini response for page {page_number}: {response.text}")
        
        # Clean and normalize the response text first
        json_text = response.text
        
        # Strip any markdown code blocks
        if '```json' in json_text:
            json_text = json_text.split('```json')[1].split('```')[0].strip()
        elif '```' in json_text:
            json_text = json_text.split('```')[1].split('```')[0].strip()
            
        # First pass - fix quotes and basic structure
        json_text = json_text.replace("'", '"')  # Replace all single quotes
        
        # Fix escaping and special characters
        json_text = re.sub(r'(?<!\\)"', '\\"', json_text)  # Escape unescaped double quotes
        json_text = re.sub(r'\\+"', '"', json_text)  # Fix over-escaped quotes
        
        # Clean up newlines and extra whitespace
        json_text = re.sub(r'\s+', ' ', json_text)
        
        try:
            # Try parsing the cleaned JSON
            result = json.loads(json_text)
        except json.JSONDecodeError:
            # If still invalid, try more aggressive cleaning
            json_text = re.sub(r'([{,])\s*"([^"]+)"\s*:', r'\1"\2":', json_text)  # Fix key format
            json_text = re.sub(r':\s*"([^"]+)"([,}])', r':"\1"\2', json_text)  # Fix value format
            result = json.loads(json_text)
        
        # Handle non-story pages
        if result.get('page_type') == 'non_story':
            logging.info(f"Page {page_number} identified as {result.get('type_details')} - skipping panel extraction")
            return {
                'page_number': page_number,
                'page_type': result.get('page_type'),
                'type_details': result.get('type_details'),
                'panels': []
            }
        
    except json.JSONDecodeError as e:
        logging.error(f"JSON parsing error for page {page_number}: {e}\nResponse text: {response.text}")
        # Retry with explicit JSON request
        clarified_prompt = prompt + "\nIMPORTANT: Response must be valid JSON without any markdown code blocks or additional text."
        response = model.generate_content([clarified_prompt, image])
        result = json.loads(response.text)
        
    except genai.types.BlockedPromptException as e:
        logging.warning(f"Content safety block for page {page_number}, job {job_id}: {e}")
        raise  # Let retry decorator handle it
        
    except genai.types.StopCandidateException:
        # Retry with lower temperature
        logging.warning(f"StopCandidate encountered for page {page_number}, retrying with lower temperature")
        generation_config = genai.types.GenerationConfig(temperature=0.05)
        response = model.generate_content([prompt, image], generation_config=generation_config)
        result = json.loads(response.text)
    
    # Add metadata and validate result
    result['page_number'] = page_number
    result['image_dimensions'] = {'width': width, 'height': height}
    
    if 'panels' not in result:
        raise ValueError("Missing 'panels' key in response")
    
    processing_time = time.time() - start_time
    logging.info(f"Page {page_number} analyzed in {processing_time:.2f}s for job {job_id}")
    return result

def extract_panel_images(
    page_image_path: Path,
    analysis_result: Dict[str, Any],
    job_id: str,
    page_number: int
) -> List[Path]:
    """Extract individual panel images based on analysis results."""
    # Skip if this is a non-story page
    if analysis_result.get('page_type') == 'non_story':
        return []
        
    job_panels_dir = PANELS_DIR / job_id
    job_panels_dir.mkdir(parents=True, exist_ok=True)
    panel_paths = []
    
    try:
        page_img = PIL.Image.open(page_image_path)
        width, height = page_img.size
        
        # Sort panels by reading order
        panels = sorted(analysis_result.get('panels', []), key=lambda p: p['reading_order'])
        
        # Calculate minimum panel size thresholds
        min_width = width * 0.1  # Panel must be at least 10% of page width
        min_height = height * 0.1  # Panel must be at least 10% of page height
        
        for panel in panels:
            try:
                bbox = panel['bounding_box']
                x, y = max(0, bbox['x']), max(0, bbox['y'])
                w, h = min(width - x, bbox['width']), min(height - y, bbox['height'])
                
                # Skip panels that are too small (likely decorative elements)
                if w < min_width or h < min_height:
                    logging.info(f"Skipping small panel on page {page_number}, panel {panel['reading_order']} ({w}x{h})")
                    continue
                    
                # Skip panels that take up almost the entire page (likely background)
                if w > width * 0.95 and h > height * 0.95:
                    logging.info(f"Skipping full-page panel on page {page_number}, panel {panel['reading_order']}")
                    continue
                
                # Skip panels without any dialogue (unless it's explicitly marked as important)
                if not panel.get('dialogues') and not panel.get('is_important', False):
                    logging.info(f"Skipping panel without dialogue on page {page_number}, panel {panel['reading_order']}")
                    continue
                
                # Crop and save panel
                panel_img = page_img.crop((x, y, x + w, y + h))
                output_path = job_panels_dir / f"panel_p{page_number:03d}_r{panel['reading_order']:02d}.png"
                panel_img.save(str(output_path))
                panel_paths.append(output_path)
                
            except Exception as e:
                logging.warning(f"Failed to extract panel from page {page_number}: {e}")
                continue
                
        return panel_paths
        
    except Exception as e:
        logging.error(f"Failed to extract panels from page {page_number}: {e}")
        return []

def process_manga_pages(page_image_paths: List[Path], job_id: str) -> Dict[str, Any]:
    """Process all manga pages for a job."""
    results = {
        "pages": [],
        "total_panels": 0,
        "total_dialogues": 0
    }
    
    for page_number, page_path in enumerate(page_image_paths, 1):
        try:
            # Add small delay between pages
            if page_number > 1:
                time.sleep(0.5)
            
            # Analyze page
            analysis = analyze_manga_page(page_path, page_number, job_id)
            
            # Extract panels
            panel_paths = extract_panel_images(page_path, analysis, job_id, page_number)
            
            # Create mapping of reading_order to panel paths
            panel_path_map = {}
            for path in panel_paths:
                # Extract reading order from filename (panel_p001_r02.png -> 2)
                reading_order = int(path.stem.split('_r')[1])
                panel_path_map[reading_order] = str(path)  # Convert path to string
            
            # Update panel data with extracted image paths
            for panel in analysis.get('panels', []):
                reading_order = panel['reading_order']
                if reading_order in panel_path_map:
                    panel['panel_path'] = panel_path_map[reading_order]
            
            # Aggregate results
            page_result = {
                'page_number': page_number,
                'panels': analysis.get('panels', [])
            }
            results['pages'].append(page_result)
            
            # Update counters
            results['total_panels'] += len(panel_paths)
            results['total_dialogues'] += sum(len(p.get('dialogues', [])) for p in analysis.get('panels', []))
            
            logging.info(f"Processed page {page_number}/{len(page_image_paths)} with {len(panel_paths)} panels for job {job_id}")
            
        except Exception as e:
            logging.error(f"Failed to process page {page_number} for job {job_id}: {e}")
            continue
    
    if not results['pages']:
        raise Exception(f"Failed to process any pages for job {job_id}")
        
    return results