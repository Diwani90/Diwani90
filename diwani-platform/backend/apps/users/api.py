"""
API المستخدمين
=============

Django Ninja API للمصادقة وإدارة المستخدمين
"""

from typing import List, Optional
from uuid import UUID

from django.db import transaction
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router, File, UploadedFile, Form
from ninja.pagination import paginate, LimitOffsetPagination

from .models import (
    User,
    UserAddress,
    UserDevice,
    UserSession,
    VendorProfile,
    DriverProfile,
)
from .schemas import (
    # Auth
    PhoneLoginRequestSchema,
    OTPVerifyRequestSchema,
    TokenResponseSchema,
    RefreshTokenRequestSchema,
    LogoutRequestSchema,
    OTPSentSchema,
    # User
    UserSchema,
    UserBasicSchema,
    UserUpdateSchema,
    ChangePasswordSchema,
    # Registration
    CustomerRegisterSchema,
    VendorRegisterSchema,
    DriverRegisterSchema,
    # Address
    AddressSchema,
    AddressCreateSchema,
    AddressUpdateSchema,
    # Device
    DeviceSchema,
    DeviceRegisterSchema,
    DeviceUpdateSchema,
    # Profiles
    VendorProfileSchema,
    VendorProfileUpdateSchema,
    DriverProfileSchema,
    DriverProfileUpdateSchema,
    DriverLocationUpdateSchema,
    DriverStatusUpdateSchema,
    # Session
    SessionSchema,
    # Common
    MessageSchema,
    ErrorSchema,
)
from .services import auth_service, user_service, otp_service
from .auth import JWTAuth, get_current_user, OptionalJWTAuth

router = Router()


# =============================================
# المصادقة - Authentication
# =============================================

@router.post('/auth/login', response={200: OTPSentSchema, 400: ErrorSchema}, tags=['المصادقة'])
def login_request(request: HttpRequest, data: PhoneLoginRequestSchema):
    """
    طلب تسجيل الدخول بالهاتف

    يرسل رمز OTP إلى رقم الهاتف
    """
    ip_address = get_client_ip(request)

    success, message = auth_service.login_with_phone(
        phone_number=data.phone_number,
        ip_address=ip_address
    )

    if success:
        return 200, {
            'message': message,
            'expires_in': 600,
            'resend_after': 60
        }

    return 400, {'error': message}


@router.post('/auth/verify', response={200: TokenResponseSchema, 400: ErrorSchema}, tags=['المصادقة'])
def verify_otp(request: HttpRequest, data: OTPVerifyRequestSchema):
    """
    التحقق من OTP وتسجيل الدخول

    يعيد رموز الوصول عند النجاح
    """
    ip_address = get_client_ip(request)

    device_info = None
    if data.device_id:
        device_info = {
            'device_id': data.device_id,
            'device_name': data.device_name,
            'platform': data.platform or 'web',
            'push_token': data.push_token,
        }

    result = auth_service.verify_and_login(
        phone_number=data.phone_number,
        code=data.code,
        device_info=device_info,
        ip_address=ip_address
    )

    if result.success:
        return 200, {
            'access_token': result.tokens.access_token,
            'refresh_token': result.tokens.refresh_token,
            'token_type': result.tokens.token_type,
            'expires_in': result.tokens.expires_in,
            'user': result.user
        }

    return 400, {'error': result.error, 'code': result.error_code}


@router.post('/auth/refresh', response={200: TokenResponseSchema, 400: ErrorSchema}, tags=['المصادقة'])
def refresh_token(request: HttpRequest, data: RefreshTokenRequestSchema):
    """
    تحديث رموز الوصول

    يستخدم refresh_token للحصول على رموز جديدة
    """
    ip_address = get_client_ip(request)

    result = auth_service.refresh_tokens(
        refresh_token=data.refresh_token,
        ip_address=ip_address
    )

    if result.success:
        return 200, {
            'access_token': result.tokens.access_token,
            'refresh_token': result.tokens.refresh_token,
            'token_type': result.tokens.token_type,
            'expires_in': result.tokens.expires_in,
            'user': result.user
        }

    return 400, {'error': result.error, 'code': result.error_code}


