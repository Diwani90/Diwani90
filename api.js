import axios from 'axios';

const BASE_URL = 'https://e5h6i7c0jpq1.manus.space/api';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.message);
    return Promise.reject(error);
  }
);

export const apiService = {
  // Categories
  getCategories: () => api.get('/categories'),
  getMainCategories: () => api.get('/categories/main'),
  getCategory: (id) => api.get(`/categories/${id}`),

  // Suppliers
  getSuppliers: (params = {}) => api.get('/suppliers', { params }),
  getFeaturedSuppliers: () => api.get('/suppliers/featured'),
  getSupplier: (id) => api.get(`/suppliers/${id}`),

  // Products
  getProducts: (params = {}) => api.get('/products', { params }),
  getFeaturedProducts: () => api.get('/products/featured'),
  searchProducts: (params = {}) => api.get('/products/search', { params }),
  getProduct: (id) => api.get(`/products/${id}`),

  // Orders
  createOrder: (orderData) => api.post('/orders', orderData),
  getOrders: (params = {}) => api.get('/orders', { params }),
  getOrder: (id) => api.get(`/orders/${id}`),
  updateOrderStatus: (id, status) => api.put(`/orders/${id}/status`, { status }),
};

export default api;

