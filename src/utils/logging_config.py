#!/usr/bin/env python3
"""
Logging configuration for Gotcha Guardian Payment Server
Provides centralized logging setup and utilities
"""

import os
import logging
import logging.handlers
import json
from datetime import datetime
from typing import Optional, Dict, Any
from flask import request, g
import traceback
import sys


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        if hasattr(record, 'ip_address'):
            log_entry['ip_address'] = record.ip_address
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info', 'request_id', 'user_id', 'ip_address']:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class RequestContextFilter(logging.Filter):
    """Filter to add request context to log records"""
    
    def filter(self, record):
        # Add request ID if available
        if hasattr(g, 'request_id'):
            record.request_id = g.request_id
        
        # Add user ID if available
        if hasattr(g, 'user_id'):
            record.user_id = g.user_id
        
        # Add IP address if request context is available
        try:
            if request:
                record.ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        except RuntimeError:
            # Outside request context
            pass
        
        return True


def setup_logging(app_name: str = 'gotcha_guardian', 
                 log_level: str = 'INFO',
                 log_dir: str = 'logs',
                 max_bytes: int = 10*1024*1024,  # 10MB
                 backup_count: int = 5,
                 json_format: bool = True) -> Dict[str, logging.Logger]:
    """Setup comprehensive logging configuration"""
    
    # Create logs directory if it doesn't exist
    try:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
    except (OSError, PermissionError) as e:
        # Fallback to current directory if logs directory can't be created
        print(f"Warning: Could not create log directory '{log_dir}': {e}")
        print("Falling back to current directory for logs")
        log_dir = '.'
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Create request context filter
    context_filter = RequestContextFilter()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(context_filter)
    
    # Main application log file
    app_handler = None
    try:
        app_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, f'{app_name}.log'),
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        app_handler.setLevel(getattr(logging, log_level.upper()))
        app_handler.setFormatter(formatter)
        app_handler.addFilter(context_filter)
    except (OSError, PermissionError) as e:
        print(f"Warning: Could not create application log file: {e}")
        print("Application will use console logging only")
    
    # Error log file
    error_handler = None
    try:
        error_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, f'{app_name}_errors.log'),
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        error_handler.addFilter(context_filter)
    except (OSError, PermissionError) as e:
        print(f"Warning: Could not create error log file: {e}")
    
    # Security log file
    security_handler = None
    try:
        security_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, f'{app_name}_security.log'),
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        security_handler.setLevel(logging.INFO)
        security_handler.setFormatter(formatter)
        security_handler.addFilter(context_filter)
    except (OSError, PermissionError) as e:
        print(f"Warning: Could not create security log file: {e}")
    
    # Payment log file
    payment_handler = None
    try:
        payment_handler = logging.handlers.RotatingFileHandler(
            os.path.join(log_dir, f'{app_name}_payments.log'),
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        payment_handler.setLevel(logging.INFO)
        payment_handler.setFormatter(formatter)
        payment_handler.addFilter(context_filter)
    except (OSError, PermissionError) as e:
        print(f"Warning: Could not create payment log file: {e}")
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    if app_handler:
        root_logger.addHandler(app_handler)
    if error_handler:
        root_logger.addHandler(error_handler)
    
    # Create specialized loggers
    loggers = {
        'app': logging.getLogger(app_name),
        'security': logging.getLogger(f'{app_name}.security'),
        'payment': logging.getLogger(f'{app_name}.payment'),
        'database': logging.getLogger(f'{app_name}.database'),
        'email': logging.getLogger(f'{app_name}.email'),
        'api': logging.getLogger(f'{app_name}.api')
    }
    
    # Configure security logger
    if security_handler:
        loggers['security'].addHandler(security_handler)
    loggers['security'].propagate = False
    
    # Configure payment logger
    if payment_handler:
        loggers['payment'].addHandler(payment_handler)
    loggers['payment'].propagate = False
    
    # Set levels for specialized loggers
    for logger in loggers.values():
        logger.setLevel(getattr(logging, log_level.upper()))
    
    return loggers


def get_logger(name: str = 'gotcha_guardian') -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)


def log_request(logger: logging.Logger, 
               method: str, 
               url: str, 
               status_code: int, 
               response_time: float,
               user_id: Optional[str] = None,
               additional_data: Optional[Dict[str, Any]] = None):
    """Log HTTP request details"""
    
    log_data = {
        'event_type': 'http_request',
        'method': method,
        'url': url,
        'status_code': status_code,
        'response_time_ms': round(response_time * 1000, 2),
        'user_id': user_id
    }
    
    if additional_data:
        log_data.update(additional_data)
    
    # Add request context
    try:
        if request:
            log_data.update({
                'ip_address': request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
                'user_agent': request.headers.get('User-Agent', 'unknown'),
                'referer': request.headers.get('Referer', 'unknown')
            })
    except RuntimeError:
        pass
    
    # Log at appropriate level based on status code
    if status_code >= 500:
        logger.error(f"HTTP {status_code} - {method} {url}", extra=log_data)
    elif status_code >= 400:
        logger.warning(f"HTTP {status_code} - {method} {url}", extra=log_data)
    else:
        logger.info(f"HTTP {status_code} - {method} {url}", extra=log_data)


def log_error(logger: logging.Logger, 
             error: Exception, 
             context: Optional[Dict[str, Any]] = None,
             user_id: Optional[str] = None):
    """Log error with context"""
    
    log_data = {
        'event_type': 'error',
        'error_type': type(error).__name__,
        'error_message': str(error),
        'user_id': user_id
    }
    
    if context:
        log_data['context'] = context
    
    logger.error(f"Error: {type(error).__name__}: {str(error)}", 
                exc_info=True, extra=log_data)


