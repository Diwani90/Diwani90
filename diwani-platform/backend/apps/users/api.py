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
from .auth import JWTAuth, get_current_user, OptionalJWTAuth, AdminJWTAuth

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


# =============================================
# إدارة المستخدمين - Admin User Management
# =============================================

@router.get('/admin/users', auth=AdminJWTAuth(), tags=['إدارة المستخدمين'])
def list_all_users(
    request: HttpRequest,
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    user_type: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: str = '-created_at',
):
    """قائمة جميع المستخدمين (للمدير فقط)"""
    from django.db.models import Q

    queryset = User.objects.all()

    # البحث
    if search:
        queryset = queryset.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone_number__icontains=search) |
            Q(email__icontains=search)
        )

    # فلتر النوع
    if user_type:
        queryset = queryset.filter(user_type=user_type)

    # فلتر الحالة
    if status:
        queryset = queryset.filter(status=status)

    # الترتيب
    queryset = queryset.order_by(sort_by)

    # التصفيح
    total = queryset.count()
    offset = (page - 1) * per_page
    users = queryset[offset:offset + per_page]

    return {
        'items': [
            {
                'id': str(u.id),
                'phone_number': u.phone_number,
                'full_name': u.full_name,
                'email': u.email,
                'user_type': u.user_type,
                'status': u.status,
                'is_verified': u.is_verified,
                'created_at': u.created_at.isoformat(),
                'last_login_at': u.last_login_at.isoformat() if u.last_login_at else None,
            }
            for u in users
        ],
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page,
    }


@router.get('/admin/users/{user_id}', auth=AdminJWTAuth(), tags=['إدارة المستخدمين'])
def get_user_details(request: HttpRequest, user_id: UUID):
    """تفاصيل مستخدم (للمدير فقط)"""
    user = get_object_or_404(User, id=user_id)

    result = {
        'id': str(user.id),
        'phone_number': user.phone_number,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.full_name,
        'email': user.email,
        'user_type': user.user_type,
        'status': user.status,
        'is_verified': user.is_verified,
        'phone_verified': user.phone_verified,
        'email_verified': user.email_verified,
        'national_id': user.national_id,
        'orders_count': user.orders_count,
        'total_spent': float(user.total_spent),
        'loyalty_points': user.loyalty_points,
        'created_at': user.created_at.isoformat(),
        'last_login_at': user.last_login_at.isoformat() if user.last_login_at else None,
    }

    # إضافة معلومات التاجر إن وجدت
    if user.user_type == 'vendor':
        vendor_profile = VendorProfile.objects.filter(user=user).first()
        if vendor_profile:
            result['vendor_profile'] = {
                'company_name': vendor_profile.company_name,
                'commercial_register': vendor_profile.commercial_register,
                'tax_number': vendor_profile.tax_number,
                'is_verified': vendor_profile.is_verified,
            }

    # إضافة معلومات السائق إن وجدت
    if user.user_type == 'driver':
        driver_profile = DriverProfile.objects.filter(user=user).first()
        if driver_profile:
            result['driver_profile'] = {
                'license_number': driver_profile.license_number,
                'vehicle_type': driver_profile.vehicle_type,
                'vehicle_plate': driver_profile.vehicle_plate,
                'is_verified': driver_profile.is_verified,
                'is_available': driver_profile.is_available,
            }

    return result


@router.put('/admin/users/{user_id}/status', auth=AdminJWTAuth(), tags=['إدارة المستخدمين'])
def update_user_status(
    request: HttpRequest,
    user_id: UUID,
    status: str,
    reason: Optional[str] = None,
):
    """تحديث حالة المستخدم (للمدير فقط)"""
    user = get_object_or_404(User, id=user_id)

    valid_statuses = ['active', 'pending', 'suspended', 'banned']
    if status not in valid_statuses:
        return {'error': f'حالة غير صالحة. الحالات المسموحة: {", ".join(valid_statuses)}'}

    old_status = user.status
    user.status = status
    user.save(update_fields=['status'])

    # يمكن إضافة log للتغييرات هنا

    return {
        'message': 'تم تحديث حالة المستخدم بنجاح',
        'user_id': str(user.id),
        'old_status': old_status,
        'new_status': status,
    }


@router.delete('/admin/users/{user_id}', auth=AdminJWTAuth(), tags=['إدارة المستخدمين'])
def delete_user(request: HttpRequest, user_id: UUID):
    """حذف مستخدم (للمدير فقط) - Soft delete"""
    user = get_object_or_404(User, id=user_id)

    # لا يمكن حذف المدير نفسه
    if user.id == request.auth.id:
        return {'error': 'لا يمكنك حذف حسابك الخاص'}

    # Soft delete
    user.status = UserStatus.BANNED
    user.is_active = False
    user.save(update_fields=['status', 'is_active'])

    # إلغاء جميع الجلسات
    UserSession.objects.filter(user=user, is_active=True).update(is_active=False)

    return {'message': 'تم حذف المستخدم بنجاح', 'user_id': str(user.id)}


