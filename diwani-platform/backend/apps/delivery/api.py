"""
===================================
منصة ديواني - Delivery API
Django Ninja API Endpoints for Delivery
===================================
"""

from typing import List, Optional
from uuid import UUID
from math import ceil
from decimal import Decimal

from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone

from ninja import Router, Query, File
from ninja.files import UploadedFile

from apps.orders.models import Order
from apps.accounts.models import DriverProfile
from .models import (
    DeliveryZone, DeliveryRequest, DriverLocationHistory,
    DeliveryAssignmentLog, DriverAvailability, DeliveryEarnings
)
from .schemas import (
    DeliveryZoneOutSchema,
    DeliveryFeeCalculationSchema,
    DeliveryFeeResponseSchema,
    DeliveryRequestOutSchema,
    DeliveryRequestListSchema,
    DriverLocationUpdateSchema,
    DriverLocationOutSchema,
    AvailableDeliverySchema,
    AcceptDeliverySchema,
    RejectDeliverySchema,
    CompleteDeliverySchema,
    EarningOutSchema,
    EarningsSummarySchema,
    DriverAvailabilitySchema,
    DriverAvailabilityOutSchema,
    DeliveryTrackingSchema,
    DeliveryRatingSchema,
    DeliveryStatsSchema,
    DriverStatsSchema,
    PaginatedDeliverySchema,
    PaginatedEarningsSchema,
    MessageSchema,
    ErrorSchema,
)

# Create router
router = Router(tags=['التوصيل'])


# ===================================
# Delivery Zone Endpoints
# ===================================
@router.get('/zones', response=List[DeliveryZoneOutSchema])
def list_delivery_zones(request, city: Optional[str] = None):
    """
    مناطق التوصيل
    ---
    قائمة مناطق التوصيل المتاحة
    """
    queryset = DeliveryZone.objects.filter(is_active=True)

    if city:
        queryset = queryset.filter(city__icontains=city)

    return queryset


@router.post('/calculate-fee', response=DeliveryFeeResponseSchema)
def calculate_delivery_fee(request, data: DeliveryFeeCalculationSchema):
    """
    حساب رسوم التوصيل
    ---
    حساب رسوم ووقت التوصيل بناءً على الموقع
    """
    from geopy.distance import geodesic

    pickup = (data.pickup_latitude, data.pickup_longitude)
    delivery = (data.delivery_latitude, data.delivery_longitude)

    # Calculate distance
    distance = geodesic(pickup, delivery).km

    # Check if delivery location is in a zone
    delivery_point = Point(data.delivery_longitude, data.delivery_latitude, srid=4326)
    zone = DeliveryZone.objects.filter(
        is_active=True,
        is_available=True
    ).first()  # Simple fallback, ideally check boundary

    if not zone:
        return DeliveryFeeResponseSchema(
            distance_km=Decimal(str(round(distance, 2))),
            delivery_fee=Decimal('0'),
            estimated_time_minutes=0,
            is_available=False,
            message='منطقة التوصيل غير متاحة حالياً'
        )

    # Calculate fee
    fee = zone.base_delivery_fee + (Decimal(str(distance)) * zone.per_km_fee)
    fee = max(zone.min_delivery_fee, min(fee, zone.max_delivery_fee))

    # Estimate time (assuming 30 km/h average speed + 10 min buffer)
    estimated_time = int((distance / 30) * 60) + 10 + zone.estimated_delivery_time

    return DeliveryFeeResponseSchema(
        distance_km=Decimal(str(round(distance, 2))),
        delivery_fee=fee,
        estimated_time_minutes=estimated_time,
        is_available=True,
        message='التوصيل متاح'
    )


