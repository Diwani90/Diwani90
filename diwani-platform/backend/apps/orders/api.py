"""
API الطلبات
==========

Django Ninja API لإدارة الطلبات
"""

import logging
from typing import List, Optional
from uuid import UUID

logger = logging.getLogger(__name__)

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.db.models import Q
from ninja import Router, Query, File, UploadedFile
from ninja.pagination import paginate, LimitOffsetPagination

from .models import (
    Order,
    OrderItem,
    OrderStatus,
    OrderDelivery,
    OrderReview,
    OrderRefund,
)
from .schemas import (
    OrderSchema,
    OrderListSchema,
    OrderDetailSchema,
    OrderCreateSchema,
    OrderUpdateSchema,
    OrderItemSchema,
    OrderItemCreateSchema,
    OrderItemUpdateSchema,
    OrderStatusUpdateSchema,
    OrderCancelSchema,
    OrderReviewSchema,
    OrderReviewCreateSchema,
    VendorResponseSchema,
    RefundSchema,
    RefundRequestSchema,
    DeliveryTrackingSchema,
    OrderFilterSchema,
    OrderStatsSchema,
    OrderCreatedSchema,
    MessageSchema,
)
from .services import order_service, delivery_service
from apps.users.auth import JWTAuth, VendorJWTAuth, DriverJWTAuth

router = Router()


# =============================================
# دوال مساعدة للتتبع
# =============================================

def _get_pickup_location(order):
    """الحصول على موقع الاستلام (موقع المتجر)"""
    if not order or not order.vendor:
        return None

    vendor = order.vendor

    # محاولة الحصول على الموقع من location field
    if hasattr(vendor, 'location') and vendor.location:
        return {
            'latitude': vendor.location.y,
            'longitude': vendor.location.x,
            'address': getattr(vendor, 'address', '') or '',
            'name': vendor.name or '',
        }

    # محاولة الحصول من الإحداثيات المباشرة
    if hasattr(vendor, 'latitude') and hasattr(vendor, 'longitude'):
        if vendor.latitude and vendor.longitude:
            return {
                'latitude': float(vendor.latitude),
                'longitude': float(vendor.longitude),
                'address': getattr(vendor, 'address', '') or '',
                'name': vendor.name or '',
            }

    # إرجاع العنوان فقط إن وجد
    if hasattr(vendor, 'address') and vendor.address:
        return {
            'latitude': None,
            'longitude': None,
            'address': vendor.address,
            'name': vendor.name or '',
        }

    return None


def _get_destination_location(order, delivery):
    """الحصول على موقع الوجهة (عنوان العميل)"""
    # أولاً: من التوصيل
    if delivery:
        if hasattr(delivery, 'delivery_location') and delivery.delivery_location:
            return {
                'latitude': delivery.delivery_location.y,
                'longitude': delivery.delivery_location.x,
                'address': str(delivery.delivery_address) if delivery.delivery_address else '',
            }

        if delivery.delivery_address:
            addr = delivery.delivery_address
            if hasattr(addr, 'location') and addr.location:
                return {
                    'latitude': addr.location.y,
                    'longitude': addr.location.x,
                    'address': str(addr),
                }

            # إحداثيات مباشرة
            if hasattr(addr, 'latitude') and hasattr(addr, 'longitude'):
                if addr.latitude and addr.longitude:
                    return {
                        'latitude': float(addr.latitude),
                        'longitude': float(addr.longitude),
                        'address': str(addr),
                    }

            return {
                'latitude': None,
                'longitude': None,
                'address': str(addr),
            }

    # ثانياً: من الطلب
    if order and hasattr(order, 'delivery_address') and order.delivery_address:
        addr = order.delivery_address
        if hasattr(addr, 'location') and addr.location:
            return {
                'latitude': addr.location.y,
                'longitude': addr.location.x,
                'address': str(addr),
            }

        return {
            'latitude': None,
            'longitude': None,
            'address': str(addr),
        }

    return None


