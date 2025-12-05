/**
 * ===================================
 * منصة ديواني - Products Page
 * Full products management page
 * ===================================
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { productsService } from '../../../services/api';
import DashboardLayout from '../DashboardLayout';
import { useToast } from '../../ui/toast';
import {
  PlusIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  CubeIcon,
  ArrowUpIcon,
  ArrowDownIcon,
} from '@heroicons/react/24/outline';

const ProductsPage = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showFilters, setShowFilters] = useState(false);

  const fetchProducts = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        page,
        page_size: 10,
        search: search || undefined,
        status: filter !== 'all' ? filter : undefined,
        ordering: `${sortOrder === 'desc' ? '-' : ''}${sortBy}`,
      };

      const response = await productsService.getMyProducts(params);
      setProducts(response.items || []);
      setTotalPages(response.pages || 1);
    } catch (error) {
      console.error('Error fetching products:', error);
      // Use demo data for development
      setProducts([
        { id: '1', name: 'أسمنت بورتلاند', sku: 'CEM-001', price: 25, stock: 500, status: 'active', category: 'أسمنت' },
        { id: '2', name: 'حديد تسليح 12mm', sku: 'STL-012', price: 3500, stock: 200, status: 'active', category: 'حديد' },
        { id: '3', name: 'بلوك خرساني 20cm', sku: 'BLK-020', price: 3.5, stock: 10000, status: 'active', category: 'بلوك' },
        { id: '4', name: 'رمل أبيض ناعم', sku: 'SND-001', price: 80, stock: 50, status: 'low_stock', category: 'رمل وحصى' },
        { id: '5', name: 'طوب أحمر', sku: 'BRK-001', price: 0.5, stock: 0, status: 'out_of_stock', category: 'طوب' },
      ]);
    } finally {
      setLoading(false);
    }
  }, [page, search, filter, sortBy, sortOrder]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  const handleDelete = async (productId) => {
    if (!window.confirm('هل أنت متأكد من حذف هذا المنتج؟')) {
      return;
    }

    try {
      await productsService.deleteProduct(productId);
      setProducts(products.filter((p) => p.id !== productId));
      toast?.success?.('تم الحذف', 'تم حذف المنتج بنجاح');
    } catch (error) {
      console.error('Error deleting product:', error);
      toast?.error?.('خطأ', 'حدث خطأ في حذف المنتج');
    }
  };

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      active: { label: 'نشط', color: 'bg-green-100 text-green-800' },
      low_stock: { label: 'مخزون منخفض', color: 'bg-yellow-100 text-yellow-800' },
      out_of_stock: { label: 'نفذ', color: 'bg-red-100 text-red-800' },
      inactive: { label: 'غير نشط', color: 'bg-gray-100 text-gray-800' },
    };
    return statusMap[status] || statusMap.active;
  };

  const SortIcon = ({ field }) => {
    if (sortBy !== field) return null;
    return sortOrder === 'asc' ? (
      <ArrowUpIcon className="h-4 w-4 inline mr-1" />
    ) : (
      <ArrowDownIcon className="h-4 w-4 inline mr-1" />
    );
  };

  return (
    <DashboardLayout>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">المنتجات</h1>
          <p className="text-gray-500 mt-1">إدارة منتجات متجرك</p>
        </div>
        <Link
          to="/dashboard/products/new"
          className="mt-4 sm:mt-0 inline-flex items-center px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          <PlusIcon className="h-5 w-5 ml-2" />
          إضافة منتج
        </Link>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
        <div className="flex flex-col lg:flex-row lg:items-center gap-4">
          {/* Search */}
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="absolute right-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="ابحث عن منتج..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pr-10 pl-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Filter buttons */}
          <div className="flex items-center gap-2">
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">جميع المنتجات</option>
              <option value="active">نشط</option>
              <option value="low_stock">مخزون منخفض</option>
              <option value="out_of_stock">نفذ</option>
              <option value="inactive">غير نشط</option>
            </select>

            <button
              onClick={() => setShowFilters(!showFilters)}
              className="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <FunnelIcon className="h-5 w-5 text-gray-600" />
            </button>
          </div>
        </div>
      </div>

      {/* Products Table */}
      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-500">جاري التحميل...</p>
          </div>
        ) : products.length === 0 ? (
          <div className="p-12 text-center">
            <CubeIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">لا توجد منتجات</h3>
            <p className="text-gray-500 mb-6">ابدأ بإضافة أول منتج لمتجرك</p>
            <Link
              to="/dashboard/products/new"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              <PlusIcon className="h-5 w-5 ml-2" />
              إضافة منتج
            </Link>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-100">
                  <tr>
                    <th
                      className="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer hover:text-gray-700"
                      onClick={() => handleSort('name')}
                    >
                      <SortIcon field="name" />
                      المنتج
                    </th>
                    <th className="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase">
                      التصنيف
                    </th>
                    <th
                      className="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer hover:text-gray-700"
                      onClick={() => handleSort('price')}
                    >
                      <SortIcon field="price" />
                      السعر
                    </th>
                    <th
                      className="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer hover:text-gray-700"
                      onClick={() => handleSort('stock')}
                    >
                      <SortIcon field="stock" />
                      المخزون
                    </th>
                    <th className="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase">
                      الحالة
                    </th>
                    <th className="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase">
                      الإجراءات
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {products.map((product) => {
                    const status = getStatusBadge(product.status);
                    return (
                      <tr key={product.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <div className="flex items-center">
                            <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                              {product.image ? (
                                <img
                                  src={product.image}
                                  alt={product.name}
                                  className="w-full h-full object-cover rounded-lg"
                                />
                              ) : (
                                <CubeIcon className="h-6 w-6 text-gray-400" />
                              )}
                            </div>
                            <div className="mr-4">
                              <p className="font-medium text-gray-900">{product.name}</p>
                              <p className="text-sm text-gray-500">SKU: {product.sku}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">
                          {product.category}
                        </td>
                        <td className="px-6 py-4">
                          <span className="font-semibold text-gray-900">
                            {new Intl.NumberFormat('ar-SA').format(product.price)} ر.س
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">
                          {new Intl.NumberFormat('ar-SA').format(product.stock)}
                        </td>
                        <td className="px-6 py-4">
                          <span className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${status.color}`}>
                            {status.label}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => navigate(`/dashboard/products/${product.id}`)}
                              className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg"
                              title="عرض"
                            >
                              <EyeIcon className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => navigate(`/dashboard/products/${product.id}/edit`)}
                              className="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded-lg"
                              title="تعديل"
                            >
                              <PencilIcon className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(product.id)}
                              className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
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

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-between">
                <p className="text-sm text-gray-500">
                  الصفحة {page} من {totalPages}
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-3 py-1 border border-gray-200 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
                  >
                    السابق
                  </button>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="px-3 py-1 border border-gray-200 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
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

export default ProductsPage;
