import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../App';
import { useToast } from '../ui/toast';
import axios from 'axios';
import {
  BuildingOfficeIcon,
  StarIcon,
  MapPinIcon,
  ChatBubbleLeftRightIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  UserGroupIcon
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';

const SuppliersPage = () => {
  const { user, isAuthenticated } = useAuth();
  const { toast } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const [suppliers, setSuppliers] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  
  // Filter states
  const [filters, setFilters] = useState({
    search: searchParams.get('search') || '',
    category: searchParams.get('category') || '',
    city: searchParams.get('city') || '',
    skip: 0,
    limit: 20
  });
  
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetchCategories();
    fetchSuppliers(true);
  }, []);

  useEffect(() => {
    // Update URL params when filters change
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value && key !== 'skip' && key !== 'limit') {
        params.set(key, value);
      }
    });
    setSearchParams(params);
  }, [filters]);

  const fetchCategories = async () => {
    try {
      const response = await axios.get('/categories');
      setCategories(response.data.categories);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchSuppliers = async (reset = false) => {
    try {
      if (reset) {
        setLoading(true);
      } else {
        setLoadingMore(true);
      }

      const queryParams = { ...filters };
      if (!reset) {
        queryParams.skip = suppliers.length;
      } else {
        queryParams.skip = 0;
      }

      const response = await axios.get('/suppliers', { params: queryParams });
      
      if (reset) {
        setSuppliers(response.data);
      } else {
        setSuppliers(prev => [...prev, ...response.data]);
      }
      
      setHasMore(response.data.length === filters.limit);
    } catch (error) {
      console.error('Error fetching suppliers:', error);
      toast.error('خطأ', 'حدث خطأ في تحميل الموردين');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      skip: 0
    }));
  };

  const handleSearch = (e) => {
    e.preventDefault();
    fetchSuppliers(true);
  };

  const handleLoadMore = () => {
    fetchSuppliers(false);
  };

  const startChat = (supplierId) => {
    if (!isAuthenticated) {
      toast.error('تسجيل الدخول مطلوب', 'يجب تسجيل الدخول للتواصل مع الموردين');
      return;
    }
    window.location.href = `/chat?with=${supplierId}`;
  };

  const saudiCities = [
    'الرياض', 'جدة', 'مكة المكرمة', 'المدينة المنورة', 'الدمام', 'الخبر', 'الظهران',
    'تبوك', 'بريدة', 'خميس مشيط', 'حائل', 'الجبيل', 'نجران', 'ينبع', 'أبها'
  ];

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
          <h1 className="text-3xl font-bold text-gray-900 mb-4 flex items-center">
            <UserGroupIcon className="h-8 w-8 ml-3" />
            دليل الموردين
          </h1>
          
          {/* Search Bar */}
          <form onSubmit={handleSearch} className="flex gap-4 mb-6">
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400 absolute right-3 top-1/2 transform -translate-y-1/2" />
              <input
                type="text"
                placeholder="ابحث عن الموردين..."
                value={filters.search}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                className="input-field pr-10"
              />
            </div>
            <button type="submit" className="btn-primary">
              بحث
            </button>
            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className="btn-secondary flex items-center"
            >
              <FunnelIcon className="h-5 w-5 ml-2" />
              فلترة
            </button>
          </form>

          {/* Filters */}
          {showFilters && (
            <div className="card mb-6">
              <div className="card-body">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Category Filter */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      التخصص
                    </label>
                    <select
                      value={filters.category}
                      onChange={(e) => handleFilterChange('category', e.target.value)}
                      className="input-field"
                    >
                      <option value="">جميع التخصصات</option>
                      {categories.map((category) => (
                        <option key={category.id} value={category.id}>
                          {category.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* City Filter */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      المدينة
                    </label>
                    <select
                      value={filters.city}
                      onChange={(e) => handleFilterChange('city', e.target.value)}
                      className="input-field"
                    >
                      <option value="">جميع المدن</option>
                      {saudiCities.map((city) => (
                        <option key={city} value={city}>
                          {city}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Actions */}
                  <div className="flex items-end gap-2">
                    <button
                      onClick={() => {
                        setFilters({
                          search: '',
                          category: '',
                          city: '',
                          skip: 0,
                          limit: 20
                        });
                        fetchSuppliers(true);
                      }}
                      className="btn-secondary"
                    >
                      مسح
                    </button>
                    <button
                      onClick={() => fetchSuppliers(true)}
                      className="btn-primary"
                    >
                      تطبيق
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Suppliers Grid */}
        {suppliers.length > 0 ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              {suppliers.map((supplier) => (
                <div key={supplier.id} className="card hover:shadow-lg transition-shadow duration-200">
                  <div className="card-body">
                    {/* Supplier Header */}
                    <div className="flex items-center mb-4">
                      <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center ml-4">
                        <BuildingOfficeIcon className="h-8 w-8 text-blue-600" />
                      </div>
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 mb-1">
                          {supplier.company_name}
                        </h3>
                        <p className="text-sm text-gray-600">{supplier.full_name}</p>
                      </div>
                    </div>

                    {/* Rating */}
                    <div className="flex items-center mb-3">
                      <div className="flex items-center">
                        {[...Array(5)].map((_, i) => (
                          i < Math.floor(supplier.rating) ? (
                            <StarIconSolid key={i} className="h-4 w-4 text-yellow-400" />
                          ) : (
                            <StarIcon key={i} className="h-4 w-4 text-gray-300" />
                          )
                        ))}
                      </div>
                      <span className="text-sm text-gray-600 mr-2">
                        ({supplier.total_reviews} تقييم)
                      </span>
                    </div>

                    {/* Description */}
                    <p className="text-gray-700 text-sm mb-4 line-clamp-3">
                      {supplier.business_description}
                    </p>

                    {/* Categories */}
                    {supplier.categories && supplier.categories.length > 0 && (
                      <div className="mb-4">
                        <div className="flex flex-wrap gap-2">
                          {supplier.categories.slice(0, 3).map((categoryId) => {
                            const category = categories.find(c => c.id === categoryId);
                            return category ? (
                              <span
                                key={categoryId}
                                className="badge badge-primary text-xs"
                              >
                                {category.name}
                              </span>
                            ) : null;
                          })}
                          {supplier.categories.length > 3 && (
                            <span className="badge badge-info text-xs">
                              +{supplier.categories.length - 3}
                            </span>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Location */}
                    {supplier.city && (
                      <div className="flex items-center text-sm text-gray-600 mb-4">
                        <MapPinIcon className="h-4 w-4 ml-1" />
                        {supplier.city}
                      </div>
                    )}

                    {/* Actions */}
                    <div className="flex gap-3">
                      <Link
                        to={`/products?supplier_id=${supplier.id}`}
                        className="flex-1 btn-primary text-center text-sm"
                      >
                        عرض المنتجات
                      </Link>
                      {isAuthenticated && (
                        <button
                          onClick={() => startChat(supplier.id)}
                          className="btn-secondary flex items-center justify-center"
                        >
                          <ChatBubbleLeftRightIcon className="h-4 w-4" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Load More Button */}
            {hasMore && (
              <div className="text-center">
                <button
                  onClick={handleLoadMore}
                  disabled={loadingMore}
                  className="btn-secondary"
                >
                  {loadingMore ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-600 ml-2"></div>
                      جاري التحميل...
                    </div>
                  ) : (
                    'تحميل المزيد'
                  )}
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-16">
            <UserGroupIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">لا توجد موردين</h3>
            <p className="text-gray-600 mb-6">لم يتم العثور على موردين يطابقون معايير البحث</p>
            <button
              onClick={() => {
                setFilters({
                  search: '',
                  category: '',
                  city: '',
                  skip: 0,
                  limit: 20
                });
                fetchSuppliers(true);
              }}
              className="btn-primary"
            >
              مسح الفلاتر
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default SuppliersPage;