def _calculate_eta(delivery):
    """حساب الوقت المتوقع للوصول"""
    from django.utils import timezone
    from datetime import timedelta

    if not delivery:
        return None

    # إذا كان هناك وقت متوقع محفوظ
    if hasattr(delivery, 'estimated_arrival') and delivery.estimated_arrival:
        return delivery.estimated_arrival.isoformat()

    # حساب تقديري بناءً على الحالة والموقع
    if delivery.status == 'in_transit' or delivery.status == 'out_for_delivery':
        # تقدير بناءً على المسافة المتبقية
        if delivery.current_location and hasattr(delivery, 'delivery_location') and delivery.delivery_location:
            try:
                # حساب المسافة
                distance = delivery.current_location.distance(delivery.delivery_location)
                distance_km = distance.km if hasattr(distance, 'km') else float(distance) * 111

                # تقدير الوقت: 3 دقائق لكل كيلومتر في المتوسط (سرعة 20 كم/ساعة في المدينة)
                estimated_minutes = max(5, int(distance_km * 3))

                eta = timezone.now() + timedelta(minutes=estimated_minutes)
                return eta.isoformat()

            except Exception as e:
                logger.warning(f"Failed to calculate ETA from current location: {e}")

        # تقدير افتراضي: 30 دقيقة
        eta = timezone.now() + timedelta(minutes=30)
        return eta.isoformat()

    elif delivery.status == 'assigned':
        # السائق لم يبدأ بعد: 45 دقيقة تقديرياً
        eta = timezone.now() + timedelta(minutes=45)
        return eta.isoformat()

    elif delivery.status == 'picked_up':
        # تم الاستلام، في الطريق: 20 دقيقة تقديرياً
        eta = timezone.now() + timedelta(minutes=20)
        return eta.isoformat()

    return None


# =============================================
# API العميل - Customer Orders
# =============================================

@router.post('/orders', response={200: OrderCreatedSchema, 400: dict}, auth=JWTAuth(), tags=['طلبات العميل'])
def create_order(request: HttpRequest, data: OrderCreateSchema):
    """
    إنشاء طلب جديد

    يُنشئ طلب كمسودة قابل للتعديل قبل التأكيد
    """
    result = order_service.create_order(
        customer=request.auth,
        vendor_id=str(data.vendor_id),
        items=[item.dict() for item in data.items],
        delivery_address_id=str(data.delivery_address_id) if data.delivery_address_id else None,
        delivery_type=data.delivery_type,
        delivery_notes=data.delivery_notes or '',
        scheduled_delivery_date=data.scheduled_delivery_date,
        scheduled_delivery_time=data.scheduled_delivery_time or '',
        payment_method=data.payment_method,
        coupon_code=data.coupon_code or '',
        customer_notes=data.customer_notes or '',
        service_date=data.service_date,
        service_time=data.service_time,
        rental_start_date=data.rental_start_date,
        rental_end_date=data.rental_end_date,
        ip_address=get_client_ip(request),
        source='app',
    )

    if result.success:
        return 200, {
            'order_id': result.order.id,
            'order_number': result.order.order_number,
            'payment_url': result.payment_url,
            'message': 'تم إنشاء الطلب بنجاح'
        }

    return 400, {'error': result.error, 'code': result.error_code}


@router.get('/orders', response=List[OrderListSchema], auth=JWTAuth(), tags=['طلبات العميل'])
@paginate(LimitOffsetPagination)
def list_customer_orders(
    request: HttpRequest,
    filters: OrderFilterSchema = Query(...),
):
    """قائمة طلبات العميل"""
    queryset = Order.objects.filter(customer=request.auth)

    if filters.status:
        queryset = queryset.filter(status=filters.status)

    if filters.payment_status:
        queryset = queryset.filter(payment_status=filters.payment_status)

    if filters.start_date:
        queryset = queryset.filter(created_at__date__gte=filters.start_date)

    if filters.end_date:
        queryset = queryset.filter(created_at__date__lte=filters.end_date)

    if filters.search:
        queryset = queryset.filter(
            Q(order_number__icontains=filters.search) |
            Q(vendor__name__icontains=filters.search)
        )

    return queryset.select_related('vendor').prefetch_related('items').order_by('-created_at')


@router.get('/orders/{order_id}', response=OrderDetailSchema, auth=JWTAuth(), tags=['طلبات العميل'])
def get_order(request: HttpRequest, order_id: UUID):
    """تفاصيل طلب"""
    return get_object_or_404(
        Order.objects.select_related('vendor', 'delivery_address', 'delivery')
        .prefetch_related('items', 'items__product', 'status_history'),
        id=order_id,
        customer=request.auth
    )


@router.post('/orders/{order_id}/place', response={200: OrderCreatedSchema, 400: dict}, auth=JWTAuth(), tags=['طلبات العميل'])
def place_order(request: HttpRequest, order_id: UUID):
    """
    تأكيد الطلب وبدء الدفع

    ينقل الطلب من مسودة إلى بانتظار الدفع
    """
    order = get_object_or_404(Order, id=order_id, customer=request.auth)

    result = order_service.place_order(order, request.auth)

    if result.success:
        return 200, {
            'order_id': result.order.id,
            'order_number': result.order.order_number,
            'payment_url': result.payment_url,
            'message': 'تم تأكيد الطلب. يرجى إكمال الدفع'
        }

    return 400, {'error': result.error, 'code': result.error_code}