@router.post('/auth/logout', response=MessageSchema, auth=JWTAuth(), tags=['المصادقة'])
def logout(request: HttpRequest, data: LogoutRequestSchema):
    """تسجيل الخروج"""
    user = request.auth

    # الحصول على session_id من الرمز
    session_id = getattr(request, 'session_id', None)

    auth_service.logout(
        user=user,
        session_id=session_id,
        all_devices=data.all_devices
    )

    return {'message': 'تم تسجيل الخروج بنجاح', 'success': True}


# =============================================
# التسجيل - Registration
# =============================================

@router.post('/auth/register/customer', response={200: TokenResponseSchema, 400: ErrorSchema}, tags=['التسجيل'])
def register_customer(request: HttpRequest, data: CustomerRegisterSchema):
    """تسجيل عميل جديد"""
    ip_address = get_client_ip(request)

    device_info = None
    if data.device_id:
        device_info = {
            'device_id': data.device_id,
            'platform': data.platform or 'web',
        }

    result = auth_service.register_customer(
        phone_number=data.phone_number,
        code=data.otp_code,
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        referral_code=data.referral_code,
        device_info=device_info,
        ip_address=ip_address
    )

    if result.success:
        return 200, {
            'access_token': result.tokens.access_token,
            'refresh_token': result.tokens.refresh_token,
            'token_type': result.tokens.token_type,
            'expires_in': result.tokens.expires_in,
            'user': result.user
        }

    return 400, {'error': result.error, 'code': result.error_code}


@router.post('/auth/register/vendor', response={200: TokenResponseSchema, 400: ErrorSchema}, tags=['التسجيل'])
def register_vendor(request: HttpRequest, data: VendorRegisterSchema):
    """تسجيل تاجر جديد"""
    ip_address = get_client_ip(request)

    result = auth_service.register_vendor(
        phone_number=data.phone_number,
        code=data.otp_code,
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        company_name=data.company_name,
        company_name_en=data.company_name_en,
        commercial_register=data.commercial_register,
        tax_number=data.tax_number,
        business_type=data.business_type,
        ip_address=ip_address
    )

    if result.success:
        return 200, {
            'access_token': result.tokens.access_token,
            'refresh_token': result.tokens.refresh_token,
            'token_type': result.tokens.token_type,
            'expires_in': result.tokens.expires_in,
            'user': result.user
        }

    return 400, {'error': result.error, 'code': result.error_code}


@router.post('/auth/register/driver', response={200: TokenResponseSchema, 400: ErrorSchema}, tags=['التسجيل'])
def register_driver(request: HttpRequest, data: DriverRegisterSchema):
    """تسجيل سائق جديد"""
    ip_address = get_client_ip(request)

    result = auth_service.register_driver(
        phone_number=data.phone_number,
        code=data.otp_code,
        first_name=data.first_name,
        last_name=data.last_name,
        national_id=data.national_id,
        license_number=data.license_number,
        license_expiry=data.license_expiry,
        vehicle_type=data.vehicle_type,
        vehicle_model=data.vehicle_model,
        vehicle_plate=data.vehicle_plate,
        ip_address=ip_address
    )

    if result.success:
        return 200, {
            'access_token': result.tokens.access_token,
            'refresh_token': result.tokens.refresh_token,
            'token_type': result.tokens.token_type,
            'expires_in': result.tokens.expires_in,
            'user': result.user
        }

    return 400, {'error': result.error, 'code': result.error_code}


@router.post('/auth/register/request-otp', response={200: OTPSentSchema, 400: ErrorSchema}, tags=['التسجيل'])
def request_registration_otp(request: HttpRequest, data: PhoneLoginRequestSchema):
    """طلب OTP للتسجيل"""
    ip_address = get_client_ip(request)

    # التحقق من عدم وجود المستخدم
    if User.objects.filter(phone_number__endswith=data.phone_number[-9:]).exists():
        return 400, {'error': 'رقم الهاتف مسجل مسبقاً', 'code': 'phone_exists'}

    success, message = otp_service.send_otp(
        phone_number=data.phone_number,
        purpose='register',
        ip_address=ip_address
    )

    if success:
        return 200, {
            'message': message,
            'expires_in': 600,
            'resend_after': 60
        }

    return 400, {'error': message}


