# Project Structure

This document provides a comprehensive overview of the Gotcha Guardian Payment Server project structure and organization.

## 📁 Root Directory Structure

```
gotcha-guardian-payment-server/
├── 📁 .github/                    # GitHub configuration
│   └── 📁 workflows/              # GitHub Actions workflows
│       └── ci.yml                 # CI/CD pipeline
├── 📁 config/                     # Configuration files
│   └── products.json              # Product definitions
├── 📁 src/                        # Source code
│   ├── 📁 api/                    # API endpoints
│   ├── 📁 models/                 # Data models
│   ├── 📁 services/               # Business logic
│   ├── 📁 utils/                  # Utility functions
│   ├── 📁 validators/             # Input validation
│   └── 📁 web/                    # Web interface
├── 📁 tests/                      # Test files
│   ├── 📁 unit/                   # Unit tests
│   ├── 📁 integration/            # Integration tests
│   └── 📁 e2e/                    # End-to-end tests
├── 📁 static/                     # Static web assets
│   ├── 📁 css/                    # Stylesheets
│   ├── 📁 js/                     # JavaScript files
│   └── 📁 images/                 # Images
├── 📁 templates/                  # HTML templates
│   ├── 📁 main/                   # Main site templates
│   ├── 📁 admin/                  # Admin interface templates
│   └── 📁 emails/                 # Email templates
├── 📁 data/                       # Database files (created at runtime)
├── 📁 logs/                       # Log files (created at runtime)
├── 📁 products/                   # Product files (created at runtime)
├── 📁 backups/                    # Database backups (created at runtime)
├── 📁 temp/                       # Temporary files (created at runtime)
├── payment_server.py              # Main application entry point
├── setup.py                       # Setup and initialization script
├── run_dev.py                     # Development server runner
├── requirements.txt               # Python dependencies
├── pytest.ini                     # Test configuration
├── .env.example                   # Environment variables template
├── .gitignore                     # Git ignore rules
├── Dockerfile                     # Docker container definition
├── docker-compose.yml             # Docker Compose configuration
├── railway.json                   # Railway deployment configuration
├── README.md                      # Project documentation
├── DEPLOYMENT.md                  # Deployment guide
├── LICENSE                        # MIT License
└── PROJECT_STRUCTURE.md           # This file
```

## 📂 Detailed Directory Breakdown

### `/src/` - Source Code

The main application source code is organized into logical modules:

#### `/src/api/` - API Endpoints
```
api/
├── __init__.py                    # API package initialization
├── main.py                        # Main API routes (product catalog, purchase)
├── admin.py                       # Admin API routes (management, analytics)
├── paypal.py                      # PayPal integration endpoints
└── webhooks.py                    # Webhook handlers
```

**Purpose**: RESTful API endpoints for all external interactions
- **main.py**: Public-facing endpoints for product browsing and purchasing
- **admin.py**: Protected admin endpoints for system management
- **paypal.py**: PayPal payment processing integration
- **webhooks.py**: Webhook receivers for payment notifications

#### `/src/models/` - Data Models
```
models/
├── __init__.py                    # Models package initialization
├── database.py                    # Database connection and management
├── order.py                       # Order data model
├── product.py                     # Product data model
├── user.py                        # User data model
├── payment.py                     # Payment transaction model
├── download.py                    # Download tracking model
└── admin.py                       # Admin user model
```

**Purpose**: Data models and database operations
- **database.py**: SQLite database setup and connection management
- **order.py**: Order lifecycle management and status tracking
- **product.py**: Product information and file management
- **user.py**: Customer information and authentication
- **payment.py**: Payment transaction records and status
- **download.py**: Download attempt tracking and security
- **admin.py**: Administrative user management

#### `/src/services/` - Business Logic
```
services/
├── __init__.py                    # Services package initialization
├── payment_service.py             # Payment processing logic
├── order_service.py               # Order management logic
├── product_service.py             # Product management logic
├── email_service.py               # Email notification service
├── download_service.py            # Secure download management
├── backup_service.py              # Database backup service
└── analytics_service.py           # Analytics and reporting
```

**Purpose**: Core business logic and service layer
- **payment_service.py**: PayPal integration and payment processing
- **order_service.py**: Order creation, validation, and fulfillment
- **product_service.py**: Product catalog management and file handling
- **email_service.py**: Email notifications and templates
- **download_service.py**: Secure file delivery and access control
- **backup_service.py**: Automated backup and recovery
- **analytics_service.py**: Sales analytics and reporting

#### `/src/utils/` - Utility Functions
```
utils/
├── __init__.py                    # Utils package initialization
├── security.py                    # Security utilities and encryption
├── logging_config.py              # Logging configuration
└── helpers.py                     # General helper functions
```

**Purpose**: Shared utility functions and configurations
- **security.py**: Encryption, hashing, JWT tokens, CSRF protection
- **logging_config.py**: Centralized logging setup and formatters
- **helpers.py**: Common utilities for formatting, file operations, etc.

#### `/src/validators/` - Input Validation
```
validators/
├── __init__.py                    # Validators package initialization
├── schemas.py                     # Marshmallow validation schemas
└── utils.py                       # Validation utility functions
```

**Purpose**: Input validation and data sanitization
- **schemas.py**: Marshmallow schemas for API request/response validation
- **utils.py**: Custom validation functions and sanitization

#### `/src/web/` - Web Interface
```
web/
├── __init__.py                    # Web package initialization
├── main.py                        # Main web routes
├── admin.py                       # Admin web interface
└── forms.py                       # WTForms form definitions
```

**Purpose**: Web-based user interface (optional)
- **main.py**: Public web pages for product browsing
- **admin.py**: Administrative web interface
- **forms.py**: Form definitions and validation

### `/tests/` - Test Suite

