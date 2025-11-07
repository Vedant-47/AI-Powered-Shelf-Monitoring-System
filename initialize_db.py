import sqlite3
import os
from datetime import datetime

class HerbalifeDB:
    def __init__(self):
        os.makedirs('data', exist_ok=True)
        self.conn = sqlite3.connect('data/herbalife.db')
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        # Products table with Herbalife-specific fields
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            product_type TEXT NOT NULL,
            product_code TEXT UNIQUE,
            flavor TEXT,
            variant TEXT,
            target_benefit TEXT,
            current_stock INTEGER DEFAULT 0,
            min_stock INTEGER,
            last_detected TIMESTAMP,
            image_path TEXT,
            is_active BOOLEAN DEFAULT TRUE
        )
        ''')

        # Shelf images table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS shelf_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT NOT NULL,
            capture_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            products_detected INTEGER,
            empty_spaces INTEGER
        )
        ''')

        # Alerts table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            alert_type TEXT CHECK(alert_type IN ('low_stock', 'misplacement', 'expiry')),
            alert_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
        ''')

        self.conn.commit()

    def initialize_sample_data(self):
        """Insert sample Herbalife products based on provided images"""
        sample_products = [
            ("HN - Skin Booster", "skin_booster", "345/1153", "orange", "Collagen Powder", "Skin Health", 0, 5),
            ("Formula 1 Shake Mix", "formula_1", "3433-3132", "vanilla", "Meal Replacement", "Weight Management", 0, 10),
            ("Vitilife Brain Solution", "vitamin_complex", None, None, "Capsules", "Cognitive Support", 0, 7),
            ("Collagen Booster", "collagen_mix", "152-153", None, "Liquid", "Joint Health", 0, 4),
            ("Specialty Fiber Blend", "specialty_blend", None, None, "Powder", "Digestive Health", 0, 3)
        ]
        
        self.cursor.executemany('''
        INSERT INTO products 
        (product_name, product_type, product_code, flavor, variant, target_benefit, current_stock, min_stock)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_products)
        
        self.conn.commit()

if __name__ == "__main__":
    db = HerbalifeDB()
    db.initialize_sample_data()
    print("Herbalife database initialized with sample products.")