# =============================================
# الملف الشخصي - Profile
# =============================================

@router.get('/me', response=UserSchema, auth=JWTAuth(), tags=['الملف الشخصي'])
def get_current_profile(request: HttpRequest):
    """الحصول على الملف الشخصي"""
    return request.auth


@router.put('/me', response=UserSchema, auth=JWTAuth(), tags=['الملف الشخصي'])
def update_profile(request: HttpRequest, data: UserUpdateSchema):
    """تحديث الملف الشخصي"""
    user = request.auth

    updated_user = user_service.update_profile(
        user=user,
        data=data.dict(exclude_unset=True)
    )

    return updated_user


@router.post('/me/avatar', response=MessageSchema, auth=JWTAuth(), tags=['الملف الشخصي'])
def upload_avatar(request: HttpRequest, image: UploadedFile = File(...)):
    """رفع الصورة الشخصية"""
    user = request.auth

    # التحقق من نوع الملف
    allowed_types = ['image/jpeg', 'image/png', 'image/webp']
    if image.content_type not in allowed_types:
        return {'message': 'نوع الملف غير مدعوم', 'success': False}

    # التحقق من الحجم (5MB)
    if image.size > 5 * 1024 * 1024:
        return {'message': 'حجم الملف أكبر من 5MB', 'success': False}

    user.avatar = image
    user.save(update_fields=['avatar'])

    return {'message': 'تم تحديث الصورة بنجاح', 'success': True}


@router.get('/me/stats', auth=JWTAuth(), tags=['الملف الشخصي'])
def get_user_stats(request: HttpRequest):
    """إحصائيات المستخدم"""
    return user_service.get_user_stats(request.auth)


# =============================================
# العناوين - Addresses
# =============================================

@router.get('/me/addresses', response=List[AddressSchema], auth=JWTAuth(), tags=['العناوين'])
def list_addresses(request: HttpRequest):
    """قائمة العناوين"""
    return UserAddress.objects.filter(user=request.auth)


@router.post('/me/addresses', response=AddressSchema, auth=JWTAuth(), tags=['العناوين'])
def create_address(request: HttpRequest, data: AddressCreateSchema):
    """إضافة عنوان جديد"""
    return user_service.add_address(
        user=request.auth,
        data=data.dict()
    )


@router.get('/me/addresses/{address_id}', response=AddressSchema, auth=JWTAuth(), tags=['العناوين'])
def get_address(request: HttpRequest, address_id: UUID):
    """تفاصيل عنوان"""
    return get_object_or_404(
        UserAddress,
        id=address_id,
        user=request.auth
    )


@router.put('/me/addresses/{address_id}', response=AddressSchema, auth=JWTAuth(), tags=['العناوين'])
def update_address(request: HttpRequest, address_id: UUID, data: AddressUpdateSchema):
    """تحديث عنوان"""
    address = user_service.update_address(
        user=request.auth,
        address_id=str(address_id),
        data=data.dict(exclude_unset=True)
    )

    if not address:
        return {'error': 'العنوان غير موجود'}

    return address


@router.delete('/me/addresses/{address_id}', response=MessageSchema, auth=JWTAuth(), tags=['العناوين'])
def delete_address(request: HttpRequest, address_id: UUID):
    """حذف عنوان"""
    deleted = user_service.delete_address(
        user=request.auth,
        address_id=str(address_id)
    )

    if deleted:
        return {'message': 'تم حذف العنوان', 'success': True}

    return {'message': 'العنوان غير موجود', 'success': False}


@router.post('/me/addresses/{address_id}/default', response=MessageSchema, auth=JWTAuth(), tags=['العناوين'])
def set_default_address(request: HttpRequest, address_id: UUID):
    """تعيين العنوان الافتراضي"""
    # استخدام transaction لتجنب race conditions
    with transaction.atomic():
        # قفل الصفوف المتأثرة أثناء التحديث
        address = UserAddress.objects.select_for_update().filter(
            id=address_id,
            user=request.auth
        ).first()

        if not address:
            return {'message': 'العنوان غير موجود', 'success': False}

        # إلغاء العنوان الافتراضي السابق مع القفل
        UserAddress.objects.select_for_update().filter(
            user=request.auth,
            is_default=True
        ).update(is_default=False)

        address.is_default = True
        address.save(update_fields=['is_default'])

    return {'message': 'تم تعيين العنوان الافتراضي', 'success': True}


