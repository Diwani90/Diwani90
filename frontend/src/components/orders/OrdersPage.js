import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../App';
import { useToast } from '../ui/toast';
import axios from 'axios';
import {
  ClipboardDocumentListIcon,
  EyeIcon,
  ChatBubbleLeftRightIcon,
  TruckIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

const OrdersPage = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [updatingStatus, setUpdatingStatus] = useState({});

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await axios.get('/orders');
      setOrders(response.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
      toast.error('خطأ', 'حدث خطأ في تحميل الطلبات');
    } finally {
      setLoading(false);
    }
  };

  const updateOrderStatus = async (orderId, newStatus) => {
    setUpdatingStatus(prev => ({ ...prev, [orderId]: true }));
    
    try {
      await axios.put(`/orders/${orderId}/status`, { status: newStatus });
      
      setOrders(prev => 
        prev.map(order => 
          order.id === orderId 
            ? { ...order, status: newStatus, updated_at: new Date().toISOString() }
            : order
        )
      );
      
      toast.success('تم التحديث', 'تم تحديث حالة الطلب بنجاح');
    } catch (error) {
      console.error('Error updating order status:', error);
      toast.error('خطأ', 'حدث خطأ في تحديث حالة الطلب');
    } finally {
      setUpdatingStatus(prev => ({ ...prev, [orderId]: false }));
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending':
        return <ClockIcon className="h-5 w-5 text-yellow-500" />;
      case 'confirmed':
        return <CheckCircleIcon className="h-5 w-5 text-blue-500" />;
      case 'shipped':
        return <TruckIcon className="h-5 w-5 text-purple-500" />;
      case 'delivered':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'cancelled':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'pending': return 'معلق';
      case 'confirmed': return 'مؤكد';
      case 'shipped': return 'في الطريق';
      case 'delivered': return 'تم التسليم';
      case 'cancelled': return 'ملغي';
      default: return status;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'confirmed': return 'bg-blue-100 text-blue-800';
      case 'shipped': return 'bg-purple-100 text-purple-800';
      case 'delivered': return 'bg-green-100 text-green-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const canUpdateStatus = (order) => {
    return user?.role === 'supplier' && order.supplier_id === user.id;
  };

  const getNextStatus = (currentStatus) => {
    switch (currentStatus) {
      case 'pending': return 'confirmed';
      case 'confirmed': return 'shipped';
      case 'shipped': return 'delivered';
      default: return null;
    }
  };

  const getNextStatusText = (currentStatus) => {
    switch (currentStatus) {
      case 'pending': return 'تأكيد الطلب';
      case 'confirmed': return 'شحن الطلب';
      case 'shipped': return 'تسليم الطلب';
      default: return null;
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
          <h1 className="text-3xl font-bold text-gray-900 flex items-center">
            <ClipboardDocumentListIcon className="h-8 w-8 ml-3" />
            {user?.role === 'customer' ? 'طلباتي' : 'الطلبات الواردة'}
          </h1>
          <p className="text-gray-600 mt-2">
            {user?.role === 'customer' 
              ? 'تتبع حالة طلباتك وإدارتها' 
              : 'إدارة الطلبات الواردة من العملاء'
            }
          </p>
        </div>

        {orders.length > 0 ? (
          <div className="space-y-6">
            {orders.map((order) => (
              <div key={order.id} className="card">
                <div className="card-header">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center">
                      <h3 className="text-lg font-semibold text-gray-900">
                        طلب #{order.id.slice(-8)}
                      </h3>
                      <span className={`mr-3 inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(order.status)}`}>
                        {getStatusIcon(order.status)}
                        <span className="mr-1">{getStatusText(order.status)}</span>
                      </span>
                    </div>
                    <div className="text-left">
                      <p className="text-lg font-bold text-blue-600">{order.total_amount} ر.س</p>
                      <p className="text-sm text-gray-500">
                        {new Date(order.created_at).toLocaleDateString('ar-SA', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric'
                        })}
                      </p>
                    </div>
                  </div>
                </div>
                
                <div className="card-body">
                  {/* Order Items */}
                  <div className="mb-4">
                    <h4 className="font-medium text-gray-900 mb-3">المنتجات:</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {order.items.map((item, index) => (
                        <div key={index} className="flex items-center p-3 bg-gray-50 rounded-lg">
                          <div className="flex-1">
                            <p className="font-medium text-gray-900">{item.name}</p>
                            <p className="text-sm text-gray-600">
                              الكمية: {item.quantity} × {item.price} ر.س
                            </p>
                          </div>
                          <p className="font-semibold text-blue-600">
                            {item.quantity * item.price} ر.س
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Delivery Address */}
                  <div className="mb-4">
                    <h4 className="font-medium text-gray-900 mb-2">عنوان التوصيل:</h4>
                    <p className="text-gray-700 bg-gray-50 p-3 rounded-lg">
                      {order.delivery_address}
                    </p>
                    {order.delivery_notes && (
                      <div className="mt-2">
                        <h5 className="font-medium text-gray-900 mb-1">ملاحظات:</h5>
                        <p className="text-gray-600 text-sm">{order.delivery_notes}</p>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex flex-wrap gap-3 justify-between items-center pt-4 border-t border-gray-200">
                    <div className="flex flex-wrap gap-3">
                      {/* Customer Actions */}
                      {user?.role === 'customer' && (
                        <>
                          <button className="btn-secondary text-sm flex items-center">
                            <EyeIcon className="h-4 w-4 ml-1" />
                            تفاصيل
                          </button>
                          <button className="btn-secondary text-sm flex items-center">
                            <ChatBubbleLeftRightIcon className="h-4 w-4 ml-1" />
                            تواصل مع المورد
                          </button>
                        </>
                      )}

                      {/* Supplier Actions */}
                      {canUpdateStatus(order) && (
                        <>
                          {getNextStatus(order.status) && (
                            <button
                              onClick={() => updateOrderStatus(order.id, getNextStatus(order.status))}
                              disabled={updatingStatus[order.id]}
                              className="btn-primary text-sm flex items-center"
                            >
                              {updatingStatus[order.id] ? (
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white ml-1"></div>
                              ) : (
                                getStatusIcon(getNextStatus(order.status))
                              )}
                              <span className="mr-1">
                                {updatingStatus[order.id] ? 'جاري التحديث...' : getNextStatusText(order.status)}
                              </span>
                            </button>
                          )}
                          
                          {order.status === 'pending' && (
                            <button
                              onClick={() => updateOrderStatus(order.id, 'cancelled')}
                              disabled={updatingStatus[order.id]}
                              className="btn-danger text-sm flex items-center"
                            >
                              <XCircleIcon className="h-4 w-4 ml-1" />
                              إلغاء الطلب
                            </button>
                          )}
                          
                          <button className="btn-secondary text-sm flex items-center">
                            <ChatBubbleLeftRightIcon className="h-4 w-4 ml-1" />
                            تواصل مع العميل
                          </button>
                        </>
                      )}
                    </div>

                    {/* Order Timeline */}
                    <div className="text-sm text-gray-500">
                      آخر تحديث: {new Date(order.updated_at).toLocaleString('ar-SA')}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          /* Empty State */
          <div className="text-center py-16">
            <ClipboardDocumentListIcon className="h-24 w-24 text-gray-400 mx-auto mb-6" />
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              {user?.role === 'customer' ? 'لا توجد طلبات' : 'لا توجد طلبات واردة'}
            </h2>
            <p className="text-gray-600 mb-8">
              {user?.role === 'customer' 
                ? 'لم تقم بأي طلبات حتى الآن' 
                : 'لم تتلق أي طلبات من العملاء حتى الآن'
              }
            </p>
            {user?.role === 'customer' && (
              <Link to="/products" className="btn-primary">
                ابدأ التسوق
              </Link>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default OrdersPage;