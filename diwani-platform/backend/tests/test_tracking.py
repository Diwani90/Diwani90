"""
اختبارات نظام التتبع
====================
"""

import pytest
from decimal import Decimal
from datetime import timedelta

from django.contrib.gis.geos import Point
from django.utils import timezone

from apps.tracking.models import (
    Delivery, DeliveryStatus, DeliveryType, DeliveryEvent,
    DeliveryTrackingPoint, DriverLocation, Geofence, TrackingEventType
)
from apps.tracking.services import (
    TrackingService, GeoUtils, GeoPoint, ETACalculator, GeofenceService
)


# =============================================
# Delivery Model Tests
# =============================================

@pytest.mark.django_db
class TestDeliveryModel:
    """اختبارات نموذج التوصيل"""

    def test_create_delivery(self, order, driver_user):
        """اختبار إنشاء توصيل"""
        delivery = Delivery.objects.create(
            order=order,
            driver=driver_user,
            delivery_type=DeliveryType.STANDARD,
            pickup_location=Point(46.6753, 24.7136, srid=4326),
            pickup_address='عنوان الاستلام',
            pickup_contact_name='اسم جهة الاستلام',
            pickup_contact_phone='+966500000001',
            dropoff_location=Point(46.6500, 24.7500, srid=4326),
            dropoff_address='عنوان التسليم',
            dropoff_contact_name='اسم المستلم',
            dropoff_contact_phone='+966500000002',
        )

        assert delivery.id is not None
        assert delivery.status == DeliveryStatus.PENDING
        assert delivery.pickup_verification_code is not None
        assert delivery.delivery_verification_code is not None

    def test_assign_driver(self, delivery, driver_user):
        """اختبار تعيين سائق"""
        delivery.assign_driver(driver_user)

        assert delivery.driver == driver_user
        assert delivery.status == DeliveryStatus.ASSIGNED
        assert delivery.assigned_at is not None

    def test_delivery_workflow(self, delivery):
        """اختبار سير عمل التوصيل"""
        # القبول
        delivery.accept()
        assert delivery.status == DeliveryStatus.ACCEPTED

        # بدء الذهاب للاستلام
        delivery.start_pickup()
        assert delivery.status == DeliveryStatus.PICKING_UP
        assert delivery.started_at is not None

        # الوصول لنقطة الاستلام
        delivery.arrive_at_pickup()
        assert delivery.status == DeliveryStatus.AT_PICKUP

        # تأكيد الاستلام
        delivery.confirm_pickup()
        assert delivery.status == DeliveryStatus.PICKED_UP
        assert delivery.actual_pickup_time is not None

        # بدء التوصيل
        delivery.start_delivery()
        assert delivery.status == DeliveryStatus.IN_TRANSIT

        # الوصول للوجهة
        delivery.arrive_at_destination()
        assert delivery.status == DeliveryStatus.ARRIVED

        # إتمام التوصيل
        delivery.complete_delivery()
        assert delivery.status == DeliveryStatus.DELIVERED
        assert delivery.actual_delivery_time is not None
        assert delivery.completed_at is not None

    def test_delivery_failure(self, delivery):
        """اختبار فشل التوصيل"""
        delivery.fail_delivery('العميل غير متواجد')

        assert delivery.delivery_attempts == 1
        assert delivery.failure_reason == 'العميل غير متواجد'
        # أول محاولة فشل - يعود للانتظار
        assert delivery.status == DeliveryStatus.PENDING

        # فشل ثلاث مرات
        delivery.fail_delivery('سبب ثاني')
        delivery.fail_delivery('سبب ثالث')

        assert delivery.delivery_attempts == 3
        assert delivery.status == DeliveryStatus.FAILED

    def test_delivery_cancellation(self, delivery, customer_user):
        """اختبار إلغاء التوصيل"""
        assert delivery.can_be_cancelled

        delivery.cancel(customer_user, 'تغيير في الخطط')

        assert delivery.status == DeliveryStatus.CANCELLED
        assert delivery.cancelled_by == customer_user
        assert delivery.cancellation_reason == 'تغيير في الخطط'

    def test_cannot_cancel_in_transit(self, delivery):
        """اختبار عدم إمكانية الإلغاء أثناء التوصيل"""
        delivery.status = DeliveryStatus.IN_TRANSIT
        delivery.save()

        assert not delivery.can_be_cancelled

    def test_update_location(self, delivery):
        """اختبار تحديث الموقع"""
        delivery.update_location(
            latitude=24.7200,
            longitude=46.6800,
            speed=40.5,
            heading=90
        )

        assert delivery.current_location is not None
        assert delivery.current_location.y == 24.7200
        assert delivery.current_location.x == 46.6800
        assert float(delivery.current_speed) == 40.5
        assert delivery.last_location_update is not None


