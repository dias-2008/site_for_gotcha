#!/usr/bin/env python3
"""
Product Service for Gotcha Guardian Payment Server
Handles product management, downloads, and file operations
"""

import os
import logging
import hashlib
import zipfile
import tempfile
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import mimetypes
from pathlib import Path


class ProductService:
    """Enhanced product service with file management and security"""
    
    def __init__(self, config, database_manager):
        self.config = config
        self.db = database_manager
        self.logger = logging.getLogger(__name__)
        self.products = self._load_products()
        self.download_dir = self._get_download_directory()
        
    def _load_products(self) -> Dict[str, Dict[str, Any]]:
        """Load product definitions from configuration"""
        try:
            # Default products - in production, this could come from database or config file
            products = {
                'gotcha_guardian_basic': {
                    'id': 'gotcha_guardian_basic',
                    'name': 'Gotcha Guardian Basic',
                    'description': 'Basic version of Gotcha Guardian with essential features',
                    'price': 29.99,
                    'file_path': 'gotcha_guardian_basic.zip',
                    'file_size': '15.2 MB',
                    'version': '1.0.0',
                    'requirements': 'Windows 10+, 4GB RAM',
                    'features': [
                        'Real-time protection',
                        'Basic scanning',
                        'Email support'
                    ],
                    'download_limit': 5,
                    'active': True
                },
                'gotcha_guardian_pro': {
                    'id': 'gotcha_guardian_pro',
                    'name': 'Gotcha Guardian Pro',
                    'description': 'Professional version with advanced features',
                    'price': 59.99,
                    'file_path': 'gotcha_guardian_pro.zip',
                    'file_size': '28.5 MB',
                    'version': '1.0.0',
                    'requirements': 'Windows 10+, 8GB RAM',
                    'features': [
                        'Advanced real-time protection',
                        'Deep scanning',
                        'Behavioral analysis',
                        'Priority support',
                        'Automatic updates'
                    ],
                    'download_limit': 10,
                    'active': True
                },
                'gotcha_guardian_enterprise': {
                    'id': 'gotcha_guardian_enterprise',
                    'name': 'Gotcha Guardian Enterprise',
                    'description': 'Enterprise solution for businesses',
                    'price': 199.99,
                    'file_path': 'gotcha_guardian_enterprise.zip',
                    'file_size': '45.8 MB',
                    'version': '1.0.0',
                    'requirements': 'Windows Server 2016+, 16GB RAM',
                    'features': [
                        'All Pro features',
                        'Centralized management',
                        'Multi-device licensing',
                        'Custom policies',
                        'Dedicated support',
                        'API access'
                    ],
                    'download_limit': -1,  # Unlimited
                    'active': True
                }
            }
            
            self.logger.info(f"Loaded {len(products)} products")
            return products
            
        except Exception as e:
            self.logger.error(f"Failed to load products: {str(e)}")
            return {}
    
    def _get_download_directory(self) -> str:
        """Get the directory where product files are stored"""
        try:
            app_config = self.config.get_app_config()
            download_dir = app_config.get('download_directory', 'downloads')
            
            # Create directory if it doesn't exist
            os.makedirs(download_dir, exist_ok=True)
            
            return download_dir
            
        except Exception as e:
            self.logger.error(f"Failed to get download directory: {str(e)}")
            return 'downloads'
    
    def get_all_products(self) -> List[Dict[str, Any]]:
        """Get all active products"""
        try:
            active_products = []
            
            for product_id, product in self.products.items():
                if product.get('active', True):
                    # Create a copy without sensitive information
                    public_product = {
                        'id': product['id'],
                        'name': product['name'],
                        'description': product['description'],
                        'price': product['price'],
                        'file_size': product['file_size'],
                        'version': product['version'],
                        'requirements': product['requirements'],
                        'features': product['features']
                    }
                    active_products.append(public_product)
            
            return active_products
            
        except Exception as e:
            self.logger.error(f"Failed to get products: {str(e)}")
            return []
    
    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific product by ID"""
        try:
            product = self.products.get(product_id)
            
            if product and product.get('active', True):
                return product.copy()
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get product {product_id}: {str(e)}")
            return None
    
    def validate_activation_key(self, activation_key: str) -> Optional[Dict[str, Any]]:
        """Validate activation key and return purchase info"""
        try:
            purchase = self.db.get_purchase_by_activation_key(activation_key)
            
            if not purchase:
                self.logger.warning(f"Invalid activation key: {activation_key[:8]}...")
                return None
            
            # Check if product exists
            product = self.get_product_by_id(purchase['product_id'])
            
            if not product:
                self.logger.error(f"Product not found for activation key: {purchase['product_id']}")
                return None
            
            # Check download limit
            download_limit = product.get('download_limit', 5)
            
            if download_limit > 0 and purchase['download_count'] >= download_limit:
                self.logger.warning(f"Download limit exceeded for activation key: {activation_key[:8]}...")
                return {
                    'valid': False,
                    'error': 'Download limit exceeded',
                    'download_count': purchase['download_count'],
                    'download_limit': download_limit
                }
            
            return {
                'valid': True,
                'purchase': purchase,
                'product': product,
                'download_count': purchase['download_count'],
                'download_limit': download_limit
            }
            
        except Exception as e:
            self.logger.error(f"Failed to validate activation key: {str(e)}")
            return None
    
    def get_download_info(self, activation_key: str) -> Optional[Dict[str, Any]]:
        """Get download information for an activation key"""
        try:
            validation_result = self.validate_activation_key(activation_key)
            
            if not validation_result or not validation_result.get('valid'):
                return validation_result
            
            purchase = validation_result['purchase']
            product = validation_result['product']
            
            file_path = os.path.join(self.download_dir, product['file_path'])
            
            # Check if file exists
            if not os.path.exists(file_path):
                self.logger.error(f"Product file not found: {file_path}")
                return {
                    'valid': False,
                    'error': 'Product file not available'
                }
            
            # Get file information
            file_stats = os.stat(file_path)
            file_hash = self._calculate_file_hash(file_path)
            
            return {
                'valid': True,
                'file_path': file_path,
                'file_name': product['file_path'],
                'file_size': file_stats.st_size,
                'file_hash': file_hash,
                'product': product,
                'purchase': purchase,
                'download_count': purchase['download_count'],
                'download_limit': product.get('download_limit', 5)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get download info: {str(e)}")
            return None
    
    def process_download(self, activation_key: str) -> Optional[Dict[str, Any]]:
        """Process a download request and update counters"""
        try:
            download_info = self.get_download_info(activation_key)
            
            if not download_info or not download_info.get('valid'):
                return download_info
            
            # Update download count
            success = self.db.update_download_count(activation_key)
            
            if not success:
                self.logger.error(f"Failed to update download count for: {activation_key[:8]}...")
                return {
                    'valid': False,
                    'error': 'Failed to update download count'
                }
            
            # Log the download
            self.logger.info(
                f"Download processed: {download_info['product']['name']} "
                f"for key {activation_key[:8]}... "
                f"(count: {download_info['download_count'] + 1})"
            )
            
            return download_info
            
        except Exception as e:
            self.logger.error(f"Failed to process download: {str(e)}")
            return None
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of a file"""
        try:
            hash_sha256 = hashlib.sha256()
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            
            return hash_sha256.hexdigest()
            
        except Exception as e:
            self.logger.error(f"Failed to calculate file hash: {str(e)}")
            return ""
    
    def create_secure_download_token(self, activation_key: str) -> Optional[str]:
        """Create a temporary secure download token"""
        try:
            import secrets
            import time
            
            # Create a secure token
            token = secrets.token_urlsafe(32)
            timestamp = int(time.time())
            
            # In a production environment, you would store this in a cache/database
            # with expiration time. For now, we'll encode it in the token itself
            token_data = f"{activation_key}:{timestamp}:{token}"
            
            # Base64 encode the token data
            import base64
            secure_token = base64.urlsafe_b64encode(token_data.encode()).decode()
            
            self.logger.info(f"Secure download token created for: {activation_key[:8]}...")
            return secure_token
            
        except Exception as e:
            self.logger.error(f"Failed to create secure download token: {str(e)}")
            return None
    
    def validate_download_token(self, token: str, max_age_hours: int = 24) -> Optional[str]:
        """Validate a secure download token and return activation key"""
        try:
            import base64
            import time
            
            # Decode the token
            token_data = base64.urlsafe_b64decode(token.encode()).decode()
            parts = token_data.split(':')
            
            if len(parts) != 3:
                self.logger.warning("Invalid token format")
                return None
            
            activation_key, timestamp_str, _ = parts
            timestamp = int(timestamp_str)
            
            # Check if token has expired
            current_time = int(time.time())
            max_age_seconds = max_age_hours * 3600
            
            if current_time - timestamp > max_age_seconds:
                self.logger.warning(f"Download token expired: {token[:16]}...")
                return None
            
            # Validate the activation key
            validation_result = self.validate_activation_key(activation_key)
            
            if validation_result and validation_result.get('valid'):
                return activation_key
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to validate download token: {str(e)}")
            return None
    
    def get_product_statistics(self) -> Dict[str, Any]:
        """Get product download and sales statistics"""
        try:
            stats = self.db.get_purchase_stats()
            
            # Add product-specific information
            product_details = {}
            
            for product_id, product in self.products.items():
                if product.get('active', True):
                    product_details[product_id] = {
                        'name': product['name'],
                        'price': product['price'],
                        'version': product['version'],
                        'sales_count': stats['products_sold'].get(product_id, 0)
                    }
            
            return {
                'total_products': len(self.products),
                'active_products': len([p for p in self.products.values() if p.get('active', True)]),
                'product_details': product_details,
                'sales_stats': stats
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get product statistics: {str(e)}")
            return {}
    
    def create_product_package(self, product_id: str, source_files: List[str], 
                             output_path: Optional[str] = None) -> Optional[str]:
        """Create a product package (ZIP file) from source files"""
        try:
            product = self.get_product_by_id(product_id)
            
            if not product:
                self.logger.error(f"Product not found: {product_id}")
                return None
            
            if not output_path:
                output_path = os.path.join(self.download_dir, product['file_path'])
            
            # Create the ZIP file
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in source_files:
                    if os.path.exists(file_path):
                        # Add file to ZIP with relative path
                        arcname = os.path.basename(file_path)
                        zipf.write(file_path, arcname)
                        self.logger.info(f"Added {file_path} to package")
                    else:
                        self.logger.warning(f"Source file not found: {file_path}")
                
                # Add a README file with product information
                readme_content = self._generate_readme_content(product)
                zipf.writestr('README.txt', readme_content)
            
            # Verify the created package
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                self.logger.info(f"Product package created: {output_path} ({file_size} bytes)")
                return output_path
            else:
                self.logger.error(f"Failed to create product package: {output_path}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to create product package: {str(e)}")
            return None
    
    def _generate_readme_content(self, product: Dict[str, Any]) -> str:
        """Generate README content for product package"""
        try:
            readme = f"""
{product['name']} - Version {product['version']}
{'=' * (len(product['name']) + len(product['version']) + 12)}

Thank you for purchasing {product['name']}!

Product Description:
{product['description']}

System Requirements:
{product['requirements']}

Features:
{chr(10).join('- ' + feature for feature in product['features'])}

Installation Instructions:
1. Extract all files to your desired installation directory
2. Run the installer or main executable
3. Follow the on-screen instructions
4. Use your activation key when prompted

Support:
If you need assistance, please contact our support team.

Thank you for choosing Gotcha Guardian!

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            return readme
            
        except Exception as e:
            self.logger.error(f"Failed to generate README content: {str(e)}")
            return "README file for your purchased product."
    
    def verify_product_integrity(self, product_id: str) -> Dict[str, Any]:
        """Verify the integrity of a product file"""
        try:
            product = self.get_product_by_id(product_id)
            
            if not product:
                return {
                    'valid': False,
                    'error': f'Product not found: {product_id}'
                }
            
            file_path = os.path.join(self.download_dir, product['file_path'])
            
            if not os.path.exists(file_path):
                return {
                    'valid': False,
                    'error': f'Product file not found: {file_path}'
                }
            
            # Check file size
            file_stats = os.stat(file_path)
            file_size = file_stats.st_size
            
            # Calculate hash
            file_hash = self._calculate_file_hash(file_path)
            
            # Check if it's a valid ZIP file
            is_valid_zip = False
            try:
                with zipfile.ZipFile(file_path, 'r') as zipf:
                    # Test the ZIP file
                    zipf.testzip()
                    is_valid_zip = True
                    file_count = len(zipf.namelist())
            except:
                file_count = 0
            
            return {
                'valid': is_valid_zip,
                'file_path': file_path,
                'file_size': file_size,
                'file_hash': file_hash,
                'is_valid_zip': is_valid_zip,
                'file_count': file_count if is_valid_zip else 0,
                'last_modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to verify product integrity: {str(e)}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def cleanup_expired_tokens(self, max_age_hours: int = 24) -> int:
        """Clean up expired download tokens (if stored in database)"""
        try:
            # This is a placeholder for token cleanup
            # In a production environment, you would implement this
            # to clean up expired tokens from your storage system
            
            self.logger.info("Token cleanup completed")
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired tokens: {str(e)}")
            return 0