/**
 * ===================================
 * منصة ديواني - Stats Cards Component
 * Dashboard statistics cards
 * ===================================
 */

import React from 'react';
import {
  ShoppingBagIcon,
  CurrencyDollarIcon,
  ClipboardDocumentListIcon,
  BuildingStorefrontIcon,
  ArrowUpIcon,
  ArrowDownIcon,
} from '@heroicons/react/24/outline';

const StatsCards = ({ stats, loading = false }) => {
  const cards = [
    {
      title: 'إجمالي المبيعات',
      value: stats?.totalRevenue || 0,
      format: 'currency',
      icon: CurrencyDollarIcon,
      color: 'green',
      bgColor: 'bg-green-50',
      iconBg: 'bg-green-100',
      iconColor: 'text-green-600',
      change: stats?.revenueChange || 12.5,
      changeType: 'increase',
    },
    {
      title: 'إجمالي الطلبات',
      value: stats?.totalOrders || 0,
      format: 'number',
      icon: ClipboardDocumentListIcon,
      color: 'blue',
      bgColor: 'bg-blue-50',
      iconBg: 'bg-blue-100',
      iconColor: 'text-blue-600',
      change: stats?.ordersChange || 8.2,
      changeType: 'increase',
    },
    {
      title: 'المنتجات المتاحة',
      value: stats?.totalProducts || 0,
      format: 'number',
      icon: ShoppingBagIcon,
      color: 'purple',
      bgColor: 'bg-purple-50',
      iconBg: 'bg-purple-100',
      iconColor: 'text-purple-600',
    },
    {
      title: 'طلبات معلقة',
      value: stats?.pendingOrders || 0,
      format: 'number',
      icon: BuildingStorefrontIcon,
      color: 'orange',
      bgColor: 'bg-orange-50',
      iconBg: 'bg-orange-100',
      iconColor: 'text-orange-600',
      urgent: stats?.pendingOrders > 5,
    },
  ];

  const formatValue = (value, format) => {
    if (format === 'currency') {
      return new Intl.NumberFormat('ar-SA', {
        style: 'decimal',
        maximumFractionDigits: 0,
      }).format(value) + ' ر.س';
    }
    return new Intl.NumberFormat('ar-SA').format(value);
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white rounded-xl shadow-sm p-6 animate-pulse">
            <div className="flex items-center">
              <div className="w-12 h-12 bg-gray-200 rounded-lg" />
              <div className="mr-4 flex-1">
                <div className="h-4 bg-gray-200 rounded w-20 mb-2" />
                <div className="h-8 bg-gray-200 rounded w-24" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {cards.map((card, index) => (
        <div
          key={index}
          className={`bg-white rounded-xl shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden`}
        >
          <div className="p-6">
            <div className="flex items-center">
              <div className={`${card.iconBg} p-3 rounded-lg`}>
                <card.icon className={`h-6 w-6 ${card.iconColor}`} />
              </div>
              <div className="mr-4 flex-1">
                <p className="text-sm text-gray-500 mb-1">{card.title}</p>
                <p className={`text-2xl font-bold text-gray-900 ${card.urgent ? 'text-orange-600' : ''}`}>
                  {formatValue(card.value, card.format)}
                </p>
              </div>
            </div>

            {/* Change indicator */}
            {card.change !== undefined && (
              <div className="mt-4 flex items-center">
                {card.changeType === 'increase' ? (
                  <>
                    <ArrowUpIcon className="h-4 w-4 text-green-500" />
                    <span className="text-sm text-green-500 mr-1">+{card.change}%</span>
                  </>
                ) : (
                  <>
                    <ArrowDownIcon className="h-4 w-4 text-red-500" />
                    <span className="text-sm text-red-500 mr-1">-{card.change}%</span>
                  </>
                )}
                <span className="text-sm text-gray-400 mr-2">من الشهر الماضي</span>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default StatsCards;
