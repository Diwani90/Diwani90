/**
 * ===================================
 * منصة ديواني - Products Management Component
 * Dashboard products table with quick actions
 * ===================================
 */

import React from 'react';
import { Link } from 'react-router-dom';
import {
  PlusIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  CubeIcon,
} from '@heroicons/react/24/outline';

const ProductsManagement = ({ products = [], loading = false, onDelete, onEdit }) => {
  // Demo data if no products provided
  const displayProducts = products.length > 0 ? products : [
    { id: 1, name: 'منتج 1', sku: 'لحجر', stock: 30, status: 'active', price: 110 },
    { id: 2, name: 'منتج 2', sku: 'خنطق', stock: 120, status: 'active', price: 240 },
    { id: 3, name: 'منتج 3', sku: 'عبرنقش', stock: 80, status: 'active', price: 180 },
    { id: 4, name: 'منتج 4', sku: 'نطط', stock: 250, status: 'low_stock', price: 300 },
  ];

  const getStockStatus = (stock) => {
    if (stock <= 10) return { label: 'نفذ', color: 'bg-red-100 text-red-800' };
    if (stock <= 50) return { label: 'منخفض', color: 'bg-yellow-100 text-yellow-800' };
    return { label: 'متوفر', color: 'bg-green-100 text-green-800' };
  };

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
                <div className="w-12 h-12 bg-gray-200 rounded-lg animate-pulse" />
                <div className="mr-4">
                  <div className="h-4 bg-gray-200 rounded w-24 mb-2 animate-pulse" />
                  <div className="h-3 bg-gray-200 rounded w-16 animate-pulse" />
                </div>
              </div>
              <div className="h-6 bg-gray-200 rounded w-20 animate-pulse" />
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
        <h3 className="text-lg font-semibold text-gray-900">إدارة المنتجات</h3>
        <Link
          to="/dashboard/products/new"
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          <PlusIcon className="h-4 w-4 ml-2" />
          إضافة منتج
        </Link>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                المنتج
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                السعر
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                المخزون
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
            {displayProducts.map((product) => {
              const stockStatus = getStockStatus(product.stock);
              return (
                <tr key={product.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                        {product.image ? (
                          <img
                            src={product.image}
                            alt={product.name}
                            className="w-full h-full object-cover rounded-lg"
                          />
                        ) : (
                          <CubeIcon className="h-5 w-5 text-gray-400" />
                        )}
                      </div>
                      <div className="mr-4">
                        <p className="text-sm font-medium text-gray-900">{product.name}</p>
                        <p className="text-xs text-gray-500">SKU: {product.sku}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm font-semibold text-gray-900">
                      {new Intl.NumberFormat('ar-SA').format(product.price)} ر.س
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-gray-600">
                      {new Intl.NumberFormat('ar-SA').format(product.stock)} وحدة
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${stockStatus.color}`}
                    >
                      {stockStatus.label}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <Link
                        to={`/dashboard/products/${product.id}`}
                        className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                        title="عرض"
                      >
                        <EyeIcon className="h-4 w-4" />
                      </Link>
                      <button
                        onClick={() => onEdit && onEdit(product)}
                        className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                        title="تعديل"
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => onDelete && onDelete(product.id)}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        title="حذف"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-100 flex items-center justify-between">
        <p className="text-sm text-gray-500">
          عرض {displayProducts.length} منتج
        </p>
        <Link
          to="/dashboard/products"
          className="text-sm text-blue-600 hover:text-blue-700 font-medium"
        >
          عرض جميع المنتجات
        </Link>
      </div>

      {/* Empty state */}
      {displayProducts.length === 0 && (
        <div className="p-12 text-center">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CubeIcon className="w-8 h-8 text-gray-400" />
          </div>
          <p className="text-gray-500 mb-4">لا توجد منتجات حتى الآن</p>
          <Link
            to="/dashboard/products/new"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            <PlusIcon className="h-4 w-4 ml-2" />
            إضافة أول منتج
          </Link>
        </div>
      )}
    </div>
  );
};

export default ProductsManagement;
