import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../App';
import { useToast } from '../ui/toast';
import axios from 'axios';
import {
  TruckIcon,
  MapPinIcon,
  CurrencyDollarIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  PhoneIcon,
  ChevronLeftIcon,
  SignalIcon,
  SignalSlashIcon
} from '@heroicons/react/24/outline';

const DriverDashboard = () => {
  const { user } = useAuth();
  const { toast } = useToast();

  const [stats, setStats] = useState(null);
  const [activeDeliveries, setActiveDeliveries] = useState([]);
  const [isOnline, setIsOnline] = useState(false);
  const [loading, setLoading] = useState(true);
  const [updatingStatus, setUpdatingStatus] = useState(false);

  useEffect(() => {
    fetchDashboardData();

    // تحديث الموقع كل 30 ثانية
    const locationInterval = setInterval(updateLocation, 30000);

    return () => clearInterval(locationInterval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsResponse, deliveriesResponse] = await Promise.all([
        axios.get('/tracking/stats/driver'),
        axios.get('/tracking/deliveries', {
          params: { status: 'in_progress,assigned,picked_up' }
        })
      ]);

      setStats(statsResponse.data);
      setActiveDeliveries(deliveriesResponse.data?.items || deliveriesResponse.data || []);
      setIsOnline(statsResponse.data?.is_online || false);
    } catch (error) {
      console.error('Error fetching driver data:', error);
      toast.error('خطأ', 'حدث خطأ في تحميل البيانات');
    } finally {
      setLoading(false);
    }
  };

  const updateLocation = async () => {
    if (!isOnline) return;

    try {
      if ('geolocation' in navigator) {
        navigator.geolocation.getCurrentPosition(async (position) => {
          await axios.post('/tracking/driver/location', {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
            speed: position.coords.speed || 0,
            heading: position.coords.heading || 0
          });
        }, (error) => {
          console.error('Geolocation error:', error);
        });
      }
    } catch (error) {
      console.error('Error updating location:', error);
    }
  };

  const toggleOnlineStatus = async () => {
    setUpdatingStatus(true);
    try {
      await axios.post('/tracking/driver/online', {
        is_online: !isOnline
      });
      setIsOnline(!isOnline);
      toast.success(
        isOnline ? 'أنت الآن غير متصل' : 'أنت الآن متصل',
        isOnline ? 'لن تستقبل طلبات توصيل جديدة' : 'يمكنك استقبال طلبات توصيل'
      );

      // تحديث الموقع فوراً عند الاتصال
      if (!isOnline) {
        updateLocation();
      }
    } catch (error) {
      console.error('Error updating online status:', error);
      toast.error('خطأ', 'حدث خطأ في تحديث الحالة');
    } finally {
      setUpdatingStatus(false);
    }
  };

  const updateDeliveryStatus = async (deliveryId, newStatus) => {
    try {
      await axios.post(`/tracking/deliveries/${deliveryId}/status`, {
        status: newStatus
      });

      setActiveDeliveries(prev =>
        prev.map(d =>
          d.id === deliveryId ? { ...d, status: newStatus } : d
        )
      );

      toast.success('تم التحديث', 'تم تحديث حالة التوصيل');
    } catch (error) {
      console.error('Error updating delivery status:', error);
      toast.error('خطأ', 'حدث خطأ في تحديث الحالة');
    }
  };

  const getStatusLabel = (status) => {
    const labels = {
      'assigned': 'تم التعيين',
      'picked_up': 'تم الاستلام',
      'in_transit': 'في الطريق',
      'arrived': 'وصل الموقع',
      'delivered': 'تم التوصيل',
      'failed': 'فشل',
      'cancelled': 'ملغي'
    };
    return labels[status] || status;
  };

  const getStatusColor = (status) => {
    const colors = {
      'assigned': 'bg-yellow-100 text-yellow-800',
      'picked_up': 'bg-blue-100 text-blue-800',
      'in_transit': 'bg-purple-100 text-purple-800',
      'arrived': 'bg-green-100 text-green-800',
      'delivered': 'bg-green-500 text-white',
      'failed': 'bg-red-100 text-red-800',
      'cancelled': 'bg-gray-100 text-gray-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className={`px-4 py-6 ${isOnline ? 'bg-green-600' : 'bg-gray-600'} text-white`}>
        <div className="max-w-7xl mx-auto">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold">مرحباً، {user?.full_name || 'سائق'}</h1>
              <p className="text-sm opacity-90">
                {isOnline ? 'أنت متصل ويمكنك استقبال الطلبات' : 'أنت غير متصل'}
              </p>
            </div>

            <button
              onClick={toggleOnlineStatus}
              disabled={updatingStatus}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                isOnline
                  ? 'bg-white text-green-600 hover:bg-gray-100'
                  : 'bg-white text-gray-600 hover:bg-gray-100'
              }`}
            >
              {updatingStatus ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-current"></div>
              ) : isOnline ? (
                <SignalIcon className="h-5 w-5" />
              ) : (
                <SignalSlashIcon className="h-5 w-5" />
              )}
              {isOnline ? 'متصل' : 'غير متصل'}
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Stats Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-xl shadow-sm p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">توصيلات اليوم</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats?.today_deliveries || 0}
                </p>
              </div>
              <div className="bg-blue-100 p-3 rounded-lg">
                <TruckIcon className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">أرباح اليوم</p>
                <p className="text-2xl font-bold text-green-600">
                  {stats?.today_earnings || 0} ر.س
                </p>
              </div>
              <div className="bg-green-100 p-3 rounded-lg">
                <CurrencyDollarIcon className="h-6 w-6 text-green-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">المسافة</p>
                <p className="text-2xl font-bold text-gray-900">
                  {stats?.today_distance || 0} كم
                </p>
              </div>
              <div className="bg-purple-100 p-3 rounded-lg">
                <MapPinIcon className="h-6 w-6 text-purple-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">التقييم</p>
                <p className="text-2xl font-bold text-yellow-600">
                  {stats?.rating || '0.0'}
                </p>
              </div>
              <div className="bg-yellow-100 p-3 rounded-lg">
                <ClockIcon className="h-6 w-6 text-yellow-600" />
              </div>
            </div>
          </div>
        </div>

        {/* Active Deliveries */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">التوصيلات النشطة</h2>
          </div>

          {activeDeliveries.length > 0 ? (
            <div className="divide-y divide-gray-200">
              {activeDeliveries.map((delivery) => (
                <div key={delivery.id} className="p-4">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(delivery.status)}`}>
                        {getStatusLabel(delivery.status)}
                      </span>
                      <h3 className="font-medium text-gray-900 mt-1">
                        طلب #{delivery.order_number || delivery.id?.slice(0, 8)}
                      </h3>
                    </div>
                    <p className="text-lg font-bold text-green-600">
                      {delivery.driver_fee || 0} ر.س
                    </p>
                  </div>

                  {/* Pickup Location */}
                  <div className="flex items-start gap-3 mb-2">
                    <div className="bg-blue-100 p-1 rounded-full mt-1">
                      <MapPinIcon className="h-4 w-4 text-blue-600" />
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">نقطة الاستلام</p>
                      <p className="text-sm text-gray-900">
                        {delivery.pickup_address || 'موقع المتجر'}
                      </p>
                    </div>
                  </div>

                  {/* Destination */}
                  <div className="flex items-start gap-3 mb-4">
                    <div className="bg-green-100 p-1 rounded-full mt-1">
                      <MapPinIcon className="h-4 w-4 text-green-600" />
                    </div>
                    <div>
                      <p className="text-xs text-gray-500">نقطة التسليم</p>
                      <p className="text-sm text-gray-900">
                        {delivery.delivery_address || 'عنوان العميل'}
                      </p>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    {delivery.status === 'assigned' && (
                      <button
                        onClick={() => updateDeliveryStatus(delivery.id, 'picked_up')}
                        className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-blue-700 transition-colors"
                      >
                        تم الاستلام
                      </button>
                    )}

                    {delivery.status === 'picked_up' && (
                      <button
                        onClick={() => updateDeliveryStatus(delivery.id, 'in_transit')}
                        className="flex-1 bg-purple-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-purple-700 transition-colors"
                      >
                        بدء التوصيل
                      </button>
                    )}

                    {delivery.status === 'in_transit' && (
                      <button
                        onClick={() => updateDeliveryStatus(delivery.id, 'arrived')}
                        className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-green-700 transition-colors"
                      >
                        وصلت للموقع
                      </button>
                    )}

                    {delivery.status === 'arrived' && (
                      <Link
                        to={`/driver/delivery/${delivery.id}/complete`}
                        className="flex-1 bg-green-600 text-white py-2 px-4 rounded-lg font-medium hover:bg-green-700 transition-colors text-center"
                      >
                        إتمام التوصيل
                      </Link>
                    )}

                    {/* Call Customer */}
                    {delivery.customer_phone && (
                      <a
                        href={`tel:${delivery.customer_phone}`}
                        className="bg-gray-100 text-gray-700 p-2 rounded-lg hover:bg-gray-200 transition-colors"
                      >
                        <PhoneIcon className="h-5 w-5" />
                      </a>
                    )}

                    {/* Navigate */}
                    <a
                      href={`https://www.google.com/maps/dir/?api=1&destination=${delivery.delivery_lat},${delivery.delivery_lng}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="bg-gray-100 text-gray-700 p-2 rounded-lg hover:bg-gray-200 transition-colors"
                    >
                      <MapPinIcon className="h-5 w-5" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center">
              <TruckIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500 mb-2">لا توجد توصيلات نشطة</p>
              <p className="text-sm text-gray-400">
                {isOnline
                  ? 'ستصلك إشعارات عند توفر طلبات جديدة'
                  : 'قم بتفعيل الاتصال لاستقبال الطلبات'}
              </p>
            </div>
          )}
        </div>

        {/* Quick Links */}
        <div className="grid grid-cols-2 gap-4 mt-6">
          <Link
            to="/driver/history"
            className="bg-white rounded-xl shadow-sm p-4 flex items-center justify-between hover:shadow-md transition-shadow"
          >
            <div>
              <p className="font-medium text-gray-900">سجل التوصيلات</p>
              <p className="text-sm text-gray-500">عرض التوصيلات السابقة</p>
            </div>
            <ChevronLeftIcon className="h-5 w-5 text-gray-400" />
          </Link>

          <Link
            to="/driver/earnings"
            className="bg-white rounded-xl shadow-sm p-4 flex items-center justify-between hover:shadow-md transition-shadow"
          >
            <div>
              <p className="font-medium text-gray-900">الأرباح</p>
              <p className="text-sm text-gray-500">تفاصيل الأرباح والتحويلات</p>
            </div>
            <ChevronLeftIcon className="h-5 w-5 text-gray-400" />
          </Link>
        </div>
      </div>
    </div>
  );
};

export default DriverDashboard;
