/**
 * ===================================
 * منصة ديواني - Delivery Management Page
 * Shipping and delivery tracking
 * ===================================
 */

import React, { useState, useEffect } from 'react';
import DashboardLayout from '../DashboardLayout';
import { deliveryService } from '../../../services/api';
import {
  TruckIcon,
  MapPinIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  PhoneIcon,
  UserIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline';

const statusConfig = {
  pending: { label: 'بانتظار السائق', color: 'bg-yellow-100 text-yellow-800', icon: ClockIcon },
  assigned: { label: 'تم التعيين', color: 'bg-blue-100 text-blue-800', icon: UserIcon },
  picked_up: { label: 'تم الاستلام', color: 'bg-indigo-100 text-indigo-800', icon: TruckIcon },
  in_transit: { label: 'في الطريق', color: 'bg-purple-100 text-purple-800', icon: TruckIcon },
  delivered: { label: 'تم التسليم', color: 'bg-green-100 text-green-800', icon: CheckCircleIcon },
  cancelled: { label: 'ملغي', color: 'bg-red-100 text-red-800', icon: XCircleIcon },
};

const DeliveryPage = () => {
  const [deliveries, setDeliveries] = useState([]);
  const [zones, setZones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [selectedDelivery, setSelectedDelivery] = useState(null);
  const [stats, setStats] = useState({});

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Demo data - replace with actual API calls
      await new Promise(resolve => setTimeout(resolve, 800));

      setStats({
        totalDeliveries: 156,
        inTransit: 12,
        delivered: 138,
        cancelled: 6,
        averageTime: 45, // minutes
      });

      setZones([
        { id: 1, name: 'الرياض - شمال', base_fee: 25, per_km: 2, estimated_time: 30 },
        { id: 2, name: 'الرياض - جنوب', base_fee: 30, per_km: 2.5, estimated_time: 35 },
        { id: 3, name: 'الرياض - شرق', base_fee: 25, per_km: 2, estimated_time: 30 },
        { id: 4, name: 'الرياض - غرب', base_fee: 28, per_km: 2.2, estimated_time: 32 },
      ]);

      setDeliveries([
        {
          id: 'DEL-001',
          order_number: 'ORD-1433',
          status: 'in_transit',
          customer_name: 'أحمد محمد',
          customer_phone: '0501234567',
          address: 'الرياض، حي النخيل، شارع الملك فهد',
          driver_name: 'محمد السائق',
          driver_phone: '0509876543',
          estimated_time: 25,
          distance: 12.5,
          fee: 35,
          created_at: '2024-01-15T10:30:00Z',
        },
        {
          id: 'DEL-002',
          order_number: 'ORD-1432',
          status: 'assigned',
          customer_name: 'فاطمة علي',
          customer_phone: '0507654321',
          address: 'الرياض، حي الملقا، شارع التخصصي',
          driver_name: 'خالد السائق',
          driver_phone: '0501122334',
          estimated_time: 40,
          distance: 18.2,
          fee: 45,
          created_at: '2024-01-15T11:00:00Z',
        },
        {
          id: 'DEL-003',
          order_number: 'ORD-1431',
          status: 'delivered',
          customer_name: 'سعد العتيبي',
          customer_phone: '0503456789',
          address: 'الرياض، حي الياسمين، شارع الأمير سلطان',
          driver_name: 'عبدالله السائق',
          driver_phone: '0505544332',
          estimated_time: 0,
          distance: 8.7,
          fee: 28,
          created_at: '2024-01-15T09:00:00Z',
          delivered_at: '2024-01-15T09:45:00Z',
        },
        {
          id: 'DEL-004',
          order_number: 'ORD-1430',
          status: 'pending',
          customer_name: 'نورة الشمري',
          customer_phone: '0506789012',
          address: 'الرياض، حي الورود، شارع العروبة',
          driver_name: null,
          driver_phone: null,
          estimated_time: 50,
          distance: 22.1,
          fee: 52,
          created_at: '2024-01-15T11:30:00Z',
        },
      ]);
    } catch (error) {
      console.error('Error fetching deliveries:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredDeliveries = deliveries.filter((d) => {
    const matchesSearch = d.order_number.toLowerCase().includes(search.toLowerCase()) ||
      d.customer_name.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'all' || d.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const StatCard = ({ icon: Icon, label, value, subValue, color }) => (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <div className="flex items-center">
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
        <div className="mr-4">
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {subValue && <p className="text-xs text-gray-400">{subValue}</p>}
        </div>
      </div>
    </div>
  );

  return (
    <DashboardLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">إدارة التوصيل</h1>
        <p className="text-gray-500 mt-1">تتبع وإدارة عمليات التوصيل</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          icon={TruckIcon}
          label="إجمالي التوصيلات"
          value={stats.totalDeliveries}
          color="bg-blue-500"
        />
        <StatCard
          icon={TruckIcon}
          label="في الطريق"
          value={stats.inTransit}
          subValue="توصيلة نشطة"
          color="bg-purple-500"
        />
        <StatCard
          icon={CheckCircleIcon}
          label="تم التسليم"
          value={stats.delivered}
          color="bg-green-500"
        />
        <StatCard
          icon={ClockIcon}
          label="متوسط وقت التوصيل"
          value={`${stats.averageTime} دقيقة`}
          color="bg-orange-500"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Deliveries List */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-xl shadow-sm overflow-hidden">
            {/* Filters */}
            <div className="p-4 border-b border-gray-100">
              <div className="flex flex-col md:flex-row gap-4">
                <div className="relative flex-1">
                  <MagnifyingGlassIcon className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    placeholder="ابحث برقم الطلب أو اسم العميل..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full pr-10 pl-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">جميع الحالات</option>
                  {Object.entries(statusConfig).map(([key, config]) => (
                    <option key={key} value={key}>{config.label}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* List */}
            {loading ? (
              <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
              </div>
            ) : filteredDeliveries.length === 0 ? (
              <div className="p-12 text-center">
                <TruckIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">لا توجد توصيلات</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {filteredDeliveries.map((delivery) => {
                  const status = statusConfig[delivery.status];
                  const StatusIcon = status.icon;
                  return (
                    <div
                      key={delivery.id}
                      onClick={() => setSelectedDelivery(delivery)}
                      className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                        selectedDelivery?.id === delivery.id ? 'bg-blue-50' : ''
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center">
                          <span className="font-medium text-blue-600">{delivery.order_number}</span>
                          <span className={`mr-3 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${status.color}`}>
                            <StatusIcon className="h-3 w-3 ml-1" />
                            {status.label}
                          </span>
                        </div>
                        <span className="text-sm text-gray-500">
                          {delivery.fee} ر.س
                        </span>
                      </div>
                      <div className="flex items-center text-sm text-gray-600 mb-2">
                        <UserIcon className="h-4 w-4 ml-2" />
                        {delivery.customer_name}
                      </div>
                      <div className="flex items-center text-sm text-gray-500">
                        <MapPinIcon className="h-4 w-4 ml-2" />
                        <span className="truncate">{delivery.address}</span>
                      </div>
                      {delivery.status === 'in_transit' && delivery.estimated_time > 0 && (
                        <div className="mt-2 flex items-center text-sm text-purple-600">
                          <ClockIcon className="h-4 w-4 ml-1" />
                          الوصول خلال {delivery.estimated_time} دقيقة
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Selected Delivery Details */}
          {selectedDelivery ? (
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">تفاصيل التوصيل</h3>

              <div className="space-y-4">
                <div>
                  <span className="text-sm text-gray-500">رقم الطلب</span>
                  <p className="font-medium text-blue-600">{selectedDelivery.order_number}</p>
                </div>

                <div>
                  <span className="text-sm text-gray-500">العميل</span>
                  <p className="font-medium text-gray-900">{selectedDelivery.customer_name}</p>
                  <a
                    href={`tel:${selectedDelivery.customer_phone}`}
                    className="text-sm text-blue-600 flex items-center mt-1"
                  >
                    <PhoneIcon className="h-4 w-4 ml-1" />
                    {selectedDelivery.customer_phone}
                  </a>
                </div>

                <div>
                  <span className="text-sm text-gray-500">العنوان</span>
                  <p className="text-gray-900">{selectedDelivery.address}</p>
                </div>

                {selectedDelivery.driver_name && (
                  <div className="pt-4 border-t border-gray-100">
                    <span className="text-sm text-gray-500">السائق</span>
                    <p className="font-medium text-gray-900">{selectedDelivery.driver_name}</p>
                    <a
                      href={`tel:${selectedDelivery.driver_phone}`}
                      className="text-sm text-blue-600 flex items-center mt-1"
                    >
                      <PhoneIcon className="h-4 w-4 ml-1" />
                      {selectedDelivery.driver_phone}
                    </a>
                  </div>
                )}

                <div className="pt-4 border-t border-gray-100 grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-sm text-gray-500">المسافة</span>
                    <p className="font-medium text-gray-900">{selectedDelivery.distance} كم</p>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">رسوم التوصيل</span>
                    <p className="font-medium text-gray-900">{selectedDelivery.fee} ر.س</p>
                  </div>
                </div>

                {/* Map placeholder */}
                <div className="mt-4 h-48 bg-gray-100 rounded-lg flex items-center justify-center">
                  <MapPinIcon className="h-8 w-8 text-gray-400" />
                  <span className="text-gray-400 mr-2">الخريطة</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm p-6 text-center">
              <TruckIcon className="h-12 w-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">اختر توصيلة لعرض التفاصيل</p>
            </div>
          )}

          {/* Delivery Zones */}
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">مناطق التوصيل</h3>
            <div className="space-y-3">
              {zones.map((zone) => (
                <div
                  key={zone.id}
                  className="p-3 bg-gray-50 rounded-lg flex items-center justify-between"
                >
                  <div>
                    <p className="font-medium text-gray-900">{zone.name}</p>
                    <p className="text-xs text-gray-500">
                      {zone.base_fee} ر.س + {zone.per_km} ر.س/كم
                    </p>
                  </div>
                  <span className="text-sm text-gray-500">{zone.estimated_time} دقيقة</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default DeliveryPage;
