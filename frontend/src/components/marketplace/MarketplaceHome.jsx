/**
 * ===================================
 * منصة ديواني - Marketplace Homepage
 * Professional customer-facing storefront
 * ===================================
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { productsService, storesService } from '../../services/api';
import {
  MagnifyingGlassIcon,
  MapPinIcon,
  TruckIcon,
  ShieldCheckIcon,
  CreditCardIcon,
  PhoneIcon,
  BuildingStorefrontIcon,
  ArrowLeftIcon,
  StarIcon,
  HeartIcon,
  ShoppingCartIcon,
} from '@heroicons/react/24/outline';
import { StarIcon as StarSolidIcon } from '@heroicons/react/24/solid';

// Building materials categories with icons
const CATEGORIES = [
  { id: 'cement', name: 'أسمنت', icon: '🏗️', color: 'bg-gray-100' },
  { id: 'steel', name: 'حديد', icon: '🔩', color: 'bg-red-50' },
  { id: 'blocks', name: 'بلوك وطوب', icon: '🧱', color: 'bg-orange-50' },
  { id: 'sand', name: 'رمل وحصى', icon: '⛱️', color: 'bg-yellow-50' },
  { id: 'wood', name: 'خشب', icon: '🪵', color: 'bg-amber-50' },
  { id: 'paint', name: 'دهانات', icon: '🎨', color: 'bg-blue-50' },
  { id: 'plumbing', name: 'سباكة', icon: '🚿', color: 'bg-cyan-50' },
  { id: 'electrical', name: 'كهرباء', icon: '💡', color: 'bg-yellow-50' },
  { id: 'tiles', name: 'بلاط وسيراميك', icon: '🔲', color: 'bg-purple-50' },
  { id: 'insulation', name: 'عزل', icon: '🛡️', color: 'bg-green-50' },
];

// Saudi cities for location selector
const CITIES = [
  'الرياض', 'جدة', 'مكة المكرمة', 'المدينة المنورة', 'الدمام',
  'الخبر', 'الطائف', 'بريدة', 'تبوك', 'خميس مشيط',
];

const MarketplaceHome = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCity, setSelectedCity] = useState('الرياض');
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [topStores, setTopStores] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHomeData();
  }, []);

  const fetchHomeData = async () => {
    try {
      // Fetch featured products and top stores
      // Using demo data for development
      await new Promise(resolve => setTimeout(resolve, 800));

      setFeaturedProducts([
        {
          id: '1',
          name: 'أسمنت بورتلاند 50 كجم',
          price: 25,
          compare_price: 28,
          image: '/api/placeholder/300/300',
          store_name: 'مؤسسة البناء الحديث',
          rating: 4.8,
          reviews_count: 124,
          is_featured: true,
        },
        {
          id: '2',
          name: 'حديد تسليح 12mm - طن',
          price: 3500,
          compare_price: null,
          image: '/api/placeholder/300/300',
          store_name: 'مصانع الحديد السعودية',
          rating: 4.9,
          reviews_count: 89,
          is_featured: true,
        },
        {
          id: '3',
          name: 'بلوك خرساني 20x20x40',
          price: 3.5,
          compare_price: 4,
          image: '/api/placeholder/300/300',
          store_name: 'مصنع البلوك المتين',
          rating: 4.7,
          reviews_count: 256,
          is_featured: true,
        },
        {
          id: '4',
          name: 'رمل أبيض ناعم - متر',
          price: 80,
          compare_price: null,
          image: '/api/placeholder/300/300',
          store_name: 'شركة الرمال الذهبية',
          rating: 4.6,
          reviews_count: 78,
          is_featured: true,
        },
        {
          id: '5',
          name: 'خشب صنوبر مستورد',
          price: 120,
          compare_price: 140,
          image: '/api/placeholder/300/300',
          store_name: 'مؤسسة الأخشاب الفاخرة',
          rating: 4.5,
          reviews_count: 45,
          is_featured: true,
        },
        {
          id: '6',
          name: 'دهان جوتن داخلي 18 لتر',
          price: 380,
          compare_price: 420,
          image: '/api/placeholder/300/300',
          store_name: 'معرض الدهانات المتكامل',
          rating: 4.9,
          reviews_count: 312,
          is_featured: true,
        },
      ]);

      setTopStores([
        {
          id: '1',
          name: 'مؤسسة البناء الحديث',
          logo: '/api/placeholder/80/80',
          rating: 4.8,
          products_count: 156,
          city: 'الرياض',
          is_verified: true,
        },
        {
          id: '2',
          name: 'مصانع الحديد السعودية',
          logo: '/api/placeholder/80/80',
          rating: 4.9,
          products_count: 89,
          city: 'جدة',
          is_verified: true,
        },
        {
          id: '3',
          name: 'مصنع البلوك المتين',
          logo: '/api/placeholder/80/80',
          rating: 4.7,
          products_count: 234,
          city: 'الدمام',
          is_verified: true,
        },
        {
          id: '4',
          name: 'شركة الرمال الذهبية',
          logo: '/api/placeholder/80/80',
          rating: 4.6,
          products_count: 45,
          city: 'الرياض',
          is_verified: false,
        },
      ]);
    } catch (error) {
      console.error('Error fetching home data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      window.location.href = `/products?search=${encodeURIComponent(searchQuery)}`;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50" dir="rtl">
      {/* Hero Section */}
      <section className="relative bg-gradient-to-bl from-blue-900 via-blue-800 to-blue-900 overflow-hidden">
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0" style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
          }} />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-32">
          <div className="text-center">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white mb-6">
              منصة <span className="text-yellow-400">ديواني</span> لمواد البناء
            </h1>
            <p className="text-xl text-blue-100 mb-10 max-w-3xl mx-auto">
              أكبر سوق إلكتروني لمواد البناء في المملكة العربية السعودية
              <br />
              أسعار منافسة • توصيل سريع • موردين موثوقين
            </p>

            {/* Search Box */}
            <form onSubmit={handleSearch} className="max-w-3xl mx-auto">
              <div className="flex flex-col md:flex-row gap-4 bg-white rounded-2xl p-2 shadow-2xl">
                {/* City selector */}
                <div className="flex items-center px-4 border-l border-gray-200 md:w-48">
                  <MapPinIcon className="h-5 w-5 text-gray-400 ml-2" />
                  <select
                    value={selectedCity}
                    onChange={(e) => setSelectedCity(e.target.value)}
                    className="w-full bg-transparent text-gray-700 focus:outline-none"
                  >
                    {CITIES.map((city) => (
                      <option key={city} value={city}>{city}</option>
                    ))}
                  </select>
                </div>

                {/* Search input */}
                <div className="flex-1 flex items-center">
                  <MagnifyingGlassIcon className="h-5 w-5 text-gray-400 ml-2" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="ابحث عن أسمنت، حديد، بلوك..."
                    className="w-full py-3 px-2 text-gray-700 placeholder-gray-400 focus:outline-none"
                  />
                </div>

                {/* Search button */}
                <button
                  type="submit"
                  className="bg-blue-600 text-white px-8 py-3 rounded-xl font-medium hover:bg-blue-700 transition-colors"
                >
                  ابحث
                </button>
              </div>
            </form>

            {/* Popular searches */}
            <div className="mt-6 flex flex-wrap justify-center gap-2">
              <span className="text-blue-200 text-sm">الأكثر بحثاً:</span>
              {['أسمنت', 'حديد تسليح', 'بلوك', 'رمل', 'سيراميك'].map((term) => (
                <Link
                  key={term}
                  to={`/products?search=${term}`}
                  className="px-3 py-1 bg-white/10 text-white text-sm rounded-full hover:bg-white/20 transition-colors"
                >
                  {term}
                </Link>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Categories Section */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">تصفح حسب التصنيف</h2>
            <p className="text-gray-500">جميع مواد البناء التي تحتاجها في مكان واحد</p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {CATEGORIES.map((category) => (
              <Link
                key={category.id}
                to={`/products?category=${category.id}`}
                className={`${category.color} rounded-2xl p-6 text-center hover:shadow-lg transition-all duration-300 hover:-translate-y-1`}
              >
                <span className="text-4xl block mb-3">{category.icon}</span>
                <span className="font-medium text-gray-900">{category.name}</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {[
              { icon: TruckIcon, title: 'توصيل سريع', desc: 'توصيل لجميع مناطق المملكة' },
              { icon: ShieldCheckIcon, title: 'ضمان الجودة', desc: 'منتجات أصلية 100%' },
              { icon: CreditCardIcon, title: 'دفع آمن', desc: 'مدى، Apple Pay، تقسيط' },
              { icon: PhoneIcon, title: 'دعم فني', desc: 'متاحون على مدار الساعة' },
            ].map((feature, index) => (
              <div key={index} className="text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <feature.icon className="h-8 w-8 text-blue-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-sm text-gray-500">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Products Section */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-3xl font-bold text-gray-900">المنتجات المميزة</h2>
              <p className="text-gray-500 mt-2">أفضل العروض والأسعار</p>
            </div>
            <Link
              to="/products"
              className="flex items-center text-blue-600 hover:text-blue-700 font-medium"
            >
              عرض الكل
              <ArrowLeftIcon className="h-5 w-5 mr-2" />
            </Link>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-6">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="bg-gray-100 rounded-2xl p-4 animate-pulse">
                  <div className="h-48 bg-gray-200 rounded-xl mb-4" />
                  <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
                  <div className="h-4 bg-gray-200 rounded w-1/2" />
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-6">
              {featuredProducts.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Top Stores Section */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-3xl font-bold text-gray-900">الموردين المميزين</h2>
              <p className="text-gray-500 mt-2">موردين موثوقين بتقييمات عالية</p>
            </div>
            <Link
              to="/suppliers"
              className="flex items-center text-blue-600 hover:text-blue-700 font-medium"
            >
              عرض الكل
              <ArrowLeftIcon className="h-5 w-5 mr-2" />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {topStores.map((store) => (
              <StoreCard key={store.id} store={store} />
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-l from-blue-600 to-blue-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            هل أنت مورد مواد بناء؟
          </h2>
          <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
            انضم إلى منصة ديواني واوصل لآلاف العملاء في جميع أنحاء المملكة
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/register?type=vendor"
              className="px-8 py-4 bg-white text-blue-600 font-bold rounded-xl hover:bg-gray-100 transition-colors"
            >
              سجل كمورد الآن
            </Link>
            <Link
              to="/about"
              className="px-8 py-4 border-2 border-white text-white font-bold rounded-xl hover:bg-white/10 transition-colors"
            >
              تعرف على المزيد
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center mb-4">
                <BuildingStorefrontIcon className="h-8 w-8 text-blue-400" />
                <span className="text-xl font-bold mr-2">ديواني</span>
              </div>
              <p className="text-gray-400 text-sm">
                منصة سعودية رائدة في التجارة الإلكترونية لمواد البناء
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">روابط سريعة</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li><Link to="/products" className="hover:text-white">المنتجات</Link></li>
                <li><Link to="/suppliers" className="hover:text-white">الموردين</Link></li>
                <li><Link to="/about" className="hover:text-white">من نحن</Link></li>
                <li><Link to="/contact" className="hover:text-white">اتصل بنا</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">خدمة العملاء</h4>
              <ul className="space-y-2 text-gray-400 text-sm">
                <li><Link to="/help" className="hover:text-white">مركز المساعدة</Link></li>
                <li><Link to="/shipping" className="hover:text-white">سياسة الشحن</Link></li>
                <li><Link to="/returns" className="hover:text-white">الإرجاع والاستبدال</Link></li>
                <li><Link to="/faq" className="hover:text-white">الأسئلة الشائعة</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">تواصل معنا</h4>
              <p className="text-gray-400 text-sm mb-2">920000123</p>
              <p className="text-gray-400 text-sm mb-4">support@diwani.sa</p>
              <div className="flex gap-4">
                <a href="#" className="text-gray-400 hover:text-white">
                  <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z" />
                  </svg>
                </a>
                <a href="#" className="text-gray-400 hover:text-white">
                  <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073z" />
                  </svg>
                </a>
              </div>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400 text-sm">
            <p>© 2024 ديواني. جميع الحقوق محفوظة.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

// Product Card Component
const ProductCard = ({ product }) => {
  const discount = product.compare_price
    ? Math.round(((product.compare_price - product.price) / product.compare_price) * 100)
    : null;

  return (
    <Link to={`/products/${product.id}`} className="group">
      <div className="bg-white rounded-2xl overflow-hidden shadow-sm hover:shadow-lg transition-all duration-300 group-hover:-translate-y-1">
        <div className="relative">
          <div className="aspect-square bg-gray-100">
            <img
              src={product.image}
              alt={product.name}
              className="w-full h-full object-cover"
            />
          </div>
          {discount && (
            <span className="absolute top-3 right-3 px-2 py-1 bg-red-500 text-white text-xs font-bold rounded-lg">
              -{discount}%
            </span>
          )}
          <button
            className="absolute top-3 left-3 p-2 bg-white/80 rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-white"
            onClick={(e) => {
              e.preventDefault();
              // Add to wishlist
            }}
          >
            <HeartIcon className="h-5 w-5 text-gray-600" />
          </button>
        </div>
        <div className="p-4">
          <p className="text-xs text-gray-500 mb-1">{product.store_name}</p>
          <h3 className="font-medium text-gray-900 mb-2 line-clamp-2 min-h-[2.5rem]">
            {product.name}
          </h3>
          <div className="flex items-center mb-2">
            <div className="flex items-center">
              {[1, 2, 3, 4, 5].map((star) => (
                star <= Math.floor(product.rating) ? (
                  <StarSolidIcon key={star} className="h-4 w-4 text-yellow-400" />
                ) : (
                  <StarIcon key={star} className="h-4 w-4 text-gray-300" />
                )
              ))}
            </div>
            <span className="text-xs text-gray-500 mr-1">({product.reviews_count})</span>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <span className="text-lg font-bold text-blue-600">{product.price} ر.س</span>
              {product.compare_price && (
                <span className="text-sm text-gray-400 line-through mr-2">
                  {product.compare_price} ر.س
                </span>
              )}
            </div>
            <button
              className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              onClick={(e) => {
                e.preventDefault();
                // Add to cart
              }}
            >
              <ShoppingCartIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </Link>
  );
};

// Store Card Component
const StoreCard = ({ store }) => (
  <Link to={`/suppliers/${store.id}`} className="group">
    <div className="bg-white rounded-2xl p-6 shadow-sm hover:shadow-lg transition-all duration-300 group-hover:-translate-y-1">
      <div className="flex items-center mb-4">
        <div className="w-16 h-16 bg-gray-100 rounded-xl overflow-hidden ml-4">
          <img
            src={store.logo}
            alt={store.name}
            className="w-full h-full object-cover"
          />
        </div>
        <div>
          <div className="flex items-center">
            <h3 className="font-semibold text-gray-900">{store.name}</h3>
            {store.is_verified && (
              <ShieldCheckIcon className="h-5 w-5 text-blue-500 mr-1" />
            )}
          </div>
          <p className="text-sm text-gray-500">{store.city}</p>
        </div>
      </div>
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center">
          <StarSolidIcon className="h-4 w-4 text-yellow-400 ml-1" />
          <span className="font-medium">{store.rating}</span>
        </div>
        <span className="text-gray-500">{store.products_count} منتج</span>
      </div>
    </div>
  </Link>
);

export default MarketplaceHome;
