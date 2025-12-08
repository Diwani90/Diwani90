import React, { useState, useEffect } from 'react';
import { useAuth } from '../../App';
import { useToast } from '../ui/toast';
import axios from 'axios';
import {
  BuildingStorefrontIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  EyeIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline';

const AdminVendorsPage = () => {
  const { user } = useAuth();
  const { toast } = useToast();

  const [vendors, setVendors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 20,
    total: 0,
    total_pages: 0
  });
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    is_verified: ''
  });
  const [selectedVendor, setSelectedVendor] = useState(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    fetchVendors();
  }, [pagination.page, filters]);

  const fetchVendors = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: pagination.page,
        per_page: pagination.per_page,
        ...(filters.search && { search: filters.search }),
        ...(filters.status && { status: filters.status }),
        ...(filters.is_verified !== '' && { is_verified: filters.is_verified })
      });

      const response = await axios.get(`/users/admin/vendors?${params}`);
      setVendors(response.data.items || []);
      setPagination(prev => ({
        ...prev,
        total: response.data.total,
        total_pages: response.data.total_pages
      }));
    } catch (error) {
      console.error('Error fetching vendors:', error);
      toast.error('خطأ', 'حدث خطأ في تحميل البائعين');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPagination(prev => ({ ...prev, page: 1 }));
    fetchVendors();
  };

  const verifyVendor = async (vendorId, isVerified) => {
    try {
      await axios.post(`/users/admin/vendors/${vendorId}/verify?is_verified=${isVerified}`);
      toast.success('تم بنجاح', isVerified ? 'تم توثيق البائع' : 'تم رفض توثيق البائع');
      fetchVendors();
      setShowModal(false);
    } catch (error) {
      console.error('Error verifying vendor:', error);
      toast.error('خطأ', 'حدث خطأ في عملية التوثيق');
    }
  };

  const updateVendorStatus = async (vendorId, newStatus) => {
    try {
      await axios.put(`/users/admin/vendors/${vendorId}/status?status=${newStatus}`);
      toast.success('تم بنجاح', 'تم تحديث حالة البائع');
      fetchVendors();
      setShowModal(false);
    } catch (error) {
      console.error('Error updating vendor status:', error);
      toast.error('خطأ', 'حدث خطأ في تحديث الحالة');
    }
  };

  const viewVendorDetails = async (vendorId) => {
    try {
      const response = await axios.get(`/users/admin/vendors/${vendorId}`);
      setSelectedVendor(response.data);
      setShowModal(true);
    } catch (error) {
      console.error('Error fetching vendor details:', error);
      toast.error('خطأ', 'حدث خطأ في تحميل بيانات البائع');
    }
  };

  const getStatusLabel = (status) => {
    const labels = {
      'active': 'نشط',
      'pending': 'قيد الانتظار',
      'suspended': 'موقوف',
      'banned': 'محظور'
    };
    return labels[status] || status;
  };

  const getStatusColor = (status) => {
    const colors = {
      'active': 'bg-green-100 text-green-800',
      'pending': 'bg-yellow-100 text-yellow-800',
      'suspended': 'bg-orange-100 text-orange-800',
      'banned': 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  if (loading && vendors.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-600 to-teal-600 px-4 py-6 text-white">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl font-bold flex items-center">
            <BuildingStorefrontIcon className="h-7 w-7 ml-2" />
            إدارة البائعين
          </h1>
          <p className="text-sm opacity-90 mt-1">عرض وإدارة جميع البائعين والموردين</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Filters */}
        <div className="bg-white rounded-xl shadow-sm p-4 mb-6">
          <form onSubmit={handleSearch} className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="relative">
              <MagnifyingGlassIcon className="h-5 w-5 text-gray-400 absolute right-3 top-1/2 transform -translate-y-1/2" />
              <input
                type="text"
                placeholder="البحث باسم الشركة أو الهاتف..."
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                className="input-field pr-10"
              />
            </div>

            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="input-field"
            >
              <option value="">جميع الحالات</option>
              <option value="active">نشط</option>
              <option value="pending">قيد الانتظار</option>
              <option value="suspended">موقوف</option>
              <option value="banned">محظور</option>
            </select>

            <select
              value={filters.is_verified}
              onChange={(e) => setFilters(prev => ({ ...prev, is_verified: e.target.value }))}
              className="input-field"
            >
              <option value="">جميع حالات التوثيق</option>
              <option value="true">موثق</option>
              <option value="false">غير موثق</option>
            </select>

            <button type="submit" className="btn-primary flex items-center justify-center">
              <FunnelIcon className="h-5 w-5 ml-2" />
              تصفية
            </button>
          </form>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl shadow-sm p-4 text-center">
            <p className="text-2xl font-bold text-gray-900">{pagination.total}</p>
            <p className="text-sm text-gray-600">إجمالي البائعين</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4 text-center">
            <p className="text-2xl font-bold text-green-600">
              {vendors.filter(v => v.is_verified).length}
            </p>
            <p className="text-sm text-gray-600">موثق</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4 text-center">
            <p className="text-2xl font-bold text-yellow-600">
              {vendors.filter(v => !v.is_verified && v.status === 'pending').length}
            </p>
            <p className="text-sm text-gray-600">بانتظار التوثيق</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4 text-center">
            <p className="text-2xl font-bold text-blue-600">
              {vendors.filter(v => v.status === 'active').length}
            </p>
            <p className="text-sm text-gray-600">نشط</p>
          </div>
        </div>

        {/* Vendors Table */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    الشركة
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    المالك
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    السجل التجاري
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    التوثيق
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    الحالة
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    الإجراءات
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {vendors.map((vendor) => (
                  <tr key={vendor.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="h-10 w-10 rounded-full bg-green-100 flex items-center justify-center">
                          <BuildingStorefrontIcon className="h-6 w-6 text-green-600" />
                        </div>
                        <div className="mr-4">
                          <div className="text-sm font-medium text-gray-900">{vendor.company_name}</div>
                          <div className="text-sm text-gray-500">{vendor.phone_number}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{vendor.owner_name}</div>
                      <div className="text-sm text-gray-500">{vendor.email || '-'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {vendor.commercial_register || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {vendor.is_verified ? (
                        <span className="flex items-center text-green-600">
                          <ShieldCheckIcon className="h-5 w-5 ml-1" />
                          موثق
                        </span>
                      ) : (
                        <span className="flex items-center text-yellow-600">
                          <ClockIcon className="h-5 w-5 ml-1" />
                          غير موثق
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(vendor.status)}`}>
                        {getStatusLabel(vendor.status)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => viewVendorDetails(vendor.id)}
                          className="text-blue-600 hover:text-blue-900"
                          title="عرض التفاصيل"
                        >
                          <EyeIcon className="h-5 w-5" />
                        </button>
                        {!vendor.is_verified && (
                          <button
                            onClick={() => verifyVendor(vendor.id, true)}
                            className="text-green-600 hover:text-green-900"
                            title="توثيق"
                          >
                            <CheckCircleIcon className="h-5 w-5" />
                          </button>
                        )}
                        {vendor.status === 'active' ? (
                          <button
                            onClick={() => updateVendorStatus(vendor.id, 'suspended')}
                            className="text-orange-600 hover:text-orange-900"
                            title="إيقاف"
                          >
                            <XCircleIcon className="h-5 w-5" />
                          </button>
                        ) : vendor.status !== 'active' && (
                          <button
                            onClick={() => updateVendorStatus(vendor.id, 'active')}
                            className="text-green-600 hover:text-green-900"
                            title="تفعيل"
                          >
                            <CheckCircleIcon className="h-5 w-5" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Empty State */}
          {vendors.length === 0 && !loading && (
            <div className="text-center py-12">
              <BuildingStorefrontIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">لا يوجد بائعين</p>
            </div>
          )}

          {/* Pagination */}
          {pagination.total_pages > 1 && (
            <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200">
              <div className="flex-1 flex justify-between items-center">
                <p className="text-sm text-gray-700">
                  عرض <span className="font-medium">{((pagination.page - 1) * pagination.per_page) + 1}</span>
                  {' '}-{' '}
                  <span className="font-medium">
                    {Math.min(pagination.page * pagination.per_page, pagination.total)}
                  </span>
                  {' '}من{' '}
                  <span className="font-medium">{pagination.total}</span>
                </p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                    disabled={pagination.page === 1}
                    className="btn-secondary disabled:opacity-50"
                  >
                    <ChevronRightIcon className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                    disabled={pagination.page === pagination.total_pages}
                    className="btn-secondary disabled:opacity-50"
                  >
                    <ChevronLeftIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Vendor Details Modal */}
      {showModal && selectedVendor && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">تفاصيل البائع</h2>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-gray-500">اسم الشركة</label>
                    <p className="font-medium">{selectedVendor.company_name}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">اسم الشركة (إنجليزي)</label>
                    <p className="font-medium">{selectedVendor.company_name_en || '-'}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">السجل التجاري</label>
                    <p className="font-medium">{selectedVendor.commercial_register || '-'}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">الرقم الضريبي</label>
                    <p className="font-medium">{selectedVendor.tax_number || '-'}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">نوع النشاط</label>
                    <p className="font-medium">{selectedVendor.business_type || '-'}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">حالة التوثيق</label>
                    {selectedVendor.is_verified ? (
                      <p className="text-green-600 font-medium flex items-center">
                        <ShieldCheckIcon className="h-5 w-5 ml-1" />
                        موثق
                      </p>
                    ) : (
                      <p className="text-yellow-600 font-medium">غير موثق</p>
                    )}
                  </div>
                </div>

                <div className="border-t pt-4">
                  <h3 className="font-semibold mb-2">معلومات المالك</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm text-gray-500">الاسم</label>
                      <p className="font-medium">{selectedVendor.user?.full_name}</p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-500">الهاتف</label>
                      <p className="font-medium">{selectedVendor.user?.phone_number}</p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-500">البريد</label>
                      <p className="font-medium">{selectedVendor.user?.email || '-'}</p>
                    </div>
                    <div>
                      <label className="text-sm text-gray-500">تاريخ التسجيل</label>
                      <p className="font-medium">
                        {new Date(selectedVendor.user?.created_at).toLocaleDateString('ar-SA')}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                {!selectedVendor.is_verified && (
                  <button
                    onClick={() => verifyVendor(selectedVendor.id, true)}
                    className="btn-primary flex-1 bg-green-600 hover:bg-green-700"
                  >
                    <ShieldCheckIcon className="h-5 w-5 ml-2 inline" />
                    توثيق البائع
                  </button>
                )}
                {selectedVendor.is_verified && (
                  <button
                    onClick={() => verifyVendor(selectedVendor.id, false)}
                    className="btn-secondary flex-1 text-orange-600"
                  >
                    إلغاء التوثيق
                  </button>
                )}
                <button
                  onClick={() => setShowModal(false)}
                  className="btn-secondary flex-1"
                >
                  إغلاق
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminVendorsPage;
