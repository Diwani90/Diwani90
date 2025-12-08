import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../App';
import { useToast } from '../ui/toast';
import axios from 'axios';
import {
  ShoppingCartIcon,
  ClipboardDocumentListIcon,
  ChatBubbleLeftRightIcon,
  StarIcon,
  TruckIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

const CustomerDashboard = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [stats, setStats] = useState({});
  const [recentOrders, setRecentOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsResponse, ordersResponse] = await Promise.all([
        axios.get('/users/me/stats'),
        axios.get('/orders/orders?limit=5')
      ]);

      setStats(statsResponse.data || {});
      setRecentOrders(ordersResponse.data?.items || ordersResponse.data || []);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast.error('خطأ', 'حدث خطأ في تحميل بيانات لوحة التحكم');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">مرحباً، {user?.full_name}</h1>
          <p className="text-gray-600 mt-2">لوحة تحكم العميل</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="card">
            <div className="card-body">
              <div className="flex items-center">
                <div className="bg-blue-100 p-3 rounded-lg">
                  <ClipboardDocumentListIcon className="h-6 w-6 text-blue-600" />
                </div>
                <div className="mr-4">
                  <p className="text-sm text-gray-600">إجمالي الطلبات</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.total_orders || 0}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-body">
              <div className="flex items-center">
                <div className="bg-yellow-100 p-3 rounded-lg">
                  <TruckIcon className="h-6 w-6 text-yellow-600" />
                </div>
                <div className="mr-4">
                  <p className="text-sm text-gray-600">طلبات معلقة</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.pending_orders || 0}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-body">
              <div className="flex items-center">
                <div className="bg-green-100 p-3 rounded-lg">
                  <ShoppingCartIcon className="h-6 w-6 text-green-600" />
                </div>
                <div className="mr-4">
                  <p className="text-sm text-gray-600">عناصر في السلة</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.cart_items || 0}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-body">
              <div className="flex items-center">
                <div className="bg-purple-100 p-3 rounded-lg">
                  <CheckCircleIcon className="h-6 w-6 text-purple-600" />
                </div>
                <div className="mr-4">
                  <p className="text-sm text-gray-600">طلبات مكتملة</p>
                  <p className="text-2xl font-bold text-gray-900">{(stats.total_orders || 0) - (stats.pending_orders || 0)}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Link
            to="/products"
            className="card hover:shadow-lg transition-shadow duration-200"
          >
            <div className="card-body text-center">
              <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <ShoppingCartIcon className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">تصفح المنتجات</h3>
              <p className="text-gray-600">اكتشف مجموعة واسعة من مواد البناء</p>
            </div>
          </Link>

          <Link
            to="/cart"
            className="card hover:shadow-lg transition-shadow duration-200"
          >
            <div className="card-body text-center">
              <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <ShoppingCartIcon className="h-8 w-8 text-green-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">عرض السلة</h3>
              <p className="text-gray-600">راجع المنتجات في سلة التسوق</p>
            </div>
          </Link>

          <Link
            to="/chat"
            className="card hover:shadow-lg transition-shadow duration-200"
          >
            <div className="card-body text-center">
              <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <ChatBubbleLeftRightIcon className="h-8 w-8 text-purple-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">المحادثات</h3>
              <p className="text-gray-600">تواصل مع الموردين</p>
            </div>
          </Link>
        </div>

        {/* Recent Orders */}
        <div className="card">
          <div className="card-header">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-900">الطلبات الأخيرة</h2>
              <Link
                to="/orders"
                className="text-blue-600 hover:text-blue-700 font-medium"
              >
                عرض الكل
              </Link>
            </div>
          </div>
          <div className="card-body">
            {recentOrders.length > 0 ? (
              <div className="space-y-4">
                {recentOrders.map((order) => (
                  <div key={order.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center">
                      <div className="bg-blue-100 p-2 rounded-lg ml-4">
                        <ClipboardDocumentListIcon className="h-5 w-5 text-blue-600" />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">طلب #{order.id.slice(-8)}</p>
                        <p className="text-sm text-gray-600">
                          {new Date(order.created_at).toLocaleDateString('ar-SA')}
                        </p>
                      </div>
                    </div>
                    <div className="text-left">
                      <p className="font-semibold text-gray-900">{order.total_amount} ر.س</p>
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        order.status === 'delivered' ? 'bg-green-100 text-green-800' :
                        order.status === 'shipped' ? 'bg-blue-100 text-blue-800' :
                        order.status === 'confirmed' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {order.status === 'pending' ? 'معلق' :
                         order.status === 'confirmed' ? 'مؤكد' :
                         order.status === 'shipped' ? 'في الطريق' :
                         order.status === 'delivered' ? 'تم التسليم' :
                         order.status === 'cancelled' ? 'ملغي' : order.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <ClipboardDocumentListIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">لا توجد طلبات حتى الآن</p>
                <Link
                  to="/products"
                  className="btn-primary mt-4 inline-block"
                >
                  ابدأ التسوق
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CustomerDashboard;