#!/usr/bin/env python3
"""
Helper utilities for Gotcha Guardian Payment Server
Provides various utility functions for common operations
"""

import os
import shutil
import zipfile
import hashlib
import secrets
import string
import json
import csv
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
from decimal import Decimal
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import requests
from pathlib import Path
import time


def format_currency(amount: Union[float, Decimal, str], currency: str = 'USD') -> str:
    """Format currency amount for display"""
    try:
        if isinstance(amount, str):
            amount = Decimal(amount)
        elif isinstance(amount, float):
            amount = Decimal(str(amount))
        
        # Format based on currency
        if currency.upper() == 'USD':
            return f"${amount:.2f}"
        elif currency.upper() == 'EUR':
            return f"€{amount:.2f}"
        elif currency.upper() == 'GBP':
            return f"£{amount:.2f}"
        else:
            return f"{amount:.2f} {currency.upper()}"
    
    except (ValueError, TypeError):
        return f"0.00 {currency.upper()}"


def format_datetime(dt: datetime, format_type: str = 'default') -> str:
    """Format datetime for display"""
    if not isinstance(dt, datetime):
        return 'Invalid date'
    
    formats = {
        'default': '%Y-%m-%d %H:%M:%S',
        'date_only': '%Y-%m-%d',
        'time_only': '%H:%M:%S',
        'friendly': '%B %d, %Y at %I:%M %p',
        'iso': '%Y-%m-%dT%H:%M:%SZ',
        'compact': '%Y%m%d_%H%M%S'
    }
    
    format_str = formats.get(format_type, formats['default'])
    return dt.strftime(format_str)


def generate_order_id(prefix: str = 'ORD', length: int = 8) -> str:
    """Generate unique order ID"""
    timestamp = datetime.now().strftime('%Y%m%d')
    random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(length))
    return f"{prefix}-{timestamp}-{random_part}"


def calculate_file_size(file_path: str) -> Dict[str, Any]:
    """Calculate file size and return formatted information"""
    try:
        size_bytes = os.path.getsize(file_path)
        
        # Convert to human readable format
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                size_formatted = f"{size_bytes:.1f} {unit}"
                break
            size_bytes /= 1024.0
        else:
            size_formatted = f"{size_bytes:.1f} PB"
        
        return {
            'success': True,
            'size_bytes': os.path.getsize(file_path),
            'size_formatted': size_formatted,
            'file_path': file_path
        }
    
    except (FileNotFoundError, PermissionError) as e:
        return {
            'success': False,
            'error': str(e),
            'file_path': file_path
        }


def create_backup(source_path: str, backup_dir: str = 'backups', 
                 include_timestamp: bool = True) -> Dict[str, Any]:
    """Create backup of file or directory"""
    try:
        # Create backup directory if it doesn't exist
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generate backup filename
        source_name = os.path.basename(source_path)
        if include_timestamp:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{source_name}_{timestamp}"
        else:
            backup_name = f"{source_name}_backup"
        
        backup_path = os.path.join(backup_dir, backup_name)
        
        # Create backup
        if os.path.isfile(source_path):
            shutil.copy2(source_path, backup_path)
        elif os.path.isdir(source_path):
            shutil.copytree(source_path, backup_path)
        else:
            return {
                'success': False,
                'error': 'Source path does not exist or is not accessible'
            }
        
        return {
            'success': True,
            'backup_path': backup_path,
            'source_path': source_path,
            'backup_size': calculate_file_size(backup_path)
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'source_path': source_path
        }