# =============================================
# إدارة البائعين/الموردين - Admin Vendor Management
# =============================================

@router.get('/admin/vendors', auth=AdminJWTAuth(), tags=['إدارة البائعين'])
def list_all_vendors(
    request: HttpRequest,
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    status: Optional[str] = None,
    is_verified: Optional[bool] = None,
    sort_by: str = '-created_at',
):
    """قائمة جميع البائعين/الموردين (للمدير فقط)"""
    from django.db.models import Q

    queryset = VendorProfile.objects.select_related('user').all()

    # البحث
    if search:
        queryset = queryset.filter(
            Q(company_name__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__phone_number__icontains=search) |
            Q(commercial_register__icontains=search)
        )

    # فلتر الحالة
    if status:
        queryset = queryset.filter(user__status=status)

    # فلتر التوثيق
    if is_verified is not None:
        queryset = queryset.filter(is_verified=is_verified)

    # الترتيب
    if sort_by.startswith('-'):
        field = sort_by[1:]
        queryset = queryset.order_by(f'-user__{field}' if field == 'created_at' else sort_by)
    else:
        queryset = queryset.order_by(f'user__{sort_by}' if sort_by == 'created_at' else sort_by)

    # التصفيح
    total = queryset.count()
    offset = (page - 1) * per_page
    vendors = queryset[offset:offset + per_page]

    return {
        'items': [
            {
                'id': str(v.id),
                'user_id': str(v.user.id),
                'company_name': v.company_name,
                'owner_name': v.user.full_name,
                'phone_number': v.user.phone_number,
                'email': v.user.email,
                'commercial_register': v.commercial_register,
                'tax_number': v.tax_number,
                'status': v.user.status,
                'is_verified': v.is_verified,
                'created_at': v.user.created_at.isoformat(),
            }
            for v in vendors
        ],
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page,
    }


@router.get('/admin/vendors/{vendor_id}', auth=AdminJWTAuth(), tags=['إدارة البائعين'])
def get_vendor_details(request: HttpRequest, vendor_id: UUID):
    """تفاصيل بائع/مورد (للمدير فقط)"""
    vendor = get_object_or_404(VendorProfile.objects.select_related('user'), id=vendor_id)

    return {
        'id': str(vendor.id),
        'user_id': str(vendor.user.id),
        'company_name': vendor.company_name,
        'company_name_en': vendor.company_name_en,
        'commercial_register': vendor.commercial_register,
        'tax_number': vendor.tax_number,
        'business_type': vendor.business_type,
        'is_verified': vendor.is_verified,
        'verified_at': vendor.verified_at.isoformat() if vendor.verified_at else None,
        'user': {
            'full_name': vendor.user.full_name,
            'phone_number': vendor.user.phone_number,
            'email': vendor.user.email,
            'status': vendor.user.status,
            'created_at': vendor.user.created_at.isoformat(),
        }
    }


@router.post('/admin/vendors/{vendor_id}/verify', auth=AdminJWTAuth(), tags=['إدارة البائعين'])
def verify_vendor(
    request: HttpRequest,
    vendor_id: UUID,
    is_verified: bool = True,
    notes: Optional[str] = None,
):
    """توثيق/رفض بائع (للمدير فقط)"""
    from django.utils import timezone

    vendor = get_object_or_404(VendorProfile, id=vendor_id)

    vendor.is_verified = is_verified
    if is_verified:
        vendor.verified_at = timezone.now()
        vendor.user.status = 'active'
        vendor.user.is_verified = True
        vendor.user.save(update_fields=['status', 'is_verified'])
    else:
        vendor.verified_at = None
        vendor.user.status = 'pending'
        vendor.user.save(update_fields=['status'])

    vendor.save(update_fields=['is_verified', 'verified_at'])

    action = 'توثيق' if is_verified else 'رفض توثيق'
    return {
        'message': f'تم {action} البائع بنجاح',
        'vendor_id': str(vendor.id),
        'is_verified': vendor.is_verified,
    }


@router.put('/admin/vendors/{vendor_id}/status', auth=AdminJWTAuth(), tags=['إدارة البائعين'])
def update_vendor_status(
    request: HttpRequest,
    vendor_id: UUID,
    status: str,
    reason: Optional[str] = None,
):
    """تحديث حالة البائع (للمدير فقط)"""
    vendor = get_object_or_404(VendorProfile, id=vendor_id)

    valid_statuses = ['active', 'pending', 'suspended', 'banned']
    if status not in valid_statuses:
        return {'error': f'حالة غير صالحة. الحالات المسموحة: {", ".join(valid_statuses)}'}

    old_status = vendor.user.status
    vendor.user.status = status
    vendor.user.save(update_fields=['status'])

    return {
        'message': 'تم تحديث حالة البائع بنجاح',
        'vendor_id': str(vendor.id),
        'old_status': old_status,
        'new_status': status,
    }


