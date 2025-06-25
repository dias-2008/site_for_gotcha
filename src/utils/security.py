#!/usr/bin/env python3
"""
Security utilities for Gotcha Guardian Payment Server
Provides encryption, hashing, and security management functions
"""

import os
import secrets
import hashlib
import hmac
import base64
import json
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps
from flask import request, jsonify, current_app
import time


class SecurityManager:
    """Centralized security management"""
    
    def __init__(self, secret_key: str, encryption_key: Optional[str] = None):
        self.secret_key = secret_key
        self.encryption_key = encryption_key or self._generate_encryption_key()
        self.fernet = Fernet(self.encryption_key.encode() if isinstance(self.encryption_key, str) else self.encryption_key)
        self._failed_attempts = {}
        self._blocked_ips = {}
        
    def _generate_encryption_key(self) -> bytes:
        """Generate a new encryption key"""
        return Fernet.generate_key()
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            encrypted = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception:
            raise ValueError("Failed to encrypt data")
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(decoded)
            return decrypted.decode()
        except Exception:
            raise ValueError("Failed to decrypt data")
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate a cryptographically secure token"""
        return secrets.token_urlsafe(length)
    
    def hash_data(self, data: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash data with salt"""
        if not salt:
            salt = secrets.token_hex(16)
        
        hash_obj = hashlib.pbkdf2_hmac('sha256', data.encode(), salt.encode(), 100000)
        return hash_obj.hex(), salt
    
    def verify_hash(self, data: str, hashed: str, salt: str) -> bool:
        """Verify hashed data"""
        hash_obj = hashlib.pbkdf2_hmac('sha256', data.encode(), salt.encode(), 100000)
        return hmac.compare_digest(hash_obj.hex(), hashed)
    
    def create_jwt_token(self, payload: Dict[str, Any], expires_in: int = 3600) -> str:
        """Create JWT token"""
        payload['exp'] = datetime.utcnow() + timedelta(seconds=expires_in)
        payload['iat'] = datetime.utcnow()
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def record_failed_attempt(self, identifier: str):
        """Record failed authentication attempt"""
        now = time.time()
        if identifier not in self._failed_attempts:
            self._failed_attempts[identifier] = []
        
        # Remove attempts older than 1 hour
        self._failed_attempts[identifier] = [
            attempt for attempt in self._failed_attempts[identifier]
            if now - attempt < 3600
        ]
        
        self._failed_attempts[identifier].append(now)
        
        # Block if too many attempts
        if len(self._failed_attempts[identifier]) >= 5:
            self._blocked_ips[identifier] = now + 3600  # Block for 1 hour
    
    def is_blocked(self, identifier: str) -> bool:
        """Check if identifier is blocked"""
        if identifier in self._blocked_ips:
            if time.time() < self._blocked_ips[identifier]:
                return True
            else:
                del self._blocked_ips[identifier]
        return False
    
    def clear_failed_attempts(self, identifier: str):
        """Clear failed attempts for identifier"""
        if identifier in self._failed_attempts:
            del self._failed_attempts[identifier]
    
    def generate_api_key(self, user_id: str, permissions: list = None) -> str:
        """Generate API key with embedded permissions"""
        payload = {
            'user_id': user_id,
            'permissions': permissions or [],
            'created': datetime.utcnow().isoformat(),
            'type': 'api_key'
        }
        return self.create_jwt_token(payload, expires_in=365*24*3600)  # 1 year
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate API key and return user info"""
        payload = self.verify_jwt_token(api_key)
        if payload and payload.get('type') == 'api_key':
            return payload
        return None


def generate_csrf_token() -> str:
    """Generate CSRF token"""
    return secrets.token_urlsafe(32)


def verify_csrf_token(token: str, session_token: str) -> bool:
    """Verify CSRF token"""
    return hmac.compare_digest(token, session_token)


def hash_password(password: str) -> str:
    """Hash password using Werkzeug"""
    return generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return check_password_hash(password_hash, password)


def generate_api_key(length: int = 32) -> str:
    """Generate API key"""
    return secrets.token_urlsafe(length)


def encrypt_data(data: str, key: bytes) -> str:
    """Encrypt data with Fernet"""
    f = Fernet(key)
    encrypted = f.encrypt(data.encode())
    return base64.urlsafe_b64encode(encrypted).decode()


def decrypt_data(encrypted_data: str, key: bytes) -> str:
    """Decrypt data with Fernet"""
    f = Fernet(key)
    decoded = base64.urlsafe_b64decode(encrypted_data.encode())
    decrypted = f.decrypt(decoded)
    return decrypted.decode()


def create_signature(data: str, secret: str) -> str:
    """Create HMAC signature"""
    return hmac.new(
        secret.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()


def verify_signature(data: str, signature: str, secret: str) -> bool:
    """Verify HMAC signature"""
    expected = create_signature(data, secret)
    return hmac.compare_digest(signature, expected)


def sanitize_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Sanitize HTTP headers"""
    safe_headers = {}
    allowed_headers = {
        'content-type', 'authorization', 'user-agent', 'accept',
        'accept-language', 'accept-encoding', 'cache-control',
        'x-requested-with', 'x-csrf-token'
    }
    
    for key, value in headers.items():
        if key.lower() in allowed_headers:
            # Remove potentially dangerous characters
            safe_value = ''.join(c for c in value if c.isprintable())
            safe_headers[key] = safe_value[:1000]  # Limit length
    
    return safe_headers


