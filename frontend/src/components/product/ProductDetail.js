import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../../App';
import { useToast } from '../ui/toast';
import axios from 'axios';
import {
  StarIcon,
  ShoppingCartIcon,
  ChatBubbleLeftRightIcon,
  BuildingStorefrontIcon,
  MapPinIcon,
  TruckIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';

const ProductDetail = () => {
  const { id } = useParams();
  const { user, isAuthenticated } = useAuth();
  const { toast } = useToast();
  
  const [product, setProduct] = useState(null);
  const [supplier, setSupplier] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const [selectedImage, setSelectedImage] = useState(0);

  useEffect(() => {
    fetchProductDetail();
  }, [id]);

  const fetchProductDetail = async () => {
    try {
      const [productResponse, reviewsResponse] = await Promise.all([
        axios.get(`/products/${id}`),
        axios.get(`/reviews?product_id=${id}`)
      ]);
      
      setProduct(productResponse.data);
      setReviews(reviewsResponse.data || []);
      
      // Fetch supplier info
      if (productResponse.data.supplier_id) {
        const supplierResponse = await axios.get(`/suppliers/${productResponse.data.supplier_id}`);
        setSupplier(supplierResponse.data);
      }
    } catch (error) {
      console.error('Error fetching product detail:', error);
      toast.error('خطأ', 'حدث خطأ في تحميل تفاصيل المنتج');
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async () => {
    if (!isAuthenticated) {
      toast.error('تسجيل الدخول مطلوب', 'يجب تسجيل الدخول لإضافة المنتجات للسلة');
      return;
    }

    if (user?.role !== 'customer') {
      toast.error('غير مسموح', 'يمكن للعملاء فقط إضافة المنتجات للسلة');
      return;
    }

    if (quantity < product.minimum_order) {
      toast.error('كمية غير صحيحة', `الحد الأدنى للطلب هو ${product.minimum_order}`);
      return;
    }

    if (quantity > product.available_quantity) {
      toast.error('كمية غير متوفرة', 'الكمية المطلوبة تتجاوز المتوفر في المخزون');
      return;
    }

    try {
      await axios.post('/cart/add', {
        product_id: product.id,
        quantity: quantity
      });
      toast.success('تم بنجاح', 'تم إضافة المنتج للسلة');
    } catch (error) {
      console.error('Error adding to cart:', error);
      toast.error('خطأ', 'حدث خطأ في إضافة المنتج للسلة');
    }
  };

  const startChat = async () => {
    if (!isAuthenticated) {
      toast.error('تسجيل الدخول مطلوب', 'يجب تسجيل الدخول للتواصل مع الموردين');
      return;
    }

    // Navigate to chat with supplier
    window.location.href = `/chat?with=${supplier.id}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">المنتج غير موجود</h1>
          <Link to="/products" className="btn-primary">
            العودة للمنتجات
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Breadcrumb */}
        <nav className="mb-8">
          <ol className="flex items-center space-x-2 space-x-reverse">
            <li>
              <Link to="/" className="text-gray-500 hover:text-gray-700">
                الرئيسية
              </Link>
            </li>
            <li className="text-gray-300">/</li>
            <li>
              <Link to="/products" className="text-gray-500 hover:text-gray-700">
                المنتجات
              </Link>
            </li>
            <li className="text-gray-300">/</li>
            <li className="text-gray-900 font-medium">{product.name}</li>
          </ol>
        </nav>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-12">
          {/* Product Images */}
          <div>
            <div className="aspect-w-1 aspect-h-1 bg-gray-200 rounded-2xl overflow-hidden mb-4">
              {product.images && product.images.length > 0 ? (
                <img
                  src={product.images[selectedImage]}
                  alt={product.name}
                  className="w-full h-96 object-cover"
                />
              ) : (
                <div className="w-full h-96 bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center">
                  <BuildingStorefrontIcon className="h-24 w-24 text-gray-400" />
                </div>
              )}
            </div>
            
            {/* Image Thumbnails */}
            {product.images && product.images.length > 1 && (
              <div className="grid grid-cols-4 gap-4">
                {product.images.map((image, index) => (
                  <button
                    key={index}
                    onClick={() => setSelectedImage(index)}
                    className={`aspect-w-1 aspect-h-1 rounded-lg overflow-hidden border-2 ${
                      selectedImage === index ? 'border-blue-500' : 'border-gray-200'
                    }`}
                  >
                    <img
                      src={image}
                      alt={`${product.name} ${index + 1}`}
                      className="w-full h-20 object-cover"
                    />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Product Info */}
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-4">{product.name}</h1>
            
            {/* Rating */}
            <div className="flex items-center mb-6">
              <div className="flex items-center">
                {[...Array(5)].map((_, i) => (
                  i < Math.floor(product.rating) ? (
                    <StarIconSolid key={i} className="h-5 w-5 text-yellow-400" />
                  ) : (
                    <StarIcon key={i} className="h-5 w-5 text-gray-300" />
                  )
                ))}
              </div>
              <span className="text-sm text-gray-600 mr-2">
                ({product.total_reviews} تقييم)
              </span>
            </div>

            {/* Price */}
            <div className="mb-6">
              <span className="text-4xl font-bold text-blue-600">{product.price} ر.س</span>
              <span className="text-lg text-gray-600 mr-2">/{product.unit}</span>
            </div>

            {/* Description */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">الوصف</h3>
              <p className="text-gray-700 leading-relaxed">{product.description}</p>
            </div>

            {/* Specifications */}
            {product.specifications && Object.keys(product.specifications).length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">المواصفات</h3>
                <div className="space-y-2">
                  {Object.entries(product.specifications).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-gray-600">{key}:</span>
                      <span className="text-gray-900 font-medium">{value}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Availability */}
            <div className="mb-6">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">المتوفر:</span>
                <span className={`font-medium ${
                  product.available_quantity > 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {product.available_quantity > 0 
                    ? `${product.available_quantity} ${product.unit}` 
                    : 'غير متوفر'
                  }
                </span>
              </div>
              <div className="flex items-center justify-between text-sm mt-2">
                <span className="text-gray-600">الحد الأدنى للطلب:</span>
                <span className="text-gray-900 font-medium">
                  {product.minimum_order} {product.unit}
                </span>
              </div>
            </div>

            {/* Quantity and Add to Cart */}
            {isAuthenticated && user?.role === 'customer' && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  الكمية
                </label>
                <div className="flex items-center space-x-4 space-x-reverse mb-4">
                  <button
                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                    className="w-10 h-10 rounded-lg border border-gray-300 flex items-center justify-center hover:bg-gray-50"
                  >
                    -
                  </button>
                  <input
                    type="number"
                    min={product.minimum_order}
                    max={product.available_quantity}
                    value={quantity}
                    onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                    className="w-20 text-center input-field"
                  />
                  <button
                    onClick={() => setQuantity(Math.min(product.available_quantity, quantity + 1))}
                    className="w-10 h-10 rounded-lg border border-gray-300 flex items-center justify-center hover:bg-gray-50"
                  >
                    +
                  </button>
                  <span className="text-sm text-gray-600">{product.unit}</span>
                </div>

                <div className="flex space-x-4 space-x-reverse">
                  <button
                    onClick={addToCart}
                    disabled={product.available_quantity === 0}
                    className="flex-1 btn-primary flex items-center justify-center"
                  >
                    <ShoppingCartIcon className="h-5 w-5 ml-2" />
                    إضافة للسلة
                  </button>
                  <button
                    onClick={startChat}
                    className="btn-secondary flex items-center justify-center"
                  >
                    <ChatBubbleLeftRightIcon className="h-5 w-5 ml-2" />
                    تواصل
                  </button>
                </div>
              </div>
            )}

            {/* Trust Badges */}
            <div className="grid grid-cols-3 gap-4 pt-6 border-t border-gray-200">
              <div className="text-center">
                <ShieldCheckIcon className="h-8 w-8 text-green-500 mx-auto mb-2" />
                <p className="text-xs text-gray-600">جودة مضمونة</p>
              </div>
              <div className="text-center">
                <TruckIcon className="h-8 w-8 text-blue-500 mx-auto mb-2" />
                <p className="text-xs text-gray-600">توصيل سريع</p>
              </div>
              <div className="text-center">
                <ChatBubbleLeftRightIcon className="h-8 w-8 text-purple-500 mx-auto mb-2" />
                <p className="text-xs text-gray-600">دعم فني</p>
              </div>
            </div>
          </div>
        </div>

        {/* Supplier Info */}
        {supplier && (
          <div className="card mb-12">
            <div className="card-header">
              <h2 className="text-xl font-semibold text-gray-900">معلومات المورد</h2>
            </div>
            <div className="card-body">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center ml-4">
                    <BuildingStorefrontIcon className="h-8 w-8 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{supplier.company_name}</h3>
                    <p className="text-gray-600">{supplier.business_description}</p>
                    <div className="flex items-center mt-2">
                      <div className="flex items-center ml-4">
                        {[...Array(5)].map((_, i) => (
                          i < Math.floor(supplier.rating) ? (
                            <StarIconSolid key={i} className="h-4 w-4 text-yellow-400" />
                          ) : (
                            <StarIcon key={i} className="h-4 w-4 text-gray-300" />
                          )
                        ))}
                      </div>
                      <span className="text-sm text-gray-600">({supplier.total_reviews} تقييم)</span>
                    </div>
                  </div>
                </div>
                <div className="text-left">
                  <Link
                    to={`/suppliers/${supplier.id}`}
                    className="btn-secondary mb-2 block"
                  >
                    عرض المتجر
                  </Link>
                  {isAuthenticated && (
                    <button
                      onClick={startChat}
                      className="btn-primary flex items-center"
                    >
                      <ChatBubbleLeftRightIcon className="h-4 w-4 ml-1" />
                      تواصل
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Reviews Section */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-xl font-semibold text-gray-900">التقييمات والمراجعات</h2>
          </div>
          <div className="card-body">
            {reviews.length > 0 ? (
              <div className="space-y-6">
                {reviews.map((review) => (
                  <div key={review.id} className="border-b border-gray-200 pb-6 last:border-b-0 last:pb-0">
                    <div className="flex items-center mb-3">
                      <div className="flex items-center">
                        {[...Array(5)].map((_, i) => (
                          i < review.rating ? (
                            <StarIconSolid key={i} className="h-4 w-4 text-yellow-400" />
                          ) : (
                            <StarIcon key={i} className="h-4 w-4 text-gray-300" />
                          )
                        ))}
                      </div>
                      <span className="text-sm text-gray-600 mr-3">
                        {new Date(review.created_at).toLocaleDateString('ar-SA')}
                      </span>
                    </div>
                    <p className="text-gray-700">{review.comment}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <StarIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500">لا توجد تقييمات حتى الآن</p>
                <p className="text-sm text-gray-400">كن أول من يقيم هذا المنتج</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductDetail;