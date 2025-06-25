# API Documentation

This document provides comprehensive documentation for the Gotcha Guardian Payment Server API endpoints.

## 📋 Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Public API Endpoints](#public-api-endpoints)
- [Admin API Endpoints](#admin-api-endpoints)
- [PayPal Integration](#paypal-integration)
- [Webhook Endpoints](#webhook-endpoints)
- [Response Formats](#response-formats)
- [Status Codes](#status-codes)
- [Examples](#examples)

## 🌐 Overview

### Base URL
```
Production: https://your-domain.com/api
Staging: https://staging-your-domain.com/api
Local: http://localhost:5000/api
```

### API Version
- **Current Version**: v1
- **Content-Type**: `application/json`
- **Character Encoding**: UTF-8

### Request Headers
```http
Content-Type: application/json
Accept: application/json
User-Agent: YourApp/1.0
```

## 🔐 Authentication

### Public Endpoints
Most endpoints are public and don't require authentication.

### Admin Endpoints
Admin endpoints require API key authentication:

```http
Authorization: Bearer YOUR_API_KEY
```

### CSRF Protection
For web interface requests, include CSRF token:

```http
X-CSRFToken: YOUR_CSRF_TOKEN
```

## ❌ Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "issue": "Invalid email format"
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_123456789"
  }
}
```

### Common Error Codes
- `VALIDATION_ERROR`: Input validation failed
- `PAYMENT_ERROR`: Payment processing failed
- `NOT_FOUND`: Resource not found
- `UNAUTHORIZED`: Authentication required
- `FORBIDDEN`: Insufficient permissions
- `RATE_LIMITED`: Too many requests
- `SERVER_ERROR`: Internal server error

## 🚦 Rate Limiting

### Default Limits
- **Public API**: 100 requests per minute per IP
- **Admin API**: 1000 requests per minute per API key
- **Payment endpoints**: 10 requests per minute per IP

### Rate Limit Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248600
```

## 🌍 Public API Endpoints

### Health Check

#### `GET /health`
Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "uptime": 3600
}
```

### Product Catalog

#### `GET /products`
Retrieve all available products.

**Query Parameters:**
- `category` (optional): Filter by category
- `active_only` (optional): Show only active products (default: true)

**Response:**
```json
{
  "products": [
    {
      "id": "basic",
      "name": "Gotcha Guardian Basic",
      "description": "Essential protection features",
      "price": 29.99,
      "currency": "USD",
      "category": "software",
      "features": [
        "Real-time monitoring",
        "Basic alerts"
      ],
      "system_requirements": {
        "os": "Windows 10+",
        "ram": "4GB",
        "storage": "100MB"
      },
      "active": true
    }
  ],
  "total": 1,
  "currency": "USD"
}
```

#### `GET /products/{product_id}`
Retrieve specific product details.

**Path Parameters:**
- `product_id`: Product identifier

**Response:**
```json
{
  "id": "basic",
  "name": "Gotcha Guardian Basic",
  "description": "Essential protection features",
  "price": 29.99,
  "currency": "USD",
  "category": "software",
  "features": [
    "Real-time monitoring",
    "Basic alerts"
  ],
  "system_requirements": {
    "os": "Windows 10+",
    "ram": "4GB",
    "storage": "100MB"
  },
  "file": {
    "size": 52428800,
    "version": "1.0.0"
  },
  "licensing": {
    "type": "single_user",
    "duration": "lifetime"
  },
  "active": true
}
```

### Order Management

#### `POST /orders`
Create a new order.

**Request Body:**
```json
{
  "product_id": "basic",
  "customer": {
    "email": "customer@example.com",
    "name": "John Doe",
    "phone": "+1234567890"
  },
  "billing_address": {
    "street": "123 Main St",
    "city": "Anytown",
    "state": "CA",
    "zip": "12345",
    "country": "US"
  }
}
```

**Response:**
```json
{
  "order_id": "ord_123456789",
  "status": "pending",
  "product": {
    "id": "basic",
    "name": "Gotcha Guardian Basic",
    "price": 29.99
  },
  "customer": {
    "email": "customer@example.com",
    "name": "John Doe"
  },
  "total_amount": 29.99,
  "currency": "USD",
  "payment_url": "https://paypal.com/checkout/...",
  "expires_at": "2024-01-15T11:30:00Z",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### `GET /orders/{order_id}`
Retrieve order details.

**Path Parameters:**
- `order_id`: Order identifier

**Query Parameters:**
- `email`: Customer email (required for verification)

**Response:**
```json
{
  "order_id": "ord_123456789",
  "status": "completed",
  "product": {
    "id": "basic",
    "name": "Gotcha Guardian Basic",
    "price": 29.99
  },
  "customer": {
    "email": "customer@example.com",
    "name": "John Doe"
  },
  "payment": {
    "method": "paypal",
    "transaction_id": "txn_987654321",
    "status": "completed",
    "paid_at": "2024-01-15T10:35:00Z"
  },
  "download": {
    "available": true,
    "expires_at": "2024-01-22T10:35:00Z",
    "download_count": 0,
    "max_downloads": 3
  },
  "total_amount": 29.99,
  "currency": "USD",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:00Z"
}
```

### Download Management

#### `POST /downloads/request`
Request a download link.

**Request Body:**
```json
{
  "order_id": "ord_123456789",
  "email": "customer@example.com"
}
```

**Response:**
```json
{
  "download_token": "dl_abcdef123456",
  "download_url": "/api/downloads/dl_abcdef123456",
  "expires_at": "2024-01-15T11:00:00Z",
  "file_info": {
    "name": "gotcha-guardian-basic-v1.0.0.zip",
    "size": 52428800,
    "hash": "sha256:abc123..."
  },
  "remaining_downloads": 2
}
```

#### `GET /downloads/{download_token}`
Download the product file.

**Path Parameters:**
- `download_token`: Secure download token

**Response:**
- **Success**: Binary file download
- **Error**: JSON error response

### Activation Management

#### `POST /activation/validate`
Validate an activation key.

**Request Body:**
```json
{
  "activation_key": "ABCD-EFGH-IJKL-MNOP",
  "product_id": "basic",
  "hardware_id": "hw_123456789"
}
```

**Response:**
```json
{
  "valid": true,
  "product": {
    "id": "basic",
    "name": "Gotcha Guardian Basic",
    "version": "1.0.0"
  },
  "license": {
    "type": "single_user",
    "expires_at": null,
    "max_activations": 1,
    "current_activations": 1
  },
  "activated_at": "2024-01-15T10:35:00Z"
}
```

## 🔧 Admin API Endpoints

### Authentication Required
All admin endpoints require API key authentication.

### Dashboard

#### `GET /admin/dashboard`
Retrieve dashboard statistics.

**Response:**
```json
{
  "stats": {
    "total_orders": 150,
    "total_revenue": 4497.50,
    "pending_orders": 5,
    "completed_orders": 145,
    "failed_orders": 0
  },
  "recent_orders": [
    {
      "order_id": "ord_123456789",
      "customer_email": "customer@example.com",
      "product_name": "Gotcha Guardian Basic",
      "amount": 29.99,
      "status": "completed",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "revenue_chart": {
    "daily": [
      {"date": "2024-01-15", "revenue": 89.97},
      {"date": "2024-01-14", "revenue": 149.95}
    ]
  }
}
```

### Order Management

#### `GET /admin/orders`
Retrieve all orders with filtering.

**Query Parameters:**
- `status`: Filter by status (pending, completed, failed, cancelled)
- `product_id`: Filter by product
- `start_date`: Start date filter (ISO 8601)
- `end_date`: End date filter (ISO 8601)
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 50, max: 100)

**Response:**
```json
{
  "orders": [
    {
      "order_id": "ord_123456789",
      "status": "completed",
      "customer": {
        "email": "customer@example.com",
        "name": "John Doe"
      },
      "product": {
        "id": "basic",
        "name": "Gotcha Guardian Basic"
      },
      "amount": 29.99,
      "currency": "USD",
      "payment_method": "paypal",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:35:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 150,
    "pages": 3
  }
}
```

#### `PUT /admin/orders/{order_id}`
Update order status.

**Path Parameters:**
- `order_id`: Order identifier

**Request Body:**
```json
{
  "status": "cancelled",
  "reason": "Customer request"
}
```

**Response:**
```json
{
  "order_id": "ord_123456789",
  "status": "cancelled",
  "updated_at": "2024-01-15T11:00:00Z",
  "reason": "Customer request"
}
```

### Analytics

#### `GET /admin/analytics/revenue`
Retrieve revenue analytics.

**Query Parameters:**
- `period`: Time period (day, week, month, year)
- `start_date`: Start date (ISO 8601)
- `end_date`: End date (ISO 8601)
- `product_id`: Filter by product (optional)

**Response:**
```json
{
  "period": "month",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "total_revenue": 4497.50,
  "total_orders": 150,
  "average_order_value": 29.98,
  "data": [
    {
      "date": "2024-01-01",
      "revenue": 149.95,
      "orders": 5
    },
    {
      "date": "2024-01-02",
      "revenue": 89.97,
      "orders": 3
    }
  ],
  "products": [
    {
      "product_id": "basic",
      "product_name": "Gotcha Guardian Basic",
      "revenue": 2999.00,
      "orders": 100,
      "percentage": 66.7
    }
  ]
}
```

#### `GET /admin/analytics/customers`
Retrieve customer analytics.

**Response:**
```json
{
  "total_customers": 145,
  "new_customers_this_month": 23,
  "repeat_customers": 5,
  "top_customers": [
    {
      "email": "customer@example.com",
      "total_orders": 3,
      "total_spent": 89.97,
      "last_order": "2024-01-15T10:30:00Z"
    }
  ],
  "geographic_distribution": [
    {
      "country": "US",
      "customers": 120,
      "percentage": 82.8
    },
    {
      "country": "CA",
      "customers": 15,
      "percentage": 10.3
    }
  ]
}
```

### System Management

#### `GET /admin/system/status`
Retrieve system status.

**Response:**
```json
{
  "status": "healthy",
  "uptime": 86400,
  "version": "1.0.0",
  "database": {
    "status": "connected",
    "size": "15.2MB",
    "last_backup": "2024-01-15T06:00:00Z"
  },
  "storage": {
    "total_space": "100GB",
    "used_space": "2.3GB",
    "available_space": "97.7GB"
  },
  "services": {
    "paypal": "connected",
    "email": "connected",
    "logging": "active"
  }
}
```

#### `POST /admin/system/backup`
Create system backup.

**Response:**
```json
{
  "backup_id": "backup_20240115_103000",
  "status": "completed",
  "file_path": "/backups/backup_20240115_103000.zip",
  "size": 15728640,
  "created_at": "2024-01-15T10:30:00Z"
}
```

## 💳 PayPal Integration

### Payment Processing

#### `POST /paypal/create-payment`
Create PayPal payment (internal use).

#### `POST /paypal/execute-payment`
Execute PayPal payment (internal use).

#### `POST /paypal/webhook`
PayPal webhook endpoint for payment notifications.

**Request Body:** PayPal webhook payload

**Response:**
```json
{
  "status": "received",
  "event_type": "PAYMENT.CAPTURE.COMPLETED",
  "processed_at": "2024-01-15T10:35:00Z"
}
```

## 🔗 Webhook Endpoints

### PayPal Webhooks

#### `POST /webhooks/paypal`
Handle PayPal payment notifications.

**Supported Events:**
- `PAYMENT.CAPTURE.COMPLETED`
- `PAYMENT.CAPTURE.DENIED`
- `PAYMENT.CAPTURE.PENDING`
- `PAYMENT.CAPTURE.REFUNDED`

### Custom Webhooks

#### `POST /webhooks/order-status`
Notify external systems of order status changes.

## 📊 Response Formats

### Success Response
```json
{
  "data": { /* response data */ },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_123456789",
    "version": "1.0.0"
  }
}
```

### Error Response
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": { /* additional error details */ },
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_123456789"
  }
}
```

### Pagination
```json
{
  "data": [ /* array of items */ ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 150,
    "pages": 3,
    "has_next": true,
    "has_prev": false
  }
}
```

## 📋 Status Codes

### HTTP Status Codes
- **200 OK**: Request successful
- **201 Created**: Resource created successfully
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource conflict
- **422 Unprocessable Entity**: Validation error
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error
- **503 Service Unavailable**: Service temporarily unavailable

### Order Status Codes
- `pending`: Order created, awaiting payment
- `processing`: Payment received, processing order
- `completed`: Order fulfilled, download available
- `cancelled`: Order cancelled
- `failed`: Order failed (payment or processing error)
- `refunded`: Order refunded

### Payment Status Codes
- `pending`: Payment initiated
- `processing`: Payment being processed
- `completed`: Payment successful
- `failed`: Payment failed
- `cancelled`: Payment cancelled
- `refunded`: Payment refunded

## 💡 Examples

### Complete Purchase Flow

1. **Get Products**
```bash
curl -X GET "https://api.example.com/products" \
  -H "Accept: application/json"
```

2. **Create Order**
```bash
curl -X POST "https://api.example.com/orders" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "basic",
    "customer": {
      "email": "customer@example.com",
      "name": "John Doe"
    }
  }'