@router.post('/orders/{order_id}/cancel', response={200: MessageSchema, 400: dict}, auth=JWTAuth(), tags=['طلبات العميل'])
def cancel_order(request: HttpRequest, order_id: UUID, data: OrderCancelSchema):
    """إلغاء طلب"""
    order = get_object_or_404(Order, id=order_id, customer=request.auth)

    result = order_service.cancel_order(
        order=order,
        user=request.auth,
        reason=data.reason,
        notes=data.notes or ''
    )

    if result.success:
        return 200, {'message': 'تم إلغاء الطلب بنجاح', 'success': True}

    return 400, {'error': result.error, 'code': result.error_code}


@router.get('/orders/{order_id}/tracking', response=DeliveryTrackingSchema, auth=JWTAuth(), tags=['طلبات العميل'])
def track_order(request: HttpRequest, order_id: UUID):
    """تتبع طلب"""
    order = get_object_or_404(
        Order.objects.select_related('delivery'),
        id=order_id,
        customer=request.auth
    )

    delivery = order.delivery

    return {
        'order_id': order.id,
        'order_number': order.order_number,
        'status': delivery.status if delivery else order.status,
        'driver_name': delivery.driver.get_full_name() if delivery and delivery.driver else None,
        'driver_phone': delivery.driver.phone_number if delivery and delivery.driver else None,
        'current_location': {
            'latitude': delivery.current_location.y,
            'longitude': delivery.current_location.x,
            'recorded_at': delivery.last_location_update,
        } if delivery and delivery.current_location else None,
        'pickup_location': _get_pickup_location(order),
        'destination_location': _get_destination_location(order, delivery),
        'estimated_arrival': _calculate_eta(delivery) if delivery else None,
        'tracking_points': list(
            delivery.tracking_points.values(
                'latitude', 'longitude', 'accuracy', 'speed', 'heading', 'recorded_at'
            )[:100]
        ) if delivery else [],
    }


# =============================================
# التقييمات - Reviews
# =============================================

@router.post('/orders/{order_id}/review', response={200: OrderReviewSchema, 400: dict}, auth=JWTAuth(), tags=['التقييمات'])
def create_review(request: HttpRequest, order_id: UUID, data: OrderReviewCreateSchema):
    """إضافة تقييم للطلب"""
    order = get_object_or_404(
        Order,
        id=order_id,
        customer=request.auth,
        status=OrderStatus.COMPLETED
    )

    # التحقق من عدم وجود تقييم سابق
    if hasattr(order, 'review'):
        return 400, {'error': 'تم تقييم هذا الطلب مسبقاً'}

    review = OrderReview.objects.create(
        order=order,
        customer=request.auth,
        vendor_rating=data.vendor_rating,
        vendor_comment=data.vendor_comment or '',
        products_rating=data.products_rating,
        products_comment=data.products_comment or '',
        delivery_rating=data.delivery_rating,
        delivery_comment=data.delivery_comment or '',
        is_anonymous=data.is_anonymous,
    )

    # تحديث تقييم المتجر
    _update_vendor_rating(order.vendor)

    return 200, review


@router.get('/orders/{order_id}/review', response=OrderReviewSchema, auth=JWTAuth(), tags=['التقييمات'])
def get_review(request: HttpRequest, order_id: UUID):
    """الحصول على تقييم الطلب"""
    order = get_object_or_404(Order, id=order_id, customer=request.auth)
    return get_object_or_404(OrderReview, order=order)


# =============================================
# الاسترداد - Refunds
# =============================================

@router.post('/orders/{order_id}/refund', response={200: RefundSchema, 400: dict}, auth=JWTAuth(), tags=['الاسترداد'])
def request_refund(request: HttpRequest, order_id: UUID, data: RefundRequestSchema):
    """طلب استرداد"""
    order = get_object_or_404(Order, id=order_id, customer=request.auth)

    if not order.is_paid:
        return 400, {'error': 'الطلب غير مدفوع'}

    # حساب المبلغ
    if data.item_id:
        item = get_object_or_404(OrderItem, id=data.item_id, order=order)
        amount = data.amount or item.total_price
    else:
        amount = data.amount or order.paid_amount

    refund = OrderRefund.objects.create(
        order=order,
        item_id=data.item_id,
        amount=amount,
        reason=data.reason,
        reason_details=data.reason_details or '',
        requested_by=request.auth,
    )

    return 200, refund


