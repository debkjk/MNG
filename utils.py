import os
from os.path import splitext, basename, exists
import cv2
import numpy as np

def get_files(directory, extensions=['.jpg', '.png', '.jpeg']):
    """Get all files with specified extensions in a directory."""
    files = []
    for filename in os.listdir(directory):
        if splitext(filename)[1].lower() in extensions:
            files.append(os.path.join(directory, filename))
    return sorted(files)

def load_image(image_path):
    """Load image from path using OpenCV."""
    if not exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Failed to load image: {image_path}")
    return img