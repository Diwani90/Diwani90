import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../App';
import { 
  HomeIcon, 
  BuildingStorefrontIcon, 
  UserGroupIcon, 
  ShoppingCartIcon, 
  ChatBubbleLeftRightIcon,
  Cog6ToothIcon,
  UserCircleIcon,
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  XMarkIcon,
  ClipboardDocumentListIcon
} from '@heroicons/react/24/outline';

const Navigation = () => {
  const { isAuthenticated, user, logout } = useAuth();
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
    setIsMobileMenuOpen(false);
  };

  const navItems = [
    { name: 'الرئيسية', href: '/', icon: HomeIcon, public: true },
    { name: 'المنتجات', href: '/products', icon: BuildingStorefrontIcon, public: true },
    { name: 'الموردين', href: '/suppliers', icon: UserGroupIcon, public: true },
  ];

  const customerItems = [
    { name: 'لوحة التحكم', href: '/customer/dashboard', icon: Cog6ToothIcon },
    { name: 'السلة', href: '/cart', icon: ShoppingCartIcon },
    { name: 'الطلبات', href: '/orders', icon: ClipboardDocumentListIcon },
    { name: 'المحادثات', href: '/chat', icon: ChatBubbleLeftRightIcon },
  ];

  const supplierItems = [
    { name: 'لوحة التحكم', href: '/supplier/dashboard', icon: Cog6ToothIcon },
    { name: 'الطلبات', href: '/orders', icon: ClipboardDocumentListIcon },
    { name: 'المحادثات', href: '/chat', icon: ChatBubbleLeftRightIcon },
  ];

  const driverItems = [
    { name: 'لوحة التحكم', href: '/driver/dashboard', icon: Cog6ToothIcon },
    { name: 'سجل التوصيلات', href: '/driver/history', icon: ClipboardDocumentListIcon },
    { name: 'المحادثات', href: '/chat', icon: ChatBubbleLeftRightIcon },
  ];

  const getUserSpecificItems = () => {
    if (!isAuthenticated) return [];
    if (user?.role === 'customer') return customerItems;
    if (user?.role === 'supplier' || user?.role === 'vendor') return supplierItems;
    if (user?.role === 'driver') return driverItems;
    return [];
  };

  return (
    <nav className="bg-white shadow-lg border-b-2 border-blue-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2 space-x-reverse">
            <div className="h-10 w-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
              <BuildingStorefrontIcon className="h-6 w-6 text-white" />
            </div>
            <div className="text-right">
              <h1 className="text-xl font-bold text-gray-900">منصة البناء</h1>
              <p className="text-xs text-gray-500">مواد البناء السعودية</p>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8 space-x-reverse">
            {/* Public Navigation Items */}
            {navItems.filter(item => item.public || isAuthenticated).map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className="flex items-center space-x-2 space-x-reverse text-gray-700 hover:text-blue-600 transition-colors duration-200 px-3 py-2 rounded-lg hover:bg-blue-50"
              >
                <item.icon className="h-5 w-5" />
                <span className="font-medium">{item.name}</span>
              </Link>
            ))}

            {/* User Specific Items */}
            {getUserSpecificItems().map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className="flex items-center space-x-2 space-x-reverse text-gray-700 hover:text-blue-600 transition-colors duration-200 px-3 py-2 rounded-lg hover:bg-blue-50"
              >
                <item.icon className="h-5 w-5" />
                <span className="font-medium">{item.name}</span>
              </Link>
            ))}

            {/* Auth Section */}
            {isAuthenticated ? (
              <div className="flex items-center space-x-4 space-x-reverse">
                <div className="flex items-center space-x-2 space-x-reverse text-gray-700">
                  <UserCircleIcon className="h-6 w-6" />
                  <span className="font-medium">{user?.full_name}</span>
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                    {user?.role === 'customer' ? 'عميل' : user?.role === 'supplier' ? 'مورد' : 'إدارة'}
                  </span>
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-2 space-x-reverse text-red-600 hover:text-red-700 transition-colors duration-200 px-3 py-2 rounded-lg hover:bg-red-50"
                >
                  <ArrowRightOnRectangleIcon className="h-5 w-5" />
                  <span className="font-medium">تسجيل الخروج</span>
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-4 space-x-reverse">
                <Link
                  to="/login"
                  className="text-gray-700 hover:text-blue-600 font-medium transition-colors duration-200"
                >
                  تسجيل الدخول
                </Link>
                <Link
                  to="/register"
                  className="btn-primary text-sm"
                >
                  إنشاء حساب
                </Link>
              </div>
            )}
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="text-gray-700 hover:text-gray-900 focus:outline-none focus:text-gray-900"
            >
              {isMobileMenuOpen ? (
                <XMarkIcon className="h-6 w-6" />
              ) : (
                <Bars3Icon className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMobileMenuOpen && (
          <div className="md:hidden">
            <div className="px-2 pt-2 pb-3 space-y-1 bg-gray-50 rounded-lg mt-2">
              {/* Public Navigation Items */}
              {navItems.filter(item => item.public || isAuthenticated).map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex items-center space-x-3 space-x-reverse text-gray-700 hover:text-blue-600 hover:bg-white px-3 py-2 rounded-lg transition-colors duration-200"
                >
                  <item.icon className="h-5 w-5" />
                  <span className="font-medium">{item.name}</span>
                </Link>
              ))}

              {/* User Specific Items */}
              {getUserSpecificItems().map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="flex items-center space-x-3 space-x-reverse text-gray-700 hover:text-blue-600 hover:bg-white px-3 py-2 rounded-lg transition-colors duration-200"
                >
                  <item.icon className="h-5 w-5" />
                  <span className="font-medium">{item.name}</span>
                </Link>
              ))}

              {/* Auth Section */}
              {isAuthenticated ? (
                <div className="border-t pt-4 mt-4">
                  <div className="flex items-center space-x-3 space-x-reverse text-gray-700 px-3 py-2">
                    <UserCircleIcon className="h-6 w-6" />
                    <div>
                      <span className="font-medium block">{user?.full_name}</span>
                      <span className="text-xs text-gray-500">
                        {user?.role === 'customer' ? 'عميل' : user?.role === 'supplier' ? 'مورد' : 'إدارة'}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center space-x-3 space-x-reverse text-red-600 hover:text-red-700 hover:bg-red-50 px-3 py-2 rounded-lg transition-colors duration-200 mt-2"
                  >
                    <ArrowRightOnRectangleIcon className="h-5 w-5" />
                    <span className="font-medium">تسجيل الخروج</span>
                  </button>
                </div>
              ) : (
                <div className="border-t pt-4 mt-4 space-y-2">
                  <Link
                    to="/login"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className="block w-full text-center py-2 px-4 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors duration-200"
                  >
                    تسجيل الدخول
                  </Link>
                  <Link
                    to="/register"
                    onClick={() => setIsMobileMenuOpen(false)}
                    className="block w-full text-center btn-primary"
                  >
                    إنشاء حساب
                  </Link>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navigation;