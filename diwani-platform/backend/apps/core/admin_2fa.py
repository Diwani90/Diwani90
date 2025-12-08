"""
===================================
منصة ديواني - Admin 2FA Configuration
المصادقة الثنائية للوحة التحكم
===================================

يستخدم TOTP (Time-based One-Time Password)
متوافق مع:
- Google Authenticator
- Microsoft Authenticator
- Authy
- أي تطبيق TOTP
"""

import logging
from functools import wraps

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin import AdminSite
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import path, reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect

try:
    from django_otp import devices_for_user, user_has_device
    from django_otp.admin import OTPAdminSite
    from django_otp.decorators import otp_required
    from django_otp.plugins.otp_totp.models import TOTPDevice
    OTP_AVAILABLE = True
except ImportError:
    OTP_AVAILABLE = False
    OTPAdminSite = AdminSite

logger = logging.getLogger(__name__)


class Diwani2FAAdminSite(OTPAdminSite if OTP_AVAILABLE else AdminSite):
    """
    لوحة تحكم ديواني مع 2FA

    الميزات:
    - إجبار 2FA لجميع المدراء في الإنتاج
    - QR Code للإعداد السهل
    - Backup codes
    - Audit logging
    """

    site_header = 'لوحة تحكم ديواني 🔐'
    site_title = 'ديواني'
    index_title = 'مرحباً بك في لوحة التحكم المؤمّنة'

    # إعدادات 2FA
    REQUIRE_2FA_IN_PRODUCTION = True
    GRACE_PERIOD_DAYS = 7  # فترة سماح لإعداد 2FA

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._registry = {}

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path('2fa/setup/', self.admin_view(self.setup_2fa_view), name='setup_2fa'),
            path('2fa/verify/', self.admin_view(self.verify_2fa_view), name='verify_2fa'),
            path('2fa/disable/', self.admin_view(self.disable_2fa_view), name='disable_2fa'),
            path('2fa/backup-codes/', self.admin_view(self.backup_codes_view), name='backup_codes'),
        ]

        return custom_urls + urls

    def has_permission(self, request):
        """التحقق من الصلاحيات مع 2FA"""
        if not super().has_permission(request):
            return False

        # في وضع التطوير، نتجاوز 2FA
        if settings.DEBUG and not getattr(settings, 'FORCE_2FA_DEBUG', False):
            return True

        # التحقق من 2FA في الإنتاج
        if OTP_AVAILABLE and self.REQUIRE_2FA_IN_PRODUCTION:
            user = request.user

            # التحقق من أن المستخدم مُوثَّق بـ 2FA
            if hasattr(request, 'user') and request.user.is_authenticated:
                if not user_has_device(user):
                    # المستخدم ليس لديه جهاز 2FA - السماح فقط لصفحة الإعداد
                    if not self._is_setup_page(request):
                        return False

        return True

    def _is_setup_page(self, request):
        """التحقق إذا كانت الصفحة هي صفحة إعداد 2FA"""
        return request.path.endswith('/2fa/setup/')

    @method_decorator(never_cache)
    def setup_2fa_view(self, request):
        """صفحة إعداد 2FA"""
        if not OTP_AVAILABLE:
            messages.error(request, 'المصادقة الثنائية غير متوفرة')
            return redirect('admin:index')

        user = request.user

        if request.method == 'POST':
            # إنشاء جهاز TOTP جديد
            device, created = TOTPDevice.objects.get_or_create(
                user=user,
                name='Diwani Admin TOTP',
                defaults={'confirmed': False}
            )

            if created or not device.confirmed:
                # توليد مفتاح جديد
                device.key = TOTPDevice.random_key()
                device.save()

            # توليد QR Code
            qr_url = device.config_url

            return render(request, 'admin/2fa/setup.html', {
                'qr_url': qr_url,
                'secret_key': device.key,
                'device': device,
            })

        # التحقق إذا كان لديه جهاز مفعّل
        devices = list(devices_for_user(user))
        confirmed_devices = [d for d in devices if getattr(d, 'confirmed', True)]

        return render(request, 'admin/2fa/setup.html', {
            'has_2fa': len(confirmed_devices) > 0,
            'devices': confirmed_devices,
        })

    @method_decorator(never_cache)
    def verify_2fa_view(self, request):
        """التحقق من رمز 2FA"""
        if not OTP_AVAILABLE:
            return redirect('admin:index')

        user = request.user

        if request.method == 'POST':
            token = request.POST.get('token', '')

            # البحث عن جهاز غير مؤكد
            device = TOTPDevice.objects.filter(
                user=user,
                confirmed=False
            ).first()

            if device and device.verify_token(token):
                device.confirmed = True
                device.save()

                # تسجيل في Audit log
                logger.info(f"2FA enabled for admin user: {user.username}")

                messages.success(request, '✅ تم تفعيل المصادقة الثنائية بنجاح!')
                return redirect('admin:index')
            else:
                messages.error(request, '❌ الرمز غير صحيح. حاول مرة أخرى.')

        return render(request, 'admin/2fa/verify.html')

    @method_decorator(never_cache)
    def disable_2fa_view(self, request):
        """تعطيل 2FA"""
        if not OTP_AVAILABLE:
            return redirect('admin:index')

        user = request.user

        if request.method == 'POST':
            # التحقق من كلمة المرور
            password = request.POST.get('password', '')

            if user.check_password(password):
                # حذف جميع أجهزة TOTP
                TOTPDevice.objects.filter(user=user).delete()

                logger.warning(f"2FA disabled for admin user: {user.username}")
                messages.warning(request, '⚠️ تم تعطيل المصادقة الثنائية')
                return redirect('admin:index')
            else:
                messages.error(request, '❌ كلمة المرور غير صحيحة')

        return render(request, 'admin/2fa/disable.html')

    @method_decorator(never_cache)
    def backup_codes_view(self, request):
        """توليد رموز احتياطية"""
        if not OTP_AVAILABLE:
            return redirect('admin:index')

        # توليد رموز احتياطية جديدة
        import secrets
        backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]

        # حفظ في الجلسة للعرض مرة واحدة
        request.session['backup_codes'] = backup_codes

        return render(request, 'admin/2fa/backup_codes.html', {
            'backup_codes': backup_codes,
        })

    def login(self, request, extra_context=None):
        """تخصيص صفحة الدخول"""
        extra_context = extra_context or {}
        extra_context['site_header'] = self.site_header
        extra_context['has_2fa'] = OTP_AVAILABLE

        return super().login(request, extra_context)