# ===================================
# Customer Delivery Tracking Endpoints
# ===================================
@router.get('/track/{delivery_number}', response={200: DeliveryTrackingSchema, 404: ErrorSchema})
def track_delivery(request, delivery_number: str):
    """
    تتبع التوصيل
    ---
    تتبع حالة التوصيل والسائق
    """
    try:
        delivery = DeliveryRequest.objects.select_related(
            'driver', 'order'
        ).get(delivery_number=delivery_number)

        # Build timeline
        timeline = []
        if delivery.created_at:
            timeline.append({
                'status': 'pending',
                'title': 'تم إنشاء طلب التوصيل',
                'time': delivery.created_at.isoformat()
            })
        if delivery.assigned_at:
            timeline.append({
                'status': 'assigned',
                'title': 'تم تعيين السائق',
                'time': delivery.assigned_at.isoformat()
            })
        if delivery.picked_up_at:
            timeline.append({
                'status': 'picked_up',
                'title': 'تم استلام الطلب من المتجر',
                'time': delivery.picked_up_at.isoformat()
            })
        if delivery.delivered_at:
            timeline.append({
                'status': 'delivered',
                'title': 'تم التوصيل',
                'time': delivery.delivered_at.isoformat()
            })

        # Get driver location
        driver_lat = None
        driver_lng = None
        estimated_arrival = None

        if delivery.driver and hasattr(delivery.driver, 'driver_profile'):
            profile = delivery.driver.driver_profile
            if profile.current_location:
                driver_lat = profile.current_location.y
                driver_lng = profile.current_location.x

                # Calculate ETA if in transit
                if delivery.status == DeliveryRequest.RequestStatus.IN_TRANSIT:
                    from geopy.distance import geodesic
                    if delivery.delivery_location:
                        driver_pos = (driver_lat, driver_lng)
                        dest_pos = (delivery.delivery_location.y, delivery.delivery_location.x)
                        remaining_km = geodesic(driver_pos, dest_pos).km
                        estimated_arrival = int((remaining_km / 30) * 60) + 5

        return 200, DeliveryTrackingSchema(
            delivery_number=delivery.delivery_number,
            status=delivery.status,
            status_display=delivery.get_status_display(),
            driver_name=delivery.driver.full_name if delivery.driver else '',
            driver_phone=delivery.driver.phone_number if delivery.driver else '',
            driver_latitude=driver_lat,
            driver_longitude=driver_lng,
            pickup_address=delivery.pickup_address,
            delivery_address=delivery.delivery_address,
            estimated_arrival=estimated_arrival,
            distance_remaining=None,
            timeline=timeline
        )

    except DeliveryRequest.DoesNotExist:
        return 404, ErrorSchema(message='طلب التوصيل غير موجود')


@router.post('/deliveries/{delivery_id}/rate', response={200: MessageSchema, 400: ErrorSchema})
def rate_delivery(request, delivery_id: UUID, data: DeliveryRatingSchema):
    """
    تقييم التوصيل
    """
    try:
        delivery = DeliveryRequest.objects.get(
            id=delivery_id,
            order__customer=request.user,
            status=DeliveryRequest.RequestStatus.DELIVERED
        )

        delivery.customer_rating = data.rating
        delivery.customer_feedback = data.feedback
        delivery.save(update_fields=['customer_rating', 'customer_feedback'])

        # Update driver rating
        if delivery.driver and hasattr(delivery.driver, 'driver_profile'):
            profile = delivery.driver.driver_profile
            avg_rating = DeliveryRequest.objects.filter(
                driver=delivery.driver,
                customer_rating__isnull=False
            ).aggregate(avg=Avg('customer_rating'))['avg']

            if avg_rating:
                profile.rating = Decimal(str(round(avg_rating, 2)))
                profile.rating_count = DeliveryRequest.objects.filter(
                    driver=delivery.driver,
                    customer_rating__isnull=False
                ).count()
                profile.save(update_fields=['rating', 'rating_count'])

        return 200, MessageSchema(message='شكراً لتقييمك')

    except DeliveryRequest.DoesNotExist:
        return 400, ErrorSchema(message='طلب التوصيل غير موجود')


# ===================================
# Driver Endpoints
# ===================================
@router.post('/driver/location', response=MessageSchema)
def update_driver_location(request, data: DriverLocationUpdateSchema):
    """
    تحديث موقع السائق
    ---
    يستخدمه تطبيق السائق لتحديث الموقع
    """
    if not hasattr(request.user, 'driver_profile'):
        return MessageSchema(message='لست مسجلاً كسائق', success=False)

    profile = request.user.driver_profile
    location = Point(data.longitude, data.latitude, srid=4326)

    profile.current_location = location
    profile.last_location_update = timezone.now()
    profile.save(update_fields=['current_location', 'last_location_update'])

    # Log location history for active deliveries
    active_delivery = DeliveryRequest.objects.filter(
        driver=request.user,
        status__in=[
            DeliveryRequest.RequestStatus.ACCEPTED,
            DeliveryRequest.RequestStatus.PICKED_UP,
            DeliveryRequest.RequestStatus.IN_TRANSIT
        ]
    ).first()

    DriverLocationHistory.objects.create(
        driver=request.user,
        delivery_request=active_delivery,
        location=location,
        speed=data.speed,
        heading=data.heading,
        accuracy=data.accuracy
    )

    return MessageSchema(message='تم تحديث الموقع')


