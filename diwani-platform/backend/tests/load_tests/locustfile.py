"""
اختبارات الضغط والأداء - Locust
================================

اختبارات الحمل للتحقق من أداء المنصة تحت الضغط

التشغيل:
    locust -f locustfile.py --host=http://localhost:8000

أو بدون واجهة رسومية:
    locust -f locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 1m
"""

import json
import random
import urllib.parse
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner


# =============================================
# تكوين الاختبارات
# =============================================

# أرقام هواتف وهمية للاختبار
TEST_PHONES = [f'+9665{str(i).zfill(8)}' for i in range(1000, 2000)]

# رموز OTP وهمية (في وضع الاختبار)
TEST_OTP = '123456'


# =============================================
# مستخدم عادي (عميل)
# =============================================

class CustomerUser(HttpUser):
    """محاكاة سلوك العميل العادي"""

    wait_time = between(1, 5)  # انتظار 1-5 ثواني بين الطلبات
    weight = 5  # وزن أكبر - عملاء أكثر

    def on_start(self):
        """تسجيل الدخول عند البدء"""
        self.access_token = None
        self.try_login()

    def try_login(self):
        """محاولة تسجيل الدخول"""
        phone = random.choice(TEST_PHONES)

        # طلب OTP
        response = self.client.post('/api/v1/users/auth/login', json={
            'phone_number': phone
        })

        if response.status_code == 200:
            # التحقق من OTP
            response = self.client.post('/api/v1/users/auth/verify', json={
                'phone_number': phone,
                'code': TEST_OTP
            })

            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')

    @property
    def auth_headers(self):
        if self.access_token:
            return {'Authorization': f'Bearer {self.access_token}'}
        return {}

    @task(10)
    def view_homepage_stats(self):
        """عرض إحصائيات الصفحة الرئيسية"""
        self.client.get('/api/v1/platform/stats/')

    @task(8)
    def browse_products(self):
        """تصفح المنتجات"""
        self.client.get('/api/v1/products/products?limit=20')

    @task(5)
    def search_products(self):
        """البحث عن منتجات"""
        search_terms = ['أسمنت', 'حديد', 'رمل', 'طوب', 'جبس']
        term = random.choice(search_terms)
        encoded_term = urllib.parse.quote(term)
        self.client.get(f'/api/v1/search/products?q={encoded_term}')

    @task(3)
    def view_product_detail(self):
        """عرض تفاصيل منتج"""
        # جلب قائمة المنتجات أولاً
        response = self.client.get('/api/v1/products/products?limit=10')
        if response.status_code == 200:
            data = response.json()
            products = data.get('items', data) if isinstance(data, dict) else data
            if products:
                product = random.choice(products)
                self.client.get(f'/api/v1/products/products/{product["id"]}')

    @task(3)
    def browse_stores(self):
        """تصفح المتاجر"""
        self.client.get('/api/v1/stores/stores?limit=20')

    @task(2)
    def view_my_profile(self):
        """عرض ملفي الشخصي"""
        if self.access_token:
            self.client.get('/api/v1/users/me', headers=self.auth_headers)

    @task(2)
    def view_my_orders(self):
        """عرض طلباتي"""
        if self.access_token:
            self.client.get('/api/v1/orders/orders', headers=self.auth_headers)

    @task(1)
    def view_my_stats(self):
        """عرض إحصائياتي"""
        if self.access_token:
            self.client.get('/api/v1/users/me/stats', headers=self.auth_headers)


# =============================================
# مستخدم بائع/تاجر
# =============================================

class VendorUser(HttpUser):
    """محاكاة سلوك البائع"""

    wait_time = between(2, 8)
    weight = 2

    def on_start(self):
        self.access_token = None
        self.try_login()

    def try_login(self):
        phone = random.choice(TEST_PHONES[500:700])  # شريحة مختلفة

        response = self.client.post('/api/v1/users/auth/login', json={
            'phone_number': phone
        })

        if response.status_code == 200:
            response = self.client.post('/api/v1/users/auth/verify', json={
                'phone_number': phone,
                'code': TEST_OTP
            })

            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')

    @property
    def auth_headers(self):
        if self.access_token:
            return {'Authorization': f'Bearer {self.access_token}'}
        return {}

    @task(5)
    def view_my_store(self):
        """عرض متجري"""
        if self.access_token:
            self.client.get('/api/v1/stores/vendor/store', headers=self.auth_headers)

    @task(4)
    def view_my_products(self):
        """عرض منتجاتي"""
        if self.access_token:
            self.client.get('/api/v1/products/vendor/products', headers=self.auth_headers)

    @task(3)
    def view_my_orders(self):
        """عرض الطلبات الواردة"""
        if self.access_token:
            self.client.get('/api/v1/orders/vendor/orders', headers=self.auth_headers)

    @task(2)
    def view_store_stats(self):
        """عرض إحصائيات المتجر"""
        if self.access_token:
            self.client.get('/api/v1/stores/vendor/store/stats', headers=self.auth_headers)

    @task(2)
    def view_balance(self):
        """عرض الرصيد"""
        if self.access_token:
            self.client.get('/api/v1/stores/vendor/store/balance', headers=self.auth_headers)


