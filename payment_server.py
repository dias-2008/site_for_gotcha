#!/usr/bin/env python3
"""
Enhanced Payment Server for Gotcha Guardian
Handles real PayPal payments, user registration, and activation key delivery
with improved error handling, logging, validation, and security
"""

import os
import json
import sqlite3
import secrets
import smtplib
import logging
import tempfile
import zipfile
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from logging.handlers import RotatingFileHandler
from typing import Dict, List, Optional, Tuple

from flask import Flask, request, jsonify, render_template_string, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from marshmallow import Schema, fields, ValidationError
import paypalrestsdk

from config import config
from src.models.database import DatabaseManager
from src.services.email_service import EmailService
from src.services.payment_service import PaymentService
from src.services.product_service import ProductService
from src.utils.validators import validate_email, validate_activation_key
from src.utils.security import generate_activation_key, create_secure_filename
from src.utils.logging_config import setup_logging

# Load environment variables from .env file for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available in production, which is fine
    pass

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

# Setup CORS
CORS(app, origins=['*'], methods=['GET', 'POST', 'OPTIONS'])

# Setup rate limiting
if config.RATE_LIMIT_ENABLED:
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=[config.RATE_LIMIT_DEFAULT]
    )
else:
    limiter = None

# Setup logging
logger = setup_logging(config)

# Initialize services
db_manager = DatabaseManager(config)
email_service = EmailService(config)
payment_service = PaymentService(config)
product_service = ProductService(config)

# Request validation schemas
class ContactSchema(Schema):
    name = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    email = fields.Email(required=True)
    message = fields.Str(required=True, validate=lambda x: len(x.strip()) > 10)

class PaymentCreateSchema(Schema):
    email = fields.Email(required=True)
    product_id = fields.Str(required=True, validate=lambda x: x in product_service.get_available_products())

class PaymentExecuteSchema(Schema):
    paymentID = fields.Str(required=True)
    payerID = fields.Str(required=True)

# Error handlers
@app.errorhandler(ValidationError)
def handle_validation_error(e):
    """Handle marshmallow validation errors"""
    logger.warning(f"Validation error: {e.messages}")
    return jsonify({
        'success': False,
        'error': 'Invalid input data',
        'details': e.messages
    }), 400

@app.errorhandler(429)
def handle_rate_limit_error(e):
    """Handle rate limit errors"""
    logger.warning(f"Rate limit exceeded: {get_remote_address()}")
    return jsonify({
        'success': False,
        'error': 'Rate limit exceeded. Please try again later.'
    }), 429

@app.errorhandler(500)
def handle_internal_error(e):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({
        'success': False,
        'error': 'Internal server error. Please try again later.'
    }), 500

# Utility functions
def log_request_info():
    """Log request information for debugging"""
    if config.DEBUG:
        logger.debug(f"Request: {request.method} {request.path} from {get_remote_address()}")
        if request.json:
            # Don't log sensitive data
            safe_data = {k: v for k, v in request.json.items() if k not in ['password', 'secret', 'key']}
            logger.debug(f"Request data: {safe_data}")

def create_success_response(data: dict, message: str = "Success") -> dict:
    """Create standardized success response"""
    return {
        'success': True,
        'message': message,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }

def create_error_response(error: str, details: dict = None) -> dict:
    """Create standardized error response"""
    response = {
        'success': False,
        'error': error,
        'timestamp': datetime.now().isoformat()
    }
    if details:
        response['details'] = details
    return response

# Routes
@app.route('/')
def index():
    """Main page with payment interface"""
    try:
        log_request_info()
        with open('site.html', 'r', encoding='utf-8') as f:
            return render_template_string(f.read())
    except FileNotFoundError:
        logger.error("site.html not found")
        return "Payment interface temporarily unavailable", 503
    except Exception as e:
        logger.error(f"Error loading main page: {str(e)}")
        return "Service temporarily unavailable", 503

