"""
===================================
منصة ديواني - URL Configuration
===================================
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from ninja_extra import NinjaExtraAPI

# ===================================
# API Configuration
# ===================================
api = NinjaExtraAPI(
    title='Diwani API - منصة ديواني',
    version='2.0.0',
    description='''
    # 🏗️ منصة ديواني لمواد البناء

    منصة سعودية متكاملة للتجارة الإلكترونية في مواد البناء والخدمات اللوجستية

    ## 📦 الميزات الرئيسية:
    - 👤 المصادقة والمستخدمين (OTP، JWT)
    - 🏪 إدارة المتاجر والموردين
    - 📦 المنتجات (مخزون + حسب الطلب)
    - 🛒 سلة التسوق والطلبات
    - 💳 المدفوعات (Tap Connect)
    - 🚚 التوصيل والتتبع اللحظي
    - 💰 النظام المالي والتسوية
    - 🔍 البحث المتقدم (Elasticsearch)
    - 💬 المحادثات (WebSocket)
    - 🔔 الإشعارات الفورية

    ## 🔐 المصادقة:
    استخدم JWT Bearer Token في header:
    ```
    Authorization: Bearer <your_token>
    ```

    ## 💰 التسعير المرن:
    يدعم النظام أنواع تسعير متعددة:
    - سعر ثابت، بالساعة، باليوم
    - بالكيلومتر، بالوزن، بالحجم
    - متدرج (خصومات الكميات)
    - حسب العرض، مجاني

    ## 📍 التغطية الجغرافية:
    جميع المناطق السعودية

    ---
    **الإصدار:** 2.0.0 | **التاريخ:** 2025
    ''',
    urls_namespace='api',
)

# ===================================
# Register API Routers
# ===================================

# Users API - المصادقة والمستخدمين
from apps.users.api import router as users_router
api.add_router('/users', users_router, tags=['المستخدمين'])

# Products API - المنتجات والأقسام
from apps.products.api import router as products_router
api.add_router('/products', products_router, tags=['المنتجات'])

# Stores API - المتاجر والبائعين
from apps.stores.api import router as stores_router
api.add_router('/stores', stores_router, tags=['المتاجر'])

# Orders API - الطلبات والتوصيل
from apps.orders.api import router as orders_router
api.add_router('/orders', orders_router, tags=['الطلبات'])

# Finance API - النظام المالي
from apps.finance.api import router as finance_router
api.add_router('/finance', finance_router, tags=['المالية'])

# Search API - البحث المتقدم
from apps.search.api import router as search_router
api.add_router('/search', search_router, tags=['البحث'])

# ===================================
# URL Patterns
# ===================================
urlpatterns = [
    # Admin Panel - لوحة التحكم
    path('admin/', admin.site.urls),

    # API v1 - واجهة برمجة التطبيقات
    path('api/v1/', api.urls),

    # Finance Webhooks - استقبال أحداث Tap والمحاسبة
    path('webhooks/', include('apps.finance.urls')),

    # Health Check - فحص الحالة
    path('health/', lambda r: __import__('django.http', fromlist=['JsonResponse']).JsonResponse({
        'status': 'healthy',
        'version': '2.0.0',
        'platform': 'Diwani'
    })),
]

# ===================================
# Development URLs
# ===================================
if settings.DEBUG:
    # Static & Media files
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Debug Toolbar
    try:
        import debug_toolbar
        urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
    except ImportError:
        pass

    # Silk Profiler
    try:
        urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]
    except ImportError:
        pass

# ===================================
# Admin Customization
# ===================================
admin.site.site_header = 'لوحة تحكم ديواني'
admin.site.site_title = 'ديواني'
admin.site.index_title = 'مرحباً بك في لوحة التحكم'
