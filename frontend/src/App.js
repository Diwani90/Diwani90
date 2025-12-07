import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import './App.css';

// Import components (we'll create these)
import HomePage from './components/HomePage';
import LoginPage from './components/auth/LoginPage';
import RegisterPage from './components/auth/RegisterPage';
import ForgotPasswordPage from './components/auth/ForgotPasswordPage';
import CustomerDashboard from './components/customer/CustomerDashboard';
import SupplierDashboard from './components/supplier/SupplierDashboard';
import ProductCatalog from './components/product/ProductCatalog';
import ProductDetail from './components/product/ProductDetail';
import CartPage from './components/cart/CartPage';
import CheckoutPage from './components/checkout/CheckoutPage';
import OrdersPage from './components/orders/OrdersPage';
import ChatPage from './components/chat/ChatPage';
import SuppliersPage from './components/suppliers/SuppliersPage';
import TermsPage from './components/pages/TermsPage';
import PrivacyPage from './components/pages/PrivacyPage';
import Navigation from './components/layout/Navigation';
import { ToastProvider } from './components/ui/toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api/v1`;

// Configure axios defaults
axios.defaults.baseURL = API;

// Auth Context
const AuthContext = createContext();

const authReducer = (state, action) => {
  switch (action.type) {
    case 'LOGIN_SUCCESS':
      localStorage.setItem('token', action.payload.access_token);
      localStorage.setItem('user', JSON.stringify(action.payload.user));
      axios.defaults.headers.common['Authorization'] = `Bearer ${action.payload.access_token}`;
      return {
        ...state,
        isAuthenticated: true,
        user: action.payload.user,
        token: action.payload.access_token,
        loading: false
      };
    case 'LOGOUT':
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      delete axios.defaults.headers.common['Authorization'];
      return {
        ...state,
        isAuthenticated: false,
        user: null,
        token: null,
        loading: false
      };
    case 'SET_LOADING':
      return {
        ...state,
        loading: action.payload
      };
    case 'LOAD_USER':
      const token = localStorage.getItem('token');
      const user = localStorage.getItem('user');
      if (token && user) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        return {
          ...state,
          isAuthenticated: true,
          user: JSON.parse(user),
          token: token,
          loading: false
        };
      }
      return {
        ...state,
        loading: false
      };
    default:
      return state;
  }
};

export const AuthProvider = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, {
    isAuthenticated: false,
    user: null,
    token: null,
    loading: true
  });

  useEffect(() => {
    dispatch({ type: 'LOAD_USER' });
  }, []);

  const login = async (authData) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      // إذا كانت البيانات تحتوي على token مباشرة (من صفحة تسجيل الدخول الجديدة)
      if (authData.access_token) {
        dispatch({ type: 'LOGIN_SUCCESS', payload: authData });
        return { success: true };
      }
      // للتوافق مع الطريقة القديمة (إذا احتجنا)
      const response = await axios.post('/users/auth/login', authData);
      dispatch({ type: 'LOGIN_SUCCESS', payload: response.data });
      return { success: true };
    } catch (error) {
      dispatch({ type: 'SET_LOADING', payload: false });
      return {
        success: false,
        error: error.response?.data?.detail || 'حدث خطأ في تسجيل الدخول'
      };
    }
  };

  const register = async (userData) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      // Note: Registration is now handled directly in RegisterPage with phone+OTP
      // This is kept for legacy compatibility
      const response = await axios.post('/users/auth/register/customer', userData);
      dispatch({ type: 'LOGIN_SUCCESS', payload: response.data });
      return { success: true };
    } catch (error) {
      dispatch({ type: 'SET_LOADING', payload: false });
      return { 
        success: false, 
        error: error.response?.data?.detail || 'حدث خطأ في التسجيل' 
      };
    }
  };

  const logout = () => {
    dispatch({ type: 'LOGOUT' });
  };

  return (
    <AuthContext.Provider value={{
      ...state,
      login,
      register,
      logout
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Protected Route Component
const ProtectedRoute = ({ children, allowedRoles = [] }) => {
  const { isAuthenticated, user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return children;
};

function App() {
  return (
    <div className="App min-h-screen bg-gray-50" dir="rtl">
      <BrowserRouter>
        <AuthProvider>
          <ToastProvider>
            <div className="flex flex-col min-h-screen">
              <Navigation />
              <main className="flex-1">
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/login" element={<LoginPage />} />
                  <Route path="/register" element={<RegisterPage />} />
                  <Route path="/forgot-password" element={<ForgotPasswordPage />} />
                  <Route path="/terms" element={<TermsPage />} />
                  <Route path="/privacy" element={<PrivacyPage />} />
                  <Route path="/products" element={<ProductCatalog />} />
                  <Route path="/products/:id" element={<ProductDetail />} />
                  <Route path="/suppliers" element={<SuppliersPage />} />
                  
                  {/* Customer Routes */}
                  <Route path="/customer/dashboard" element={
                    <ProtectedRoute allowedRoles={['customer']}>
                      <CustomerDashboard />
                    </ProtectedRoute>
                  } />
                  <Route path="/cart" element={
                    <ProtectedRoute allowedRoles={['customer']}>
                      <CartPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/checkout" element={
                    <ProtectedRoute allowedRoles={['customer']}>
                      <CheckoutPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/orders" element={
                    <ProtectedRoute allowedRoles={['customer', 'supplier']}>
                      <OrdersPage />
                    </ProtectedRoute>
                  } />
                  
                  {/* Supplier Routes */}
                  <Route path="/supplier/dashboard" element={
                    <ProtectedRoute allowedRoles={['supplier']}>
                      <SupplierDashboard />
                    </ProtectedRoute>
                  } />
                  
                  {/* Chat */}
                  <Route path="/chat" element={
                    <ProtectedRoute>
                      <ChatPage />
                    </ProtectedRoute>
                  } />
                  <Route path="/chat/:conversationId" element={
                    <ProtectedRoute>
                      <ChatPage />
                    </ProtectedRoute>
                  } />
                  
                  {/* Redirect based on user role */}
                  <Route path="/dashboard" element={
                    <ProtectedRoute>
                      <DashboardRedirect />
                    </ProtectedRoute>
                  } />
                </Routes>
              </main>
            </div>
          </ToastProvider>
        </AuthProvider>
      </BrowserRouter>
    </div>
  );
}

// Component to redirect to appropriate dashboard
const DashboardRedirect = () => {
  const { user } = useAuth();
  
  if (user.role === 'customer') {
    return <Navigate to="/customer/dashboard" replace />;
  } else if (user.role === 'supplier') {
    return <Navigate to="/supplier/dashboard" replace />;
  } else {
    return <Navigate to="/" replace />;
  }
};

export default App;