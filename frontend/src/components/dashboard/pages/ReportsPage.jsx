/**
 * ===================================
 * منصة ديواني - Reports & Analytics Page
 * Advanced analytics dashboard
 * ===================================
 */

import React, { useState, useEffect, useMemo } from 'react';
import DashboardLayout from '../DashboardLayout';
import {
  ArrowUpIcon,
  ArrowDownIcon,
  CalendarIcon,
  ArrowPathIcon,
  DocumentArrowDownIcon,
} from '@heroicons/react/24/outline';

// Date range options
const DATE_RANGES = [
  { id: 'today', label: 'اليوم' },
  { id: 'week', label: 'هذا الأسبوع' },
  { id: 'month', label: 'هذا الشهر' },
  { id: 'quarter', label: 'هذا الربع' },
  { id: 'year', label: 'هذا العام' },
  { id: 'custom', label: 'تخصيص' },
];

const ReportsPage = () => {
  const [dateRange, setDateRange] = useState('month');
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({});
  const [salesData, setSalesData] = useState([]);
  const [topProducts, setTopProducts] = useState([]);
  const [topCustomers, setTopCustomers] = useState([]);
  const [ordersByStatus, setOrdersByStatus] = useState({});

  useEffect(() => {
    fetchReportsData();
  }, [dateRange]);

  const fetchReportsData = async () => {
    setLoading(true);
    // Simulate API call - replace with actual API
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Demo data
    setStats({
      totalRevenue: 156780,
      revenueChange: 18.5,
      totalOrders: 342,
      ordersChange: 12.3,
      averageOrderValue: 458,
      aovChange: 5.2,
      conversionRate: 3.8,
      conversionChange: 0.5,
      totalCustomers: 189,
      customersChange: 22.1,
      repeatRate: 45,
      repeatChange: 8.3,
    });

    // Sales chart data
    setSalesData(generateSalesData(dateRange));

    // Top products
    setTopProducts([
      { id: 1, name: 'أسمنت بورتلاند 50 كجم', sales: 45600, quantity: 1824, trend: 12 },
      { id: 2, name: 'حديد تسليح 12mm', sales: 38200, quantity: 456, trend: 8 },
      { id: 3, name: 'بلوك خرساني 20cm', sales: 28500, quantity: 8142, trend: -3 },
      { id: 4, name: 'رمل أبيض ناعم', sales: 18900, quantity: 236, trend: 15 },
      { id: 5, name: 'طوب أحمر', sales: 12400, quantity: 24800, trend: 5 },
    ]);

    // Top customers
    setTopCustomers([
      { id: 1, name: 'شركة البناء المتقدم', orders: 28, total: 45600, lastOrder: '2024-01-15' },
      { id: 2, name: 'مؤسسة الخليج للمقاولات', orders: 22, total: 38200, lastOrder: '2024-01-14' },
      { id: 3, name: 'محمد أحمد العمري', orders: 18, total: 28500, lastOrder: '2024-01-13' },
      { id: 4, name: 'شركة النخبة للتطوير', orders: 15, total: 24800, lastOrder: '2024-01-12' },
      { id: 5, name: 'مؤسسة الفهد للبناء', orders: 12, total: 18900, lastOrder: '2024-01-10' },
    ]);

    // Orders by status
    setOrdersByStatus({
      pending: 24,
      confirmed: 18,
      processing: 12,
      shipped: 8,
      delivered: 245,
      cancelled: 35,
    });

    setLoading(false);
  };

  // Generate sales data based on date range
  const generateSalesData = (range) => {
    const data = [];
    let days = 30;
    if (range === 'week') days = 7;
    if (range === 'today') days = 1;
    if (range === 'quarter') days = 90;
    if (range === 'year') days = 365;

    for (let i = 0; i < Math.min(days, 30); i++) {
      const date = new Date();
      date.setDate(date.getDate() - (days - i - 1));
      data.push({
        date: date.toLocaleDateString('ar-SA', { month: 'short', day: 'numeric' }),
        sales: Math.floor(Math.random() * 8000) + 2000,
        orders: Math.floor(Math.random() * 20) + 5,
      });
    }
    return data;
  };

  // Calculate chart dimensions
  const chartConfig = useMemo(() => {
    if (salesData.length === 0) return {};
    const maxSales = Math.max(...salesData.map(d => d.sales));
    const minSales = Math.min(...salesData.map(d => d.sales));
    return { maxSales, minSales, range: maxSales - minSales || 1 };
  }, [salesData]);

  const StatCard = ({ title, value, change, format = 'number', icon: Icon }) => (
    <div className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm text-gray-500">{title}</span>
        {Icon && <Icon className="h-5 w-5 text-gray-400" />}
      </div>
      <div className="flex items-end justify-between">
        <span className="text-2xl font-bold text-gray-900">
          {format === 'currency' && formatCurrency(value)}
          {format === 'number' && formatNumber(value)}
          {format === 'percent' && `${value}%`}
        </span>
        {change !== undefined && (
          <span className={`flex items-center text-sm ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {change >= 0 ? <ArrowUpIcon className="h-4 w-4" /> : <ArrowDownIcon className="h-4 w-4" />}
            {Math.abs(change)}%
          </span>
        )}
      </div>
    </div>
  );

  return (
    <DashboardLayout>
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">التقارير والإحصائيات</h1>
          <p className="text-gray-500 mt-1">تحليلات شاملة لأداء متجرك</p>
        </div>
        <div className="flex items-center gap-4 mt-4 md:mt-0">
          {/* Date Range Selector */}
          <div className="flex items-center bg-white rounded-lg shadow-sm border border-gray-200">
            {DATE_RANGES.slice(0, 5).map((range) => (
              <button
                key={range.id}
                onClick={() => setDateRange(range.id)}
                className={`px-4 py-2 text-sm font-medium transition-colors first:rounded-r-lg last:rounded-l-lg ${
                  dateRange === range.id
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                {range.label}
              </button>
            ))}
          </div>
          {/* Refresh */}
          <button
            onClick={fetchReportsData}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
          >
            <ArrowPathIcon className={`h-5 w-5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          {/* Export */}
          <button className="flex items-center px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-50">
            <DocumentArrowDownIcon className="h-5 w-5 ml-2" />
            تصدير
          </button>
        </div>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-white rounded-xl shadow-sm p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-20 mb-4" />
              <div className="h-8 bg-gray-200 rounded w-32" />
            </div>
          ))}
        </div>
      ) : (
        <>
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            <StatCard
              title="إجمالي الإيرادات"
              value={stats.totalRevenue}
              change={stats.revenueChange}
              format="currency"
            />
            <StatCard
              title="إجمالي الطلبات"
              value={stats.totalOrders}
              change={stats.ordersChange}
              format="number"
            />
            <StatCard
              title="متوسط قيمة الطلب"
              value={stats.averageOrderValue}
              change={stats.aovChange}
              format="currency"
            />
            <StatCard
              title="معدل التحويل"
              value={stats.conversionRate}
              change={stats.conversionChange}
              format="percent"
            />
            <StatCard
              title="إجمالي العملاء"
              value={stats.totalCustomers}
              change={stats.customersChange}
              format="number"
            />
            <StatCard
              title="معدل الشراء المتكرر"
              value={stats.repeatRate}
              change={stats.repeatChange}
              format="percent"
            />
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
            {/* Sales Chart */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-6">تطور المبيعات</h3>
              <div className="h-64 relative">
                {/* Y-axis */}
                <div className="absolute right-0 top-0 bottom-8 w-12 flex flex-col justify-between text-xs text-gray-500">
                  <span>{formatNumber(chartConfig.maxSales)}</span>
                  <span>{formatNumber((chartConfig.maxSales + chartConfig.minSales) / 2)}</span>
                  <span>{formatNumber(chartConfig.minSales)}</span>
                </div>

                {/* Chart */}
                <div className="absolute left-0 top-0 bottom-8 right-14">
                  <svg viewBox="0 0 100 50" className="w-full h-full" preserveAspectRatio="none">
                    {/* Grid */}
                    <line x1="0" y1="12.5" x2="100" y2="12.5" stroke="#e5e7eb" strokeWidth="0.2" />
                    <line x1="0" y1="25" x2="100" y2="25" stroke="#e5e7eb" strokeWidth="0.2" />
                    <line x1="0" y1="37.5" x2="100" y2="37.5" stroke="#e5e7eb" strokeWidth="0.2" />

                    {/* Gradient */}
                    <defs>
                      <linearGradient id="salesGradient2" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.4" />
                        <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.05" />
                      </linearGradient>
                    </defs>

                    {/* Area */}
                    <path
                      d={`M 0,50 ${salesData.map((d, i) => {
                        const x = (i / (salesData.length - 1)) * 100;
                        const y = 50 - ((d.sales - chartConfig.minSales) / chartConfig.range) * 45;
                        return `L ${x},${y}`;
                      }).join(' ')} L 100,50 Z`}
                      fill="url(#salesGradient2)"
                    />

                    {/* Line */}
                    <path
                      d={`M ${salesData.map((d, i) => {
                        const x = (i / (salesData.length - 1)) * 100;
                        const y = 50 - ((d.sales - chartConfig.minSales) / chartConfig.range) * 45;
                        return `${x},${y}`;
                      }).join(' L ')}`}
                      fill="none"
                      stroke="#3b82f6"
                      strokeWidth="0.5"
                    />

                    {/* Points */}
                    {salesData.map((d, i) => {
                      const x = (i / (salesData.length - 1)) * 100;
                      const y = 50 - ((d.sales - chartConfig.minSales) / chartConfig.range) * 45;
                      return (
                        <circle
                          key={i}
                          cx={x}
                          cy={y}
                          r="0.8"
                          fill="#3b82f6"
                          className="hover:r-2 cursor-pointer"
                        />
                      );
                    })}
                  </svg>
                </div>

                {/* X-axis */}
                <div className="absolute bottom-0 right-14 left-0 flex justify-between text-xs text-gray-500">
                  {salesData.filter((_, i) => i % Math.ceil(salesData.length / 6) === 0).map((d, i) => (
                    <span key={i}>{d.date}</span>
                  ))}
                </div>
              </div>
            </div>

            {/* Orders by Status */}
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-6">توزيع الطلبات</h3>
              <div className="space-y-4">
                {Object.entries(ordersByStatus).map(([status, count]) => {
                  const total = Object.values(ordersByStatus).reduce((a, b) => a + b, 0);
                  const percent = ((count / total) * 100).toFixed(1);
                  const colors = {
                    pending: 'bg-yellow-500',
                    confirmed: 'bg-blue-500',
                    processing: 'bg-indigo-500',
                    shipped: 'bg-purple-500',
                    delivered: 'bg-green-500',
                    cancelled: 'bg-red-500',
                  };
                  const labels = {
                    pending: 'معلق',
                    confirmed: 'مؤكد',
                    processing: 'قيد التجهيز',
                    shipped: 'في الطريق',
                    delivered: 'تم التسليم',
                    cancelled: 'ملغي',
                  };
                  return (
                    <div key={status}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-gray-600">{labels[status]}</span>
                        <span className="text-sm font-medium text-gray-900">{count} ({percent}%)</span>
                      </div>
                      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${colors[status]} transition-all duration-500`}
                          style={{ width: `${percent}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Tables Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Top Products */}
            <div className="bg-white rounded-xl shadow-sm overflow-hidden">
              <div className="p-6 border-b border-gray-100">
                <h3 className="text-lg font-semibold text-gray-900">المنتجات الأكثر مبيعاً</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500">المنتج</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500">المبيعات</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500">الكمية</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500">التغير</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {topProducts.map((product, index) => (
                      <tr key={product.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <div className="flex items-center">
                            <span className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium ml-3">
                              {index + 1}
                            </span>
                            <span className="font-medium text-gray-900">{product.name}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm font-semibold text-gray-900">
                          {formatCurrency(product.sales)}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">
                          {formatNumber(product.quantity)}
                        </td>
                        <td className="px-6 py-4">
                          <span className={`flex items-center text-sm ${product.trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {product.trend >= 0 ? <ArrowUpIcon className="h-3 w-3 ml-1" /> : <ArrowDownIcon className="h-3 w-3 ml-1" />}
                            {Math.abs(product.trend)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Top Customers */}
            <div className="bg-white rounded-xl shadow-sm overflow-hidden">
              <div className="p-6 border-b border-gray-100">
                <h3 className="text-lg font-semibold text-gray-900">أفضل العملاء</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500">العميل</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500">الطلبات</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500">الإجمالي</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500">آخر طلب</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {topCustomers.map((customer, index) => (
                      <tr key={customer.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <div className="flex items-center">
                            <span className="w-6 h-6 bg-green-100 text-green-600 rounded-full flex items-center justify-center text-xs font-medium ml-3">
                              {index + 1}
                            </span>
                            <span className="font-medium text-gray-900">{customer.name}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">{customer.orders}</td>
                        <td className="px-6 py-4 text-sm font-semibold text-gray-900">
                          {formatCurrency(customer.total)}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {new Date(customer.lastOrder).toLocaleDateString('ar-SA')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </>
      )}
    </DashboardLayout>
  );
};

// Helper functions
function formatCurrency(value) {
  return new Intl.NumberFormat('ar-SA', {
    style: 'decimal',
    maximumFractionDigits: 0,
  }).format(value) + ' ر.س';
}

function formatNumber(value) {
  return new Intl.NumberFormat('ar-SA').format(value);
}

export default ReportsPage;
