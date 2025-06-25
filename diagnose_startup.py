#!/usr/bin/env python3
"""
Diagnostic script to identify startup issues
"""

import sys
import os
import traceback

print("=== Gotcha Guardian Payment Server Startup Diagnosis ===")
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")
print()

try:
    print("Step 1: Testing basic imports...")
    import flask
    import sqlite3
    import smtplib
    print("✅ Basic imports successful")
    
    print("\nStep 2: Testing config import...")
    from config import config
    print("✅ Config import successful")
    print(f"   - Debug mode: {config.DEBUG}")
    print(f"   - PayPal mode: {config.PAYPAL_MODE}")
    print(f"   - Host: {config.HOST}")
    print(f"   - Port: {config.PORT}")
    
    print("\nStep 3: Testing config validation...")
    errors = config.validate()
    if errors:
        print("⚠️  Configuration errors found:")
        for error in errors:
            print(f"   - {error}")
    else:
        print("✅ Configuration validation passed")
    
    print("\nStep 4: Testing service imports...")
    from src.models.database import DatabaseManager
    from src.services.email_service import EmailService
    from src.services.payment_service import PaymentService
    from src.services.product_service import ProductService
    print("✅ Service imports successful")
    
    print("\nStep 5: Testing service initialization...")
    db_manager = DatabaseManager(config)
    email_service = EmailService(config)
    payment_service = PaymentService(config, db_manager)
    product_service = ProductService(config)
    print("✅ Service initialization successful")
    
    print("\nStep 6: Testing Flask app creation...")
    from flask import Flask
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.SECRET_KEY
    print("✅ Flask app creation successful")
    
    print("\n🎉 All diagnostic checks passed!")
    print("\nThe server should be able to start. Try running:")
    print("   python payment_server.py")
    print("   or")
    print("   python run_dev.py")
    
except Exception as e:
    print(f"\n❌ Error during diagnosis: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
    print("\nThis error is likely preventing the server from starting.")
