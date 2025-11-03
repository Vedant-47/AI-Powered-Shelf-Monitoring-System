import os
import yaml
from datetime import datetime
import cv2
import numpy as np
from PIL import Image

def load_config():
    """Load configuration from YAML file"""
    with open('config/config.yaml') as f:
        return yaml.safe_load(f)

def ensure_directory_exists(path):
    """Ensure a directory exists, create if it doesn't"""
    os.makedirs(path, exist_ok=True)
    return path

def save_uploaded_file(uploaded_file, upload_dir, prefix=""):
    """Save an uploaded file (from Streamlit) to the specified directory"""
    ensure_directory_exists(upload_dir)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_ext = os.path.splitext(uploaded_file.name)[1]
    filename = f"{prefix}{timestamp}{file_ext}"
    filepath = os.path.join(upload_dir, filename)
    
    # Save the file
    with open(filepath, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    return filepath

def draw_boxes_on_image(image_path, boxes, color=(0, 255, 0), thickness=2):
    """
    Draw bounding boxes on an image
    Args:
        image_path: Path to the image file
        boxes: List of bounding boxes in format [x1, y1, x2, y2]
        color: Tuple of (B, G, R) values
        thickness: Line thickness
    Returns:
        Image with boxes drawn (as numpy array)
    """
    img = cv2.imread(image_path)
    for box in boxes:
        x1, y1, x2, y2 = map(int, box)
        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
    return img

def calculate_coverage(boxes, image_shape):
    """
    Calculate the percentage of image covered by bounding boxes
    Args:
        boxes: List of bounding boxes in format [x1, y1, x2, y2]
        image_shape: Tuple of (height, width)
    Returns:
        Coverage percentage (0-1)
    """
    total_area = image_shape[0] * image_shape[1]
    if total_area == 0:
        return 0.0
    
    product_area = 0
    for box in boxes:
        x1, y1, x2, y2 = box
        product_area += (x2 - x1) * (y2 - y1)
    
    return product_area / total_area

def resize_image(image, max_width=800):
    """
    Resize an image while maintaining aspect ratio
    Args:
        image: Input image (numpy array or PIL Image)
        max_width: Maximum width for the output image
    Returns:
        Resized image (PIL Image)
    """
    if isinstance(image, np.ndarray):
        image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    
    width, height = image.size
    if width > max_width:
        ratio = max_width / float(width)
        new_height = int(height * ratio)
        image = image.resize((max_width, new_height), Image.LANCZOS)
    
    return image

def get_product_categories():
    """Load product categories from config"""
    config = load_config()
    return config.get('product_categories', [])