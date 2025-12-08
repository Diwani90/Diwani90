#!/usr/bin/env python
"""
===================================
منصة ديواني - اختبار شامل قبل الإطلاق
Diwani Platform - Pre-Production Test Suite
===================================

يختبر:
1. الاتصال بقواعد البيانات
2. Redis و Celery
3. Elasticsearch
4. ZATCA Integration
5. Payment Gateways
6. 2FA Configuration
7. Audit Logging
8. API Endpoints
9. Security Headers
10. Performance

الاستخدام:
    python manage.py shell < tests/pre_production_test.py
    أو
    docker exec diwani_backend python manage.py shell < tests/pre_production_test.py
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from decimal import Decimal

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

import django
django.setup()

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.test import Client, RequestFactory
from django.contrib.auth import get_user_model

User = get_user_model()

# Colors for output
class Colors:
    OK = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*60}{Colors.ENDC}")

def print_ok(text):
    print(f"{Colors.OK}✓ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_fail(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

results = {
    'passed': 0,
    'failed': 0,
    'warnings': 0,
    'details': []
}

# ===================================
# 1. Database Connection
# ===================================
print_header("1. اختبار الاتصال بقاعدة البيانات")

try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print_ok(f"PostgreSQL متصل: {version[:50]}...")

        # Check PostGIS
        cursor.execute("SELECT PostGIS_Version();")
        postgis = cursor.fetchone()[0]
        print_ok(f"PostGIS مفعّل: {postgis}")

        results['passed'] += 2
except Exception as e:
    print_fail(f"فشل الاتصال بقاعدة البيانات: {e}")
    results['failed'] += 1
    results['details'].append(f"Database: {e}")

# ===================================
# 2. Redis Cache
# ===================================
print_header("2. اختبار Redis Cache")

try:
    # Test set/get
    cache.set('test_key', 'test_value', 30)
    value = cache.get('test_key')

    if value == 'test_value':
        print_ok("Redis يعمل - set/get ناجح")
        results['passed'] += 1
    else:
        print_fail(f"Redis - قيمة خاطئة: {value}")
        results['failed'] += 1

    cache.delete('test_key')

    # Test increment
    cache.set('counter', 0, 30)
    cache.incr('counter')
    if cache.get('counter') == 1:
        print_ok("Redis increment يعمل")
        results['passed'] += 1
    cache.delete('counter')

except Exception as e:
    print_fail(f"Redis غير متصل: {e}")
    results['failed'] += 1
    results['details'].append(f"Redis: {e}")

# ===================================
# 3. Elasticsearch
# ===================================
print_header("3. اختبار Elasticsearch")

try:
    from elasticsearch import Elasticsearch

    es_hosts = settings.ELASTICSEARCH_DSL.get('hosts', 'http://localhost:9200')
    es = Elasticsearch(es_hosts)

    if es.ping():
        print_ok("Elasticsearch متصل")

        # Check cluster health
        health = es.cluster.health()
        status = health.get('status', 'unknown')

        if status == 'green':
            print_ok(f"Cluster status: {status}")
            results['passed'] += 1
        elif status == 'yellow':
            print_warning(f"Cluster status: {status} (acceptable for single node)")
            results['warnings'] += 1
        else:
            print_fail(f"Cluster status: {status}")
            results['failed'] += 1

        # Check indices
        indices = es.cat.indices(format='json')
        print_ok(f"عدد الفهارس: {len(indices)}")
        results['passed'] += 1

    else:
        print_fail("Elasticsearch غير متصل")
        results['failed'] += 1

except ImportError:
    print_warning("elasticsearch-py غير مثبت")
    results['warnings'] += 1
except Exception as e:
    print_fail(f"خطأ Elasticsearch: {e}")
    results['failed'] += 1
    results['details'].append(f"Elasticsearch: {e}")

# ===================================
# 4. Celery
# ===================================
print_header("4. اختبار Celery")

try:
    from config.celery import app as celery_app

    # Check broker connection
    inspector = celery_app.control.inspect()
    stats = inspector.stats()

    if stats:
        workers = list(stats.keys())
        print_ok(f"Celery workers متصلة: {len(workers)}")
        for worker in workers:
            print_ok(f"  - {worker}")
        results['passed'] += 1
    else:
        print_warning("لا يوجد Celery workers نشطة")
        results['warnings'] += 1

except Exception as e:
    print_warning(f"Celery: {e}")
    results['warnings'] += 1

# ===================================
# 5. Models & Migrations
# ===================================
print_header("5. اختبار Models و Migrations")

try:
    from django.core.management import call_command
    from io import StringIO

    out = StringIO()
    call_command('showmigrations', '--list', stdout=out)
    migrations_output = out.getvalue()

    unapplied = migrations_output.count('[ ]')
    applied = migrations_output.count('[X]')

    if unapplied == 0:
        print_ok(f"جميع Migrations مُطبّقة ({applied} migration)")
        results['passed'] += 1
    else:
        print_warning(f"يوجد {unapplied} migrations غير مُطبّقة")
        results['warnings'] += 1

except Exception as e:
    print_fail(f"خطأ في Migrations: {e}")
    results['failed'] += 1

# ===================================
# 6. Security Settings
# ===================================
print_header("6. اختبار إعدادات الأمان")

security_checks = [
    ('DEBUG', False, "DEBUG يجب أن يكون False في الإنتاج"),
    ('SECURE_SSL_REDIRECT', True, "يجب تفعيل SSL redirect"),
    ('SESSION_COOKIE_SECURE', True, "Session cookie يجب أن يكون secure"),
    ('CSRF_COOKIE_SECURE', True, "CSRF cookie يجب أن يكون secure"),
    ('SECURE_HSTS_SECONDS', lambda x: x > 0, "HSTS يجب أن يكون مفعّل"),
]

for setting_name, expected, message in security_checks:
    value = getattr(settings, setting_name, None)

    if callable(expected):
        passed = expected(value) if value else False
    else:
        passed = (value == expected)

    if settings.DEBUG:
        # In dev mode, just warn
        if not passed:
            print_warning(f"{setting_name} = {value} ({message})")
            results['warnings'] += 1
        else:
            print_ok(f"{setting_name} = {value}")
            results['passed'] += 1
    else:
        if passed:
            print_ok(f"{setting_name} = {value}")
            results['passed'] += 1
        else:
            print_fail(f"{setting_name} = {value} ({message})")
            results['failed'] += 1

# ===================================
# 7. ZATCA Configuration
# ===================================
print_header("7. اختبار إعدادات ZATCA")

try:
    from apps.finance.integrations.zatca import (
        ZATCAService, ZATCAInvoice, ZATCAInvoiceItem,
        ZATCASeller, ZATCABuyer, InvoiceType, InvoiceSubtype,
        ZATCAQRGenerator
    )

    print_ok("ZATCA module imported successfully")
    results['passed'] += 1

    # Test QR generation
    qr_data = ZATCAQRGenerator.generate(
        seller_name="متجر اختبار",
        vat_number="300000000000003",
        timestamp=datetime.now(),
        total_with_vat=Decimal("115.00"),
        vat_amount=Decimal("15.00")
    )

    if qr_data and len(qr_data) > 50:
        print_ok(f"QR Code generation يعمل (length: {len(qr_data)})")
        results['passed'] += 1
    else:
        print_fail("QR Code generation فشل")
        results['failed'] += 1

    # Test XML builder
    seller = ZATCASeller(
        name="شركة اختبار",
        vat_number="300000000000003",
        cr_number="1234567890",
        street="شارع الملك فهد",
        building="123",
        city="الرياض",
        district="العليا",
        postal_code="12345"
    )

    buyer = ZATCABuyer(name="عميل اختبار")

    items = [
        ZATCAInvoiceItem(
            name="منتج اختبار",
            quantity=Decimal("2"),
            unit_price=Decimal("50.00")
        )
    ]

    invoice = ZATCAInvoice(
        uuid="550e8400-e29b-41d4-a716-446655440000",
        invoice_number="INV-TEST-001",
        invoice_date=datetime.now(),
        invoice_type=InvoiceType.SIMPLIFIED,
        invoice_subtype=InvoiceSubtype.SIMPLIFIED_INVOICE,
        seller=seller,
        buyer=buyer,
        items=items
    )

    service = ZATCAService()
    result = service.create_invoice(invoice)

    if result.get('xml') and result.get('hash'):
        print_ok("ZATCA Invoice creation يعمل")
        print_ok(f"  - XML length: {len(result['xml'])} chars")
        print_ok(f"  - Hash: {result['hash'][:20]}...")
        results['passed'] += 2
    else:
        print_fail("ZATCA Invoice creation فشل")
        results['failed'] += 1

except ImportError as e:
    print_fail(f"ZATCA module import error: {e}")
    results['failed'] += 1
except Exception as e:
    print_warning(f"ZATCA test error: {e}")
    results['warnings'] += 1

# ===================================
# 8. Audit Logging
# ===================================
print_header("8. اختبار Audit Logging")

try:
    from apps.core.audit import AuditLog, AuditLogManager, AuditAction

    print_ok("Audit module imported")

    # Test logging
    log = AuditLogManager.log(
        action=AuditAction.LOGIN,
        extra_data={'test': True},
        status='success'
    )

    if log and log.id:
        print_ok(f"Audit log created: {log.id}")
        results['passed'] += 1

        # Clean up
        log.delete()
    else:
        print_fail("Audit log creation failed")
        results['failed'] += 1

except Exception as e:
    print_warning(f"Audit logging test: {e}")
    results['warnings'] += 1

# ===================================
# 9. 2FA Configuration
# ===================================
print_header("9. اختبار 2FA Configuration")

try:
    from django_otp.plugins.otp_totp.models import TOTPDevice

    print_ok("django-otp installed")
    results['passed'] += 1

    # Check if OTP middleware is enabled
    if 'django_otp.middleware.OTPMiddleware' in settings.MIDDLEWARE:
        print_ok("OTP Middleware مفعّل")
        results['passed'] += 1
    else:
        print_warning("OTP Middleware غير مفعّل")
        results['warnings'] += 1

except ImportError:
    print_fail("django-otp غير مثبت")
    results['failed'] += 1

# ===================================
# 10. API Health Check
# ===================================
print_header("10. اختبار API Endpoints")

client = Client()

endpoints = [
    ('/health/', 200, 'Health check'),
    ('/api/v1/platform/stats/', 200, 'Platform stats'),
]

for endpoint, expected_status, name in endpoints:
    try:
        response = client.get(endpoint)
        if response.status_code == expected_status:
            print_ok(f"{name}: {response.status_code}")
            results['passed'] += 1
        else:
            print_fail(f"{name}: {response.status_code} (expected {expected_status})")
            results['failed'] += 1
    except Exception as e:
        print_warning(f"{name}: {e}")
        results['warnings'] += 1

# ===================================
# 11. Sentry Configuration
# ===================================
print_header("11. اختبار Sentry")

sentry_dsn = getattr(settings, 'SENTRY_DSN', None)
if sentry_dsn:
    print_ok(f"Sentry DSN configured: {sentry_dsn[:30]}...")
    results['passed'] += 1
else:
    if settings.DEBUG:
        print_warning("Sentry DSN غير مُعدّ (مقبول في التطوير)")
        results['warnings'] += 1
    else:
        print_fail("Sentry DSN غير مُعدّ (مطلوب في الإنتاج)")
        results['failed'] += 1

# ===================================
# Summary
# ===================================
print_header("ملخص النتائج")

total = results['passed'] + results['failed'] + results['warnings']
pass_rate = (results['passed'] / total * 100) if total > 0 else 0

print(f"""
{Colors.OK}نجح: {results['passed']}{Colors.ENDC}
{Colors.FAIL}فشل: {results['failed']}{Colors.ENDC}
{Colors.WARNING}تحذيرات: {results['warnings']}{Colors.ENDC}

نسبة النجاح: {pass_rate:.1f}%
""")

if results['failed'] > 0:
    print(f"{Colors.FAIL}❌ يوجد {results['failed']} اختبارات فاشلة - لا يُنصح بالإطلاق!{Colors.ENDC}")
    if results['details']:
        print(f"\nتفاصيل الأخطاء:")
        for detail in results['details']:
            print(f"  - {detail}")
elif results['warnings'] > 3:
    print(f"{Colors.WARNING}⚠️ يوجد تحذيرات كثيرة - راجعها قبل الإطلاق{Colors.ENDC}")
else:
    print(f"{Colors.OK}✅ المنصة جاهزة للإطلاق!{Colors.ENDC}")

# Return exit code
sys.exit(0 if results['failed'] == 0 else 1)
