#!/usr/bin/env python3
"""
Payment Server for Gotcha Guardian
Handles real PayPal payments, user registration, and activation key delivery
"""

import os
import json
import sqlite3
import secrets
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from flask import Flask, request, jsonify, render_template_string, send_file
from flask_cors import CORS
import paypalrestsdk
import zipfile
import tempfile

# Load environment variables from .env file for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available in production, which is fine
    pass

app = Flask(__name__)
CORS(app)

# PayPal Configuration - Using Environment Variables
paypalrestsdk.configure({
    "mode": os.getenv("PAYPAL_MODE", "sandbox"),  # "sandbox" or "live"
    "client_id": os.getenv("PAYPAL_CLIENT_ID"),
    "client_secret": os.getenv("PAYPAL_CLIENT_SECRET")
})

# Email Configuration - Using Environment Variables
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Product Configuration
PRODUCTS = {
    "watcher": {
        "name": "Watcher Trial",
        "price": 2.00,
        "description": "Basic monitoring with Telegram alerts",
        "files": ["gotcha_watcher/gotcha_watcher.py", "gotcha_watcher/README.md"]
    },
    "guardian": {
        "name": "Guardian Trial", 
        "price": 19.99,
        "description": "Enhanced monitoring with remote control",
        "files": ["gotcha_guardian_unified.py", "activation.py", "README_Ultimate.md"]
    },
    "commander": {
        "name": "Commander Trial",
        "price": 39.99, 
        "description": "Full cyber defense suite",
        "files": ["gotcha_commander/gotcha_commander_ultimate.py", "gotcha_commander/README_COMMANDER.md"]
    }
}

