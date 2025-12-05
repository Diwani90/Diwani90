/**
 * ===================================
 * منصة ديواني - API Services Layer
 * Professional API integration
 * ===================================
 */

import axios from 'axios';

// Base API configuration
const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const API_VERSION = '/api/v1';

// Create axios instance
const api = axios.create({
  baseURL: `${API_BASE_URL}${API_VERSION}`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ===================================
// Auth Services
// ===================================
export const authService = {
  login: async (phone, password) => {
    const response = await api.post('/accounts/login', { phone_number: phone, password });
    return response.data;
  },

  register: async (userData) => {
    const response = await api.post('/accounts/register', userData);
    return response.data;
  },

  sendOTP: async (phone) => {
    const response = await api.post('/accounts/otp/send', { phone_number: phone });
    return response.data;
  },

  verifyOTP: async (phone, code) => {
    const response = await api.post('/accounts/otp/verify', { phone_number: phone, code });
    return response.data;
  },

  getProfile: async () => {
    const response = await api.get('/accounts/profile');
    return response.data;
  },

  updateProfile: async (data) => {
    const response = await api.patch('/accounts/profile', data);
    return response.data;
  },
};

// ===================================
// Stores Services
// ===================================
export const storesService = {
  getMyStore: async () => {
    const response = await api.get('/stores/my-store');
    return response.data;
  },

  createStore: async (data) => {
    const response = await api.post('/stores/', data);
    return response.data;
  },

  updateStore: async (storeId, data) => {
    const response = await api.patch(`/stores/${storeId}`, data);
    return response.data;
  },

  getStoreStats: async () => {
    const response = await api.get('/stores/my-store/stats');
    return response.data;
  },

  listStores: async (params = {}) => {
    const response = await api.get('/stores/', { params });
    return response.data;
  },

  getStore: async (storeId) => {
    const response = await api.get(`/stores/${storeId}`);
    return response.data;
  },
};

// ===================================
// Products Services
// ===================================
export const productsService = {
  listProducts: async (params = {}) => {
    const response = await api.get('/products/', { params });
    return response.data;
  },

  getProduct: async (productId) => {
    const response = await api.get(`/products/${productId}`);
    return response.data;
  },

  createProduct: async (data) => {
    const response = await api.post('/products/', data);
    return response.data;
  },

  updateProduct: async (productId, data) => {
    const response = await api.patch(`/products/${productId}`, data);
    return response.data;
  },

  deleteProduct: async (productId) => {
    const response = await api.delete(`/products/${productId}`);
    return response.data;
  },

  getMyProducts: async (params = {}) => {
    const response = await api.get('/products/my-products', { params });
    return response.data;
  },

  getCategories: async () => {
    const response = await api.get('/products/categories');
    return response.data;
  },

  getLowStockProducts: async () => {
    const response = await api.get('/products/low-stock');
    return response.data;
  },

  updateStock: async (productId, quantity, type = 'set') => {
    const response = await api.post(`/products/${productId}/stock`, { quantity, type });
    return response.data;
  },
};

// ===================================
// Orders Services
// ===================================
export const ordersService = {
  listOrders: async (params = {}) => {
    const response = await api.get('/orders/', { params });
    return response.data;
  },

  getOrder: async (orderId) => {
    const response = await api.get(`/orders/${orderId}`);
    return response.data;
  },

  createOrder: async (data) => {
    const response = await api.post('/orders/', data);
    return response.data;
  },

  updateOrderStatus: async (orderId, status) => {
    const response = await api.post(`/orders/${orderId}/status`, { status });
    return response.data;
  },

  cancelOrder: async (orderId, reason) => {
    const response = await api.post(`/orders/${orderId}/cancel`, { reason });
    return response.data;
  },

  getCart: async () => {
    const response = await api.get('/orders/cart');
    return response.data;
  },

  addToCart: async (productId, quantity) => {
    const response = await api.post('/orders/cart/add', { product_id: productId, quantity });
    return response.data;
  },

  removeFromCart: async (itemId) => {
    const response = await api.delete(`/orders/cart/items/${itemId}`);
    return response.data;
  },

  clearCart: async () => {
    const response = await api.delete('/orders/cart');
    return response.data;
  },

  getVendorOrders: async (params = {}) => {
    const response = await api.get('/orders/vendor/orders', { params });
    return response.data;
  },

  getVendorStats: async () => {
    const response = await api.get('/orders/vendor/stats');
    return response.data;
  },
};

// ===================================
// Payments Services
// ===================================
export const paymentsService = {
  getPaymentMethods: async () => {
    const response = await api.get('/payments/methods');
    return response.data;
  },

  initializePayment: async (data) => {
    const response = await api.post('/payments/initialize', data);
    return response.data;
  },

  verifyPayment: async (transactionId) => {
    const response = await api.get(`/payments/verify/${transactionId}`);
    return response.data;
  },

  getPaymentHistory: async (params = {}) => {
    const response = await api.get('/payments/history', { params });
    return response.data;
  },

  getSavedCards: async () => {
    const response = await api.get('/payments/cards');
    return response.data;
  },

  deleteCard: async (cardId) => {
    const response = await api.delete(`/payments/cards/${cardId}`);
    return response.data;
  },

  getVendorSummary: async () => {
    const response = await api.get('/payments/vendor/summary');
    return response.data;
  },
};

// ===================================
// Notifications Services
// ===================================
export const notificationsService = {
  getNotifications: async (params = {}) => {
    const response = await api.get('/notifications/notifications', { params });
    return response.data;
  },

  getUnreadNotifications: async (limit = 10) => {
    const response = await api.get('/notifications/notifications/unread', { params: { limit } });
    return response.data;
  },

  getNotificationCount: async () => {
    const response = await api.get('/notifications/notifications/count');
    return response.data;
  },

  markAsRead: async (notificationId) => {
    const response = await api.post(`/notifications/notifications/${notificationId}/read`);
    return response.data;
  },

  markAllAsRead: async () => {
    const response = await api.post('/notifications/notifications/read-all');
    return response.data;
  },

  getPreferences: async () => {
    const response = await api.get('/notifications/preferences');
    return response.data;
  },

  updatePreferences: async (data) => {
    const response = await api.patch('/notifications/preferences', data);
    return response.data;
  },

  updateFCMToken: async (token) => {
    const response = await api.post('/notifications/fcm-token', null, { params: { token } });
    return response.data;
  },
};

// ===================================
// Delivery Services
// ===================================
export const deliveryService = {
  getZones: async () => {
    const response = await api.get('/delivery/zones');
    return response.data;
  },

  calculateFee: async (data) => {
    const response = await api.post('/delivery/calculate-fee', data);
    return response.data;
  },

  trackDelivery: async (deliveryNumber) => {
    const response = await api.get(`/delivery/track/${deliveryNumber}`);
    return response.data;
  },

  rateDelivery: async (deliveryId, rating, feedback = '') => {
    const response = await api.post(`/delivery/${deliveryId}/rate`, { rating, feedback });
    return response.data;
  },
};

// ===================================
// Dashboard Services
// ===================================
export const dashboardService = {
  // Vendor Dashboard Stats
  getVendorDashboard: async () => {
    const [storeStats, vendorOrders, vendorStats, myProducts] = await Promise.all([
      storesService.getStoreStats().catch(() => null),
      ordersService.getVendorOrders({ page_size: 5 }).catch(() => ({ items: [] })),
      ordersService.getVendorStats().catch(() => null),
      productsService.getMyProducts({ page_size: 10 }).catch(() => ({ items: [] })),
    ]);

    return {
      stats: {
        totalProducts: storeStats?.total_products || myProducts?.total || 0,
        totalOrders: vendorStats?.total_orders || 0,
        pendingOrders: vendorStats?.pending_orders || 0,
        totalRevenue: vendorStats?.total_revenue || 0,
        monthlyRevenue: vendorStats?.monthly_revenue || 0,
        averageRating: storeStats?.average_rating || 0,
      },
      recentOrders: vendorOrders?.items || [],
      products: myProducts?.items || [],
    };
  },

  // Sales data for chart
  getSalesChart: async (period = 'month') => {
    // This would call a backend endpoint for chart data
    // For now, return mock data structure
    const response = await api.get('/orders/vendor/sales-chart', { params: { period } }).catch(() => null);
    return response?.data || generateMockChartData();
  },
};

// Generate mock chart data for demo
function generateMockChartData() {
  const days = ['1 يناير', '5 يناير', '10 يناير', '15 يناير', '20 يناير', '25 يناير', '30 يناير'];
  return days.map((day, index) => ({
    date: day,
    sales: Math.floor(Math.random() * 10000) + 2000,
  }));
}

export default api;
