/**
 * ===================================
 * منصة ديواني - Recent Orders Component
 * Dashboard recent orders table
 * ===================================
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { EyeIcon } from '@heroicons/react/24/outline';

const statusConfig = {
  pending: {
    label: 'معلق',
    color: 'bg-yellow-100 text-yellow-800',
  },
  confirmed: {
    label: 'مؤكد',
    color: 'bg-blue-100 text-blue-800',
  },
  processing: {
    label: 'قيد التجهيز',
    color: 'bg-indigo-100 text-indigo-800',
  },
  shipped: {
    label: 'في الطريق',
    color: 'bg-purple-100 text-purple-800',
  },
  delivered: {
    label: 'تم التسليم',
    color: 'bg-green-100 text-green-800',
  },
  cancelled: {
    label: 'ملغي',
    color: 'bg-red-100 text-red-800',
  },
};

const RecentOrders = ({ orders = [], loading = false }) => {
  // Demo data if no orders provided
  const displayOrders = orders.length > 0 ? orders : [
    { id: '1433', customer_name: 'أحمد حسن', total: 320, status: 'delivered', created_at: '2024-01-15' },
    { id: '1432', customer_name: 'قاطمة علي', total: 560, status: 'processing', created_at: '2024-01-14' },
    { id: '1431', customer_name: 'خالد محمد', total: 120, status: 'pending', created_at: '2024-01-13' },
    { id: '1430', customer_name: 'علي إبراهيم', total: 780, status: 'confirmed', created_at: '2024-01-12' },
  ];

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm">
        <div className="p-6 border-b border-gray-100">
          <div className="h-6 bg-gray-200 rounded w-32 animate-pulse" />
        </div>
        <div className="p-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex items-center justify-between py-4 border-b border-gray-50 last:border-0">
              <div className="flex items-center">
                <div className="w-10 h-10 bg-gray-200 rounded-lg animate-pulse" />
                <div className="mr-4">
                  <div className="h-4 bg-gray-200 rounded w-24 mb-2 animate-pulse" />
                  <div className="h-3 bg-gray-200 rounded w-16 animate-pulse" />
                </div>
              </div>
              <div className="h-6 bg-gray-200 rounded w-16 animate-pulse" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900">الطلبات الأخيرة</h3>
        <Link
          to="/dashboard/orders"
          className="text-sm text-blue-600 hover:text-blue-700 font-medium"
        >
          عرض الكل
        </Link>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                الرقم
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
                الإجراءات
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-100">
            {displayOrders.map((order) => (
              <tr key={order.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm font-medium text-gray-900">#{order.id}</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm text-gray-600">{order.customer_name}</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm font-semibold text-gray-900">
                    {new Intl.NumberFormat('ar-SA').format(order.total)} ر.س
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span
                    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      statusConfig[order.status]?.color || 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {statusConfig[order.status]?.label || order.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <Link
                    to={`/dashboard/orders/${order.id}`}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    <EyeIcon className="h-5 w-5" />
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Empty state */}
      {displayOrders.length === 0 && (
        <div className="p-12 text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <p className="text-gray-500">لا توجد طلبات حتى الآن</p>
        </div>
      )}
    </div>
  );
};

export default RecentOrders;
