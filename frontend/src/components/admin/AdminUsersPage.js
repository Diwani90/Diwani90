import React, { useState, useEffect } from 'react';
import { useAuth } from '../../App';
import { useToast } from '../ui/toast';
import axios from 'axios';
import {
  UsersIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  EyeIcon,
  PencilIcon,
  TrashIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ChevronLeftIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline';

const AdminUsersPage = () => {
  const { user } = useAuth();
  const { toast } = useToast();

  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 20,
    total: 0,
    total_pages: 0
  });
  const [filters, setFilters] = useState({
    search: '',
    user_type: '',
    status: ''
  });
  const [selectedUser, setSelectedUser] = useState(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    fetchUsers();
  }, [pagination.page, filters]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: pagination.page,
        per_page: pagination.per_page,
        ...(filters.search && { search: filters.search }),
        ...(filters.user_type && { user_type: filters.user_type }),
        ...(filters.status && { status: filters.status })
      });

      const response = await axios.get(`/users/admin/users?${params}`);
      setUsers(response.data.items || []);
      setPagination(prev => ({
        ...prev,
        total: response.data.total,
        total_pages: response.data.total_pages
      }));
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('خطأ', 'حدث خطأ في تحميل المستخدمين');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPagination(prev => ({ ...prev, page: 1 }));
    fetchUsers();
  };

  const updateUserStatus = async (userId, newStatus) => {
    try {
      await axios.put(`/users/admin/users/${userId}/status?status=${newStatus}`);
      toast.success('تم بنجاح', 'تم تحديث حالة المستخدم');
      fetchUsers();
      setShowModal(false);
    } catch (error) {
      console.error('Error updating user status:', error);
      toast.error('خطأ', 'حدث خطأ في تحديث الحالة');
    }
  };

  const deleteUser = async (userId) => {
    if (!window.confirm('هل أنت متأكد من حذف هذا المستخدم؟')) return;

    try {
      await axios.delete(`/users/admin/users/${userId}`);
      toast.success('تم بنجاح', 'تم حذف المستخدم');
      fetchUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
      toast.error('خطأ', 'حدث خطأ في حذف المستخدم');
    }
  };

  const viewUserDetails = async (userId) => {
    try {
      const response = await axios.get(`/users/admin/users/${userId}`);
      setSelectedUser(response.data);
      setShowModal(true);
    } catch (error) {
      console.error('Error fetching user details:', error);
      toast.error('خطأ', 'حدث خطأ في تحميل بيانات المستخدم');
    }
  };

  const getUserTypeLabel = (type) => {
    const labels = {
      'customer': 'عميل',
      'vendor': 'بائع',
      'driver': 'سائق',
      'admin': 'مدير'
    };
    return labels[type] || type;
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

  if (loading && users.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 pb-8">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-4 py-6 text-white">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl font-bold flex items-center">
            <UsersIcon className="h-7 w-7 ml-2" />
            إدارة المستخدمين
          </h1>
          <p className="text-sm opacity-90 mt-1">عرض وإدارة جميع مستخدمي المنصة</p>
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
                placeholder="البحث بالاسم أو الهاتف..."
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                className="input-field pr-10"
              />
            </div>

            <select
              value={filters.user_type}
              onChange={(e) => setFilters(prev => ({ ...prev, user_type: e.target.value }))}
              className="input-field"
            >
              <option value="">جميع الأنواع</option>
              <option value="customer">عميل</option>
              <option value="vendor">بائع</option>
              <option value="driver">سائق</option>
              <option value="admin">مدير</option>
            </select>

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
            <p className="text-sm text-gray-600">إجمالي المستخدمين</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4 text-center">
            <p className="text-2xl font-bold text-green-600">
              {users.filter(u => u.status === 'active').length}
            </p>
            <p className="text-sm text-gray-600">نشط</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4 text-center">
            <p className="text-2xl font-bold text-yellow-600">
              {users.filter(u => u.status === 'pending').length}
            </p>
            <p className="text-sm text-gray-600">قيد الانتظار</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm p-4 text-center">
            <p className="text-2xl font-bold text-red-600">
              {users.filter(u => u.status === 'suspended' || u.status === 'banned').length}
            </p>
            <p className="text-sm text-gray-600">موقوف/محظور</p>
          </div>
        </div>

        {/* Users Table */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    المستخدم
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    الهاتف
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    النوع
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    الحالة
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    تاريخ التسجيل
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    الإجراءات
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                          <span className="text-blue-600 font-medium">
                            {u.full_name?.charAt(0) || '?'}
                          </span>
                        </div>
                        <div className="mr-4">
                          <div className="text-sm font-medium text-gray-900">{u.full_name}</div>
                          <div className="text-sm text-gray-500">{u.email || '-'}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {u.phone_number}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                        {getUserTypeLabel(u.user_type)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(u.status)}`}>
                        {getStatusLabel(u.status)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(u.created_at).toLocaleDateString('ar-SA')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => viewUserDetails(u.id)}
                          className="text-blue-600 hover:text-blue-900"
                          title="عرض التفاصيل"
                        >
                          <EyeIcon className="h-5 w-5" />
                        </button>
                        {u.status === 'active' ? (
                          <button
                            onClick={() => updateUserStatus(u.id, 'suspended')}
                            className="text-orange-600 hover:text-orange-900"
                            title="إيقاف"
                          >
                            <XCircleIcon className="h-5 w-5" />
                          </button>
                        ) : (
                          <button
                            onClick={() => updateUserStatus(u.id, 'active')}
                            className="text-green-600 hover:text-green-900"
                            title="تفعيل"
                          >
                            <CheckCircleIcon className="h-5 w-5" />
                          </button>
                        )}
                        <button
                          onClick={() => deleteUser(u.id)}
                          className="text-red-600 hover:text-red-900"
                          title="حذف"
                        >
                          <TrashIcon className="h-5 w-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

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

      {/* User Details Modal */}
      {showModal && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">تفاصيل المستخدم</h2>

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-gray-500">الاسم</label>
                    <p className="font-medium">{selectedUser.full_name}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">الهاتف</label>
                    <p className="font-medium">{selectedUser.phone_number}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">البريد</label>
                    <p className="font-medium">{selectedUser.email || '-'}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">النوع</label>
                    <p className="font-medium">{getUserTypeLabel(selectedUser.user_type)}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">الحالة</label>
                    <p className={`inline-block px-2 py-1 text-xs rounded-full ${getStatusColor(selectedUser.status)}`}>
                      {getStatusLabel(selectedUser.status)}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">عدد الطلبات</label>
                    <p className="font-medium">{selectedUser.orders_count || 0}</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">إجمالي الإنفاق</label>
                    <p className="font-medium">{selectedUser.total_spent || 0} ر.س</p>
                  </div>
                  <div>
                    <label className="text-sm text-gray-500">نقاط الولاء</label>
                    <p className="font-medium">{selectedUser.loyalty_points || 0}</p>
                  </div>
                </div>

                {selectedUser.vendor_profile && (
                  <div className="border-t pt-4">
                    <h3 className="font-semibold mb-2">معلومات البائع</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm text-gray-500">اسم الشركة</label>
                        <p className="font-medium">{selectedUser.vendor_profile.company_name}</p>
                      </div>
                      <div>
                        <label className="text-sm text-gray-500">السجل التجاري</label>
                        <p className="font-medium">{selectedUser.vendor_profile.commercial_register || '-'}</p>
                      </div>
                    </div>
                  </div>
                )}

                {selectedUser.driver_profile && (
                  <div className="border-t pt-4">
                    <h3 className="font-semibold mb-2">معلومات السائق</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm text-gray-500">رقم الرخصة</label>
                        <p className="font-medium">{selectedUser.driver_profile.license_number}</p>
                      </div>
                      <div>
                        <label className="text-sm text-gray-500">نوع المركبة</label>
                        <p className="font-medium">{selectedUser.driver_profile.vehicle_type}</p>
                      </div>
                      <div>
                        <label className="text-sm text-gray-500">لوحة المركبة</label>
                        <p className="font-medium">{selectedUser.driver_profile.vehicle_plate}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex gap-3 mt-6">
                {selectedUser.status !== 'active' && (
                  <button
                    onClick={() => updateUserStatus(selectedUser.id, 'active')}
                    className="btn-primary flex-1"
                  >
                    تفعيل
                  </button>
                )}
                {selectedUser.status === 'active' && (
                  <button
                    onClick={() => updateUserStatus(selectedUser.id, 'suspended')}
                    className="btn-secondary flex-1 text-orange-600"
                  >
                    إيقاف
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

export default AdminUsersPage;
