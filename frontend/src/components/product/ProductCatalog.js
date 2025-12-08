import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../../App';
import { useToast } from '../ui/toast';
import axios from 'axios';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  BuildingStorefrontIcon,
  StarIcon,
  ShoppingCartIcon,
  AdjustmentsHorizontalIcon
} from '@heroicons/react/24/outline';

const ProductCatalog = () => {
  const { user, isAuthenticated } = useAuth();
  const { toast } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  
  // Filter states
  const [filters, setFilters] = useState({
    search: searchParams.get('search') || '',
    category: searchParams.get('category') || '',
    min_price: searchParams.get('min_price') || '',
    max_price: searchParams.get('max_price') || '',
    city: searchParams.get('city') || '',
    skip: 0,
    limit: 20
  });
  
  const [showFilters, setShowFilters] = useState(false);

  useEffect(() => {
    fetchCategories();
    fetchProducts(true);
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
      const response = await axios.get('/products/categories');
      setCategories(response.data || []);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchProducts = async (reset = false) => {
    try {
      if (reset) {
        setLoading(true);
      } else {
        setLoadingMore(true);
      }

      const queryParams = { ...filters };
      if (!reset) {
        queryParams.skip = products.length;
      } else {
        queryParams.skip = 0;
      }

      const response = await axios.get('/products/products', { params: queryParams });

      // Handle paginated response from backend
      const productsList = response.data?.items || response.data || [];

      if (reset) {
        setProducts(productsList);
      } else {
        setProducts(prev => [...prev, ...productsList]);
      }

      setHasMore(productsList.length === filters.limit);
    } catch (error) {
      console.error('Error fetching products:', error);
      toast.error('خطأ', 'حدث خطأ في تحميل المنتجات');
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
    fetchProducts(true);
  };

  const handleLoadMore = () => {
    fetchProducts(false);
  };

  const addToCart = async (productId) => {
    if (!isAuthenticated) {
      toast.error('تسجيل الدخول مطلوب', 'يجب تسجيل الدخول لإضافة المنتجات للسلة');
      return;
    }

    if (user?.role !== 'customer') {
      toast.error('غير مسموح', 'يمكن للعملاء فقط إضافة المنتجات للسلة');
      return;
    }

    try {
      await axios.post('/orders/cart/add', null, {
        params: {
          product_id: productId,
          quantity: 1
        }
      });
      toast.success('تم بنجاح', 'تم إضافة المنتج للسلة');
    } catch (error) {
      console.error('Error adding to cart:', error);
      toast.error('خطأ', 'حدث خطأ في إضافة المنتج للسلة');
    }
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
          <h1 className="text-3xl font-bold text-gray-900 mb-4">كتالوج المنتجات</h1>
          
          {/* Search Bar */}
          <form onSubmit={handleSearch} className="flex gap-4 mb-6">
            <div className="flex-1 relative">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400 absolute right-3 top-1/2 transform -translate-y-1/2" />
              <input
                type="text"
                placeholder="ابحث عن المنتجات..."
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
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  {/* Category Filter */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      الفئة
                    </label>
                    <select
                      value={filters.category}
                      onChange={(e) => handleFilterChange('category', e.target.value)}
                      className="input-field"
                    >
                      <option value="">جميع الفئات</option>
                      {categories.map((category) => (
                        <option key={category.id} value={category.id}>
                          {category.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Price Range */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      السعر الأدنى
                    </label>
                    <input
                      type="number"
                      placeholder="0"
                      value={filters.min_price}
                      onChange={(e) => handleFilterChange('min_price', e.target.value)}
                      className="input-field"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      السعر الأعلى
                    </label>
                    <input
                      type="number"
                      placeholder="1000000"
                      value={filters.max_price}
                      onChange={(e) => handleFilterChange('max_price', e.target.value)}
                      className="input-field"
                    />
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
                </div>

                <div className="flex justify-end mt-4 space-x-4 space-x-reverse">
                  <button
                    onClick={() => {
                      setFilters({
                        search: '',
                        category: '',
                        min_price: '',
                        max_price: '',
                        city: '',
                        skip: 0,
                        limit: 20
                      });
                      fetchProducts(true);
                    }}
                    className="btn-secondary"
                  >
                    مسح الفلاتر
                  </button>
                  <button
                    onClick={() => fetchProducts(true)}
                    className="btn-primary"
                  >
                    تطبيق الفلاتر
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Products Grid */}
        {products.length > 0 ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {products.map((product) => (
                <div key={product.id} className="product-card bg-white rounded-2xl shadow-lg overflow-hidden">
                  <Link to={`/products/${product.id}`}>
                    <div className="aspect-w-1 aspect-h-1 bg-gray-200">
                      {product.images && product.images.length > 0 ? (
                        <img
                          src={product.images[0]}
                          alt={product.name}
                          className="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-300"
                        />
                      ) : (
                        <div className="w-full h-48 bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center">
                          <BuildingStorefrontIcon className="h-16 w-16 text-gray-400" />
                        </div>
                      )}
                    </div>
                  </Link>
                  
                  <div className="p-6">
                    <Link to={`/products/${product.id}`}>
                      <h3 className="font-semibold text-gray-900 mb-2 hover:text-blue-600 transition-colors">
                        {product.name}
                      </h3>
                    </Link>
                    
                    <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                      {product.description}
                    </p>
                    
                    <div className="flex items-center mb-4">
                      <div className="flex items-center">
                        {[...Array(5)].map((_, i) => (
                          <StarIcon
                            key={i}
                            className={`h-4 w-4 ${
                              i < Math.floor(product.rating)
                                ? 'text-yellow-400 fill-current'
                                : 'text-gray-300'
                            }`}
                          />
                        ))}
                      </div>
                      <span className="text-sm text-gray-500 mr-2">
                        ({product.total_reviews})
                      </span>
                    </div>
                    
                    <div className="flex justify-between items-center mb-4">
                      <div>
                        <span className="text-2xl font-bold text-blue-600">
                          {product.price} ر.س
                        </span>
                        <span className="text-sm text-gray-500">
                          /{product.unit}
                        </span>
                      </div>
                      <span className="text-sm text-gray-500">
                        متوفر: {product.available_quantity}
                      </span>
                    </div>
                    
                    {isAuthenticated && user?.role === 'customer' && (
                      <button
                        onClick={() => addToCart(product.id)}
                        className="w-full btn-primary flex items-center justify-center"
                      >
                        <ShoppingCartIcon className="h-5 w-5 ml-2" />
                        إضافة للسلة
                      </button>
                    )}
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
            <BuildingStorefrontIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">لا توجد منتجات</h3>
            <p className="text-gray-600 mb-6">لم يتم العثور على منتجات تطابق معايير البحث</p>
            <button
              onClick={() => {
                setFilters({
                  search: '',
                  category: '',
                  min_price: '',
                  max_price: '',
                  city: '',
                  skip: 0,
                  limit: 20
                });
                fetchProducts(true);
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

export default ProductCatalog;