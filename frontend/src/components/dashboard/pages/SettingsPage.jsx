/**
 * ===================================
 * منصة ديواني - Settings Page
 * Store settings and configuration
 * ===================================
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../App';
import { storesService, notificationsService } from '../../../services/api';
import DashboardLayout from '../DashboardLayout';
import { useToast } from '../../ui/toast';
import {
  BuildingStorefrontIcon,
  UserCircleIcon,
  BellIcon,
  CreditCardIcon,
  MapPinIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';

const SettingsPage = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState('store');
  const [loading, setLoading] = useState(false);
  const [storeData, setStoreData] = useState({
    name: '',
    description: '',
    phone: '',
    email: '',
    address: '',
    city: '',
    commercial_register: '',
    tax_number: '',
  });
  const [notificationPrefs, setNotificationPrefs] = useState({
    email_notifications: true,
    sms_notifications: true,
    push_notifications: true,
    order_updates: true,
    marketing: false,
  });

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const store = await storesService.getMyStore().catch(() => null);
      const prefs = await notificationsService.getPreferences().catch(() => null);

      if (store) {
        setStoreData({
          name: store.name || '',
          description: store.description || '',
          phone: store.phone || '',
          email: store.email || '',
          address: store.address || '',
          city: store.city || '',
          commercial_register: store.commercial_register || '',
          tax_number: store.tax_number || '',
        });
      }

      if (prefs) {
        setNotificationPrefs(prefs);
      }
    } catch (error) {
      console.error('Error fetching settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStoreSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      await storesService.updateStore(storeData);
      toast?.success?.('تم الحفظ', 'تم حفظ إعدادات المتجر بنجاح');
    } catch (error) {
      console.error('Error saving store:', error);
      toast?.error?.('خطأ', 'حدث خطأ في حفظ الإعدادات');
    } finally {
      setLoading(false);
    }
  };

  const handleNotificationSubmit = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      await notificationsService.updatePreferences(notificationPrefs);
      toast?.success?.('تم الحفظ', 'تم حفظ تفضيلات الإشعارات');
    } catch (error) {
      console.error('Error saving notifications:', error);
      toast?.error?.('خطأ', 'حدث خطأ في حفظ الإعدادات');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'store', name: 'المتجر', icon: BuildingStorefrontIcon },
    { id: 'profile', name: 'الملف الشخصي', icon: UserCircleIcon },
    { id: 'notifications', name: 'الإشعارات', icon: BellIcon },
    { id: 'payments', name: 'المدفوعات', icon: CreditCardIcon },
    { id: 'shipping', name: 'الشحن', icon: MapPinIcon },
    { id: 'security', name: 'الأمان', icon: ShieldCheckIcon },
  ];

  return (
    <DashboardLayout>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">الإعدادات</h1>
        <p className="text-gray-500 mt-1">إدارة إعدادات متجرك وحسابك</p>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Sidebar Tabs */}
        <div className="lg:w-64 flex-shrink-0">
          <div className="bg-white rounded-xl shadow-sm p-2">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center px-4 py-3 rounded-lg text-right transition-colors ${
                  activeTab === tab.id
                    ? 'bg-blue-50 text-blue-600'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <tab.icon className="h-5 w-5 ml-3" />
                <span className="font-medium">{tab.name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1">
          {/* Store Settings */}
          {activeTab === 'store' && (
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">إعدادات المتجر</h2>
              <form onSubmit={handleStoreSubmit} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">اسم المتجر</label>
                    <input
                      type="text"
                      value={storeData.name}
                      onChange={(e) => setStoreData({ ...storeData, name: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="اسم متجرك"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">البريد الإلكتروني</label>
                    <input
                      type="email"
                      value={storeData.email}
                      onChange={(e) => setStoreData({ ...storeData, email: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="email@example.com"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">رقم الجوال</label>
                    <input
                      type="tel"
                      value={storeData.phone}
                      onChange={(e) => setStoreData({ ...storeData, phone: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="05xxxxxxxx"
                      dir="ltr"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">المدينة</label>
                    <select
                      value={storeData.city}
                      onChange={(e) => setStoreData({ ...storeData, city: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="">اختر المدينة</option>
                      <option value="riyadh">الرياض</option>
                      <option value="jeddah">جدة</option>
                      <option value="dammam">الدمام</option>
                      <option value="makkah">مكة المكرمة</option>
                      <option value="madinah">المدينة المنورة</option>
                    </select>
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-gray-700 mb-2">وصف المتجر</label>
                    <textarea
                      value={storeData.description}
                      onChange={(e) => setStoreData({ ...storeData, description: e.target.value })}
                      rows={3}
                      className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="وصف مختصر عن متجرك..."
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">السجل التجاري</label>
                    <input
                      type="text"
                      value={storeData.commercial_register}
                      onChange={(e) => setStoreData({ ...storeData, commercial_register: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="رقم السجل التجاري"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">الرقم الضريبي</label>
                    <input
                      type="text"
                      value={storeData.tax_number}
                      onChange={(e) => setStoreData({ ...storeData, tax_number: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="الرقم الضريبي"
                    />
                  </div>
                </div>
                <div className="pt-4">
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                  >
                    {loading ? 'جاري الحفظ...' : 'حفظ التغييرات'}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Notifications Settings */}
          {activeTab === 'notifications' && (
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">تفضيلات الإشعارات</h2>
              <form onSubmit={handleNotificationSubmit} className="space-y-6">
                <div className="space-y-4">
                  {[
                    { key: 'email_notifications', label: 'إشعارات البريد الإلكتروني', desc: 'استلام الإشعارات عبر البريد' },
                    { key: 'sms_notifications', label: 'الرسائل النصية', desc: 'استلام الإشعارات عبر SMS' },
                    { key: 'push_notifications', label: 'الإشعارات الفورية', desc: 'إشعارات التطبيق الفورية' },
                    { key: 'order_updates', label: 'تحديثات الطلبات', desc: 'إشعارات عند تغير حالة الطلب' },
                    { key: 'marketing', label: 'العروض والتسويق', desc: 'عروض وتخفيضات خاصة' },
                  ].map((item) => (
                    <div key={item.key} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-medium text-gray-900">{item.label}</p>
                        <p className="text-sm text-gray-500">{item.desc}</p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={notificationPrefs[item.key]}
                          onChange={(e) => setNotificationPrefs({ ...notificationPrefs, [item.key]: e.target.checked })}
                          className="sr-only peer"
                        />
                        <div className="w-11 h-6 bg-gray-200 rounded-full peer peer-checked:bg-blue-600 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-full"></div>
                      </label>
                    </div>
                  ))}
                </div>
                <div className="pt-4">
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                  >
                    {loading ? 'جاري الحفظ...' : 'حفظ التفضيلات'}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Profile Settings */}
          {activeTab === 'profile' && (
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">الملف الشخصي</h2>
              <div className="flex items-center mb-6">
                <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center">
                  <UserCircleIcon className="h-12 w-12 text-blue-600" />
                </div>
                <div className="mr-4">
                  <p className="font-semibold text-gray-900">{user?.full_name || 'المستخدم'}</p>
                  <p className="text-sm text-gray-500">{user?.email}</p>
                  <button className="mt-2 text-sm text-blue-600 hover:text-blue-700">تغيير الصورة</button>
                </div>
              </div>
              <p className="text-gray-500">إعدادات الملف الشخصي قيد التطوير...</p>
            </div>
          )}

          {/* Payments Settings */}
          {activeTab === 'payments' && (
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">إعدادات المدفوعات</h2>
              <p className="text-gray-500">إعدادات المدفوعات قيد التطوير...</p>
            </div>
          )}

          {/* Shipping Settings */}
          {activeTab === 'shipping' && (
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">إعدادات الشحن</h2>
              <p className="text-gray-500">إعدادات الشحن قيد التطوير...</p>
            </div>
          )}

          {/* Security Settings */}
          {activeTab === 'security' && (
            <div className="bg-white rounded-xl shadow-sm p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">الأمان والخصوصية</h2>
              <p className="text-gray-500">إعدادات الأمان قيد التطوير...</p>
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
};

export default SettingsPage;
