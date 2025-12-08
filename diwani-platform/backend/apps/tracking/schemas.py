"""
مخططات نظام التتبع
===================

Pydantic schemas للتحقق من البيانات
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from ninja import Schema
from pydantic import Field, field_validator


# =============================================
# Location Schemas
# =============================================

class LocationSchema(Schema):
    """موقع جغرافي"""
    latitude: float = Field(..., ge=-90, le=90, description="خط العرض")
    longitude: float = Field(..., ge=-180, le=180, description="خط الطول")
    altitude: Optional[float] = Field(None, description="الارتفاع بالمتر")
    accuracy: Optional[float] = Field(None, ge=0, description="الدقة بالمتر")


class LocationUpdateSchema(Schema):
    """تحديث الموقع"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    speed: float = Field(0, ge=0, description="السرعة بالكم/س")
    heading: float = Field(0, ge=0, le=360, description="الاتجاه بالدرجات")
    accuracy: Optional[float] = Field(None, ge=0)
    altitude: Optional[float] = None
    battery_level: Optional[int] = Field(None, ge=0, le=100)
    timestamp: Optional[datetime] = None


class AddressSchema(Schema):
    """العنوان"""
    address: str = Field(..., min_length=5, max_length=500)
    city: Optional[str] = None
    district: Optional[str] = None
    postal_code: Optional[str] = None
    location: LocationSchema
    contact_name: str = Field(..., min_length=2, max_length=100)
    contact_phone: str = Field(..., pattern=r'^\+?[0-9]{9,15}$')
    notes: Optional[str] = Field(None, max_length=500)


# =============================================
# Delivery Schemas
# =============================================

class DeliveryCreateSchema(Schema):
    """إنشاء توصيل جديد"""
    order_id: UUID
    delivery_type: str = Field('standard', pattern='^(standard|express|same_day|scheduled|pickup)$')
    vehicle_type: Optional[str] = None

    # الاستلام
    pickup_location: LocationSchema
    pickup_address: str
    pickup_contact_name: str
    pickup_contact_phone: str
    pickup_notes: Optional[str] = None

    # التسليم
    dropoff_location: LocationSchema
    dropoff_address: str
    dropoff_contact_name: str
    dropoff_contact_phone: str
    dropoff_notes: Optional[str] = None

    # الجدولة
    scheduled_time: Optional[datetime] = None

    # إضافي
    special_instructions: Optional[str] = None
    package_description: Optional[str] = None
    package_weight_kg: Optional[Decimal] = None
    requires_signature: bool = False
    requires_photo: bool = True
    priority: int = Field(0, ge=0, le=10)
    is_urgent: bool = False


class DeliveryUpdateSchema(Schema):
    """تحديث توصيل"""
    status: Optional[str] = None
    driver_id: Optional[UUID] = None
    scheduled_time: Optional[datetime] = None
    special_instructions: Optional[str] = None
    priority: Optional[int] = Field(None, ge=0, le=10)


class DeliveryAssignSchema(Schema):
    """تعيين سائق"""
    driver_id: UUID
    estimated_pickup_time: Optional[datetime] = None


class DeliveryStatusUpdateSchema(Schema):
    """تحديث حالة التوصيل"""
    status: str = Field(..., pattern='^(accepted|picking_up|at_pickup|picked_up|in_transit|near_destination|arrived|delivered|failed|cancelled)$')
    location: Optional[LocationSchema] = None
    notes: Optional[str] = None


class DeliveryCompleteSchema(Schema):
    """إتمام التوصيل"""
    verification_code: Optional[str] = Field(None, pattern='^[0-9]{6}$')
    signature_base64: Optional[str] = None
    photo_base64: Optional[str] = None
    notes: Optional[str] = None


class DeliveryFailSchema(Schema):
    """فشل التوصيل"""
    reason: str = Field(..., min_length=10, max_length=500)
    location: Optional[LocationSchema] = None


class DeliveryCancelSchema(Schema):
    """إلغاء التوصيل"""
    reason: str = Field(..., min_length=10, max_length=500)


class DeliveryRatingSchema(Schema):
    """تقييم التوصيل"""
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = Field(None, max_length=1000)


# =============================================
# Response Schemas
# =============================================

class TrackingPointResponseSchema(Schema):
    """نقطة تتبع"""
    id: UUID
    latitude: float
    longitude: float
    speed: float
    heading: float
    status: str
    recorded_at: datetime


