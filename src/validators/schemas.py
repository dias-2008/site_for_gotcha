#!/usr/bin/env python3
"""
Validation Schemas for Gotcha Guardian Payment Server
Defines Marshmallow schemas for request validation
"""

from marshmallow import Schema, fields, validate, validates, ValidationError
import re
from typing import Dict, Any


class ContactFormSchema(Schema):
    """Schema for contact form validation"""
    
    name = fields.Str(
        required=True,
        validate=[
            validate.Length(min=2, max=100, error="Name must be between 2 and 100 characters"),
            validate.Regexp(
                r'^[a-zA-Z\s\-\.]+$',
                error="Name can only contain letters, spaces, hyphens, and periods"
            )
        ],
        error_messages={
            'required': 'Name is required',
            'null': 'Name cannot be null',
            'invalid': 'Invalid name format'
        }
    )
    
    email = fields.Email(
        required=True,
        validate=validate.Length(max=255, error="Email must be less than 255 characters"),
        error_messages={
            'required': 'Email is required',
            'null': 'Email cannot be null',
            'invalid': 'Invalid email format'
        }
    )
    
    message = fields.Str(
        required=True,
        validate=[
            validate.Length(min=10, max=2000, error="Message must be between 10 and 2000 characters")
        ],
        error_messages={
            'required': 'Message is required',
            'null': 'Message cannot be null',
            'invalid': 'Invalid message format'
        }
    )
    
    @validates('email')
    def validate_email_domain(self, value):
        """Additional email validation"""
        # Block common disposable email domains
        disposable_domains = [
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'throwaway.email'
        ]
        
        domain = value.split('@')[-1].lower()
        if domain in disposable_domains:
            raise ValidationError('Disposable email addresses are not allowed')
    
    @validates('message')
    def validate_message_content(self, value):
        """Validate message content for spam patterns"""
        # Check for excessive URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, value)
        
        if len(urls) > 3:
            raise ValidationError('Message contains too many URLs')
        
        # Check for spam keywords
        spam_keywords = ['viagra', 'casino', 'lottery', 'winner', 'congratulations']
        message_lower = value.lower()
        
        for keyword in spam_keywords:
            if keyword in message_lower:
                raise ValidationError('Message contains prohibited content')


class PaymentCreateSchema(Schema):
    """Schema for payment creation validation"""
    
    email = fields.Email(
        required=True,
        validate=validate.Length(max=255, error="Email must be less than 255 characters"),
        error_messages={
            'required': 'Email is required',
            'invalid': 'Invalid email format'
        }
    )
    
    product_id = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=50, error="Product ID must be between 3 and 50 characters"),
            validate.Regexp(
                r'^[a-zA-Z0-9_]+$',
                error="Product ID can only contain letters, numbers, and underscores"
            )
        ],
        error_messages={
            'required': 'Product ID is required',
            'invalid': 'Invalid product ID format'
        }
    )
    
    return_url = fields.Url(
        required=True,
        error_messages={
            'required': 'Return URL is required',
            'invalid': 'Invalid return URL format'
        }
    )
    
    cancel_url = fields.Url(
        required=True,
        error_messages={
            'required': 'Cancel URL is required',
            'invalid': 'Invalid cancel URL format'
        }
    )
    
    @validates('product_id')
    def validate_product_exists(self, value):
        """Validate that the product exists"""
        # This would typically check against a database or product list
        valid_products = [
            'gotcha_guardian_basic',
            'gotcha_guardian_pro', 
            'gotcha_guardian_enterprise'
        ]
        
        if value not in valid_products:
            raise ValidationError(f'Invalid product ID: {value}')