@router.get('/driver/available-deliveries', response=List[AvailableDeliverySchema])
def list_available_deliveries(request):
    """
    الطلبات المتاحة للتوصيل
    ---
    قائمة طلبات التوصيل المتاحة للسائق
    """
    if not hasattr(request.user, 'driver_profile'):
        return []

    profile = request.user.driver_profile

    if not profile.is_online or not profile.is_available:
        return []

    # Get pending deliveries
    deliveries = DeliveryRequest.objects.filter(
        status=DeliveryRequest.RequestStatus.PENDING
    ).order_by('created_at')

    results = []
    for delivery in deliveries[:20]:
        # Calculate distance to pickup
        distance_to_pickup = None
        if profile.current_location and delivery.pickup_location:
            from geopy.distance import geodesic
            driver_pos = (profile.current_location.y, profile.current_location.x)
            pickup_pos = (delivery.pickup_location.y, delivery.pickup_location.x)
            distance_to_pickup = geodesic(driver_pos, pickup_pos).km

        results.append(AvailableDeliverySchema(
            id=delivery.id,
            delivery_number=delivery.delivery_number,
            pickup_address=delivery.pickup_address,
            delivery_address=delivery.delivery_address,
            distance_km=delivery.distance_km,
            estimated_duration=delivery.estimated_duration,
            delivery_fee=delivery.delivery_fee,
            driver_earnings=delivery.driver_earnings,
            distance_to_pickup_km=round(distance_to_pickup, 2) if distance_to_pickup else None,
            pickup_contact_name=delivery.pickup_contact_name,
            created_at=delivery.created_at
        ))

    return results


@router.post('/driver/accept', response={200: DeliveryRequestOutSchema, 400: ErrorSchema})
def accept_delivery(request, data: AcceptDeliverySchema):
    """
    قبول طلب توصيل
    """
    try:
        delivery = DeliveryRequest.objects.get(
            id=data.delivery_id,
            status=DeliveryRequest.RequestStatus.PENDING
        )

        delivery.assign_driver(request.user)
        delivery.accept()

        # Update driver availability
        if hasattr(request.user, 'driver_profile'):
            request.user.driver_profile.is_available = False
            request.user.driver_profile.save(update_fields=['is_available'])

        # Log assignment
        DeliveryAssignmentLog.objects.create(
            delivery_request=delivery,
            driver=request.user,
            result=DeliveryAssignmentLog.AssignmentResult.ACCEPTED,
            responded_at=timezone.now()
        )

        return 200, delivery

    except DeliveryRequest.DoesNotExist:
        return 400, ErrorSchema(message='طلب التوصيل غير متاح')


@router.post('/driver/reject', response=MessageSchema)
def reject_delivery(request, data: RejectDeliverySchema):
    """
    رفض طلب توصيل
    """
    try:
        delivery = DeliveryRequest.objects.get(id=data.delivery_id)

        DeliveryAssignmentLog.objects.create(
            delivery_request=delivery,
            driver=request.user,
            result=DeliveryAssignmentLog.AssignmentResult.REJECTED,
            rejection_reason=data.reason,
            responded_at=timezone.now()
        )

        return MessageSchema(message='تم رفض الطلب')

    except DeliveryRequest.DoesNotExist:
        return MessageSchema(message='طلب التوصيل غير موجود', success=False)


@router.post('/driver/pickup/{delivery_id}', response={200: DeliveryRequestOutSchema, 400: ErrorSchema})
def pickup_delivery(request, delivery_id: UUID):
    """
    تأكيد استلام الطلب من المتجر
    """
    try:
        delivery = DeliveryRequest.objects.get(
            id=delivery_id,
            driver=request.user,
            status=DeliveryRequest.RequestStatus.ACCEPTED
        )

        delivery.pickup()

        # Update order status
        if delivery.order:
            delivery.order.status = Order.OrderStatus.PICKED_UP
            delivery.order.picked_up_at = timezone.now()
            delivery.order.save(update_fields=['status', 'picked_up_at'])

        return 200, delivery

    except DeliveryRequest.DoesNotExist:
        return 400, ErrorSchema(message='طلب التوصيل غير موجود')


@router.post('/driver/start-delivery/{delivery_id}', response={200: DeliveryRequestOutSchema, 400: ErrorSchema})
def start_delivery(request, delivery_id: UUID):
    """
    بدء التوصيل للعميل
    """
    try:
        delivery = DeliveryRequest.objects.get(
            id=delivery_id,
            driver=request.user,
            status=DeliveryRequest.RequestStatus.PICKED_UP
        )

        delivery.start_delivery()

        # Update order status
        if delivery.order:
            delivery.order.status = Order.OrderStatus.ON_THE_WAY
            delivery.order.save(update_fields=['status'])

        return 200, delivery

    except DeliveryRequest.DoesNotExist:
        return 400, ErrorSchema(message='طلب التوصيل غير موجود')