# =============================================
# مستخدم سائق
# =============================================

class DriverUser(HttpUser):
    """محاكاة سلوك السائق"""

    wait_time = between(3, 10)
    weight = 1

    def on_start(self):
        self.access_token = None
        self.try_login()

    def try_login(self):
        phone = random.choice(TEST_PHONES[700:900])

        response = self.client.post('/api/v1/users/auth/login', json={
            'phone_number': phone
        })

        if response.status_code == 200:
            response = self.client.post('/api/v1/users/auth/verify', json={
                'phone_number': phone,
                'code': TEST_OTP
            })

            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')

    @property
    def auth_headers(self):
        if self.access_token:
            return {'Authorization': f'Bearer {self.access_token}'}
        return {}

    @task(5)
    def view_available_deliveries(self):
        """عرض التوصيلات المتاحة"""
        if self.access_token:
            self.client.get('/api/v1/tracking/driver/deliveries/available', headers=self.auth_headers)

    @task(4)
    def view_my_deliveries(self):
        """عرض توصيلاتي"""
        if self.access_token:
            self.client.get('/api/v1/tracking/driver/deliveries', headers=self.auth_headers)

    @task(3)
    def update_location(self):
        """تحديث موقعي"""
        if self.access_token:
            lat = 24.7136 + random.uniform(-0.1, 0.1)
            lng = 46.6753 + random.uniform(-0.1, 0.1)

            self.client.post('/api/v1/users/me/driver-profile/location',
                           json={'latitude': lat, 'longitude': lng},
                           headers=self.auth_headers)

    @task(2)
    def view_earnings(self):
        """عرض أرباحي"""
        if self.access_token:
            self.client.get('/api/v1/tracking/driver/earnings', headers=self.auth_headers)


# =============================================
# مستخدم مدير (اختبار Admin APIs)
# =============================================

class AdminUser(HttpUser):
    """محاكاة سلوك المدير"""

    wait_time = between(5, 15)
    weight = 1  # عدد قليل من المدراء

    def on_start(self):
        self.access_token = None
        # المدير يسجل دخول خاص
        self.try_admin_login()

    def try_admin_login(self):
        """تسجيل دخول المدير"""
        phone = '+966500000000'  # رقم المدير الافتراضي

        response = self.client.post('/api/v1/users/auth/login', json={
            'phone_number': phone
        })

        if response.status_code == 200:
            response = self.client.post('/api/v1/users/auth/verify', json={
                'phone_number': phone,
                'code': TEST_OTP
            })

            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')

    @property
    def auth_headers(self):
        if self.access_token:
            return {'Authorization': f'Bearer {self.access_token}'}
        return {}

    @task(5)
    def view_admin_stats(self):
        """عرض إحصائيات الإدارة"""
        if self.access_token:
            self.client.get('/api/v1/users/admin/stats', headers=self.auth_headers)

    @task(4)
    def list_users(self):
        """عرض قائمة المستخدمين"""
        if self.access_token:
            page = random.randint(1, 5)
            self.client.get(f'/api/v1/users/admin/users?page={page}', headers=self.auth_headers)

    @task(3)
    def list_vendors(self):
        """عرض قائمة البائعين"""
        if self.access_token:
            self.client.get('/api/v1/users/admin/vendors', headers=self.auth_headers)

    @task(3)
    def list_drivers(self):
        """عرض قائمة السائقين"""
        if self.access_token:
            self.client.get('/api/v1/users/admin/drivers', headers=self.auth_headers)

    @task(2)
    def search_users(self):
        """البحث عن مستخدمين"""
        if self.access_token:
            search_terms = ['أحمد', 'محمد', 'خالد', 'عبدالله']
            term = random.choice(search_terms)
            self.client.get(f'/api/v1/users/admin/users?search={term}', headers=self.auth_headers)

    @task(2)
    def filter_by_status(self):
        """تصفية حسب الحالة"""
        if self.access_token:
            statuses = ['active', 'pending', 'suspended']
            status = random.choice(statuses)
            self.client.get(f'/api/v1/users/admin/users?status={status}', headers=self.auth_headers)


# =============================================
# أحداث الاختبار
# =============================================

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """عند بدء الاختبار"""
    print("=" * 60)
    print("بدء اختبارات الضغط لمنصة ديواني")
    print("=" * 60)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """عند انتهاء الاختبار"""
    print("=" * 60)
    print("انتهاء اختبارات الضغط")
    print("=" * 60)


# =============================================
# تكوين إضافي
# =============================================

# يمكن تشغيل الاختبار بالأمر:
# locust -f locustfile.py --host=http://localhost:8000
#
# للاختبار بدون واجهة رسومية:
# locust -f locustfile.py --host=http://localhost:8000 --headless -u 100 -r 10 -t 60s
#
# المعاملات:
# -u: عدد المستخدمين الإجمالي
# -r: معدل إضافة المستخدمين بالثانية
# -t: مدة الاختبار
