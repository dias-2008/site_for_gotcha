# Gotcha Guardian Payment Server

A secure, production-ready payment processing server for software sales with PayPal integration, built with Flask and designed for easy deployment on Railway.

## 🚀 Features

- **Secure Payment Processing**: PayPal integration with webhook support
- **Product Management**: Digital product delivery with activation keys
- **Email Notifications**: Automated purchase confirmations and notifications
- **Security**: CSRF protection, rate limiting, input validation, and encryption
- **Admin Dashboard**: Sales analytics and management interface
- **File Downloads**: Secure, token-based file delivery system
- **Database**: SQLite with automatic backups
- **Logging**: Comprehensive logging with JSON formatting
- **Docker Support**: Containerized deployment ready
- **Railway Deployment**: One-click deployment configuration

## 📋 Prerequisites

- Python 3.9+
- PayPal Developer Account
- SMTP Email Service (Gmail, SendGrid, etc.)
- Railway Account (for deployment)

## 🛠️ Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/gotcha-guardian-payment-server.git
cd gotcha-guardian-payment-server
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Application Settings
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here
BASE_URL=http://localhost:5000

# PayPal Configuration
PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=your-paypal-client-id
PAYPAL_CLIENT_SECRET=your-paypal-client-secret
PAYPAL_WEBHOOK_ID=your-webhook-id
PAYPAL_WEBHOOK_URL=http://localhost:5000/api/paypal/webhook

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
ADMIN_EMAIL=admin@yourdomain.com
SUPPORT_EMAIL=support@yourdomain.com

# Security
ENCRYPTION_KEY=your-encryption-key
JWT_SECRET_KEY=your-jwt-secret
```

### 5. Create Required Directories

```bash
mkdir data logs products backups temp
```

### 6. Initialize Database

```bash
python -c "from src.models.database import DatabaseManager; DatabaseManager().init_db()"
```

### 7. Run the Application

```bash
python payment_server.py
```

The server will start at `http://localhost:5000`

## 🐳 Docker Development

### Build and Run with Docker

```bash
# Build the image
docker build -t gotcha-guardian-payment-server .

# Run the container
docker run -p 5000:5000 --env-file .env gotcha-guardian-payment-server
```

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🚀 Railway Deployment

### Quick Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/yourusername/gotcha-guardian-payment-server)

### Manual Deployment

1. **Create Railway Project**
   ```bash
   railway login
   railway init
   railway link
   ```

2. **Set Environment Variables**
   ```bash
   railway variables set FLASK_ENV=production
   railway variables set SECRET_KEY=your-production-secret-key
   railway variables set PAYPAL_MODE=live
   railway variables set PAYPAL_CLIENT_ID=your-live-paypal-client-id
   railway variables set PAYPAL_CLIENT_SECRET=your-live-paypal-client-secret
   # ... add all other required variables
   ```

3. **Deploy**
   ```bash
   railway up
   ```

4. **Set Custom Domain** (Optional)
   ```bash
   railway domain
   ```

### Required Environment Variables for Production

```env
# Essential Variables
SECRET_KEY=your-production-secret-key
PAYPAL_CLIENT_ID=your-live-paypal-client-id
PAYPAL_CLIENT_SECRET=your-live-paypal-client-secret
PAYPAL_WEBHOOK_ID=your-live-webhook-id
SMTP_USERNAME=your-smtp-username
SMTP_PASSWORD=your-smtp-password
ENCRYPTION_KEY=your-encryption-key
JWT_SECRET_KEY=your-jwt-secret
FROM_EMAIL=noreply@yourdomain.com
ADMIN_EMAIL=admin@yourdomain.com
SUPPORT_EMAIL=support@yourdomain.com

# Production Settings
FLASK_ENV=production
PAYPAL_MODE=live
BASE_URL=https://your-domain.railway.app
PAYPAL_WEBHOOK_URL=https://your-domain.railway.app/api/paypal/webhook
```

## 📁 Project Structure

