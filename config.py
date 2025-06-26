#!/usr/bin/env python3
"""
Configuration management for Gotcha Guardian Payment Server
Handles environment variables, validation, and application settings
"""

import os
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlparse


def _parse_port(port_str: str) -> int:
    """Parse port with error handling"""
    try:
        return int(port_str)
    except (ValueError, TypeError):
        print(f"Warning: Invalid PORT value '{port_str}', using default 5000")
        return 5000


@dataclass
class Config:
    """Configuration class for payment server"""
    
    # Database Configuration
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///payments.db')
    
    # PayPal Configuration
    PAYPAL_CLIENT_ID: str = os.getenv('PAYPAL_CLIENT_ID', '')
    PAYPAL_CLIENT_SECRET: str = os.getenv('PAYPAL_CLIENT_SECRET', '')
    PAYPAL_MODE: str = os.getenv('PAYPAL_MODE', 'sandbox')  # 'sandbox' or 'live'
    
    # Email Configuration
    EMAIL_ADDRESS: str = os.getenv('EMAIL_ADDRESS', '')
    EMAIL_PASSWORD: str = os.getenv('EMAIL_PASSWORD', '')
    SMTP_SERVER: str = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT: int = int(os.getenv('SMTP_PORT', '587'))
    
    # Security Configuration
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Application Configuration
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')
    PORT: int = _parse_port(os.getenv('PORT', '5000'))
    HOST: str = os.getenv('HOST', '0.0.0.0')
    
    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED: bool = os.getenv('RATE_LIMIT_ENABLED', 'True').lower() in ('true', '1', 'yes')
    RATE_LIMIT_DEFAULT: str = os.getenv('RATE_LIMIT_DEFAULT', '100 per hour')
    RATE_LIMIT_PAYMENT: str = os.getenv('RATE_LIMIT_PAYMENT', '10 per hour')
    RATE_LIMIT_STORAGE_URI: str = os.getenv('RATE_LIMIT_STORAGE_URI', 'memory://')  # Use Redis in production: redis://localhost:6379/0
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH: int = int(os.getenv('MAX_CONTENT_LENGTH', '16777216'))  # 16MB
    UPLOAD_FOLDER: str = os.getenv('UPLOAD_FOLDER', 'uploads')
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', './logs/payment_server.log')
    LOG_MAX_BYTES: int = int(os.getenv('LOG_MAX_BYTES', '10485760'))  # 10MB
    LOG_BACKUP_COUNT: int = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # Product Configuration
    PRODUCTS_CONFIG_FILE: str = os.getenv('PRODUCTS_CONFIG_FILE', 'products.json')
    
    # Download Configuration
    DOWNLOAD_EXPIRY_HOURS: int = int(os.getenv('DOWNLOAD_EXPIRY_HOURS', '24'))
    MAX_DOWNLOAD_ATTEMPTS: int = int(os.getenv('MAX_DOWNLOAD_ATTEMPTS', '5'))
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Required PayPal configuration
        if not self.PAYPAL_CLIENT_ID:
            errors.append("PAYPAL_CLIENT_ID is required")
        
        if not self.PAYPAL_CLIENT_SECRET:
            errors.append("PAYPAL_CLIENT_SECRET is required")
        
        if self.PAYPAL_MODE not in ['sandbox', 'live']:
            errors.append("PAYPAL_MODE must be 'sandbox' or 'live'")
        
        # Required email configuration
        if not self.EMAIL_ADDRESS:
            errors.append("EMAIL_ADDRESS is required")
        
        if not self.EMAIL_PASSWORD:
            errors.append("EMAIL_PASSWORD is required")
        
        if not self.SMTP_SERVER:
            errors.append("SMTP_SERVER is required")
        
        # Validate email format
        if self.EMAIL_ADDRESS and '@' not in self.EMAIL_ADDRESS:
            errors.append("EMAIL_ADDRESS must be a valid email address")
        
        # Validate SMTP port
        if not (1 <= self.SMTP_PORT <= 65535):
            errors.append("SMTP_PORT must be between 1 and 65535")
        
        # Validate application port
        if not (1 <= self.PORT <= 65535):
            errors.append("PORT must be between 1 and 65535")
        
        # Security validation
        if self.SECRET_KEY == 'dev-secret-key-change-in-production' and not self.DEBUG:
            errors.append("SECRET_KEY must be changed in production")
        
        if len(self.SECRET_KEY) < 32:
            errors.append("SECRET_KEY should be at least 32 characters long")
        
        # Database URL validation
        if self.DATABASE_URL:
            try:
                parsed = urlparse(self.DATABASE_URL)
                if not parsed.scheme:
                    errors.append("DATABASE_URL must include a scheme (e.g., sqlite://, postgresql://)")
            except Exception:
                errors.append("DATABASE_URL format is invalid")
        
        # Log level validation
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.LOG_LEVEL.upper() not in valid_log_levels:
            errors.append(f"LOG_LEVEL must be one of: {', '.join(valid_log_levels)}")
        
        return errors
    
    def validate_production(self) -> List[str]:
        """Additional validation for production environment"""
        errors = self.validate()
        
        if self.DEBUG:
            errors.append("DEBUG should be False in production")
        
        if self.PAYPAL_MODE != 'live':
            errors.append("PAYPAL_MODE should be 'live' in production")
        
        if self.SECRET_KEY == 'dev-secret-key-change-in-production':
            errors.append("SECRET_KEY must be changed in production")
        
        return errors
    
    def get_database_config(self) -> dict:
        """Get database configuration dictionary"""
        if self.DATABASE_URL.startswith('sqlite'):
            return {
                'engine': 'sqlite',
                'database': self.DATABASE_URL.replace('sqlite:///', '').replace('sqlite://', '')
            }
        elif self.DATABASE_URL.startswith('postgresql'):
            parsed = urlparse(self.DATABASE_URL)
            return {
                'engine': 'postgresql',
                'host': parsed.hostname,
                'port': parsed.port or 5432,
                'database': parsed.path.lstrip('/'),
                'username': parsed.username,
                'password': parsed.password
            }
        else:
            return {'engine': 'sqlite', 'database': 'payments.db'}
    
    def get_smtp_config(self) -> dict:
        """Get SMTP configuration dictionary"""
        return {
            'server': self.SMTP_SERVER,
            'port': self.SMTP_PORT,
            'username': self.EMAIL_ADDRESS,
            'password': self.EMAIL_PASSWORD,
            'use_tls': True
        }
    
    def get_email_config(self) -> dict:
        """Get email configuration dictionary"""
        return {
            'smtp_server': self.SMTP_SERVER,
            'smtp_port': self.SMTP_PORT,
            'username': self.EMAIL_ADDRESS,
            'password': self.EMAIL_PASSWORD,
            'from_email': self.EMAIL_ADDRESS,
            'use_tls': True
        }
    
    def get_paypal_config(self) -> dict:
        """Get PayPal configuration dictionary"""
        return {
            'mode': self.PAYPAL_MODE,
            'client_id': self.PAYPAL_CLIENT_ID,
            'client_secret': self.PAYPAL_CLIENT_SECRET
        }
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.DEBUG or self.PAYPAL_MODE == 'sandbox'
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.DEBUG and self.PAYPAL_MODE == 'live'
    
    def get_log_config(self) -> dict:
        """Get logging configuration dictionary"""
        return {
            'level': self.LOG_LEVEL,
            'file': self.LOG_FILE,
            'max_bytes': self.LOG_MAX_BYTES,
            'backup_count': self.LOG_BACKUP_COUNT
        }
    
    def get_app_config(self) -> dict:
        """Get application configuration dictionary"""
        return {
            'debug': self.DEBUG,
            'port': self.PORT,
            'host': self.HOST,
            'secret_key': self.SECRET_KEY,
            'download_directory': 'downloads',
            'upload_folder': self.UPLOAD_FOLDER,
            'max_content_length': self.MAX_CONTENT_LENGTH,
            'base_url': f"http://{self.HOST}:{self.PORT}"
        }
    
    def __post_init__(self):
        """Post-initialization validation"""
        # Ensure upload folder exists
        if not os.path.exists(self.UPLOAD_FOLDER):
            os.makedirs(self.UPLOAD_FOLDER, exist_ok=True)
        
        # Ensure logs directory exists
        log_dir = os.path.dirname(self.LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)


def load_config() -> Config:
    """Load and validate configuration"""
    config = Config()
    
    # Validate configuration
    errors = config.validate()
    if errors:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"   - {error}")
        
        # In development, show warnings but continue
        if config.is_development():
            print("⚠️  Running in development mode with configuration warnings")
        else:
            print("❌ Cannot start in production with configuration errors")
            raise ValueError("Invalid configuration")
    
    return config


# Global configuration instance
config = load_config()
