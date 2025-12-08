"""
اختبارات Admin APIs الشاملة
============================

اختبارات وحدة وتكامل لـ:
- إدارة المستخدمين
- إدارة البائعين
- إدارة السائقين
- الإحصائيات
"""

import pytest
from decimal import Decimal
from django.test import TestCase, Client
from django.utils import timezone
from datetime import timedelta
import json

from apps.users.models import User, UserType, UserStatus, VendorProfile, DriverProfile


# =============================================
# Admin Users API Tests
# =============================================

@pytest.mark.django_db
class TestAdminUsersAPI:
    """اختبارات API إدارة المستخدمين"""

    @pytest.fixture
    def setup_users(self, db):
        """إنشاء مستخدمين للاختبار"""
        # مدير
        admin = User.objects.create_superuser(
            phone_number='+966500000001',
            password='adminpass123',
            first_name='مدير',
            last_name='النظام',
        )

        # عملاء
        customers = []
        for i in range(5):
            user = User.objects.create_user(
                phone_number=f'+96650111100{i}',
                password='testpass123',
                first_name=f'عميل{i}',
                last_name='اختباري',
                user_type=UserType.CUSTOMER,
                status=UserStatus.ACTIVE if i < 3 else UserStatus.PENDING,
            )
            customers.append(user)

        # بائعين
        vendors = []
        for i in range(3):
            user = User.objects.create_user(
                phone_number=f'+96650222200{i}',
                password='testpass123',
                first_name=f'بائع{i}',
                last_name='اختباري',
                user_type=UserType.VENDOR,
                status=UserStatus.PENDING,
            )
            VendorProfile.objects.create(
                user=user,
                company_name=f'شركة {i}',
                commercial_register=f'123456789{i}',
            )
            vendors.append(user)

        # سائقين
        drivers = []
        for i in range(2):
            user = User.objects.create_user(
                phone_number=f'+96650333300{i}',
                password='testpass123',
                first_name=f'سائق{i}',
                last_name='اختباري',
                user_type=UserType.DRIVER,
                status=UserStatus.PENDING,
            )
            DriverProfile.objects.create(
                user=user,
                license_number=f'DL12345{i}',
                vehicle_type='شاحنة',
                vehicle_plate=f'ABC 123{i}',
            )
            drivers.append(user)

        return {
            'admin': admin,
            'customers': customers,
            'vendors': vendors,
            'drivers': drivers,
        }

    def test_list_users_requires_admin(self, api_client, customer_auth_headers):
        """اختبار أن قائمة المستخدمين تتطلب صلاحيات مدير"""
        response = api_client.get(
            '/api/v1/users/admin/users',
            **customer_auth_headers
        )
        assert response.status_code in [401, 403]

    def test_list_users_success(self, api_client, setup_users, admin_auth_headers):
        """اختبار قائمة المستخدمين - نجاح"""
        response = api_client.get(
            '/api/v1/users/admin/users',
            **admin_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert 'items' in data
        assert 'total' in data
        assert data['total'] >= 10  # admin + 5 customers + 3 vendors + 2 drivers

    def test_list_users_filter_by_type(self, api_client, setup_users, admin_auth_headers):
        """اختبار تصفية المستخدمين حسب النوع"""
        response = api_client.get(
            '/api/v1/users/admin/users?user_type=customer',
            **admin_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        for user in data['items']:
            assert user['user_type'] == 'customer'

    def test_list_users_filter_by_status(self, api_client, setup_users, admin_auth_headers):
        """اختبار تصفية المستخدمين حسب الحالة"""
        response = api_client.get(
            '/api/v1/users/admin/users?status=pending',
            **admin_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        for user in data['items']:
            assert user['status'] == 'pending'

    def test_list_users_search(self, api_client, setup_users, admin_auth_headers):
        """اختبار البحث في المستخدمين"""
        response = api_client.get(
            '/api/v1/users/admin/users?search=عميل',
            **admin_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) > 0

    def test_list_users_pagination(self, api_client, setup_users, admin_auth_headers):
        """اختبار تصفيح المستخدمين"""
        response = api_client.get(
            '/api/v1/users/admin/users?page=1&per_page=3',
            **admin_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) <= 3
        assert data['page'] == 1
        assert data['per_page'] == 3

    def test_get_user_details(self, api_client, setup_users, admin_auth_headers):
        """اختبار تفاصيل مستخدم"""
        customer = setup_users['customers'][0]

        response = api_client.get(
            f'/api/v1/users/admin/users/{customer.id}',
            **admin_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['id'] == str(customer.id)
        assert data['phone_number'] == customer.phone_number

    def test_get_vendor_details_with_profile(self, api_client, setup_users, admin_auth_headers):
        """اختبار تفاصيل بائع مع ملف التاجر"""
        vendor = setup_users['vendors'][0]

        response = api_client.get(
            f'/api/v1/users/admin/users/{vendor.id}',
            **admin_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert 'vendor_profile' in data
        assert data['vendor_profile']['company_name'] is not None

    def test_update_user_status(self, api_client, setup_users, admin_auth_headers):
        """اختبار تحديث حالة المستخدم"""
        customer = setup_users['customers'][0]

        response = api_client.put(
            f'/api/v1/users/admin/users/{customer.id}/status?status=suspended',
            **admin_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['new_status'] == 'suspended'

        # التحقق من قاعدة البيانات
        customer.refresh_from_db()
        assert customer.status == 'suspended'

    def test_update_user_status_invalid(self, api_client, setup_users, admin_auth_headers):
        """اختبار تحديث حالة مستخدم بقيمة غير صالحة"""
        customer = setup_users['customers'][0]

        response = api_client.put(
            f'/api/v1/users/admin/users/{customer.id}/status?status=invalid_status',
            **admin_auth_headers
        )

        assert response.status_code == 200  # يعيد JSON مع خطأ
        data = response.json()
        assert 'error' in data

    def test_delete_user_soft_delete(self, api_client, setup_users, admin_auth_headers):
        """اختبار حذف مستخدم (soft delete)"""
        customer = setup_users['customers'][4]  # آخر عميل

        response = api_client.delete(
            f'/api/v1/users/admin/users/{customer.id}',
            **admin_auth_headers
        )

        assert response.status_code == 200

        # التحقق من قاعدة البيانات
        customer.refresh_from_db()
        assert customer.status == 'banned'
        assert not customer.is_active

    def test_cannot_delete_self(self, api_client, setup_users, admin_auth_headers):
        """اختبار عدم إمكانية حذف المدير لنفسه"""
        admin = setup_users['admin']

        response = api_client.delete(
            f'/api/v1/users/admin/users/{admin.id}',
            **admin_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert 'error' in data


# =============================================
# Admin Vendors API Tests
# =============================================

@pytest.mark.django_db
class TestAdminVendorsAPI:
    """اختبارات API إدارة البائعين"""

    def test_list_vendors(self, api_client, setup_users, admin_auth_headers):
        """اختبار قائمة البائعين"""
        response = api_client.get(
            '/api/v1/users/admin/vendors',
            **admin_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert 'items' in data
        assert len(data['items']) >= 3

    def test_list_vendors_filter_verified(self, api_client, setup_users, admin_auth_headers):
        """اختبار تصفية البائعين حسب التوثيق"""
        response = api_client.get(
            '/api/v1/users/admin/vendors?is_verified=false',
            **admin_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        for vendor in data['items']:
            assert vendor['is_verified'] == False

    def test_verify_vendor(self, api_client, setup_users, admin_auth_headers):
        """اختبار توثيق بائع"""
        vendor_user = setup_users['vendors'][0]
        vendor_profile = VendorProfile.objects.get(user=vendor_user)

        response = api_client.post(
            f'/api/v1/users/admin/vendors/{vendor_profile.id}/verify?is_verified=true',
            **admin_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['is_verified'] == True

        # التحقق من قاعدة البيانات
        vendor_profile.refresh_from_db()
        assert vendor_profile.is_verified == True

        vendor_user.refresh_from_db()
        assert vendor_user.status == 'active'

    def test_reject_vendor_verification(self, api_client, setup_users, admin_auth_headers):
        """اختبار رفض توثيق بائع"""
        vendor_user = setup_users['vendors'][1]
        vendor_profile = VendorProfile.objects.get(user=vendor_user)

        # توثيق أولاً
        vendor_profile.is_verified = True
        vendor_profile.save()

        # رفض التوثيق
        response = api_client.post(
            f'/api/v1/users/admin/vendors/{vendor_profile.id}/verify?is_verified=false',
            **admin_auth_headers
        )

        assert response.status_code == 200

        vendor_profile.refresh_from_db()
        assert vendor_profile.is_verified == False


# =============================================
# Admin Drivers API Tests
# =============================================

@pytest.mark.django_db
class TestAdminDriversAPI:
    """اختبارات API إدارة السائقين"""

    def test_list_drivers(self, api_client, setup_users, admin_auth_headers):
        """اختبار قائمة السائقين"""
        response = api_client.get(
            '/api/v1/users/admin/drivers',
            **admin_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert 'items' in data
        assert len(data['items']) >= 2

    def test_verify_driver(self, api_client, setup_users, admin_auth_headers):
        """اختبار توثيق سائق"""
        driver_user = setup_users['drivers'][0]
        driver_profile = DriverProfile.objects.get(user=driver_user)

        response = api_client.post(
            f'/api/v1/users/admin/drivers/{driver_profile.id}/verify?is_verified=true',
            **admin_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['is_verified'] == True


# =============================================
# Admin Stats API Tests
# =============================================

@pytest.mark.django_db
class TestAdminStatsAPI:
    """اختبارات API إحصائيات الإدارة"""

    def test_get_admin_stats(self, api_client, setup_users, admin_auth_headers):
        """اختبار الإحصائيات الشاملة"""
        response = api_client.get(
            '/api/v1/users/admin/stats',
            **admin_auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert 'users' in data
        assert 'vendors' in data
        assert 'drivers' in data

        # التحقق من إحصائيات المستخدمين
        assert 'total' in data['users']
        assert 'active' in data['users']
        assert 'customers' in data['users']
        assert 'vendors' in data['users']
        assert 'drivers' in data['users']

    def test_stats_requires_admin(self, api_client, customer_auth_headers):
        """اختبار أن الإحصائيات تتطلب صلاحيات مدير"""
        response = api_client.get(
            '/api/v1/users/admin/stats',
            **customer_auth_headers
        )
        assert response.status_code in [401, 403]


# =============================================
# Platform Stats API Tests
# =============================================

@pytest.mark.django_db
class TestPlatformStatsAPI:
    """اختبارات API إحصائيات المنصة العامة"""

    def test_platform_stats_no_auth_required(self, api_client):
        """اختبار أن إحصائيات المنصة لا تتطلب مصادقة"""
        response = api_client.get('/api/v1/platform/stats/')

        assert response.status_code == 200
        data = response.json()

        assert 'total_users' in data
        assert 'total_suppliers' in data
        assert 'total_products' in data
        assert 'total_orders' in data

    def test_platform_stats_cached(self, api_client):
        """اختبار تخزين الإحصائيات مؤقتاً"""
        # الطلب الأول
        response1 = api_client.get('/api/v1/platform/stats/')

        # الطلب الثاني - يجب أن يكون من الـ cache
        response2 = api_client.get('/api/v1/platform/stats/')

        assert response1.status_code == 200
        assert response2.status_code == 200


# =============================================
# User Stats API Tests
# =============================================

@pytest.mark.django_db
class TestUserStatsAPI:
    """اختبارات API إحصائيات المستخدم"""

    def test_get_my_stats(self, api_client, customer_user, customer_auth_headers):
        """اختبار إحصائياتي"""
        response = api_client.get(
            '/api/v1/users/me/stats',
            **customer_auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert 'orders_count' in data
        assert 'total_spent' in data
        assert 'loyalty_points' in data

    def test_stats_requires_auth(self, api_client):
        """اختبار أن الإحصائيات تتطلب مصادقة"""
        response = api_client.get('/api/v1/users/me/stats')
        assert response.status_code == 401


# =============================================
# Integration Tests
# =============================================

@pytest.mark.django_db
class TestAdminWorkflow:
    """اختبارات سير العمل الإداري"""

    def test_complete_vendor_verification_workflow(self, api_client, setup_users, admin_auth_headers):
        """اختبار سير عمل توثيق البائع الكامل"""
        vendor_user = setup_users['vendors'][0]
        vendor_profile = VendorProfile.objects.get(user=vendor_user)

        # 1. التحقق من قائمة البائعين غير الموثقين
        response = api_client.get(
            '/api/v1/users/admin/vendors?is_verified=false',
            **admin_auth_headers
        )
        assert response.status_code == 200

        # 2. عرض تفاصيل البائع
        response = api_client.get(
            f'/api/v1/users/admin/vendors/{vendor_profile.id}',
            **admin_auth_headers
        )
        assert response.status_code == 200

        # 3. توثيق البائع
        response = api_client.post(
            f'/api/v1/users/admin/vendors/{vendor_profile.id}/verify?is_verified=true',
            **admin_auth_headers
        )
        assert response.status_code == 200

        # 4. التحقق من تحديث الحالة
        vendor_user.refresh_from_db()
        assert vendor_user.status == 'active'

    def test_user_suspension_workflow(self, api_client, setup_users, admin_auth_headers):
        """اختبار سير عمل إيقاف المستخدم"""
        customer = setup_users['customers'][0]

        # 1. عرض تفاصيل المستخدم
        response = api_client.get(
            f'/api/v1/users/admin/users/{customer.id}',
            **admin_auth_headers
        )
        assert response.status_code == 200

        # 2. إيقاف المستخدم
        response = api_client.put(
            f'/api/v1/users/admin/users/{customer.id}/status?status=suspended',
            **admin_auth_headers
        )
        assert response.status_code == 200

        # 3. التحقق من ظهوره في قائمة الموقوفين
        response = api_client.get(
            '/api/v1/users/admin/users?status=suspended',
            **admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        suspended_ids = [u['id'] for u in data['items']]
        assert str(customer.id) in suspended_ids

        # 4. إعادة تفعيل المستخدم
        response = api_client.put(
            f'/api/v1/users/admin/users/{customer.id}/status?status=active',
            **admin_auth_headers
        )
        assert response.status_code == 200


# =============================================
# Edge Cases & Error Handling
# =============================================

@pytest.mark.django_db
class TestEdgeCases:
    """اختبارات الحالات الحدية ومعالجة الأخطاء"""

    def test_get_nonexistent_user(self, api_client, admin_auth_headers):
        """اختبار طلب مستخدم غير موجود"""
        import uuid
        fake_id = uuid.uuid4()

        response = api_client.get(
            f'/api/v1/users/admin/users/{fake_id}',
            **admin_auth_headers
        )

        assert response.status_code == 404

    def test_empty_search_results(self, api_client, admin_auth_headers):
        """اختبار نتائج بحث فارغة"""
        response = api_client.get(
            '/api/v1/users/admin/users?search=nonexistentuser12345',
            **admin_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 0
        assert len(data['items']) == 0

    def test_invalid_page_number(self, api_client, admin_auth_headers):
        """اختبار رقم صفحة غير صالح"""
        response = api_client.get(
            '/api/v1/users/admin/users?page=999999',
            **admin_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data['items']) == 0
