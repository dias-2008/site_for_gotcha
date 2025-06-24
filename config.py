import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    # Database
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'sqlite:///app.db')
    
    # PayPal
    PAYPAL_CLIENT_ID: str = os.getenv('PAYPAL_CLIENT_ID', '')
    PAYPAL_CLIENT_SECRET: str = os.getenv('PAYPAL_CLIENT_SECRET', '')
    PAYPAL_MODE: str = os.getenv('PAYPAL_MODE', 'sandbox')
    
    # Email
    EMAIL_ADDRESS: str = os.getenv('EMAIL_ADDRESS', '')
    EMAIL_PASSWORD: str = os.getenv('EMAIL_PASSWORD', '')
    SMTP_SERVER: str = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT: int = int(os.getenv('SMTP_PORT', '587'))
    
    # Security
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    
    # Application
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    PORT: int = int(os.getenv('PORT', '5000'))
    
    def validate(self) -> list[str]:
        """Validate required configuration values."""
        errors = []
        
        if not self.PAYPAL_CLIENT_ID:
            errors.append('PAYPAL_CLIENT_ID is required')
        if not self.PAYPAL_CLIENT_SECRET:
            errors.append('PAYPAL_CLIENT_SECRET is required')
        if not self.EMAIL_ADDRESS:
            errors.append('EMAIL_ADDRESS is required for contact form')
            
        return errors