# =============================================
# الأجهزة - Devices
# =============================================

@router.get('/me/devices', response=List[DeviceSchema], auth=JWTAuth(), tags=['الأجهزة'])
def list_devices(request: HttpRequest):
    """قائمة الأجهزة"""
    return UserDevice.objects.filter(user=request.auth, is_active=True)


@router.post('/me/devices', response=DeviceSchema, auth=JWTAuth(), tags=['الأجهزة'])
def register_device(request: HttpRequest, data: DeviceRegisterSchema):
    """تسجيل جهاز جديد"""
    device, created = UserDevice.objects.update_or_create(
        user=request.auth,
        device_id=data.device_id,
        defaults={
            'device_name': data.device_name or '',
            'platform': data.platform,
            'os_version': data.os_version or '',
            'app_version': data.app_version or '',
            'push_token': data.push_token or '',
            'is_active': True,
        }
    )

    return device


@router.put('/me/devices/{device_id}', response=DeviceSchema, auth=JWTAuth(), tags=['الأجهزة'])
def update_device(request: HttpRequest, device_id: str, data: DeviceUpdateSchema):
    """تحديث جهاز"""
    device = get_object_or_404(
        UserDevice,
        device_id=device_id,
        user=request.auth
    )

    for field, value in data.dict(exclude_unset=True).items():
        if value is not None:
            setattr(device, field, value)

    device.save()
    return device


@router.delete('/me/devices/{device_id}', response=MessageSchema, auth=JWTAuth(), tags=['الأجهزة'])
def remove_device(request: HttpRequest, device_id: str):
    """إزالة جهاز"""
    deleted, _ = UserDevice.objects.filter(
        device_id=device_id,
        user=request.auth
    ).delete()

    if deleted:
        return {'message': 'تم إزالة الجهاز', 'success': True}

    return {'message': 'الجهاز غير موجود', 'success': False}


# =============================================
# الجلسات - Sessions
# =============================================

@router.get('/me/sessions', response=List[SessionSchema], auth=JWTAuth(), tags=['الجلسات'])
def list_sessions(request: HttpRequest):
    """قائمة الجلسات النشطة"""
    return UserSession.objects.filter(
        user=request.auth,
        is_active=True
    ).select_related('device')


@router.delete('/me/sessions/{session_id}', response=MessageSchema, auth=JWTAuth(), tags=['الجلسات'])
def revoke_session(request: HttpRequest, session_id: UUID):
    """إلغاء جلسة"""
    session = get_object_or_404(
        UserSession,
        id=session_id,
        user=request.auth,
        is_active=True
    )

    session.revoke()

    return {'message': 'تم إلغاء الجلسة', 'success': True}


@router.post('/me/sessions/revoke-all', response=MessageSchema, auth=JWTAuth(), tags=['الجلسات'])
def revoke_all_sessions(request: HttpRequest, except_current: bool = True):
    """إلغاء جميع الجلسات"""
    queryset = UserSession.objects.filter(
        user=request.auth,
        is_active=True
    )

    if except_current:
        current_session_id = getattr(request, 'session_id', None)
        if current_session_id:
            queryset = queryset.exclude(id=current_session_id)

    count = queryset.update(
        is_active=False,
        revoked_at=__import__('django.utils.timezone', fromlist=['now']).now()
    )

    return {'message': f'تم إلغاء {count} جلسة', 'success': True}


# =============================================
# ملف تعريف التاجر - Vendor Profile
# =============================================

@router.get('/me/vendor-profile', response=VendorProfileSchema, auth=JWTAuth(), tags=['ملف التاجر'])
def get_vendor_profile(request: HttpRequest):
    """الحصول على ملف تعريف التاجر"""
    user = request.auth

    if user.user_type != 'vendor':
        return {'error': 'هذا المستخدم ليس تاجراً'}

    return get_object_or_404(VendorProfile, user=user)