# =============================================
# إدارة السائقين - Admin Driver Management
# =============================================

@router.get('/admin/drivers', auth=AdminJWTAuth(), tags=['إدارة السائقين'])
def list_all_drivers(
    request: HttpRequest,
    page: int = 1,
    per_page: int = 20,
    search: Optional[str] = None,
    status: Optional[str] = None,
    is_verified: Optional[bool] = None,
    is_available: Optional[bool] = None,
    sort_by: str = '-created_at',
):
    """قائمة جميع السائقين (للمدير فقط)"""
    from django.db.models import Q

    queryset = DriverProfile.objects.select_related('user').all()

    # البحث
    if search:
        queryset = queryset.filter(
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search) |
            Q(user__phone_number__icontains=search) |
            Q(license_number__icontains=search) |
            Q(vehicle_plate__icontains=search)
        )

    # فلتر الحالة
    if status:
        queryset = queryset.filter(user__status=status)

    # فلتر التوثيق
    if is_verified is not None:
        queryset = queryset.filter(is_verified=is_verified)

    # فلتر التوفر
    if is_available is not None:
        queryset = queryset.filter(is_available=is_available)

    # الترتيب
    if sort_by.startswith('-'):
        field = sort_by[1:]
        queryset = queryset.order_by(f'-user__{field}' if field == 'created_at' else sort_by)
    else:
        queryset = queryset.order_by(f'user__{sort_by}' if sort_by == 'created_at' else sort_by)

    # التصفيح
    total = queryset.count()
    offset = (page - 1) * per_page
    drivers = queryset[offset:offset + per_page]

    return {
        'items': [
            {
                'id': str(d.id),
                'user_id': str(d.user.id),
                'full_name': d.user.full_name,
                'phone_number': d.user.phone_number,
                'license_number': d.license_number,
                'vehicle_type': d.vehicle_type,
                'vehicle_plate': d.vehicle_plate,
                'status': d.user.status,
                'is_verified': d.is_verified,
                'is_available': d.is_available,
                'is_online': d.is_online,
                'created_at': d.user.created_at.isoformat(),
            }
            for d in drivers
        ],
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': (total + per_page - 1) // per_page,
    }


@router.post('/admin/drivers/{driver_id}/verify', auth=AdminJWTAuth(), tags=['إدارة السائقين'])
def verify_driver(
    request: HttpRequest,
    driver_id: UUID,
    is_verified: bool = True,
    notes: Optional[str] = None,
):
    """توثيق/رفض سائق (للمدير فقط)"""
    from django.utils import timezone

    driver = get_object_or_404(DriverProfile, id=driver_id)

    driver.is_verified = is_verified
    if is_verified:
        driver.verified_at = timezone.now()
        driver.user.status = 'active'
        driver.user.is_verified = True
        driver.user.save(update_fields=['status', 'is_verified'])
    else:
        driver.verified_at = None
        driver.user.status = 'pending'
        driver.user.save(update_fields=['status'])

    driver.save(update_fields=['is_verified', 'verified_at'])

    action = 'توثيق' if is_verified else 'رفض توثيق'
    return {
        'message': f'تم {action} السائق بنجاح',
        'driver_id': str(driver.id),
        'is_verified': driver.is_verified,
    }


# =============================================
# إحصائيات الإدارة - Admin Statistics
# =============================================

@router.get('/admin/stats', auth=AdminJWTAuth(), tags=['إحصائيات الإدارة'])
def get_admin_stats(request: HttpRequest):
    """إحصائيات شاملة للإدارة"""
    from django.db.models import Count, Sum, Avg, Q
    from django.utils import timezone
    from datetime import timedelta

    today = timezone.now()
    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)

    # إحصائيات المستخدمين
    users_stats = User.objects.aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(status='active')),
        pending=Count('id', filter=Q(status='pending')),
        suspended=Count('id', filter=Q(status='suspended')),
        customers=Count('id', filter=Q(user_type='customer')),
        vendors=Count('id', filter=Q(user_type='vendor')),
        drivers=Count('id', filter=Q(user_type='driver')),
        new_last_30_days=Count('id', filter=Q(created_at__gte=last_30_days)),
        new_last_7_days=Count('id', filter=Q(created_at__gte=last_7_days)),
    )

    # إحصائيات البائعين
    vendors_stats = VendorProfile.objects.aggregate(
        total=Count('id'),
        verified=Count('id', filter=Q(is_verified=True)),
        pending=Count('id', filter=Q(is_verified=False)),
    )

    # إحصائيات السائقين
    drivers_stats = DriverProfile.objects.aggregate(
        total=Count('id'),
        verified=Count('id', filter=Q(is_verified=True)),
        available=Count('id', filter=Q(is_available=True)),
        online=Count('id', filter=Q(is_online=True)),
    )

    return {
        'users': users_stats,
        'vendors': vendors_stats,
        'drivers': drivers_stats,
        'updated_at': today.isoformat(),
    }
