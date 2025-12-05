"""
===================================
منصة ديواني - Accounts Schemas
Pydantic schemas for API validation
===================================
"""

from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, field_validator
from ninja import Schema
import re


# ===================================
# Validators
# ===================================
def validate_saudi_phone(phone: str) -> str:
    """Validate and normalize Saudi phone number."""
    # Remove all non-digits
    digits = ''.join(filter(str.isdigit, phone))

    # Remove country code if present
    if digits.startswith('966'):
        digits = digits[3:]
    elif digits.startswith('0'):
        digits = digits[1:]

    # Validate
    if not re.match(r'^5[0-9]{8}$', digits):
        raise ValueError('رقم الجوال يجب أن يكون سعودي صالح')

    return f'+966{digits}'


# ===================================
# Authentication Schemas
# ===================================
class RequestOTPSchema(Schema):
    """Schema for requesting OTP."""
    phone_number: str = Field(..., description='رقم الجوال السعودي')

    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v):
        return validate_saudi_phone(v)


class VerifyOTPSchema(Schema):
    """Schema for verifying OTP."""
    phone_number: str = Field(..., description='رقم الجوال')
    code: str = Field(..., min_length=6, max_length=6, description='رمز التحقق')

    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v):
        return validate_saudi_phone(v)


class RegisterSchema(Schema):
    """Schema for user registration."""
    phone_number: str = Field(..., description='رقم الجوال')
    first_name: str = Field(..., min_length=2, max_length=50, description='الاسم الأول')
    last_name: str = Field(..., min_length=2, max_length=50, description='اسم العائلة')
    email: Optional[EmailStr] = Field(None, description='البريد الإلكتروني')
    referral_code: Optional[str] = Field(None, description='كود الإحالة')

    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v):
        return validate_saudi_phone(v)


class LoginResponseSchema(Schema):
    """Schema for login response."""
    access_token: str
    refresh_token: str
    token_type: str = 'Bearer'
    expires_in: int
    user: 'UserOutSchema'


class RefreshTokenSchema(Schema):
    """Schema for refreshing tokens."""
    refresh_token: str


# ===================================
# User Schemas
# ===================================
class UserOutSchema(Schema):
    """Schema for user output."""
    id: UUID
    phone_number: str
    email: Optional[str]
    first_name: str
    last_name: str
    full_name: str
    avatar: Optional[str]
    user_type: str
    is_verified: bool
    is_identity_verified: bool
    wallet_balance: Decimal
    referral_code: str
    language: str
    push_notifications_enabled: bool
    created_at: datetime


class UserUpdateSchema(Schema):
    """Schema for updating user profile."""
    first_name: Optional[str] = Field(None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[EmailStr] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    language: Optional[str] = None
    push_notifications_enabled: Optional[bool] = None
    sms_notifications_enabled: Optional[bool] = None


class UpdateFCMTokenSchema(Schema):
    """Schema for updating FCM token."""
    fcm_token: str


class ChangePhoneSchema(Schema):
    """Schema for changing phone number."""
    new_phone_number: str

    @field_validator('new_phone_number')
    @classmethod
    def validate_phone(cls, v):
        return validate_saudi_phone(v)


# ===================================
# Address Schemas
# ===================================
class AddressCreateSchema(Schema):
    """Schema for creating address."""
    label: str = Field(..., max_length=50, description='العنوان المختصر')
    address_type: str = Field('home', description='نوع العنوان')
    street_address: str = Field(..., max_length=255, description='العنوان')
    building_number: Optional[str] = Field(None, max_length=20)
    apartment_number: Optional[str] = Field(None, max_length=20)
    floor: Optional[str] = Field(None, max_length=10)
    city: str = Field(..., max_length=100, description='المدينة')
    district: str = Field(..., max_length=100, description='الحي')
    postal_code: Optional[str] = Field(None, max_length=10)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    additional_directions: Optional[str] = None
    phone_number: Optional[str] = None
    is_default: bool = False


class AddressUpdateSchema(Schema):
    """Schema for updating address."""
    label: Optional[str] = Field(None, max_length=50)
    address_type: Optional[str] = None
    street_address: Optional[str] = Field(None, max_length=255)
    building_number: Optional[str] = Field(None, max_length=20)
    apartment_number: Optional[str] = Field(None, max_length=20)
    floor: Optional[str] = Field(None, max_length=10)
    city: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=10)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    additional_directions: Optional[str] = None
    phone_number: Optional[str] = None
    is_default: Optional[bool] = None


class AddressOutSchema(Schema):
    """Schema for address output."""
    id: UUID
    label: str
    address_type: str
    street_address: str
    building_number: Optional[str]
    apartment_number: Optional[str]
    floor: Optional[str]
    city: str
    district: str
    postal_code: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    additional_directions: Optional[str]
    phone_number: Optional[str]
    is_default: bool
    full_address: str
    created_at: datetime

    @staticmethod
    def resolve_latitude(obj):
        if obj.location:
            return obj.location.y
        return None

    @staticmethod
    def resolve_longitude(obj):
        if obj.location:
            return obj.location.x
        return None


# ===================================
# Wallet Schemas
# ===================================
class WalletTransactionOutSchema(Schema):
    """Schema for wallet transaction output."""
    id: UUID
    amount: Decimal
    transaction_type: str
    status: str
    description: str
    reference_id: Optional[str]
    balance_after: Decimal
    created_at: datetime


class WalletBalanceSchema(Schema):
    """Schema for wallet balance."""
    balance: Decimal
    currency: str = 'SAR'


# ===================================
# Driver Schemas
# ===================================
class DriverRegisterSchema(Schema):
    """Schema for driver registration."""
    vehicle_type: str
    vehicle_model: str
    vehicle_year: int = Field(..., ge=2015, le=2030)
    vehicle_color: str
    plate_number: str


class DriverProfileOutSchema(Schema):
    """Schema for driver profile output."""
    id: UUID
    status: str
    is_online: bool
    is_available: bool
    vehicle_type: str
    vehicle_model: str
    vehicle_year: int
    vehicle_color: str
    plate_number: str
    total_deliveries: int
    total_earnings: Decimal
    rating: Decimal
    rating_count: int
    created_at: datetime


class DriverLocationUpdateSchema(Schema):
    """Schema for updating driver location."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


# ===================================
# Vendor Schemas
# ===================================
class VendorRegisterSchema(Schema):
    """Schema for vendor registration."""
    business_name: str = Field(..., max_length=200)
    business_name_en: Optional[str] = Field(None, max_length=200)
    commercial_registration: str = Field(..., max_length=20)
    tax_number: Optional[str] = Field(None, max_length=15)


class VendorProfileOutSchema(Schema):
    """Schema for vendor profile output."""
    id: UUID
    business_name: str
    business_name_en: Optional[str]
    commercial_registration: str
    tax_number: Optional[str]
    status: str
    commission_rate: Decimal
    total_sales: Decimal
    total_orders: int
    created_at: datetime


# ===================================
# Common Response Schemas
# ===================================
class MessageSchema(Schema):
    """Simple message response."""
    message: str
    success: bool = True


class ErrorSchema(Schema):
    """Error response schema."""
    message: str
    code: Optional[str] = None
    details: Optional[dict] = None
