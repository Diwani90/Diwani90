/**
 * ===================================
 * منصة ديواني - Sales Chart Component
 * Professional sales analytics chart
 * ===================================
 */

import React, { useMemo } from 'react';

const SalesChart = ({ data = [], loading = false, period = 'month' }) => {
  // Calculate chart dimensions and values
  const chartData = useMemo(() => {
    if (!data || data.length === 0) {
      // Generate demo data if no data provided
      return [
        { date: '1 يناير', sales: 3200 },
        { date: '5 يناير', sales: 4800 },
        { date: '10 يناير', sales: 8500 },
        { date: '15 يناير', sales: 6200 },
        { date: '20 يناير', sales: 9800 },
        { date: '25 يناير', sales: 7400 },
        { date: '30 يناير', sales: 10200 },
      ];
    }
    return data;
  }, [data]);

  const maxValue = Math.max(...chartData.map((d) => d.sales));
  const minValue = Math.min(...chartData.map((d) => d.sales));
  const range = maxValue - minValue || 1;

  // Generate SVG path for the line
  const generatePath = () => {
    const width = 100;
    const height = 60;
    const padding = 5;

    const points = chartData.map((d, i) => {
      const x = padding + (i / (chartData.length - 1)) * (width - padding * 2);
      const y = height - padding - ((d.sales - minValue) / range) * (height - padding * 2);
      return `${x},${y}`;
    });

    return `M ${points.join(' L ')}`;
  };

  // Generate area path
  const generateAreaPath = () => {
    const width = 100;
    const height = 60;
    const padding = 5;

    const points = chartData.map((d, i) => {
      const x = padding + (i / (chartData.length - 1)) * (width - padding * 2);
      const y = height - padding - ((d.sales - minValue) / range) * (height - padding * 2);
      return `${x},${y}`;
    });

    const firstX = padding;
    const lastX = padding + ((chartData.length - 1) / (chartData.length - 1)) * (width - padding * 2);

    return `M ${firstX},${height - padding} L ${points.join(' L ')} L ${lastX},${height - padding} Z`;
  };

  // Y-axis labels
  const yLabels = [
    { value: maxValue, label: formatNumber(maxValue) },
    { value: (maxValue + minValue) / 2, label: formatNumber((maxValue + minValue) / 2) },
    { value: minValue, label: formatNumber(minValue) },
  ];

  function formatNumber(num) {
    if (num >= 1000) {
      return (num / 1000).toFixed(0) + 'K';
    }
    return num.toString();
  }

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="h-4 bg-gray-200 rounded w-32 mb-4 animate-pulse" />
        <div className="h-64 bg-gray-100 rounded animate-pulse" />
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">إحصائيات المبيعات</h3>
        <div className="flex items-center gap-2">
          <select
            className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
            defaultValue={period}
          >
            <option value="week">هذا الأسبوع</option>
            <option value="month">هذا الشهر</option>
            <option value="year">هذا العام</option>
          </select>
        </div>
      </div>

      {/* Chart Container */}
      <div className="relative h-64">
        {/* Y-axis labels */}
        <div className="absolute right-0 top-0 bottom-0 w-12 flex flex-col justify-between py-4 text-xs text-gray-500">
          {yLabels.map((label, i) => (
            <span key={i}>{label.label}</span>
          ))}
        </div>

        {/* Chart area */}
        <div className="absolute left-0 top-0 bottom-0 right-14">
          <svg
            viewBox="0 0 100 60"
            className="w-full h-full"
            preserveAspectRatio="none"
          >
            {/* Grid lines */}
            <line x1="5" y1="10" x2="95" y2="10" stroke="#e5e7eb" strokeWidth="0.2" />
            <line x1="5" y1="30" x2="95" y2="30" stroke="#e5e7eb" strokeWidth="0.2" />
            <line x1="5" y1="50" x2="95" y2="50" stroke="#e5e7eb" strokeWidth="0.2" />

            {/* Gradient fill */}
            <defs>
              <linearGradient id="salesGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.05" />
              </linearGradient>
            </defs>

            {/* Area fill */}
            <path
              d={generateAreaPath()}
              fill="url(#salesGradient)"
            />

            {/* Line */}
            <path
              d={generatePath()}
              fill="none"
              stroke="#3b82f6"
              strokeWidth="0.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Data points */}
            {chartData.map((d, i) => {
              const x = 5 + (i / (chartData.length - 1)) * 90;
              const y = 55 - ((d.sales - minValue) / range) * 45;
              return (
                <g key={i}>
                  <circle
                    cx={x}
                    cy={y}
                    r="1"
                    fill="#3b82f6"
                    className="cursor-pointer"
                  />
                  {/* Hover tooltip would go here */}
                </g>
              );
            })}
          </svg>
        </div>

        {/* X-axis labels */}
        <div className="absolute bottom-0 right-14 left-0 flex justify-between text-xs text-gray-500">
          {chartData.map((d, i) => (
            <span key={i} className="transform -rotate-0">
              {d.date}
            </span>
          ))}
        </div>
      </div>

      {/* Summary */}
      <div className="mt-6 pt-4 border-t border-gray-100 flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">إجمالي المبيعات</p>
          <p className="text-xl font-bold text-gray-900">
            {new Intl.NumberFormat('ar-SA').format(
              chartData.reduce((sum, d) => sum + d.sales, 0)
            )}{' '}
            ر.س
          </p>
        </div>
        <div className="flex items-center text-green-500">
          <svg className="w-4 h-4 ml-1" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z"
              clipRule="evenodd"
            />
          </svg>
          <span className="text-sm font-medium">+18.3% من الشهر الماضي</span>
        </div>
      </div>
    </div>
  );
};

export default SalesChart;
