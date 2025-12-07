import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../App';
import axios from 'axios';
import {
  BuildingOffice2Icon,
  TruckIcon,
  StarIcon,
  UserGroupIcon,
  ShoppingCartIcon,
  MagnifyingGlassIcon,
  MapPinIcon,
  PhoneIcon,
  EnvelopeIcon,
  CheckIcon
} from '@heroicons/react/24/outline';

const HomePage = () => {
  const { isAuthenticated, user } = useAuth();
  const navigate = useNavigate();
  const [categories, setCategories] = useState([]);
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [stats, setStats] = useState({});
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchCategories();
    fetchFeaturedProducts();
    fetchStats();
  }, []);

  const fetchCategories = async () => {
    try {
      const response = await axios.get('/categories');
      setCategories(response.data.categories);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const fetchFeaturedProducts = async () => {
    try {
      const response = await axios.get('/products?limit=8');
      setFeaturedProducts(response.data);
    } catch (error) {
      console.error('Error fetching featured products:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get('/platform/stats/');
      setStats({
        totalSuppliers: response.data.total_suppliers || 0,
        totalProducts: response.data.total_products || 0,
        totalOrders: response.data.total_orders || 0,
        totalUsers: response.data.total_users || 0,
        averageRating: response.data.average_rating || 0
      });
    } catch (error) {
      // في حالة خطأ نعرض صفر بدلاً من أرقام وهمية
      console.error('Error fetching stats:', error);
      setStats({
        totalSuppliers: 0,
        totalProducts: 0,
        totalOrders: 0,
        totalUsers: 0,
        averageRating: 0
      });
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/products?search=${encodeURIComponent(searchQuery)}`);
    }
  };

  const categoryIcons = {
    concrete: '🏗️',
    rebar: '⚙️',
    steel: '🔩',
    blocks: '🧱',
    wood: '🪵',
    sand: '⛰️',
    plumbing: '🔧',
    electrical: '⚡',
    paints: '🎨',
    ceramics: '🏺',
    kitchens: '🍽️',
    insulation: '🧊',
    tools: '🔨',
    general: '🏠'
  };

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-blue-900 via-blue-800 to-purple-900 text-white">
        <div className="absolute inset-0 hero-pattern"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold mb-6 animate-fade-in-up">
              منصة مواد البناء الرائدة
              <span className="block text-blue-300 text-3xl md:text-4xl mt-2">في المملكة العربية السعودية</span>
            </h1>
            <p className="text-xl md:text-2xl mb-8 text-blue-100 max-w-3xl mx-auto animate-fade-in-up">
              اكتشف أفضل مواد البناء من موردين موثوقين، واحصل على كل ما تحتاجه لمشروعك في مكان واحد
            </p>
            
            {/* Search Bar */}
            <form onSubmit={handleSearch} className="max-w-2xl mx-auto mb-8 animate-fade-in-up">
              <div className="flex bg-white rounded-2xl shadow-2xl p-2">
                <input
                  type="text"
                  placeholder="ابحث عن مواد البناء..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="flex-1 px-6 py-4 text-gray-900 text-lg rounded-xl border-0 focus:outline-none"
                />
                <button
                  type="submit"
                  className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-8 py-4 rounded-xl hover:from-blue-600 hover:to-purple-700 transition-all duration-300 flex items-center"
                >
                  <MagnifyingGlassIcon className="h-6 w-6 ml-2" />
                  بحث
                </button>
              </div>
            </form>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center animate-fade-in-up">
              {!isAuthenticated ? (
                <>
                  <Link to="/register" className="btn-primary text-lg px-8 py-4">
                    ابدأ رحلتك معنا
                  </Link>
                  <Link to="/products" className="btn-secondary text-lg px-8 py-4">
                    تصفح المنتجات
                  </Link>
                </>
              ) : (
                <>
                  <Link to="/dashboard" className="btn-primary text-lg px-8 py-4">
                    لوحة التحكم
                  </Link>
                  <Link to="/products" className="btn-secondary text-lg px-8 py-4">
                    تصفح المنتجات
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <UserGroupIcon className="h-8 w-8 text-blue-600" />
              </div>
              <h3 className="text-3xl font-bold text-gray-900">{stats.totalSuppliers}+</h3>
              <p className="text-gray-600">مورد موثوق</p>
            </div>
            <div className="text-center">
              <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <BuildingOffice2Icon className="h-8 w-8 text-green-600" />
              </div>
              <h3 className="text-3xl font-bold text-gray-900">{stats.totalProducts}+</h3>
              <p className="text-gray-600">منتج متنوع</p>
            </div>
            <div className="text-center">
              <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <ShoppingCartIcon className="h-8 w-8 text-purple-600" />
              </div>
              <h3 className="text-3xl font-bold text-gray-900">{stats.totalOrders}+</h3>
              <p className="text-gray-600">طلب مكتمل</p>
            </div>
            <div className="text-center">
              <div className="bg-orange-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <StarIcon className="h-8 w-8 text-orange-600" />
              </div>
              <h3 className="text-3xl font-bold text-gray-900">{stats.averageRating || '-'}</h3>
              <p className="text-gray-600">تقييم العملاء</p>
            </div>
          </div>
        </div>
      </section>

      {/* Categories Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">فئات مواد البناء</h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              اختر من مجموعة واسعة من مواد البناء عالية الجودة
            </p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-6">
            {categories.map((category) => (
              <Link
                key={category.id}
                to={`/products?category=${category.id}`}
                className="category-card bg-white p-6 rounded-2xl shadow-lg hover:shadow-2xl border border-gray-100 text-center group"
              >
                <div className="text-4xl mb-4 group-hover:scale-110 transition-transform duration-300">
                  {categoryIcons[category.id] || '🏗️'}
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{category.name}</h3>
                <p className="text-sm text-gray-500">{category.name_en}</p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Products */}
      {featuredProducts.length > 0 && (
        <section className="py-20 bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-gray-900 mb-4">المنتجات المميزة</h2>
              <p className="text-xl text-gray-600">أحدث وأفضل المنتجات من موردينا المميزين</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
              {featuredProducts.slice(0, 4).map((product) => (
                <Link
                  key={product.id}
                  to={`/products/${product.id}`}
                  className="product-card bg-white rounded-2xl shadow-lg overflow-hidden group"
                >
                  <div className="aspect-w-1 aspect-h-1 bg-gray-200">
                    {product.images && product.images.length > 0 ? (
                      <img
                        src={product.images[0]}
                        alt={product.name}
                        className="w-full h-48 object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                    ) : (
                      <div className="w-full h-48 bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center">
                        <BuildingOffice2Icon className="h-16 w-16 text-gray-400" />
                      </div>
                    )}
                  </div>
                  <div className="p-6">
                    <h3 className="font-semibold text-gray-900 mb-2 group-hover:text-blue-600 transition-colors">
                      {product.name}
                    </h3>
                    <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                      {product.description}
                    </p>
                    <div className="flex justify-between items-center">
                      <span className="text-2xl font-bold text-blue-600">
                        {product.price} ر.س
                      </span>
                      <span className="text-sm text-gray-500">
                        /{product.unit}
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
            <div className="text-center mt-12">
              <Link to="/products" className="btn-primary text-lg px-8 py-4">
                عرض جميع المنتجات
              </Link>
            </div>
          </div>
        </section>
      )}

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">لماذا تختار منصتنا؟</h2>
            <p className="text-xl text-gray-600">نقدم أفضل تجربة لشراء مواد البناء</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            <div className="text-center">
              <div className="bg-blue-100 w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <CheckIcon className="h-10 w-10 text-blue-600" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">جودة مضمونة</h3>
              <p className="text-gray-600 leading-relaxed">
                جميع منتجاتنا من موردين معتمدين ومطابقة للمواصفات السعودية
              </p>
            </div>
            <div className="text-center">
              <div className="bg-green-100 w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <TruckIcon className="h-10 w-10 text-green-600" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">توصيل سريع</h3>
              <p className="text-gray-600 leading-relaxed">
                خدمة توصيل موثوقة وسريعة لجميع أنحاء المملكة العربية السعودية
              </p>
            </div>
            <div className="text-center">
              <div className="bg-purple-100 w-20 h-20 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <StarIcon className="h-10 w-10 text-purple-600" />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">أسعار تنافسية</h3>
              <p className="text-gray-600 leading-relaxed">
                نضمن لك أفضل الأسعار مع إمكانية المقارنة بين الموردين المختلفين
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Contact Section */}
      <section className="py-20 bg-gray-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold mb-4">تواصل معنا</h2>
            <p className="text-xl text-gray-300">نحن هنا لمساعدتك في جميع احتياجاتك</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            <div className="text-center">
              <div className="bg-blue-600 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                <PhoneIcon className="h-8 w-8" />
              </div>
              <h3 className="text-xl font-bold mb-2">الهاتف</h3>
              <p className="text-gray-300 dir-ltr">920 000 000</p>
            </div>
            <div className="text-center">
              <div className="bg-green-600 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                <EnvelopeIcon className="h-8 w-8" />
              </div>
              <h3 className="text-xl font-bold mb-2">البريد الإلكتروني</h3>
              <p className="text-gray-300">support@diwani.sa</p>
            </div>
            <div className="text-center">
              <div className="bg-purple-600 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-6">
                <MapPinIcon className="h-8 w-8" />
              </div>
              <h3 className="text-xl font-bold mb-2">العنوان</h3>
              <p className="text-gray-300">الرياض، المملكة العربية السعودية</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;