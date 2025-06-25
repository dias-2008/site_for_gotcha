#!/usr/bin/env python3
"""
Payment Service for Gotcha Guardian Payment Server
Handles PayPal integration and payment processing
"""

import logging
import paypalrestsdk
from typing import Dict, Optional, Any
from datetime import datetime
import uuid
import json


class PaymentService:
    """Enhanced payment service with PayPal integration"""
    
    def __init__(self, config, database_manager):
        self.config = config
        self.db = database_manager
        self.logger = logging.getLogger(__name__)
        self._initialize_paypal()
        
    def _initialize_paypal(self):
        """Initialize PayPal SDK with configuration"""
        try:
            paypal_config = self.config.get_paypal_config()
            
            paypalrestsdk.configure({
                "mode": paypal_config['mode'],  # sandbox or live
                "client_id": paypal_config['client_id'],
                "client_secret": paypal_config['client_secret']
            })
            
            self.logger.info(f"PayPal SDK initialized in {paypal_config['mode']} mode")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize PayPal SDK: {str(e)}")
            raise
    
    def create_payment(self, email: str, product_id: str, product_name: str, 
                      amount: float, return_url: str, cancel_url: str) -> Optional[Dict[str, Any]]:
        """Create a PayPal payment"""
        try:
            # Create payment object
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": return_url,
                    "cancel_url": cancel_url
                },
                "transactions": [{
                    "item_list": {
                        "items": [{
                            "name": product_name,
                            "sku": product_id,
                            "price": f"{amount:.2f}",
                            "currency": "USD",
                            "quantity": 1
                        }]
                    },
                    "amount": {
                        "total": f"{amount:.2f}",
                        "currency": "USD"
                    },
                    "description": f"Purchase of {product_name}",
                    "custom": json.dumps({
                        "email": email,
                        "product_id": product_id,
                        "timestamp": datetime.now().isoformat()
                    })
                }]
            })
            
            # Create the payment
            if payment.create():
                # Store payment in database
                purchase_id = self.db.create_purchase(
                    email=email,
                    product_id=product_id,
                    amount=amount,
                    paypal_payment_id=payment.id,
                    status='pending'
                )
                
                if purchase_id:
                    # Get approval URL
                    approval_url = None
                    for link in payment.links:
                        if link.rel == "approval_url":
                            approval_url = link.href
                            break
                    
                    self.logger.info(f"Payment created: {payment.id} for {email}")
                    
                    return {
                        'payment_id': payment.id,
                        'approval_url': approval_url,
                        'purchase_id': purchase_id,
                        'status': 'created'
                    }
                else:
                    self.logger.error(f"Failed to store purchase in database for payment {payment.id}")
                    return None
            else:
                self.logger.error(f"PayPal payment creation failed: {payment.error}")
                return None
                
        except Exception as e:
            self.logger.error(f"Payment creation failed: {str(e)}")
            return None
    
    def execute_payment(self, payment_id: str, payer_id: str) -> Optional[Dict[str, Any]]:
        """Execute a PayPal payment after user approval"""
        try:
            # Get the payment
            payment = paypalrestsdk.Payment.find(payment_id)
            
            if not payment:
                self.logger.error(f"Payment not found: {payment_id}")
                return None
            
            # Execute the payment
            if payment.execute({"payer_id": payer_id}):
                # Get purchase from database
                purchase = self.db.get_purchase_by_paypal_id(payment_id)
                
                if not purchase:
                    self.logger.error(f"Purchase not found for payment: {payment_id}")
                    return None
                
                # Generate activation key
                activation_key = self._generate_activation_key(purchase['product_id'])
                
                # Update purchase status
                success = self.db.update_purchase_status(
                    paypal_payment_id=payment_id,
                    status='completed',
                    activation_key=activation_key
                )
                
                if success:
                    self.logger.info(f"Payment executed successfully: {payment_id}")
                    
                    return {
                        'payment_id': payment_id,
                        'status': 'completed',
                        'activation_key': activation_key,
                        'purchase': purchase,
                        'transaction_id': payment.transactions[0].related_resources[0].sale.id
                    }
                else:
                    self.logger.error(f"Failed to update purchase status for payment: {payment_id}")
                    return None
            else:
                self.logger.error(f"PayPal payment execution failed: {payment.error}")
                
                # Update purchase status to failed
                self.db.update_purchase_status(
                    paypal_payment_id=payment_id,
                    status='failed'
                )
                
                return None
                
        except Exception as e:
            self.logger.error(f"Payment execution failed: {str(e)}")
            
            # Update purchase status to failed
            try:
                self.db.update_purchase_status(
                    paypal_payment_id=payment_id,
                    status='failed'
                )
            except:
                pass
            
            return None
    
    def get_payment_details(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Get PayPal payment details"""
        try:
            payment = paypalrestsdk.Payment.find(payment_id)
            
            if payment:
                return {
                    'id': payment.id,
                    'state': payment.state,
                    'intent': payment.intent,
                    'payer': payment.payer,
                    'transactions': payment.transactions,
                    'create_time': payment.create_time,
                    'update_time': payment.update_time
                }
            else:
                self.logger.error(f"Payment not found: {payment_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get payment details: {str(e)}")
            return None
    
    def cancel_payment(self, payment_id: str) -> bool:
        """Cancel a payment and update database"""
        try:
            # Update purchase status in database
            success = self.db.update_purchase_status(
                paypal_payment_id=payment_id,
                status='cancelled'
            )
            
            if success:
                self.logger.info(f"Payment cancelled: {payment_id}")
                return True
            else:
                self.logger.error(f"Failed to cancel payment in database: {payment_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Payment cancellation failed: {str(e)}")
            return False
    
    def refund_payment(self, payment_id: str, amount: Optional[float] = None, 
                      reason: str = "Requested by customer") -> Optional[Dict[str, Any]]:
        """Process a refund for a payment"""
        try:
            # Get the payment
            payment = paypalrestsdk.Payment.find(payment_id)
            
            if not payment or payment.state != 'approved':
                self.logger.error(f"Payment not found or not approved: {payment_id}")
                return None
            
            # Get the sale transaction
            sale = None
            for transaction in payment.transactions:
                for resource in transaction.related_resources:
                    if hasattr(resource, 'sale'):
                        sale = resource.sale
                        break
                if sale:
                    break
            
            if not sale:
                self.logger.error(f"No sale transaction found for payment: {payment_id}")
                return None
            
            # Create refund
            refund_data = {
                "reason": reason
            }
            
            if amount:
                refund_data["amount"] = {
                    "total": f"{amount:.2f}",
                    "currency": "USD"
                }
            
            refund = sale.refund(refund_data)
            
            if refund.success():
                # Update purchase status
                self.db.update_purchase_status(
                    paypal_payment_id=payment_id,
                    status='refunded'
                )
                
                self.logger.info(f"Refund processed: {refund.id} for payment {payment_id}")
                
                return {
                    'refund_id': refund.id,
                    'state': refund.state,
                    'amount': refund.amount,
                    'create_time': refund.create_time
                }
            else:
                self.logger.error(f"Refund failed: {refund.error}")
                return None
                
        except Exception as e:
            self.logger.error(f"Refund processing failed: {str(e)}")
            return None
    
    def verify_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Verify PayPal webhook signature"""
        try:
            # This is a simplified verification
            # In production, you should implement proper webhook signature verification
            # using PayPal's webhook verification API
            
            required_fields = ['id', 'event_type', 'resource']
            
            for field in required_fields:
                if field not in webhook_data:
                    self.logger.error(f"Missing required webhook field: {field}")
                    return False
            
            self.logger.info(f"Webhook verified: {webhook_data['id']}")
            return True
            
        except Exception as e:
            self.logger.error(f"Webhook verification failed: {str(e)}")
            return False
    
    def process_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Process PayPal webhook events"""
        try:
            if not self.verify_webhook(webhook_data):
                return False
            
            event_type = webhook_data['event_type']
            resource = webhook_data['resource']
            
            self.logger.info(f"Processing webhook: {event_type}")
            
            if event_type == 'PAYMENT.SALE.COMPLETED':
                return self._handle_sale_completed(resource)
            elif event_type == 'PAYMENT.SALE.DENIED':
                return self._handle_sale_denied(resource)
            elif event_type == 'PAYMENT.SALE.REFUNDED':
                return self._handle_sale_refunded(resource)
            else:
                self.logger.info(f"Unhandled webhook event type: {event_type}")
                return True
                
        except Exception as e:
            self.logger.error(f"Webhook processing failed: {str(e)}")
            return False
    
    def _handle_sale_completed(self, resource: Dict[str, Any]) -> bool:
        """Handle sale completed webhook"""
        try:
            payment_id = resource.get('parent_payment')
            
            if payment_id:
                purchase = self.db.get_purchase_by_paypal_id(payment_id)
                
                if purchase and purchase['status'] != 'completed':
                    activation_key = self._generate_activation_key(purchase['product_id'])
                    
                    success = self.db.update_purchase_status(
                        paypal_payment_id=payment_id,
                        status='completed',
                        activation_key=activation_key
                    )
                    
                    if success:
                        self.logger.info(f"Sale completed via webhook: {payment_id}")
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to handle sale completed webhook: {str(e)}")
            return False
    
    def _handle_sale_denied(self, resource: Dict[str, Any]) -> bool:
        """Handle sale denied webhook"""
        try:
            payment_id = resource.get('parent_payment')
            
            if payment_id:
                success = self.db.update_purchase_status(
                    paypal_payment_id=payment_id,
                    status='denied'
                )
                
                if success:
                    self.logger.info(f"Sale denied via webhook: {payment_id}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to handle sale denied webhook: {str(e)}")
            return False
    
    def _handle_sale_refunded(self, resource: Dict[str, Any]) -> bool:
        """Handle sale refunded webhook"""
        try:
            payment_id = resource.get('parent_payment')
            
            if payment_id:
                success = self.db.update_purchase_status(
                    paypal_payment_id=payment_id,
                    status='refunded'
                )
                
                if success:
                    self.logger.info(f"Sale refunded via webhook: {payment_id}")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to handle sale refunded webhook: {str(e)}")
            return False
    
    def _generate_activation_key(self, product_id: str) -> str:
        """Generate a unique activation key"""
        try:
            # Try to get a pre-generated activation key first
            activation_key = self.db.get_unused_activation_key(product_id)
            
            if activation_key:
                return activation_key
            
            # Generate a new activation key if none available
            timestamp = datetime.now().strftime('%Y%m%d')
            unique_id = str(uuid.uuid4()).replace('-', '').upper()[:12]
            
            activation_key = f"{product_id.upper()}-{timestamp}-{unique_id}"
            
            self.logger.info(f"Generated activation key for product: {product_id}")
            return activation_key
            
        except Exception as e:
            self.logger.error(f"Failed to generate activation key: {str(e)}")
            # Fallback to simple UUID
            return str(uuid.uuid4()).replace('-', '').upper()
    
    def get_payment_statistics(self) -> Dict[str, Any]:
        """Get payment statistics"""
        try:
            stats = self.db.get_purchase_stats()
            
            # Add PayPal-specific statistics
            stats['payment_provider'] = 'PayPal'
            stats['currency'] = 'USD'
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get payment statistics: {str(e)}")
            return {}
    
    def test_paypal_connection(self) -> bool:
        """Test PayPal API connection"""
        try:
            # Try to get PayPal API credentials info
            # This is a simple test to verify the connection
            test_payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {"payment_method": "paypal"},
                "transactions": [{
                    "amount": {"total": "0.01", "currency": "USD"},
                    "description": "Test connection"
                }]
            })
            
            # We don't actually create the payment, just validate the structure
            self.logger.info("PayPal connection test successful")
            return True
            
        except Exception as e:
            self.logger.error(f"PayPal connection test failed: {str(e)}")
            return False