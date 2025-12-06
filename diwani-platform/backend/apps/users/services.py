"""
خدمات نظام المستخدمين
=====================

خدمات المصادقة وإدارة المستخدمين
"""

import hashlib
import secrets
from datetime import timedelta
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

import jwt

from .models import (
    User,
    UserType,
    UserStatus,
    OTPCode,
    UserSession,
    UserDevice,
    UserAddress,
    VendorProfile,
    DriverProfile,
)


# =============================================
# إعدادات JWT
# =============================================

JWT_SECRET = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # ساعة
REFRESH_TOKEN_EXPIRE_DAYS = 30  # شهر


@dataclass
class TokenPair:
    """زوج الرموز"""
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = 'Bearer'


@dataclass
class AuthResult:
    """نتيجة المصادقة"""
    success: bool
    user: Optional[User] = None
    tokens: Optional[TokenPair] = None
    session: Optional[UserSession] = None
    error: Optional[str] = None
    error_code: Optional[str] = None


# =============================================
# خدمة OTP
# =============================================

class OTPService:
    """خدمة رموز التحقق"""

    # Rate limiting
    MAX_OTP_PER_HOUR = 5
    OTP_COOLDOWN_SECONDS = 60

    def send_otp(
        self,
        phone_number: str,
        purpose: str = 'login',
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        إرسال رمز التحقق

        Returns:
            (success, message or error)
        """
        # تطبيع رقم الهاتف
        phone_number = self._normalize_phone(phone_number)

        # التحقق من Rate Limiting
        if not self._check_rate_limit(phone_number):
            return False, 'تم تجاوز الحد الأقصى للمحاولات. حاول بعد ساعة'

        # التحقق من Cooldown
        last_otp = OTPCode.objects.filter(
            phone_number=phone_number,
            purpose=purpose,
            created_at__gte=timezone.now() - timedelta(seconds=self.OTP_COOLDOWN_SECONDS)
        ).first()

        if last_otp:
            remaining = self.OTP_COOLDOWN_SECONDS - (timezone.now() - last_otp.created_at).seconds
            return False, f'انتظر {remaining} ثانية قبل طلب رمز جديد'

        # توليد وحفظ الرمز
        code = OTPCode.generate_code()

        OTPCode.objects.create(
            phone_number=phone_number,
            code=code,
            purpose=purpose,
            ip_address=ip_address,
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        # إرسال SMS
        self._send_sms(phone_number, code, purpose)

        # تحديث Rate Limiting
        self._increment_rate_limit(phone_number)

        return True, 'تم إرسال رمز التحقق بنجاح'

    def verify_otp(
        self,
        phone_number: str,
        code: str,
        purpose: str = 'login'
    ) -> Tuple[bool, str]:
        """
        التحقق من الرمز

        Returns:
            (success, message or error)
        """
        phone_number = self._normalize_phone(phone_number)

        # البحث عن آخر رمز صالح
        otp = OTPCode.objects.filter(
            phone_number=phone_number,
            purpose=purpose,
            is_used=False,
        ).order_by('-created_at').first()

        if not otp:
            return False, 'لم يتم العثور على رمز تحقق'

        if otp.is_expired:
            return False, 'انتهت صلاحية الرمز'

        if otp.attempts >= otp.max_attempts:
            return False, 'تم تجاوز الحد الأقصى للمحاولات'

        if otp.verify(code):
            return True, 'تم التحقق بنجاح'

        remaining = otp.max_attempts - otp.attempts
        return False, f'رمز خاطئ. متبقي {remaining} محاولات'

    def _normalize_phone(self, phone: str) -> str:
        """تطبيع رقم الهاتف"""
        phone = phone.replace(' ', '').replace('-', '')
        if phone.startswith('05'):
            phone = '+966' + phone[1:]
        elif phone.startswith('5'):
            phone = '+966' + phone
        return phone

    def _check_rate_limit(self, phone_number: str) -> bool:
        """التحقق من Rate Limiting"""
        key = f'otp_rate:{phone_number}'
        count = cache.get(key, 0)
        return count < self.MAX_OTP_PER_HOUR

    def _increment_rate_limit(self, phone_number: str):
        """زيادة عداد Rate Limiting"""
        key = f'otp_rate:{phone_number}'
        count = cache.get(key, 0)
        cache.set(key, count + 1, timeout=3600)  # ساعة

    def _send_sms(self, phone_number: str, code: str, purpose: str):
        """
        إرسال SMS

        في الإنتاج، استخدم مزود SMS مثل Unifonic أو Twilio
        """
        message = f'رمز التحقق الخاص بك في ديواني: {code}'

        # TODO: تكامل مع مزود SMS
        # مثال:
        # sms_provider.send(
        #     to=phone_number,
        #     message=message,
        #     sender='DIWANI'
        # )

        # للتطوير
        if settings.DEBUG:
            print(f'[OTP] {phone_number}: {code}')


# =============================================
# خدمة المصادقة
# =============================================

class AuthService:
    """خدمة المصادقة الرئيسية"""

    def __init__(self):
        self.otp_service = OTPService()

    def login_with_phone(
        self,
        phone_number: str,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        بدء تسجيل الدخول بالهاتف

        يرسل OTP ويعيد رسالة
        """
        return self.otp_service.send_otp(
            phone_number=phone_number,
            purpose='login',
            ip_address=ip_address
        )

    def verify_and_login(
        self,
        phone_number: str,
        code: str,
        device_info: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AuthResult:
        """
        التحقق من OTP وتسجيل الدخول

        يُنشئ مستخدم جديد إذا لم يكن موجوداً
        """
        # التحقق من OTP
        success, message = self.otp_service.verify_otp(
            phone_number=phone_number,
            code=code,
            purpose='login'
        )

        if not success:
            return AuthResult(success=False, error=message)

        # تطبيع الهاتف
        phone_number = self.otp_service._normalize_phone(phone_number)

        # البحث عن المستخدم أو إنشاء جديد
        user, created = User.objects.get_or_create(
            phone_number=phone_number,
            defaults={
                'phone_verified': True,
                'is_verified': True,
            }
        )

        if not created:
            user.phone_verified = True
            user.last_login_at = timezone.now()
            user.save(update_fields=['phone_verified', 'last_login_at'])

        # التحقق من الحالة
        if user.status == UserStatus.BANNED:
            return AuthResult(
                success=False,
                error='تم حظر هذا الحساب',
                error_code='account_banned'
            )

        if user.status == UserStatus.SUSPENDED:
            return AuthResult(
                success=False,
                error='تم تعليق هذا الحساب مؤقتاً',
                error_code='account_suspended'
            )

        # تسجيل الجهاز
        device = None
        if device_info:
            device = self._register_device(user, device_info, ip_address)

        # إنشاء الجلسة والرموز
        tokens, session = self._create_session(user, device, ip_address)

        return AuthResult(
            success=True,
            user=user,
            tokens=tokens,
            session=session
        )

    def register_customer(
        self,
        phone_number: str,
        code: str,
        first_name: str,
        last_name: str,
        email: Optional[str] = None,
        referral_code: Optional[str] = None,
        device_info: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AuthResult:
        """تسجيل عميل جديد"""

        # التحقق من OTP
        success, message = self.otp_service.verify_otp(
            phone_number=phone_number,
            code=code,
            purpose='register'
        )

        if not success:
            return AuthResult(success=False, error=message)

        phone_number = self.otp_service._normalize_phone(phone_number)

        # التحقق من عدم وجود المستخدم
        if User.objects.filter(phone_number=phone_number).exists():
            return AuthResult(
                success=False,
                error='رقم الهاتف مسجل مسبقاً',
                error_code='phone_exists'
            )

        if email and User.objects.filter(email=email).exists():
            return AuthResult(
                success=False,
                error='البريد الإلكتروني مسجل مسبقاً',
                error_code='email_exists'
            )

        # البحث عن المُحيل
        referred_by = None
        if referral_code:
            referred_by = User.objects.filter(referral_code=referral_code).first()

        with transaction.atomic():
            # إنشاء المستخدم
            user = User.objects.create(
                phone_number=phone_number,
                first_name=first_name,
                last_name=last_name,
                email=email,
                user_type=UserType.CUSTOMER,
                phone_verified=True,
                is_verified=True,
                referred_by=referred_by,
            )

            # مكافأة الإحالة
            if referred_by:
                self._process_referral_bonus(referred_by, user)

        # تسجيل الجهاز
        device = None
        if device_info:
            device = self._register_device(user, device_info, ip_address)

        # إنشاء الجلسة
        tokens, session = self._create_session(user, device, ip_address)

        return AuthResult(
            success=True,
            user=user,
            tokens=tokens,
            session=session
        )

    def register_vendor(
        self,
        phone_number: str,
        code: str,
        first_name: str,
        last_name: str,
        email: str,
        company_name: str,
        company_name_en: Optional[str] = None,
        commercial_register: Optional[str] = None,
        tax_number: Optional[str] = None,
        business_type: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> AuthResult:
        """تسجيل تاجر جديد"""

        # التحقق من OTP
        success, message = self.otp_service.verify_otp(
            phone_number=phone_number,
            code=code,
            purpose='register'
        )

        if not success:
            return AuthResult(success=False, error=message)

        phone_number = self.otp_service._normalize_phone(phone_number)

        # التحقق من عدم وجود المستخدم
        if User.objects.filter(phone_number=phone_number).exists():
            return AuthResult(
                success=False,
                error='رقم الهاتف مسجل مسبقاً',
                error_code='phone_exists'
            )

        with transaction.atomic():
            # إنشاء المستخدم
            user = User.objects.create(
                phone_number=phone_number,
                first_name=first_name,
                last_name=last_name,
                email=email,
                user_type=UserType.VENDOR,
                status=UserStatus.PENDING,  # يحتاج مراجعة
                phone_verified=True,
            )

            # إنشاء ملف التاجر
            VendorProfile.objects.create(
                user=user,
                company_name=company_name,
                company_name_en=company_name_en or '',
                commercial_register=commercial_register or '',
                tax_number=tax_number or '',
                business_type=business_type or '',
            )

        # إنشاء الجلسة
        tokens, session = self._create_session(user, None, ip_address)

        return AuthResult(
            success=True,
            user=user,
            tokens=tokens,
            session=session
        )

    def refresh_tokens(
        self,
        refresh_token: str,
        ip_address: Optional[str] = None
    ) -> AuthResult:
        """تحديث الرموز"""
        try:
            # فك الرمز
            payload = jwt.decode(
                refresh_token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM]
            )

            if payload.get('type') != 'refresh':
                return AuthResult(
                    success=False,
                    error='رمز غير صالح',
                    error_code='invalid_token'
                )

            user_id = payload.get('user_id')
            session_id = payload.get('session_id')

            # التحقق من الجلسة
            session = UserSession.objects.filter(
                id=session_id,
                user_id=user_id,
                is_active=True
            ).first()

            if not session:
                return AuthResult(
                    success=False,
                    error='الجلسة غير موجودة أو منتهية',
                    error_code='session_invalid'
                )

            # التحقق من صلاحية رمز التحديث
            token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            if session.refresh_token_hash != token_hash:
                return AuthResult(
                    success=False,
                    error='رمز التحديث غير صالح',
                    error_code='refresh_token_invalid'
                )

            user = session.user

            # التحقق من حالة المستخدم
            if user.status in [UserStatus.BANNED, UserStatus.SUSPENDED]:
                session.revoke()
                return AuthResult(
                    success=False,
                    error='الحساب موقوف',
                    error_code='account_inactive'
                )

            # إنشاء رموز جديدة
            tokens = self._generate_tokens(user, session)

            # تحديث الجلسة
            session.token_hash = hashlib.sha256(tokens.access_token.encode()).hexdigest()
            session.refresh_token_hash = hashlib.sha256(tokens.refresh_token.encode()).hexdigest()
            session.expires_at = timezone.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            session.refresh_expires_at = timezone.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            session.ip_address = ip_address
            session.save()

            return AuthResult(
                success=True,
                user=user,
                tokens=tokens,
                session=session
            )

        except jwt.ExpiredSignatureError:
            return AuthResult(
                success=False,
                error='انتهت صلاحية الرمز',
                error_code='token_expired'
            )
        except jwt.InvalidTokenError:
            return AuthResult(
                success=False,
                error='رمز غير صالح',
                error_code='invalid_token'
            )

    def logout(
        self,
        user: User,
        session_id: Optional[str] = None,
        all_devices: bool = False
    ) -> bool:
        """تسجيل الخروج"""
        if all_devices:
            # إلغاء جميع الجلسات
            UserSession.objects.filter(user=user, is_active=True).update(
                is_active=False,
                revoked_at=timezone.now()
            )
        elif session_id:
            # إلغاء جلسة محددة
            UserSession.objects.filter(
                id=session_id,
                user=user,
                is_active=True
            ).update(
                is_active=False,
                revoked_at=timezone.now()
            )

        return True

    def verify_token(self, token: str) -> Optional[User]:
        """التحقق من رمز الوصول"""
        try:
            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM]
            )

            if payload.get('type') != 'access':
                return None

            user_id = payload.get('user_id')
            session_id = payload.get('session_id')

            # التحقق من الجلسة
            session = UserSession.objects.filter(
                id=session_id,
                user_id=user_id,
                is_active=True
            ).select_related('user').first()

            if not session:
                return None

            # التحقق من صلاحية الرمز
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            if session.token_hash != token_hash:
                return None

            user = session.user

            # التحقق من حالة المستخدم
            if user.status in [UserStatus.BANNED, UserStatus.SUSPENDED]:
                return None

            # تحديث آخر نشاط
            session.save()  # يحدث last_activity تلقائياً

            return user

        except jwt.InvalidTokenError:
            return None

    def _create_session(
        self,
        user: User,
        device: Optional[UserDevice] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[TokenPair, UserSession]:
        """إنشاء جلسة جديدة"""

        # إنشاء الجلسة
        session = UserSession.objects.create(
            user=user,
            device=device,
            token_hash='',  # سيُحدث بعد توليد الرموز
            expires_at=timezone.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            refresh_expires_at=timezone.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            ip_address=ip_address,
        )

        # توليد الرموز
        tokens = self._generate_tokens(user, session)

        # تحديث هاشات الرموز
        session.token_hash = hashlib.sha256(tokens.access_token.encode()).hexdigest()
        session.refresh_token_hash = hashlib.sha256(tokens.refresh_token.encode()).hexdigest()
        session.save(update_fields=['token_hash', 'refresh_token_hash'])

        return tokens, session

    def _generate_tokens(self, user: User, session: UserSession) -> TokenPair:
        """توليد رموز JWT"""
        now = timezone.now()

        # Access Token
        access_payload = {
            'user_id': str(user.id),
            'session_id': str(session.id),
            'type': 'access',
            'user_type': user.user_type,
            'iat': now.timestamp(),
            'exp': (now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp(),
        }
        access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        # Refresh Token
        refresh_payload = {
            'user_id': str(user.id),
            'session_id': str(session.id),
            'type': 'refresh',
            'iat': now.timestamp(),
            'exp': (now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).timestamp(),
        }
        refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )

    def _register_device(
        self,
        user: User,
        device_info: Dict[str, Any],
        ip_address: Optional[str] = None
    ) -> UserDevice:
        """تسجيل جهاز"""
        device_id = device_info.get('device_id', '')

        device, created = UserDevice.objects.update_or_create(
            user=user,
            device_id=device_id,
            defaults={
                'device_name': device_info.get('device_name', ''),
                'platform': device_info.get('platform', 'web'),
                'os_version': device_info.get('os_version', ''),
                'app_version': device_info.get('app_version', ''),
                'push_token': device_info.get('push_token', ''),
                'ip_address': ip_address,
                'is_active': True,
            }
        )

        return device

    def _process_referral_bonus(self, referrer: User, new_user: User):
        """معالجة مكافأة الإحالة"""
        # إضافة نقاط للمُحيل
        bonus_points = 100  # يمكن جعلها قابلة للتكوين
        referrer.loyalty_points += bonus_points
        referrer.save(update_fields=['loyalty_points'])

        # TODO: إرسال إشعار للمُحيل


# =============================================
# خدمة المستخدمين
# =============================================

class UserService:
    """خدمة إدارة المستخدمين"""

    def update_profile(
        self,
        user: User,
        data: Dict[str, Any]
    ) -> User:
        """تحديث الملف الشخصي"""
        allowed_fields = [
            'first_name', 'last_name', 'display_name',
            'email', 'gender', 'date_of_birth',
            'language', 'timezone'
        ]

        for field in allowed_fields:
            if field in data and data[field] is not None:
                setattr(user, field, data[field])

        user.save()
        return user

    def add_address(self, user: User, data: Dict[str, Any]) -> UserAddress:
        """إضافة عنوان"""
        address = UserAddress.objects.create(user=user, **data)
        return address

    def update_address(
        self,
        user: User,
        address_id: str,
        data: Dict[str, Any]
    ) -> Optional[UserAddress]:
        """تحديث عنوان"""
        try:
            address = UserAddress.objects.get(id=address_id, user=user)
            for field, value in data.items():
                if value is not None:
                    setattr(address, field, value)
            address.save()
            return address
        except UserAddress.DoesNotExist:
            return None

    def delete_address(self, user: User, address_id: str) -> bool:
        """حذف عنوان"""
        deleted, _ = UserAddress.objects.filter(id=address_id, user=user).delete()
        return deleted > 0

    def get_user_stats(self, user: User) -> Dict[str, Any]:
        """إحصائيات المستخدم"""
        return {
            'orders_count': user.orders_count,
            'total_spent': float(user.total_spent),
            'rating': float(user.rating),
            'ratings_count': user.ratings_count,
            'loyalty_points': user.loyalty_points,
            'loyalty_tier': user.loyalty_tier,
            'referrals_count': user.referrals.count(),
            'member_since': user.created_at.isoformat(),
        }


# =============================================
# Singletons
# =============================================

otp_service = OTPService()
auth_service = AuthService()
user_service = UserService()
