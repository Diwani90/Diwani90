import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../App';
import { useToast } from '../ui/toast';
import axios from 'axios';
import {
  CreditCardIcon,
  MapPinIcon,
  TruckIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline';

const CheckoutPage = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  
  const [cartItems, setCartItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [orderData, setOrderData] = useState({
    delivery_address: user?.delivery_address || '',
    delivery_notes: '',
    payment_method: 'cash'
  });

  useEffect(() => {
    fetchCart();
  }, []);

  const fetchCart = async () => {
    try {
      const response = await axios.get('/cart');
      const items = response.data.items || [];
      
      if (items.length === 0) {
        toast.error('السلة فارغة', 'لا يمكن إتمام الطلب بسلة فارغة');
        navigate('/cart');
        return;
      }
      
      setCartItems(items);
    } catch (error) {
      console.error('Error fetching cart:', error);
      toast.error('خطأ', 'حدث خطأ في تحميل السلة');
      navigate('/cart');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setOrderData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const getTotalPrice = () => {
    return cartItems.reduce((total, item) => total + item.total_price, 0);
  };

  // Group items by supplier
  const getOrdersBySupplier = () => {
    const ordersBySupplier = {};
    
    cartItems.forEach(item => {
      const supplierId = item.product.supplier_id;
      if (!ordersBySupplier[supplierId]) {
        ordersBySupplier[supplierId] = {
          supplier_id: supplierId,
          items: [],
          total: 0
        };
      }
      
      ordersBySupplier[supplierId].items.push({
        product_id: item.product.id,
        quantity: item.cart_item.quantity,
        price: item.product.price,
        name: item.product.name
      });
      
      ordersBySupplier[supplierId].total += item.total_price;
    });
    
    return Object.values(ordersBySupplier);
  };

  const placeOrder = async () => {
    if (!orderData.delivery_address.trim()) {
      toast.error('عنوان مطلوب', 'يرجى إدخال عنوان التوصيل');
      return;
    }

    setProcessing(true);
    
    try {
      const orders = getOrdersBySupplier();
      const createdOrders = [];
      
      // Create separate orders for each supplier
      for (const orderGroup of orders) {
        const orderPayload = {
          supplier_id: orderGroup.supplier_id,
          items: orderGroup.items,
          delivery_address: orderData.delivery_address,
          delivery_notes: orderData.delivery_notes
        };
        
        const response = await axios.post('/orders', orderPayload);
        createdOrders.push(response.data);
      }
      
      toast.success('تم إنشاء الطلب بنجاح', `تم إنشاء ${createdOrders.length} طلب`);
      navigate('/orders');
      
    } catch (error) {
      console.error('Error placing order:', error);
      toast.error('خطأ في الطلب', 'حدث خطأ أثناء إنشاء الطلب');
    } finally {
      setProcessing(false);
    }
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
          <h1 className="text-3xl font-bold text-gray-900">إكمال الطلب</h1>
          <p className="text-gray-600 mt-2">راجع تفاصيل طلبك قبل الإكمال</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Order Form */}
          <div className="lg:col-span-2 space-y-6">
            {/* Delivery Information */}
            <div className="card">
              <div className="card-header">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                  <MapPinIcon className="h-5 w-5 ml-2" />
                  معلومات التوصيل
                </h2>
              </div>
              <div className="card-body">
                <div className="space-y-4">
                  <div>
                    <label htmlFor="delivery_address" className="block text-sm font-medium text-gray-700 mb-2">
                      عنوان التوصيل *
                    </label>
                    <textarea
                      id="delivery_address"
                      name="delivery_address"
                      rows={3}
                      value={orderData.delivery_address}
                      onChange={handleInputChange}
                      className="input-field"
                      placeholder="أدخل العنوان الكامل للتوصيل"
                      required
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="delivery_notes" className="block text-sm font-medium text-gray-700 mb-2">
                      ملاحظات التوصيل (اختياري)
                    </label>
                    <textarea
                      id="delivery_notes"
                      name="delivery_notes"
                      rows={2}
                      value={orderData.delivery_notes}
                      onChange={handleInputChange}
                      className="input-field"
                      placeholder="أي ملاحظات خاصة للمورد أو سائق التوصيل"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Payment Method */}
            <div className="card">
              <div className="card-header">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                  <CreditCardIcon className="h-5 w-5 ml-2" />
                  طريقة الدفع
                </h2>
              </div>
              <div className="card-body">
                <div className="space-y-3">
                  <label className="flex items-center p-4 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
                    <input
                      type="radio"
                      name="payment_method"
                      value="cash"
                      checked={orderData.payment_method === 'cash'}
                      onChange={handleInputChange}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                    />
                    <div className="mr-3">
                      <div className="font-medium text-gray-900">الدفع عند التوصيل</div>
                      <div className="text-sm text-gray-500">ادفع نقداً عند استلام الطلب</div>
                    </div>
                  </label>
                  
                  <label className="flex items-center p-4 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50 opacity-50">
                    <input
                      type="radio"
                      name="payment_method"
                      value="card"
                      disabled
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                    />
                    <div className="mr-3">
                      <div className="font-medium text-gray-900">الدفع الإلكتروني</div>
                      <div className="text-sm text-gray-500">متوفر قريباً</div>
                    </div>
                  </label>
                </div>
              </div>
            </div>

            {/* Order Summary by Supplier */}
            <div className="card">
              <div className="card-header">
                <h2 className="text-lg font-semibold text-gray-900">تفاصيل الطلب</h2>
              </div>
              <div className="card-body">
                <div className="space-y-6">
                  {getOrdersBySupplier().map((orderGroup, index) => (
                    <div key={orderGroup.supplier_id} className="border border-gray-200 rounded-lg p-4">
                      <h3 className="font-semibold text-gray-900 mb-3">
                        طلب #{index + 1} - {orderGroup.total} ر.س
                      </h3>
                      <div className="space-y-2">
                        {orderGroup.items.map((item, itemIndex) => (
                          <div key={itemIndex} className="flex justify-between text-sm">
                            <span>{item.name} × {item.quantity}</span>
                            <span>{item.price * item.quantity} ر.س</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600 mb-2">
                    <strong>ملاحظة:</strong> نظراً لوجود منتجات من موردين مختلفين، سيتم إنشاء طلبات منفصلة لكل مورد.
                  </p>
                  <p className="text-sm text-gray-600">
                    يمكن أن تصل الطلبات في أوقات مختلفة حسب المورد.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Order Summary Sidebar */}
          <div className="lg:col-span-1">
            <div className="card sticky top-4">
              <div className="card-header">
                <h2 className="text-lg font-semibold text-gray-900">ملخص الطلب</h2>
              </div>
              <div className="card-body">
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span className="text-gray-600">عدد المنتجات:</span>
                    <span className="font-semibold">{cartItems.length}</span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-gray-600">المجموع الفرعي:</span>
                    <span className="font-semibold">{getTotalPrice()} ر.س</span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-gray-600">الشحن:</span>
                    <span className="font-semibold">مجاني</span>
                  </div>
                  
                  <hr className="border-gray-200" />
                  
                  <div className="flex justify-between text-lg">
                    <span className="font-bold">المجموع:</span>
                    <span className="font-bold text-blue-600">{getTotalPrice()} ر.س</span>
                  </div>
                </div>

                <button
                  onClick={placeOrder}
                  disabled={processing || !orderData.delivery_address.trim()}
                  className="w-full btn-primary mt-6 flex items-center justify-center"
                >
                  {processing ? (
                    <div className="flex items-center">
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white ml-2"></div>
                      جاري إنشاء الطلب...
                    </div>
                  ) : (
                    'تأكيد الطلب'
                  )}
                </button>

                {/* Trust Badges */}
                <div className="mt-6 grid grid-cols-2 gap-4 text-center">
                  <div className="text-center">
                    <ShieldCheckIcon className="h-6 w-6 text-green-500 mx-auto mb-1" />
                    <p className="text-xs text-gray-600">دفع آمن</p>
                  </div>
                  <div className="text-center">
                    <TruckIcon className="h-6 w-6 text-blue-500 mx-auto mb-1" />
                    <p className="text-xs text-gray-600">توصيل سريع</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CheckoutPage;