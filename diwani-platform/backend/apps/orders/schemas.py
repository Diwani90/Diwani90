"""
Schemas نظام الطلبات
===================

Django Ninja Schemas للطلبات
"""

from datetime import date, datetime, time
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from ninja import Schema, Field


# =============================================
# عناصر الطلب
# =============================================

class OrderItemSchema(Schema):
    """عنصر طلب"""
    id: UUID
    product_id: UUID
    product_name: str
    product_name_en: Optional[str]
    product_image: Optional[str]
    variant_id: Optional[UUID]
    variant_name: Optional[str]
    sku: Optional[str]
    unit_price: Decimal
    quantity: Decimal
    discount: Decimal
    options_price: Decimal
    total_price: Decimal
    selected_options: Dict[str, Any]
    pricing_type: str
    rental_days: int
    rental_hours: int
    is_available: bool
    availability_note: Optional[str]

    @staticmethod
    def resolve_product_name(obj):
        return obj.product_snapshot.get('name', obj.product.name if obj.product else '')

    @staticmethod
    def resolve_product_name_en(obj):
        return obj.product_snapshot.get('name_en', '')

    @staticmethod
    def resolve_product_image(obj):
        return obj.product_snapshot.get('image', '')

    @staticmethod
    def resolve_sku(obj):
        return obj.product_snapshot.get('sku', '')

    @staticmethod
    def resolve_variant_name(obj):
        return obj.variant.name if obj.variant else None


class OrderItemCreateSchema(Schema):
    """إنشاء عنصر طلب"""
    product_id: UUID
    variant_id: Optional[UUID] = None
    quantity: float = 1
    selected_options: Optional[Dict[str, str]] = None
    rental_days: int = 0
    rental_hours: int = 0
    service_details: Optional[Dict[str, Any]] = None


class OrderItemUpdateSchema(Schema):
    """تحديث عنصر طلب"""
    quantity: Optional[float] = None
    selected_options: Optional[Dict[str, str]] = None


# =============================================
# معلومات التوصيل
# =============================================

class DeliveryInfoSchema(Schema):
    """معلومات التوصيل"""
    id: UUID
    status: str
    driver_id: Optional[UUID]
    driver_name: Optional[str]
    driver_phone: Optional[str]
    tracking_number: Optional[str]
    current_latitude: Optional[float]
    current_longitude: Optional[float]
    estimated_distance_km: Optional[Decimal]
    estimated_duration_minutes: Optional[int]
    assigned_at: Optional[datetime]
    picked_up_at: Optional[datetime]
    delivered_at: Optional[datetime]
    delivery_photo: Optional[str]
    recipient_name: Optional[str]
    attempts: int

    @staticmethod
    def resolve_driver_name(obj):
        return obj.driver.get_full_name() if obj.driver else None

    @staticmethod
    def resolve_driver_phone(obj):
        return obj.driver.phone_number if obj.driver else None

    @staticmethod
    def resolve_current_latitude(obj):
        return obj.current_location.y if obj.current_location else None

    @staticmethod
    def resolve_current_longitude(obj):
        return obj.current_location.x if obj.current_location else None


class DeliveryAddressSchema(Schema):
    """عنوان التوصيل"""
    id: UUID
    label: Optional[str]
    street_address: str
    building_number: Optional[str]
    city: str
    district: Optional[str]
    latitude: Optional[Decimal]
    longitude: Optional[Decimal]
    contact_name: Optional[str]
    contact_phone: Optional[str]


# =============================================
# الطلب
# =============================================

class OrderSchema(Schema):
    """الطلب الكامل"""
    id: UUID
    order_number: str
    order_type: str
    status: str
    payment_status: str
    payment_method: Optional[str]

    # الأطراف
    customer_id: UUID
    customer_name: str
    vendor_id: UUID
    vendor_name: str

    # المبالغ
    subtotal: Decimal
    delivery_fee: Decimal
    service_fee: Decimal
    discount_amount: Decimal
    coupon_discount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal

    # التوصيل
    delivery_type: str
    delivery_notes: Optional[str]
    scheduled_delivery_date: Optional[date]
    scheduled_delivery_time: Optional[str]

    # التوقيت
    placed_at: Optional[datetime]
    confirmed_at: Optional[datetime]
    delivered_at: Optional[datetime]
    completed_at: Optional[datetime]

    # العناصر
    items: List[OrderItemSchema]
    items_count: int

    # التوصيل
    delivery: Optional[DeliveryInfoSchema]
    delivery_address: Optional[DeliveryAddressSchema]

    created_at: datetime
    updated_at: datetime

    @staticmethod
    def resolve_customer_name(obj):
        return obj.customer.get_full_name()

    @staticmethod
    def resolve_vendor_name(obj):
        return obj.vendor.name

    @staticmethod
    def resolve_items_count(obj):
        return obj.items.count()


