/**
 * API Client
 * Handles all API requests with automatic JWT token injection
 */

class APIClient {
        // Home service bookings for current user
        async getMyBookings() {
            const data = await this.get('/api/my/bookings');
            return Array.isArray(data) ? data : (data.bookings || data);
        }

        // Package bookings for current user
        async getMyPackageBookings() {
            const data = await this.get('/api/package/bookings');
            return Array.isArray(data) ? data : (data.bookings || data);
        }
    constructor() {
        this.baseURL = window.APP_CONFIG.API_BASE_URL;
        this.tokenKey = window.APP_CONFIG.TOKEN_KEY;
    }
    
    // Get authorization headers
    getHeaders(includeAuth = true, includeContentType = true) {
        const headers = {};
        
        if (includeContentType) {
            headers['Content-Type'] = 'application/json';
        }
        
        if (includeAuth) {
            const token = localStorage.getItem(this.tokenKey);
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
        }
        
        return headers;
    }
    
    // Handle API response
    async handleResponse(response) {
        let data;
        let isJson = true;
        try {
            data = await response.json();
        } catch (e) {
            isJson = false;
        }

        if (!response.ok) {
            // Handle unauthorized errors
            if (response.status === 401) {
                // Token expired or invalid
                if (window.authManager) {
                    window.authManager.clearAuth();
                    window.location.href = window.APP_CONFIG.URLS.login;
                }
            }
            if (!isJson) {
                // HTML error page or other non-JSON error
                throw new Error('Server error: ' + response.status + ' (non-JSON response)');
            }
            throw new Error((data && data.message) || `HTTP error! status: ${response.status}`);
        }

        if (!isJson) {
            throw new Error('Server returned non-JSON response');
        }
        return data;
    }
    