def send_notification(notification_type: str, 
                     recipient: str, 
                     subject: str, 
                     message: str,
                     smtp_config: Dict[str, Any],
                     attachments: Optional[List[str]] = None) -> Dict[str, Any]:
    """Send email notification"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = smtp_config['from_email']
        msg['To'] = recipient
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(message, 'html' if '<' in message else 'plain'))
        
        # Add attachments if provided
        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(file_path)}'
                    )
                    msg.attach(part)
        
        # Send email
        with smtplib.SMTP(smtp_config['host'], smtp_config['port']) as server:
            if smtp_config.get('use_tls'):
                server.starttls()
            
            if smtp_config.get('username') and smtp_config.get('password'):
                server.login(smtp_config['username'], smtp_config['password'])
            
            server.send_message(msg)
        
        return {
            'success': True,
            'recipient': recipient,
            'subject': subject,
            'notification_type': notification_type
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'recipient': recipient,
            'notification_type': notification_type
        }


def create_zip_archive(files: List[str], archive_path: str, 
                      compression: int = zipfile.ZIP_DEFLATED) -> Dict[str, Any]:
    """Create ZIP archive from list of files"""
    try:
        with zipfile.ZipFile(archive_path, 'w', compression) as zipf:
            for file_path in files:
                if os.path.exists(file_path):
                    # Add file to archive with relative path
                    arcname = os.path.basename(file_path)
                    zipf.write(file_path, arcname)
                else:
                    return {
                        'success': False,
                        'error': f'File not found: {file_path}'
                    }
        
        return {
            'success': True,
            'archive_path': archive_path,
            'file_count': len(files),
            'archive_size': calculate_file_size(archive_path)
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'archive_path': archive_path
        }


def extract_zip_archive(archive_path: str, extract_to: str) -> Dict[str, Any]:
    """Extract ZIP archive to specified directory"""
    try:
        os.makedirs(extract_to, exist_ok=True)
        
        with zipfile.ZipFile(archive_path, 'r') as zipf:
            # Check for potentially dangerous paths
            for member in zipf.namelist():
                if os.path.isabs(member) or '..' in member:
                    return {
                        'success': False,
                        'error': f'Unsafe path in archive: {member}'
                    }
            
            zipf.extractall(extract_to)
            extracted_files = zipf.namelist()
        
        return {
            'success': True,
            'extract_path': extract_to,
            'extracted_files': extracted_files,
            'file_count': len(extracted_files)
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'archive_path': archive_path
        }


def calculate_hash(data: Union[str, bytes], algorithm: str = 'sha256') -> str:
    """Calculate hash of data"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(data)
    return hash_obj.hexdigest()


def verify_file_integrity(file_path: str, expected_hash: str, 
                         algorithm: str = 'sha256') -> bool:
    """Verify file integrity using hash"""
    try:
        with open(file_path, 'rb') as f:
            file_hash = hashlib.new(algorithm)
            for chunk in iter(lambda: f.read(4096), b''):
                file_hash.update(chunk)
        
        return file_hash.hexdigest().lower() == expected_hash.lower()
    
    except (FileNotFoundError, PermissionError):
        return False