class OrderListSchema(Schema):
    """قائمة الطلبات"""
    id: UUID
    order_number: str
    order_type: str
    status: str
    payment_status: str
    vendor_name: str
    vendor_logo: Optional[str]
    total_amount: Decimal
    items_count: int
    first_item_image: Optional[str]
    created_at: datetime

    @staticmethod
    def resolve_vendor_name(obj):
        return obj.vendor.name

    @staticmethod
    def resolve_vendor_logo(obj):
        return obj.vendor.logo.url if obj.vendor.logo else None

    @staticmethod
    def resolve_items_count(obj):
        return obj.items.count()

    @staticmethod
    def resolve_first_item_image(obj):
        first_item = obj.items.first()
        if first_item:
            return first_item.product_snapshot.get('image', '')
        return None


class OrderDetailSchema(OrderSchema):
    """تفاصيل الطلب الكاملة"""
    previous_status: Optional[str]
    status_changed_at: datetime

    # العمولات (للتاجر)
    vendor_commission: Decimal
    platform_commission: Decimal

    # الكوبون
    coupon_code: Optional[str]

    # الملاحظات
    customer_notes: Optional[str]
    vendor_notes: Optional[str]

    # الإلغاء
    cancellation_reason: Optional[str]
    cancellation_notes: Optional[str]
    cancelled_at: Optional[datetime]

    # للخدمات
    service_date: Optional[date]
    service_time: Optional[time]
    rental_start_date: Optional[date]
    rental_end_date: Optional[date]

    # سجل الحالات
    status_history: List['OrderStatusHistorySchema']

    @staticmethod
    def resolve_status_history(obj):
        return obj.status_history.all()[:20]


# =============================================
# إنشاء الطلب
# =============================================

class OrderCreateSchema(Schema):
    """إنشاء طلب جديد"""
    vendor_id: UUID
    items: List[OrderItemCreateSchema]
    delivery_address_id: Optional[UUID] = None
    delivery_type: str = 'standard'
    delivery_notes: Optional[str] = None
    scheduled_delivery_date: Optional[date] = None
    scheduled_delivery_time: Optional[str] = None
    payment_method: str = 'card'
    coupon_code: Optional[str] = None
    customer_notes: Optional[str] = None

    # للخدمات
    service_date: Optional[date] = None
    service_time: Optional[time] = None

    # للتأجير
    rental_start_date: Optional[date] = None
    rental_end_date: Optional[date] = None


class OrderUpdateSchema(Schema):
    """تحديث الطلب"""
    delivery_notes: Optional[str] = None
    scheduled_delivery_date: Optional[date] = None
    scheduled_delivery_time: Optional[str] = None
    customer_notes: Optional[str] = None


# =============================================
# سجل الحالات
# =============================================

class OrderStatusHistorySchema(Schema):
    """سجل تغيير الحالة"""
    id: UUID
    status: str
    previous_status: Optional[str]
    changed_by_name: Optional[str]
    notes: Optional[str]
    created_at: datetime

    @staticmethod
    def resolve_changed_by_name(obj):
        return obj.changed_by.get_full_name() if obj.changed_by else None


# =============================================
# تحديث الحالة
# =============================================

class OrderStatusUpdateSchema(Schema):
    """تحديث حالة الطلب"""
    status: str
    notes: Optional[str] = None


class OrderCancelSchema(Schema):
    """إلغاء الطلب"""
    reason: str
    notes: Optional[str] = None


# =============================================
# التقييمات
# =============================================

class OrderReviewSchema(Schema):
    """تقييم الطلب"""
    id: UUID
    vendor_rating: int
    vendor_comment: Optional[str]
    products_rating: Optional[int]
    products_comment: Optional[str]
    delivery_rating: Optional[int]
    delivery_comment: Optional[str]
    overall_rating: float
    images: List[str]
    vendor_response: Optional[str]
    vendor_responded_at: Optional[datetime]
    is_anonymous: bool
    created_at: datetime