    // GET request
    async get(endpoint, includeAuth = true) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: 'GET',
                headers: this.getHeaders(includeAuth)
            });
            
            return await this.handleResponse(response);
        } catch (error) {
            console.error('GET request error:', error);
            throw error;
        }
    }
    
    // POST request
    async post(endpoint, data, includeAuth = true) {
        try {
            const isFormData = data instanceof FormData;
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: 'POST',
                headers: isFormData ? this.getHeaders(includeAuth, false) : this.getHeaders(includeAuth),
                body: isFormData ? data : JSON.stringify(data)
            });
            
            return await this.handleResponse(response);
        } catch (error) {
            console.error('POST request error:', error);
            throw error;
        }
    }
    
    // PUT request
    async put(endpoint, data, includeAuth = true) {
        try {
            const isFormData = data instanceof FormData;
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: 'PUT',
                headers: isFormData ? this.getHeaders(includeAuth, false) : this.getHeaders(includeAuth),
                body: isFormData ? data : JSON.stringify(data)
            });
            
            return await this.handleResponse(response);
        } catch (error) {
            console.error('PUT request error:', error);
            throw error;
        }
    }
    
    // DELETE request
    async delete(endpoint, includeAuth = true) {
        try {
            const response = await fetch(`${this.baseURL}${endpoint}`, {
                method: 'DELETE',
                headers: this.getHeaders(includeAuth)
            });
            
            return await this.handleResponse(response);
        } catch (error) {
            console.error('DELETE request error:', error);
            throw error;
        }
    }
    
    // Auth endpoints
    async login(email, password) {
        return await this.post('/auth/login', { email, password }, false);
    }
    
    async register(userData) {
        return await this.post('/auth/register', userData, false);
    }
    
    async getProfile() {
        return await this.get('/auth/profile');
    }

    async updateProfile(profileData) {
        return await this.put('/auth/profile', profileData);
    }
    
    // Services endpoints
    async getServices() {
        const data = await this.get('/api/services', false);
        // Normalize: backend returns an array; wrap into { services: [] }
        return Array.isArray(data) ? { services: data } : data;
    }
    
    async getService(id) {
        return await this.get(`/api/services/${id}`, false);
    }
    
    async createService(serviceData) {
        // If FormData, use it directly; otherwise map to backend field names
        if (serviceData instanceof FormData) {
            return await this.post('/api/services', serviceData);
        }
        
        const payload = {
            name: serviceData.name,
            subcategory_id: serviceData.subcategory_id,
            duration_mins: serviceData.duration_mins ?? serviceData.duration, // support both
            price: serviceData.price,
            description: serviceData.description ?? null,
            service_type: serviceData.service_type ?? 'in-center'
        };
        return await this.post('/api/services', payload);
    }
    
    async updateService(id, serviceData) {
        // If FormData, use it directly; otherwise map to backend field names
        if (serviceData instanceof FormData) {
            return await this.put(`/api/services/${id}`, serviceData);
        }
        
        const payload = {
            name: serviceData.name,
            subcategory_id: serviceData.subcategory_id,
            duration_mins: serviceData.duration_mins ?? serviceData.duration,
            price: serviceData.price,
            description: serviceData.description ?? null,
            service_type: serviceData.service_type ?? 'in-center'
        };
        return await this.put(`/api/services/${id}`, payload);
    }
    
    async deleteService(id) {
        return await this.delete(`/api/services/${id}`);
    }
    
    // Categories endpoints
    async getCategories() {
        const data = await this.get('/api/categories', false);
        return Array.isArray(data) ? { categories: data } : data;
    }
    
    async createCategory(categoryData) {
        return await this.post('/api/categories', categoryData);
    }
    async updateCategory(id, categoryData) {
        return await this.put(`/api/categories/${id}`, categoryData);
    }

    async deleteCategory(id) {
        return await this.delete(`/api/categories/${id}`);
    }
    
    // Subcategories endpoints
    async getSubcategories() {
        const data = await this.get('/api/subcategories', false);
        return Array.isArray(data) ? { subcategories: data } : data;
    }
    
    async createSubcategory(subcategoryData) {
        return await this.post('/api/subcategories', subcategoryData);
    }
    async updateSubcategory(id, subcategoryData) {
        return await this.put(`/api/subcategories/${id}`, subcategoryData);
    }

    async deleteSubcategory(id) {
        return await this.delete(`/api/subcategories/${id}`);
    }
    
    // Packages endpoints
    async getPackages() {
        return await this.get('/api/packages', false);
    }
    
    // Appointments endpoints
    async createAppointment(appointmentData) {
        return await this.post('/api/appointments', appointmentData);
    }
    
    async getAvailableSlots(serviceIds, date) {
        return await this.get(`/api/slots?service_ids=${serviceIds}&date=${date}`, false);
    }
    
    // Bookings endpoints
    async createBooking(bookingData) {
        return await this.post('/api/bookings', bookingData);
    }
    
    // Products endpoints
    async getProducts() {
        const data = await this.get('/products', false);
        return Array.isArray(data) ? { products: data } : data;
    }

    async getSuppliers() {
        const data = await this.get('/suppliers');
        return Array.isArray(data) ? { suppliers: data } : data;
    }

    async createSupplier(supplierData) {
        return await this.post('/suppliers', supplierData);
    }

    async updateSupplier(id, supplierData) {
        return await this.put(`/suppliers/${id}`, supplierData);
    }

    async deleteSupplier(id) {
        return await this.delete(`/suppliers/${id}`);
    }

    // Customer endpoints
    async getMyCustomer() {
        return await this.get('/customers/me');
    }

    async createCustomer(data) {
        return await this.post('/customers/me', data);
    }

    async updateCustomer(data) {
        return await this.put('/customers/me', data);
    }

    // Areas
    async getAreas() {
        const data = await this.get('/areas');
        return Array.isArray(data) ? { areas: data } : data;
    }

    async getArea(id) {
        return await this.get(`/areas/${id}`);
    }

    // Cart / Order helpers: sync local cart to server and create an order
    async syncCartAndCreateOrder(cartItems) {
        // cartItems: [{id, name, price, quantity}]
        // Ensure authenticated
        const profile = await this.getProfile();
        const user = profile.user;
        if (!user) throw new Error('User not found');

        // Get or create customer profile
        let customerResp;
        try {
            customerResp = await this.getMyCustomer();
        } catch (err) {
            // try to create minimal customer
            customerResp = await this.createCustomer({});
        }
        const customerId = customerResp.id || customerResp.customer_id || customerResp.user_id || customerResp.id;

        // Post each item to /cart; the first response contains cart id
        let cartId = null;
        for (const item of cartItems) {
            const resp = await this.post('/cart', {
                customer_id: customerId,
                product_id: item.id,
                quantity: item.quantity
            });
            if (!cartId && resp && resp.id) cartId = resp.id;
        }

        if (!cartId) throw new Error('Failed to create cart on server');

        // Create order
        const order = await this.post('/orders', { customer_id: customerId, cart_id: cartId });
        return order;
    }
    
    async createProduct(productData) {
        // If FormData, use it directly; otherwise use as is
        if (productData instanceof FormData) {
            return await this.post('/products', productData);
        }
        return await this.post('/products', productData);
    }

    async updateProduct(id, productData) {
        // If FormData, use it directly; otherwise use as is
        if (productData instanceof FormData) {
            return await this.put(`/products/${id}`, productData);
        }
        return await this.put(`/products/${id}`, productData);
    }

    async deleteProduct(id) {
        return await this.delete(`/products/${id}`);
    }
    
    // Brands endpoints
    async getBrands() {
        const data = await this.get('/brands', false);
        return Array.isArray(data) ? { brands: data } : data;
    }
    
    async createBrand(brandData) {
        return await this.post('/brands', brandData);
    }

    async updateBrand(id, brandData) {
        return await this.put(`/brands/${id}`, brandData);
    }

    async deleteBrand(id) {
        return await this.delete(`/brands/${id}`);
    }
    
    // Stock endpoints
    async getStock() {
        return await this.get('/stock');
    }

    async createStock(stockData) {
        return await this.post('/stock', stockData);
    }

    async updateStock(id, stockData) {
        return await this.put(`/stock/${id}`, stockData);
    }

    async deleteStock(id) {
        return await this.delete(`/stock/${id}`);
    }

    // Offers endpoints
    async getOffers() {
        const data = await this.get('/offers', false);
        return Array.isArray(data) ? { offers: data } : data;
    }

    async createOffer(offerData) {
        return await this.post('/offers', offerData);
    }

    async updateOffer(id, offerData) {
        return await this.put(`/offers/${id}`, offerData);
    }

    async deleteOffer(id) {
        return await this.delete(`/offers/${id}`);
    }

    // Bills and payments
    async listBills() {
        return await this.get('/bills');
    }

    async getBillPDF(billId) {
        // return full URL for download
        return `${this.baseURL}/bills/${billId}/pdf`;
    }

    // Deliveries
    async createDelivery(deliveryData) {
        return await this.post('/deliveries', deliveryData);
    }


    async createRazorpayOrder(orderId) {
        return await this.post('/payments/razorpay/create_order', { order_id: orderId });
    }

    /**
     * Create a Razorpay order from a given amount (for cart checkout before backend order is created)
     * @param {number} amount - The total amount (in INR, float)
     * @returns {Promise<object>} Razorpay order response
     */
    async createRazorpayOrderFromAmount(amount) {
        // Backend endpoint should accept { amount } and return Razorpay order object
        // Defensive: handle non-JSON error responses gracefully
        try {
            return await this.post('/payments/razorpay/create_order_from_amount', { amount });
        } catch (err) {
            // If error is 404 or non-JSON, show a clear message
            if (err.message && err.message.includes('404')) {
                throw new Error('Razorpay order endpoint not found. Please contact support.');
            }
            throw err;
        }
    }

    async verifyRazorpayPayment(payload) {
        return await this.post('/payments/razorpay/verify', payload);
    }

    async assignDelivery(deliveryId, staffId) {
        return await this.put(`/deliveries/${deliveryId}/assign`, { staff_id: staffId });
    }

    async completeDelivery(deliveryId) {
        return await this.put(`/deliveries/${deliveryId}/complete`, {});
    }

    // Complaints
    async submitComplaint(data) {
        return await this.post('/complaints', data);
    }

    async listComplaints() {
        return await this.get('/complaints');
    }

    async getMyComplaints() {
        return await this.get('/complaints/me');
    }

    async reviewComplaint(complaintId, payload) {
        return await this.put(`/complaints/${complaintId}/review`, payload);
    }
    
    // Bills endpoints
    async createBill(billData) {
        return await this.post('/bills', billData);
    }
    
    async getUserBills() {
        return await this.get('/bills');
    }

    // Staff endpoints
    async getAvailableStaff() {
        const data = await this.get('/api/staff/available', false);
        return Array.isArray(data) ? { staff: data } : data;
    }

    async getStaffs() {
        const data = await this.get('/api/staff');
        return Array.isArray(data) ? { staff: data } : data;
    }

    async createStaff(staffData) {
        return await this.post('/api/staff', staffData);
    }

    async updateStaff(id, staffData) {
        return await this.put(`/api/staff/${id}`, staffData);
    }

    async deleteStaff(id) {
        return await this.delete(`/api/staff/${id}`);
    }

    // Customers
    async getCustomers() {
        const data = await this.get('/api/customers');
        return Array.isArray(data) ? { customers: data } : data;
    }

    // Admin: Users
    async getUsers() {
        const data = await this.get('/api/users');
        return Array.isArray(data) ? { users: data } : data;
    }

    // Appointments for current user
    async getMyAppointments() {
        const data = await this.get('/api/my/appointments');
        return Array.isArray(data) ? { appointments: data } : data;
    }

    // Orders for current user
    async getMyOrders() {
        const data = await this.get('/orders/my');
        return Array.isArray(data) ? { orders: data } : data;
    }

    // Staff endpoints
    async getStaffAssignments() {
        const data = await this.get('/api/staff/me/assignments');
        return Array.isArray(data) ? data : (data.assignments || data);
    }

    async getMyDeliveries() {
        const data = await this.get('/deliveries/my');
        return data;
    }

    async updateDeliveryStatus(deliveryId, status) {
        return await this.put(`/deliveries/${deliveryId}/status`, { status });
    }

    // Staff self profile
    async getMyStaff() {
        return await this.get('/api/staff/me');
    }

    async updateMyStaffProfile(payload) {
        return await this.put('/api/staff/me', payload);
    }

    async createMyStaff(payload) {
        return await this.post('/api/staff/me', payload);
    }

    // Admin / Staff: list all appointments (optionally filtered by date via query param)
    async listAppointments(params = '') {
        // params may be like '?date=2025-12-29'
        const endpoint = '/api/appointments' + (params || '');
        const data = await this.get(endpoint);
        return Array.isArray(data) ? { appointments: data } : data;
    }
}

// Initialize API client
const apiClient = new APIClient();

// Export for use in other scripts
window.apiClient = apiClient;