```

3. **Check Order Status**
```bash
curl -X GET "https://api.example.com/orders/ord_123456789?email=customer@example.com" \
  -H "Accept: application/json"
```

4. **Request Download**
```bash
curl -X POST "https://api.example.com/downloads/request" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ord_123456789",
    "email": "customer@example.com"
  }'
```

5. **Download File**
```bash
curl -X GET "https://api.example.com/downloads/dl_abcdef123456" \
  -o "gotcha-guardian-basic.zip"
```

### Admin Operations

1. **Get Dashboard Stats**
```bash
curl -X GET "https://api.example.com/admin/dashboard" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Accept: application/json"
```

2. **Get Revenue Analytics**
```bash
curl -X GET "https://api.example.com/admin/analytics/revenue?period=month" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Accept: application/json"
```

3. **Update Order Status**
```bash
curl -X PUT "https://api.example.com/admin/orders/ord_123456789" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "cancelled",
    "reason": "Customer request"
  }'
```

## 🔒 Security Considerations

### API Security
- All endpoints use HTTPS in production
- Rate limiting prevents abuse
- Input validation on all endpoints
- CSRF protection for web interface
- Secure headers implemented

### Data Protection
- Customer data is encrypted at rest
- PII is masked in logs
- Download tokens expire automatically
- Activation keys are securely generated

### Payment Security
- PayPal handles all payment processing
- No credit card data stored
- Webhook signatures verified
- Transaction logs maintained

For additional security information, please refer to our security documentation.