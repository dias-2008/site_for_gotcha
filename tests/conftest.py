# Gotcha Guardian Payment Server - Test Configuration
# Pytest configuration and fixtures

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch
from flask import Flask

# Import the main application components
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import Config
from src.models.database import DatabaseManager
from src.services.email_service import EmailService
from src.services.payment_service import PaymentService
from src.services.product_service import ProductService


@pytest.fixture(scope="session")
def test_config():
    """Create a test configuration."""
    config = Config()
    
    # Override with test settings
    config.DEBUG = True
    config.TESTING = True
    config.DATABASE_URL = "sqlite:///:memory:"
    config.SECRET_KEY = "test-secret-key-for-testing-only"
    config.PAYPAL_CLIENT_ID = "test-paypal-client-id"
    config.PAYPAL_CLIENT_SECRET = "test-paypal-client-secret"
    config.PAYPAL_SANDBOX = True
    config.SMTP_SERVER = "localhost"
    config.SMTP_PORT = 587
    config.SMTP_USERNAME = "test@example.com"
    config.SMTP_PASSWORD = "test-password"
    config.FROM_EMAIL = "test@example.com"
    config.ADMIN_EMAIL = "admin@example.com"
    
    return config


@pytest.fixture(scope="function")
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="function")
def mock_database(test_config):
    """Create a mock database manager."""
    with patch('src.models.database.DatabaseManager') as mock_db:
        db_instance = Mock()
        db_instance.init_db.return_value = True
        db_instance.get_connection.return_value = Mock()
        db_instance.execute_query.return_value = True
        db_instance.fetch_one.return_value = None
        db_instance.fetch_all.return_value = []
        mock_db.return_value = db_instance
        yield db_instance


@pytest.fixture(scope="function")
def mock_email_service(test_config):
    """Create a mock email service."""
    with patch('src.services.email_service.EmailService') as mock_email:
        email_instance = Mock()
        email_instance.send_email.return_value = True
        email_instance.send_purchase_confirmation.return_value = True
        email_instance.send_admin_notification.return_value = True
        mock_email.return_value = email_instance
        yield email_instance


@pytest.fixture(scope="function")
def mock_payment_service(test_config):
    """Create a mock payment service."""
    with patch('src.services.payment_service.PaymentService') as mock_payment:
        payment_instance = Mock()
        payment_instance.create_payment.return_value = {
            'success': True,
            'payment_id': 'test-payment-id',
            'order_id': 'test-order-id',
            'approval_url': 'https://test-approval-url.com'
        }
        payment_instance.execute_payment.return_value = {
            'success': True,
            'transaction_id': 'test-transaction-id',
            'amount': '9.99',
            'currency': 'USD'
        }
        mock_payment.return_value = payment_instance
        yield payment_instance


@pytest.fixture(scope="function")
def mock_product_service(test_config, temp_dir):
    """Create a mock product service."""
    with patch('src.services.product_service.ProductService') as mock_product:
        product_instance = Mock()
        product_instance.get_products.return_value = [
            {
                'id': 'basic',
                'name': 'Basic Plan',
                'price': 9.99,
                'description': 'Basic protection plan',
                'features': ['Feature 1', 'Feature 2'],
                'featured': False
            },
            {
                'id': 'premium',
                'name': 'Premium Plan',
                'price': 19.99,
                'description': 'Premium protection plan',
                'features': ['Feature 1', 'Feature 2', 'Feature 3'],
                'featured': True
            }
        ]
        product_instance.get_product.return_value = {
            'id': 'basic',
            'name': 'Basic Plan',
            'price': 9.99,
            'description': 'Basic protection plan',
            'features': ['Feature 1', 'Feature 2'],
            'featured': False
        }
        product_instance.generate_activation_key.return_value = 'TEST-ACTIVATION-KEY-12345'
        product_instance.create_download_link.return_value = 'https://test-download-url.com/file.zip'
        mock_product.return_value = product_instance
        yield product_instance


@pytest.fixture(scope="function")
def flask_app(test_config, mock_database, mock_email_service, mock_payment_service, mock_product_service):
    """Create a Flask test application."""
    app = Flask(__name__)
    app.config.update({
        'TESTING': True,
        'SECRET_KEY': test_config.SECRET_KEY,
        'WTF_CSRF_ENABLED': False
    })
    
    with app.app_context():
        yield app


@pytest.fixture(scope="function")
def client(flask_app):
    """Create a test client."""
    return flask_app.test_client()


@pytest.fixture(scope="function")
def sample_contact_data():
    """Sample contact data for testing."""
    return {
        'name': 'John Doe',
        'email': 'john.doe@example.com',
        'country': 'United States'
    }


@pytest.fixture(scope="function")
def sample_payment_data():
    """Sample payment data for testing."""
    return {
        'product_id': 'basic',
        'contact': {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'country': 'United States'
        }
    }


@pytest.fixture(scope="function")
def sample_execution_data():
    """Sample payment execution data for testing."""
    return {
        'order_id': 'test-order-id',
        'payment_id': 'test-payment-id'
    }


# Test markers
pytest_plugins = []


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as a security test"
    )
    config.addinivalue_line(
        "markers", "payment: mark test as a payment-related test"
    )
    config.addinivalue_line(
        "markers", "email: mark test as an email-related test"
    )
    config.addinivalue_line(
        "markers", "database: mark test as a database-related test"
    )
    config.addinivalue_line(
        "markers", "api: mark test as an API test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )