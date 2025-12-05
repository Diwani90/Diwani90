/**
 * ===================================
 * منصة ديواني - Orders Page
 * Full orders management page
 * ===================================
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { ordersService } from '../../../services/api';
import DashboardLayout from '../DashboardLayout';
import { useToast } from '../../ui/toast';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  EyeIcon,
  CheckIcon,
  TruckIcon,
  XMarkIcon,
  ClipboardDocumentListIcon,
} from '@heroicons/react/24/outline';

const statusConfig = {
  pending: { label: 'معلق', color: 'bg-yellow-100 text-yellow-800', icon: '⏳' },
  confirmed: { label: 'مؤكد', color: 'bg-blue-100 text-blue-800', icon: '✓' },
  processing: { label: 'قيد التجهيز', color: 'bg-indigo-100 text-indigo-800', icon: '📦' },
  shipped: { label: 'في الطريق', color: 'bg-purple-100 text-purple-800', icon: '🚚' },
  delivered: { label: 'تم التسليم', color: 'bg-green-100 text-green-800', icon: '✅' },
  cancelled: { label: 'ملغي', color: 'bg-red-100 text-red-800', icon: '❌' },
};

const OrdersPage = () => {
  const { toast } = useToast();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [showModal, setShowModal] = useState(false);

  const fetchOrders = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        page,
        page_size: 10,
        search: search || undefined,
        status: statusFilter !== 'all' ? statusFilter : undefined,
      };

      const response = await ordersService.getVendorOrders(params);
      setOrders(response.items || []);
      setTotalPages(response.pages || 1);
    } catch (error) {
      console.error('Error fetching orders:', error);
      // Demo data for development
      setOrders([
        { id: '1433', order_number: 'ORD-1433', customer_name: 'أحمد حسن', customer_phone: '0501234567', total: 3200, status: 'pending', items_count: 5, created_at: '2024-01-15T10:30:00Z' },
        { id: '1432', order_number: 'ORD-1432', customer_name: 'قاطمة علي', customer_phone: '0507654321', total: 5600, status: 'processing', items_count: 3, created_at: '2024-01-14T14:20:00Z' },
        { id: '1431', order_number: 'ORD-1431', customer_name: 'خالد محمد', customer_phone: '0509876543', total: 1200, status: 'shipped', items_count: 2, created_at: '2024-01-13T09:15:00Z' },
        { id: '1430', order_number: 'ORD-1430', customer_name: 'علي إبراهيم', customer_phone: '0503456789', total: 7800, status: 'delivered', items_count: 8, created_at: '2024-01-12T16:45:00Z' },
        { id: '1429', order_number: 'ORD-1429', customer_name: 'سارة أحمد', customer_phone: '0502345678', total: 450, status: 'cancelled', items_count: 1, created_at: '2024-01-11T11:00:00Z' },
      ]);
    } finally {
      setLoading(false);
    }
  }, [page, search, statusFilter]);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  const updateOrderStatus = async (orderId, newStatus) => {
    try {
      await ordersService.updateOrderStatus(orderId, newStatus);
      setOrders(orders.map((o) => (o.id === orderId ? { ...o, status: newStatus } : o)));
      toast?.success?.('تم التحديث', 'تم تحديث حالة الطلب بنجاح');
    } catch (error) {
      console.error('Error updating order:', error);
      toast?.error?.('خطأ', 'حدث خطأ في تحديث حالة الطلب');
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('ar-SA', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <DashboardLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">الطلبات</h1>
        <p className="text-gray-500 mt-1">إدارة ومتابعة طلبات العملاء</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
        {Object.entries(statusConfig).map(([key, config]) => {
          const count = orders.filter((o) => o.status === key).length;
          return (
            <button
              key={key}
              onClick={() => setStatusFilter(key === statusFilter ? 'all' : key)}
              className={`p-4 rounded-xl text-center transition-all ${
                statusFilter === key
                  ? 'bg-blue-600 text-white shadow-lg'
                  : 'bg-white shadow-sm hover:shadow-md'
              }`}
            >
              <span className="text-2xl">{config.icon}</span>
              <p className={`text-2xl font-bold mt-2 ${statusFilter === key ? 'text-white' : 'text-gray-900'}`}>
                {count}
              </p>
              <p className={`text-sm ${statusFilter === key ? 'text-blue-100' : 'text-gray-500'}`}>
                {config.label}
              </p>
            </button>
          );
        })}
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
        <div className="flex flex-col md:flex-row md:items-center gap-4">
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="ابحث برقم الطلب أو اسم العميل..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pr-10 pl-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">جميع الحالات</option>
            {Object.entries(statusConfig).map(([key, config]) => (
              <option key={key} value={key}>{config.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Orders Table */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          </div>
        ) : orders.length === 0 ? (
          <div className="p-12 text-center">
            <ClipboardDocumentListIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">لا توجد طلبات</h3>
            <p className="text-gray-500">ستظهر الطلبات الجديدة هنا</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-100">
                  <tr>
                    <th className="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase">رقم الطلب</th>
                    <th className="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase">العميل</th>
                    <th className="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase">المنتجات</th>
                    <th className="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase">المبلغ</th>
                    <th className="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase">الحالة</th>
                    <th className="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase">التاريخ</th>
                    <th className="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase">الإجراءات</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {orders.map((order) => {
                    const status = statusConfig[order.status] || statusConfig.pending;
                    return (
                      <tr key={order.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <span className="font-medium text-blue-600">#{order.order_number}</span>
                        </td>
                        <td className="px-6 py-4">
                          <div>
                            <p className="font-medium text-gray-900">{order.customer_name}</p>
                            <p className="text-sm text-gray-500">{order.customer_phone}</p>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">
                          {order.items_count} منتج
                        </td>
                        <td className="px-6 py-4">
                          <span className="font-semibold text-gray-900">
                            {new Intl.NumberFormat('ar-SA').format(order.total)} ر.س
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${status.color}`}>
                            {status.label}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {formatDate(order.created_at)}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-1">
                            <Link
                              to={`/dashboard/orders/${order.id}`}
                              className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg"
                              title="عرض التفاصيل"
                            >
                              <EyeIcon className="h-4 w-4" />
                            </Link>
                            {order.status === 'pending' && (
                              <button
                                onClick={() => updateOrderStatus(order.id, 'confirmed')}
                                className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg"
                                title="تأكيد الطلب"
                              >
                                <CheckIcon className="h-4 w-4" />
                              </button>
                            )}
                            {order.status === 'confirmed' && (
                              <button
                                onClick={() => updateOrderStatus(order.id, 'shipped')}
                                className="p-2 text-gray-400 hover:text-purple-600 hover:bg-purple-50 rounded-lg"
                                title="شحن الطلب"
                              >
                                <TruckIcon className="h-4 w-4" />
                              </button>
                            )}
                            {['pending', 'confirmed'].includes(order.status) && (
                              <button
                                onClick={() => updateOrderStatus(order.id, 'cancelled')}
                                className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                                title="إلغاء الطلب"
                              >
                                <XMarkIcon className="h-4 w-4" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-between">
                <p className="text-sm text-gray-500">الصفحة {page} من {totalPages}</p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-3 py-1 border rounded-lg disabled:opacity-50"
                  >
                    السابق
                  </button>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="px-3 py-1 border rounded-lg disabled:opacity-50"
                  >
                    التالي
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </DashboardLayout>
  );
};

export default OrdersPage;