def clean_old_files(directory: str, max_age_days: int = 30, 
                   file_pattern: str = '*') -> Dict[str, Any]:
    """Clean old files from directory"""
    try:
        from pathlib import Path
        import glob
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        pattern_path = os.path.join(directory, file_pattern)
        
        deleted_files = []
        total_size_freed = 0
        
        for file_path in glob.glob(pattern_path):
            if os.path.isfile(file_path):
                file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_mtime < cutoff_date:
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    deleted_files.append(file_path)
                    total_size_freed += file_size
        
        return {
            'success': True,
            'deleted_files': deleted_files,
            'files_deleted': len(deleted_files),
            'size_freed_bytes': total_size_freed,
            'size_freed_formatted': format_file_size(total_size_freed)
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'directory': directory
        }


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def validate_json_file(file_path: str) -> Dict[str, Any]:
    """Validate JSON file format"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            'valid': True,
            'data': data,
            'file_path': file_path
        }
    
    except json.JSONDecodeError as e:
        return {
            'valid': False,
            'error': f'JSON decode error: {str(e)}',
            'file_path': file_path
        }
    except FileNotFoundError:
        return {
            'valid': False,
            'error': 'File not found',
            'file_path': file_path
        }
    except Exception as e:
        return {
            'valid': False,
            'error': str(e),
            'file_path': file_path
        }


def export_to_csv(data: List[Dict[str, Any]], file_path: str, 
                 fieldnames: Optional[List[str]] = None) -> Dict[str, Any]:
    """Export data to CSV file"""
    try:
        if not data:
            return {
                'success': False,
                'error': 'No data to export'
            }
        
        if not fieldnames:
            fieldnames = list(data[0].keys())
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        return {
            'success': True,
            'file_path': file_path,
            'records_exported': len(data),
            'file_size': calculate_file_size(file_path)
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'file_path': file_path
        }


def import_from_csv(file_path: str) -> Dict[str, Any]:
    """Import data from CSV file"""
    try:
        data = []
        
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(row)
        
        return {
            'success': True,
            'data': data,
            'records_imported': len(data),
            'file_path': file_path
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'file_path': file_path
        }


def make_http_request(url: str, method: str = 'GET', 
                     headers: Optional[Dict[str, str]] = None,
                     data: Optional[Dict[str, Any]] = None,
                     timeout: int = 30) -> Dict[str, Any]:
    """Make HTTP request with error handling"""
    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            json=data if method.upper() in ['POST', 'PUT', 'PATCH'] else None,
            params=data if method.upper() == 'GET' else None,
            timeout=timeout
        )
        
        return {
            'success': True,
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            'url': url
        }
    
    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Request timeout',
            'url': url
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'Connection error',
            'url': url
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'url': url
        }


def retry_operation(func, max_retries: int = 3, delay: float = 1.0, 
                   backoff_factor: float = 2.0, exceptions: tuple = (Exception,)):
    """Retry operation with exponential backoff"""
    def wrapper(*args, **kwargs):
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                
                if attempt < max_retries:
                    sleep_time = delay * (backoff_factor ** attempt)
                    time.sleep(sleep_time)
                else:
                    raise last_exception
        
        raise last_exception
    
    return wrapper


def generate_qr_code(data: str, file_path: str, size: int = 10) -> Dict[str, Any]:
    """Generate QR code (requires qrcode library)"""
    try:
        import qrcode
        from PIL import Image
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=4,
        )
        
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(file_path)
        
        return {
            'success': True,
            'file_path': file_path,
            'data': data,
            'file_size': calculate_file_size(file_path)
        }
    
    except ImportError:
        return {
            'success': False,
            'error': 'QR code library not installed (pip install qrcode[pil])'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'file_path': file_path
        }


def monitor_system_resources() -> Dict[str, Any]:
    """Monitor system resources (requires psutil library)"""
    try:
        import psutil
        
        return {
            'success': True,
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent
            },
            'timestamp': datetime.now().isoformat()
        }
    
    except ImportError:
        return {
            'success': False,
            'error': 'System monitoring library not installed (pip install psutil)'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def create_directory_structure(base_path: str, structure: Dict[str, Any]) -> Dict[str, Any]:
    """Create directory structure from dictionary"""
    try:
        created_dirs = []
        created_files = []
        
        def create_structure(current_path: str, items: Dict[str, Any]):
            for name, content in items.items():
                item_path = os.path.join(current_path, name)
                
                if isinstance(content, dict):
                    # It's a directory
                    os.makedirs(item_path, exist_ok=True)
                    created_dirs.append(item_path)
                    create_structure(item_path, content)
                else:
                    # It's a file
                    os.makedirs(os.path.dirname(item_path), exist_ok=True)
                    with open(item_path, 'w', encoding='utf-8') as f:
                        f.write(str(content) if content is not None else '')
                    created_files.append(item_path)
        
        os.makedirs(base_path, exist_ok=True)
        create_structure(base_path, structure)
        
        return {
            'success': True,
            'base_path': base_path,
            'created_directories': created_dirs,
            'created_files': created_files,
            'total_items': len(created_dirs) + len(created_files)
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'base_path': base_path
        }