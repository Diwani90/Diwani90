"""
اختبارات تطبيق المستخدمين
=========================
"""

import pytest
from decimal import Decimal
from django.test import TestCase
from django.utils import timezone

from apps.users.models import User, UserType, OTPCode
from apps.users.services import OTPService, AuthService


# =============================================
# User Model Tests
# =============================================

@pytest.mark.django_db
class TestUserModel:
    """اختبارات نموذج المستخدم"""

    def test_create_customer_user(self):
        """اختبار إنشاء مستخدم عميل"""
        user = User.objects.create_user(
            phone_number='+966501111111',
            password='testpass123',
            first_name='أحمد',
            last_name='محمد',
            user_type=UserType.CUSTOMER,
        )

        assert user.id is not None
        assert user.phone_number == '+966501111111'
        assert user.user_type == UserType.CUSTOMER
        assert user.check_password('testpass123')
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_vendor_user(self):
        """اختبار إنشاء مستخدم تاجر"""
        user = User.objects.create_user(
            phone_number='+966502222222',
            password='testpass123',
            first_name='خالد',
            last_name='علي',
            user_type=UserType.VENDOR,
        )

        assert user.user_type == UserType.VENDOR

    def test_create_driver_user(self):
        """اختبار إنشاء مستخدم سائق"""
        user = User.objects.create_user(
            phone_number='+966503333333',
            password='testpass123',
            first_name='محمد',
            last_name='سالم',
            user_type=UserType.DRIVER,
        )

        assert user.user_type == UserType.DRIVER

    def test_create_superuser(self):
        """اختبار إنشاء مستخدم مدير"""
        user = User.objects.create_superuser(
            phone_number='+966500000001',
            password='adminpass123',
            first_name='مدير',
            last_name='النظام',
        )

        assert user.is_staff
        assert user.is_superuser
        assert user.user_type == UserType.ADMIN

    def test_full_name_property(self):
        """اختبار خاصية الاسم الكامل"""
        user = User.objects.create_user(
            phone_number='+966504444444',
            password='testpass123',
            first_name='عبدالله',
            last_name='الشمري',
        )

        assert user.full_name == 'عبدالله الشمري'

    def test_phone_number_unique(self):
        """اختبار عدم تكرار رقم الهاتف"""
        User.objects.create_user(
            phone_number='+966505555555',
            password='testpass123',
        )

        with pytest.raises(Exception):
            User.objects.create_user(
                phone_number='+966505555555',
                password='testpass456',
            )


# =============================================
# OTP Service Tests
# =============================================

@pytest.mark.django_db
class TestOTPService:
    """اختبارات خدمة OTP"""

    def test_generate_otp(self):
        """اختبار توليد رمز OTP"""
        otp_code, error = OTPService.generate_otp('+966506666666')

        assert otp_code is not None
        assert error is None
        assert len(otp_code.code) == 6
        assert otp_code.code.isdigit()

    def test_otp_expiry(self):
        """اختبار انتهاء صلاحية OTP"""
        otp_code, _ = OTPService.generate_otp('+966507777777')

        # التحقق من عدم انتهاء الصلاحية
        assert not otp_code.is_expired

        # تعيين وقت انتهاء في الماضي
        otp_code.expires_at = timezone.now() - timezone.timedelta(minutes=5)
        otp_code.save()

        assert otp_code.is_expired

    def test_verify_otp_success(self):
        """اختبار التحقق من OTP - نجاح"""
        otp_code, _ = OTPService.generate_otp('+966508888888')
        code = otp_code.code

        success, error = OTPService.verify_otp('+966508888888', code)

        assert success
        assert error is None

    def test_verify_otp_wrong_code(self):
        """اختبار التحقق من OTP - رمز خاطئ"""
        OTPService.generate_otp('+966509999999')

        success, error = OTPService.verify_otp('+966509999999', '000000')

        assert not success
        assert error is not None

    def test_rate_limiting(self):
        """اختبار الحد من معدل طلبات OTP"""
        phone = '+966510000000'

        # توليد عدة رموز
        for i in range(5):
            OTPService.generate_otp(phone)

        # المحاولة السادسة يجب أن تفشل
        otp_code, error = OTPService.generate_otp(phone)

        assert error is not None
        assert 'معدل' in error or 'limit' in error.lower()


# =============================================
# Auth Service Tests
# =============================================

@pytest.mark.django_db
class TestAuthService:
    """اختبارات خدمة المصادقة"""

    def test_generate_tokens(self, customer_user):
        """اختبار توليد رموز JWT"""
        tokens = AuthService.generate_tokens(customer_user)

        assert 'access_token' in tokens
        assert 'refresh_token' in tokens
        assert tokens['access_token'] is not None
        assert tokens['refresh_token'] is not None

    def test_verify_access_token(self, customer_user):
        """اختبار التحقق من رمز الوصول"""
        tokens = AuthService.generate_tokens(customer_user)

        user = AuthService.verify_token(tokens['access_token'])

        assert user is not None
        assert user.id == customer_user.id

    def test_refresh_token(self, customer_user):
        """اختبار تجديد رمز الوصول"""
        tokens = AuthService.generate_tokens(customer_user)

        new_tokens = AuthService.refresh_tokens(tokens['refresh_token'])

        assert new_tokens is not None
        assert 'access_token' in new_tokens

    def test_invalid_token(self):
        """اختبار رمز غير صالح"""
        user = AuthService.verify_token('invalid_token')

        assert user is None


# =============================================
# Registration Tests
# =============================================

@pytest.mark.django_db
class TestUserRegistration:
    """اختبارات التسجيل"""

    def test_register_customer(self):
        """اختبار تسجيل عميل جديد"""
        user, error = AuthService.register_customer(
            phone_number='+966511111111',
            first_name='سعد',
            last_name='العتيبي',
        )

        assert user is not None
        assert error is None
        assert user.user_type == UserType.CUSTOMER
        assert not user.is_phone_verified

    def test_register_vendor(self):
        """اختبار تسجيل تاجر جديد"""
        user, error = AuthService.register_vendor(
            phone_number='+966512222222',
            first_name='فهد',
            last_name='القحطاني',
            company_name='شركة البناء المتقدم',
        )

        assert user is not None
        assert error is None
        assert user.user_type == UserType.VENDOR

    def test_duplicate_phone_registration(self, customer_user):
        """اختبار التسجيل برقم مكرر"""
        user, error = AuthService.register_customer(
            phone_number=customer_user.phone_number,
            first_name='اسم',
            last_name='اختباري',
        )

        assert user is None
        assert error is not None