```
gotcha-guardian-payment-server/
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py          # Database models and manager
│   │   └── payment.py           # Payment-related models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── admin.py             # Admin dashboard routes
│   │   ├── api.py               # API endpoints
│   │   ├── main.py              # Main application routes
│   │   └── paypal.py            # PayPal integration routes
│   ├── services/
│   │   ├── __init__.py
│   │   ├── email_service.py     # Email handling
│   │   ├── payment_service.py   # Payment processing
│   │   └── product_service.py   # Product management
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── helpers.py           # Utility functions
│   │   ├── logging_config.py    # Logging configuration
│   │   └── security.py          # Security utilities
│   └── validators/
│       ├── __init__.py
│       ├── schemas.py           # Validation schemas
│       └── utils.py             # Validation utilities
├── config/
│   └── products.json            # Product definitions
├── templates/
│   ├── admin/                   # Admin templates
│   ├── emails/                  # Email templates
│   └── main/                    # Main application templates
├── static/
│   ├── css/                     # Stylesheets
│   ├── js/                      # JavaScript files
│   └── images/                  # Static images
├── data/                        # Database files
├── logs/                        # Application logs
├── products/                    # Product files
├── backups/                     # Database backups
├── temp/                        # Temporary files
├── payment_server.py            # Main application entry point
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker configuration
├── docker-compose.yml           # Docker Compose configuration
├── railway.json                 # Railway deployment configuration
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## 🔧 Configuration

### Product Configuration

Edit `config/products.json` to define your products:

```json
{
  "products": {
    "basic": {
      "name": "Your Software Basic",
      "description": "Basic version description",
      "price": 29.99,
      "currency": "USD",
      "features": ["Feature 1", "Feature 2"],
      "file": {
        "filename": "your-software-basic.zip",
        "size": 15728640,
        "hash": "sha256-hash-here"
      }
    }
  }
}
```

### PayPal Webhook Setup

1. Go to PayPal Developer Dashboard
2. Create a webhook endpoint: `https://your-domain.com/api/paypal/webhook`
3. Select these events:
   - `PAYMENT.SALE.COMPLETED`
   - `PAYMENT.SALE.DENIED`
   - `PAYMENT.SALE.REFUNDED`
4. Copy the Webhook ID to your environment variables

## 📊 API Endpoints

### Public Endpoints

- `GET /` - Main page
- `GET /api/health` - Health check
- `GET /api/products` - List products
- `POST /api/contact` - Contact form
- `POST /api/payments/create` - Create payment
- `POST /api/payments/execute` - Execute payment
- `POST /api/paypal/webhook` - PayPal webhook
- `GET /api/download/<token>` - Download files

### Admin Endpoints (Protected)

- `GET /admin` - Admin dashboard
- `GET /admin/stats` - Sales statistics
- `GET /admin/payments` - Payment history
- `POST /admin/refund` - Process refunds
- `GET /admin/logs` - View logs

## 🔒 Security Features

- **CSRF Protection**: All forms protected against CSRF attacks
- **Rate Limiting**: API endpoints have rate limits
- **Input Validation**: All inputs validated and sanitized
- **Secure Headers**: Security headers automatically added
- **Encryption**: Sensitive data encrypted at rest
- **JWT Tokens**: Secure token-based authentication
- **File Upload Security**: File type and size validation
- **SQL Injection Protection**: Parameterized queries
- **XSS Protection**: Output encoding and CSP headers

## 📝 Logging

The application uses structured JSON logging with multiple log levels:

- **Application Logs**: `logs/app.log`
- **Error Logs**: `logs/error.log`
- **Security Logs**: `logs/security.log`
- **Payment Logs**: `logs/payment.log`

Log rotation is automatic with configurable retention periods.

## 🔄 Backup and Recovery

### Automatic Backups

- Database backups run daily at 2 AM
- Backups are compressed and encrypted
- Retention period: 30 days
- Backup location: `backups/` directory

### Manual Backup

```bash
python -c "from src.models.database import DatabaseManager; DatabaseManager().create_backup()"
```

### Restore from Backup

```bash
python -c "from src.models.database import DatabaseManager; DatabaseManager().restore_backup('backup_filename.db')"
```

