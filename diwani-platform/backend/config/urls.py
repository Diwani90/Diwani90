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
# API Configuration
# ===================================
api = NinjaExtraAPI(
    title='Diwani API',
    version='1.0.0',
    description='''
    🚀 منصة ديواني - API Documentation

    منصة متكاملة للتجارة الإلكترونية والتوصيل

    ## الميزات:
    - 🛒 إدارة المتاجر والمنتجات
    - 📦 نظام الطلبات
    - 🚚 التوصيل والتتبع اللحظي
    - 💳 بوابات الدفع
    - 🔔 الإشعارات
    ''',
    urls_namespace='api',
)

# Register JWT Controller
api.register_controllers(NinjaJWTDefaultController)

# ===================================
# URL Patterns
# ===================================
urlpatterns = [
    # Admin Panel
    path('admin/', admin.site.urls),

    # API v1
    path('api/', api.urls),

    # Health Check
    path('api/health/', include('apps.core.urls')),

    # App-specific APIs
    path('api/v1/accounts/', include('apps.accounts.urls')),
    path('api/v1/stores/', include('apps.stores.urls')),
    path('api/v1/products/', include('apps.products.urls')),
    path('api/v1/orders/', include('apps.orders.urls')),
    path('api/v1/delivery/', include('apps.delivery.urls')),
    path('api/v1/payments/', include('apps.payments.urls')),
    path('api/v1/notifications/', include('apps.notifications.urls')),
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
