/**
 * ===================================
 * منصة ديواني - Dashboard Home Page
 * Main vendor dashboard with all components
 * ===================================
 */

import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../App';
import { dashboardService, productsService } from '../../services/api';
import DashboardLayout from './DashboardLayout';
import StatsCards from './StatsCards';
import SalesChart from './SalesChart';
import RecentOrders from './RecentOrders';
import ProductsManagement from './ProductsManagement';
import { useToast } from '../ui/toast';

const DashboardHome = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({});
  const [recentOrders, setRecentOrders] = useState([]);
  const [products, setProducts] = useState([]);
  const [chartData, setChartData] = useState([]);

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      const data = await dashboardService.getVendorDashboard();

      setStats(data.stats);
      setRecentOrders(data.recentOrders);
      setProducts(data.products);

      // Fetch chart data
      const salesData = await dashboardService.getSalesChart('month');
      setChartData(salesData);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast?.error?.('خطأ', 'حدث خطأ في تحميل بيانات لوحة التحكم');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const handleDeleteProduct = async (productId) => {
    if (!window.confirm('هل أنت متأكد من حذف هذا المنتج؟')) {
      return;
    }

    try {
      await productsService.deleteProduct(productId);
      setProducts(products.filter((p) => p.id !== productId));
      toast?.success?.('تم الحذف', 'تم حذف المنتج بنجاح');
    } catch (error) {
      console.error('Error deleting product:', error);
      toast?.error?.('خطأ', 'حدث خطأ في حذف المنتج');
    }
  };

  return (
    <DashboardLayout>
      {/* Welcome Header */}
      <div className="mb-8">
        <h1 className="text-2xl lg:text-3xl font-bold text-gray-900">
          مرحباً، {user?.full_name || 'المورد'}
        </h1>
        <p className="text-gray-500 mt-1">
          نظرة عامة على نشاطك التجاري اليوم
        </p>
      </div>

      {/* Stats Cards */}
      <StatsCards stats={stats} loading={loading} />

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Sales Chart */}
        <div className="lg:col-span-1">
          <SalesChart data={chartData} loading={loading} />
        </div>

        {/* Recent Orders */}
        <div className="lg:col-span-1">
          <RecentOrders orders={recentOrders} loading={loading} />
        </div>
      </div>

      {/* Products Management - Full Width */}
      <div className="mb-8">
        <ProductsManagement
          products={products}
          loading={loading}
          onDelete={handleDeleteProduct}
        />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <QuickActionCard
          title="إضافة منتج جديد"
          description="أضف منتجات جديدة لمتجرك"
          icon="📦"
          href="/dashboard/products/new"
        />
        <QuickActionCard
          title="عرض جميع الطلبات"
          description="إدارة ومتابعة طلباتك"
          icon="📋"
          href="/dashboard/orders"
        />
        <QuickActionCard
          title="إعدادات المتجر"
          description="تخصيص إعدادات متجرك"
          icon="⚙️"
          href="/dashboard/settings"
        />
      </div>
    </DashboardLayout>
  );
};

// Quick Action Card Component
const QuickActionCard = ({ title, description, icon, href }) => {
  return (
    <a
      href={href}
      className="block p-6 bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow duration-200 group"
    >
      <div className="text-3xl mb-4">{icon}</div>
      <h3 className="text-lg font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
        {title}
      </h3>
      <p className="text-sm text-gray-500 mt-1">{description}</p>
    </a>
  );
};

export default DashboardHome;
