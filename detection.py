import os
import cv2
import numpy as np
import pytesseract
import re
from ultralytics import YOLO
from PIL import Image
import yaml
from datetime import datetime

class HerbalifeDetector:
    def __init__(self):
        # Set path to Tesseract executable
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

        # Load configuration from YAML
        with open('config/config.yaml') as f:
            self.config = yaml.safe_load(f)

        # Load thresholds
        self.empty_space_threshold = self.config['alert_thresholds'].get('empty_space', 0.2)
        self.low_stock_threshold = self.config['alert_thresholds'].get('low_stock', 3)

        self.product_thresholds = {
            'skin_booster': self.config['alert_thresholds'].get('skin_booster', 5),
            'formula_1': self.config['alert_thresholds'].get('formula_1', 10),
            'vitamin_complex': self.config['alert_thresholds'].get('vitamin_complex', 7),
            'collagen_mix': self.config['alert_thresholds'].get('collagen_mix', 4),
            'specialty_blend': self.config['alert_thresholds'].get('specialty_blend', 3)
        }

        # Load YOLO model
        self.model = YOLO(self.config['paths']['model'])

    def preprocess_image(self, image_path):
        """Enhance image for better OCR accuracy"""
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image at {image_path}")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        return denoised

    def extract_product_info(self, image_path):
        """Extract details like type, code, and flavor from cropped image"""
        processed_img = self.preprocess_image(image_path)
        text = pytesseract.image_to_string(processed_img, config='--oem 3 --psm 6')

        product_info = {
            'type': None,
            'code': None,
            'flavor': None,
            'variant': None
        }

        # Detect product type using keywords
        for p_type, terms in self.config['herbalife_config']['product_types'].items():
            if any(term.lower() in text.lower() for term in terms):
                product_info['type'] = p_type
                break

        # Extract product code using regex
        code_pattern = self.config['herbalife_config']['product_codes']['pattern']
        code_match = re.search(code_pattern, text)
        if code_match:
            product_info['code'] = code_match.group()

        # Detect flavor
        for flavor in self.config['herbalife_config']['flavors']:
            if flavor.lower() in text.lower():
                product_info['flavor'] = flavor
                break

        return product_info

    def analyze_shelf(self, image_path):
        """Analyze shelf image to identify products and check for missing ones"""
        img = cv2.imread(image_path)
        if img is None:
            return {'error': f"Could not read image at {image_path}"}

        # Use YOLO to detect objects
        results = self.model.predict(source=img)
        detections = results[0].boxes.xyxy.cpu().numpy()

        products = []
        detected_types = set()

        for box in detections:
            x1, y1, x2, y2 = map(int, box)
            cropped_img = Image.open(image_path).crop((x1, y1, x2, y2))
            temp_path = f"temp_crop_{x1}_{y1}.jpg"
            cropped_img.save(temp_path)

            product_info = self.extract_product_info(temp_path)
            if product_info['type']:
                detected_types.add(product_info['type'])

            products.append({
                'bbox': [x1, y1, x2, y2],
                'info': product_info
            })

            os.remove(temp_path)  # Remove temporary cropped file

        # Compare with expected products to find missing ones
        expected_products = set(self.config.get('expected_products', []))
        missing_products = expected_products - detected_types

        alerts = [
            {
                'alert_type': 'missing_product',
                'message': f"Product '{missing}' is missing from the shelf."
            }
            for missing in missing_products
        ]

        return {
            'image_path': image_path,
            'products': products,
            'timestamp': str(datetime.now()),
            'alerts': alerts
        }

