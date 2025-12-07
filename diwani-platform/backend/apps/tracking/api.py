"""
واجهة API لنظام التتبع
======================

تتضمن:
- إدارة التوصيلات
- تتبع المواقع في الوقت الحقيقي
- إدارة السائقين
- الإحصائيات
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.db import transaction
from django.db.models import Avg, Count, Sum, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import Router, Query
from ninja.pagination import paginate, PageNumberPagination

from apps.core.auth import AuthBearer, get_current_user
from apps.users.models import User

from .models import (
    Delivery, DeliveryStatus, DeliveryType, DeliveryEvent,
    DeliveryTrackingPoint, DriverLocation, Geofence,
    TrackingEventType, VehicleType
)
from .schemas import (
    DeliveryCreateSchema, DeliveryUpdateSchema, DeliveryAssignSchema,
    DeliveryStatusUpdateSchema, DeliveryCompleteSchema, DeliveryFailSchema,
    DeliveryCancelSchema, DeliveryRatingSchema, DeliveryResponseSchema,
    DeliveryListResponseSchema, DeliveryTrackingResponseSchema,
    LocationUpdateSchema, DriverLocationSchema, DriverAvailabilitySchema,
    DriverOnlineStatusSchema, NearbyDriversResponseSchema, NearbyDriverSchema,
    GeofenceCreateSchema, DeliveryStatsSchema, DriverStatsSchema,
    TrackingPointResponseSchema, DeliveryEventResponseSchema, ETAResponseSchema
)
from .services import get_tracking_service, GeoPoint

logger = logging.getLogger(__name__)
router = Router(tags=["التتبع"])


# =============================================
# Helper Functions
# =============================================

def delivery_to_response(delivery: Delivery) -> dict:
    """تحويل التوصيل لاستجابة API"""
    return {
        'id': delivery.id,
        'order_id': delivery.order_id,
        'driver_id': delivery.driver_id,
        'delivery_type': delivery.delivery_type,
        'vehicle_type': delivery.vehicle_type,
        'status': delivery.status,
        'pickup_address': delivery.pickup_address,
        'pickup_contact_name': delivery.pickup_contact_name,
        'pickup_location': {
            'lat': delivery.pickup_location.y,
            'lng': delivery.pickup_location.x
        },
        'dropoff_address': delivery.dropoff_address,
        'dropoff_contact_name': delivery.dropoff_contact_name,
        'dropoff_location': {
            'lat': delivery.dropoff_location.y,
            'lng': delivery.dropoff_location.x
        },
        'current_location': {
            'lat': delivery.current_location.y,
            'lng': delivery.current_location.x
        } if delivery.current_location else None,
        'current_speed': float(delivery.current_speed),
        'total_distance_km': float(delivery.total_distance_km),
        'distance_traveled_km': float(delivery.distance_traveled_km),
        'distance_remaining_km': float(delivery.distance_remaining_km),
        'estimated_pickup_time': delivery.estimated_pickup_time,
        'actual_pickup_time': delivery.actual_pickup_time,
        'estimated_delivery_time': delivery.estimated_delivery_time,
        'actual_delivery_time': delivery.actual_delivery_time,
        'eta_minutes': delivery.eta_minutes,
        'delivery_fee': delivery.delivery_fee,
        'is_active': delivery.is_active,
        'is_completed': delivery.is_completed,
        'delivery_attempts': delivery.delivery_attempts,
        'customer_rating': delivery.customer_rating,
        'created_at': delivery.created_at,
        'updated_at': delivery.updated_at,
    }


# =============================================
# Delivery Endpoints
# =============================================

@router.post("/deliveries", response={201: DeliveryResponseSchema}, auth=AuthBearer())
def create_delivery(request, payload: DeliveryCreateSchema):
    """إنشاء توصيل جديد"""
    user = get_current_user(request)

    delivery = Delivery.objects.create(
        order_id=payload.order_id,
        delivery_type=payload.delivery_type,
        vehicle_type=payload.vehicle_type,
        pickup_location=Point(
            payload.pickup_location.longitude,
            payload.pickup_location.latitude,
            srid=4326
        ),
        pickup_address=payload.pickup_address,
        pickup_contact_name=payload.pickup_contact_name,
        pickup_contact_phone=payload.pickup_contact_phone,
        pickup_notes=payload.pickup_notes or '',
        dropoff_location=Point(
            payload.dropoff_location.longitude,
            payload.dropoff_location.latitude,
            srid=4326
        ),
        dropoff_address=payload.dropoff_address,
        dropoff_contact_name=payload.dropoff_contact_name,
        dropoff_contact_phone=payload.dropoff_contact_phone,
        dropoff_notes=payload.dropoff_notes or '',
        scheduled_time=payload.scheduled_time,
        special_instructions=payload.special_instructions or '',
        package_description=payload.package_description or '',
        package_weight_kg=payload.package_weight_kg,
        requires_signature=payload.requires_signature,
        requires_photo=payload.requires_photo,
        priority=payload.priority,
        is_urgent=payload.is_urgent,
    )

    # إنشاء حدث الإنشاء
    DeliveryEvent.objects.create(
        delivery=delivery,
        event_type=TrackingEventType.STATUS_CHANGE,
        title='تم إنشاء التوصيل',
        description='تم إنشاء طلب توصيل جديد',
        new_status=DeliveryStatus.PENDING,
        actor=user,
        actor_type='system',
        occurred_at=timezone.now()
    )

    return 201, delivery_to_response(delivery)


@router.get("/deliveries", response=DeliveryListResponseSchema, auth=AuthBearer())
def list_deliveries(
    request,
    status: Optional[str] = None,
    delivery_type: Optional[str] = None,
    driver_id: Optional[UUID] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """قائمة التوصيلات"""
    user = get_current_user(request)
    queryset = Delivery.objects.all()

    # فلترة حسب الدور
    if user.user_type == 'driver':
        queryset = queryset.filter(driver=user)
    elif user.user_type == 'vendor':
        queryset = queryset.filter(order__vendor__owner=user)
    elif user.user_type == 'customer':
        queryset = queryset.filter(order__customer=user)

    # فلترة إضافية
    if status:
        queryset = queryset.filter(status=status)
    if delivery_type:
        queryset = queryset.filter(delivery_type=delivery_type)
    if driver_id:
        queryset = queryset.filter(driver_id=driver_id)
    if date_from:
        queryset = queryset.filter(created_at__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__lte=date_to)

    total = queryset.count()
    total_pages = (total + page_size - 1) // page_size

    offset = (page - 1) * page_size
    deliveries = queryset.order_by('-created_at')[offset:offset + page_size]

    return {
        'items': [delivery_to_response(d) for d in deliveries],
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages
    }


@router.get("/deliveries/{delivery_id}", response=DeliveryResponseSchema, auth=AuthBearer())
def get_delivery(request, delivery_id: UUID):
    """تفاصيل التوصيل"""
    delivery = get_object_or_404(Delivery, id=delivery_id)
    return delivery_to_response(delivery)


@router.get("/deliveries/{delivery_id}/tracking", response=DeliveryTrackingResponseSchema, auth=AuthBearer())
def get_delivery_tracking(request, delivery_id: UUID):
    """تتبع التوصيل الكامل"""
    delivery = get_object_or_404(Delivery, id=delivery_id)

    # نقاط التتبع
    tracking_points = DeliveryTrackingPoint.objects.filter(
        delivery=delivery
    ).order_by('-recorded_at')[:100]

    # الأحداث
    events = DeliveryEvent.objects.filter(
        delivery=delivery,
        is_customer_visible=True
    ).order_by('-occurred_at')[:50]

    # حساب ETA
    eta = None
    if delivery.is_active and delivery.current_location and delivery.dropoff_location:
        tracking_service = get_tracking_service()
        eta_result = tracking_service._eta_calculator.calculate(
            current_location=GeoPoint(
                latitude=delivery.current_location.y,
                longitude=delivery.current_location.x
            ),
            destination=GeoPoint(
                latitude=delivery.dropoff_location.y,
                longitude=delivery.dropoff_location.x
            ),
            current_speed=float(delivery.current_speed)
        )
        eta = {
            'minutes': eta_result.estimated_minutes,
            'estimated_arrival': eta_result.estimated_arrival,
            'distance_remaining_km': eta_result.distance_remaining,
            'confidence': eta_result.confidence
        }

    return {
        'delivery': delivery_to_response(delivery),
        'tracking_points': [
            {
                'id': tp.id,
                'latitude': tp.location.y,
                'longitude': tp.location.x,
                'speed': float(tp.speed),
                'heading': float(tp.heading),
                'status': tp.status,
                'recorded_at': tp.recorded_at
            }
            for tp in tracking_points
        ],
        'events': [
            {
                'id': e.id,
                'event_type': e.event_type,
                'title': e.title,
                'description': e.description,
                'old_status': e.old_status,
                'new_status': e.new_status,
                'occurred_at': e.occurred_at,
                'actor_type': e.actor_type
            }
            for e in events
        ],
        'eta': eta
    }


@router.post("/deliveries/{delivery_id}/assign", response=DeliveryResponseSchema, auth=AuthBearer())
def assign_driver(request, delivery_id: UUID, payload: DeliveryAssignSchema):
    """تعيين سائق للتوصيل"""
    user = get_current_user(request)
    delivery = get_object_or_404(Delivery, id=delivery_id)

    if delivery.status not in [DeliveryStatus.PENDING, DeliveryStatus.ASSIGNED]:
        return {"error": "لا يمكن تعيين سائق لهذا التوصيل"}, 400

    driver = get_object_or_404(User, id=payload.driver_id, user_type='driver')

    old_status = delivery.status
    delivery.assign_driver(driver)

    if payload.estimated_pickup_time:
        delivery.estimated_pickup_time = payload.estimated_pickup_time
        delivery.save(update_fields=['estimated_pickup_time'])

    # إنشاء حدث
    DeliveryEvent.objects.create(
        delivery=delivery,
        event_type=TrackingEventType.STATUS_CHANGE,
        title='تم تعيين سائق',
        description=f'تم تعيين السائق {driver.full_name}',
        old_status=old_status,
        new_status=DeliveryStatus.ASSIGNED,
        actor=user,
        actor_type='system',
        occurred_at=timezone.now()
    )

    return delivery_to_response(delivery)


@router.post("/deliveries/{delivery_id}/status", response=DeliveryResponseSchema, auth=AuthBearer())
def update_delivery_status(request, delivery_id: UUID, payload: DeliveryStatusUpdateSchema):
    """تحديث حالة التوصيل"""
    user = get_current_user(request)
    delivery = get_object_or_404(Delivery, id=delivery_id)

    old_status = delivery.status
    status_actions = {
        'accepted': delivery.accept,
        'picking_up': delivery.start_pickup,
        'at_pickup': delivery.arrive_at_pickup,
        'picked_up': delivery.confirm_pickup,
        'in_transit': delivery.start_delivery,
        'arrived': delivery.arrive_at_destination,
    }

    action = status_actions.get(payload.status)
    if action:
        action()
    else:
        delivery.status = payload.status
        delivery.save(update_fields=['status'])

    # تحديث الموقع إذا متوفر
    if payload.location:
        delivery.update_location(
            latitude=payload.location.latitude,
            longitude=payload.location.longitude
        )

    # إنشاء حدث
    DeliveryEvent.objects.create(
        delivery=delivery,
        event_type=TrackingEventType.STATUS_CHANGE,
        title=f'تم تحديث الحالة إلى {delivery.get_status_display()}',
        description=payload.notes or '',
        old_status=old_status,
        new_status=payload.status,
        location=Point(
            payload.location.longitude,
            payload.location.latitude,
            srid=4326
        ) if payload.location else None,
        actor=user,
        actor_type='driver' if user.user_type == 'driver' else 'system',
        occurred_at=timezone.now()
    )

    return delivery_to_response(delivery)


@router.post("/deliveries/{delivery_id}/complete", response=DeliveryResponseSchema, auth=AuthBearer())
def complete_delivery(request, delivery_id: UUID, payload: DeliveryCompleteSchema):
    """إتمام التوصيل"""
    user = get_current_user(request)
    delivery = get_object_or_404(Delivery, id=delivery_id)

    if delivery.status != DeliveryStatus.ARRIVED:
        return {"error": "يجب أن تكون في الوجهة لإتمام التوصيل"}, 400

    # التحقق من رمز التحقق
    if delivery.delivery_verification_code and payload.verification_code:
        if delivery.delivery_verification_code != payload.verification_code:
            return {"error": "رمز التحقق غير صحيح"}, 400

    old_status = delivery.status
    delivery.complete_delivery()

    # إنشاء حدث
    DeliveryEvent.objects.create(
        delivery=delivery,
        event_type=TrackingEventType.STATUS_CHANGE,
        title='تم تسليم الطلب',
        description='تم تسليم الطلب بنجاح',
        old_status=old_status,
        new_status=DeliveryStatus.DELIVERED,
        actor=user,
        actor_type='driver',
        occurred_at=timezone.now()
    )

    return delivery_to_response(delivery)


@router.post("/deliveries/{delivery_id}/fail", response=DeliveryResponseSchema, auth=AuthBearer())
def fail_delivery(request, delivery_id: UUID, payload: DeliveryFailSchema):
    """تسجيل فشل التوصيل"""
    user = get_current_user(request)
    delivery = get_object_or_404(Delivery, id=delivery_id)

    old_status = delivery.status
    delivery.fail_delivery(payload.reason)

    # إنشاء حدث
    DeliveryEvent.objects.create(
        delivery=delivery,
        event_type=TrackingEventType.EXCEPTION,
        title='فشل محاولة التوصيل',
        description=payload.reason,
        old_status=old_status,
        new_status=delivery.status,
        location=Point(
            payload.location.longitude,
            payload.location.latitude,
            srid=4326
        ) if payload.location else None,
        actor=user,
        actor_type='driver',
        occurred_at=timezone.now()
    )

    return delivery_to_response(delivery)


@router.post("/deliveries/{delivery_id}/cancel", response=DeliveryResponseSchema, auth=AuthBearer())
def cancel_delivery(request, delivery_id: UUID, payload: DeliveryCancelSchema):
    """إلغاء التوصيل"""
    user = get_current_user(request)
    delivery = get_object_or_404(Delivery, id=delivery_id)

    if not delivery.can_be_cancelled:
        return {"error": "لا يمكن إلغاء هذا التوصيل"}, 400

    old_status = delivery.status
    delivery.cancel(user, payload.reason)

    # إنشاء حدث
    DeliveryEvent.objects.create(
        delivery=delivery,
        event_type=TrackingEventType.STATUS_CHANGE,
        title='تم إلغاء التوصيل',
        description=payload.reason,
        old_status=old_status,
        new_status=DeliveryStatus.CANCELLED,
        actor=user,
        actor_type='customer' if user.user_type == 'customer' else 'system',
        occurred_at=timezone.now()
    )

    return delivery_to_response(delivery)


@router.post("/deliveries/{delivery_id}/rate", response=DeliveryResponseSchema, auth=AuthBearer())
def rate_delivery(request, delivery_id: UUID, payload: DeliveryRatingSchema):
    """تقييم التوصيل"""
    user = get_current_user(request)
    delivery = get_object_or_404(Delivery, id=delivery_id)

    if not delivery.is_completed:
        return {"error": "لا يمكن تقييم توصيل غير مكتمل"}, 400

    delivery.customer_rating = payload.rating
    delivery.customer_feedback = payload.feedback or ''
    delivery.save(update_fields=['customer_rating', 'customer_feedback'])

    return delivery_to_response(delivery)


# =============================================
# Location Tracking Endpoints
# =============================================

@router.post("/deliveries/{delivery_id}/location", auth=AuthBearer())
def update_delivery_location(request, delivery_id: UUID, payload: LocationUpdateSchema):
    """تحديث موقع التوصيل"""
    user = get_current_user(request)
    delivery = get_object_or_404(Delivery, id=delivery_id)

    if delivery.driver_id != user.id:
        return {"error": "غير مصرح"}, 403

    # تحديث الموقع
    delivery.update_location(
        latitude=payload.latitude,
        longitude=payload.longitude,
        speed=payload.speed,
        heading=payload.heading
    )

    # حفظ نقطة التتبع
    DeliveryTrackingPoint.objects.create(
        delivery=delivery,
        location=Point(payload.longitude, payload.latitude, srid=4326),
        altitude=payload.altitude,
        accuracy=payload.accuracy,
        speed=Decimal(str(payload.speed)),
        heading=Decimal(str(payload.heading)),
        status=delivery.status,
        battery_level=payload.battery_level,
        recorded_at=payload.timestamp or timezone.now()
    )

    return {"success": True}


@router.post("/driver/location", auth=AuthBearer())
def update_driver_location(request, payload: LocationUpdateSchema):
    """تحديث موقع السائق"""
    user = get_current_user(request)

    if user.user_type != 'driver':
        return {"error": "غير مصرح"}, 403

    location_point = Point(payload.longitude, payload.latitude, srid=4326)

    driver_location, created = DriverLocation.objects.update_or_create(
        driver=user,
        defaults={
            'location': location_point,
            'accuracy': payload.accuracy,
            'speed': Decimal(str(payload.speed)),
            'heading': Decimal(str(payload.heading)),
            'battery_level': payload.battery_level,
        }
    )

    return {"success": True}


@router.get("/driver/location", response=DriverLocationSchema, auth=AuthBearer())
def get_driver_location(request):
    """الحصول على موقع السائق الحالي"""
    user = get_current_user(request)

    if user.user_type != 'driver':
        return {"error": "غير مصرح"}, 403

    location = get_object_or_404(DriverLocation, driver=user)

    return {
        'driver_id': location.driver_id,
        'latitude': location.location.y,
        'longitude': location.location.x,
        'speed': float(location.speed),
        'heading': float(location.heading),
        'is_online': location.is_online,
        'is_available': location.is_available,
        'is_on_delivery': location.is_on_delivery,
        'current_delivery_id': location.current_delivery_id,
        'last_update': location.last_update,
        'battery_level': location.battery_level
    }


@router.post("/driver/availability", auth=AuthBearer())
def update_driver_availability(request, payload: DriverAvailabilitySchema):
    """تحديث توفر السائق"""
    user = get_current_user(request)

    if user.user_type != 'driver':
        return {"error": "غير مصرح"}, 403

    DriverLocation.objects.filter(driver=user).update(
        is_available=payload.is_available
    )

    return {"success": True, "is_available": payload.is_available}


@router.post("/driver/online", auth=AuthBearer())
def update_driver_online_status(request, payload: DriverOnlineStatusSchema):
    """تحديث حالة الاتصال"""
    user = get_current_user(request)

    if user.user_type != 'driver':
        return {"error": "غير مصرح"}, 403

    DriverLocation.objects.filter(driver=user).update(
        is_online=payload.is_online,
        is_available=payload.is_online  # إذا غير متصل = غير متاح
    )

    return {"success": True, "is_online": payload.is_online}


@router.get("/drivers/nearby", response=NearbyDriversResponseSchema, auth=AuthBearer())
def get_nearby_drivers(
    request,
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(10, ge=1, le=100),
    vehicle_type: Optional[str] = None
):
    """السائقين القريبين"""
    point = Point(longitude, latitude, srid=4326)

    queryset = DriverLocation.objects.filter(
        is_online=True,
        is_available=True,
        location__distance_lte=(point, D(km=radius_km))
    ).annotate(
        distance=Distance('location', point)
    ).order_by('distance')

    if vehicle_type:
        # نحتاج للربط مع DriverProfile للفلترة حسب نوع المركبة
        pass

    drivers = []
    for loc in queryset[:20]:
        distance_km = loc.distance.km if loc.distance else 0
        # تقدير ETA بناءً على متوسط سرعة 30 كم/س
        eta_minutes = int(distance_km / 0.5) if distance_km > 0 else 1

        drivers.append({
            'driver_id': loc.driver_id,
            'driver_name': loc.driver.full_name,
            'distance_km': round(distance_km, 2),
            'eta_minutes': eta_minutes,
            'rating': float(getattr(loc.driver, 'rating', 0) or 0),
            'vehicle_type': None,
            'is_available': loc.is_available
        })

    return {
        'drivers': drivers,
        'total': len(drivers)
    }


# =============================================
# Statistics Endpoints
# =============================================

@router.get("/stats/deliveries", response=DeliveryStatsSchema, auth=AuthBearer())
def get_delivery_stats(
    request,
    period: str = Query('today', pattern='^(today|week|month)$')
):
    """إحصائيات التوصيلات"""
    user = get_current_user(request)

    # تحديد الفترة
    now = timezone.now()
    if period == 'today':
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        start_date = now - timedelta(days=7)
    else:
        start_date = now - timedelta(days=30)

    queryset = Delivery.objects.filter(created_at__gte=start_date)

    # فلترة حسب الدور
    if user.user_type == 'driver':
        queryset = queryset.filter(driver=user)
    elif user.user_type == 'vendor':
        queryset = queryset.filter(order__vendor__owner=user)

    stats = queryset.aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(status=DeliveryStatus.DELIVERED)),
        failed=Count('id', filter=Q(status=DeliveryStatus.FAILED)),
        cancelled=Count('id', filter=Q(status=DeliveryStatus.CANCELLED)),
        total_distance=Sum('distance_traveled_km'),
        total_earnings=Sum('driver_earnings'),
    )

    in_progress = queryset.filter(
        status__in=[
            DeliveryStatus.ASSIGNED,
            DeliveryStatus.ACCEPTED,
            DeliveryStatus.PICKING_UP,
            DeliveryStatus.PICKED_UP,
            DeliveryStatus.IN_TRANSIT,
        ]
    ).count()

    # حساب متوسط وقت التوصيل
    completed = queryset.filter(
        status=DeliveryStatus.DELIVERED,
        started_at__isnull=False,
        completed_at__isnull=False
    )

    avg_time = 0
    if completed.exists():
        times = []
        for d in completed:
            if d.started_at and d.completed_at:
                delta = (d.completed_at - d.started_at).total_seconds() / 60
                times.append(delta)
        if times:
            avg_time = sum(times) / len(times)

    # متوسط التقييم
    avg_rating = queryset.filter(
        customer_rating__isnull=False
    ).aggregate(avg=Avg('customer_rating'))['avg'] or 0

    return {
        'total_deliveries': stats['total'] or 0,
        'completed_deliveries': stats['completed'] or 0,
        'failed_deliveries': stats['failed'] or 0,
        'cancelled_deliveries': stats['cancelled'] or 0,
        'in_progress_deliveries': in_progress,
        'average_delivery_time_minutes': round(avg_time, 1),
        'average_rating': round(float(avg_rating), 2),
        'total_distance_km': float(stats['total_distance'] or 0),
        'total_earnings': stats['total_earnings'] or Decimal('0'),
        'period': period
    }


@router.get("/stats/driver", response=DriverStatsSchema, auth=AuthBearer())
def get_driver_stats(request):
    """إحصائيات السائق"""
    user = get_current_user(request)

    if user.user_type != 'driver':
        return {"error": "غير مصرح"}, 403

    deliveries = Delivery.objects.filter(driver=user)

    stats = deliveries.aggregate(
        total=Count('id'),
        completed=Count('id', filter=Q(status=DeliveryStatus.DELIVERED)),
        total_distance=Sum('distance_traveled_km'),
        total_earnings=Sum('driver_earnings'),
    )

    completion_rate = 0
    if stats['total']:
        completion_rate = (stats['completed'] / stats['total']) * 100

    avg_rating = deliveries.filter(
        customer_rating__isnull=False
    ).aggregate(avg=Avg('customer_rating'))['avg'] or 0

    # متوسط وقت التوصيل
    completed = deliveries.filter(
        status=DeliveryStatus.DELIVERED,
        started_at__isnull=False,
        completed_at__isnull=False
    )

    avg_time = 0
    if completed.exists():
        times = []
        for d in completed:
            if d.started_at and d.completed_at:
                delta = (d.completed_at - d.started_at).total_seconds() / 60
                times.append(delta)
        if times:
            avg_time = sum(times) / len(times)

    return {
        'driver_id': user.id,
        'total_deliveries': stats['total'] or 0,
        'completed_deliveries': stats['completed'] or 0,
        'completion_rate': round(completion_rate, 1),
        'average_rating': round(float(avg_rating), 2),
        'total_distance_km': float(stats['total_distance'] or 0),
        'total_earnings': stats['total_earnings'] or Decimal('0'),
        'average_delivery_time_minutes': round(avg_time, 1),
        'online_hours_today': 0  # يحتاج تتبع منفصل
    }
