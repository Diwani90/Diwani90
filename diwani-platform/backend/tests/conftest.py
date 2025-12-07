"""
إعدادات pytest والـ fixtures المشتركة
=====================================
"""

import os
import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import uuid4

import django
from django.conf import settings

# تكوين Django قبل استيراد النماذج
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.test')
django.setup()

from django.contrib.gis.geos import Point
from django.test import Client
from django.utils import timezone

from apps.users.models import User, UserType


# =============================================
# Pytest Configuration
# =============================================

@pytest.fixture(scope='session')
def django_db_setup():
    """إعداد قاعدة البيانات للاختبارات"""
    settings.DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }


@pytest.fixture
def api_client():
    """عميل API للاختبارات"""
    return Client()


# =============================================
# User Fixtures
# =============================================

@pytest.fixture
def customer_user(db):
    """مستخدم عميل للاختبارات"""
    user = User.objects.create_user(
        phone_number='+966501234567',
        password='testpass123',
        first_name='أحمد',
        last_name='محمد',
        user_type=UserType.CUSTOMER,
        is_phone_verified=True,
    )
    return user


@pytest.fixture
def vendor_user(db):
    """مستخدم تاجر للاختبارات"""
    user = User.objects.create_user(
        phone_number='+966507654321',
        password='testpass123',
        first_name='خالد',
        last_name='علي',
        user_type=UserType.VENDOR,
        is_phone_verified=True,
    )
    return user


@pytest.fixture
def driver_user(db):
    """مستخدم سائق للاختبارات"""
    user = User.objects.create_user(
        phone_number='+966509876543',
        password='testpass123',
        first_name='محمد',
        last_name='سالم',
        user_type=UserType.DRIVER,
        is_phone_verified=True,
    )
    return user


@pytest.fixture
def admin_user(db):
    """مستخدم مدير للاختبارات"""
    user = User.objects.create_superuser(
        phone_number='+966500000000',
        password='adminpass123',
        first_name='مدير',
        last_name='النظام',
    )
    return user


# =============================================
# Store Fixtures
# =============================================

@pytest.fixture
def store(db, vendor_user):
    """متجر للاختبارات"""
    from apps.stores.models import Store, StoreType, StoreStatus

    return Store.objects.create(
        owner=vendor_user,
        store_type=StoreType.SUPPLIER,
        name='متجر اختباري',
        name_en='Test Store',
        phone='+966501112222',
        address='الرياض، حي النخيل',
        city='الرياض',
        location=Point(46.6753, 24.7136, srid=4326),
        status=StoreStatus.ACTIVE,
    )


# =============================================
# Product Fixtures
# =============================================

@pytest.fixture
def category(db):
    """تصنيف للاختبارات"""
    from apps.products.models import Category

    return Category.objects.create(
        name='مواد بناء',
        name_en='Building Materials',
        slug='building-materials',
    )


@pytest.fixture
def product(db, store, category):
    """منتج للاختبارات"""
    from apps.products.models import Product, ProductType, ProductStatus

    return Product.objects.create(
        vendor=store,
        category=category,
        product_type=ProductType.STOCK,
        name='أسمنت بورتلاندي',
        name_en='Portland Cement',
        price=Decimal('25.00'),
        stock_quantity=Decimal('1000'),
        status=ProductStatus.ACTIVE,
    )


# =============================================
# Order Fixtures
# =============================================

@pytest.fixture
def order(db, customer_user, store, product):
    """طلب للاختبارات"""
    from apps.orders.models import Order, OrderStatus

    order = Order.objects.create(
        customer=customer_user,
        vendor=store,
        status=OrderStatus.PENDING,
        subtotal=Decimal('250.00'),
        delivery_fee=Decimal('25.00'),
        tax_amount=Decimal('41.25'),
        total_amount=Decimal('316.25'),
        delivery_address='الرياض، حي الياسمين',
        delivery_location=Point(46.6500, 24.7500, srid=4326),
    )
    return order


# =============================================
# Delivery Fixtures
# =============================================

@pytest.fixture
def delivery(db, order, driver_user):
    """توصيل للاختبارات"""
    from apps.tracking.models import Delivery, DeliveryStatus, DeliveryType

    return Delivery.objects.create(
        order=order,
        driver=driver_user,
        delivery_type=DeliveryType.STANDARD,
        status=DeliveryStatus.ASSIGNED,
        pickup_location=Point(46.6753, 24.7136, srid=4326),
        pickup_address='متجر اختباري، الرياض',
        pickup_contact_name='خالد علي',
        pickup_contact_phone='+966507654321',
        dropoff_location=Point(46.6500, 24.7500, srid=4326),
        dropoff_address='الرياض، حي الياسمين',
        dropoff_contact_name='أحمد محمد',
        dropoff_contact_phone='+966501234567',
    )


# =============================================
# Authentication Fixtures
# =============================================

@pytest.fixture
def customer_auth_headers(customer_user):
    """رؤوس المصادقة لعميل"""
    from apps.users.services import AuthService

    tokens = AuthService.generate_tokens(customer_user)
    return {'Authorization': f"Bearer {tokens['access_token']}"}


@pytest.fixture
def vendor_auth_headers(vendor_user):
    """رؤوس المصادقة لتاجر"""
    from apps.users.services import AuthService

    tokens = AuthService.generate_tokens(vendor_user)
    return {'Authorization': f"Bearer {tokens['access_token']}"}


@pytest.fixture
def driver_auth_headers(driver_user):
    """رؤوس المصادقة لسائق"""
    from apps.users.services import AuthService

    tokens = AuthService.generate_tokens(driver_user)
    return {'Authorization': f"Bearer {tokens['access_token']}"}


@pytest.fixture
def admin_auth_headers(admin_user):
    """رؤوس المصادقة لمدير"""
    from apps.users.services import AuthService

    tokens = AuthService.generate_tokens(admin_user)
    return {'Authorization': f"Bearer {tokens['access_token']}"}


# =============================================
# Helper Functions
# =============================================

@pytest.fixture
def make_location():
    """منشئ مواقع جغرافية"""
    def _make_location(lat=24.7136, lng=46.6753):
        return Point(lng, lat, srid=4326)
    return _make_location


@pytest.fixture
def riyadh_location():
    """موقع الرياض"""
    return Point(46.6753, 24.7136, srid=4326)


@pytest.fixture
def jeddah_location():
    """موقع جدة"""
    return Point(39.1728, 21.5433, srid=4326)