@app.route('/api/health')
def health_check():
    """Enhanced health check endpoint"""
    try:
        log_request_info()
        
        # Check database connection
        db_status = db_manager.check_connection()
        
        # Check email service
        email_status = email_service.check_connection()
        
        # Check PayPal service
        paypal_status = payment_service.check_connection()
        
        # Determine overall health
        is_healthy = db_status and email_status and paypal_status
        
        health_data = {
            'status': 'healthy' if is_healthy else 'degraded',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'database': 'connected' if db_status else 'disconnected',
                'email': 'connected' if email_status else 'disconnected',
                'paypal': 'connected' if paypal_status else 'disconnected'
            },
            'environment': {
                'mode': config.PAYPAL_MODE,
                'debug': config.DEBUG,
                'version': '2.0.0'
            },
            'products': list(product_service.get_available_products().keys())
        }
        
        status_code = 200 if is_healthy else 503
        return jsonify(health_data), status_code
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/contact', methods=['POST'])
@limiter.limit("5 per minute") if limiter else lambda f: f
def handle_contact():
    """Handle contact form submissions with validation"""
    try:
        log_request_info()
        
        # Validate input
        schema = ContactSchema()
        data = schema.load(request.get_json() or {})
        
        # Send contact email
        success = email_service.send_contact_email(
            name=data['name'],
            email=data['email'],
            message=data['message']
        )
        
        if success:
            logger.info(f"Contact form submitted by {data['email']}")
            return jsonify(create_success_response(
                {},
                "Message sent successfully. We'll get back to you soon!"
            ))
        else:
            logger.error(f"Failed to send contact email from {data['email']}")
            return jsonify(create_error_response(
                "Failed to send message. Please try again later."
            )), 500
            
    except ValidationError as e:
        raise e  # Let the error handler deal with it
    except Exception as e:
        logger.error(f"Contact form error: {str(e)}")
        return jsonify(create_error_response(
            "Server error. Please try again later."
        )), 500

@app.route('/api/create-payment', methods=['POST'])
@limiter.limit(config.RATE_LIMIT_PAYMENT) if limiter else lambda f: f
def create_payment():
    """Create PayPal payment with enhanced validation"""
    try:
        log_request_info()
        
        # Validate input
        schema = PaymentCreateSchema()
        data = schema.load(request.get_json() or {})
        
        email = data['email']
        product_id = data['product_id']
        
        # Create payment
        payment_result = payment_service.create_payment(
            email=email,
            product_id=product_id,
            return_url=f"{request.url_root}api/payment-success",
            cancel_url=f"{request.url_root}api/payment-cancel"
        )
        
        if payment_result['success']:
            logger.info(f"Payment created for {email}, product: {product_id}")
            return jsonify(create_success_response({
                'approval_url': payment_result['approval_url'],
                'payment_id': payment_result['payment_id']
            }))
        else:
            logger.error(f"Payment creation failed: {payment_result['error']}")
            return jsonify(create_error_response(
                payment_result['error']
            )), 500
            
    except ValidationError as e:
        raise e
    except Exception as e:
        logger.error(f"Payment creation error: {str(e)}")
        return jsonify(create_error_response(
            "Payment creation failed. Please try again."
        )), 500

@app.route('/api/execute-payment', methods=['POST'])
@limiter.limit(config.RATE_LIMIT_PAYMENT) if limiter else lambda f: f
def execute_payment():
    """Execute PayPal payment after approval"""
    try:
        log_request_info()
        
        # Validate input
        schema = PaymentExecuteSchema()
        data = schema.load(request.get_json() or {})
        
        payment_id = data['paymentID']
        payer_id = data['payerID']
        
        # Execute payment
        execution_result = payment_service.execute_payment(payment_id, payer_id)
        
        if execution_result['success']:
            # Generate activation key and create download link
            activation_key = execution_result['activation_key']
            download_link = f"{request.url_root}api/download/{activation_key}"
            
            # Send activation email
            email_sent = email_service.send_activation_email(
                email=execution_result['email'],
                product_id=execution_result['product_id'],
                activation_key=activation_key,
                download_link=download_link
            )
            
            if email_sent:
                logger.info(f"Payment executed successfully for {execution_result['email']}")
                return jsonify(create_success_response({
                    'activation_key': activation_key,
                    'download_link': download_link,
                    'email_sent': True
                }, "Payment successful! Check your email for the activation key."))
            else:
                logger.warning(f"Payment successful but email failed for {execution_result['email']}")
                return jsonify(create_success_response({
                    'activation_key': activation_key,
                    'download_link': download_link,
                    'email_sent': False
                }, "Payment successful! Email delivery failed, but you can download using the link below."))
        else:
            logger.error(f"Payment execution failed: {execution_result['error']}")
            return jsonify(create_error_response(
                execution_result['error']
            )), 500
            
    except ValidationError as e:
        raise e
    except Exception as e:
        logger.error(f"Payment execution error: {str(e)}")
        return jsonify(create_error_response(
            "Payment execution failed. Please contact support."
        )), 500