@router.post('/driver/complete/{delivery_id}', response={200: DeliveryRequestOutSchema, 400: ErrorSchema})
def complete_delivery(
    request,
    delivery_id: UUID,
    photo: UploadedFile = File(None),
    signature: UploadedFile = File(None),
    notes: str = ''
):
    """
    إتمام التوصيل
    """
    try:
        delivery = DeliveryRequest.objects.get(
            id=delivery_id,
            driver=request.user,
            status=DeliveryRequest.RequestStatus.IN_TRANSIT
        )

        delivery.driver_notes = notes
        delivery.complete(photo=photo, signature=signature)

        # Update order status
        if delivery.order:
            delivery.order.complete()

        # Update driver availability
        if hasattr(request.user, 'driver_profile'):
            request.user.driver_profile.is_available = True
            request.user.driver_profile.total_deliveries += 1
            request.user.driver_profile.save(update_fields=['is_available', 'total_deliveries'])

        # Create earnings record
        DeliveryEarnings.objects.create(
            driver=request.user,
            delivery_request=delivery,
            earning_type=DeliveryEarnings.EarningType.DELIVERY,
            amount=delivery.driver_earnings,
            description=f'توصيل #{delivery.delivery_number}'
        )

        return 200, delivery

    except DeliveryRequest.DoesNotExist:
        return 400, ErrorSchema(message='طلب التوصيل غير موجود')


@router.get('/driver/current', response={200: DeliveryRequestOutSchema, 404: ErrorSchema})
def get_current_delivery(request):
    """
    التوصيل الحالي
    """
    delivery = DeliveryRequest.objects.filter(
        driver=request.user,
        status__in=[
            DeliveryRequest.RequestStatus.ACCEPTED,
            DeliveryRequest.RequestStatus.PICKED_UP,
            DeliveryRequest.RequestStatus.IN_TRANSIT
        ]
    ).first()

    if not delivery:
        return 404, ErrorSchema(message='لا يوجد توصيل حالي')

    return 200, delivery


