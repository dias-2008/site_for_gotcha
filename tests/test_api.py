# Gotcha Guardian Payment Server - API Tests
# Test the main API endpoints

import pytest
import json
from unittest.mock import patch, Mock


class TestHealthEndpoint:
    """Test the health check endpoint."""
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_health_endpoint_success(self, client, mock_database, mock_email_service, mock_payment_service):
        """Test health endpoint returns success when all services are healthy."""
        # Mock all services as healthy
        mock_database.get_connection.return_value = Mock()
        mock_email_service.test_connection.return_value = True
        mock_payment_service.test_connection.return_value = True
        
        with patch('payment_server.db_manager', mock_database), \
             patch('payment_server.email_service', mock_email_service), \
             patch('payment_server.payment_service', mock_payment_service):
            
            response = client.get('/api/health')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'status' in data
            assert 'timestamp' in data
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_health_endpoint_database_failure(self, client, mock_database, mock_email_service, mock_payment_service):
        """Test health endpoint when database is unhealthy."""
        # Mock database as unhealthy
        mock_database.get_connection.side_effect = Exception("Database connection failed")
        mock_email_service.test_connection.return_value = True
        mock_payment_service.test_connection.return_value = True
        
        with patch('payment_server.db_manager', mock_database), \
             patch('payment_server.email_service', mock_email_service), \
             patch('payment_server.payment_service', mock_payment_service):
            
            response = client.get('/api/health')
            
            assert response.status_code == 503
            data = json.loads(response.data)
            assert data['success'] is False


class TestProductsEndpoint:
    """Test the products endpoint."""
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_get_products_success(self, client, mock_product_service):
        """Test getting products successfully."""
        with patch('payment_server.product_service', mock_product_service):
            response = client.get('/api/products')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'products' in data
            assert len(data['products']) == 2
            assert data['products'][0]['id'] == 'basic'
            assert data['products'][1]['id'] == 'premium'
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_get_products_service_error(self, client, mock_product_service):
        """Test getting products when service fails."""
        mock_product_service.get_products.side_effect = Exception("Service error")
        
        with patch('payment_server.product_service', mock_product_service):
            response = client.get('/api/products')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert data['success'] is False


class TestPaymentEndpoints:
    """Test payment-related endpoints."""
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.payment
    def test_create_payment_success(self, client, sample_payment_data, mock_payment_service, mock_product_service, mock_database):
        """Test creating a payment successfully."""
        with patch('payment_server.payment_service', mock_payment_service), \
             patch('payment_server.product_service', mock_product_service), \
             patch('payment_server.db_manager', mock_database):
            
            response = client.post('/api/create-payment',
                                 data=json.dumps(sample_payment_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'payment_id' in data
            assert 'order_id' in data
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.payment
    def test_create_payment_invalid_data(self, client):
        """Test creating payment with invalid data."""
        invalid_data = {
            'product_id': '',  # Invalid empty product ID
            'contact': {
                'name': '',  # Invalid empty name
                'email': 'invalid-email',  # Invalid email format
                'country': ''
            }
        }
        
        response = client.post('/api/create-payment',
                             data=json.dumps(invalid_data),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'error' in data
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.payment
    def test_execute_payment_success(self, client, sample_execution_data, mock_payment_service, mock_email_service, mock_database):
        """Test executing a payment successfully."""
        # Mock database to return order data
        mock_database.fetch_one.return_value = {
            'id': 1,
            'order_id': 'test-order-id',
            'product_id': 'basic',
            'customer_name': 'John Doe',
            'customer_email': 'john.doe@example.com',
            'amount': 9.99,
            'status': 'pending'
        }
        
        with patch('payment_server.payment_service', mock_payment_service), \
             patch('payment_server.email_service', mock_email_service), \
             patch('payment_server.db_manager', mock_database):
            
            response = client.post('/api/execute-payment',
                                 data=json.dumps(sample_execution_data),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'transaction_id' in data
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.payment
    def test_execute_payment_not_found(self, client, sample_execution_data, mock_database):
        """Test executing payment when order is not found."""
        # Mock database to return no order
        mock_database.fetch_one.return_value = None
        
        with patch('payment_server.db_manager', mock_database):
            response = client.post('/api/execute-payment',
                                 data=json.dumps(sample_execution_data),
                                 content_type='application/json')
            
            assert response.status_code == 404
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'not found' in data['error'].lower()


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.security
    def test_rate_limiting_health_endpoint(self, client):
        """Test rate limiting on health endpoint."""
        # Make multiple requests to trigger rate limiting
        # Note: This test assumes rate limiting is configured
        responses = []
        for i in range(15):  # Assuming limit is 10 per minute
            response = client.get('/api/health')
            responses.append(response.status_code)
        
        # Check if any requests were rate limited (429)
        # This test might need adjustment based on actual rate limiting config
        assert any(status == 429 for status in responses[-5:])  # Last 5 should include 429


class TestErrorHandling:
    """Test error handling across endpoints."""
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_404_error(self, client):
        """Test 404 error for non-existent endpoint."""
        response = client.get('/api/non-existent-endpoint')
        assert response.status_code == 404
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_method_not_allowed(self, client):
        """Test 405 error for wrong HTTP method."""
        response = client.delete('/api/health')  # Health endpoint only supports GET
        assert response.status_code == 405
    
    @pytest.mark.unit
    @pytest.mark.api
    def test_invalid_json(self, client):
        """Test handling of invalid JSON data."""
        response = client.post('/api/create-payment',
                             data='invalid json',
                             content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False


class TestCORS:
    """Test CORS functionality."""
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.security
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.get('/api/health')
        
        # Check for CORS headers
        assert 'Access-Control-Allow-Origin' in response.headers
        assert 'Access-Control-Allow-Methods' in response.headers
        assert 'Access-Control-Allow-Headers' in response.headers
    
    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.security
    def test_preflight_request(self, client):
        """Test CORS preflight request."""
        response = client.options('/api/create-payment',
                                headers={
                                    'Origin': 'https://example.com',
                                    'Access-Control-Request-Method': 'POST',
                                    'Access-Control-Request-Headers': 'Content-Type'
                                })
        
        assert response.status_code == 200
        assert 'Access-Control-Allow-Origin' in response.headers
        assert 'Access-Control-Allow-Methods' in response.headers