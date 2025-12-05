"""
===================================
منصة ديواني - Accounts API
Django Ninja API Endpoints
===================================
"""

from typing import List
from datetime import timedelta
from uuid import UUID

from django.contrib.auth import authenticate
from django.contrib.gis.geos import Point
from django.utils import timezone
from django.conf import settings

from ninja import Router, File
from ninja.files import UploadedFile
from ninja_jwt.tokens import RefreshToken

from .models import User, OTP, Address, WalletTransaction, DriverProfile, VendorProfile
from .schemas import (
    RequestOTPSchema,
    VerifyOTPSchema,
    RegisterSchema,
    LoginResponseSchema,
    RefreshTokenSchema,
    UserOutSchema,
    UserUpdateSchema,
    UpdateFCMTokenSchema,
    AddressCreateSchema,
    AddressUpdateSchema,
    AddressOutSchema,
    WalletTransactionOutSchema,
    WalletBalanceSchema,
    DriverRegisterSchema,
    DriverProfileOutSchema,
    DriverLocationUpdateSchema,
    VendorRegisterSchema,
    VendorProfileOutSchema,
    MessageSchema,
    ErrorSchema,
)

# Create router
router = Router(tags=['المستخدمين والمصادقة'])


# ===================================
# Authentication Endpoints
# ===================================
@router.post('/auth/request-otp', response={200: MessageSchema, 400: ErrorSchema})
def request_otp(request, data: RequestOTPSchema):
    """
    طلب رمز التحقق OTP
    ---
    يرسل رمز تحقق مكون من 6 أرقام إلى رقم الجوال
    """
    try:
        # Generate OTP
        otp = OTP.generate(data.phone_number, purpose=OTP.Purpose.LOGIN)

        # TODO: Send SMS via Unifonic/Msegat
        # For development, we'll log the OTP
        print(f"[DEV] OTP for {data.phone_number}: {otp.code}")

        return 200, MessageSchema(
            message='تم إرسال رمز التحقق بنجاح',
            success=True
        )
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


@router.post('/auth/verify-otp', response={200: LoginResponseSchema, 400: ErrorSchema})
def verify_otp(request, data: VerifyOTPSchema):
    """
    التحقق من رمز OTP وتسجيل الدخول
    ---
    يتحقق من الرمز ويعيد tokens للمصادقة
    """
    try:
        # Find latest valid OTP
        otp = OTP.objects.filter(
            phone_number=data.phone_number,
            purpose=OTP.Purpose.LOGIN,
            is_used=False
        ).order_by('-created_at').first()

        if not otp:
            return 400, ErrorSchema(message='لم يتم العثور على رمز تحقق')

        # Verify OTP
        success, message = otp.verify(data.code)
        if not success:
            return 400, ErrorSchema(message=message)

        # Get or create user
        user, created = User.objects.get_or_create(
            phone_number=data.phone_number,
            defaults={
                'first_name': 'مستخدم',
                'last_name': 'جديد',
                'is_verified': True
            }
        )

        if not created:
            user.is_verified = True
            user.last_login_at = timezone.now()
            user.save(update_fields=['is_verified', 'last_login_at'])

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        return 200, LoginResponseSchema(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.NINJA_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
            user=UserOutSchema.from_orm(user)
        )
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


@router.post('/auth/register', response={201: LoginResponseSchema, 400: ErrorSchema})
def register(request, data: RegisterSchema):
    """
    تسجيل مستخدم جديد
    ---
    يتطلب التحقق من رقم الجوال أولاً
    """
    try:
        # Check if user already exists
        if User.objects.filter(phone_number=data.phone_number).exists():
            return 400, ErrorSchema(message='رقم الجوال مسجل مسبقاً')

        # Check referral code if provided
        referred_by = None
        if data.referral_code:
            referred_by = User.objects.filter(
                referral_code=data.referral_code
            ).first()

        # Create user
        user = User.objects.create_user(
            phone_number=data.phone_number,
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            referred_by=referred_by,
            is_verified=True
        )

        # Add referral bonus if applicable
        if referred_by:
            referred_by.add_to_wallet(10, 'مكافأة إحالة')
            user.add_to_wallet(10, 'مكافأة تسجيل بكود إحالة')

        # Generate tokens
        refresh = RefreshToken.for_user(user)

        return 201, LoginResponseSchema(
            access_token=str(refresh.access_token),
            refresh_token=str(refresh),
            expires_in=settings.NINJA_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(),
            user=UserOutSchema.from_orm(user)
        )
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


@router.post('/auth/refresh', response={200: dict, 400: ErrorSchema})
def refresh_token(request, data: RefreshTokenSchema):
    """
    تجديد التوكن
    ---
    يجدد access token باستخدام refresh token
    """
    try:
        refresh = RefreshToken(data.refresh_token)
        return 200, {
            'access_token': str(refresh.access_token),
            'token_type': 'Bearer'
        }
    except Exception as e:
        return 400, ErrorSchema(message='التوكن غير صالح')


# ===================================
# User Profile Endpoints
# ===================================
@router.get('/me', response=UserOutSchema, auth=None)  # Will add auth later
def get_current_user(request):
    """
    الحصول على بيانات المستخدم الحالي
    """
    # TODO: Add proper authentication
    user = request.user if request.user.is_authenticated else User.objects.first()
    return user


@router.patch('/me', response={200: UserOutSchema, 400: ErrorSchema})
def update_profile(request, data: UserUpdateSchema):
    """
    تحديث بيانات المستخدم
    """
    try:
        user = request.user
        update_data = data.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(user, field, value)

        user.save()
        return 200, UserOutSchema.from_orm(user)
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


@router.post('/me/avatar', response={200: UserOutSchema, 400: ErrorSchema})
def upload_avatar(request, file: UploadedFile = File(...)):
    """
    رفع الصورة الشخصية
    """
    try:
        user = request.user

        # Validate file type
        allowed_types = settings.DIWANI_SETTINGS['ALLOWED_IMAGE_TYPES']
        if file.content_type not in allowed_types:
            return 400, ErrorSchema(message='نوع الملف غير مدعوم')

        # Validate file size
        max_size = settings.DIWANI_SETTINGS['MAX_IMAGE_SIZE_MB'] * 1024 * 1024
        if file.size > max_size:
            return 400, ErrorSchema(message='حجم الملف كبير جداً')

        user.avatar = file
        user.save(update_fields=['avatar'])

        return 200, UserOutSchema.from_orm(user)
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


@router.post('/me/fcm-token', response=MessageSchema)
def update_fcm_token(request, data: UpdateFCMTokenSchema):
    """
    تحديث رمز FCM للإشعارات
    """
    user = request.user
    user.fcm_token = data.fcm_token
    user.save(update_fields=['fcm_token'])
    return MessageSchema(message='تم تحديث رمز الإشعارات')


# ===================================
# Address Endpoints
# ===================================
@router.get('/me/addresses', response=List[AddressOutSchema])
def list_addresses(request):
    """
    قائمة عناوين المستخدم
    """
    return request.user.addresses.all()


@router.post('/me/addresses', response={201: AddressOutSchema, 400: ErrorSchema})
def create_address(request, data: AddressCreateSchema):
    """
    إضافة عنوان جديد
    """
    try:
        address_data = data.dict(exclude={'latitude', 'longitude'})

        # Create location point if coordinates provided
        if data.latitude and data.longitude:
            address_data['location'] = Point(data.longitude, data.latitude, srid=4326)

        address = Address.objects.create(user=request.user, **address_data)
        return 201, AddressOutSchema.from_orm(address)
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


@router.get('/me/addresses/{address_id}', response={200: AddressOutSchema, 404: ErrorSchema})
def get_address(request, address_id: UUID):
    """
    الحصول على تفاصيل عنوان
    """
    try:
        address = Address.objects.get(id=address_id, user=request.user)
        return 200, AddressOutSchema.from_orm(address)
    except Address.DoesNotExist:
        return 404, ErrorSchema(message='العنوان غير موجود')


@router.patch('/me/addresses/{address_id}', response={200: AddressOutSchema, 400: ErrorSchema})
def update_address(request, address_id: UUID, data: AddressUpdateSchema):
    """
    تحديث عنوان
    """
    try:
        address = Address.objects.get(id=address_id, user=request.user)
        update_data = data.dict(exclude_unset=True, exclude={'latitude', 'longitude'})

        # Update location if coordinates provided
        if data.latitude is not None and data.longitude is not None:
            address.location = Point(data.longitude, data.latitude, srid=4326)

        for field, value in update_data.items():
            setattr(address, field, value)

        address.save()
        return 200, AddressOutSchema.from_orm(address)
    except Address.DoesNotExist:
        return 400, ErrorSchema(message='العنوان غير موجود')
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


@router.delete('/me/addresses/{address_id}', response={200: MessageSchema, 404: ErrorSchema})
def delete_address(request, address_id: UUID):
    """
    حذف عنوان
    """
    try:
        address = Address.objects.get(id=address_id, user=request.user)
        address.delete()
        return 200, MessageSchema(message='تم حذف العنوان بنجاح')
    except Address.DoesNotExist:
        return 404, ErrorSchema(message='العنوان غير موجود')


# ===================================
# Wallet Endpoints
# ===================================
@router.get('/me/wallet', response=WalletBalanceSchema)
def get_wallet_balance(request):
    """
    رصيد المحفظة
    """
    return WalletBalanceSchema(balance=request.user.wallet_balance)


@router.get('/me/wallet/transactions', response=List[WalletTransactionOutSchema])
def list_wallet_transactions(request, limit: int = 20, offset: int = 0):
    """
    سجل عمليات المحفظة
    """
    transactions = WalletTransaction.objects.filter(
        user=request.user
    )[offset:offset + limit]
    return [WalletTransactionOutSchema.from_orm(t) for t in transactions]


# ===================================
# Driver Endpoints
# ===================================
@router.post('/me/become-driver', response={201: DriverProfileOutSchema, 400: ErrorSchema})
def become_driver(
    request,
    data: DriverRegisterSchema,
    driving_license: UploadedFile = File(...),
    vehicle_registration: UploadedFile = File(...)
):
    """
    التسجيل كسائق
    """
    try:
        user = request.user

        if hasattr(user, 'driver_profile'):
            return 400, ErrorSchema(message='أنت مسجل كسائق بالفعل')

        profile = DriverProfile.objects.create(
            user=user,
            **data.dict(),
            driving_license=driving_license,
            vehicle_registration=vehicle_registration
        )

        user.user_type = User.UserType.DRIVER
        user.save(update_fields=['user_type'])

        return 201, DriverProfileOutSchema.from_orm(profile)
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


@router.get('/me/driver-profile', response={200: DriverProfileOutSchema, 404: ErrorSchema})
def get_driver_profile(request):
    """
    الحصول على ملف السائق
    """
    try:
        profile = request.user.driver_profile
        return 200, DriverProfileOutSchema.from_orm(profile)
    except DriverProfile.DoesNotExist:
        return 404, ErrorSchema(message='لم يتم العثور على ملف السائق')


@router.post('/me/driver/location', response=MessageSchema)
def update_driver_location(request, data: DriverLocationUpdateSchema):
    """
    تحديث موقع السائق
    """
    try:
        profile = request.user.driver_profile
        profile.update_location(data.latitude, data.longitude)
        return MessageSchema(message='تم تحديث الموقع')
    except DriverProfile.DoesNotExist:
        return MessageSchema(message='لم يتم العثور على ملف السائق', success=False)


@router.post('/me/driver/online', response=MessageSchema)
def go_online(request):
    """
    تفعيل حالة الاتصال للسائق
    """
    try:
        profile = request.user.driver_profile
        profile.go_online()
        return MessageSchema(message='أنت الآن متصل')
    except DriverProfile.DoesNotExist:
        return MessageSchema(message='لم يتم العثور على ملف السائق', success=False)


@router.post('/me/driver/offline', response=MessageSchema)
def go_offline(request):
    """
    إيقاف حالة الاتصال للسائق
    """
    try:
        profile = request.user.driver_profile
        profile.go_offline()
        return MessageSchema(message='أنت الآن غير متصل')
    except DriverProfile.DoesNotExist:
        return MessageSchema(message='لم يتم العثور على ملف السائق', success=False)


# ===================================
# Vendor Endpoints
# ===================================
@router.post('/me/become-vendor', response={201: VendorProfileOutSchema, 400: ErrorSchema})
def become_vendor(
    request,
    data: VendorRegisterSchema,
    commercial_registration_doc: UploadedFile = File(...)
):
    """
    التسجيل كتاجر
    """
    try:
        user = request.user

        if hasattr(user, 'vendor_profile'):
            return 400, ErrorSchema(message='أنت مسجل كتاجر بالفعل')

        profile = VendorProfile.objects.create(
            user=user,
            **data.dict(),
            commercial_registration_doc=commercial_registration_doc
        )

        user.user_type = User.UserType.VENDOR
        user.save(update_fields=['user_type'])

        return 201, VendorProfileOutSchema.from_orm(profile)
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


@router.get('/me/vendor-profile', response={200: VendorProfileOutSchema, 404: ErrorSchema})
def get_vendor_profile(request):
    """
    الحصول على ملف التاجر
    """
    try:
        profile = request.user.vendor_profile
        return 200, VendorProfileOutSchema.from_orm(profile)
    except VendorProfile.DoesNotExist:
        return 404, ErrorSchema(message='لم يتم العثور على ملف التاجر')