def init_database():
    """Initialize the database with required tables"""
    conn = sqlite3.connect('payments.db')
    cursor = conn.cursor()
    
    # Create purchases table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
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
        )
    ''')
    
    # Create activation_keys table for pre-generated keys
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activation_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            activation_key TEXT UNIQUE NOT NULL,
            used BOOLEAN DEFAULT FALSE,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def generate_activation_key():
    """Generate a unique activation key"""
    return f"GG-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"

def create_product_zip(product_id):
    """Create a ZIP file with product files"""
    if product_id not in PRODUCTS:
        return None
        
    product = PRODUCTS[product_id]
    temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    
    with zipfile.ZipFile(temp_zip.name, 'w') as zipf:
        # Add product files
        for file_path in product['files']:
            if os.path.exists(file_path):
                zipf.write(file_path, os.path.basename(file_path))
        
        # Add activation instructions
        instructions = f"""
Gotcha Guardian {product['name']} - Installation Instructions

1. Extract all files to a folder of your choice
2. Run the main application file
3. When prompted, enter your activation key
4. Follow the setup wizard

Your Activation Key: [WILL_BE_REPLACED]

Support: https://t.me/Gotcha25

Thank you for your purchase!
"""
        zipf.writestr("INSTALLATION_INSTRUCTIONS.txt", instructions)
        
        # Add a sample file if no actual files exist
        if not any(os.path.exists(f) for f in product['files']):
            sample_content = f"""
# {product['name']} - Sample File

This is a sample file for {product['name']}.
The actual product files will be included in the final release.

Product: {product['name']}
Price: ${product['price']}
Description: {product['description']}

Activation Key: [WILL_BE_REPLACED]

For support, contact: https://t.me/Gotcha25
"""
            zipf.writestr(f"{product_id}_sample.txt", sample_content)
    
    return temp_zip.name

def send_activation_email(email, product_id, activation_key, download_link):
    """Send activation email with download link"""
    try:
        product = PRODUCTS[product_id]
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = email
        msg['Subject'] = f"Your {product['name']} Activation Key"
        
        body = f"""
        <html>
        <body>
            <h2>Thank you for your purchase!</h2>
            <p>You have successfully purchased <strong>{product['name']}</strong>.</p>
            
            <h3>Your Activation Key:</h3>
            <p style="font-size: 18px; font-weight: bold; color: #007bff; background: #f8f9fa; padding: 10px; border-radius: 5px;">
                {activation_key}
            </p>
            
            <h3>Download Your Software:</h3>
            <p><a href="{download_link}" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Download Now</a></p>
            
            <h3>Installation Instructions:</h3>
            <ol>
                <li>Click the download link above</li>
                <li>Extract the ZIP file to your desired location</li>
                <li>Run the main application</li>
                <li>Enter your activation key when prompted</li>
                <li>Follow the setup wizard</li>
            </ol>
            
            <p><strong>Support:</strong> <a href="https://t.me/Gotcha25">Join our Telegram</a></p>
            
            <p>Thank you for choosing Gotcha Guardian!</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, email, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

@app.route('/')
def index():
    """Main page with payment interface"""
    return render_template_string(open('site.html').read())

@app.route('/api/create-payment', methods=['POST'])
def create_payment():
    """Create PayPal payment"""
    try:
        data = request.json
        email = data.get('email')
        product_id = data.get('product_id')
        
        if not email or not product_id or product_id not in PRODUCTS:
            return jsonify({'error': 'Invalid email or product'}), 400
            
        product = PRODUCTS[product_id]
        
        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": f"{request.url_root}api/payment-success",
                "cancel_url": f"{request.url_root}api/payment-cancel"
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": product['name'],
                        "sku": product_id,
                        "price": str(product['price']),
                        "currency": "USD",
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": str(product['price']),
                    "currency": "USD"
                },
                "description": product['description']
            }]
        })
        
        if payment.create():
            # Store pending purchase
            conn = sqlite3.connect('payments.db')
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO purchases (email, product_id, amount, paypal_payment_id, status) VALUES (?, ?, ?, ?, ?)",
                (email, product_id, product['price'], payment.id, 'pending')
            )
            conn.commit()
            conn.close()
            
            # Get approval URL
            for link in payment.links:
                if link.rel == "approval_url":
                    return jsonify({'approval_url': link.href})
        else:
            return jsonify({'error': 'Payment creation failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/execute-payment', methods=['POST'])
def execute_payment():
    """Execute PayPal payment after approval"""
    try:
        data = request.json
        payment_id = data.get('paymentID')
        payer_id = data.get('payerID')
        
        payment = paypalrestsdk.Payment.find(payment_id)
        
        if payment.execute({"payer_id": payer_id}):
            # Update purchase status and generate activation key
            conn = sqlite3.connect('payments.db')
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT email, product_id FROM purchases WHERE paypal_payment_id = ?",
                (payment_id,)
            )
            result = cursor.fetchone()
            
            if result:
                email, product_id = result
                activation_key = generate_activation_key()
                
                cursor.execute(
                    "UPDATE purchases SET status = 'completed', activation_key = ? WHERE paypal_payment_id = ?",
                    (activation_key, payment_id)
                )
                conn.commit()
                
                # Create download link
                download_link = f"{request.url_root}api/download/{activation_key}"
                
                # Send activation email
                if send_activation_email(email, product_id, activation_key, download_link):
                    conn.close()
                    return jsonify({
                        'success': True,
                        'activation_key': activation_key,
                        'download_link': download_link
                    })
                else:
                    conn.close()
                    return jsonify({'error': 'Payment successful but email sending failed'}), 500
            else:
                conn.close()
                return jsonify({'error': 'Purchase not found'}), 404
        else:
            return jsonify({'error': 'Payment execution failed'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<activation_key>')
def download_product(activation_key):
    """Download product files using activation key"""
    try:
        conn = sqlite3.connect('payments.db')
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT product_id, email, download_count FROM purchases WHERE activation_key = ? AND status = 'completed'",
            (activation_key,)
        )
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return "Invalid activation key", 404
            
        product_id, email, download_count = result
        
        # Update download count and timestamp
        cursor.execute(
            "UPDATE purchases SET download_count = download_count + 1, last_download = CURRENT_TIMESTAMP WHERE activation_key = ?",
            (activation_key,)
        )
        conn.commit()
        conn.close()
        
        # Create product ZIP
        zip_path = create_product_zip(product_id)
        if not zip_path:
            return "Product files not found", 404
            
        # Update ZIP with actual activation key
        with zipfile.ZipFile(zip_path, 'a') as zipf:
            # Read and update instructions
            instructions = f"""
Gotcha Guardian {PRODUCTS[product_id]['name']} - Installation Instructions

1. Extract all files to a folder of your choice
2. Run the main application file
3. When prompted, enter your activation key
4. Follow the setup wizard

Your Activation Key: {activation_key}

Support: https://t.me/Gotcha25

Thank you for your purchase!
"""
            zipf.writestr("INSTALLATION_INSTRUCTIONS.txt", instructions)
        
        return send_file(
            zip_path,
            as_attachment=True,
            download_name=f"gotcha_{product_id}_{activation_key}.zip",
            mimetype='application/zip'
        )
        
    except Exception as e:
        return f"Download error: {str(e)}", 500

@app.route('/api/purchases')
def list_purchases():
    """List all purchases (admin endpoint)"""
    try:
        conn = sqlite3.connect('payments.db')
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT email, product_id, amount, activation_key, purchase_date, status, download_count FROM purchases ORDER BY purchase_date DESC"
        )
        purchases = cursor.fetchall()
        conn.close()
        
        result = []
        for purchase in purchases:
            result.append({
                'email': purchase[0],
                'product': purchase[1],
                'amount': purchase[2],
                'activation_key': purchase[3],
                'purchase_date': purchase[4],
                'status': purchase[5],
                'download_count': purchase[6]
            })
            
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def validate_environment():
    """Validate that all required environment variables are set"""
    required_vars = [
        'PAYPAL_CLIENT_ID',
        'PAYPAL_CLIENT_SECRET', 
        'EMAIL_ADDRESS',
        'EMAIL_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ ERROR: Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n📝 Please set these environment variables before starting the server.")
        print("\n🚀 For Railway deployment, add these in your Railway dashboard.")
        return False
    
    print("✅ All required environment variables are set")
    return True

if __name__ == '__main__':
    if not validate_environment():
        exit(1)
        
    init_database()
    print("Payment server starting...")
    print("Database initialized")
    print("Available products:", list(PRODUCTS.keys()))
    
    # Use PORT environment variable for Railway deployment
    port = int(os.getenv('PORT', 5000))
    app.run(debug=os.getenv('DEBUG', 'False').lower() == 'true', host='0.0.0.0', port=port)