class PaymentExecuteSchema(Schema):
    """Schema for payment execution validation"""
    
    payment_id = fields.Str(
        required=True,
        validate=[
            validate.Length(min=10, max=100, error="Payment ID must be between 10 and 100 characters"),
            validate.Regexp(
                r'^[A-Z0-9]+$',
                error="Payment ID can only contain uppercase letters and numbers"
            )
        ],
        error_messages={
            'required': 'Payment ID is required',
            'invalid': 'Invalid payment ID format'
        }
    )
    
    payer_id = fields.Str(
        required=True,
        validate=[
            validate.Length(min=10, max=100, error="Payer ID must be between 10 and 100 characters"),
            validate.Regexp(
                r'^[A-Z0-9]+$',
                error="Payer ID can only contain uppercase letters and numbers"
            )
        ],
        error_messages={
            'required': 'Payer ID is required',
            'invalid': 'Invalid payer ID format'
        }
    )


class DownloadRequestSchema(Schema):
    """Schema for download request validation"""
    
    activation_key = fields.Str(
        required=True,
        validate=[
            validate.Length(min=20, max=100, error="Activation key must be between 20 and 100 characters"),
            validate.Regexp(
                r'^[A-Z0-9\-]+$',
                error="Activation key can only contain uppercase letters, numbers, and hyphens"
            )
        ],
        error_messages={
            'required': 'Activation key is required',
            'invalid': 'Invalid activation key format'
        }
    )
    
    @validates('activation_key')
    def validate_activation_key_format(self, value):
        """Validate activation key format"""
        # Expected format: PRODUCT-YYYYMMDD-XXXXXXXXXXXX
        parts = value.split('-')
        
        if len(parts) < 3:
            raise ValidationError('Invalid activation key format')
        
        # Validate date part (if present)
        if len(parts) >= 2 and len(parts[1]) == 8:
            try:
                from datetime import datetime
                datetime.strptime(parts[1], '%Y%m%d')
            except ValueError:
                raise ValidationError('Invalid date in activation key')


class AdminStatsSchema(Schema):
    """Schema for admin statistics request validation"""
    
    start_date = fields.DateTime(
        required=False,
        format='%Y-%m-%d',
        error_messages={
            'invalid': 'Invalid start date format. Use YYYY-MM-DD'
        }
    )
    
    end_date = fields.DateTime(
        required=False,
        format='%Y-%m-%d',
        error_messages={
            'invalid': 'Invalid end date format. Use YYYY-MM-DD'
        }
    )
    
    product_id = fields.Str(
        required=False,
        validate=[
            validate.Length(max=50, error="Product ID must be less than 50 characters"),
            validate.Regexp(
                r'^[a-zA-Z0-9_]+$',
                error="Product ID can only contain letters, numbers, and underscores"
            )
        ],
        error_messages={
            'invalid': 'Invalid product ID format'
        }
    )
    
    limit = fields.Int(
        required=False,
        validate=validate.Range(min=1, max=1000, error="Limit must be between 1 and 1000"),
        missing=100,
        error_messages={
            'invalid': 'Limit must be a valid integer'
        }
    )
    
    offset = fields.Int(
        required=False,
        validate=validate.Range(min=0, error="Offset must be 0 or greater"),
        missing=0,
        error_messages={
            'invalid': 'Offset must be a valid integer'
        }
    )
    
    @validates('end_date')
    def validate_date_range(self, value):
        """Validate that end_date is after start_date"""
        start_date = self.context.get('start_date')
        
        if start_date and value and value < start_date:
            raise ValidationError('End date must be after start date')


class WebhookSchema(Schema):
    """Schema for webhook validation"""
    
    id = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=100, error="Webhook ID is required"),
        error_messages={
            'required': 'Webhook ID is required'
        }
    )
    
    event_type = fields.Str(
        required=True,
        validate=validate.OneOf([
            'PAYMENT.SALE.COMPLETED',
            'PAYMENT.SALE.DENIED',
            'PAYMENT.SALE.REFUNDED',
            'PAYMENT.SALE.REVERSED'
        ], error="Invalid event type"),
        error_messages={
            'required': 'Event type is required'
        }
    )
    
    resource = fields.Dict(
        required=True,
        error_messages={
            'required': 'Resource data is required'
        }
    )
    
    create_time = fields.DateTime(
        required=False,
        format='%Y-%m-%dT%H:%M:%SZ'
    )


