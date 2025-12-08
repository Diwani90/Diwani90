"""
Schemas نظام المستخدمين
======================

Django Ninja Schemas للمصادقة وإدارة المستخدمين
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from ninja import Schema, Field
from pydantic import EmailStr, validator


# =============================================
# المصادقة - Authentication
# =============================================

class PhoneLoginRequestSchema(Schema):
    """طلب تسجيل دخول بالهاتف"""
    phone_number: str = Field(..., description='رقم الهاتف السعودي')

    @validator('phone_number')
    def validate_phone(cls, v):
        import re
        v = v.replace(' ', '').replace('-', '')
        if not re.match(r'^(\+966|05|5)\d{8}$', v):
            raise ValueError('رقم الهاتف يجب أن يكون سعودي صحيح')
        return v


class OTPVerifyRequestSchema(Schema):
    """طلب التحقق من OTP"""
    phone_number: str
    code: str = Field(..., min_length=6, max_length=6)
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    platform: Optional[str] = 'web'
    push_token: Optional[str] = None


class TokenResponseSchema(Schema):
    """استجابة الرموز"""
    access_token: str
    refresh_token: str
    token_type: str = 'Bearer'
    expires_in: int
    user: 'UserBasicSchema'


class RefreshTokenRequestSchema(Schema):
    """طلب تحديث الرمز"""
    refresh_token: str


class LogoutRequestSchema(Schema):
    """طلب تسجيل الخروج"""
    all_devices: bool = False


# =============================================
# المستخدم - User
# =============================================

class UserBasicSchema(Schema):
    """معلومات المستخدم الأساسية"""
    id: UUID
    phone_number: str
    email: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    display_name: Optional[str]
    avatar_url: Optional[str]
    user_type: str
    is_verified: bool

    @staticmethod
    def resolve_avatar_url(obj):
        if obj.avatar:
            return obj.avatar.url
        return obj.avatar_url


class UserSchema(Schema):
    """معلومات المستخدم الكاملة"""
    id: UUID
    phone_number: str
    email: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    display_name: Optional[str]
    avatar_url: Optional[str]
    gender: Optional[str]
    date_of_birth: Optional[date]

    user_type: str
    status: str
    is_verified: bool
    phone_verified: bool
    email_verified: bool
    identity_verified: bool

    language: str
    timezone: str

    orders_count: int
    total_spent: Decimal
    rating: Decimal
    ratings_count: int
    loyalty_points: int
    loyalty_tier: str

    referral_code: Optional[str]

    created_at: datetime
    last_login_at: Optional[datetime]


class UserUpdateSchema(Schema):
    """تحديث بيانات المستخدم"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    language: Optional[str] = None
    timezone: Optional[str] = None


