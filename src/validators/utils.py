#!/usr/bin/env python3
"""
Validation Utilities for Gotcha Guardian Payment Server
Provides utility functions for input validation and sanitization
"""

import re
import html
import bleach
from typing import Optional, Union, List, Dict, Any
from decimal import Decimal, InvalidOperation
from datetime import datetime
import hashlib
import secrets
import string


def validate_email(email: str) -> bool:
    """Validate email address format"""
    if not email or not isinstance(email, str):
        return False
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False
    
    # Additional checks
    if len(email) > 255:
        return False
    
    # Check for consecutive dots
    if '..' in email:
        return False
    
    # Check for valid domain
    domain = email.split('@')[-1]
    if domain.startswith('.') or domain.endswith('.'):
        return False
    
    return True


def validate_activation_key(key: str) -> Dict[str, Any]:
    """Validate activation key format and extract information"""
    if not key or not isinstance(key, str):
        return {'valid': False, 'error': 'Invalid key format'}
    
    # Expected format: PRODUCT-YYYYMMDD-XXXXXXXXXXXX
    parts = key.split('-')
    
    if len(parts) < 3:
        return {'valid': False, 'error': 'Invalid key structure'}
    
    product_part = parts[0]
    date_part = parts[1] if len(parts) > 1 else ''
    unique_part = '-'.join(parts[2:]) if len(parts) > 2 else ''
    
    # Validate product part
    if not re.match(r'^[A-Z0-9_]+$', product_part):
        return {'valid': False, 'error': 'Invalid product identifier'}
    
    # Validate date part
    if len(date_part) == 8 and date_part.isdigit():
        try:
            creation_date = datetime.strptime(date_part, '%Y%m%d')
        except ValueError:
            return {'valid': False, 'error': 'Invalid date in key'}
    else:
        creation_date = None
    
    # Validate unique part
    if not re.match(r'^[A-Z0-9\-]+$', unique_part):
        return {'valid': False, 'error': 'Invalid unique identifier'}
    
    return {
        'valid': True,
        'product': product_part,
        'date': creation_date,
        'unique_id': unique_part,
        'full_key': key
    }


def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """Sanitize user input to prevent XSS and other attacks"""
    if not text or not isinstance(text, str):
        return ''
    
    # Remove HTML tags and escape special characters
    cleaned = bleach.clean(text, tags=[], attributes={}, strip=True)
    
    # HTML escape
    cleaned = html.escape(cleaned)
    
    # Remove control characters except newlines and tabs
    cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', cleaned)
    
    # Normalize whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Truncate if max_length specified
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length].strip()
    
    return cleaned


def validate_amount(amount: Union[str, float, Decimal]) -> Dict[str, Any]:
    """Validate monetary amount"""
    try:
        if isinstance(amount, str):
            # Remove currency symbols and whitespace
            amount = re.sub(r'[^\d.,\-]', '', amount)
            # Handle comma as decimal separator
            amount = amount.replace(',', '.')
        
        decimal_amount = Decimal(str(amount))
        
        # Check for reasonable range
        if decimal_amount < Decimal('0.01'):
            return {'valid': False, 'error': 'Amount too small (minimum $0.01)'}
        
        if decimal_amount > Decimal('10000.00'):
            return {'valid': False, 'error': 'Amount too large (maximum $10,000)'}
        
        # Check decimal places
        if decimal_amount.as_tuple().exponent < -2:
            return {'valid': False, 'error': 'Too many decimal places (maximum 2)'}
        
        return {
            'valid': True,
            'amount': decimal_amount,
            'formatted': f"${decimal_amount:.2f}"
        }
    
    except (InvalidOperation, ValueError, TypeError):
        return {'valid': False, 'error': 'Invalid amount format'}


def validate_product_id(product_id: str) -> bool:
    """Validate product ID format"""
    if not product_id or not isinstance(product_id, str):
        return False
    
    # Must be alphanumeric with underscores, 3-50 characters
    pattern = r'^[a-zA-Z0-9_]{3,50}$'
    return bool(re.match(pattern, product_id))


def validate_file_path(file_path: str, allowed_extensions: Optional[List[str]] = None) -> Dict[str, Any]:
    """Validate file path and extension"""
    if not file_path or not isinstance(file_path, str):
        return {'valid': False, 'error': 'Invalid file path'}
    
    # Remove any directory traversal attempts
    if '..' in file_path or file_path.startswith('/'):
        return {'valid': False, 'error': 'Invalid file path format'}
    
    # Check file extension
    if '.' not in file_path:
        return {'valid': False, 'error': 'File must have an extension'}
    
    extension = file_path.split('.')[-1].lower()
    
    if allowed_extensions and extension not in allowed_extensions:
        return {
            'valid': False, 
            'error': f'Invalid file extension. Allowed: {", ".join(allowed_extensions)}'
        }
    
    # Check for valid filename characters
    filename = file_path.split('/')[-1]
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', filename):
        return {'valid': False, 'error': 'Invalid filename characters'}
    
    return {
        'valid': True,
        'filename': filename,
        'extension': extension,
        'path': file_path
    }