# =============================================
# GeoUtils Tests
# =============================================

class TestGeoUtils:
    """اختبارات الأدوات الجغرافية"""

    def test_haversine_distance(self):
        """اختبار حساب المسافة"""
        # الرياض إلى جدة (حوالي 950 كم)
        riyadh = GeoPoint(latitude=24.7136, longitude=46.6753)
        jeddah = GeoPoint(latitude=21.5433, longitude=39.1728)

        distance = GeoUtils.haversine_distance(riyadh, jeddah)

        assert 900 < distance < 1000  # تقريباً 950 كم

    def test_bearing(self):
        """اختبار حساب الاتجاه"""
        point1 = GeoPoint(latitude=24.7136, longitude=46.6753)
        point2 = GeoPoint(latitude=24.8000, longitude=46.6753)  # شمال مباشرة

        bearing = GeoUtils.bearing(point1, point2)

        # يجب أن يكون تقريباً 0 (شمال)
        assert -5 < bearing < 5 or 355 < bearing < 365

    def test_point_in_circle(self):
        """اختبار نقطة داخل دائرة"""
        center = GeoPoint(latitude=24.7136, longitude=46.6753)
        inside = GeoPoint(latitude=24.7140, longitude=46.6755)
        outside = GeoPoint(latitude=24.8000, longitude=46.8000)

        assert GeoUtils.is_point_in_circle(inside, center, 1000)  # 1 كم
        assert not GeoUtils.is_point_in_circle(outside, center, 1000)

    def test_calculate_speed(self):
        """اختبار حساب السرعة"""
        now = timezone.now()
        point1 = GeoPoint(
            latitude=24.7136,
            longitude=46.6753,
            timestamp=now - timedelta(hours=1)
        )
        point2 = GeoPoint(
            latitude=24.8136,
            longitude=46.7753,
            timestamp=now
        )

        speed = GeoUtils.calculate_speed(point1, point2)

        # يجب أن تكون السرعة موجبة
        assert speed > 0


# =============================================
# ETA Calculator Tests
# =============================================

class TestETACalculator:
    """اختبارات حاسبة ETA"""

    def test_calculate_eta(self):
        """اختبار حساب ETA"""
        calculator = ETACalculator()

        current = GeoPoint(latitude=24.7136, longitude=46.6753)
        destination = GeoPoint(latitude=24.7500, longitude=46.7000)

        eta = calculator.calculate(current, destination, current_speed=30)

        assert eta.estimated_minutes > 0
        assert eta.distance_remaining > 0
        assert eta.confidence > 0

    def test_eta_with_traffic_factor(self):
        """اختبار ETA مع معامل الحركة"""
        calculator = ETACalculator()

        # اختبار معامل الحركة
        traffic_factor = calculator._get_traffic_factor()

        assert 0.5 <= traffic_factor <= 2.0


# =============================================
# Geofence Tests
# =============================================

@pytest.mark.django_db
class TestGeofence:
    """اختبارات السياج الجغرافي"""

    def test_create_geofence(self, delivery):
        """اختبار إنشاء سياج"""
        geofence = Geofence.objects.create(
            delivery=delivery,
            name='نقطة الاستلام',
            geofence_type='pickup',
            center=Point(46.6753, 24.7136, srid=4326),
            radius_meters=100,
        )

        assert geofence.id is not None
        assert geofence.is_active

    def test_geofence_contains_point(self, delivery):
        """اختبار احتواء السياج لنقطة"""
        geofence = Geofence.objects.create(
            delivery=delivery,
            name='منطقة اختبار',
            geofence_type='zone',
            center=Point(46.6753, 24.7136, srid=4326),
            radius_meters=1000,  # 1 كم
        )

        inside = Point(46.6760, 24.7140, srid=4326)
        outside = Point(46.7000, 24.8000, srid=4326)

        assert geofence.contains_point(inside)
        assert not geofence.contains_point(outside)