@router.get('/orders/{order_id}/refunds', response=List[RefundSchema], auth=JWTAuth(), tags=['الاسترداد'])
def list_refunds(request: HttpRequest, order_id: UUID):
    """قائمة طلبات الاسترداد للطلب"""
    order = get_object_or_404(Order, id=order_id, customer=request.auth)
    return OrderRefund.objects.filter(order=order)


# =============================================
# API التاجر - Vendor Orders
# =============================================

@router.get('/vendor/orders', response=List[OrderListSchema], auth=VendorJWTAuth(), tags=['طلبات التاجر'])
@paginate(LimitOffsetPagination)
def list_vendor_orders(
    request: HttpRequest,
    filters: OrderFilterSchema = Query(...),
):
    """قائمة طلبات المتجر"""
    from apps.stores.models import Store

    store = Store.objects.filter(owner=request.auth).first()
    if not store:
        return []

    queryset = Order.objects.filter(vendor=store)

    if filters.status:
        queryset = queryset.filter(status=filters.status)

    if filters.payment_status:
        queryset = queryset.filter(payment_status=filters.payment_status)

    if filters.start_date:
        queryset = queryset.filter(created_at__date__gte=filters.start_date)

    if filters.end_date:
        queryset = queryset.filter(created_at__date__lte=filters.end_date)

    if filters.search:
        queryset = queryset.filter(
            Q(order_number__icontains=filters.search) |
            Q(customer__first_name__icontains=filters.search) |
            Q(customer__phone_number__icontains=filters.search)
        )

    return queryset.select_related('customer').prefetch_related('items').order_by('-created_at')


@router.get('/vendor/orders/{order_id}', response=OrderDetailSchema, auth=VendorJWTAuth(), tags=['طلبات التاجر'])
def get_vendor_order(request: HttpRequest, order_id: UUID):
    """تفاصيل طلب للتاجر"""
    from apps.stores.models import Store

    store = Store.objects.filter(owner=request.auth).first()

    return get_object_or_404(
        Order.objects.select_related('customer', 'delivery_address', 'delivery')
        .prefetch_related('items', 'items__product', 'status_history'),
        id=order_id,
        vendor=store
    )


@router.post('/vendor/orders/{order_id}/accept', response={200: MessageSchema, 400: dict}, auth=VendorJWTAuth(), tags=['طلبات التاجر'])
def accept_vendor_order(request: HttpRequest, order_id: UUID):
    """قبول طلب"""
    from apps.stores.models import Store

    store = Store.objects.filter(owner=request.auth).first()
    order = get_object_or_404(Order, id=order_id, vendor=store)

    result = order_service.accept_order(order, request.auth)

    if result.success:
        return 200, {'message': 'تم قبول الطلب', 'success': True}

    return 400, {'error': result.error}


@router.post('/vendor/orders/{order_id}/status', response={200: MessageSchema, 400: dict}, auth=VendorJWTAuth(), tags=['طلبات التاجر'])
def update_vendor_order_status(request: HttpRequest, order_id: UUID, data: OrderStatusUpdateSchema):
    """تحديث حالة الطلب"""
    from apps.stores.models import Store

    store = Store.objects.filter(owner=request.auth).first()
    order = get_object_or_404(Order, id=order_id, vendor=store)

    result = order_service.update_status(
        order=order,
        new_status=data.status,
        user=request.auth,
        notes=data.notes or ''
    )

    if result.success:
        return 200, {'message': f'تم تحديث الحالة إلى {data.status}', 'success': True}

    return 400, {'error': result.error}


@router.post('/vendor/orders/{order_id}/review/response', response=MessageSchema, auth=VendorJWTAuth(), tags=['طلبات التاجر'])
def respond_to_review(request: HttpRequest, order_id: UUID, data: VendorResponseSchema):
    """رد التاجر على التقييم"""
    from apps.stores.models import Store
    from django.utils import timezone

    store = Store.objects.filter(owner=request.auth).first()
    order = get_object_or_404(Order, id=order_id, vendor=store)
    review = get_object_or_404(OrderReview, order=order)

    review.vendor_response = data.response
    review.vendor_responded_at = timezone.now()
    review.save()

    return {'message': 'تم إضافة الرد بنجاح', 'success': True}


