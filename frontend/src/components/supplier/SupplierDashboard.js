import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../App';
import { useToast } from '../ui/toast';
import axios from 'axios';
import {
  BuildingStorefrontIcon,
  ClipboardDocumentListIcon,
  CurrencyDollarIcon,
  TruckIcon,
  PlusIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon
} from '@heroicons/react/24/outline';

const SupplierDashboard = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [stats, setStats] = useState({});
  const [recentOrders, setRecentOrders] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsResponse, ordersResponse, productsResponse] = await Promise.all([
        axios.get('/stores/vendor/store/stats'),
        axios.get('/orders/vendor/orders?limit=5'),
        axios.get('/products/vendor/products?limit=10')
      ]);

      // Map store stats to expected format
      const storeStats = statsResponse.data;
      setStats({
        total_products: storeStats.products?.total || 0,
        total_orders: storeStats.orders?.total || 0,
        pending_orders: storeStats.orders?.pending || 0,
        total_revenue: storeStats.sales?.total || 0
      });
      setRecentOrders(ordersResponse.data?.items || ordersResponse.data || []);
      setProducts(productsResponse.data?.items || productsResponse.data || []);
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
          <p className="text-gray-600 mt-2">لوحة تحكم المورد - {user?.company_name}</p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="card">
            <div className="card-body">
              <div className="flex items-center">
                <div className="bg-blue-100 p-3 rounded-lg">
                  <BuildingStorefrontIcon className="h-6 w-6 text-blue-600" />
                </div>
                <div className="mr-4">
                  <p className="text-sm text-gray-600">إجمالي المنتجات</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.total_products || 0}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-body">
              <div className="flex items-center">
                <div className="bg-green-100 p-3 rounded-lg">
                  <ClipboardDocumentListIcon className="h-6 w-6 text-green-600" />
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
                <div className="bg-purple-100 p-3 rounded-lg">
                  <CurrencyDollarIcon className="h-6 w-6 text-purple-600" />
                </div>
                <div className="mr-4">
                  <p className="text-sm text-gray-600">إجمالي الإيرادات</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.total_revenue || 0} ر.س</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Products Management */}
          <div className="card">
            <div className="card-header">
              <div className="flex justify-between items-center">
                <h2 className="text-xl font-semibold text-gray-900">منتجاتي</h2>
                <button className="btn-primary text-sm flex items-center">
                  <PlusIcon className="h-4 w-4 ml-1" />
                  إضافة منتج
                </button>
              </div>
            </div>
            <div className="card-body">
              {products.length > 0 ? (
                <div className="space-y-4">
                  {products.slice(0, 5).map((product) => (
                    <div key={product.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center">
                        <div className="w-12 h-12 bg-gray-200 rounded-lg ml-4 flex items-center justify-center">
                          {product.images && product.images.length > 0 ? (
                            <img
                              src={product.images[0]}
                              alt={product.name}
                              className="w-full h-full object-cover rounded-lg"
                            />
                          ) : (
                            <BuildingStorefrontIcon className="h-6 w-6 text-gray-400" />
                          )}
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{product.name}</p>
                          <p className="text-sm text-gray-600">{product.price} ر.س/{product.unit}</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 space-x-reverse">
                        <button className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg">
                          <EyeIcon className="h-4 w-4" />
                        </button>
                        <button className="p-2 text-green-600 hover:bg-green-50 rounded-lg">
                          <PencilIcon className="h-4 w-4" />
                        </button>
                        <button className="p-2 text-red-600 hover:bg-red-50 rounded-lg">
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <BuildingStorefrontIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">لا توجد منتجات حتى الآن</p>
                  <button className="btn-primary mt-4">
                    إضافة أول منتج
                  </button>
                </div>
              )}
            </div>
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
                        <div className="bg-green-100 p-2 rounded-lg ml-4">
                          <ClipboardDocumentListIcon className="h-5 w-5 text-green-600" />
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
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SupplierDashboard;