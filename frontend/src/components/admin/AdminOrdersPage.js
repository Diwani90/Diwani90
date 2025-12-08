import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../App';
import { useToast } from '../ui/toast';
import axios from 'axios';
import {
  ShoppingCartIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  EyeIcon,
  ClockIcon,
  CheckCircleIcon,
  TruckIcon,
  XCircleIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  CurrencyDollarIcon
} from '@heroicons/react/24/outline';

const AdminOrdersPage = () => {
  const { user } = useAuth();
  const { toast } = useToast();

  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 20,
    total: 0,
    total_pages: 0
  });
  const [filters, setFilters] = useState({
    search: '',
    status: ''
  });
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    fetchOrders();
  }, [pagination.page, filters]);

  const fetchOrders = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        limit: pagination.per_page,
        offset: (pagination.page - 1) * pagination.per_page,
        ...(filters.status && { status: filters.status })
      });

      const response = await axios.get(`/orders/orders?${params}`);
      const items = response.data.items || response.data || [];
      setOrders(Array.isArray(items) ? items : []);

      // Calculate pagination from response
      const total = response.data.count || items.length;
      setPagination(prev => ({
        ...prev,
        total: total,
        total_pages: Math.ceil(total / pagination.per_page)
      }));
    } catch (error) {
      console.error('Error fetching orders:', error);
      toast.error('خطأ', 'حدث خطأ في تحميل الطلبات');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPagination(prev => ({ ...prev, page: 1 }));
    fetchOrders();
  };

  const updateOrderStatus = async (orderId, newStatus) => {
    try {
      await axios.put(`/orders/orders/${orderId}/status`, { status: newStatus });
      toast.success('تم بنجاح', 'تم تحديث حالة الطلب');
      fetchOrders();
      setShowModal(false);
    } catch (error) {
      console.error('Error updating order status:', error);
      toast.error('خطأ', 'حدث خطأ في تحديث حالة الطلب');
    }
  };

  const viewOrderDetails = async (orderId) => {
    try {
      const response = await axios.get(`/orders/orders/${orderId}`);
      setSelectedOrder(response.data);
      setShowModal(true);
    } catch (error) {
      console.error('Error fetching order details:', error);
      toast.error('خطأ', 'حدث خطأ في تحميل بيانات الطلب');
    }
  };

  const getStatusLabel = (status) => {
    const labels = {
      'pending': 'بانتظار',
      'confirmed': 'مؤكد',
      'processing': 'قيد التجهيز',
      'shipped': 'تم الشحن',
      'out_for_delivery': 'في الطريق',
      'delivered': 'تم التوصيل',
      'completed': 'مكتمل',
      'cancelled': 'ملغي'
    };
    return labels[status] || status;
  };

  const getStatusColor = (status) => {
    const colors = {
      'pending': 'bg-yellow-100 text-yellow-800',
      'confirmed': 'bg-blue-100 text-blue-800',
      'processing': 'bg-purple-100 text-purple-800',
      'shipped': 'bg-indigo-100 text-indigo-800',
      'out_for_delivery': 'bg-cyan-100 text-cyan-800',
      'delivered': 'bg-green-100 text-green-800',
      'completed': 'bg-green-500 text-white',
      'cancelled': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':
        return <ClockIcon className="h-5 w-5" />;
      case 'confirmed':
      case 'processing':
        return <CheckCircleIcon className="h-5 w-5" />;
      case 'shipped':
      case 'out_for_delivery':
        return <TruckIcon className="h-5 w-5" />;
      case 'delivered':
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5" />;
      case 'cancelled':
        return <XCircleIcon className="h-5 w-5" />;
      default:
        return <ClockIcon className="h-5 w-5" />;
    }
  };

  if (loading && orders.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 px-4 py-6 text-white">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl font-bold flex items-center">
            <ShoppingCartIcon className="h-7 w-7 ml-2" />
            إدارة الطلبات
          </h1>
          <p className="text-sm opacity-90 mt-1">عرض ومتابعة جميع الطلبات</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
          <form onSubmit={handleSearch} className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="relative">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400 absolute right-3 top-1/2 transform -translate-y-1/2" />
              <input
                type="text"
                placeholder="البحث برقم الطلب..."
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                className="input-field pr-10"
              />
            </div>

            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="input-field"
            >
              <option value="">جميع الحالات</option>
              <option value="pending">بانتظار</option>
              <option value="confirmed">مؤكد</option>
              <option value="processing">قيد التجهيز</option>
              <option value="shipped">تم الشحن</option>
              <option value="delivered">تم التوصيل</option>
              <option value="completed">مكتمل</option>
              <option value="cancelled">ملغي</option>
            </select>

            <button type="submit" className="btn-primary flex items-center justify-center">
              <FunnelIcon className="h-5 w-5 ml-2" />
              تصفية
            </button>
          </form>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl shadow-sm p-4 text-center">
            <p className="text-2xl font-bold text-gray-900">{pagination.total}</p>
            <p className="text-sm text-gray-600">إجمالي الطلبات</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4 text-center">
            <p className="text-2xl font-bold text-yellow-600">
              {orders.filter(o => o.status === 'pending').length}
            </p>
            <p className="text-sm text-gray-600">بانتظار</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4 text-center">
            <p className="text-2xl font-bold text-blue-600">
              {orders.filter(o => ['processing', 'shipped'].includes(o.status)).length}
            </p>
            <p className="text-sm text-gray-600">قيد التنفيذ</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4 text-center">
            <p className="text-2xl font-bold text-green-600">
              {orders.filter(o => ['delivered', 'completed'].includes(o.status)).length}
            </p>
            <p className="text-sm text-gray-600">مكتمل</p>
          </div>
        </div>

        {/* Orders Table */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    رقم الطلب
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    العميل
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    المبلغ
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    الحالة
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    التاريخ
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    الإجراءات
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {orders.map((order) => (
                  <tr key={order.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="h-10 w-10 rounded-full bg-purple-100 flex items-center justify-center">
                          <ShoppingCartIcon className="h-5 w-5 text-purple-600" />
                        </div>
                        <div className="mr-4">
                          <div className="text-sm font-medium text-gray-900">
                            #{order.order_number || order.id?.slice(0, 8)}
                          </div>
                          <div className="text-xs text-gray-500">
                            {order.items_count || order.items?.length || 0} منتج
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{order.customer_name || '-'}</div>
                      <div className="text-sm text-gray-500">{order.customer_phone || '-'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-bold text-gray-900">
                        {order.total_amount || 0} ر.س
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(order.status)}`}>
                        {getStatusIcon(order.status)}
                        <span className="mr-1">{getStatusLabel(order.status)}</span>
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(order.created_at).toLocaleDateString('ar-SA')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => viewOrderDetails(order.id)}
                          className="text-blue-600 hover:text-blue-900"
                          title="عرض التفاصيل"
                        >
                          <EyeIcon className="h-5 w-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Empty State */}
          {orders.length === 0 && !loading && (
            <div className="text-center py-12">
              <ShoppingCartIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">لا توجد طلبات</p>
            </div>
          )}

          {/* Pagination */}
          {pagination.total_pages > 1 && (
            <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200">
              <div className="flex-1 flex justify-between items-center">
                <p className="text-sm text-gray-700">
                  عرض <span className="font-medium">{((pagination.page - 1) * pagination.per_page) + 1}</span>
                  {' '}-{' '}
                  <span className="font-medium">
                    {Math.min(pagination.page * pagination.per_page, pagination.total)}
                  </span>
                  {' '}من{' '}
                  <span className="font-medium">{pagination.total}</span>
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                    disabled={pagination.page === 1}
                    className="btn-secondary disabled:opacity-50"
                  >
                    <ChevronRightIcon className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                    disabled={pagination.page === pagination.total_pages}
                    className="btn-secondary disabled:opacity-50"
                  >
                    <ChevronLeftIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Order Details Modal */}
      {showModal && selectedOrder && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                تفاصيل الطلب #{selectedOrder.order_number || selectedOrder.id?.slice(0, 8)}
              </h2>

              <div className="space-y-6">
                {/* Order Info */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-gray-500">الحالة</label>
                    <p className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(selectedOrder.status)}`}>
                      {getStatusLabel(selectedOrder.status)}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">تاريخ الطلب</label>
                    <p className="font-medium">
                      {new Date(selectedOrder.created_at).toLocaleDateString('ar-SA')}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">إجمالي المبلغ</label>
                    <p className="font-bold text-lg text-blue-600">
                      {selectedOrder.total_amount || 0} ر.س
                    </p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">طريقة الدفع</label>
                    <p className="font-medium">
                      {selectedOrder.payment_method === 'cash' ? 'نقدي عند التوصيل' : 'إلكتروني'}
                    </p>
                  </div>
                </div>

                {/* Customer Info */}
                <div className="border-t pt-4">
                  <h3 className="font-semibold mb-2">معلومات العميل</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm text-gray-500">الاسم</label>
                      <p className="font-medium">{selectedOrder.customer_name || '-'}</p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-500">الهاتف</label>
                      <p className="font-medium">{selectedOrder.customer_phone || '-'}</p>
                    </div>
                  </div>
                </div>

                {/* Delivery Info */}
                <div className="border-t pt-4">
                  <h3 className="font-semibold mb-2">معلومات التوصيل</h3>
                  <div>
                    <label className="text-sm text-gray-500">العنوان</label>
                    <p className="font-medium">{selectedOrder.delivery_address || '-'}</p>
                  </div>
                  {selectedOrder.delivery_notes && (
                    <div className="mt-2">
                      <label className="text-sm text-gray-500">ملاحظات</label>
                      <p className="font-medium">{selectedOrder.delivery_notes}</p>
                    </div>
                  )}
                </div>

                {/* Items */}
                {selectedOrder.items && selectedOrder.items.length > 0 && (
                  <div className="border-t pt-4">
                    <h3 className="font-semibold mb-2">المنتجات</h3>
                    <div className="space-y-2">
                      {selectedOrder.items.map((item, index) => (
                        <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                          <div>
                            <p className="font-medium">{item.product_name || item.name}</p>
                            <p className="text-sm text-gray-500">الكمية: {item.quantity}</p>
                          </div>
                          <p className="font-bold">{item.subtotal || (item.price * item.quantity)} ر.س</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex gap-3 mt-6">
                {selectedOrder.status === 'pending' && (
                  <button
                    onClick={() => updateOrderStatus(selectedOrder.id, 'confirmed')}
                    className="btn-primary flex-1"
                  >
                    تأكيد الطلب
                  </button>
                )}
                {selectedOrder.status === 'confirmed' && (
                  <button
                    onClick={() => updateOrderStatus(selectedOrder.id, 'processing')}
                    className="btn-primary flex-1"
                  >
                    بدء التجهيز
                  </button>
                )}
                {['pending', 'confirmed'].includes(selectedOrder.status) && (
                  <button
                    onClick={() => updateOrderStatus(selectedOrder.id, 'cancelled')}
                    className="btn-secondary flex-1 text-red-600"
                  >
                    إلغاء الطلب
                  </button>
                )}
                <button
                  onClick={() => setShowModal(false)}
                  className="btn-secondary flex-1"
                >
                  إغلاق
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminOrdersPage;