@router.get('/vendor/orders/stats', response=OrderStatsSchema, auth=VendorJWTAuth(), tags=['طلبات التاجر'])
def get_vendor_order_stats(
    request: HttpRequest,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """إحصائيات الطلبات للتاجر"""
    from apps.stores.models import Store
    from datetime import datetime

    store = Store.objects.filter(owner=request.auth).first()
    if not store:
        return {}

    stats = order_service.get_order_stats(
        user=request.auth,
        user_type='vendor',
        vendor_id=str(store.id),
        start_date=datetime.fromisoformat(start_date).date() if start_date else None,
        end_date=datetime.fromisoformat(end_date).date() if end_date else None,
    )

    return stats


# =============================================
# API السائق - Driver Orders
# =============================================

@router.get('/driver/orders/available', response=List[OrderListSchema], auth=DriverJWTAuth(), tags=['طلبات السائق'])
@paginate(LimitOffsetPagination)
def list_available_orders(
    request: HttpRequest,
    latitude: float,
    longitude: float,
    radius_km: float = 10,
):
    """الطلبات المتاحة للتوصيل"""
    deliveries = delivery_service.get_nearby_orders(
        driver=request.auth,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km
    )

    return [d.order for d in deliveries]


@router.get('/driver/orders/active', response=List[OrderListSchema], auth=DriverJWTAuth(), tags=['طلبات السائق'])
def list_driver_active_orders(request: HttpRequest):
    """الطلبات النشطة للسائق"""
    return Order.objects.filter(
        delivery__driver=request.auth,
        delivery__status__in=[
            OrderDelivery.DeliveryStatus.ASSIGNED,
            OrderDelivery.DeliveryStatus.PICKED_UP,
            OrderDelivery.DeliveryStatus.IN_TRANSIT,
        ]
    ).select_related('vendor', 'delivery_address')


@router.post('/driver/orders/{order_id}/accept', response={200: MessageSchema, 400: dict}, auth=DriverJWTAuth(), tags=['طلبات السائق'])
def accept_delivery(request: HttpRequest, order_id: UUID):
    """قبول طلب توصيل"""
    delivery = get_object_or_404(
        OrderDelivery,
        order_id=order_id,
        status=OrderDelivery.DeliveryStatus.PENDING
    )

    success = delivery_service.assign_driver(delivery, request.auth)

    if success:
        return 200, {'message': 'تم قبول الطلب', 'success': True}

    return 400, {'error': 'فشل في قبول الطلب'}


@router.post('/driver/orders/{order_id}/pickup', response=MessageSchema, auth=DriverJWTAuth(), tags=['طلبات السائق'])
def mark_pickup(request: HttpRequest, order_id: UUID):
    """تسجيل استلام الطلب"""
    delivery = get_object_or_404(
        OrderDelivery,
        order_id=order_id,
        driver=request.auth
    )

    delivery_service.mark_picked_up(delivery, request.auth)

    return {'message': 'تم تسجيل الاستلام', 'success': True}


@router.post('/driver/orders/{order_id}/deliver', response=MessageSchema, auth=DriverJWTAuth(), tags=['طلبات السائق'])
def mark_delivered(
    request: HttpRequest,
    order_id: UUID,
    recipient_name: str = '',
    notes: str = '',
    photo: UploadedFile = File(None),
):
    """تسجيل تسليم الطلب"""
    delivery = get_object_or_404(
        OrderDelivery,
        order_id=order_id,
        driver=request.auth
    )

    delivery_service.mark_delivered(
        delivery=delivery,
        driver=request.auth,
        recipient_name=recipient_name,
        photo=photo,
        notes=notes
    )

    return {'message': 'تم تسليم الطلب بنجاح', 'success': True}


@router.post('/driver/orders/{order_id}/location', response=MessageSchema, auth=DriverJWTAuth(), tags=['طلبات السائق'])
def update_driver_location(
    request: HttpRequest,
    order_id: UUID,
    latitude: float,
    longitude: float,
    accuracy: Optional[float] = None,
    speed: Optional[float] = None,
    heading: Optional[float] = None,
):
    """تحديث موقع السائق"""
    delivery = get_object_or_404(
        OrderDelivery,
        order_id=order_id,
        driver=request.auth
    )

    delivery_service.update_location(
        delivery=delivery,
        latitude=latitude,
        longitude=longitude,
        accuracy=accuracy,
        speed=speed,
        heading=heading
    )

    return {'message': 'تم تحديث الموقع', 'success': True}


# =============================================
# مساعدات
# =============================================

def get_client_ip(request: HttpRequest) -> str:
    """الحصول على IP العميل"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def _update_vendor_rating(vendor):
    """تحديث تقييم المتجر"""
    from django.db.models import Avg

    avg_rating = OrderReview.objects.filter(
        order__vendor=vendor
    ).aggregate(avg=Avg('vendor_rating'))['avg']

    if avg_rating:
        vendor.rating = avg_rating
        vendor.save(update_fields=['rating'])