```
tests/
├── conftest.py                    # Pytest configuration and fixtures
├── 📁 unit/                       # Unit tests
│   ├── test_models.py             # Model unit tests
│   ├── test_services.py           # Service unit tests
│   ├── test_utils.py              # Utility unit tests
│   └── test_validators.py         # Validator unit tests
├── 📁 integration/                # Integration tests
│   ├── test_api.py                # API integration tests
│   ├── test_payment.py            # Payment integration tests
│   └── test_email.py              # Email integration tests
└── 📁 e2e/                        # End-to-end tests
    ├── test_purchase_flow.py       # Complete purchase workflow
    └── test_admin_flow.py          # Admin workflow tests
```

**Purpose**: Comprehensive test coverage
- **unit/**: Fast, isolated tests for individual components
- **integration/**: Tests for component interactions
- **e2e/**: Full workflow tests simulating real user scenarios

### `/config/` - Configuration

```
config/
└── products.json                  # Product catalog configuration
```

**Purpose**: Application configuration files
- **products.json**: Defines available products, pricing, and file information

### `/static/` - Static Assets

```
static/
├── 📁 css/                        # Stylesheets
│   ├── main.css                   # Main site styles
│   └── admin.css                  # Admin interface styles
├── 📁 js/                         # JavaScript files
│   ├── main.js                    # Main site JavaScript
│   └── admin.js                   # Admin interface JavaScript
└── 📁 images/                     # Images
    ├── logo.png                   # Site logo
    └── icons/                     # Various icons
```

**Purpose**: Static web assets served directly by the web server

### `/templates/` - HTML Templates

```
templates/
├── 📁 main/                       # Main site templates
│   ├── base.html                 # Base template
│   ├── index.html                # Homepage
│   ├── products.html             # Product catalog
│   └── purchase.html             # Purchase page
├── 📁 admin/                      # Admin interface templates
│   ├── base.html                 # Admin base template
│   ├── dashboard.html            # Admin dashboard
│   ├── orders.html               # Order management
│   └── analytics.html            # Analytics dashboard
└── 📁 emails/                     # Email templates
    ├── purchase_confirmation.html # Purchase confirmation email
    ├── download_ready.html        # Download ready notification
    └── admin_notification.html    # Admin notifications
```

**Purpose**: Jinja2 templates for HTML generation

## 🗂️ Runtime Directories

These directories are created automatically during setup or runtime:

### `/data/` - Database Storage
- **payment_server.db**: Main SQLite database
- **backup_*.db**: Database backup files

### `/logs/` - Application Logs
- **app.log**: General application logs
- **error.log**: Error logs
- **security.log**: Security-related events
- **payment.log**: Payment transaction logs

### `/products/` - Product Files
- Stores the actual product files for download
- Files are referenced in `config/products.json`
- Secured with hash verification

### `/backups/` - Automated Backups
- **database/**: Database backup files
- **logs/**: Log file archives
- **config/**: Configuration backups

### `/temp/` - Temporary Files
- Temporary files during processing
- Automatically cleaned up

## 🔧 Configuration Files

### Environment Configuration
- **.env**: Environment variables (created from .env.example)
- **.env.example**: Template for environment variables

### Application Configuration
- **requirements.txt**: Python package dependencies
- **pytest.ini**: Test runner configuration
- **railway.json**: Railway deployment configuration
- **Dockerfile**: Container build instructions
- **docker-compose.yml**: Multi-container orchestration

### Development Tools
- **setup.py**: Automated setup script
- **run_dev.py**: Development server with utilities
- **.gitignore**: Git version control exclusions

## 🚀 Entry Points

### Main Application
- **payment_server.py**: Primary application entry point
  - Initializes Flask application
  - Configures routes and middleware
  - Starts the web server

### Development Tools
- **setup.py**: Initial project setup
  - Creates directories
  - Initializes database
  - Configures environment

- **run_dev.py**: Development utilities
  - Development server with hot reload
  - Test runner
  - Code formatting and linting
  - Database management

## 📋 Key Design Principles

### 1. **Separation of Concerns**
- **API Layer**: Handles HTTP requests/responses
- **Service Layer**: Contains business logic
- **Model Layer**: Manages data persistence
- **Utility Layer**: Provides shared functionality

### 2. **Security First**
- Input validation at multiple layers
- Secure file handling and downloads
- Comprehensive logging and monitoring
- CSRF protection and secure headers

### 3. **Scalability**
- Modular architecture for easy extension
- Database abstraction for future migrations
- Containerized deployment
- Comprehensive testing suite

### 4. **Maintainability**
- Clear directory structure
- Comprehensive documentation
- Automated testing and CI/CD
- Code quality tools integration

## 🔄 Data Flow

### Purchase Flow
1. **API Request** (`/src/api/main.py`) → 
2. **Validation** (`/src/validators/`) → 
3. **Service Logic** (`/src/services/`) → 
4. **Database** (`/src/models/`) → 
5. **PayPal Integration** (`/src/api/paypal.py`) → 
6. **Email Notification** (`/src/services/email_service.py`)

### Admin Flow
1. **Admin API** (`/src/api/admin.py`) → 
2. **Authentication** (`/src/utils/security.py`) → 
3. **Service Logic** (`/src/services/`) → 
4. **Database Operations** (`/src/models/`) → 
5. **Response/Analytics** (`/src/services/analytics_service.py`)

## 📚 Additional Resources

- **README.md**: Getting started guide and basic usage
- **DEPLOYMENT.md**: Comprehensive deployment instructions
- **LICENSE**: MIT License terms
- **GitHub Actions** (`.github/workflows/`): Automated CI/CD pipeline

This structure provides a solid foundation for a secure, scalable, and maintainable payment processing system while following Python and Flask best practices.