def validate_version(version: str) -> Dict[str, Any]:
    """Validate version string (semantic versioning)"""
    if not version or not isinstance(version, str):
        return {'valid': False, 'error': 'Invalid version format'}
    
    # Semantic versioning pattern: X.Y.Z
    pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9\-]+))?$'
    match = re.match(pattern, version)
    
    if not match:
        return {'valid': False, 'error': 'Version must be in format X.Y.Z'}
    
    major, minor, patch, prerelease = match.groups()
    
    return {
        'valid': True,
        'major': int(major),
        'minor': int(minor),
        'patch': int(patch),
        'prerelease': prerelease,
        'version': version
    }


def validate_url(url: str, allowed_schemes: Optional[List[str]] = None) -> Dict[str, Any]:
    """Validate URL format"""
    if not url or not isinstance(url, str):
        return {'valid': False, 'error': 'Invalid URL'}
    
    # Basic URL pattern
    pattern = r'^(https?)://[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})?(?::\d+)?(?:/[^\s]*)?$'
    
    if not re.match(pattern, url):
        return {'valid': False, 'error': 'Invalid URL format'}
    
    # Check scheme
    scheme = url.split('://')[0].lower()
    if allowed_schemes and scheme not in allowed_schemes:
        return {
            'valid': False, 
            'error': f'Invalid URL scheme. Allowed: {", ".join(allowed_schemes)}'
        }
    
    # Check length
    if len(url) > 2048:
        return {'valid': False, 'error': 'URL too long (maximum 2048 characters)'}
    
    return {
        'valid': True,
        'url': url,
        'scheme': scheme
    }


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_activation_key(product_id: str, date: Optional[datetime] = None) -> str:
    """Generate a new activation key"""
    if not date:
        date = datetime.now()
    
    # Format: PRODUCT-YYYYMMDD-XXXXXXXXXXXX
    date_str = date.strftime('%Y%m%d')
    unique_part = generate_secure_token(12).upper()
    
    return f"{product_id.upper()}-{date_str}-{unique_part}"


def calculate_file_hash(file_path: str, algorithm: str = 'sha256') -> Optional[str]:
    """Calculate hash of a file"""
    try:
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    except (FileNotFoundError, PermissionError, ValueError):
        return None


def validate_phone_number(phone: str) -> Dict[str, Any]:
    """Validate phone number format"""
    if not phone or not isinstance(phone, str):
        return {'valid': False, 'error': 'Invalid phone number'}
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check length (7-15 digits for international numbers)
    if len(digits_only) < 7 or len(digits_only) > 15:
        return {'valid': False, 'error': 'Phone number must be 7-15 digits'}
    
    # Format as international number
    if len(digits_only) == 10:  # US number
        formatted = f"+1-{digits_only[:3]}-{digits_only[3:6]}-{digits_only[6:]}"
    elif len(digits_only) == 11 and digits_only.startswith('1'):  # US with country code
        formatted = f"+{digits_only[0]}-{digits_only[1:4]}-{digits_only[4:7]}-{digits_only[7:]}"
    else:
        formatted = f"+{digits_only}"
    
    return {
        'valid': True,
        'digits': digits_only,
        'formatted': formatted
    }


def validate_date_range(start_date: str, end_date: str) -> Dict[str, Any]:
    """Validate date range"""
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        if start > end:
            return {'valid': False, 'error': 'Start date must be before end date'}
        
        # Check if range is reasonable (not more than 1 year)
        if (end - start).days > 365:
            return {'valid': False, 'error': 'Date range too large (maximum 1 year)'}
        
        return {
            'valid': True,
            'start_date': start,
            'end_date': end,
            'days': (end - start).days
        }
    
    except ValueError:
        return {'valid': False, 'error': 'Invalid date format (use YYYY-MM-DD)'}


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    if not filename:
        return 'unnamed_file'
    
    # Remove path separators and dangerous characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove control characters
    filename = re.sub(r'[\x00-\x1f\x7f]', '', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_length = 250 - len(ext)
        filename = name[:max_name_length] + ('.' + ext if ext else '')
    
    # Ensure it's not empty
    if not filename.strip():
        filename = 'unnamed_file'
    
    return filename


def validate_json_structure(data: Any, required_fields: List[str]) -> Dict[str, Any]:
    """Validate JSON data structure"""
    if not isinstance(data, dict):
        return {'valid': False, 'error': 'Data must be a JSON object'}
    
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    
    if missing_fields:
        return {
            'valid': False, 
            'error': f'Missing required fields: {", ".join(missing_fields)}'
        }
    
    return {'valid': True, 'data': data}


def rate_limit_key(request_info: Dict[str, str]) -> str:
    """Generate rate limiting key from request information"""
    ip = request_info.get('ip', 'unknown')
    user_agent = request_info.get('user_agent', 'unknown')
    endpoint = request_info.get('endpoint', 'unknown')
    
    # Create a hash of the combination
    key_string = f"{ip}:{user_agent}:{endpoint}"
    return hashlib.sha256(key_string.encode()).hexdigest()[:16]


def mask_sensitive_data(data: str, mask_char: str = '*', visible_chars: int = 4) -> str:
    """Mask sensitive data for logging"""
    if not data or len(data) <= visible_chars:
        return mask_char * len(data) if data else ''
    
    return data[:visible_chars] + mask_char * (len(data) - visible_chars)