## 🧪 Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=src
```

### Test PayPal Integration

1. Use PayPal Sandbox credentials
2. Test with PayPal's test credit cards
3. Verify webhook delivery in PayPal Developer Dashboard

## 🐛 Troubleshooting

### Common Issues

1. **PayPal Webhook Not Working**
   - Verify webhook URL is accessible
   - Check webhook ID in environment variables
   - Ensure HTTPS in production

2. **Email Not Sending**
   - Verify SMTP credentials
   - Check firewall settings
   - Enable "Less secure app access" for Gmail

3. **Database Errors**
   - Check file permissions
   - Verify database path exists
   - Run database initialization

4. **File Download Issues**
   - Check file permissions
   - Verify product files exist
   - Check download token expiration

### Debug Mode

Enable debug mode for detailed error information:

```env
FLASK_DEBUG=True
LOG_LEVEL=DEBUG
```

## 📈 Monitoring

### Health Checks

- Endpoint: `GET /api/health`
- Checks database connectivity
- Verifies file system access
- Returns system status

### Metrics

- Payment success/failure rates
- Response times
- Error rates
- System resource usage

### Alerts

- High error rates
- Payment failures
- System resource exhaustion
- Security events

## 🔄 Updates and Maintenance

### Updating Dependencies

```bash
pip install --upgrade -r requirements.txt
```

### Database Migrations

For schema changes, create migration scripts in `src/models/migrations/`

### Log Cleanup

Old logs are automatically cleaned up weekly. Manual cleanup:

```bash
python -c "from src.utils.helpers import clean_old_files; clean_old_files('./logs', 30)"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [GitHub Wiki](https://github.com/yourusername/gotcha-guardian-payment-server/wiki)
- **Issues**: [GitHub Issues](https://github.com/yourusername/gotcha-guardian-payment-server/issues)
- **Email**: support@yourdomain.com

## 🙏 Acknowledgments

- Flask framework and community
- PayPal Developer Platform
- Railway deployment platform
- All contributors and testers

---

**Made with ❤️ for secure software sales**

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `PAYPAL_CLIENT_ID` | PayPal application client ID | Yes |
| `PAYPAL_CLIENT_SECRET` | PayPal application secret | Yes |
| `PAYPAL_MODE` | PayPal mode (sandbox/live) | Yes |
| `EMAIL_ADDRESS` | SMTP email address | Yes |
| `EMAIL_PASSWORD` | SMTP email password | Yes |
| `SMTP_SERVER` | SMTP server address | Yes |
| `SMTP_PORT` | SMTP server port | Yes |
| `SECRET_KEY` | Flask secret key | Yes |
| `DATABASE_URL` | Database connection URL | No |
| `DEBUG` | Debug mode (true/false) | No |
| `PORT` | Server port | No |

## API Endpoints

### Public Endpoints

- `GET /` - Main payment interface
- `GET /api/health` - Health check endpoint
- `POST /api/contact` - Contact form submission
- `POST /api/create-payment` - Create PayPal payment
- `POST /api/execute-payment` - Execute PayPal payment
- `GET /api/download/<activation_key>` - Download product files

### Admin Endpoints

- `GET /api/purchases` - List all purchases (admin only)

## Products

### Available Products

1. **Watcher Trial** - $2.00
   - Basic monitoring with Telegram alerts
   - Files: `gotcha_watcher.py`, `README.md`

2. **Guardian Trial** - $19.99
   - Enhanced monitoring with remote control
   - Files: `gotcha_guardian_unified.py`, `activation.py`, `README_Ultimate.md`

3. **Commander Trial** - $39.99
   - Full cyber defense suite
   - Files: `gotcha_commander_ultimate.py`, `README_COMMANDER.md`

## Database Schema

### Purchases Table
```sql
CREATE TABLE purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    product_id TEXT NOT NULL,
    amount REAL NOT NULL,
    paypal_payment_id TEXT,
    activation_key TEXT UNIQUE,
    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending',
    download_count INTEGER DEFAULT 0,
    last_download TIMESTAMP
);
```

### Activation Keys Table
```sql
CREATE TABLE activation_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL,
    activation_key TEXT UNIQUE NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Security Features

- **Input Validation**: Comprehensive request validation
- **Rate Limiting**: Protection against abuse
- **CORS Configuration**: Secure cross-origin requests
- **Environment Validation**: Required configuration checks
- **Secure File Downloads**: Activation key verification

## Development

### Project Structure
```
├── src/
│   ├── models/          # Database models
│   ├── services/        # Business logic
│   ├── utils/           # Utility functions
│   └── validators/      # Input validation
├── tests/               # Test files
├── static/              # Static assets
├── templates/           # HTML templates
├── config.py            # Configuration management
├── payment_server.py    # Main application
└── requirements.txt     # Dependencies
```

### Running Tests
```bash
pytest tests/ -v --cov=src
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

## Deployment

### Railway Deployment

The application is configured for Railway deployment with:
- `railway.json` - Railway configuration
- `Procfile` - Process definition
- `runtime.txt` - Python version specification

### Environment Setup

1. Set all required environment variables in Railway dashboard
2. Connect GitHub repository
3. Deploy automatically on push

## Support

- **Telegram**: [@Gotcha25](https://t.me/Gotcha25)
- **GitHub Issues**: [Create an issue](https://github.com/dias-2008/site_for_gotcha/issues)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Changelog

### v2.0.0 (Latest)
- Enhanced code organization
- Improved error handling
- Added comprehensive logging
- Input validation with Marshmallow
- Rate limiting protection
- Enhanced security features
- Better test coverage

### v1.0.0
- Initial release
- Basic PayPal integration
- Email notifications
- Product download system