/**
 * Authentication Manager
 * Handles JWT token management and user authentication state
 */

class AuthManager {
    constructor() {
        this.tokenKey = window.APP_CONFIG.TOKEN_KEY;
        this.userKey = window.APP_CONFIG.USER_KEY;
        this.init();
    }
    
    init() {
        this.updateNavigationState();
        this.setupLogoutHandler();
    }
    
    // Check if user is authenticated
    isAuthenticated() {
        return !!this.getToken();
    }
    
    // Get stored JWT token
    getToken() {
        return localStorage.getItem(this.tokenKey);
    }
    
    // Get stored user data
    getUser() {
        const userStr = localStorage.getItem(this.userKey);
        return userStr ? JSON.parse(userStr) : null;
    }
    
    // Get user role
    getUserRole() {
        const user = this.getUser();
        return user ? user.role.toLowerCase() : null;
    }
    
    // Store authentication data
    setAuth(token, user) {
        localStorage.setItem(this.tokenKey, token);
        localStorage.setItem(this.userKey, JSON.stringify(user));
        this.updateNavigationState();
    }
    
    // Clear authentication data
    clearAuth() {
        localStorage.removeItem(this.tokenKey);
        localStorage.removeItem(this.userKey);
        localStorage.removeItem('cart'); // Clear cart on logout
        this.updateNavigationState();
    }
    
    // Logout user
    logout() {
        this.clearAuth();
        window.location.href = window.APP_CONFIG.URLS.home;
    }
    
    // Update navigation based on auth state
    updateNavigationState() {
        const isAuth = this.isAuthenticated();
        const role = this.getUserRole();
        const user = this.getUser();
        
        // Guest navigation
        const guestNav = document.querySelectorAll('.guest-nav');
        guestNav.forEach(el => {
            el.classList.toggle('d-none', isAuth);
        });
        
        // Authenticated navigation
        const authNav = document.querySelectorAll('.auth-nav');
        authNav.forEach(el => {
            el.classList.toggle('d-none', !isAuth);
        });
        
        // Role-specific navigation
        const customerNav = document.querySelectorAll('.customer-nav');
        customerNav.forEach(el => {
            el.classList.toggle('d-none', role !== 'customer');
        });
        
        const adminNav = document.querySelectorAll('.admin-nav');
        adminNav.forEach(el => {
            el.classList.toggle('d-none', role !== 'admin');
        });
        
        const staffNav = document.querySelectorAll('.staff-nav');
        staffNav.forEach(el => {
            el.classList.toggle('d-none', role !== 'staff');
        });
        
        // Update user name in navbar
        if (isAuth && user) {
            const userNameEl = document.getElementById('userName');
            if (userNameEl) {
                userNameEl.textContent = user.name || 'User';
            }
        }
        
        // Update cart count
        this.updateCartCount();
    }
    
    // Update cart count in navbar
    updateCartCount() {
        const cartCountEl = document.getElementById('cartCount');
        if (cartCountEl) {
            const cart = JSON.parse(localStorage.getItem('cart') || '[]');
            const count = cart.reduce((sum, item) => sum + (item.quantity || 1), 0);
            cartCountEl.textContent = count;
            cartCountEl.classList.toggle('d-none', count === 0);
        }
    }
    
    // Setup logout button handler
    setupLogoutHandler() {
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', (e) => {
                e.preventDefault();
                if (confirm('Are you sure you want to logout?')) {
                    this.logout();
                }
            });
        }
    }
    
    // Redirect if not authenticated
    requireAuth() {
        if (!this.isAuthenticated()) {
            window.location.href = window.APP_CONFIG.URLS.login;
            return false;
        }
        return true;
    }
    
    // Redirect if not specific role
    requireRole(requiredRole) {
        if (!this.requireAuth()) return false;
        
        const role = this.getUserRole();
        if (role !== requiredRole.toLowerCase()) {
            alert('You do not have permission to access this page.');
            window.location.href = window.APP_CONFIG.URLS.home;
            return false;
        }
        return true;
    }
}

// Initialize auth manager
const authManager = new AuthManager();

// Export for use in other scripts
window.authManager = authManager;