def validate_origin(origin: str, allowed_origins: list) -> bool:
    """Validate request origin"""
    if not origin:
        return False
    
    # Check against allowed origins
    for allowed in allowed_origins:
        if allowed == '*':
            return True
        if origin == allowed:
            return True
        # Allow subdomains if specified
        if allowed.startswith('*.') and origin.endswith(allowed[1:]):
            return True
    
    return False


def rate_limit_decorator(max_requests: int = 100, window: int = 3600):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client identifier
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            
            # Create rate limit key
            key = f"rate_limit:{client_ip}:{request.endpoint}"
            
            # Check rate limit (this would typically use Redis)
            # For now, we'll use a simple in-memory store
            if not hasattr(current_app, '_rate_limits'):
                current_app._rate_limits = {}
            
            now = time.time()
            if key in current_app._rate_limits:
                requests, window_start = current_app._rate_limits[key]
                
                # Reset window if expired
                if now - window_start > window:
                    current_app._rate_limits[key] = (1, now)
                else:
                    if requests >= max_requests:
                        return jsonify({
                            'error': 'Rate limit exceeded',
                            'retry_after': int(window - (now - window_start))
                        }), 429
                    
                    current_app._rate_limits[key] = (requests + 1, window_start)
            else:
                current_app._rate_limits[key] = (1, now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_api_key(f):
    """Decorator to require valid API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Validate API key (implement your validation logic)
        security_manager = getattr(current_app, 'security_manager', None)
        if not security_manager:
            return jsonify({'error': 'Security manager not configured'}), 500
        
        user_info = security_manager.validate_api_key(api_key)
        if not user_info:
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Add user info to request context
        request.user_info = user_info
        
        return f(*args, **kwargs)
    return decorated_function


def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_info = getattr(request, 'user_info', None)
            
            if not user_info:
                return jsonify({'error': 'Authentication required'}), 401
            
            permissions = user_info.get('permissions', [])
            if permission not in permissions and 'admin' not in permissions:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def secure_filename(filename: str) -> str:
    """Secure filename for uploads"""
    # Remove path components
    filename = os.path.basename(filename)
    
    # Remove dangerous characters
    filename = ''.join(c for c in filename if c.isalnum() or c in '._-')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:250] + ext
    
    # Ensure it's not empty
    if not filename:
        filename = 'unnamed_file'
    
    return filename


def validate_file_upload(file_data: bytes, allowed_types: list, max_size: int = 10*1024*1024) -> Dict[str, Any]:
    """Validate uploaded file"""
    if len(file_data) > max_size:
        return {'valid': False, 'error': f'File too large (max {max_size} bytes)'}
    
    # Check file signature (magic bytes)
    file_signatures = {
        b'\x50\x4B\x03\x04': 'zip',  # ZIP
        b'\x4D\x5A': 'exe',          # EXE
        b'\xD0\xCF\x11\xE0': 'msi',  # MSI
        b'\x89\x50\x4E\x47': 'png',  # PNG
        b'\xFF\xD8\xFF': 'jpg',      # JPEG
    }
    
    detected_type = None
    for signature, file_type in file_signatures.items():
        if file_data.startswith(signature):
            detected_type = file_type
            break
    
    if detected_type not in allowed_types:
        return {
            'valid': False, 
            'error': f'Invalid file type. Allowed: {", ".join(allowed_types)}'
        }
    
    return {
        'valid': True,
        'type': detected_type,
        'size': len(file_data)
    }


def generate_download_token(file_path: str, user_id: str, expires_in: int = 3600) -> str:
    """Generate secure download token"""
    payload = {
        'file_path': file_path,
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(seconds=expires_in),
        'type': 'download'
    }
    
    # Use app secret key if available
    secret_key = getattr(current_app, 'secret_key', 'default-secret')
    return jwt.encode(payload, secret_key, algorithm='HS256')


def verify_download_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify download token"""
    try:
        secret_key = getattr(current_app, 'secret_key', 'default-secret')
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        
        if payload.get('type') != 'download':
            return None
        
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def log_security_event(event_type: str, details: Dict[str, Any], severity: str = 'INFO'):
    """Log security events"""
    from .logging_config import get_logger
    
    logger = get_logger('security')
    
    event_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'severity': severity,
        'client_ip': request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr) if request else 'unknown',
        'user_agent': request.headers.get('User-Agent', 'unknown') if request else 'unknown',
        'details': details
    }
    
    log_message = f"Security Event: {event_type} | {json.dumps(event_data)}"
    
    if severity == 'CRITICAL':
        logger.critical(log_message)
    elif severity == 'ERROR':
        logger.error(log_message)
    elif severity == 'WARNING':
        logger.warning(log_message)
    else:
        logger.info(log_message)


def mask_sensitive_info(data: str, visible_chars: int = 4) -> str:
    """Mask sensitive information for logging"""
    if len(data) <= visible_chars:
        return '*' * len(data)
    
    return data[:visible_chars] + '*' * (len(data) - visible_chars)