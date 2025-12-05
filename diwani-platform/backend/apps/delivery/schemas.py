"""
===================================
منصة ديواني - Delivery Schemas
Pydantic schemas for Delivery APIs
===================================
"""

from typing import Optional, List
from datetime import datetime, time
from decimal import Decimal
from uuid import UUID

from ninja import Schema, Field


# ===================================
# Delivery Zone Schemas
# ===================================
class DeliveryZoneOutSchema(Schema):
    """Schema for delivery zone output."""
    id: UUID
    name: str
    name_en: str
    city: str
    districts: list
    base_delivery_fee: Decimal
    per_km_fee: Decimal
    estimated_delivery_time: int
    is_available: bool


class DeliveryFeeCalculationSchema(Schema):
    """Schema for delivery fee calculation request."""
    pickup_latitude: float = Field(..., ge=-90, le=90)
    pickup_longitude: float = Field(..., ge=-180, le=180)
    delivery_latitude: float = Field(..., ge=-90, le=90)
    delivery_longitude: float = Field(..., ge=-180, le=180)


class DeliveryFeeResponseSchema(Schema):
    """Schema for delivery fee calculation response."""
    distance_km: Decimal
    delivery_fee: Decimal
    estimated_time_minutes: int
    is_available: bool
    message: str


# ===================================
# Delivery Request Schemas
# ===================================
class DeliveryRequestOutSchema(Schema):
    """Schema for delivery request output."""
    id: UUID
    delivery_number: str
    order_id: Optional[UUID]
    order_number: str
    status: str
    status_display: str
    driver_id: Optional[UUID]
    driver_name: str
    driver_phone: str
    driver_rating: Optional[Decimal]
    pickup_address: str
    pickup_latitude: Optional[float]
    pickup_longitude: Optional[float]
    pickup_contact_name: str
    pickup_contact_phone: str
    delivery_address: str
    delivery_latitude: Optional[float]
    delivery_longitude: Optional[float]
    delivery_contact_name: str
    delivery_contact_phone: str
    distance_km: Optional[Decimal]
    estimated_duration: Optional[int]
    actual_duration: Optional[int]
    delivery_fee: Decimal
    delivery_notes: str
    customer_rating: Optional[int]
    created_at: datetime
    assigned_at: Optional[datetime]
    picked_up_at: Optional[datetime]
    delivered_at: Optional[datetime]

    @staticmethod
    def resolve_status_display(obj):
        return obj.get_status_display()

    @staticmethod
    def resolve_order_number(obj):
        return obj.order.order_number if obj.order else ''

    @staticmethod
    def resolve_driver_name(obj):
        return obj.driver.full_name if obj.driver else ''

    @staticmethod
    def resolve_driver_phone(obj):
        return obj.driver.phone_number if obj.driver else ''

    @staticmethod
    def resolve_driver_rating(obj):
        if obj.driver and hasattr(obj.driver, 'driver_profile'):
            return obj.driver.driver_profile.rating
        return None

    @staticmethod
    def resolve_pickup_latitude(obj):
        return obj.pickup_location.y if obj.pickup_location else None

    @staticmethod
    def resolve_pickup_longitude(obj):
        return obj.pickup_location.x if obj.pickup_location else None

    @staticmethod
    def resolve_delivery_latitude(obj):
        return obj.delivery_location.y if obj.delivery_location else None

    @staticmethod
    def resolve_delivery_longitude(obj):
        return obj.delivery_location.x if obj.delivery_location else None


class DeliveryRequestListSchema(Schema):
    """Schema for delivery request listing."""
    id: UUID
    delivery_number: str
    order_number: str
    status: str
    status_display: str
    driver_name: str
    delivery_address: str
    estimated_duration: Optional[int]
    created_at: datetime

    @staticmethod
    def resolve_status_display(obj):
        return obj.get_status_display()

    @staticmethod
    def resolve_order_number(obj):
        return obj.order.order_number if obj.order else ''

    @staticmethod
    def resolve_driver_name(obj):
        return obj.driver.full_name if obj.driver else 'غير محدد'