class OrderReviewCreateSchema(Schema):
    """إنشاء تقييم"""
    vendor_rating: int = Field(..., ge=1, le=5)
    vendor_comment: Optional[str] = None
    products_rating: Optional[int] = Field(None, ge=1, le=5)
    products_comment: Optional[str] = None
    delivery_rating: Optional[int] = Field(None, ge=1, le=5)
    delivery_comment: Optional[str] = None
    is_anonymous: bool = False


class VendorResponseSchema(Schema):
    """رد التاجر على التقييم"""
    response: str


# =============================================
# الاسترداد
# =============================================

class RefundSchema(Schema):
    """طلب استرداد"""
    id: UUID
    order_id: UUID
    item_id: Optional[UUID]
    amount: Decimal
    status: str
    reason: str
    reason_details: Optional[str]
    evidence_images: List[str]
    rejection_reason: Optional[str]
    transaction_id: Optional[str]
    requested_at: datetime
    approved_at: Optional[datetime]
    completed_at: Optional[datetime]


class RefundRequestSchema(Schema):
    """طلب استرداد جديد"""
    item_id: Optional[UUID] = None
    amount: Optional[Decimal] = None  # إذا لم يُحدد، يُسترد المبلغ الكامل
    reason: str
    reason_details: Optional[str] = None


# =============================================
# التتبع
# =============================================

class TrackingPointSchema(Schema):
    """نقطة تتبع"""
    latitude: float
    longitude: float
    accuracy: Optional[float]
    speed: Optional[float]
    heading: Optional[float]
    recorded_at: datetime


class DeliveryTrackingSchema(Schema):
    """تتبع التوصيل"""
    order_id: UUID
    order_number: str
    status: str
    driver_name: Optional[str]
    driver_phone: Optional[str]
    current_location: Optional[TrackingPointSchema]
    pickup_location: Optional[TrackingPointSchema]
    destination_location: Optional[TrackingPointSchema]
    estimated_arrival: Optional[datetime]
    tracking_points: List[TrackingPointSchema]


# =============================================
# الفلترة والبحث
# =============================================

class OrderFilterSchema(Schema):
    """فلترة الطلبات"""
    status: Optional[str] = None
    payment_status: Optional[str] = None
    order_type: Optional[str] = None
    vendor_id: Optional[UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    search: Optional[str] = None


# =============================================
# إحصائيات
# =============================================

class OrderStatsSchema(Schema):
    """إحصائيات الطلبات"""
    total_orders: int
    pending_orders: int
    processing_orders: int
    completed_orders: int
    cancelled_orders: int
    total_revenue: Decimal
    average_order_value: Decimal
    total_items_sold: int


# =============================================
# سلة التسوق
# =============================================

class CartItemSchema(Schema):
    """عنصر سلة التسوق"""
    id: UUID
    product_id: UUID
    product_name: str
    product_image: Optional[str]
    variant_id: Optional[UUID]
    variant_name: Optional[str]
    unit_price: Decimal
    quantity: int
    selected_options: Dict[str, Any]
    options_price: Decimal
    total_price: Decimal
    is_available: bool


class CartSchema(Schema):
    """سلة التسوق"""
    id: UUID
    vendor_id: UUID
    vendor_name: str
    items: List[CartItemSchema]
    subtotal: Decimal
    items_count: int
    created_at: datetime
    updated_at: datetime


class AddToCartSchema(Schema):
    """إضافة للسلة"""
    product_id: UUID
    variant_id: Optional[UUID] = None
    quantity: int = 1
    selected_options: Optional[Dict[str, str]] = None


class UpdateCartItemSchema(Schema):
    """تحديث عنصر في السلة"""
    quantity: Optional[int] = None
    selected_options: Optional[Dict[str, str]] = None


# =============================================
# استجابات عامة
# =============================================

class MessageSchema(Schema):
    """رسالة عامة"""
    message: str
    success: bool = True


class OrderCreatedSchema(Schema):
    """استجابة إنشاء الطلب"""
    order_id: UUID
    order_number: str
    payment_url: Optional[str] = None
    message: str


# Fix forward references
OrderDetailSchema.update_forward_refs()
