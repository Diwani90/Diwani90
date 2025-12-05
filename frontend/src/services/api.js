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
  // طلب رمز التحقق OTP
  requestOTP: async (phone) => {
    const response = await api.post('/accounts/auth/request-otp', { phone_number: phone });
    return response.data;
  },

  // التحقق من OTP وتسجيل الدخول
  verifyOTP: async (phone, code) => {
    const response = await api.post('/accounts/auth/verify-otp', { phone_number: phone, code });
    return response.data;
  },

  // تسجيل مستخدم جديد
  register: async (userData) => {
    const response = await api.post('/accounts/auth/register', userData);
    return response.data;
  },

  // تجديد التوكن
  refreshToken: async (refreshToken) => {
    const response = await api.post('/accounts/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  },

  // الحصول على بيانات المستخدم الحالي
  getProfile: async () => {
    const response = await api.get('/accounts/me');
    return response.data;
  },

  // تحديث بيانات المستخدم
  updateProfile: async (data) => {
    const response = await api.patch('/accounts/me', data);
    return response.data;
  },

  // رفع الصورة الشخصية
  uploadAvatar: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/accounts/me/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // تحديث رمز FCM للإشعارات
  updateFCMToken: async (token) => {
    const response = await api.post('/accounts/me/fcm-token', { fcm_token: token });
    return response.data;
  },

  // إدارة العناوين
  getAddresses: async () => {
    const response = await api.get('/accounts/me/addresses');
    return response.data;
  },

  createAddress: async (data) => {
    const response = await api.post('/accounts/me/addresses', data);
    return response.data;
  },

  updateAddress: async (addressId, data) => {
    const response = await api.patch(`/accounts/me/addresses/${addressId}`, data);
    return response.data;
  },

  deleteAddress: async (addressId) => {
    const response = await api.delete(`/accounts/me/addresses/${addressId}`);
    return response.data;
  },

  // المحفظة
  getWalletBalance: async () => {
    const response = await api.get('/accounts/me/wallet');
    return response.data;
  },

  getWalletTransactions: async (limit = 20, offset = 0) => {
    const response = await api.get('/accounts/me/wallet/transactions', { params: { limit, offset } });
    return response.data;
  },
};

// ===================================
// Stores Services
// ===================================
export const storesService = {
  // === إدارة متاجري ===
  // قائمة المتاجر التي أملكها
  getMyStores: async () => {
    const response = await api.get('/stores/my-stores');
    return response.data;
  },

  // إنشاء متجر جديد
  createStore: async (data) => {
    const response = await api.post('/stores/my-stores', data);
    return response.data;
  },

  // تحديث متجري
  updateStore: async (storeId, data) => {
    const response = await api.patch(`/stores/my-stores/${storeId}`, data);
    return response.data;
  },

  // إحصائيات متجري
  getStoreStats: async (storeId) => {
    const response = await api.get(`/stores/my-stores/${storeId}/stats`);
    return response.data;
  },

  // رفع شعار المتجر
  uploadStoreLogo: async (storeId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post(`/stores/my-stores/${storeId}/logo`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // رفع صورة الغلاف
  uploadStoreCover: async (storeId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post(`/stores/my-stores/${storeId}/cover`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // تحديث ساعات العمل
  setWorkingHours: async (storeId, hours) => {
    const response = await api.post(`/stores/my-stores/${storeId}/working-hours`, hours);
    return response.data;
  },

  // إضافة صورة للمعرض
  addGalleryImage: async (storeId, file, caption = '') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('caption', caption);
    const response = await api.post(`/stores/my-stores/${storeId}/gallery`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // حذف صورة من المعرض
  deleteGalleryImage: async (storeId, imageId) => {
    const response = await api.delete(`/stores/my-stores/${storeId}/gallery/${imageId}`);
    return response.data;
  },

  // الرد على تقييم
  respondToReview: async (storeId, reviewId, responseText) => {
    const response = await api.post(`/stores/my-stores/${storeId}/reviews/${reviewId}/respond`, { response: responseText });
    return response.data;
  },

  // === تصفح المتاجر العامة ===
  // قائمة المتاجر
  listStores: async (params = {}) => {
    const response = await api.get('/stores/stores', { params });
    return response.data;
  },

  // المتاجر المميزة
  getFeaturedStores: async (limit = 10) => {
    const response = await api.get('/stores/stores/featured', { params: { limit } });
    return response.data;
  },

  // المتاجر القريبة
  getNearbyStores: async (latitude, longitude, radiusKm = 10, limit = 20) => {
    const response = await api.get('/stores/stores/nearby', {
      params: { latitude, longitude, radius_km: radiusKm, limit }
    });
    return response.data;
  },

  // تفاصيل متجر
  getStore: async (storeId) => {
    const response = await api.get(`/stores/stores/${storeId}`);
    return response.data;
  },

  // تفاصيل متجر بالمعرف النصي
  getStoreBySlug: async (slug) => {
    const response = await api.get(`/stores/stores/slug/${slug}`);
    return response.data;
  },

  // ساعات عمل المتجر
  getStoreWorkingHours: async (storeId) => {
    const response = await api.get(`/stores/stores/${storeId}/working-hours`);
    return response.data;
  },

  // معرض صور المتجر
  getStoreGallery: async (storeId) => {
    const response = await api.get(`/stores/stores/${storeId}/gallery`);
    return response.data;
  },

  // تقييمات المتجر
  getStoreReviews: async (storeId, page = 1, pageSize = 20) => {
    const response = await api.get(`/stores/stores/${storeId}/reviews`, { params: { page, page_size: pageSize } });
    return response.data;
  },

  // إضافة تقييم للمتجر
  createStoreReview: async (storeId, data) => {
    const response = await api.post(`/stores/stores/${storeId}/reviews`, data);
    return response.data;
  },

  // === الفئات ===
  // قائمة فئات المتاجر
  getCategories: async () => {
    const response = await api.get('/stores/categories');
    return response.data;
  },

  // الفئات المميزة
  getFeaturedCategories: async () => {
    const response = await api.get('/stores/categories/featured');
    return response.data;
  },

  // تفاصيل فئة
  getCategory: async (categoryId) => {
    const response = await api.get(`/stores/categories/${categoryId}`);
    return response.data;
  },

  // الفئات الفرعية
  getSubcategories: async (categoryId) => {
    const response = await api.get(`/stores/categories/${categoryId}/subcategories`);
    return response.data;
  },

  // === المفضلة ===
  // قائمة المتاجر المفضلة
  getFavoriteStores: async () => {
    const response = await api.get('/stores/favorites/stores');
    return response.data;
  },

  // إضافة للمفضلة
  addToFavorites: async (storeId) => {
    const response = await api.post(`/stores/stores/${storeId}/favorite`);
    return response.data;
  },

  // إزالة من المفضلة
  removeFromFavorites: async (storeId) => {
    const response = await api.delete(`/stores/stores/${storeId}/favorite`);
    return response.data;
  },
};

// ===================================
// Products Services
// ===================================
export const productsService = {
  // === تصفح المنتجات العامة ===
  // البحث في جميع المنتجات
  searchProducts: async (params = {}) => {
    const response = await api.get('/products/products', { params });
    return response.data;
  },

  // المنتجات المميزة
  getFeaturedProducts: async (limit = 20) => {
    const response = await api.get('/products/products/featured', { params: { limit } });
    return response.data;
  },

  // تفاصيل منتج
  getProduct: async (productId) => {
    const response = await api.get(`/products/products/${productId}`);
    return response.data;
  },

  // تفاصيل منتج بالمعرف النصي
  getProductBySlug: async (storeSlug, productSlug) => {
    const response = await api.get(`/products/products/slug/${storeSlug}/${productSlug}`);
    return response.data;
  },

  // منتجات متجر معين
  getStoreProducts: async (storeId, params = {}) => {
    const response = await api.get(`/products/stores/${storeId}/products`, { params });
    return response.data;
  },

  // فئات منتجات متجر
  getStoreCategories: async (storeId) => {
    const response = await api.get(`/products/stores/${storeId}/categories`);
    return response.data;
  },

  // تقييمات المنتج
  getProductReviews: async (productId, page = 1, pageSize = 20) => {
    const response = await api.get(`/products/products/${productId}/reviews`, { params: { page, page_size: pageSize } });
    return response.data;
  },

  // إضافة تقييم للمنتج
  createProductReview: async (productId, data) => {
    const response = await api.post(`/products/products/${productId}/reviews`, data);
    return response.data;
  },

  // === إدارة منتجاتي (للتجار) ===
  // قائمة منتجاتي
  getMyProducts: async (storeId, params = {}) => {
    const response = await api.get(`/products/my-stores/${storeId}/products`, { params });
    return response.data;
  },

  // تفاصيل منتجي
  getMyProduct: async (storeId, productId) => {
    const response = await api.get(`/products/my-stores/${storeId}/products/${productId}`);
    return response.data;
  },

  // إضافة منتج جديد
  createProduct: async (storeId, data) => {
    const response = await api.post(`/products/my-stores/${storeId}/products`, data);
    return response.data;
  },

  // تحديث منتج
  updateProduct: async (storeId, productId, data) => {
    const response = await api.patch(`/products/my-stores/${storeId}/products/${productId}`, data);
    return response.data;
  },

  // حذف منتج
  deleteProduct: async (storeId, productId) => {
    const response = await api.delete(`/products/my-stores/${storeId}/products/${productId}`);
    return response.data;
  },

  // رفع صورة المنتج الرئيسية
  uploadProductImage: async (storeId, productId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post(`/products/my-stores/${storeId}/products/${productId}/image`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // إضافة صورة إضافية للمنتج
  addProductImage: async (storeId, productId, file, altText = '') => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('alt_text', altText);
    const response = await api.post(`/products/my-stores/${storeId}/products/${productId}/images`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // حذف صورة المنتج
  deleteProductImage: async (storeId, productId, imageId) => {
    const response = await api.delete(`/products/my-stores/${storeId}/products/${productId}/images/${imageId}`);
    return response.data;
  },

  // تحديث المخزون
  updateStock: async (storeId, productId, quantity) => {
    const response = await api.post(`/products/my-stores/${storeId}/products/${productId}/stock`, null, { params: { quantity } });
    return response.data;
  },

  // المنتجات منخفضة المخزون
  getLowStockProducts: async (storeId) => {
    const response = await api.get(`/products/my-stores/${storeId}/products/low-stock`);
    return response.data;
  },

  // === إدارة خيارات المنتج (Variants) ===
  createVariant: async (storeId, productId, data) => {
    const response = await api.post(`/products/my-stores/${storeId}/products/${productId}/variants`, data);
    return response.data;
  },

  updateVariant: async (storeId, productId, variantId, data) => {
    const response = await api.patch(`/products/my-stores/${storeId}/products/${productId}/variants/${variantId}`, data);
    return response.data;
  },

  deleteVariant: async (storeId, productId, variantId) => {
    const response = await api.delete(`/products/my-stores/${storeId}/products/${productId}/variants/${variantId}`);
    return response.data;
  },

  // === إدارة الإضافات (Addons) ===
  createAddon: async (storeId, productId, data) => {
    const response = await api.post(`/products/my-stores/${storeId}/products/${productId}/addons`, data);
    return response.data;
  },

  deleteAddon: async (storeId, productId, addonId) => {
    const response = await api.delete(`/products/my-stores/${storeId}/products/${productId}/addons/${addonId}`);
    return response.data;
  },

  // === إدارة فئات المنتجات ===
  createCategory: async (storeId, data) => {
    const response = await api.post(`/products/my-stores/${storeId}/categories`, data);
    return response.data;
  },

  updateCategory: async (storeId, categoryId, data) => {
    const response = await api.patch(`/products/my-stores/${storeId}/categories/${categoryId}`, data);
    return response.data;
  },

  deleteCategory: async (storeId, categoryId) => {
    const response = await api.delete(`/products/my-stores/${storeId}/categories/${categoryId}`);
    return response.data;
  },

  uploadCategoryImage: async (storeId, categoryId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post(`/products/my-stores/${storeId}/categories/${categoryId}/image`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // تفاصيل فئة
  getCategory: async (categoryId) => {
    const response = await api.get(`/products/categories/${categoryId}`);
    return response.data;
  },

  // === المفضلة ===
  getFavoriteProducts: async () => {
    const response = await api.get('/products/favorites/products');
    return response.data;
  },

  addToFavorites: async (productId) => {
    const response = await api.post(`/products/products/${productId}/favorite`);
    return response.data;
  },

  removeFromFavorites: async (productId) => {
    const response = await api.delete(`/products/products/${productId}/favorite`);
    return response.data;
  },
};

// ===================================
// Orders Services
// ===================================
export const ordersService = {
  // === سلة التسوق ===
  // جميع سلاتي (سلة لكل متجر)
  getAllCarts: async () => {
    const response = await api.get('/orders/cart');
    return response.data;
  },

  // سلة متجر معين
  getCart: async (storeId) => {
    const response = await api.get(`/orders/cart/${storeId}`);
    return response.data;
  },

  // إضافة للسلة
  addToCart: async (productId, quantity, variantId = null, addons = [], notes = '') => {
    const response = await api.post('/orders/cart/items', {
      product_id: productId,
      quantity,
      variant_id: variantId,
      addons,
      notes
    });
    return response.data;
  },

  // تحديث عنصر السلة
  updateCartItem: async (itemId, quantity, notes = null) => {
    const response = await api.patch(`/orders/cart/items/${itemId}`, { quantity, notes });
    return response.data;
  },

  // إزالة من السلة
  removeFromCart: async (itemId) => {
    const response = await api.delete(`/orders/cart/items/${itemId}`);
    return response.data;
  },

  // تفريغ السلة
  clearCart: async (storeId) => {
    const response = await api.delete(`/orders/cart/${storeId}`);
    return response.data;
  },

  // تطبيق كوبون
  applyCoupon: async (storeId, code) => {
    const response = await api.post(`/orders/cart/${storeId}/coupon`, { code });
    return response.data;
  },

  // ملخص الدفع
  getCheckoutSummary: async (storeId, deliveryAddressId = null, couponCode = null, tipAmount = 0) => {
    const response = await api.get(`/orders/cart/${storeId}/checkout-summary`, {
      params: { delivery_address_id: deliveryAddressId, coupon_code: couponCode, tip_amount: tipAmount }
    });
    return response.data;
  },

  // === الطلبات ===
  // إنشاء طلب
  createOrder: async (data) => {
    const response = await api.post('/orders/orders', data);
    return response.data;
  },

  // قائمة طلباتي
  listOrders: async (params = {}) => {
    const response = await api.get('/orders/orders', { params });
    return response.data;
  },

  // الطلبات النشطة
  getActiveOrders: async () => {
    const response = await api.get('/orders/orders/active');
    return response.data;
  },

  // تفاصيل الطلب
  getOrder: async (orderId) => {
    const response = await api.get(`/orders/orders/${orderId}`);
    return response.data;
  },

  // تفاصيل الطلب برقم الطلب
  getOrderByNumber: async (orderNumber) => {
    const response = await api.get(`/orders/orders/number/${orderNumber}`);
    return response.data;
  },

  // سجل حالات الطلب
  getOrderHistory: async (orderId) => {
    const response = await api.get(`/orders/orders/${orderId}/history`);
    return response.data;
  },

  // إلغاء الطلب
  cancelOrder: async (orderId, reason) => {
    const response = await api.post(`/orders/orders/${orderId}/cancel`, { reason });
    return response.data;
  },

  // === إدارة طلبات المتجر (للتجار) ===
  // طلبات متجري
  getStoreOrders: async (storeId, params = {}) => {
    const response = await api.get(`/orders/my-stores/${storeId}/orders`, { params });
    return response.data;
  },

  // الطلبات الجديدة المنتظرة
  getPendingOrders: async (storeId) => {
    const response = await api.get(`/orders/my-stores/${storeId}/orders/pending`);
    return response.data;
  },

  // تفاصيل طلب المتجر
  getStoreOrder: async (storeId, orderId) => {
    const response = await api.get(`/orders/my-stores/${storeId}/orders/${orderId}`);
    return response.data;
  },

  // تحديث حالة الطلب
  updateOrderStatus: async (storeId, orderId, status, notes = '', estimatedTime = null) => {
    const response = await api.post(`/orders/my-stores/${storeId}/orders/${orderId}/status`, {
      status,
      notes,
      estimated_time: estimatedTime
    });
    return response.data;
  },

  // إحصائيات طلبات المتجر
  getOrdersStats: async (storeId) => {
    const response = await api.get(`/orders/my-stores/${storeId}/orders/stats`);
    return response.data;
  },
};

// ===================================
// Payments Services
// ===================================
export const paymentsService = {
  // === طرق الدفع ===
  // طرق الدفع المتاحة
  getPaymentMethods: async (amount = null) => {
    const response = await api.get('/payments/methods', { params: { amount } });
    return response.data;
  },

  // بوابات الدفع المفعلة
  getPaymentGateways: async () => {
    const response = await api.get('/payments/gateways');
    return response.data;
  },

  // === معالجة الدفع ===
  // بدء عملية الدفع
  initializePayment: async (orderId, paymentMethod, cardToken = null) => {
    const response = await api.post('/payments/initialize', {
      order_id: orderId,
      payment_method: paymentMethod,
      card_token: cardToken
    });
    return response.data;
  },

  // تفاصيل المعاملة
  getTransaction: async (transactionId) => {
    const response = await api.get(`/payments/transactions/${transactionId}`);
    return response.data;
  },

  // سجل المعاملات
  getTransactions: async (params = {}) => {
    const response = await api.get('/payments/transactions', { params });
    return response.data;
  },

  // طلب استرداد
  requestRefund: async (transactionId, amount = null) => {
    const response = await api.post('/payments/refund', { transaction_id: transactionId, amount });
    return response.data;
  },

  // === البطاقات المحفوظة ===
  getSavedCards: async () => {
    const response = await api.get('/payments/cards');
    return response.data;
  },

  saveCard: async (data) => {
    const response = await api.post('/payments/cards', data);
    return response.data;
  },

  setDefaultCard: async (cardId) => {
    const response = await api.post('/payments/cards/default', { card_id: cardId });
    return response.data;
  },

  deleteCard: async (cardId) => {
    const response = await api.delete(`/payments/cards/${cardId}`);
    return response.data;
  },

  // === التقسيط ===
  checkInstallmentEligibility: async (amount) => {
    const response = await api.post('/payments/installments/check', { amount });
    return response.data;
  },

  getInstallmentPlans: async () => {
    const response = await api.get('/payments/installments');
    return response.data;
  },

  getInstallmentPlan: async (planId) => {
    const response = await api.get(`/payments/installments/${planId}`);
    return response.data;
  },

  // === التاجر ===
  getVendorSummary: async () => {
    const response = await api.get('/payments/vendor/summary');
    return response.data;
  },

  getVendorPayouts: async (params = {}) => {
    const response = await api.get('/payments/vendor/payouts', { params });
    return response.data;
  },

  getVendorPayout: async (payoutId) => {
    const response = await api.get(`/payments/vendor/payouts/${payoutId}`);
    return response.data;
  },

  updateBankDetails: async (data) => {
    const response = await api.post('/payments/vendor/bank-details', data);
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
  // === للعملاء ===
  // مناطق التوصيل
  getZones: async (city = null) => {
    const response = await api.get('/delivery/zones', { params: { city } });
    return response.data;
  },

  // حساب رسوم التوصيل
  calculateFee: async (pickupLat, pickupLng, deliveryLat, deliveryLng) => {
    const response = await api.post('/delivery/calculate-fee', {
      pickup_latitude: pickupLat,
      pickup_longitude: pickupLng,
      delivery_latitude: deliveryLat,
      delivery_longitude: deliveryLng
    });
    return response.data;
  },

  // تتبع التوصيل
  trackDelivery: async (deliveryNumber) => {
    const response = await api.get(`/delivery/track/${deliveryNumber}`);
    return response.data;
  },

  // تقييم التوصيل
  rateDelivery: async (deliveryId, rating, feedback = '') => {
    const response = await api.post(`/delivery/deliveries/${deliveryId}/rate`, { rating, feedback });
    return response.data;
  },

  // === للسائقين ===
  // تحديث موقع السائق
  updateDriverLocation: async (latitude, longitude, speed = null, heading = null, accuracy = null) => {
    const response = await api.post('/delivery/driver/location', {
      latitude,
      longitude,
      speed,
      heading,
      accuracy
    });
    return response.data;
  },

  // الطلبات المتاحة للتوصيل
  getAvailableDeliveries: async () => {
    const response = await api.get('/delivery/driver/available-deliveries');
    return response.data;
  },

  // قبول طلب توصيل
  acceptDelivery: async (deliveryId) => {
    const response = await api.post('/delivery/driver/accept', { delivery_id: deliveryId });
    return response.data;
  },

  // رفض طلب توصيل
  rejectDelivery: async (deliveryId, reason = '') => {
    const response = await api.post('/delivery/driver/reject', { delivery_id: deliveryId, reason });
    return response.data;
  },

  // تأكيد استلام الطلب من المتجر
  pickupDelivery: async (deliveryId) => {
    const response = await api.post(`/delivery/driver/pickup/${deliveryId}`);
    return response.data;
  },

  // بدء التوصيل للعميل
  startDelivery: async (deliveryId) => {
    const response = await api.post(`/delivery/driver/start-delivery/${deliveryId}`);
    return response.data;
  },

  // إتمام التوصيل
  completeDelivery: async (deliveryId, photo = null, signature = null, notes = '') => {
    const formData = new FormData();
    if (photo) formData.append('photo', photo);
    if (signature) formData.append('signature', signature);
    formData.append('notes', notes);
    const response = await api.post(`/delivery/driver/complete/${deliveryId}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // التوصيل الحالي
  getCurrentDelivery: async () => {
    const response = await api.get('/delivery/driver/current');
    return response.data;
  },

  // سجل التوصيلات
  getDeliveryHistory: async (params = {}) => {
    const response = await api.get('/delivery/driver/history', { params });
    return response.data;
  },

  // === أرباح السائق ===
  getEarningsSummary: async () => {
    const response = await api.get('/delivery/driver/earnings');
    return response.data;
  },

  getEarningsHistory: async (params = {}) => {
    const response = await api.get('/delivery/driver/earnings/history', { params });
    return response.data;
  },

  // === جدول التوفر ===
  getAvailability: async () => {
    const response = await api.get('/delivery/driver/availability');
    return response.data;
  },

  setAvailability: async (schedules) => {
    const response = await api.post('/delivery/driver/availability', schedules);
    return response.data;
  },

  // تفعيل/إيقاف الاتصال
  goOnline: async () => {
    const response = await api.post('/delivery/driver/online');
    return response.data;
  },

  goOffline: async () => {
    const response = await api.post('/delivery/driver/offline');
    return response.data;
  },
};

// ===================================
// Dashboard Services
// ===================================
export const dashboardService = {
  /**
   * لوحة تحكم التاجر
   * يجمع البيانات من عدة مصادر لعرضها في لوحة التحكم
   * @param {string} storeId - معرف المتجر
   */
  getVendorDashboard: async (storeId) => {
    try {
      const [storeStats, storeOrders, ordersStats, myProducts] = await Promise.all([
        storesService.getStoreStats(storeId).catch(() => null),
        ordersService.getStoreOrders(storeId, { page_size: 5 }).catch(() => ({ items: [] })),
        ordersService.getOrdersStats(storeId).catch(() => null),
        productsService.getMyProducts(storeId, { page_size: 10 }).catch(() => ({ items: [] })),
      ]);

      return {
        stats: {
          totalProducts: storeStats?.products_count || myProducts?.total || 0,
          totalOrders: ordersStats?.month?.orders || 0,
          pendingOrders: ordersStats?.pending_count || 0,
          totalRevenue: ordersStats?.month?.revenue || 0,
          todayRevenue: ordersStats?.today?.revenue || 0,
          averageRating: storeStats?.rating || 0,
          ratingCount: storeStats?.rating_count || 0,
        },
        recentOrders: storeOrders?.items || [],
        products: myProducts?.items || [],
        ordersByStatus: ordersStats?.by_status || {},
      };
    } catch (error) {
      console.error('Error fetching vendor dashboard:', error);
      return {
        stats: {},
        recentOrders: [],
        products: [],
        ordersByStatus: {},
      };
    }
  },

  /**
   * الحصول على قائمة المتاجر مع أول متجر كافتراضي
   */
  getMyStoresWithDefault: async () => {
    try {
      const stores = await storesService.getMyStores();
      const defaultStore = stores?.[0] || null;
      return {
        stores,
        defaultStore,
      };
    } catch (error) {
      return { stores: [], defaultStore: null };
    }
  },

  /**
   * ملخص المدفوعات للتاجر
   */
  getPaymentsSummary: async () => {
    try {
      const summary = await paymentsService.getVendorSummary();
      return summary;
    } catch (error) {
      return null;
    }
  },

  /**
   * بيانات الرسم البياني للمبيعات
   * @param {string} storeId - معرف المتجر
   * @param {string} period - الفترة (week, month, year)
   */
  getSalesChart: async (storeId, period = 'month') => {
    // TODO: إضافة endpoint للـ chart في الـ Backend
    // حالياً نعيد بيانات تجريبية
    return generateMockChartData(period);
  },
};

/**
 * توليد بيانات تجريبية للرسم البياني
 */
function generateMockChartData(period = 'month') {
  const arabicMonths = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر'];
  const currentMonth = new Date().getMonth();

  let days = [];
  if (period === 'week') {
    days = ['السبت', 'الأحد', 'الاثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة'];
  } else if (period === 'month') {
    days = ['1', '5', '10', '15', '20', '25', '30'].map(d => `${d} ${arabicMonths[currentMonth]}`);
  } else {
    days = arabicMonths;
  }

  return days.map((day) => ({
    date: day,
    sales: Math.floor(Math.random() * 10000) + 2000,
    orders: Math.floor(Math.random() * 50) + 5,
  }));
}

export default api;
