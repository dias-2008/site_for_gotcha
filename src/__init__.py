#!/usr/bin/env python3
"""
Gotcha Guardian Payment Server - Source Package
Modular components for payment processing, user management, and product delivery
"""

__version__ = "2.0.0"
__author__ = "Gotcha Guardian Team"
__email__ = "support@gotchaguardian.com"

# Package imports
from .models.database import DatabaseManager
from .services.email_service import EmailService
from .services.payment_service import PaymentService
from .services.product_service import ProductService
from .utils.validators import validate_email, validate_activation_key
from .utils.security import generate_activation_key, create_secure_filename
from .utils.logging_config import setup_logging

__all__ = [
    'DatabaseManager',
    'EmailService',
    'PaymentService',
    'ProductService',
    'validate_email',
    'validate_activation_key',
    'generate_activation_key',
    'create_secure_filename',
    'setup_logging'
]