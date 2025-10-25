import fitz  # PyMuPDF
from pathlib import Path
import logging
from typing import List
import shutil

# Configuration
DPI = 300  # High resolution for manga detail preservation
IMAGE_FORMAT = 'png'  # Lossless format for quality
PAGES_DIR = Path(__file__).resolve().parent.parent / 'static' / 'pages'

# Ensure output directory exists
PAGES_DIR.mkdir(parents=True, exist_ok=True)

def convert_pdf_to_images(pdf_path: Path, job_id: str) -> List[Path]:
    """
    Convert a PDF file to high-resolution PNG images.
    
    Args:
        pdf_path: Path to the uploaded PDF file
        job_id: Unique identifier for the job
        
    Returns:
        List[Path]: List of paths to the generated images in page order
        
    Raises:
        Exception: If PDF processing fails
    """
    job_dir = PAGES_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    image_paths = []
    
    doc = None
    try:
        doc = fitz.open(str(pdf_path))
        
        # Calculate zoom matrix for desired DPI
        zoom = DPI / 72  # PDF standard DPI is 72
        matrix = fitz.Matrix(zoom, zoom)
        
        # Convert each page
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            
            # Generate output path with zero-padded page number
            output_path = job_dir / f"page_{page_num:03d}.{IMAGE_FORMAT}"
            pix.save(str(output_path))
            image_paths.append(output_path)
            
            logging.info(f"Converted page {page_num + 1}/{len(doc)} for job {job_id}")
        
        return image_paths
        
    except fitz.FileDataError as e:
        logging.error(f"Invalid or corrupted PDF for job {job_id}: {e}")
        raise Exception(f"Invalid or corrupted PDF file: {e}")
    except Exception as e:
        logging.error(f"Failed to process PDF for job {job_id}: {e}")
        raise Exception(f"PDF processing failed: {e}")
    finally:
        if doc is not None:
            doc.close()
        
def validate_pdf(pdf_path: Path) -> bool:
    """
    Validate that a file is a valid PDF document.
    
    Args:
        pdf_path: Path to the PDF file to validate
        
    Returns:
        bool: True if valid PDF, False otherwise
    """
    try:
        doc = fitz.open(str(pdf_path))
        is_valid = doc.is_pdf
        doc.close()
        return is_valid
    except Exception:
        return False

def cleanup_page_images(job_id: str) -> None:
    """
    Remove all page images for a specific job.
    
    Args:
        job_id: Unique identifier for the job
    """
    try:
        job_dir = PAGES_DIR / job_id
        if job_dir.exists():
            shutil.rmtree(job_dir)
            logging.info(f"Cleaned up page images for job {job_id}")
    except Exception as e:
        logging.error(f"Failed to cleanup page images for job {job_id}: {e}")
        # Don't raise - cleanup failure shouldn't stop processing