@router.put('/me/vendor-profile', response=VendorProfileSchema, auth=JWTAuth(), tags=['ملف التاجر'])
def update_vendor_profile(request: HttpRequest, data: VendorProfileUpdateSchema):
    """تحديث ملف تعريف التاجر"""
    user = request.auth

    if user.user_type != 'vendor':
        return {'error': 'هذا المستخدم ليس تاجراً'}

    profile = get_object_or_404(VendorProfile, user=user)

    for field, value in data.dict(exclude_unset=True).items():
        if value is not None:
            setattr(profile, field, value)

    profile.save()
    return profile


@router.post('/me/vendor-profile/documents', response=MessageSchema, auth=JWTAuth(), tags=['ملف التاجر'])
def upload_vendor_documents(
    request: HttpRequest,
    commercial_register: UploadedFile = File(None),
    tax_certificate: UploadedFile = File(None),
    id_document: UploadedFile = File(None),
):
    """رفع مستندات التاجر"""
    user = request.auth

    if user.user_type != 'vendor':
        return {'message': 'هذا المستخدم ليس تاجراً', 'success': False}

    profile = get_object_or_404(VendorProfile, user=user)

    if commercial_register:
        profile.commercial_register_doc = commercial_register

    if tax_certificate:
        profile.tax_certificate_doc = tax_certificate

    if id_document:
        profile.id_document = id_document

    profile.save()

    return {'message': 'تم رفع المستندات بنجاح', 'success': True}


# =============================================
# ملف تعريف السائق - Driver Profile
# =============================================

@router.get('/me/driver-profile', response=DriverProfileSchema, auth=JWTAuth(), tags=['ملف السائق'])
def get_driver_profile(request: HttpRequest):
    """الحصول على ملف تعريف السائق"""
    user = request.auth

    if user.user_type != 'driver':
        return {'error': 'هذا المستخدم ليس سائقاً'}

    return get_object_or_404(DriverProfile, user=user)


@router.put('/me/driver-profile', response=DriverProfileSchema, auth=JWTAuth(), tags=['ملف السائق'])
def update_driver_profile(request: HttpRequest, data: DriverProfileUpdateSchema):
    """تحديث ملف تعريف السائق"""
    user = request.auth

    if user.user_type != 'driver':
        return {'error': 'هذا المستخدم ليس سائقاً'}

    profile = get_object_or_404(DriverProfile, user=user)

    for field, value in data.dict(exclude_unset=True).items():
        if value is not None:
            setattr(profile, field, value)

    profile.save()
    return profile


@router.post('/me/driver-profile/location', response=MessageSchema, auth=JWTAuth(), tags=['ملف السائق'])
def update_driver_location(request: HttpRequest, data: DriverLocationUpdateSchema):
    """تحديث موقع السائق"""
    user = request.auth

    if user.user_type != 'driver':
        return {'message': 'هذا المستخدم ليس سائقاً', 'success': False}

    profile = get_object_or_404(DriverProfile, user=user)
    profile.update_location(data.latitude, data.longitude)

    if data.is_available is not None:
        profile.is_available = data.is_available
        profile.save(update_fields=['is_available'])

    return {'message': 'تم تحديث الموقع', 'success': True}


@router.post('/me/driver-profile/status', response=MessageSchema, auth=JWTAuth(), tags=['ملف السائق'])
def update_driver_status(request: HttpRequest, data: DriverStatusUpdateSchema):
    """تحديث حالة السائق (متصل/متاح)"""
    user = request.auth

    if user.user_type != 'driver':
        return {'message': 'هذا المستخدم ليس سائقاً', 'success': False}

    profile = get_object_or_404(DriverProfile, user=user)

    profile.is_online = data.is_online
    if data.is_available is not None:
        profile.is_available = data.is_available
    elif not data.is_online:
        profile.is_available = False

    profile.save(update_fields=['is_online', 'is_available'])

    return {'message': 'تم تحديث الحالة', 'success': True}


# =============================================
# مساعدات
# =============================================

def get_client_ip(request: HttpRequest) -> str:
    """الحصول على IP العميل"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')
