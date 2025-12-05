/**
 * ===================================
 * منصة ديواني - Dashboard Layout
 * Professional sidebar layout
 * ===================================
 */

import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../App';
import {
  HomeIcon,
  ShoppingBagIcon,
  ClipboardDocumentListIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  BellIcon,
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  XMarkIcon,
  UserCircleIcon,
  BuildingStorefrontIcon,
  TruckIcon,
  CreditCardIcon,
} from '@heroicons/react/24/outline';

const DashboardLayout = ({ children }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notificationCount] = useState(3); // TODO: Get from API

  // Navigation items for vendor
  const vendorNavItems = [
    { name: 'لوحة التحكم', href: '/dashboard', icon: HomeIcon },
    { name: 'المنتجات', href: '/dashboard/products', icon: ShoppingBagIcon },
    { name: 'الطلبات', href: '/dashboard/orders', icon: ClipboardDocumentListIcon },
    { name: 'التوصيل', href: '/dashboard/delivery', icon: TruckIcon },
    { name: 'المدفوعات', href: '/dashboard/payments', icon: CreditCardIcon },
    { name: 'التقارير', href: '/dashboard/reports', icon: ChartBarIcon },
    { name: 'الإعدادات', href: '/dashboard/settings', icon: Cog6ToothIcon },
  ];

  const isActive = (href) => {
    if (href === '/dashboard') {
      return location.pathname === '/dashboard';
    }
    return location.pathname.startsWith(href);
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 right-0 z-50 w-64 bg-slate-800 transform transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'
        }`}
      >
        {/* Logo */}
        <div className="flex items-center justify-between h-16 px-6 border-b border-slate-700">
          <Link to="/dashboard" className="flex items-center">
            <BuildingStorefrontIcon className="h-8 w-8 text-blue-400" />
            <span className="mr-3 text-xl font-bold text-white">الموارد</span>
          </Link>
          <button
            className="lg:hidden text-white hover:text-gray-300"
            onClick={() => setSidebarOpen(false)}
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="mt-6 px-4">
          {vendorNavItems.map((item) => {
            const active = isActive(item.href);
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center px-4 py-3 mb-2 rounded-lg transition-colors duration-200 ${
                  active
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-slate-700 hover:text-white'
                }`}
                onClick={() => setSidebarOpen(false)}
              >
                <item.icon className="h-5 w-5" />
                <span className="mr-3 font-medium">{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* User section at bottom */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-700">
          <div className="flex items-center mb-4">
            <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
              <UserCircleIcon className="h-6 w-6 text-white" />
            </div>
            <div className="mr-3">
              <p className="text-sm font-medium text-white">{user?.full_name || 'المستخدم'}</p>
              <p className="text-xs text-gray-400">{user?.email || 'مورد'}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center w-full px-4 py-2 text-gray-300 hover:bg-slate-700 hover:text-white rounded-lg transition-colors duration-200"
          >
            <ArrowRightOnRectangleIcon className="h-5 w-5" />
            <span className="mr-3">تسجيل الخروج</span>
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pr-64">
        {/* Top header */}
        <header className="sticky top-0 z-30 bg-white shadow-sm">
          <div className="flex items-center justify-between h-16 px-4 lg:px-8">
            {/* Mobile menu button */}
            <button
              className="lg:hidden p-2 text-gray-600 hover:text-gray-900"
              onClick={() => setSidebarOpen(true)}
            >
              <Bars3Icon className="h-6 w-6" />
            </button>

            {/* Page title (dynamic) */}
            <h1 className="text-xl font-bold text-gray-900 hidden lg:block">
              {getPageTitle(location.pathname)}
            </h1>

            {/* Right side actions */}
            <div className="flex items-center gap-4">
              {/* Notifications */}
              <button className="relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg">
                <BellIcon className="h-6 w-6" />
                {notificationCount > 0 && (
                  <span className="absolute -top-1 -left-1 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
                    {notificationCount}
                  </span>
                )}
              </button>

              {/* User menu (desktop) */}
              <div className="hidden lg:flex items-center">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-bold">
                    {user?.full_name?.charAt(0) || 'م'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 lg:p-8">{children}</main>
      </div>
    </div>
  );
};

// Helper function to get page title
function getPageTitle(pathname) {
  const titles = {
    '/dashboard': 'لوحة التحكم',
    '/dashboard/products': 'المنتجات',
    '/dashboard/orders': 'الطلبات',
    '/dashboard/delivery': 'التوصيل',
    '/dashboard/payments': 'المدفوعات',
    '/dashboard/reports': 'التقارير',
    '/dashboard/settings': 'الإعدادات',
  };
  return titles[pathname] || 'لوحة التحكم';
}

export default DashboardLayout;
