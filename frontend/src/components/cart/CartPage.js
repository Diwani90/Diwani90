import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../App';
import { useToast } from '../ui/toast';
import axios from 'axios';
import {
  ShoppingCartIcon,
  TrashIcon,
  PlusIcon,
  MinusIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline';

const CartPage = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  
  const [cartItems, setCartItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState({});

  useEffect(() => {
    fetchCart();
  }, []);

  const fetchCart = async () => {
    try {
      const response = await axios.get('/cart');
      setCartItems(response.data.items || []);
    } catch (error) {
      console.error('Error fetching cart:', error);
      toast.error('خطأ', 'حدث خطأ في تحميل السلة');
    } finally {
      setLoading(false);
    }
  };

  const updateQuantity = async (itemId, newQuantity) => {
    if (newQuantity < 1) {
      removeItem(itemId);
      return;
    }

    setUpdating(prev => ({ ...prev, [itemId]: true }));
    
    try {
      // Note: This would require an update cart endpoint in the backend
      // For now, we'll remove and re-add
      await axios.delete(`/cart/${itemId}`);
      
      const item = cartItems.find(item => item.cart_item.id === itemId);
      if (item) {
        await axios.post('/cart/add', {
          product_id: item.product.id,
          quantity: newQuantity
        });
      }
      
      await fetchCart();
      toast.success('تم التحديث', 'تم تحديث كمية المنتج');
    } catch (error) {
      console.error('Error updating quantity:', error);
      toast.error('خطأ', 'حدث خطأ في تحديث الكمية');
    } finally {
      setUpdating(prev => ({ ...prev, [itemId]: false }));
    }
  };

  const removeItem = async (itemId) => {
    try {
      await axios.delete(`/cart/${itemId}`);
      setCartItems(prev => prev.filter(item => item.cart_item.id !== itemId));
      toast.success('تم الحذف', 'تم حذف المنتج من السلة');
    } catch (error) {
      console.error('Error removing item:', error);
      toast.error('خطأ', 'حدث خطأ في حذف المنتج');
    }
  };

  const getTotalPrice = () => {
    return cartItems.reduce((total, item) => total + item.total_price, 0);
  };

  const proceedToCheckout = () => {
    if (cartItems.length === 0) {
      toast.error('السلة فارغة', 'أضف منتجات للسلة أولاً');
      return;
    }
    navigate('/checkout');
  };

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
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <ShoppingCartIcon className="h-8 w-8 ml-3" />
            سلة التسوق
          </h1>
          <p className="text-gray-600 mt-2">راجع المنتجات قبل إكمال الطلب</p>
        </div>

        {cartItems.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Cart Items */}
            <div className="lg:col-span-2">
              <div className="card">
                <div className="card-header">
                  <h2 className="text-lg font-semibold text-gray-900">
                    المنتجات ({cartItems.length})
                  </h2>
                </div>
                <div className="card-body">
                  <div className="space-y-6">
                    {cartItems.map((item) => (
                      <div key={item.cart_item.id} className="flex items-center p-4 bg-gray-50 rounded-lg">
                        {/* Product Image */}
                        <div className="w-20 h-20 bg-gray-200 rounded-lg overflow-hidden ml-4 flex-shrink-0">
                          {item.product.images && item.product.images.length > 0 ? (
                            <img
                              src={item.product.images[0]}
                              alt={item.product.name}
                              className="w-full h-full object-cover"
                            />
                          ) : (
                            <div className="w-full h-full bg-gray-300 flex items-center justify-center">
                              <ShoppingCartIcon className="h-8 w-8 text-gray-400" />
                            </div>
                          )}
                        </div>

                        {/* Product Info */}
                        <div className="flex-1">
                          <Link
                            to={`/products/${item.product.id}`}
                            className="font-semibold text-gray-900 hover:text-blue-600 transition-colors"
                          >
                            {item.product.name}
                          </Link>
                          <p className="text-sm text-gray-600 mt-1">
                            {item.product.price} ر.س / {item.product.unit}
                          </p>
                          <p className="text-sm text-gray-500 mt-1">
                            الحد الأدنى: {item.product.minimum_order} {item.product.unit}
                          </p>
                        </div>

                        {/* Quantity Controls */}
                        <div className="flex items-center space-x-3 space-x-reverse mx-4">
                          <button
                            onClick={() => updateQuantity(
                              item.cart_item.id, 
                              item.cart_item.quantity - 1
                            )}
                            disabled={updating[item.cart_item.id]}
                            className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-100 transition-colors"
                          >
                            <MinusIcon className="h-4 w-4" />
                          </button>
                          
                          <span className="w-12 text-center font-medium">
                            {item.cart_item.quantity}
                          </span>
                          
                          <button
                            onClick={() => updateQuantity(
                              item.cart_item.id, 
                              item.cart_item.quantity + 1
                            )}
                            disabled={
                              updating[item.cart_item.id] || 
                              item.cart_item.quantity >= item.product.available_quantity
                            }
                            className="w-8 h-8 rounded-full border border-gray-300 flex items-center justify-center hover:bg-gray-100 transition-colors disabled:opacity-50"
                          >
                            <PlusIcon className="h-4 w-4" />
                          </button>
                        </div>

                        {/* Price and Remove */}
                        <div className="text-left">
                          <p className="font-bold text-lg text-blue-600">
                            {item.total_price} ر.س
                          </p>
                          <button
                            onClick={() => removeItem(item.cart_item.id)}
                            className="text-red-600 hover:text-red-700 mt-2 flex items-center text-sm"
                          >
                            <TrashIcon className="h-4 w-4 ml-1" />
                            حذف
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Order Summary */}
            <div className="lg:col-span-1">
              <div className="card">
                <div className="card-header">
                  <h2 className="text-lg font-semibold text-gray-900">ملخص الطلب</h2>
                </div>
                <div className="card-body">
                  <div className="space-y-4">
                    <div className="flex justify-between">
                      <span className="text-gray-600">المجموع الفرعي:</span>
                      <span className="font-semibold">{getTotalPrice()} ر.س</span>
                    </div>
                    
                    <div className="flex justify-between">
                      <span className="text-gray-600">الشحن:</span>
                      <span className="font-semibold">يحدد لاحقاً</span>
                    </div>
                    
                    <div className="flex justify-between">
                      <span className="text-gray-600">الضريبة:</span>
                      <span className="font-semibold">يحدد لاحقاً</span>
                    </div>
                    
                    <hr className="border-gray-200" />
                    
                    <div className="flex justify-between text-lg">
                      <span className="font-bold">المجموع:</span>
                      <span className="font-bold text-blue-600">{getTotalPrice()} ر.س</span>
                    </div>
                  </div>

                  <button
                    onClick={proceedToCheckout}
                    className="w-full btn-primary mt-6 flex items-center justify-center"
                  >
                    متابعة للدفع
                    <ArrowRightIcon className="h-5 w-5 mr-2" />
                  </button>

                  <Link
                    to="/products"
                    className="w-full btn-secondary mt-3 text-center block"
                  >
                    متابعة التسوق
                  </Link>
                </div>
              </div>

              {/* Trust Badges */}
              <div className="mt-6 text-center">
                <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                  <div className="flex items-center justify-center">
                    <ShoppingCartIcon className="h-5 w-5 ml-1 text-green-500" />
                    دفع آمن
                  </div>
                  <div className="flex items-center justify-center">
                    <ArrowRightIcon className="h-5 w-5 ml-1 text-blue-500" />
                    توصيل سريع
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* Empty Cart */
          <div className="text-center py-16">
            <ShoppingCartIcon className="h-24 w-24 text-gray-400 mx-auto mb-6" />
            <h2 className="text-2xl font-bold text-gray-900 mb-4">سلة التسوق فارغة</h2>
            <p className="text-gray-600 mb-8">ابدأ بإضافة منتجات إلى سلة التسوق</p>
            <Link to="/products" className="btn-primary">
              تصفح المنتجات
            </Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default CartPage;