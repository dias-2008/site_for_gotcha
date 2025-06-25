#!/usr/bin/env python3
"""
Gotcha Guardian Payment Server Setup Script

This script automates the initial setup process for the payment server,
including directory creation, database initialization, and configuration validation.
"""

import os
import sys
import subprocess
import secrets
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional


class SetupManager:
    """Manages the setup process for the payment server."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.required_dirs = [
            'data',
            'logs', 
            'products',
            'backups',
            'temp',
            'static/css',
            'static/js',
            'static/images',
            'templates/main',
            'templates/admin',
            'templates/emails'
        ]
        self.required_files = [
            '.env',
            'config/products.json'
        ]
        
    def run_setup(self, interactive: bool = True) -> bool:
        """Run the complete setup process."""
        print("🚀 Gotcha Guardian Payment Server Setup")
        print("=" * 50)
        
        try:
            # Check Python version
            if not self._check_python_version():
                return False
                
            # Create directories
            self._create_directories()
            
            # Check dependencies
            if not self._check_dependencies():
                if interactive and self._prompt_install_dependencies():
                    self._install_dependencies()
                else:
                    print("❌ Dependencies not installed. Run 'pip install -r requirements.txt'")
                    return False
            
            # Setup environment file
            if interactive:
                self._setup_environment_file()
            else:
                self._create_default_env()
            
            # Initialize database
            self._initialize_database()
            
            # Validate configuration
            self._validate_configuration()
            
            # Create sample product files
            self._create_sample_products()
            
            # Set permissions
            self._set_permissions()
            
            print("\n✅ Setup completed successfully!")
            print("\n📋 Next steps:")
            print("1. Edit .env file with your configuration")
            print("2. Update config/products.json with your products")
            print("3. Add your product files to the products/ directory")
            print("4. Run: python payment_server.py")
            
            return True
            
        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False
    
    def _check_python_version(self) -> bool:
        """Check if Python version is compatible."""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 9):
            print(f"❌ Python 3.9+ required. Current version: {version.major}.{version.minor}")
            return False
        print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    
    def _create_directories(self) -> None:
        """Create required directories."""
        print("\n📁 Creating directories...")
        for dir_path in self.required_dirs:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  ✅ {dir_path}")
    
    def _check_dependencies(self) -> bool:
        """Check if required dependencies are installed."""
        print("\n📦 Checking dependencies...")
        try:
            import flask
            import paypalrestsdk
            import marshmallow
            import cryptography
            print("  ✅ All dependencies installed")
            return True
        except ImportError as e:
            print(f"  ❌ Missing dependency: {e.name}")
            return False
    
    def _prompt_install_dependencies(self) -> bool:
        """Prompt user to install dependencies."""
        response = input("\n❓ Install dependencies now? (y/n): ").lower().strip()
        return response in ['y', 'yes']
    
    def _install_dependencies(self) -> None:
        """Install dependencies from requirements.txt."""
        print("\n📦 Installing dependencies...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
            print("  ✅ Dependencies installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to install dependencies: {e}")
            raise
    
    def _setup_environment_file(self) -> None:
        """Interactive setup of environment file."""
        print("\n🔧 Setting up environment configuration...")
        
        env_path = self.project_root / '.env'
        if env_path.exists():
            response = input("  .env file exists. Overwrite? (y/n): ").lower().strip()
            if response not in ['y', 'yes']:
                print("  ⏭️  Skipping environment setup")
                return
        
        config = self._collect_environment_config()
        self._write_environment_file(config)
        print("  ✅ Environment file created")
    
    def _collect_environment_config(self) -> Dict[str, str]:
        """Collect environment configuration from user."""
        config = {}
        
        print("\n  📝 Please provide the following configuration:")
        
        # Application settings
        config['FLASK_ENV'] = self._prompt_with_default("Flask environment", "development")
        config['FLASK_DEBUG'] = "True" if config['FLASK_ENV'] == 'development' else "False"
        config['SECRET_KEY'] = self._generate_secret_key()
        config['BASE_URL'] = self._prompt_with_default("Base URL", "http://localhost:5000")
        
        # PayPal settings
        print("\n  💳 PayPal Configuration:")
        config['PAYPAL_MODE'] = self._prompt_with_default("PayPal mode", "sandbox")
        config['PAYPAL_CLIENT_ID'] = input("    PayPal Client ID: ").strip()
        config['PAYPAL_CLIENT_SECRET'] = input("    PayPal Client Secret: ").strip()
        config['PAYPAL_WEBHOOK_ID'] = input("    PayPal Webhook ID (optional): ").strip()
        config['PAYPAL_WEBHOOK_URL'] = f"{config['BASE_URL']}/api/paypal/webhook"
        
        # Email settings
        print("\n  📧 Email Configuration:")
        config['SMTP_SERVER'] = self._prompt_with_default("SMTP Server", "smtp.gmail.com")
        config['SMTP_PORT'] = self._prompt_with_default("SMTP Port", "587")
        config['SMTP_USERNAME'] = input("    SMTP Username: ").strip()
        config['SMTP_PASSWORD'] = input("    SMTP Password: ").strip()
        config['FROM_EMAIL'] = self._prompt_with_default("From Email", config['SMTP_USERNAME'])
        config['ADMIN_EMAIL'] = input("    Admin Email: ").strip()
        config['SUPPORT_EMAIL'] = self._prompt_with_default("Support Email", config['ADMIN_EMAIL'])
        
        # Security settings
        config['ENCRYPTION_KEY'] = self._generate_encryption_key()
        config['JWT_SECRET_KEY'] = self._generate_secret_key()
        
        return config
    
    def _prompt_with_default(self, prompt: str, default: str) -> str:
        """Prompt user with a default value."""
        response = input(f"    {prompt} [{default}]: ").strip()
        return response if response else default
    
    def _generate_secret_key(self) -> str:
        """Generate a secure secret key."""
        return secrets.token_urlsafe(32)
    
    def _generate_encryption_key(self) -> str:
        """Generate a secure encryption key."""
        return secrets.token_urlsafe(32)
    
    def _write_environment_file(self, config: Dict[str, str]) -> None:
        """Write environment configuration to .env file."""
        env_content = []
        
        # Application Settings
        env_content.extend([
            "# Application Settings",
            f"FLASK_ENV={config['FLASK_ENV']}",
            f"FLASK_DEBUG={config['FLASK_DEBUG']}",
            f"SECRET_KEY={config['SECRET_KEY']}",
            f"BASE_URL={config['BASE_URL']}",
            ""
        ])
        
        # Database Settings
        env_content.extend([
            "# Database Settings",
            "DATABASE_PATH=./data/payment_server.db",
            ""
        ])
        
        # PayPal Settings
        env_content.extend([
            "# PayPal Settings",
            f"PAYPAL_MODE={config['PAYPAL_MODE']}",
            f"PAYPAL_CLIENT_ID={config['PAYPAL_CLIENT_ID']}",
            f"PAYPAL_CLIENT_SECRET={config['PAYPAL_CLIENT_SECRET']}",
            f"PAYPAL_WEBHOOK_ID={config['PAYPAL_WEBHOOK_ID']}",
            f"PAYPAL_WEBHOOK_URL={config['PAYPAL_WEBHOOK_URL']}",
            ""
        ])
        
        # Email Settings
        env_content.extend([
            "# Email Settings",
            f"SMTP_SERVER={config['SMTP_SERVER']}",
            f"SMTP_PORT={config['SMTP_PORT']}",
            f"SMTP_USERNAME={config['SMTP_USERNAME']}",
            f"SMTP_PASSWORD={config['SMTP_PASSWORD']}",
            f"FROM_EMAIL={config['FROM_EMAIL']}",
            f"ADMIN_EMAIL={config['ADMIN_EMAIL']}",
            f"SUPPORT_EMAIL={config['SUPPORT_EMAIL']}",
            ""
        ])
        
        # Security Settings
        env_content.extend([
            "# Security Settings",
            f"ENCRYPTION_KEY={config['ENCRYPTION_KEY']}",
            f"JWT_SECRET_KEY={config['JWT_SECRET_KEY']}",
            "RATE_LIMIT_ENABLED=True",
            "SECURE_HEADERS_ENABLED=True",
            "CSRF_PROTECTION_ENABLED=True",
            ""
        ])
        
        # Logging Settings
        env_content.extend([
            "# Logging Settings",
            "LOG_LEVEL=INFO",
            "LOG_DIR=./logs",
            "CONSOLE_LOG_ENABLED=True",
            "CONSOLE_LOG_LEVEL=INFO",
            ""
        ])
        
        # File Storage Settings
        env_content.extend([
            "# File Storage Settings",
            "PRODUCT_FILES_DIR=./products",
            "BACKUP_DIR=./backups",
            "TEMP_DIR=./temp",
            ""
        ])
        
        with open(self.project_root / '.env', 'w') as f:
            f.write('\n'.join(env_content))
    
    def _create_default_env(self) -> None:
        """Create a default .env file for non-interactive setup."""
        print("\n🔧 Creating default environment file...")
        
        env_path = self.project_root / '.env'
        if not env_path.exists():
            example_path = self.project_root / '.env.example'
            if example_path.exists():
                import shutil
                shutil.copy(example_path, env_path)
                print("  ✅ Default environment file created from .env.example")
            else:
                print("  ⚠️  No .env.example found. Please create .env manually")
    
    def _initialize_database(self) -> None:
        """Initialize the database."""
        print("\n🗄️  Initializing database...")
        try:
            # Add the src directory to Python path
            sys.path.insert(0, str(self.project_root / 'src'))
            
            from src.models.database import DatabaseManager
            db_manager = DatabaseManager()
            db_manager.init_db()
            print("  ✅ Database initialized successfully")
        except Exception as e:
            print(f"  ⚠️  Database initialization failed: {e}")
            print("  💡 You can initialize it later by running:")
            print("     python -c \"from src.models.database import DatabaseManager; DatabaseManager().init_db()\"")
    
    def _validate_configuration(self) -> None:
        """Validate the configuration."""
        print("\n🔍 Validating configuration...")
        
        # Check .env file
        env_path = self.project_root / '.env'
        if env_path.exists():
            print("  ✅ .env file exists")
        else:
            print("  ⚠️  .env file missing")
        
        # Check products.json
        products_path = self.project_root / 'config' / 'products.json'
        if products_path.exists():
            try:
                with open(products_path, 'r') as f:
                    json.load(f)
                print("  ✅ products.json is valid")
            except json.JSONDecodeError:
                print("  ⚠️  products.json is invalid JSON")
        else:
            print("  ⚠️  products.json missing")
    
    def _create_sample_products(self) -> None:
        """Create sample product files."""
        print("\n📦 Creating sample product files...")
        
        # Create a sample ZIP file
        sample_file = self.project_root / 'products' / 'sample-product.zip'
        if not sample_file.exists():
            import zipfile
            with zipfile.ZipFile(sample_file, 'w') as zf:
                zf.writestr('README.txt', 'This is a sample product file.\nReplace with your actual product files.')
                zf.writestr('version.txt', '1.0.0')
            print("  ✅ Sample product file created")
        
        # Calculate hash for the sample file
        file_hash = self._calculate_file_hash(sample_file)
        file_size = sample_file.stat().st_size
        
        # Update products.json with sample data
        products_path = self.project_root / 'config' / 'products.json'
        if products_path.exists():
            with open(products_path, 'r') as f:
                products_config = json.load(f)
            
            # Update the basic product with actual file info
            if 'products' in products_config and 'basic' in products_config['products']:
                products_config['products']['basic']['file']['filename'] = 'sample-product.zip'
                products_config['products']['basic']['file']['size'] = file_size
                products_config['products']['basic']['file']['hash'] = file_hash
                
                with open(products_path, 'w') as f:
                    json.dump(products_config, f, indent=2)
                print("  ✅ Updated products.json with sample file info")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _set_permissions(self) -> None:
        """Set appropriate file permissions."""
        print("\n🔒 Setting file permissions...")
        
        if os.name != 'nt':  # Not Windows
            try:
                # Set directory permissions
                for dir_path in self.required_dirs:
                    full_path = self.project_root / dir_path
                    if full_path.exists():
                        os.chmod(full_path, 0o755)
                
                # Set .env file permissions
                env_path = self.project_root / '.env'
                if env_path.exists():
                    os.chmod(env_path, 0o600)
                
                print("  ✅ File permissions set")
            except Exception as e:
                print(f"  ⚠️  Failed to set permissions: {e}")
        else:
            print("  ⏭️  Skipping permission setup on Windows")


def main():
    """Main setup function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup Gotcha Guardian Payment Server')
    parser.add_argument('--non-interactive', action='store_true', 
                       help='Run setup without user interaction')
    parser.add_argument('--skip-deps', action='store_true',
                       help='Skip dependency installation')
    
    args = parser.parse_args()
    
    setup_manager = SetupManager()
    
    try:
        success = setup_manager.run_setup(interactive=not args.non_interactive)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()