/**
 * Main Application JavaScript
 * Global utilities and initialization
 */

// Toast notification utility
class Toast {
    static show(message, type = 'info') {
        const toastContainer = this.getToastContainer();
        const toast = this.createToast(message, type);
        
        toastContainer.appendChild(toast);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }
    
    static getToastContainer() {
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        return container;
    }
    
    static createToast(message, type) {
        const toast = document.createElement('div');
        toast.className = 'toast show';
        toast.setAttribute('role', 'alert');
        
        const bgColor = {
            'success': 'bg-success',
            'error': 'bg-danger',
            'warning': 'bg-warning',
            'info': 'bg-info'
        }[type] || 'bg-info';
        
        const icon = {
            'success': 'bi-check-circle',
            'error': 'bi-exclamation-triangle',
            'warning': 'bi-exclamation-circle',
            'info': 'bi-info-circle'
        }[type] || 'bi-info-circle';
        
        toast.innerHTML = `
            <div class="toast-header ${bgColor} text-white">
                <i class="bi ${icon} me-2"></i>
                <strong class="me-auto">${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        // Add close button functionality
        const closeBtn = toast.querySelector('.btn-close');
        closeBtn.addEventListener('click', () => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        });
        
        return toast;
    }
    
    static success(message) {
        this.show(message, 'success');
    }
    
    static error(message) {
        this.show(message, 'error');
    }
    
    static warning(message) {
        this.show(message, 'warning');
    }
    
    static info(message) {
        this.show(message, 'info');
    }
}

// Form validation utility
class FormValidator {
    static validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }
    
    static validatePhone(phone) {
        const re = /^[0-9]{10}$/;
        return re.test(phone);
    }
    
    static validatePassword(password) {
        return password.length >= 6;
    }
    
    static validateForm(formElement) {
        if (!formElement.checkValidity()) {
            formElement.classList.add('was-validated');
            return false;
        }
        return true;
    }
}

// Loading overlay utility
class LoadingOverlay {
    static show(message = 'Loading...') {
        let overlay = document.getElementById('loadingOverlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'loadingOverlay';
            overlay.className = 'loading-overlay';
            overlay.innerHTML = `
                <div class="loading-content">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="loading-message">${message}</p>
                </div>
            `;
            document.body.appendChild(overlay);
        }
        overlay.style.display = 'flex';
    }
    
    static hide() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }
}

// Cart management utility
class CartManager {
    static getCart() {
        return JSON.parse(localStorage.getItem('cart') || '[]');
    }
    
    static saveCart(cart) {
        localStorage.setItem('cart', JSON.stringify(cart));
        if (window.authManager) {
            window.authManager.updateCartCount();
        }
    }
    
    static addItem(product, quantity = 1) {
        const cart = this.getCart();
        const existingItem = cart.find(item => item.id === product.id);
        
        if (existingItem) {
            existingItem.quantity += quantity;
        } else {
            cart.push({
                id: product.id,
                name: product.name,
                price: product.price,
                quantity: quantity,
                image: product.image || null
            });
        }
        
        this.saveCart(cart);
        Toast.success(`${product.name} added to cart!`);
    }
    
    static removeItem(productId) {
        let cart = this.getCart();
        cart = cart.filter(item => item.id !== productId);
        this.saveCart(cart);
    }
    
    static updateQuantity(productId, quantity) {
        const cart = this.getCart();
        const item = cart.find(item => item.id === productId);
        
        if (item) {
            if (quantity <= 0) {
                this.removeItem(productId);
            } else {
                item.quantity = quantity;
                this.saveCart(cart);
            }
        }
    }
    
    static clearCart() {
        localStorage.removeItem('cart');
        if (window.authManager) {
            window.authManager.updateCartCount();
        }
    }
    
    static getTotal() {
        const cart = this.getCart();
        return cart.reduce((total, item) => total + (item.price * item.quantity), 0);
    }
    
    static getItemCount() {
        const cart = this.getCart();
        return cart.reduce((count, item) => count + item.quantity, 0);
    }
}

// Utility functions
const Utils = {
    formatCurrency(amount) {
        return `₹${parseFloat(amount).toFixed(2)}`;
    },
    
    formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    },
    
    formatTime(timeString) {
        const [hours, minutes] = timeString.split(':');
        const hour = parseInt(hours);
        const ampm = hour >= 12 ? 'PM' : 'AM';
        const displayHour = hour % 12 || 12;
        return `${displayHour}:${minutes} ${ampm}`;
    },
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
};

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// Export utilities
window.Toast = Toast;
window.FormValidator = FormValidator;
window.LoadingOverlay = LoadingOverlay;
window.CartManager = CartManager;
window.Utils = Utils;