class ChangePasswordSchema(Schema):
    """تغيير كلمة المرور"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('كلمات المرور غير متطابقة')
        return v


class SetPasswordSchema(Schema):
    """تعيين كلمة مرور (للمستخدمين الجدد)"""
    password: str = Field(..., min_length=8)
    confirm_password: str


# =============================================
# التسجيل - Registration
# =============================================

class CustomerRegisterSchema(Schema):
    """تسجيل عميل جديد"""
    phone_number: str
    otp_code: str
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    email: Optional[EmailStr] = None
    referral_code: Optional[str] = None
    device_id: Optional[str] = None
    platform: Optional[str] = 'web'


class VendorRegisterSchema(Schema):
    """تسجيل تاجر جديد"""
    phone_number: str
    otp_code: str
    first_name: str
    last_name: str
    email: EmailStr
    company_name: str
    company_name_en: Optional[str] = None
    commercial_register: Optional[str] = None
    tax_number: Optional[str] = None
    business_type: Optional[str] = None


class DriverRegisterSchema(Schema):
    """تسجيل سائق جديد"""
    phone_number: str
    otp_code: str
    first_name: str
    last_name: str
    national_id: str
    license_number: str
    license_expiry: date
    vehicle_type: str
    vehicle_model: Optional[str] = None
    vehicle_plate: Optional[str] = None


# =============================================
# العناوين - Addresses
# =============================================

class AddressSchema(Schema):
    """عنوان المستخدم"""
    id: UUID
    label: Optional[str]
    address_type: str
    street_address: str
    building_number: Optional[str]
    floor: Optional[str]
    apartment: Optional[str]
    landmark: Optional[str]
    city: str
    district: Optional[str]
    region: Optional[str]
    postal_code: Optional[str]
    country: str
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]
    national_address: Optional[str]
    contact_name: Optional[str]
    contact_phone: Optional[str]
    is_default: bool
    is_verified: bool


class AddressCreateSchema(Schema):
    """إنشاء عنوان جديد"""
    label: Optional[str] = None
    address_type: str = 'home'
    street_address: str
    building_number: Optional[str] = None
    floor: Optional[str] = None
    apartment: Optional[str] = None
    landmark: Optional[str] = None
    city: str
    district: Optional[str] = None
    region: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    national_address: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    is_default: bool = False


class AddressUpdateSchema(Schema):
    """تحديث عنوان"""
    label: Optional[str] = None
    address_type: Optional[str] = None
    street_address: Optional[str] = None
    building_number: Optional[str] = None
    floor: Optional[str] = None
    apartment: Optional[str] = None
    landmark: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    region: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    national_address: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    is_default: Optional[bool] = None


# =============================================
# الأجهزة - Devices
# =============================================

class DeviceSchema(Schema):
    """جهاز المستخدم"""
    id: UUID
    device_id: str
    device_name: Optional[str]
    platform: str
    os_version: Optional[str]
    app_version: Optional[str]
    push_enabled: bool
    is_active: bool
    last_used_at: datetime
    created_at: datetime


class DeviceRegisterSchema(Schema):
    """تسجيل جهاز جديد"""
    device_id: str
    device_name: Optional[str] = None
    platform: str
    os_version: Optional[str] = None
    app_version: Optional[str] = None
    push_token: Optional[str] = None


class DeviceUpdateSchema(Schema):
    """تحديث الجهاز"""
    push_token: Optional[str] = None
    push_enabled: Optional[bool] = None
    app_version: Optional[str] = None


# =============================================
# ملفات التعريف - Profiles
# =============================================

class VendorProfileSchema(Schema):
    """ملف تعريف التاجر"""
    company_name: str
    company_name_en: Optional[str]
    commercial_register: Optional[str]
    tax_number: Optional[str]
    business_type: Optional[str]
    categories: List[str]
    verification_status: str
    verified_at: Optional[datetime]
    auto_accept_orders: bool
    notification_email: Optional[str]
    total_sales: Decimal
    total_orders: int
    products_count: int


class VendorProfileUpdateSchema(Schema):
    """تحديث ملف تعريف التاجر"""
    company_name: Optional[str] = None
    company_name_en: Optional[str] = None
    commercial_register: Optional[str] = None
    tax_number: Optional[str] = None
    business_type: Optional[str] = None
    categories: Optional[List[str]] = None
    auto_accept_orders: Optional[bool] = None
    notification_email: Optional[EmailStr] = None


class DriverProfileSchema(Schema):
    """ملف تعريف السائق"""
    license_number: str
    license_expiry: date
    vehicle_type: Optional[str]
    vehicle_model: Optional[str]
    vehicle_year: Optional[int]
    vehicle_plate: Optional[str]
    vehicle_color: Optional[str]
    verification_status: str
    verified_at: Optional[datetime]
    is_online: bool
    is_available: bool
    service_areas: List[str]
    max_distance_km: int
    total_deliveries: int
    total_earnings: Decimal
    acceptance_rate: Decimal
    completion_rate: Decimal


class DriverProfileUpdateSchema(Schema):
    """تحديث ملف تعريف السائق"""
    license_number: Optional[str] = None
    license_expiry: Optional[date] = None
    vehicle_type: Optional[str] = None
    vehicle_model: Optional[str] = None
    vehicle_year: Optional[int] = None
    vehicle_plate: Optional[str] = None
    vehicle_color: Optional[str] = None
    service_areas: Optional[List[str]] = None
    max_distance_km: Optional[int] = None


class DriverLocationUpdateSchema(Schema):
    """تحديث موقع السائق"""
    latitude: float
    longitude: float
    is_available: Optional[bool] = None


class DriverStatusUpdateSchema(Schema):
    """تحديث حالة السائق"""
    is_online: bool
    is_available: Optional[bool] = None


# =============================================
# الجلسات - Sessions
# =============================================

class SessionSchema(Schema):
    """جلسة المستخدم"""
    id: UUID
    device_name: Optional[str]
    platform: Optional[str]
    ip_address: Optional[str]
    location: Optional[str]
    is_active: bool
    created_at: datetime
    last_activity: datetime
    expires_at: datetime

    @staticmethod
    def resolve_device_name(obj):
        if obj.device:
            return obj.device.device_name
        return None

    @staticmethod
    def resolve_platform(obj):
        if obj.device:
            return obj.device.platform
        return None


# =============================================
# KYC التحقق من الهوية
# =============================================

class KYCSubmitSchema(Schema):
    """تقديم طلب التحقق"""
    national_id: str
    id_type: str = 'national_id'  # national_id, iqama, passport
    front_image_id: Optional[str] = None  # معرف الصورة المرفوعة
    back_image_id: Optional[str] = None


class KYCStatusSchema(Schema):
    """حالة التحقق"""
    status: str
    submitted_at: Optional[datetime]
    verified_at: Optional[datetime]
    rejection_reason: Optional[str]


# =============================================
# الإشعارات والتفضيلات
# =============================================

class NotificationPreferencesSchema(Schema):
    """تفضيلات الإشعارات"""
    push_enabled: bool
    sms_enabled: bool
    email_enabled: bool
    order_updates: bool
    promotions: bool
    chat_messages: bool
    price_alerts: bool


class NotificationPreferencesUpdateSchema(Schema):
    """تحديث تفضيلات الإشعارات"""
    push_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    order_updates: Optional[bool] = None
    promotions: Optional[bool] = None
    chat_messages: Optional[bool] = None
    price_alerts: Optional[bool] = None


# =============================================
# استجابات عامة
# =============================================

class MessageSchema(Schema):
    """رسالة عامة"""
    message: str
    success: bool = True


class ErrorSchema(Schema):
    """خطأ"""
    error: str
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class OTPSentSchema(Schema):
    """تم إرسال OTP"""
    message: str
    expires_in: int = 600  # 10 دقائق
    resend_after: int = 60  # دقيقة واحدة


# Fix forward reference
TokenResponseSchema.update_forward_refs()
