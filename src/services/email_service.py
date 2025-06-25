#!/usr/bin/env python3
"""
Email Service for Gotcha Guardian Payment Server
Handles all email operations including templates and delivery
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
import time


class EmailService:
    """Enhanced email service with templates and retry logic"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.email_config = config.get_email_config()
        
    def _get_smtp_connection(self):
        """Get SMTP connection with proper configuration"""
        try:
            if self.email_config['use_tls']:
                server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.email_config['smtp_server'], self.email_config['smtp_port'])
            
            server.login(self.email_config['username'], self.email_config['password'])
            return server
        except Exception as e:
            self.logger.error(f"Failed to connect to SMTP server: {str(e)}")
            raise
    
    def _create_message(self, to_email: str, subject: str, body: str, 
                       is_html: bool = False, attachments: Optional[List[Dict]] = None) -> MIMEMultipart:
        """Create email message with optional attachments"""
        msg = MIMEMultipart()
        msg['From'] = self.email_config['from_email']
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body
        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))
        
        # Add attachments if provided
        if attachments:
            for attachment in attachments:
                try:
                    with open(attachment['path'], 'rb') as file:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(file.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {attachment["filename"]}'
                        )
                        msg.attach(part)
                except Exception as e:
                    self.logger.error(f"Failed to attach file {attachment['path']}: {str(e)}")
        
        return msg
    
    def send_email(self, to_email: str, subject: str, body: str, 
                  is_html: bool = False, attachments: Optional[List[Dict]] = None, 
                  retry_count: int = 3) -> bool:
        """Send email with retry logic"""
        for attempt in range(retry_count):
            try:
                msg = self._create_message(to_email, subject, body, is_html, attachments)
                
                with self._get_smtp_connection() as server:
                    server.send_message(msg)
                
                self.logger.info(f"Email sent successfully to {to_email}: {subject}")
                return True
                
            except Exception as e:
                self.logger.error(f"Email send attempt {attempt + 1} failed: {str(e)}")
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self.logger.error(f"Failed to send email to {to_email} after {retry_count} attempts")
        
        return False
    
    def send_purchase_confirmation(self, email: str, product_name: str, 
                                 activation_key: str, amount: float) -> bool:
        """Send purchase confirmation email"""
        subject = f"Purchase Confirmation - {product_name}"
        
        body = self._get_purchase_confirmation_template().format(
            product_name=product_name,
            activation_key=activation_key,
            amount=amount,
            purchase_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            support_email=self.email_config['from_email']
        )
        
        return self.send_email(email, subject, body, is_html=True)
    
    def send_contact_form_notification(self, form_data: Dict[str, str]) -> bool:
        """Send contact form notification to admin"""
        subject = f"New Contact Form Submission from {form_data.get('name', 'Unknown')}"
        
        body = self._get_contact_form_template().format(
            name=form_data.get('name', 'Not provided'),
            email=form_data.get('email', 'Not provided'),
            message=form_data.get('message', 'No message'),
            submission_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        admin_email = self.email_config.get('admin_email', self.email_config['from_email'])
        return self.send_email(admin_email, subject, body, is_html=True)
    
    def send_payment_failed_notification(self, email: str, product_name: str, 
                                       error_message: str) -> bool:
        """Send payment failed notification"""
        subject = f"Payment Failed - {product_name}"
        
        body = self._get_payment_failed_template().format(
            product_name=product_name,
            error_message=error_message,
            support_email=self.email_config['from_email'],
            retry_url=self.config.get_app_config().get('base_url', 'https://your-site.com')
        )
        
        return self.send_email(email, subject, body, is_html=True)
    
    def send_download_link(self, email: str, product_name: str, 
                          download_url: str, activation_key: str) -> bool:
        """Send download link email"""
        subject = f"Download Link - {product_name}"
        
        body = self._get_download_link_template().format(
            product_name=product_name,
            download_url=download_url,
            activation_key=activation_key,
            expiry_hours=24,
            support_email=self.email_config['from_email']
        )
        
        return self.send_email(email, subject, body, is_html=True)
    
    def send_admin_alert(self, subject: str, message: str, 
                        alert_type: str = 'info') -> bool:
        """Send alert to admin"""
        admin_email = self.email_config.get('admin_email', self.email_config['from_email'])
        
        body = self._get_admin_alert_template().format(
            alert_type=alert_type.upper(),
            message=message,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            server_name=self.config.get_app_config().get('app_name', 'Gotcha Guardian')
        )
        
        return self.send_email(admin_email, f"[{alert_type.upper()}] {subject}", body, is_html=True)
    
    def test_email_connection(self) -> bool:
        """Test email connection and configuration"""
        try:
            with self._get_smtp_connection() as server:
                self.logger.info("Email connection test successful")
                return True
        except Exception as e:
            self.logger.error(f"Email connection test failed: {str(e)}")
            return False
    
    def _get_purchase_confirmation_template(self) -> str:
        """Get purchase confirmation email template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Purchase Confirmation</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .activation-key {{ background-color: #e8f5e8; padding: 15px; border-left: 4px solid #4CAF50; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Purchase Confirmation</h1>
                </div>
                <div class="content">
                    <h2>Thank you for your purchase!</h2>
                    <p>Your payment has been processed successfully. Here are your purchase details:</p>
                    
                    <ul>
                        <li><strong>Product:</strong> {product_name}</li>
                        <li><strong>Amount:</strong> ${amount:.2f}</li>
                        <li><strong>Purchase Date:</strong> {purchase_date}</li>
                    </ul>
                    
                    <div class="activation-key">
                        <h3>Your Activation Key:</h3>
                        <p style="font-family: monospace; font-size: 16px; font-weight: bold;">{activation_key}</p>
                        <p><em>Please save this activation key. You will need it to download and activate your product.</em></p>
                    </div>
                    
                    <p>To download your product, please visit our website and use your activation key.</p>
                    
                    <p>If you have any questions or need support, please contact us at {support_email}</p>
                </div>
                <div class="footer">
                    <p>Thank you for choosing Gotcha Guardian!</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_contact_form_template(self) -> str:
        """Get contact form notification template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>New Contact Form Submission</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #2196F3; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .message-box {{ background-color: #e3f2fd; padding: 15px; border-left: 4px solid #2196F3; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>New Contact Form Submission</h1>
                </div>
                <div class="content">
                    <h2>Contact Details:</h2>
                    <ul>
                        <li><strong>Name:</strong> {name}</li>
                        <li><strong>Email:</strong> {email}</li>
                        <li><strong>Submission Date:</strong> {submission_date}</li>
                    </ul>
                    
                    <div class="message-box">
                        <h3>Message:</h3>
                        <p>{message}</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_payment_failed_template(self) -> str:
        """Get payment failed notification template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Payment Failed</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f44336; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .error-box {{ background-color: #ffebee; padding: 15px; border-left: 4px solid #f44336; margin: 20px 0; }}
                .retry-button {{ background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Payment Failed</h1>
                </div>
                <div class="content">
                    <h2>We're sorry, but your payment could not be processed.</h2>
                    <p>There was an issue processing your payment for <strong>{product_name}</strong>.</p>
                    
                    <div class="error-box">
                        <h3>Error Details:</h3>
                        <p>{error_message}</p>
                    </div>
                    
                    <p>Please try again or contact our support team if the problem persists.</p>
                    
                    <a href="{retry_url}" class="retry-button">Try Again</a>
                    
                    <p>If you need assistance, please contact us at {support_email}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_download_link_template(self) -> str:
        """Get download link email template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Download Your Product</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .download-box {{ background-color: #e8f5e8; padding: 15px; border-left: 4px solid #4CAF50; margin: 20px 0; text-align: center; }}
                .download-button {{ background-color: #4CAF50; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0; font-size: 16px; }}
                .warning {{ background-color: #fff3cd; padding: 10px; border-left: 4px solid #ffc107; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Your Download is Ready!</h1>
                </div>
                <div class="content">
                    <h2>Thank you for your purchase of {product_name}!</h2>
                    
                    <div class="download-box">
                        <h3>Download Your Product</h3>
                        <a href="{download_url}" class="download-button">Download Now</a>
                        <p><strong>Activation Key:</strong> {activation_key}</p>
                    </div>
                    
                    <div class="warning">
                        <p><strong>Important:</strong> This download link will expire in {expiry_hours} hours for security reasons.</p>
                    </div>
                    
                    <h3>Installation Instructions:</h3>
                    <ol>
                        <li>Download the product using the link above</li>
                        <li>Extract the files to your desired location</li>
                        <li>Use your activation key when prompted during installation</li>
                        <li>Follow the included documentation for setup</li>
                    </ol>
                    
                    <p>If you encounter any issues or need support, please contact us at {support_email}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_admin_alert_template(self) -> str:
        """Get admin alert email template"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>System Alert</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #ff9800; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .alert-box {{ background-color: #fff3cd; padding: 15px; border-left: 4px solid #ff9800; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>System Alert - {alert_type}</h1>
                </div>
                <div class="content">
                    <h2>Alert from {server_name}</h2>
                    
                    <div class="alert-box">
                        <h3>Alert Message:</h3>
                        <p>{message}</p>
                    </div>
                    
                    <p><strong>Timestamp:</strong> {timestamp}</p>
                    
                    <p>Please review this alert and take appropriate action if necessary.</p>
                </div>
            </div>
        </body>
        </html>
        """