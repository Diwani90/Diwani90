import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../App';
import { useToast } from '../ui/toast';
import axios from 'axios';
import {
  UsersIcon,
  BuildingStorefrontIcon,
  ShoppingCartIcon,
  CurrencyDollarIcon,
  TruckIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  ChevronLeftIcon
} from '@heroicons/react/24/outline';

const AdminDashboard = () => {
  const { user } = useAuth();
  const { toast } = useToast();

  const [stats, setStats] = useState(null);
  const [recentOrders, setRecentOrders] = useState([]);
  const [pendingVendors, setPendingVendors] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      // جلب الإحصائيات من platform/stats
      const statsResponse = await axios.get('/platform/stats/');

      // محاولة جلب الطلبات الأخيرة
      let orders = [];
      try {
        const ordersResponse = await axios.get('/orders/orders?limit=10');
        orders = ordersResponse.data?.items || ordersResponse.data || [];
      } catch {
        // تجاهل الخطأ إذا لم يكن هناك صلاحية
      }

      // محاولة جلب البائعين المعلقين
      let vendors = [];
      try {
        const vendorsResponse = await axios.get('/stores/stores?status=pending&limit=5');
        vendors = vendorsResponse.data?.items || vendorsResponse.data || [];
      } catch {
        // تجاهل الخطأ إذا لم يكن هناك صلاحية
      }

      setStats(statsResponse.data);
      setRecentOrders(orders);
      setPendingVendors(vendors);
    } catch (error) {
      console.error('Error fetching admin data:', error);
      toast.error('خطأ', 'حدث خطأ في تحميل البيانات');
    } finally {
      setLoading(false);
    }
  };

  const approveVendor = async (vendorId) => {
    try {
      await axios.post(`/stores/stores/${vendorId}/verify`, {
        is_verified: true
      });

      setPendingVendors(prev => prev.filter(v => v.id !== vendorId));
      toast.success('تم بنجاح', 'تم تفعيل البائع');
    } catch (error) {
      console.error('Error approving vendor:', error);
      toast.error('خطأ', 'حدث خطأ في تفعيل البائع');
    }
  };

  const getOrderStatusLabel = (status) => {
    const labels = {
      'pending': 'بانتظار',
      'confirmed': 'مؤكد',
      'processing': 'قيد التجهيز',
      'shipped': 'تم الشحن',
      'delivered': 'تم التوصيل',
      'completed': 'مكتمل',
      'cancelled': 'ملغي'
    };
    return labels[status] || status;
  };

  const getOrderStatusColor = (status) => {
    const colors = {
      'pending': 'bg-yellow-100 text-yellow-800',
      'confirmed': 'bg-blue-100 text-blue-800',
      'processing': 'bg-purple-100 text-purple-800',
      'shipped': 'bg-indigo-100 text-indigo-800',
      'delivered': 'bg-green-100 text-green-800',
      'completed': 'bg-green-500 text-white',
      'cancelled': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-4 py-6 text-white">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl font-bold">لوحة تحكم الإدارة</h1>
          <p className="text-sm opacity-90 mt-1">مرحباً {user?.full_name || 'مدير'}</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-xl shadow-sm p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">المستخدمين</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats?.total_users || 0}
                </p>
              </div>
              <div className="bg-blue-100 p-3 rounded-lg">
                <UsersIcon className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">الموردين</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats?.total_suppliers || 0}
                </p>
              </div>
              <div className="bg-green-100 p-3 rounded-lg">
                <BuildingStorefrontIcon className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">المنتجات</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats?.total_products || 0}
                </p>
              </div>
              <div className="bg-purple-100 p-3 rounded-lg">
                <ShoppingCartIcon className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">الطلبات</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats?.total_orders || 0}
                </p>
              </div>
              <div className="bg-yellow-100 p-3 rounded-lg">
                <ChartBarIcon className="h-6 w-6 text-yellow-600" />
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Pending Vendors */}
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-lg font-semibold text-gray-900">بائعين بانتظار التفعيل</h2>
              <Link
                to="/admin/vendors"
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                عرض الكل
              </Link>
            </div>

            {pendingVendors.length > 0 ? (
              <div className="divide-y divide-gray-200">
                {pendingVendors.map((vendor) => (
                  <div key={vendor.id} className="p-4 flex justify-between items-center">
                    <div>
                      <h3 className="font-medium text-gray-900">{vendor.name}</h3>
                      <p className="text-sm text-gray-500">{vendor.city}</p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => approveVendor(vendor.id)}
                        className="bg-green-100 text-green-700 px-3 py-1 rounded-lg text-sm hover:bg-green-200 transition-colors"
                      >
                        تفعيل
                      </button>
                      <button
                        className="bg-gray-100 text-gray-700 px-3 py-1 rounded-lg text-sm hover:bg-gray-200 transition-colors"
                      >
                        مراجعة
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center">
                <CheckCircleIcon className="h-12 w-12 text-green-400 mx-auto mb-4" />
                <p className="text-gray-500">لا يوجد بائعين بانتظار التفعيل</p>
              </div>
            )}
          </div>

          {/* Recent Orders */}
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-lg font-semibold text-gray-900">آخر الطلبات</h2>
              <Link
                to="/admin/orders"
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                عرض الكل
              </Link>
            </div>

            {recentOrders.length > 0 ? (
              <div className="divide-y divide-gray-200">
                {recentOrders.slice(0, 5).map((order) => (
                  <div key={order.id} className="p-4">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-medium text-gray-900">
                          #{order.order_number || order.id?.slice(0, 8)}
                        </h3>
                        <p className="text-sm text-gray-500">
                          {new Date(order.created_at).toLocaleDateString('ar-SA')}
                        </p>
                      </div>
                      <div className="text-left">
                        <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getOrderStatusColor(order.status)}`}>
                          {getOrderStatusLabel(order.status)}
                        </span>
                        <p className="text-sm font-bold text-gray-900 mt-1">
                          {order.total_amount || 0} ر.س
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center">
                <ClockIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">لا توجد طلبات حديثة</p>
              </div>
            )}
          </div>
        </div>

        {/* Quick Links */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
          <Link
            to="/admin/users"
            className="bg-white rounded-xl shadow-sm p-4 flex items-center justify-between hover:shadow-md transition-shadow"
          >
            <div className="flex items-center gap-3">
              <div className="bg-blue-100 p-2 rounded-lg">
                <UsersIcon className="h-5 w-5 text-blue-600" />
              </div>
              <span className="font-medium text-gray-900">إدارة المستخدمين</span>
            </div>
            <ChevronLeftIcon className="h-5 w-5 text-gray-400" />
          </Link>

          <Link
            to="/admin/vendors"
            className="bg-white rounded-xl shadow-sm p-4 flex items-center justify-between hover:shadow-md transition-shadow"
          >
            <div className="flex items-center gap-3">
              <div className="bg-green-100 p-2 rounded-lg">
                <BuildingStorefrontIcon className="h-5 w-5 text-green-600" />
              </div>
              <span className="font-medium text-gray-900">إدارة البائعين</span>
            </div>
            <ChevronLeftIcon className="h-5 w-5 text-gray-400" />
          </Link>

          <Link
            to="/admin/orders"
            className="bg-white rounded-xl shadow-sm p-4 flex items-center justify-between hover:shadow-md transition-shadow"
          >
            <div className="flex items-center gap-3">
              <div className="bg-purple-100 p-2 rounded-lg">
                <ShoppingCartIcon className="h-5 w-5 text-purple-600" />
              </div>
              <span className="font-medium text-gray-900">إدارة الطلبات</span>
            </div>
            <ChevronLeftIcon className="h-5 w-5 text-gray-400" />
          </Link>

          <Link
            to="/admin/finance"
            className="bg-white rounded-xl shadow-sm p-4 flex items-center justify-between hover:shadow-md transition-shadow"
          >
            <div className="flex items-center gap-3">
              <div className="bg-yellow-100 p-2 rounded-lg">
                <CurrencyDollarIcon className="h-5 w-5 text-yellow-600" />
              </div>
              <span className="font-medium text-gray-900">التقارير المالية</span>
            </div>
            <ChevronLeftIcon className="h-5 w-5 text-gray-400" />
          </Link>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