# ===================================
# Driver Location Schemas
# ===================================
class DriverLocationUpdateSchema(Schema):
    """Schema for updating driver location."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    speed: Optional[float] = None
    heading: Optional[float] = None
    accuracy: Optional[float] = None


class DriverLocationOutSchema(Schema):
    """Schema for driver location output."""
    driver_id: UUID
    driver_name: str
    latitude: float
    longitude: float
    speed: Optional[float]
    heading: Optional[float]
    last_updated: datetime
    is_online: bool

    @staticmethod
    def resolve_latitude(obj):
        return obj.location.y if obj.location else None

    @staticmethod
    def resolve_longitude(obj):
        return obj.location.x if obj.location else None


# ===================================
# Driver Delivery Schemas
# ===================================
class AvailableDeliverySchema(Schema):
    """Schema for available delivery for drivers."""
    id: UUID
    delivery_number: str
    pickup_address: str
    delivery_address: str
    distance_km: Optional[Decimal]
    estimated_duration: Optional[int]
    delivery_fee: Decimal
    driver_earnings: Decimal
    distance_to_pickup_km: Optional[float]
    pickup_contact_name: str
    created_at: datetime


class AcceptDeliverySchema(Schema):
    """Schema for accepting a delivery."""
    delivery_id: UUID


class RejectDeliverySchema(Schema):
    """Schema for rejecting a delivery."""
    delivery_id: UUID
    reason: str = ''


class CompleteDeliverySchema(Schema):
    """Schema for completing a delivery."""
    delivery_id: UUID
    notes: str = ''


# ===================================
# Driver Earnings Schemas
# ===================================
class EarningOutSchema(Schema):
    """Schema for earning output."""
    id: UUID
    delivery_number: Optional[str]
    earning_type: str
    amount: Decimal
    description: str
    is_settled: bool
    created_at: datetime

    @staticmethod
    def resolve_delivery_number(obj):
        return obj.delivery_request.delivery_number if obj.delivery_request else None


class EarningsSummarySchema(Schema):
    """Schema for earnings summary."""
    today_earnings: Decimal
    today_deliveries: int
    week_earnings: Decimal
    week_deliveries: int
    month_earnings: Decimal
    month_deliveries: int
    total_earnings: Decimal
    total_deliveries: int
    pending_settlement: Decimal
    average_rating: Optional[Decimal]


# ===================================
# Driver Availability Schemas
# ===================================
class DriverAvailabilitySchema(Schema):
    """Schema for driver availability."""
    weekday: int = Field(..., ge=0, le=6)
    start_time: time
    end_time: time
    is_available: bool = True


class DriverAvailabilityOutSchema(Schema):
    """Schema for driver availability output."""
    id: UUID
    weekday: int
    weekday_name: str
    start_time: time
    end_time: time
    is_available: bool

    @staticmethod
    def resolve_weekday_name(obj):
        days = ['الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت']
        return days[obj.weekday]


# ===================================
# Tracking Schemas
# ===================================
class DeliveryTrackingSchema(Schema):
    """Schema for delivery tracking."""
    delivery_number: str
    status: str
    status_display: str
    driver_name: str
    driver_phone: str
    driver_latitude: Optional[float]
    driver_longitude: Optional[float]
    pickup_address: str
    delivery_address: str
    estimated_arrival: Optional[int]  # minutes
    distance_remaining: Optional[float]  # km
    timeline: List[dict]


# ===================================
# Rating Schemas
# ===================================
class DeliveryRatingSchema(Schema):
    """Schema for rating a delivery."""
    rating: int = Field(..., ge=1, le=5)
    feedback: str = ''


# ===================================
# Statistics Schemas
# ===================================
class DeliveryStatsSchema(Schema):
    """Schema for delivery statistics (admin)."""
    total_deliveries: int
    completed_deliveries: int
    cancelled_deliveries: int
    average_delivery_time: Optional[int]
    average_rating: Optional[Decimal]
    total_distance_km: Decimal
    total_earnings: Decimal
    by_status: dict
    by_zone: dict


class DriverStatsSchema(Schema):
    """Schema for driver statistics."""
    driver_id: UUID
    driver_name: str
    total_deliveries: int
    completed_deliveries: int
    average_rating: Optional[Decimal]
    total_earnings: Decimal
    average_delivery_time: Optional[int]
    acceptance_rate: float
    is_online: bool


# ===================================
# Pagination Schemas
# ===================================
class PaginatedDeliverySchema(Schema):
    """Schema for paginated deliveries."""
    items: List[DeliveryRequestListSchema]
    total: int
    page: int
    page_size: int
    pages: int


class PaginatedEarningsSchema(Schema):
    """Schema for paginated earnings."""
    items: List[EarningOutSchema]
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
