#!/usr/bin/env python3
"""
Test script to verify health check functionality
"""

import sys
import os
sys.path.append('.')

try:
    from config import config
    from src.models.database import DatabaseManager
    from src.services.email_service import EmailService
    from src.services.payment_service import PaymentService
    from src.services.product_service import ProductService
    
    print("✅ All imports successful")
    
    # Test configuration
    print(f"✅ Config loaded: Debug={config.DEBUG}")
    
    # Test database manager
    db_manager = DatabaseManager(config)
    print("✅ DatabaseManager initialized")
    
    # Test email service
    email_service = EmailService(config)
    print("✅ EmailService initialized")
    
    # Test payment service
    payment_service = PaymentService(config, db_manager)
    print("✅ PaymentService initialized")
    
    # Test product service
    product_service = ProductService(config)
    print("✅ ProductService initialized")
    
    # Test health check methods
    print("\n--- Testing Health Check Methods ---")
    
    # Test database connection
    try:
        db_healthy = db_manager.check_connection()
        print(f"✅ Database health check: {'PASS' if db_healthy else 'FAIL'}")
    except Exception as e:
        print(f"❌ Database health check error: {e}")
    
    # Test email service connection
    try:
        email_healthy = email_service.check_connection()
        print(f"✅ Email service health check: {'PASS' if email_healthy else 'FAIL'}")
    except Exception as e:
        print(f"❌ Email service health check error: {e}")
    
    # Test payment service connection
    try:
        payment_healthy = payment_service.check_connection()
        print(f"✅ Payment service health check: {'PASS' if payment_healthy else 'FAIL'}")
    except Exception as e:
        print(f"❌ Payment service health check error: {e}")
    
    # Test product service
    try:
        products = product_service.get_available_products()
        print(f"✅ Product service: {len(products)} products available")
    except Exception as e:
        print(f"❌ Product service error: {e}")
    
    print("\n🎉 Health check test completed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