def log_security_event(logger: logging.Logger,
                      event_type: str,
                      severity: str,
                      details: Dict[str, Any],
                      user_id: Optional[str] = None):
    """Log security events"""
    
    log_data = {
        'event_type': 'security_event',
        'security_event_type': event_type,
        'severity': severity,
        'user_id': user_id,
        'details': details
    }
    
    # Add request context
    try:
        if request:
            log_data.update({
                'ip_address': request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr),
                'user_agent': request.headers.get('User-Agent', 'unknown'),
                'endpoint': request.endpoint
            })
    except RuntimeError:
        pass
    
    message = f"Security Event: {event_type} - {severity}"
    
    if severity == 'CRITICAL':
        logger.critical(message, extra=log_data)
    elif severity == 'HIGH':
        logger.error(message, extra=log_data)
    elif severity == 'MEDIUM':
        logger.warning(message, extra=log_data)
    else:
        logger.info(message, extra=log_data)


def log_payment_event(logger: logging.Logger,
                     event_type: str,
                     payment_id: str,
                     amount: float,
                     currency: str = 'USD',
                     status: str = 'unknown',
                     user_id: Optional[str] = None,
                     additional_data: Optional[Dict[str, Any]] = None):
    """Log payment events"""
    
    log_data = {
        'event_type': 'payment_event',
        'payment_event_type': event_type,
        'payment_id': payment_id,
        'amount': amount,
        'currency': currency,
        'status': status,
        'user_id': user_id
    }
    
    if additional_data:
        log_data.update(additional_data)
    
    message = f"Payment Event: {event_type} - {payment_id} - ${amount} {currency}"
    logger.info(message, extra=log_data)


def log_database_operation(logger: logging.Logger,
                          operation: str,
                          table: str,
                          record_id: Optional[str] = None,
                          execution_time: Optional[float] = None,
                          user_id: Optional[str] = None):
    """Log database operations"""
    
    log_data = {
        'event_type': 'database_operation',
        'operation': operation,
        'table': table,
        'record_id': record_id,
        'user_id': user_id
    }
    
    if execution_time:
        log_data['execution_time_ms'] = round(execution_time * 1000, 2)
    
    message = f"DB Operation: {operation} on {table}"
    if record_id:
        message += f" (ID: {record_id})"
    
    logger.info(message, extra=log_data)


def log_email_event(logger: logging.Logger,
                   event_type: str,
                   recipient: str,
                   subject: str,
                   status: str = 'sent',
                   error_message: Optional[str] = None):
    """Log email events"""
    
    # Mask email for privacy
    masked_email = mask_email(recipient)
    
    log_data = {
        'event_type': 'email_event',
        'email_event_type': event_type,
        'recipient': masked_email,
        'subject': subject,
        'status': status
    }
    
    if error_message:
        log_data['error_message'] = error_message
    
    message = f"Email Event: {event_type} to {masked_email} - {status}"
    
    if status == 'failed':
        logger.error(message, extra=log_data)
    else:
        logger.info(message, extra=log_data)


def mask_email(email: str) -> str:
    """Mask email address for privacy"""
    if '@' not in email:
        return '*' * len(email)
    
    local, domain = email.split('@', 1)
    
    if len(local) <= 2:
        masked_local = '*' * len(local)
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    
    return f"{masked_local}@{domain}"


def setup_request_logging(app):
    """Setup request logging middleware"""
    
    @app.before_request
    def before_request():
        g.start_time = datetime.utcnow()
        g.request_id = generate_request_id()
    
    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = (datetime.utcnow() - g.start_time).total_seconds()
            
            logger = get_logger('gotcha_guardian.api')
            log_request(
                logger=logger,
                method=request.method,
                url=request.url,
                status_code=response.status_code,
                response_time=duration
            )
        
        return response
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        logger = get_logger('gotcha_guardian')
        log_error(logger, error, context={'endpoint': request.endpoint})
        
        # Return appropriate error response
        if hasattr(error, 'code'):
            return {'error': str(error)}, error.code
        else:
            return {'error': 'Internal server error'}, 500


def generate_request_id() -> str:
    """Generate unique request ID"""
    import uuid
    return str(uuid.uuid4())[:8]


def configure_werkzeug_logging():
    """Configure Werkzeug logging to reduce noise"""
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.WARNING)


def configure_sqlalchemy_logging(echo: bool = False):
    """Configure SQLAlchemy logging"""
    if echo:
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
        logging.getLogger('sqlalchemy.dialects').setLevel(logging.INFO)
        logging.getLogger('sqlalchemy.pool').setLevel(logging.INFO)
        logging.getLogger('sqlalchemy.orm').setLevel(logging.INFO)
    else:
        logging.getLogger('sqlalchemy').setLevel(logging.WARNING)


class LoggingMiddleware:
    """WSGI middleware for request logging"""
    
    def __init__(self, app, logger_name: str = 'gotcha_guardian.middleware'):
        self.app = app
        self.logger = get_logger(logger_name)
    
    def __call__(self, environ, start_response):
        start_time = datetime.utcnow()
        
        def new_start_response(status, response_headers, exc_info=None):
            duration = (datetime.utcnow() - start_time).total_seconds()
            
            self.logger.info(
                f"Request: {environ.get('REQUEST_METHOD')} {environ.get('PATH_INFO')} - {status}",
                extra={
                    'method': environ.get('REQUEST_METHOD'),
                    'path': environ.get('PATH_INFO'),
                    'status': status,
                    'duration_ms': round(duration * 1000, 2),
                    'ip_address': environ.get('HTTP_X_FORWARDED_FOR', environ.get('REMOTE_ADDR')),
                    'user_agent': environ.get('HTTP_USER_AGENT')
                }
            )
            
            return start_response(status, response_headers, exc_info)
        
        return self.app(environ, new_start_response)
