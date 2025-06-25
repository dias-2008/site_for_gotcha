#!/usr/bin/env python3
"""
Database Manager for Gotcha Guardian Payment Server
Handles all database operations with connection pooling and error handling
"""

import sqlite3
import logging
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class Purchase:
    """Purchase data model"""
    id: Optional[int] = None
    email: str = ""
    product_id: str = ""
    amount: float = 0.0
    paypal_payment_id: Optional[str] = None
    activation_key: Optional[str] = None
    purchase_date: Optional[datetime] = None
    status: str = "pending"
    download_count: int = 0
    last_download: Optional[datetime] = None


@dataclass
class ActivationKey:
    """Activation key data model"""
    id: Optional[int] = None
    product_id: str = ""
    activation_key: str = ""
    used: bool = False
    created_date: Optional[datetime] = None


class DatabaseManager:
    """Enhanced database manager with connection pooling and error handling"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
        self._db_path = self._get_db_path()
        
    def _get_db_path(self) -> str:
        """Get database path from configuration"""
        db_config = self.config.get_database_config()
        if db_config['engine'] == 'sqlite':
            return db_config['database']
        else:
            # For other databases, we'll use SQLite as fallback
            self.logger.warning("Non-SQLite database configured, falling back to SQLite")
            return 'payments.db'
    
    @contextmanager
    def get_connection(self):
        """Get database connection with automatic cleanup"""
        conn = None
        try:
            conn = sqlite3.connect(self._db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            conn.execute('PRAGMA foreign_keys = ON')  # Enable foreign key constraints
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    def check_connection(self) -> bool:
        """Check if database connection is working"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1')
                return True
        except Exception as e:
            self.logger.error(f"Database connection check failed: {str(e)}")
            return False
    
    def initialize_database(self) -> bool:
        """Initialize database with required tables"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create purchases table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS purchases (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT NOT NULL,
                        product_id TEXT NOT NULL,
                        amount REAL NOT NULL,
                        paypal_payment_id TEXT,
                        activation_key TEXT UNIQUE,
                        purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'pending',
                        download_count INTEGER DEFAULT 0,
                        last_download TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create activation_keys table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS activation_keys (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id TEXT NOT NULL,
                        activation_key TEXT UNIQUE NOT NULL,
                        used BOOLEAN DEFAULT FALSE,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        used_date TIMESTAMP,
                        purchase_id INTEGER,
                        FOREIGN KEY (purchase_id) REFERENCES purchases (id)
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_purchases_email ON purchases(email)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_purchases_activation_key ON purchases(activation_key)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_purchases_paypal_id ON purchases(paypal_payment_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_purchases_status ON purchases(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_activation_keys_key ON activation_keys(activation_key)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_activation_keys_product ON activation_keys(product_id)')
                
                # Create trigger to update updated_at timestamp
                cursor.execute('''
                    CREATE TRIGGER IF NOT EXISTS update_purchases_timestamp 
                    AFTER UPDATE ON purchases
                    BEGIN
                        UPDATE purchases SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                    END
                ''')
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Database initialization failed: {str(e)}")
            return False
    
    def create_purchase(self, email: str, product_id: str, amount: float, 
                      paypal_payment_id: str, status: str = 'pending') -> Optional[int]:
        """Create a new purchase record"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO purchases 
                       (email, product_id, amount, paypal_payment_id, status) 
                       VALUES (?, ?, ?, ?, ?)""",
                    (email, product_id, amount, paypal_payment_id, status)
                )
                conn.commit()
                purchase_id = cursor.lastrowid
                self.logger.info(f"Purchase created: ID {purchase_id}, Email: {email}, Product: {product_id}")
                return purchase_id
        except Exception as e:
            self.logger.error(f"Failed to create purchase: {str(e)}")
            return None
    
    def update_purchase_status(self, paypal_payment_id: str, status: str, 
                             activation_key: Optional[str] = None) -> bool:
        """Update purchase status and activation key"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if activation_key:
                    cursor.execute(
                        """UPDATE purchases 
                           SET status = ?, activation_key = ? 
                           WHERE paypal_payment_id = ?""",
                        (status, activation_key, paypal_payment_id)
                    )
                else:
                    cursor.execute(
                        """UPDATE purchases 
                           SET status = ? 
                           WHERE paypal_payment_id = ?""",
                        (status, paypal_payment_id)
                    )
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info(f"Purchase updated: PayPal ID {paypal_payment_id}, Status: {status}")
                    return True
                else:
                    self.logger.warning(f"No purchase found with PayPal ID: {paypal_payment_id}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to update purchase: {str(e)}")
            return False
    
    def get_purchase_by_paypal_id(self, paypal_payment_id: str) -> Optional[Dict[str, Any]]:
        """Get purchase by PayPal payment ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT * FROM purchases 
                       WHERE paypal_payment_id = ?""",
                    (paypal_payment_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get purchase by PayPal ID: {str(e)}")
            return None
    
    def get_purchase_by_activation_key(self, activation_key: str) -> Optional[Dict[str, Any]]:
        """Get purchase by activation key"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT * FROM purchases 
                       WHERE activation_key = ? AND status = 'completed'""",
                    (activation_key,)
                )
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get purchase by activation key: {str(e)}")
            return None
    
    def update_download_count(self, activation_key: str) -> bool:
        """Update download count and timestamp"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """UPDATE purchases 
                       SET download_count = download_count + 1, 
                           last_download = CURRENT_TIMESTAMP 
                       WHERE activation_key = ?""",
                    (activation_key,)
                )
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info(f"Download count updated for activation key: {activation_key[:8]}...")
                    return True
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to update download count: {str(e)}")
            return False
    
    def get_all_purchases(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get all purchases with pagination"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT * FROM purchases 
                       ORDER BY purchase_date DESC 
                       LIMIT ? OFFSET ?""",
                    (limit, offset)
                )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Failed to get all purchases: {str(e)}")
            return []
    
    def get_purchases_by_email(self, email: str) -> List[Dict[str, Any]]:
        """Get all purchases for a specific email"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT * FROM purchases 
                       WHERE email = ? 
                       ORDER BY purchase_date DESC""",
                    (email,)
                )
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Failed to get purchases by email: {str(e)}")
            return []
    
    def get_purchase_stats(self) -> Dict[str, Any]:
        """Get purchase statistics"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Total purchases
                cursor.execute("SELECT COUNT(*) FROM purchases WHERE status = 'completed'")
                total_purchases = cursor.fetchone()[0]
                
                # Total revenue
                cursor.execute("SELECT SUM(amount) FROM purchases WHERE status = 'completed'")
                total_revenue = cursor.fetchone()[0] or 0.0
                
                # Products sold
                cursor.execute(
                    """SELECT product_id, COUNT(*) as count 
                       FROM purchases 
                       WHERE status = 'completed' 
                       GROUP BY product_id"""
                )
                products_sold = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Recent purchases (last 7 days)
                cursor.execute(
                    """SELECT COUNT(*) FROM purchases 
                       WHERE status = 'completed' 
                       AND purchase_date >= datetime('now', '-7 days')"""
                )
                recent_purchases = cursor.fetchone()[0]
                
                return {
                    'total_purchases': total_purchases,
                    'total_revenue': total_revenue,
                    'products_sold': products_sold,
                    'recent_purchases': recent_purchases
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get purchase stats: {str(e)}")
            return {
                'total_purchases': 0,
                'total_revenue': 0.0,
                'products_sold': {},
                'recent_purchases': 0
            }
    
    def cleanup_old_pending_purchases(self, hours: int = 24) -> int:
        """Clean up old pending purchases"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """DELETE FROM purchases 
                       WHERE status = 'pending' 
                       AND purchase_date < datetime('now', '-{} hours')""".format(hours)
                )
                conn.commit()
                deleted_count = cursor.rowcount
                
                if deleted_count > 0:
                    self.logger.info(f"Cleaned up {deleted_count} old pending purchases")
                
                return deleted_count
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old purchases: {str(e)}")
            return 0
    
    def create_activation_key(self, product_id: str, activation_key: str) -> bool:
        """Create a pre-generated activation key"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO activation_keys (product_id, activation_key) 
                       VALUES (?, ?)""",
                    (product_id, activation_key)
                )
                conn.commit()
                self.logger.info(f"Activation key created for product: {product_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to create activation key: {str(e)}")
            return False
    
    def get_unused_activation_key(self, product_id: str) -> Optional[str]:
        """Get an unused activation key for a product"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """SELECT activation_key FROM activation_keys 
                       WHERE product_id = ? AND used = FALSE 
                       ORDER BY created_date ASC 
                       LIMIT 1""",
                    (product_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return row[0]
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get unused activation key: {str(e)}")
            return None
    
    def mark_activation_key_used(self, activation_key: str, purchase_id: int) -> bool:
        """Mark an activation key as used"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """UPDATE activation_keys 
                       SET used = TRUE, used_date = CURRENT_TIMESTAMP, purchase_id = ? 
                       WHERE activation_key = ?""",
                    (purchase_id, activation_key)
                )
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info(f"Activation key marked as used: {activation_key[:8]}...")
                    return True
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to mark activation key as used: {str(e)}")
            return False
    
    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database"""
        try:
            import shutil
            shutil.copy2(self._db_path, backup_path)
            self.logger.info(f"Database backed up to: {backup_path}")
            return True
        except Exception as e:
            self.logger.error(f"Database backup failed: {str(e)}")
            return False