class DeliveryEventResponseSchema(Schema):
    """حدث توصيل"""
    id: UUID
    event_type: str
    title: str
    description: str
    old_status: Optional[str]
    new_status: Optional[str]
    occurred_at: datetime
    actor_type: str


class ETAResponseSchema(Schema):
    """وقت الوصول المتوقع"""
    minutes: int
    estimated_arrival: datetime
    distance_remaining_km: float
    confidence: float = Field(..., ge=0, le=1)


class DeliveryResponseSchema(Schema):
    """استجابة التوصيل"""
    id: UUID
    order_id: UUID
    driver_id: Optional[UUID]

    # النوع والحالة
    delivery_type: str
    vehicle_type: Optional[str]
    status: str

    # الاستلام
    pickup_address: str
    pickup_contact_name: str
    pickup_location: Dict[str, float]

    # التسليم
    dropoff_address: str
    dropoff_contact_name: str
    dropoff_location: Dict[str, float]

    # الموقع الحالي
    current_location: Optional[Dict[str, float]]
    current_speed: float

    # المسافات
    total_distance_km: float
    distance_traveled_km: float
    distance_remaining_km: float

    # الأوقات
    estimated_pickup_time: Optional[datetime]
    actual_pickup_time: Optional[datetime]
    estimated_delivery_time: Optional[datetime]
    actual_delivery_time: Optional[datetime]
    eta_minutes: Optional[int]

    # التكاليف
    delivery_fee: Decimal

    # الحالة
    is_active: bool
    is_completed: bool
    delivery_attempts: int

    # التقييم
    customer_rating: Optional[int]

    # التواريخ
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DeliveryListResponseSchema(Schema):
    """قائمة التوصيلات"""
    items: List[DeliveryResponseSchema]
    total: int
    page: int
    page_size: int
    total_pages: int


class DeliveryTrackingResponseSchema(Schema):
    """تتبع التوصيل"""
    delivery: DeliveryResponseSchema
    tracking_points: List[TrackingPointResponseSchema]
    events: List[DeliveryEventResponseSchema]
    eta: Optional[ETAResponseSchema]


# =============================================
# Driver Location Schemas
# =============================================

class DriverLocationSchema(Schema):
    """موقع السائق"""
    driver_id: UUID
    latitude: float
    longitude: float
    speed: float
    heading: float
    is_online: bool
    is_available: bool
    is_on_delivery: bool
    current_delivery_id: Optional[UUID]
    last_update: datetime
    battery_level: Optional[int]


class DriverAvailabilitySchema(Schema):
    """تحديث توفر السائق"""
    is_available: bool


class DriverOnlineStatusSchema(Schema):
    """تحديث حالة الاتصال"""
    is_online: bool


class NearbyDriverSchema(Schema):
    """سائق قريب"""
    driver_id: UUID
    driver_name: str
    distance_km: float
    eta_minutes: int
    rating: float
    vehicle_type: Optional[str]
    is_available: bool


class NearbyDriversResponseSchema(Schema):
    """السائقين القريبين"""
    drivers: List[NearbyDriverSchema]
    total: int


# =============================================
# Geofence Schemas
# =============================================

class GeofenceCreateSchema(Schema):
    """إنشاء سياج جغرافي"""
    name: str = Field(..., min_length=2, max_length=100)
    geofence_type: str = Field(..., pattern='^(pickup|dropoff|zone|restricted)$')
    center: LocationSchema
    radius_meters: int = Field(100, ge=10, le=10000)
    trigger_on_enter: bool = True
    trigger_on_exit: bool = True


class GeofenceEventSchema(Schema):
    """حدث السياج الجغرافي"""
    geofence_id: UUID
    geofence_name: str
    event_type: str  # enter, exit
    driver_id: UUID
    delivery_id: Optional[UUID]
    location: LocationSchema
    occurred_at: datetime


# =============================================
# Statistics Schemas
# =============================================

class DeliveryStatsSchema(Schema):
    """إحصائيات التوصيل"""
    total_deliveries: int
    completed_deliveries: int
    failed_deliveries: int
    cancelled_deliveries: int
    in_progress_deliveries: int
    average_delivery_time_minutes: float
    average_rating: float
    total_distance_km: float
    total_earnings: Decimal
    period: str  # today, week, month


class DriverStatsSchema(Schema):
    """إحصائيات السائق"""
    driver_id: UUID
    total_deliveries: int
    completed_deliveries: int
    completion_rate: float
    average_rating: float
    total_distance_km: float
    total_earnings: Decimal
    average_delivery_time_minutes: float
    online_hours_today: float