# =============================================
# Tracking Point Tests
# =============================================

@pytest.mark.django_db
class TestTrackingPoints:
    """اختبارات نقاط التتبع"""

    def test_create_tracking_point(self, delivery):
        """اختبار إنشاء نقطة تتبع"""
        point = DeliveryTrackingPoint.objects.create(
            delivery=delivery,
            location=Point(46.6753, 24.7136, srid=4326),
            speed=Decimal('35.5'),
            heading=Decimal('90'),
            status=DeliveryStatus.IN_TRANSIT,
            battery_level=85,
            recorded_at=timezone.now(),
        )

        assert point.id is not None
        assert point.latitude == 24.7136
        assert point.longitude == 46.6753

    def test_tracking_points_ordering(self, delivery):
        """اختبار ترتيب نقاط التتبع"""
        now = timezone.now()

        point1 = DeliveryTrackingPoint.objects.create(
            delivery=delivery,
            location=Point(46.6753, 24.7136, srid=4326),
            status=DeliveryStatus.IN_TRANSIT,
            recorded_at=now - timedelta(minutes=5),
        )

        point2 = DeliveryTrackingPoint.objects.create(
            delivery=delivery,
            location=Point(46.6760, 24.7140, srid=4326),
            status=DeliveryStatus.IN_TRANSIT,
            recorded_at=now,
        )

        points = DeliveryTrackingPoint.objects.filter(
            delivery=delivery
        ).order_by('-recorded_at')

        assert points[0].id == point2.id


# =============================================
# Driver Location Tests
# =============================================

@pytest.mark.django_db
class TestDriverLocation:
    """اختبارات موقع السائق"""

    def test_update_driver_location(self, driver_user):
        """اختبار تحديث موقع السائق"""
        location, created = DriverLocation.objects.update_or_create(
            driver=driver_user,
            defaults={
                'location': Point(46.6753, 24.7136, srid=4326),
                'speed': Decimal('40'),
                'heading': Decimal('180'),
                'is_online': True,
                'is_available': True,
            }
        )

        assert created
        assert location.is_online
        assert location.is_available

    def test_driver_location_stale(self, driver_user):
        """اختبار موقع سائق قديم"""
        location = DriverLocation.objects.create(
            driver=driver_user,
            location=Point(46.6753, 24.7136, srid=4326),
        )

        # تحديث الوقت ليكون قديماً
        DriverLocation.objects.filter(
            driver=driver_user
        ).update(last_update=timezone.now() - timedelta(minutes=10))

        location.refresh_from_db()
        assert location.is_stale


# =============================================
# Delivery Event Tests
# =============================================

@pytest.mark.django_db
class TestDeliveryEvents:
    """اختبارات أحداث التوصيل"""

    def test_create_event(self, delivery, driver_user):
        """اختبار إنشاء حدث"""
        event = DeliveryEvent.objects.create(
            delivery=delivery,
            event_type=TrackingEventType.STATUS_CHANGE,
            title='تم قبول التوصيل',
            description='قبل السائق طلب التوصيل',
            old_status=DeliveryStatus.ASSIGNED,
            new_status=DeliveryStatus.ACCEPTED,
            actor=driver_user,
            actor_type='driver',
            occurred_at=timezone.now(),
        )

        assert event.id is not None
        assert event.is_customer_visible

    def test_event_ordering(self, delivery):
        """اختبار ترتيب الأحداث"""
        now = timezone.now()

        event1 = DeliveryEvent.objects.create(
            delivery=delivery,
            event_type=TrackingEventType.STATUS_CHANGE,
            title='حدث 1',
            occurred_at=now - timedelta(hours=1),
        )

        event2 = DeliveryEvent.objects.create(
            delivery=delivery,
            event_type=TrackingEventType.STATUS_CHANGE,
            title='حدث 2',
            occurred_at=now,
        )

        events = DeliveryEvent.objects.filter(
            delivery=delivery
        ).order_by('-occurred_at')

        assert events[0].id == event2.id
