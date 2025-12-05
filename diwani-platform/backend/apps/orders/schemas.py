"""
===================================
منصة ديواني - Orders Schemas
Pydantic schemas for Orders APIs
===================================
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ninja import Schema, Field


# ===================================
# Cart Item Addon Schemas
# ===================================
class CartItemAddonSchema(Schema):
    """Schema for cart item addon."""
    addon_id: UUID
    quantity: int = 1


class CartItemAddonOutSchema(Schema):
    """Schema for cart item addon output."""
    id: UUID
    addon_id: UUID
    addon_name: str
    addon_name_en: str
    price: Decimal
    quantity: int

    @staticmethod
    def resolve_addon_name(obj):
        return obj.addon.name if obj.addon else ''

    @staticmethod
    def resolve_addon_name_en(obj):
        return obj.addon.name_en if obj.addon else ''


# ===================================
# Cart Item Schemas
# ===================================
class CartItemCreateSchema(Schema):
    """Schema for adding item to cart."""
    product_id: UUID
    variant_id: Optional[UUID] = None
    quantity: int = Field(1, ge=1)
    notes: str = ''
    addons: List[CartItemAddonSchema] = []


class CartItemUpdateSchema(Schema):
    """Schema for updating cart item."""
    quantity: Optional[int] = Field(None, ge=1)
    notes: Optional[str] = None


class CartItemOutSchema(Schema):
    """Schema for cart item output."""
    id: UUID
    product_id: UUID
    product_name: str
    product_name_en: str
    product_image: Optional[str]
    variant_id: Optional[UUID]
    variant_name: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    notes: str
    addons: List[CartItemAddonOutSchema]

    @staticmethod
    def resolve_product_name(obj):
        return obj.product.name if obj.product else ''

    @staticmethod
    def resolve_product_name_en(obj):
        return obj.product.name_en if obj.product else ''

    @staticmethod
    def resolve_product_image(obj):
        if obj.product and obj.product.image:
            return obj.product.image.url
        return None

    @staticmethod
    def resolve_variant_name(obj):
        return obj.variant.name if obj.variant else ''


# ===================================
# Cart Schemas
# ===================================
class CartOutSchema(Schema):
    """Schema for cart output."""
    id: UUID
    store_id: UUID
    store_name: str
    store_logo: Optional[str]
    items: List[CartItemOutSchema]
    items_count: int
    subtotal: Decimal
    delivery_fee: Decimal
    total: Decimal
    min_order_amount: Decimal
    is_minimum_met: bool

    @staticmethod
    def resolve_store_name(obj):
        return obj.store.name if obj.store else ''

    @staticmethod
    def resolve_store_logo(obj):
        if obj.store and obj.store.logo:
            return obj.store.logo.url
        return None

    @staticmethod
    def resolve_items(obj):
        return [CartItemOutSchema.from_orm(item) for item in obj.items.all()]

    @staticmethod
    def resolve_min_order_amount(obj):
        return obj.store.min_order_amount if obj.store else Decimal('0')

    @staticmethod
    def resolve_is_minimum_met(obj):
        if obj.store:
            return obj.subtotal >= obj.store.min_order_amount
        return True


# ===================================
# Coupon Schemas
# ===================================
class CouponApplySchema(Schema):
    """Schema for applying coupon."""
    code: str


class CouponOutSchema(Schema):
    """Schema for coupon output."""
    id: UUID
    code: str
    description: str
    discount_type: str
    discount_value: Decimal
    min_order_amount: Decimal
    max_discount_amount: Optional[Decimal]
    is_valid: bool


class CouponValidationSchema(Schema):
    """Schema for coupon validation result."""
    is_valid: bool
    coupon: Optional[CouponOutSchema]
    discount_amount: Decimal
    message: str


# ===================================
# Order Item Addon Schemas
# ===================================
class OrderItemAddonOutSchema(Schema):
    """Schema for order item addon output."""
    id: UUID
    addon_name: str
    addon_name_en: str
    quantity: int
    price: Decimal


# ===================================
# Order Item Schemas
# ===================================
class OrderItemOutSchema(Schema):
    """Schema for order item output."""
    id: UUID
    product_id: Optional[UUID]
    product_name: str
    product_name_en: str
    variant_name: str
    quantity: int
    unit_price: Decimal
    addons_total: Decimal
    total_price: Decimal
    notes: str
    addons: List[OrderItemAddonOutSchema]

    @staticmethod
    def resolve_addons(obj):
        return [OrderItemAddonOutSchema.from_orm(a) for a in obj.addons.all()]


# ===================================
# Order Schemas
# ===================================
class OrderCreateSchema(Schema):
    """Schema for creating an order (checkout)."""
    cart_id: UUID
    delivery_type: str = 'delivery'  # delivery or pickup
    delivery_address_id: Optional[UUID] = None
    payment_method: str = 'cash'  # cash, card, mada, apple_pay, wallet
    coupon_code: Optional[str] = None
    customer_notes: str = ''
    tip_amount: Decimal = Decimal('0')
    scheduled_time: Optional[datetime] = None  # For scheduled orders


class OrderOutSchema(Schema):
    """Schema for order output (full details)."""
    id: UUID
    order_number: str
    status: str
    status_display: str
    payment_status: str
    payment_status_display: str
    payment_method: str
    delivery_type: str
    store_id: Optional[UUID]
    store_name: str
    store_logo: Optional[str]
    store_phone: str
    customer_name: str
    delivery_address_text: str
    delivery_latitude: Optional[float]
    delivery_longitude: Optional[float]
    driver_name: Optional[str]
    driver_phone: Optional[str]
    subtotal: Decimal
    delivery_fee: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    tip_amount: Decimal
    total: Decimal
    coupon_code: Optional[str]
    customer_notes: str
    estimated_preparation_time: Optional[int]
    estimated_delivery_time: Optional[int]
    items: List[OrderItemOutSchema]
    placed_at: datetime
    confirmed_at: Optional[datetime]
    preparing_at: Optional[datetime]
    ready_at: Optional[datetime]
    picked_up_at: Optional[datetime]
    delivered_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    cancellation_reason: str
    is_rated: bool

    @staticmethod
    def resolve_status_display(obj):
        return obj.get_status_display()

    @staticmethod
    def resolve_payment_status_display(obj):
        return obj.get_payment_status_display()

    @staticmethod
    def resolve_store_name(obj):
        return obj.store.name if obj.store else ''

    @staticmethod
    def resolve_store_logo(obj):
        if obj.store and obj.store.logo:
            return obj.store.logo.url
        return None

    @staticmethod
    def resolve_store_phone(obj):
        return obj.store.phone_number if obj.store else ''

    @staticmethod
    def resolve_customer_name(obj):
        return obj.customer.full_name if obj.customer else ''

    @staticmethod
    def resolve_delivery_latitude(obj):
        if obj.delivery_location:
            return obj.delivery_location.y
        return None

    @staticmethod
    def resolve_delivery_longitude(obj):
        if obj.delivery_location:
            return obj.delivery_location.x
        return None

    @staticmethod
    def resolve_driver_name(obj):
        return obj.driver.full_name if obj.driver else None

    @staticmethod
    def resolve_driver_phone(obj):
        return obj.driver.phone_number if obj.driver else None

    @staticmethod
    def resolve_coupon_code(obj):
        return obj.coupon.code if obj.coupon else None

    @staticmethod
    def resolve_items(obj):
        return [OrderItemOutSchema.from_orm(item) for item in obj.items.all()]


class OrderListSchema(Schema):
    """Schema for order listing (minimal)."""
    id: UUID
    order_number: str
    status: str
    status_display: str
    store_name: str
    store_logo: Optional[str]
    items_count: int
    total: Decimal
    placed_at: datetime

    @staticmethod
    def resolve_status_display(obj):
        return obj.get_status_display()

    @staticmethod
    def resolve_store_name(obj):
        return obj.store.name if obj.store else ''

    @staticmethod
    def resolve_store_logo(obj):
        if obj.store and obj.store.logo:
            return obj.store.logo.url
        return None

    @staticmethod
    def resolve_items_count(obj):
        return obj.items.count()


# ===================================
# Order Status Update Schemas
# ===================================
class OrderStatusUpdateSchema(Schema):
    """Schema for updating order status (by store)."""
    status: str
    notes: str = ''
    estimated_time: Optional[int] = None  # Minutes


class OrderCancelSchema(Schema):
    """Schema for cancelling order."""
    reason: str = ''


# ===================================
# Order Status History Schemas
# ===================================
class OrderStatusHistoryOutSchema(Schema):
    """Schema for order status history output."""
    id: UUID
    status: str
    status_display: str
    notes: str
    changed_by_name: str
    created_at: datetime

    @staticmethod
    def resolve_status_display(obj):
        from .models import Order
        return dict(Order.OrderStatus.choices).get(obj.status, obj.status)

    @staticmethod
    def resolve_changed_by_name(obj):
        return obj.changed_by.full_name if obj.changed_by else 'النظام'


# ===================================
# Checkout Summary Schemas
# ===================================
class CheckoutSummarySchema(Schema):
    """Schema for checkout summary."""
    cart: CartOutSchema
    delivery_fee: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    tip_amount: Decimal
    subtotal: Decimal
    total: Decimal
    coupon: Optional[CouponOutSchema]
    payment_methods: List[dict]
    estimated_delivery_time: int


# ===================================
# Pagination Schemas
# ===================================
class PaginatedOrderSchema(Schema):
    """Schema for paginated order response."""
    items: List[OrderListSchema]
    total: int
    page: int
    page_size: int
    pages: int


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