# إنشاء موقع Admin مع 2FA
admin_2fa_site = Diwani2FAAdminSite(name='admin_2fa')


def setup_2fa_admin():
    """
    إعداد 2FA في الـ Admin الافتراضي

    يُستدعى في apps.py أو settings
    """
    if not OTP_AVAILABLE:
        logger.warning("django-otp not available, 2FA disabled for admin")
        return

    # تخصيص الـ Admin الافتراضي
    admin.site.site_header = 'لوحة تحكم ديواني 🔐'
    admin.site.site_title = 'ديواني'
    admin.site.index_title = 'مرحباً بك في لوحة التحكم'

    # إضافة نموذج TOTP للـ Admin
    from django_otp.admin import OTPAdminSite
    from django_otp.plugins.otp_totp.admin import TOTPDeviceAdmin
    from django_otp.plugins.otp_totp.models import TOTPDevice

    # تسجيل TOTP في Admin
    if not admin.site.is_registered(TOTPDevice):
        admin.site.register(TOTPDevice, TOTPDeviceAdmin)

    logger.info("2FA configured for Django admin")


# Decorator للتحقق من 2FA
def require_2fa(view_func):
    """
    Decorator للتأكد من أن المستخدم لديه 2FA مفعّل

    الاستخدام:
        @require_2fa
        def sensitive_admin_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not OTP_AVAILABLE:
            return view_func(request, *args, **kwargs)

        user = request.user

        if not user.is_authenticated:
            return redirect('admin:login')

        if not user_has_device(user):
            messages.warning(
                request,
                '⚠️ يجب تفعيل المصادقة الثنائية للوصول لهذه الصفحة'
            )
            return redirect('admin:setup_2fa')

        return view_func(request, *args, **kwargs)

    return wrapper
