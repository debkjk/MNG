import google.generativeai as genai
from google.api_core import exceptions
import PIL.Image
from pathlib import Path
import json
import logging
import os
from typing import List, Dict, Any, Optional
import time
import functools

# Configuration
PANELS_DIR = Path(__file__).resolve().parent.parent / 'static' / 'panels'
PANELS_DIR.mkdir(parents=True, exist_ok=True)

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
    return """Analyze this manga page and return a structured JSON response with four unified tasks:

1. Panel Detection: Identify all manga panels with accurate pixel coordinates
2. Reading Order: Japanese manga reads right-to-left, top-to-bottom
3. Dialogue Extraction: Extract text from speech bubbles, thought bubbles, and narration
4. Emotion Detection: Classify dialogue emotions

Rules:
- Bounding boxes must use exact pixel coordinates
- Reading order starts at 1 and increases sequentially
- Exclude sound effects from dialogue
- For panels without dialogue, include empty dialogues array
- Use visual separation for overlapping panels

Return JSON in this exact format:
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
        result = json.loads(response.text)
        
    except json.JSONDecodeError:
        # Retry once with clarified prompt
        response = model.generate_content([prompt + "\nEnsure response is valid JSON.", image])
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
    job_panels_dir = PANELS_DIR / job_id
    job_panels_dir.mkdir(parents=True, exist_ok=True)
    panel_paths = []
    
    try:
        page_img = PIL.Image.open(page_image_path)
        width, height = page_img.size
        
        # Sort panels by reading order
        panels = sorted(analysis_result.get('panels', []), key=lambda p: p['reading_order'])
        
        for panel in panels:
            try:
                bbox = panel['bounding_box']
                x, y = max(0, bbox['x']), max(0, bbox['y'])
                w, h = min(width - x, bbox['width']), min(height - y, bbox['height'])
                
                if w <= 0 or h <= 0:
                    logging.warning(f"Invalid panel dimensions for page {page_number}, panel {panel['reading_order']}")
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