class RefundRequestSchema(Schema):
    """Schema for refund request validation"""
    
    payment_id = fields.Str(
        required=True,
        validate=[
            validate.Length(min=10, max=100, error="Payment ID must be between 10 and 100 characters")
        ],
        error_messages={
            'required': 'Payment ID is required'
        }
    )
    
    amount = fields.Decimal(
        required=False,
        validate=validate.Range(min=0.01, max=10000, error="Amount must be between 0.01 and 10000"),
        places=2,
        error_messages={
            'invalid': 'Invalid amount format'
        }
    )
    
    reason = fields.Str(
        required=False,
        validate=validate.Length(max=500, error="Reason must be less than 500 characters"),
        missing="Requested by customer"
    )


class ActivationKeyGenerateSchema(Schema):
    """Schema for activation key generation validation"""
    
    product_id = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=50, error="Product ID must be between 3 and 50 characters"),
            validate.Regexp(
                r'^[a-zA-Z0-9_]+$',
                error="Product ID can only contain letters, numbers, and underscores"
            )
        ],
        error_messages={
            'required': 'Product ID is required'
        }
    )
    
    count = fields.Int(
        required=False,
        validate=validate.Range(min=1, max=100, error="Count must be between 1 and 100"),
        missing=1,
        error_messages={
            'invalid': 'Count must be a valid integer'
        }
    )


class ProductCreateSchema(Schema):
    """Schema for product creation validation"""
    
    id = fields.Str(
        required=True,
        validate=[
            validate.Length(min=3, max=50, error="Product ID must be between 3 and 50 characters"),
            validate.Regexp(
                r'^[a-zA-Z0-9_]+$',
                error="Product ID can only contain letters, numbers, and underscores"
            )
        ],
        error_messages={
            'required': 'Product ID is required'
        }
    )
    
    name = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=100, error="Product name must be between 3 and 100 characters"),
        error_messages={
            'required': 'Product name is required'
        }
    )
    
    description = fields.Str(
        required=True,
        validate=validate.Length(min=10, max=1000, error="Description must be between 10 and 1000 characters"),
        error_messages={
            'required': 'Product description is required'
        }
    )
    
    price = fields.Decimal(
        required=True,
        validate=validate.Range(min=0.01, max=10000, error="Price must be between 0.01 and 10000"),
        places=2,
        error_messages={
            'required': 'Product price is required',
            'invalid': 'Invalid price format'
        }
    )
    
    file_path = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=255, error="File path must be between 1 and 255 characters"),
            validate.Regexp(
                r'^[a-zA-Z0-9_\-\.]+\.(zip|exe|msi)$',
                error="File must be a ZIP, EXE, or MSI file"
            )
        ],
        error_messages={
            'required': 'File path is required'
        }
    )
    
    version = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=20, error="Version must be between 1 and 20 characters"),
            validate.Regexp(
                r'^\d+\.\d+\.\d+$',
                error="Version must be in format X.Y.Z"
            )
        ],
        error_messages={
            'required': 'Product version is required'
        }
    )
    
    requirements = fields.Str(
        required=False,
        validate=validate.Length(max=500, error="Requirements must be less than 500 characters")
    )
    
    features = fields.List(
        fields.Str(validate=validate.Length(max=100)),
        required=False,
        validate=validate.Length(max=20, error="Maximum 20 features allowed")
    )
    
    download_limit = fields.Int(
        required=False,
        validate=validate.Range(min=-1, max=1000, error="Download limit must be between -1 and 1000"),
        missing=5
    )
    
    active = fields.Bool(
        required=False,
        missing=True
    )


def validate_schema(schema_class: Schema, data: Dict[str, Any]) -> Dict[str, Any]:
    """Utility function to validate data against a schema"""
    try:
        schema = schema_class()
        result = schema.load(data)
        return {'valid': True, 'data': result, 'errors': None}
    except ValidationError as e:
        return {'valid': False, 'data': None, 'errors': e.messages}
    except Exception as e:
        return {'valid': False, 'data': None, 'errors': {'general': [str(e)]}}