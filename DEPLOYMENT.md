# Deployment Guide

This guide covers various deployment options for the Gotcha Guardian Payment Server.

## 🚀 Railway Deployment (Recommended)

Railway provides the easiest deployment option with automatic scaling and built-in monitoring.

### Prerequisites

- Railway account ([railway.app](https://railway.app))
- GitHub repository with your code
- PayPal Developer account
- SMTP email service

### Step 1: Prepare Your Repository

1. **Fork or clone this repository**
2. **Update configuration files**:
   - Edit `config/products.json` with your product information
   - Update `railway.json` with your repository URL
   - Modify `README.md` with your project details

### Step 2: Deploy to Railway

#### Option A: One-Click Deploy

1. Click the "Deploy on Railway" button in the README
2. Connect your GitHub account
3. Select your forked repository
4. Railway will automatically detect the configuration

#### Option B: Manual Deploy

1. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   ```

2. **Login and initialize**:
   ```bash
   railway login
   railway init
   railway link
   ```

3. **Deploy**:
   ```bash
   railway up
   ```

### Step 3: Configure Environment Variables

Set these essential variables in Railway dashboard:

```env
# Application
SECRET_KEY=your-production-secret-key-here
FLASK_ENV=production
BASE_URL=https://your-app.railway.app

# PayPal (Production)
PAYPAL_MODE=live
PAYPAL_CLIENT_ID=your-live-paypal-client-id
PAYPAL_CLIENT_SECRET=your-live-paypal-client-secret
PAYPAL_WEBHOOK_ID=your-live-webhook-id
PAYPAL_WEBHOOK_URL=https://your-app.railway.app/api/paypal/webhook

# Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@yourdomain.com
ADMIN_EMAIL=admin@yourdomain.com
SUPPORT_EMAIL=support@yourdomain.com

# Security
ENCRYPTION_KEY=your-32-character-encryption-key
JWT_SECRET_KEY=your-jwt-secret-key
```

### Step 4: Set Up Custom Domain (Optional)

1. Go to Railway dashboard
2. Navigate to your project
3. Click "Settings" → "Domains"
4. Add your custom domain
5. Update DNS records as instructed
6. Update `BASE_URL` and `PAYPAL_WEBHOOK_URL` environment variables

### Step 5: Configure PayPal Webhooks

1. Go to [PayPal Developer Dashboard](https://developer.paypal.com)
2. Navigate to your app
3. Add webhook endpoint: `https://your-domain.com/api/paypal/webhook`
4. Select events:
   - `PAYMENT.SALE.COMPLETED`
   - `PAYMENT.SALE.DENIED`
   - `PAYMENT.SALE.REFUNDED`
5. Copy the Webhook ID to Railway environment variables

## 🐳 Docker Deployment

### Local Docker

1. **Build the image**:
   ```bash
   docker build -t gotcha-guardian-payment-server .
   ```

2. **Run with environment file**:
   ```bash
   docker run -p 5000:5000 --env-file .env gotcha-guardian-payment-server
   ```

3. **Run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

### Production Docker

1. **Build production image**:
   ```bash
   docker build --target production -t gotcha-guardian-payment-server:latest .
   ```

2. **Run with production settings**:
   ```bash
   docker run -d \
     --name payment-server \
     -p 80:5000 \
     --restart unless-stopped \
     --env-file .env.production \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/logs:/app/logs \
     -v $(pwd)/backups:/app/backups \
     gotcha-guardian-payment-server:latest
   ```

### Docker Compose Production

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  payment-server:
    build:
      context: .
      target: production
    ports:
      - "80:5000"
    environment:
      - FLASK_ENV=production
    env_file:
      - .env.production
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./backups:/app/backups
      - ./products:/app/products
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - payment-server
    restart: unless-stopped

  redis:
    image: redis:alpine
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

Deploy:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## ☁️ Cloud Platform Deployment

### Heroku

1. **Install Heroku CLI**
2. **Create Heroku app**:
   ```bash
   heroku create your-app-name
   ```

3. **Set environment variables**:
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set PAYPAL_CLIENT_ID=your-paypal-client-id
   # ... set all required variables
   ```

4. **Deploy**:
   ```bash
   git push heroku main
   ```

### DigitalOcean App Platform

1. **Create app spec** (`app.yaml`):
   ```yaml
   name: gotcha-guardian-payment-server
   services:
   - name: web
     source_dir: /
     github:
       repo: yourusername/gotcha-guardian-payment-server
       branch: main
     run_command: gunicorn --bind 0.0.0.0:$PORT payment_server:app
     environment_slug: python
     instance_count: 1
     instance_size_slug: basic-xxs
     envs:
     - key: FLASK_ENV
       value: production
     - key: SECRET_KEY
       value: your-secret-key
       type: SECRET
   ```

2. **Deploy**:
   ```bash
   doctl apps create --spec app.yaml
   ```

### AWS Elastic Beanstalk

1. **Install EB CLI**
2. **Initialize**:
   ```bash
   eb init
   ```

3. **Create environment**:
   ```bash
   eb create production
   ```

4. **Set environment variables**:
   ```bash
   eb setenv SECRET_KEY=your-secret-key PAYPAL_CLIENT_ID=your-paypal-client-id
   ```

5. **Deploy**:
   ```bash
   eb deploy
   ```

## 🖥️ VPS Deployment

### Ubuntu/Debian Server

1. **Update system**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install dependencies**:
   ```bash
   sudo apt install python3 python3-pip python3-venv nginx supervisor -y
   ```

3. **Create user**:
   ```bash
   sudo useradd -m -s /bin/bash paymentserver
   sudo su - paymentserver
   ```

4. **Clone repository**:
   ```bash
   git clone https://github.com/yourusername/gotcha-guardian-payment-server.git
   cd gotcha-guardian-payment-server
   ```

5. **Set up virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

6. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

7. **Create directories**:
   ```bash
   mkdir -p data logs products backups temp
   ```

8. **Initialize database**:
   ```bash
   python -c "from src.models.database import DatabaseManager; DatabaseManager().init_db()"
   ```

9. **Configure Supervisor** (`/etc/supervisor/conf.d/payment-server.conf`):
   ```ini
   [program:payment-server]
   command=/home/paymentserver/gotcha-guardian-payment-server/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 payment_server:app
   directory=/home/paymentserver/gotcha-guardian-payment-server
   user=paymentserver
   autostart=true
   autorestart=true
   redirect_stderr=true
   stdout_logfile=/var/log/payment-server.log
   environment=PATH="/home/paymentserver/gotcha-guardian-payment-server/venv/bin"
   ```

10. **Configure Nginx** (`/etc/nginx/sites-available/payment-server`):
    ```nginx
    server {
        listen 80;
        server_name your-domain.com;
        
        location / {
            proxy_pass http://127.0.0.1:5000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        location /static {
            alias /home/paymentserver/gotcha-guardian-payment-server/static;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    ```

11. **Enable and start services**:
    ```bash
    sudo ln -s /etc/nginx/sites-available/payment-server /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl reload nginx
    sudo supervisorctl reread
    sudo supervisorctl update
    sudo supervisorctl start payment-server
    ```

12. **Set up SSL with Let's Encrypt**:
    ```bash
    sudo apt install certbot python3-certbot-nginx -y
    sudo certbot --nginx -d your-domain.com
    ```

## 🔧 Post-Deployment Configuration

### 1. Verify Deployment

- Check health endpoint: `https://your-domain.com/api/health`
- Test product listing: `https://your-domain.com/api/products`
- Verify admin access: `https://your-domain.com/admin`

### 2. Set Up Monitoring

#### Application Monitoring
- Configure log aggregation
- Set up error tracking (Sentry)
- Monitor performance metrics

#### Infrastructure Monitoring
- CPU and memory usage
- Disk space
- Network connectivity
- SSL certificate expiration

### 3. Configure Backups

#### Database Backups
```bash
# Add to crontab
0 2 * * * /path/to/venv/bin/python -c "from src.models.database import DatabaseManager; DatabaseManager().create_backup()"
```

#### File Backups
```bash
# Backup script
#!/bin/bash
tar -czf /backups/files-$(date +%Y%m%d).tar.gz /app/products /app/data
find /backups -name "files-*.tar.gz" -mtime +30 -delete
```

### 4. Security Hardening

#### Firewall Configuration
```bash
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

#### Fail2Ban Setup
```bash
sudo apt install fail2ban -y
# Configure /etc/fail2ban/jail.local
```

#### Regular Updates
```bash
# Add to crontab
0 3 * * 0 apt update && apt upgrade -y
```

## 🚨 Troubleshooting

### Common Issues

1. **Application won't start**
   - Check environment variables
   - Verify database permissions
   - Check log files

2. **PayPal webhooks failing**
   - Verify webhook URL accessibility
   - Check SSL certificate
   - Validate webhook signature

3. **Email not sending**
   - Test SMTP credentials
   - Check firewall rules
   - Verify DNS settings

4. **High memory usage**
   - Reduce worker count
   - Enable log rotation
   - Clear temporary files

### Debug Commands

```bash
# Check application logs
tail -f logs/app.log

# Test database connection
python -c "from src.models.database import DatabaseManager; print(DatabaseManager().test_connection())"

# Verify PayPal configuration
python -c "from src.services.payment_service import PaymentService; print(PaymentService().test_connection())"

# Test email configuration
python -c "from src.services.email_service import EmailService; EmailService().test_connection()"
```

## 📊 Performance Optimization

### Application Level
- Enable caching
- Optimize database queries
- Use connection pooling
- Implement rate limiting

### Infrastructure Level
- Use CDN for static files
- Enable gzip compression
- Configure load balancing
- Implement auto-scaling

### Database Optimization
- Regular VACUUM operations
- Index optimization
- Query performance monitoring
- Connection pooling

## 🔄 Maintenance

### Regular Tasks
- Monitor application logs
- Check system resources
- Verify backup integrity
- Update dependencies
- Review security logs

### Monthly Tasks
- Rotate log files
- Clean temporary files
- Update SSL certificates
- Review performance metrics
- Test disaster recovery

### Quarterly Tasks
- Security audit
- Dependency updates
- Performance review
- Backup strategy review
- Documentation updates

---

For additional support, please refer to the [main README](README.md) or create an issue in the GitHub repository.