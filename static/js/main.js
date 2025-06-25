// Gotcha Guardian Payment Server - Main JavaScript

class PaymentPortal {
    constructor() {
        this.selectedProduct = null;
        this.paypalLoaded = false;
        this.currentSection = 'products';
        this.orderData = null;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadProducts();
        this.loadPayPalScript();
    }

    bindEvents() {
        // Product selection
        document.addEventListener('click', (e) => {
            if (e.target.closest('.product-select-btn')) {
                const productId = e.target.closest('.product-select-btn').dataset.productId;
                this.selectProduct(productId);
            }
        });

        // Form submission
        const contactForm = document.getElementById('contact-form');
        if (contactForm) {
            contactForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.validateAndProceedToPayment();
            });
        }

        // Copy activation key
        document.addEventListener('click', (e) => {
            if (e.target.closest('.copy-key-btn')) {
                this.copyActivationKey();
            }
        });

        // Download button
        document.addEventListener('click', (e) => {
            if (e.target.closest('.download-btn')) {
                this.downloadProduct();
            }
        });

        // Back to products button
        document.addEventListener('click', (e) => {
            if (e.target.closest('.back-to-products')) {
                this.showSection('products');
            }
        });
    }

    async loadProducts() {
        try {
            const response = await fetch('/api/products');
            const data = await response.json();
            
            if (data.success) {
                this.renderProducts(data.products);
            } else {
                this.showError('Failed to load products');
            }
        } catch (error) {
            console.error('Error loading products:', error);
            this.showError('Failed to load products');
        }
    }

    renderProducts(products) {
        const container = document.getElementById('products-container');
        if (!container) return;

        container.innerHTML = products.map(product => `
            <div class="product-card ${product.featured ? 'featured' : ''}">
                ${product.featured ? '<div class="product-badge">Most Popular</div>' : ''}
                <h3 class="text-2xl font-bold text-center mb-4">${product.name}</h3>
                <div class="product-price text-center">$${product.price}</div>
                <p class="text-gray-600 text-center mb-6">${product.description}</p>
                
                <ul class="product-features">
                    ${product.features.map(feature => `
                        <li>
                            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                            </svg>
                            ${feature}
                        </li>
                    `).join('')}
                </ul>
                
                <button class="btn btn-primary w-full product-select-btn" data-product-id="${product.id}">
                    Select ${product.name}
                </button>
            </div>
        `).join('');
    }

    selectProduct(productId) {
        // Find product data
        fetch('/api/products')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.selectedProduct = data.products.find(p => p.id === productId);
                    if (this.selectedProduct) {
                        this.showSection('payment');
                        this.renderSelectedProduct();
                    }
                }
            })
            .catch(error => {
                console.error('Error selecting product:', error);
                this.showError('Failed to select product');
            });
    }

    renderSelectedProduct() {
        const container = document.getElementById('selected-product');
        if (!container || !this.selectedProduct) return;

        container.innerHTML = `
            <div class="selected-product">
                <h3 class="text-xl font-bold mb-2">${this.selectedProduct.name}</h3>
                <p class="text-gray-600 mb-4">${this.selectedProduct.description}</p>
                <div class="flex justify-between items-center">
                    <span class="text-2xl font-bold text-blue-600">$${this.selectedProduct.price}</span>
                    <button class="btn btn-secondary back-to-products">Change Product</button>
                </div>
            </div>
        `;
    }

    validateAndProceedToPayment() {
        const form = document.getElementById('contact-form');
        const formData = new FormData(form);
        
        const contactData = {
            name: formData.get('name'),
            email: formData.get('email'),
            country: formData.get('country')
        };

        // Basic validation
        const errors = this.validateContactData(contactData);
        if (errors.length > 0) {
            this.showFormErrors(errors);
            return;
        }

        // Clear any previous errors
        this.clearFormErrors();
        
        // Store contact data and show PayPal button
        this.contactData = contactData;
        this.showPayPalButton();
    }

    validateContactData(data) {
        const errors = [];
        
        if (!data.name || data.name.trim().length < 2) {
            errors.push({ field: 'name', message: 'Name must be at least 2 characters long' });
        }
        
        if (!data.email || !this.isValidEmail(data.email)) {
            errors.push({ field: 'email', message: 'Please enter a valid email address' });
        }
        
        if (!data.country || data.country.trim().length < 2) {
            errors.push({ field: 'country', message: 'Please enter your country' });
        }
        
        return errors;
    }

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    showFormErrors(errors) {
        this.clearFormErrors();
        
        errors.forEach(error => {
            const field = document.querySelector(`[name="${error.field}"]`);
            if (field) {
                field.classList.add('error');
                
                const errorDiv = document.createElement('div');
                errorDiv.className = 'form-error';
                errorDiv.textContent = error.message;
                field.parentNode.appendChild(errorDiv);
            }
        });
    }

    clearFormErrors() {
        document.querySelectorAll('.form-input.error').forEach(field => {
            field.classList.remove('error');
        });
        
        document.querySelectorAll('.form-error').forEach(error => {
            error.remove();
        });
    }

    loadPayPalScript() {
        if (window.paypal) {
            this.paypalLoaded = true;
            return;
        }

        const script = document.createElement('script');
        script.src = 'https://www.paypal.com/sdk/js?client-id=YOUR_PAYPAL_CLIENT_ID&currency=USD';
        script.onload = () => {
            this.paypalLoaded = true;
        };
        script.onerror = () => {
            this.showError('Failed to load PayPal. Please refresh the page and try again.');
        };
        document.head.appendChild(script);
    }

    showPayPalButton() {
        if (!this.paypalLoaded) {
            this.showError('PayPal is still loading. Please wait a moment and try again.');
            return;
        }

        const container = document.getElementById('paypal-button-container');
        if (!container) return;

        // Clear any existing buttons
        container.innerHTML = '';

        window.paypal.Buttons({
            createOrder: (data, actions) => {
                return this.createPayPalOrder();
            },
            onApprove: (data, actions) => {
                return this.executePayPalPayment(data.orderID);
            },
            onError: (err) => {
                console.error('PayPal error:', err);
                this.showError('Payment failed. Please try again.');
            },
            onCancel: (data) => {
                this.showInfo('Payment was cancelled.');
            }
        }).render('#paypal-button-container');
    }

    async createPayPalOrder() {
        try {
            const response = await fetch('/api/create-payment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    product_id: this.selectedProduct.id,
                    contact: this.contactData
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.orderData = data;
                return data.order_id;
            } else {
                throw new Error(data.error || 'Failed to create payment');
            }
        } catch (error) {
            console.error('Error creating PayPal order:', error);
            this.showError('Failed to create payment. Please try again.');
            throw error;
        }
    }

    async executePayPalPayment(orderID) {
        try {
            const response = await fetch('/api/execute-payment', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    order_id: orderID,
                    payment_id: this.orderData.payment_id
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.orderData = { ...this.orderData, ...data };
                this.showSection('success');
                this.renderSuccessPage();
            } else {
                throw new Error(data.error || 'Payment execution failed');
            }
        } catch (error) {
            console.error('Error executing PayPal payment:', error);
            this.showError('Payment processing failed. Please contact support.');
            throw error;
        }
    }

    renderSuccessPage() {
        const container = document.getElementById('success-content');
        if (!container || !this.orderData) return;

        container.innerHTML = `
            <div class="success-container fade-in">
                <svg class="success-icon" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"></path>
                </svg>
                
                <h2 class="text-3xl font-bold text-green-600 mb-4">Payment Successful!</h2>
                <p class="text-gray-600 mb-6">Thank you for your purchase. Your order has been processed successfully.</p>
                
                <div class="download-info">
                    <h3 class="text-xl font-bold mb-4">Download Information</h3>
                    
                    ${this.orderData.download_url ? `
                        <div class="mb-4">
                            <p class="font-semibold mb-2">Download Link:</p>
                            <button class="btn btn-primary download-btn" data-url="${this.orderData.download_url}">
                                <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                                </svg>
                                Download ${this.selectedProduct.name}
                            </button>
                        </div>
                    ` : ''}
                    
                    ${this.orderData.activation_key ? `
                        <div class="mb-4">
                            <p class="font-semibold mb-2">Activation Key:</p>
                            <div class="activation-key mb-2">${this.orderData.activation_key}</div>
                            <button class="btn btn-secondary copy-key-btn">
                                <svg class="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                    <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z"></path>
                                    <path d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z"></path>
                                </svg>
                                Copy Key
                            </button>
                        </div>
                    ` : ''}
                    
                    <div class="text-sm text-gray-600">
                        <p><strong>Order ID:</strong> ${this.orderData.order_id || 'N/A'}</p>
                        <p><strong>Transaction ID:</strong> ${this.orderData.transaction_id || 'N/A'}</p>
                        <p class="mt-2">A confirmation email has been sent to <strong>${this.contactData.email}</strong></p>
                    </div>
                </div>
                
                <button class="btn btn-secondary back-to-products mt-6">
                    Purchase Another Product
                </button>
            </div>
        `;
    }

    copyActivationKey() {
        if (!this.orderData || !this.orderData.activation_key) return;
        
        navigator.clipboard.writeText(this.orderData.activation_key)
            .then(() => {
                this.showSuccess('Activation key copied to clipboard!');
            })
            .catch(() => {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = this.orderData.activation_key;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                this.showSuccess('Activation key copied to clipboard!');
            });
    }

    downloadProduct() {
        if (!this.orderData || !this.orderData.download_url) return;
        
        // Create a temporary link and click it
        const link = document.createElement('a');
        link.href = this.orderData.download_url;
        link.download = '';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        this.showInfo('Download started. If the download doesn\'t start automatically, please check your browser\'s download settings.');
    }

    showSection(sectionName) {
        // Hide all sections
        document.querySelectorAll('.section').forEach(section => {
            section.classList.add('hidden');
        });
        
        // Show target section
        const targetSection = document.getElementById(`${sectionName}-section`);
        if (targetSection) {
            targetSection.classList.remove('hidden');
            this.currentSection = sectionName;
        }
    }

    showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('alert-container') || this.createAlertContainer();
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} slide-up`;
        alert.innerHTML = `
            <div class="flex items-center justify-between">
                <span>${message}</span>
                <button class="ml-4 text-lg font-bold" onclick="this.parentElement.parentElement.remove()">&times;</button>
            </div>
        `;
        
        alertContainer.appendChild(alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }

    createAlertContainer() {
        const container = document.createElement('div');
        container.id = 'alert-container';
        container.className = 'fixed top-4 right-4 z-50 space-y-2';
        document.body.appendChild(container);
        return container;
    }

    showSuccess(message) {
        this.showAlert(message, 'success');
    }

    showError(message) {
        this.showAlert(message, 'error');
    }

    showWarning(message) {
        this.showAlert(message, 'warning');
    }

    showInfo(message) {
        this.showAlert(message, 'info');
    }
}

// Initialize the payment portal when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PaymentPortal();
});

// Utility functions
function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

function formatDate(date) {
    return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(new Date(date));
}

// Export for potential module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PaymentPortal;
}