@app.route('/api/download/<activation_key>')
@limiter.limit("10 per hour") if limiter else lambda f: f
def download_product(activation_key):
    """Download product files using activation key"""
    try:
        log_request_info()
        
        # Validate activation key format
        if not validate_activation_key(activation_key):
            logger.warning(f"Invalid activation key format: {activation_key}")
            return "Invalid activation key format", 400
        
        # Get purchase info
        purchase_info = db_manager.get_purchase_by_activation_key(activation_key)
        
        if not purchase_info:
            logger.warning(f"Invalid activation key: {activation_key}")
            return "Invalid activation key", 404
        
        # Check download limits
        if purchase_info['download_count'] >= config.MAX_DOWNLOAD_ATTEMPTS:
            logger.warning(f"Download limit exceeded for key: {activation_key}")
            return "Download limit exceeded", 403
        
        # Create product ZIP
        zip_path = product_service.create_product_zip(
            product_id=purchase_info['product_id'],
            activation_key=activation_key
        )
        
        if not zip_path:
            logger.error(f"Failed to create product ZIP for {purchase_info['product_id']}")
            return "Product files not available", 404
        
        # Update download count
        db_manager.update_download_count(activation_key)
        
        logger.info(f"Product downloaded: {purchase_info['product_id']} with key: {activation_key}")
        
        # Create secure filename
        filename = create_secure_filename(
            f"gotcha_{purchase_info['product_id']}_{activation_key[:8]}.zip"
        )
        
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/zip'
        )
        
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return "Download error. Please contact support.", 500

@app.route('/api/purchases')
@limiter.limit("30 per hour") if limiter else lambda f: f
def list_purchases():
    """List all purchases (admin endpoint)"""
    try:
        log_request_info()
        
        # TODO: Add admin authentication
        purchases = db_manager.get_all_purchases()
        
        # Remove sensitive information
        safe_purchases = []
        for purchase in purchases:
            safe_purchase = {
                'id': purchase['id'],
                'email': purchase['email'][:3] + '***' + purchase['email'][-10:],  # Mask email
                'product_id': purchase['product_id'],
                'amount': purchase['amount'],
                'purchase_date': purchase['purchase_date'],
                'status': purchase['status'],
                'download_count': purchase['download_count']
            }
            safe_purchases.append(safe_purchase)
        
        return jsonify(create_success_response({
            'purchases': safe_purchases,
            'total': len(safe_purchases)
        }))
        
    except Exception as e:
        logger.error(f"Error listing purchases: {str(e)}")
        return jsonify(create_error_response(
            "Failed to retrieve purchases"
        )), 500

@app.route('/api/stats')
@limiter.limit("10 per hour") if limiter else lambda f: f
def get_stats():
    """Get basic statistics (admin endpoint)"""
    try:
        log_request_info()
        
        # TODO: Add admin authentication
        stats = db_manager.get_purchase_stats()
        
        return jsonify(create_success_response({
            'total_purchases': stats['total_purchases'],
            'total_revenue': stats['total_revenue'],
            'products_sold': stats['products_sold'],
            'recent_purchases': stats['recent_purchases']
        }))
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify(create_error_response(
            "Failed to retrieve statistics"
        )), 500

# Initialize application
def initialize_app():
    """Initialize the application"""
    try:
        # Validate configuration
        errors = config.validate()
        if errors:
            logger.error("Configuration errors:")
            for error in errors:
                logger.error(f"  - {error}")
            
            if config.is_production():
                raise ValueError("Invalid configuration for production")
            else:
                logger.warning("Running with configuration warnings in development mode")
        
        # Initialize database
        db_manager.initialize_database()
        logger.info("✅ Database initialized")
        
        # Initialize services
        email_service.initialize()
        payment_service.initialize()
        product_service.initialize()
        logger.info("✅ Services initialized")
        
        # Log configuration
        logger.info(f"✅ Payment server initialized")
        logger.info(f"✅ Environment: {'Production' if config.is_production() else 'Development'}")
        logger.info(f"✅ PayPal mode: {config.PAYPAL_MODE}")
        logger.info(f"✅ Available products: {list(product_service.get_available_products().keys())}")
        logger.info(f"✅ Rate limiting: {'Enabled' if config.RATE_LIMIT_ENABLED else 'Disabled'}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Application initialization failed: {str(e)}")
        return False

# Initialize for both direct run and gunicorn
if not initialize_app():
    logger.error("❌ Application initialization failed")
    if __name__ == '__main__':
        exit(1)

if __name__ == '__main__':
    logger.info("🚀 Starting payment server in development mode...")
    app.run(
        debug=config.DEBUG,
        host=config.HOST,
        port=config.PORT,
        threaded=True
    )