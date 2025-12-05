"""
===================================
منصة ديواني - URL Configuration
===================================
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from ninja import NinjaAPI
from ninja_jwt.controller import NinjaJWTDefaultController
from ninja_extra import NinjaExtraAPI

# ===================================
# Import Routers
# ===================================
from apps.accounts.api import router as accounts_router
from apps.stores.api import router as stores_router
from apps.products.api import router as products_router
from apps.orders.api import router as orders_router
from apps.payments.api import router as payments_router
from apps.notifications.api import router as notifications_router
from apps.delivery.api import router as delivery_router

# ===================================
# API Configuration
# ===================================
api = NinjaExtraAPI(
    title='Diwani API - منصة ديواني',
    version='1.0.0',
    description='''
    # 🏗️ منصة ديواني لمواد البناء

    منصة سعودية متكاملة للتجارة الإلكترونية في مواد البناء

    ## 📦 الميزات الرئيسية:
    - 👤 المصادقة والمستخدمين (OTP، JWT)
    - 🏪 إدارة المتاجر والموردين
    - 📦 المنتجات والمخزون
    - 🛒 سلة التسوق والطلبات
    - 💳 بوابات الدفع (مدى، Apple Pay)
    - 🚚 التوصيل والتتبع اللحظي
    - ⭐ التقييمات والمراجعات
    - 🔔 الإشعارات الفورية

    ## 🔐 المصادقة:
    استخدم JWT Bearer Token في header:
    ```
    Authorization: Bearer <your_token>
    ```

    ## 📍 التغطية الجغرافية:
    - جميع المناطق السعودية
    - الرياض، جدة، الدمام، مكة، المدينة...

    ---
    **الإصدار:** 1.0.0 | **التاريخ:** 2024
    ''',
    urls_namespace='api',
)

# ===================================
# Register Controllers & Routers
# ===================================
# JWT Authentication Controller
api.register_controllers(NinjaJWTDefaultController)

# Register API Routers
api.add_router('/accounts', accounts_router, tags=['المستخدمين والمصادقة'])
api.add_router('/stores', stores_router, tags=['المتاجر'])
api.add_router('/products', products_router, tags=['المنتجات'])
api.add_router('/orders', orders_router, tags=['السلة والطلبات'])
api.add_router('/payments', payments_router, tags=['المدفوعات'])
api.add_router('/notifications', notifications_router, tags=['الإشعارات'])
api.add_router('/delivery', delivery_router, tags=['التوصيل'])

# ===================================
# URL Patterns
# ===================================
urlpatterns = [
    # Admin Panel
    path('admin/', admin.site.urls),

    # API v1 - Main API with all routers
    path('api/v1/', api.urls),

    # Health Check
    path('api/health/', include('apps.core.urls')),
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