@router.get('/driver/history', response=PaginatedDeliverySchema)
def list_driver_delivery_history(
    request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50)
):
    """
    سجل التوصيلات
    """
    queryset = DeliveryRequest.objects.filter(driver=request.user).order_by('-created_at')

    total = queryset.count()
    pages = ceil(total / page_size)
    offset = (page - 1) * page_size
    items = list(queryset[offset:offset + page_size])

    return PaginatedDeliverySchema(
        items=[DeliveryRequestListSchema.from_orm(d) for d in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


# ===================================
# Driver Earnings Endpoints
# ===================================
@router.get('/driver/earnings', response=EarningsSummarySchema)
def get_driver_earnings_summary(request):
    """
    ملخص الأرباح
    """
    from datetime import timedelta

    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    earnings = DeliveryEarnings.objects.filter(driver=request.user)

    today_data = earnings.filter(created_at__date=today).aggregate(
        total=Sum('amount'),
        count=Count('id')
    )

    week_data = earnings.filter(created_at__date__gte=week_start).aggregate(
        total=Sum('amount'),
        count=Count('id')
    )

    month_data = earnings.filter(created_at__date__gte=month_start).aggregate(
        total=Sum('amount'),
        count=Count('id')
    )

    all_data = earnings.aggregate(
        total=Sum('amount'),
        count=Count('id')
    )

    pending = earnings.filter(is_settled=False).aggregate(total=Sum('amount'))['total']

    # Get average rating
    avg_rating = None
    if hasattr(request.user, 'driver_profile'):
        avg_rating = request.user.driver_profile.rating

    return EarningsSummarySchema(
        today_earnings=today_data['total'] or Decimal('0'),
        today_deliveries=today_data['count'] or 0,
        week_earnings=week_data['total'] or Decimal('0'),
        week_deliveries=week_data['count'] or 0,
        month_earnings=month_data['total'] or Decimal('0'),
        month_deliveries=month_data['count'] or 0,
        total_earnings=all_data['total'] or Decimal('0'),
        total_deliveries=all_data['count'] or 0,
        pending_settlement=pending or Decimal('0'),
        average_rating=avg_rating
    )


@router.get('/driver/earnings/history', response=PaginatedEarningsSchema)
def list_driver_earnings_history(
    request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50)
):
    """
    سجل الأرباح
    """
    queryset = DeliveryEarnings.objects.filter(driver=request.user).order_by('-created_at')

    total = queryset.count()
    pages = ceil(total / page_size)
    offset = (page - 1) * page_size
    items = list(queryset[offset:offset + page_size])

    return PaginatedEarningsSchema(
        items=[EarningOutSchema.from_orm(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages
    )


# ===================================
# Driver Availability Endpoints
# ===================================
@router.get('/driver/availability', response=List[DriverAvailabilityOutSchema])
def get_driver_availability(request):
    """
    جدول التوفر
    """
    return DriverAvailability.objects.filter(driver=request.user)


@router.post('/driver/availability', response={200: List[DriverAvailabilityOutSchema], 400: ErrorSchema})
def set_driver_availability(request, schedules: List[DriverAvailabilitySchema]):
    """
    تحديث جدول التوفر
    """
    try:
        # Delete existing
        DriverAvailability.objects.filter(driver=request.user).delete()

        # Create new
        created = []
        for schedule in schedules:
            avail = DriverAvailability.objects.create(
                driver=request.user,
                **schedule.dict()
            )
            created.append(avail)

        return 200, created

    except Exception as e:
        return 400, ErrorSchema(message=str(e))


@router.post('/driver/online', response=MessageSchema)
def go_online(request):
    """
    تفعيل حالة الاتصال
    """
    if hasattr(request.user, 'driver_profile'):
        request.user.driver_profile.go_online()
        return MessageSchema(message='أنت الآن متصل')
    return MessageSchema(message='لست مسجلاً كسائق', success=False)


@router.post('/driver/offline', response=MessageSchema)
def go_offline(request):
    """
    إيقاف حالة الاتصال
    """
    if hasattr(request.user, 'driver_profile'):
        request.user.driver_profile.go_offline()
        return MessageSchema(message='أنت الآن غير متصل')
    return MessageSchema(message='لست مسجلاً كسائق', success=False)


# ===================================
# Admin/Store Endpoints
# ===================================
@router.get('/admin/stats', response=DeliveryStatsSchema)
def get_delivery_stats(request):
    """
    إحصائيات التوصيل (للإدارة)
    """
    deliveries = DeliveryRequest.objects.all()

    by_status = dict(
        deliveries.values('status').annotate(count=Count('id')).values_list('status', 'count')
    )

    completed = deliveries.filter(status=DeliveryRequest.RequestStatus.DELIVERED)

    return DeliveryStatsSchema(
        total_deliveries=deliveries.count(),
        completed_deliveries=completed.count(),
        cancelled_deliveries=deliveries.filter(status=DeliveryRequest.RequestStatus.CANCELLED).count(),
        average_delivery_time=completed.aggregate(avg=Avg('actual_duration'))['avg'],
        average_rating=completed.aggregate(avg=Avg('customer_rating'))['avg'],
        total_distance_km=completed.aggregate(total=Sum('distance_km'))['total'] or Decimal('0'),
        total_earnings=completed.aggregate(total=Sum('driver_earnings'))['total'] or Decimal('0'),
        by_status=by_status,
        by_zone={}
    )


@router.get('/admin/drivers', response=List[DriverStatsSchema])
def list_drivers_stats(request):
    """
    إحصائيات السائقين (للإدارة)
    """
    from apps.accounts.models import User

    drivers = User.objects.filter(user_type='driver')
    results = []

    for driver in drivers:
        deliveries = DeliveryRequest.objects.filter(driver=driver)
        completed = deliveries.filter(status=DeliveryRequest.RequestStatus.DELIVERED)
        total_logs = DeliveryAssignmentLog.objects.filter(driver=driver).count()
        accepted_logs = DeliveryAssignmentLog.objects.filter(
            driver=driver,
            result=DeliveryAssignmentLog.AssignmentResult.ACCEPTED
        ).count()

        results.append(DriverStatsSchema(
            driver_id=driver.id,
            driver_name=driver.full_name,
            total_deliveries=deliveries.count(),
            completed_deliveries=completed.count(),
            average_rating=driver.driver_profile.rating if hasattr(driver, 'driver_profile') else None,
            total_earnings=completed.aggregate(total=Sum('driver_earnings'))['total'] or Decimal('0'),
            average_delivery_time=completed.aggregate(avg=Avg('actual_duration'))['avg'],
            acceptance_rate=(accepted_logs / total_logs * 100) if total_logs > 0 else 0,
            is_online=driver.driver_profile.is_online if hasattr(driver, 'driver_profile') else False
        ))

    return results
