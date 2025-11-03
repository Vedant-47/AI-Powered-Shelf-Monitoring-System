import sqlite3
from datetime import datetime
import yaml
from typing import List, Dict, Optional

class Database:
    def __init__(self):
        with open('config/config.yaml') as f:
            self.config = yaml.safe_load(f)
        self.conn = sqlite3.connect(self.config['paths']['database'])
        self.cursor = self.conn.cursor()
        
    def add_product(self, name: str, category: str, barcode: str, image_path: str, min_stock: int = 3):
        """Add a new product to the database"""
        self.cursor.execute('''
        INSERT INTO products (name, category, barcode, image_path, min_stock)
        VALUES (?, ?, ?, ?, ?)
        ''', (name, category, barcode, image_path, min_stock))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def add_shelf_image(self, image_path: str):
        """Add a new shelf image to the database"""
        self.cursor.execute('''
        INSERT INTO shelf_images (image_path)
        VALUES (?)
        ''', (image_path,))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def add_alert(self, product_id: Optional[int], alert_type: str):
        """Add a new alert to the database"""
        self.cursor.execute('''
        INSERT INTO alerts (product_id, alert_type)
        VALUES (?, ?)
        ''', (product_id, alert_type))
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_active_alerts(self):
        """Get all unresolved alerts"""
        self.cursor.execute('''
        SELECT a.id, p.name, a.alert_type, a.alert_date
        FROM alerts a
        LEFT JOIN products p ON a.product_id = p.id
        WHERE a.resolved = FALSE
        ORDER BY a.alert_date DESC
        ''')
        return self.cursor.fetchall()
    
    def get_products(self):
        """Get all products"""
        self.cursor.execute('SELECT id, name, category, current_stock, min_stock FROM products')
        return self.cursor.fetchall()
    
    def update_product_stock(self, product_id: int, new_stock: int):
        """Update product stock level"""
        self.cursor.execute('''
        UPDATE products
        SET current_stock = ?
        WHERE id = ?
        ''', (new_stock, product_id))
        self.conn.commit()
        
        # Check if stock is below threshold
        self.cursor.execute('SELECT min_stock FROM products WHERE id = ?', (product_id,))
        min_stock = self.cursor.fetchone()[0]
        if new_stock < min_stock:
            self.add_alert(product_id, 'low_stock')
    
    def __del__(self):
        self.conn.close()