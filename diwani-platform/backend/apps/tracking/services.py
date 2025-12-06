"""
خدمات نظام التتبع
===================

يوفر:
- تتبع موقع التوصيل الحي
- حساب ETA بدقة
- Geofencing للتنبيهات
- سجل المواقع
- تحليل المسار
"""

import asyncio
import json
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import redis.asyncio as aioredis
from django.conf import settings
from django.utils import timezone

from apps.realtime.events import (
    DeliveryLocationUpdatedEvent,
    OrderStatusChangedEvent,
    get_event_bus,
    publish_event,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class GeoPoint:
    """نقطة جغرافية"""

    latitude: float
    longitude: float
    altitude: Optional[float] = None
    accuracy: Optional[float] = None  # meters
    timestamp: datetime = field(default_factory=timezone.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'lat': self.latitude,
            'lng': self.longitude,
            'altitude': self.altitude,
            'accuracy': self.accuracy,
            'timestamp': self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GeoPoint':
        return cls(
            latitude=data.get('lat', data.get('latitude', 0)),
            longitude=data.get('lng', data.get('longitude', 0)),
            altitude=data.get('altitude'),
            accuracy=data.get('accuracy'),
            timestamp=datetime.fromisoformat(data['timestamp'])
            if 'timestamp' in data else timezone.now(),
        )


@dataclass
class LocationUpdate:
    """تحديث موقع"""

    delivery_id: int
    driver_id: int
    point: GeoPoint
    speed: float = 0.0  # km/h
    heading: float = 0.0  # degrees (0-360)
    battery_level: Optional[int] = None
    is_moving: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            'delivery_id': self.delivery_id,
            'driver_id': self.driver_id,
            'point': self.point.to_dict(),
            'speed': self.speed,
            'heading': self.heading,
            'battery_level': self.battery_level,
            'is_moving': self.is_moving,
        }


@dataclass
class Geofence:
    """سياج جغرافي"""

    id: str
    name: str
    center: GeoPoint
    radius: float  # meters
    type: str = 'circle'  # circle, polygon
    polygon_points: Optional[List[GeoPoint]] = None
    trigger_on_enter: bool = True
    trigger_on_exit: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ETAResult:
    """نتيجة حساب ETA"""

    estimated_minutes: int
    estimated_arrival: datetime
    distance_remaining: float  # km
    traffic_factor: float = 1.0
    confidence: float = 0.8  # 0-1


@dataclass
class DeliveryTrackingInfo:
    """معلومات تتبع التوصيل"""

    delivery_id: int
    order_id: int
    driver_id: int
    status: str

    # الموقع الحالي
    current_location: Optional[GeoPoint] = None
    speed: float = 0.0
    heading: float = 0.0

    # النقاط
    pickup_location: Optional[GeoPoint] = None
    dropoff_location: Optional[GeoPoint] = None

    # ETA
    eta: Optional[ETAResult] = None

    # المسار
    route_points: List[GeoPoint] = field(default_factory=list)
    distance_traveled: float = 0.0  # km
    total_distance: float = 0.0  # km

    # التوقيت
    started_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    estimated_delivery_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'delivery_id': self.delivery_id,
            'order_id': self.order_id,
            'driver_id': self.driver_id,
            'status': self.status,
            'current_location': self.current_location.to_dict() if self.current_location else None,
            'speed': self.speed,
            'heading': self.heading,
            'eta': {
                'minutes': self.eta.estimated_minutes,
                'arrival': self.eta.estimated_arrival.isoformat(),
                'distance': self.eta.distance_remaining,
                'confidence': self.eta.confidence,
            } if self.eta else None,
            'distance_traveled': self.distance_traveled,
            'total_distance': self.total_distance,
            'started_at': self.started_at.isoformat() if self.started_at else None,
        }


# =============================================================================
# Geo Utilities
# =============================================================================

class GeoUtils:
    """أدوات جغرافية"""

    EARTH_RADIUS_KM = 6371.0

    @staticmethod
    def haversine_distance(
        point1: GeoPoint,
        point2: GeoPoint,
    ) -> float:
        """حساب المسافة بين نقطتين (كم)"""
        lat1 = math.radians(point1.latitude)
        lat2 = math.radians(point2.latitude)
        dlat = math.radians(point2.latitude - point1.latitude)
        dlon = math.radians(point2.longitude - point1.longitude)

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return GeoUtils.EARTH_RADIUS_KM * c

    @staticmethod
    def bearing(point1: GeoPoint, point2: GeoPoint) -> float:
        """حساب الاتجاه بين نقطتين (درجات)"""
        lat1 = math.radians(point1.latitude)
        lat2 = math.radians(point2.latitude)
        dlon = math.radians(point2.longitude - point1.longitude)

        x = math.sin(dlon) * math.cos(lat2)
        y = (
            math.cos(lat1) * math.sin(lat2)
            - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        )

        bearing = math.degrees(math.atan2(x, y))
        return (bearing + 360) % 360

    @staticmethod
    def is_point_in_circle(
        point: GeoPoint,
        center: GeoPoint,
        radius_meters: float,
    ) -> bool:
        """التحقق من وجود نقطة داخل دائرة"""
        distance = GeoUtils.haversine_distance(point, center) * 1000
        return distance <= radius_meters

    @staticmethod
    def is_point_in_polygon(
        point: GeoPoint,
        polygon: List[GeoPoint],
    ) -> bool:
        """التحقق من وجود نقطة داخل مضلع"""
        n = len(polygon)
        inside = False

        p1x, p1y = polygon[0].longitude, polygon[0].latitude
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n].longitude, polygon[i % n].latitude

            if point.latitude > min(p1y, p2y):
                if point.latitude <= max(p1y, p2y):
                    if point.longitude <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (
                                (point.latitude - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                            )
                        if p1x == p2x or point.longitude <= xinters:
                            inside = not inside

            p1x, p1y = p2x, p2y

        return inside

    @staticmethod
    def calculate_speed(
        point1: GeoPoint,
        point2: GeoPoint,
    ) -> float:
        """حساب السرعة بين نقطتين (كم/س)"""
        distance = GeoUtils.haversine_distance(point1, point2)
        time_diff = (point2.timestamp - point1.timestamp).total_seconds()

        if time_diff <= 0:
            return 0.0

        return (distance / time_diff) * 3600  # km/h

    @staticmethod
    def simplify_path(
        points: List[GeoPoint],
        tolerance: float = 0.0001,
    ) -> List[GeoPoint]:
        """تبسيط المسار (Douglas-Peucker)"""
        if len(points) <= 2:
            return points

        # إيجاد النقطة الأبعد
        max_distance = 0
        max_index = 0

        start = points[0]
        end = points[-1]

        for i in range(1, len(points) - 1):
            distance = GeoUtils._perpendicular_distance(points[i], start, end)
            if distance > max_distance:
                max_distance = distance
                max_index = i

        # إذا كانت المسافة أكبر من التسامح، نقسم
        if max_distance > tolerance:
            left = GeoUtils.simplify_path(points[: max_index + 1], tolerance)
            right = GeoUtils.simplify_path(points[max_index:], tolerance)
            return left[:-1] + right

        return [start, end]

    @staticmethod
    def _perpendicular_distance(
        point: GeoPoint,
        line_start: GeoPoint,
        line_end: GeoPoint,
    ) -> float:
        """حساب المسافة العمودية لنقطة عن خط"""
        dx = line_end.longitude - line_start.longitude
        dy = line_end.latitude - line_start.latitude

        if dx == 0 and dy == 0:
            return GeoUtils.haversine_distance(point, line_start)

        t = max(
            0,
            min(
                1,
                (
                    (point.longitude - line_start.longitude) * dx
                    + (point.latitude - line_start.latitude) * dy
                )
                / (dx * dx + dy * dy),
            ),
        )

        nearest = GeoPoint(
            latitude=line_start.latitude + t * dy,
            longitude=line_start.longitude + t * dx,
        )

        return GeoUtils.haversine_distance(point, nearest)


# =============================================================================
# ETA Calculator
# =============================================================================

class ETACalculator:
    """
    حاسبة وقت الوصول المتوقع

    تستخدم:
    - المسافة المتبقية
    - السرعة الحالية
    - معامل حركة المرور
    - البيانات التاريخية
    """

    # متوسط السرعات حسب النوع (كم/س)
    SPEED_PROFILES = {
        'city': 25,
        'suburban': 40,
        'highway': 80,
        'default': 30,
    }

    # معاملات حركة المرور حسب الوقت
    TRAFFIC_FACTORS = {
        (7, 9): 1.5,  # ساعة الذروة الصباحية
        (12, 14): 1.2,  # وقت الغداء
        (16, 19): 1.5,  # ساعة الذروة المسائية
        (21, 6): 0.8,  # الليل
    }

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            self._redis = await aioredis.from_url(redis_url)
        return self._redis

    def calculate(
        self,
        current_location: GeoPoint,
        destination: GeoPoint,
        current_speed: float = 0.0,
        road_type: str = 'default',
    ) -> ETAResult:
        """حساب ETA"""
        # المسافة المتبقية
        distance = GeoUtils.haversine_distance(current_location, destination)

        # السرعة المستخدمة
        if current_speed > 5:
            speed = current_speed
        else:
            speed = self.SPEED_PROFILES.get(road_type, self.SPEED_PROFILES['default'])

        # معامل حركة المرور
        traffic_factor = self._get_traffic_factor()

        # حساب الوقت
        adjusted_speed = speed / traffic_factor
        time_hours = distance / max(adjusted_speed, 1)
        time_minutes = int(time_hours * 60)

        # الثقة
        confidence = self._calculate_confidence(current_speed, distance)

        return ETAResult(
            estimated_minutes=max(1, time_minutes),
            estimated_arrival=timezone.now() + timedelta(minutes=time_minutes),
            distance_remaining=round(distance, 2),
            traffic_factor=traffic_factor,
            confidence=confidence,
        )

    def _get_traffic_factor(self) -> float:
        """الحصول على معامل حركة المرور"""
        current_hour = timezone.localtime().hour

        for (start, end), factor in self.TRAFFIC_FACTORS.items():
            if start <= end:
                if start <= current_hour < end:
                    return factor
            else:
                if current_hour >= start or current_hour < end:
                    return factor

        return 1.0

    def _calculate_confidence(
        self,
        current_speed: float,
        distance: float,
    ) -> float:
        """حساب مستوى الثقة"""
        confidence = 0.8

        # السرعة العالية تزيد الثقة
        if current_speed > 20:
            confidence += 0.1

        # المسافة القصيرة تزيد الثقة
        if distance < 5:
            confidence += 0.1
        elif distance > 20:
            confidence -= 0.1

        return min(1.0, max(0.5, confidence))

    async def get_historical_eta(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
    ) -> Optional[int]:
        """الحصول على ETA من البيانات التاريخية"""
        redis = await self._get_redis()

        # مفتاح المسار
        route_key = f"eta:history:{origin.latitude:.3f},{origin.longitude:.3f}:{destination.latitude:.3f},{destination.longitude:.3f}"

        # الحصول على المتوسط
        data = await redis.hgetall(route_key)
        if data:
            total_time = int(data.get(b'total_time', 0))
            count = int(data.get(b'count', 0))
            if count > 0:
                return total_time // count

        return None

    async def record_actual_time(
        self,
        origin: GeoPoint,
        destination: GeoPoint,
        actual_minutes: int,
    ) -> None:
        """تسجيل الوقت الفعلي للتحسين"""
        redis = await self._get_redis()

        route_key = f"eta:history:{origin.latitude:.3f},{origin.longitude:.3f}:{destination.latitude:.3f},{destination.longitude:.3f}"

        await redis.hincrby(route_key, 'total_time', actual_minutes)
        await redis.hincrby(route_key, 'count', 1)
        await redis.expire(route_key, 86400 * 30)  # 30 يوم


# =============================================================================
# Geofencing Service
# =============================================================================

class GeofenceService:
    """
    خدمة السياج الجغرافي

    تراقب دخول وخروج المركبات من مناطق محددة
    """

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        self._geofences: Dict[str, Geofence] = {}
        self._callbacks: List[Callable] = []

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            self._redis = await aioredis.from_url(redis_url)
        return self._redis

    def register_geofence(self, geofence: Geofence) -> None:
        """تسجيل سياج جغرافي"""
        self._geofences[geofence.id] = geofence
        logger.info(f"Registered geofence: {geofence.id} - {geofence.name}")

    def unregister_geofence(self, geofence_id: str) -> None:
        """إلغاء تسجيل سياج"""
        if geofence_id in self._geofences:
            del self._geofences[geofence_id]

    def add_callback(
        self,
        callback: Callable[[str, str, str, GeoPoint], None],
    ) -> None:
        """إضافة callback للأحداث"""
        self._callbacks.append(callback)

    async def check_location(
        self,
        entity_id: str,
        point: GeoPoint,
    ) -> List[Dict[str, Any]]:
        """التحقق من موقع ضد السياجات"""
        redis = await self._get_redis()
        events = []

        for geofence in self._geofences.values():
            # التحقق من الموقع
            if geofence.type == 'circle':
                is_inside = GeoUtils.is_point_in_circle(
                    point,
                    geofence.center,
                    geofence.radius,
                )
            elif geofence.type == 'polygon' and geofence.polygon_points:
                is_inside = GeoUtils.is_point_in_polygon(point, geofence.polygon_points)
            else:
                continue

            # الحصول على الحالة السابقة
            state_key = f"geofence:state:{geofence.id}:{entity_id}"
            was_inside = await redis.get(state_key)
            was_inside = was_inside == b'1' if was_inside else False

            # تحديث الحالة
            await redis.set(state_key, '1' if is_inside else '0', ex=3600)

            # التحقق من الأحداث
            if is_inside and not was_inside and geofence.trigger_on_enter:
                events.append({
                    'type': 'enter',
                    'geofence_id': geofence.id,
                    'geofence_name': geofence.name,
                    'entity_id': entity_id,
                    'point': point.to_dict(),
                })
                await self._trigger_callbacks('enter', geofence.id, entity_id, point)

            elif not is_inside and was_inside and geofence.trigger_on_exit:
                events.append({
                    'type': 'exit',
                    'geofence_id': geofence.id,
                    'geofence_name': geofence.name,
                    'entity_id': entity_id,
                    'point': point.to_dict(),
                })
                await self._trigger_callbacks('exit', geofence.id, entity_id, point)

        return events

    async def _trigger_callbacks(
        self,
        event_type: str,
        geofence_id: str,
        entity_id: str,
        point: GeoPoint,
    ) -> None:
        """استدعاء callbacks"""
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event_type, geofence_id, entity_id, point)
                else:
                    callback(event_type, geofence_id, entity_id, point)
            except Exception as e:
                logger.error(f"Geofence callback error: {e}")

    async def create_delivery_geofences(
        self,
        delivery_id: int,
        pickup_location: GeoPoint,
        dropoff_location: GeoPoint,
    ) -> List[Geofence]:
        """إنشاء سياجات لتوصيل"""
        geofences = []

        # سياج نقطة الاستلام
        pickup_geofence = Geofence(
            id=f"delivery_{delivery_id}_pickup",
            name="نقطة الاستلام",
            center=pickup_location,
            radius=100,  # 100 متر
            trigger_on_enter=True,
            trigger_on_exit=True,
            metadata={'delivery_id': delivery_id, 'point_type': 'pickup'},
        )
        self.register_geofence(pickup_geofence)
        geofences.append(pickup_geofence)

        # سياج نقطة التسليم
        dropoff_geofence = Geofence(
            id=f"delivery_{delivery_id}_dropoff",
            name="نقطة التسليم",
            center=dropoff_location,
            radius=100,
            trigger_on_enter=True,
            trigger_on_exit=False,
            metadata={'delivery_id': delivery_id, 'point_type': 'dropoff'},
        )
        self.register_geofence(dropoff_geofence)
        geofences.append(dropoff_geofence)

        return geofences

    def remove_delivery_geofences(self, delivery_id: int) -> None:
        """إزالة سياجات التوصيل"""
        self.unregister_geofence(f"delivery_{delivery_id}_pickup")
        self.unregister_geofence(f"delivery_{delivery_id}_dropoff")


# =============================================================================
# Tracking Service
# =============================================================================

class TrackingService:
    """
    خدمة التتبع الرئيسية

    تدير:
    - تحديثات المواقع
    - حساب ETA
    - Geofencing
    - بث التحديثات
    """

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        self._eta_calculator = ETACalculator()
        self._geofence_service = GeofenceService()
        self._active_deliveries: Dict[int, DeliveryTrackingInfo] = {}

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            self._redis = await aioredis.from_url(redis_url)
        return self._redis

    async def start_tracking(
        self,
        delivery_id: int,
        order_id: int,
        driver_id: int,
        pickup_location: GeoPoint,
        dropoff_location: GeoPoint,
    ) -> DeliveryTrackingInfo:
        """بدء تتبع توصيل"""
        info = DeliveryTrackingInfo(
            delivery_id=delivery_id,
            order_id=order_id,
            driver_id=driver_id,
            status='started',
            pickup_location=pickup_location,
            dropoff_location=dropoff_location,
            total_distance=GeoUtils.haversine_distance(pickup_location, dropoff_location),
            started_at=timezone.now(),
        )

        self._active_deliveries[delivery_id] = info

        # حفظ في Redis
        await self._save_tracking_info(info)

        # إنشاء سياجات
        await self._geofence_service.create_delivery_geofences(
            delivery_id,
            pickup_location,
            dropoff_location,
        )

        # نشر حدث البدء
        await self._publish_tracking_event('tracking.started', {
            'delivery_id': delivery_id,
            'order_id': order_id,
            'driver_id': driver_id,
        })

        return info

    async def update_location(self, update: LocationUpdate) -> DeliveryTrackingInfo:
        """تحديث موقع التوصيل"""
        info = self._active_deliveries.get(update.delivery_id)
        if not info:
            info = await self._load_tracking_info(update.delivery_id)
            if not info:
                raise ValueError(f"Delivery {update.delivery_id} not found")
            self._active_deliveries[update.delivery_id] = info

        # تحديث الموقع
        previous_location = info.current_location
        info.current_location = update.point
        info.speed = update.speed
        info.heading = update.heading

        # حساب المسافة المقطوعة
        if previous_location:
            info.distance_traveled += GeoUtils.haversine_distance(
                previous_location,
                update.point,
            )

        # إضافة للمسار
        info.route_points.append(update.point)

        # تبسيط المسار إذا كان طويلاً
        if len(info.route_points) > 100:
            info.route_points = GeoUtils.simplify_path(info.route_points)

        # حساب ETA
        if info.dropoff_location:
            info.eta = self._eta_calculator.calculate(
                update.point,
                info.dropoff_location,
                update.speed,
            )
            info.estimated_delivery_at = info.eta.estimated_arrival

        # حفظ في Redis
        await self._save_tracking_info(info)
        await self._save_location_history(update)

        # التحقق من Geofencing
        geofence_events = await self._geofence_service.check_location(
            f"delivery_{update.delivery_id}",
            update.point,
        )

        for event in geofence_events:
            await self._handle_geofence_event(info, event)

        # نشر تحديث الموقع
        await self._broadcast_location_update(info)

        # نشر حدث
        await publish_event(DeliveryLocationUpdatedEvent(
            delivery_id=update.delivery_id,
            driver_id=update.driver_id,
            latitude=update.point.latitude,
            longitude=update.point.longitude,
            speed=update.speed,
            heading=update.heading,
            accuracy=update.point.accuracy or 0,
            eta_minutes=info.eta.estimated_minutes if info.eta else None,
        ))

        return info

    async def get_tracking_info(self, delivery_id: int) -> Optional[DeliveryTrackingInfo]:
        """الحصول على معلومات التتبع"""
        info = self._active_deliveries.get(delivery_id)
        if not info:
            info = await self._load_tracking_info(delivery_id)
        return info

    async def stop_tracking(self, delivery_id: int, final_status: str) -> None:
        """إيقاف تتبع توصيل"""
        info = self._active_deliveries.get(delivery_id)

        if info:
            info.status = final_status

            # تسجيل الوقت الفعلي لتحسين ETA
            if info.started_at and info.pickup_location and info.dropoff_location:
                actual_minutes = int(
                    (timezone.now() - info.started_at).total_seconds() / 60
                )
                await self._eta_calculator.record_actual_time(
                    info.pickup_location,
                    info.dropoff_location,
                    actual_minutes,
                )

        # إزالة السياجات
        self._geofence_service.remove_delivery_geofences(delivery_id)

        # حذف من الذاكرة
        if delivery_id in self._active_deliveries:
            del self._active_deliveries[delivery_id]

        # نشر حدث الإيقاف
        await self._publish_tracking_event('tracking.stopped', {
            'delivery_id': delivery_id,
            'status': final_status,
        })

    async def get_location_history(
        self,
        delivery_id: int,
        limit: int = 100,
    ) -> List[LocationUpdate]:
        """الحصول على سجل المواقع"""
        redis = await self._get_redis()

        key = f"tracking:history:{delivery_id}"
        items = await redis.lrange(key, 0, limit - 1)

        history = []
        for item in items:
            data = json.loads(item)
            history.append(LocationUpdate(
                delivery_id=data['delivery_id'],
                driver_id=data['driver_id'],
                point=GeoPoint.from_dict(data['point']),
                speed=data.get('speed', 0),
                heading=data.get('heading', 0),
            ))

        return history

    async def subscribe_to_delivery(
        self,
        delivery_id: int,
        user_id: int,
    ) -> None:
        """الاشتراك في تحديثات توصيل"""
        from apps.realtime.connection import get_connection_manager

        manager = get_connection_manager()

        # إضافة المستخدم لمجموعة التوصيل
        connections = manager.get_user_connections(user_id)
        for connection_id in connections:
            await manager.join_group(connection_id, f"tracking_{delivery_id}")

    async def unsubscribe_from_delivery(
        self,
        delivery_id: int,
        user_id: int,
    ) -> None:
        """إلغاء الاشتراك"""
        from apps.realtime.connection import get_connection_manager

        manager = get_connection_manager()

        connections = manager.get_user_connections(user_id)
        for connection_id in connections:
            await manager.leave_group(connection_id, f"tracking_{delivery_id}")

    # =========================================================================
    # Internal Methods
    # =========================================================================

    async def _save_tracking_info(self, info: DeliveryTrackingInfo) -> None:
        """حفظ معلومات التتبع"""
        redis = await self._get_redis()

        key = f"tracking:info:{info.delivery_id}"
        data = {
            'delivery_id': info.delivery_id,
            'order_id': info.order_id,
            'driver_id': info.driver_id,
            'status': info.status,
            'current_location': info.current_location.to_dict() if info.current_location else None,
            'speed': info.speed,
            'heading': info.heading,
            'pickup_location': info.pickup_location.to_dict() if info.pickup_location else None,
            'dropoff_location': info.dropoff_location.to_dict() if info.dropoff_location else None,
            'distance_traveled': info.distance_traveled,
            'total_distance': info.total_distance,
            'started_at': info.started_at.isoformat() if info.started_at else None,
        }

        await redis.set(key, json.dumps(data), ex=86400)  # 24 ساعة

    async def _load_tracking_info(
        self,
        delivery_id: int,
    ) -> Optional[DeliveryTrackingInfo]:
        """تحميل معلومات التتبع"""
        redis = await self._get_redis()

        key = f"tracking:info:{delivery_id}"
        data = await redis.get(key)

        if not data:
            return None

        data = json.loads(data)

        return DeliveryTrackingInfo(
            delivery_id=data['delivery_id'],
            order_id=data['order_id'],
            driver_id=data['driver_id'],
            status=data['status'],
            current_location=GeoPoint.from_dict(data['current_location'])
            if data.get('current_location') else None,
            speed=data.get('speed', 0),
            heading=data.get('heading', 0),
            pickup_location=GeoPoint.from_dict(data['pickup_location'])
            if data.get('pickup_location') else None,
            dropoff_location=GeoPoint.from_dict(data['dropoff_location'])
            if data.get('dropoff_location') else None,
            distance_traveled=data.get('distance_traveled', 0),
            total_distance=data.get('total_distance', 0),
            started_at=datetime.fromisoformat(data['started_at'])
            if data.get('started_at') else None,
        )

    async def _save_location_history(self, update: LocationUpdate) -> None:
        """حفظ سجل المواقع"""
        redis = await self._get_redis()

        key = f"tracking:history:{update.delivery_id}"
        await redis.lpush(key, json.dumps(update.to_dict()))
        await redis.ltrim(key, 0, 999)  # الاحتفاظ بـ 1000 نقطة
        await redis.expire(key, 86400 * 7)  # 7 أيام

    async def _broadcast_location_update(
        self,
        info: DeliveryTrackingInfo,
    ) -> None:
        """بث تحديث الموقع"""
        from apps.realtime.connection import get_connection_manager

        manager = get_connection_manager()

        await manager.broadcast_to_group(
            f"tracking_{info.delivery_id}",
            {
                'type': 'tracking.location_update',
                'data': info.to_dict(),
            },
        )

    async def _handle_geofence_event(
        self,
        info: DeliveryTrackingInfo,
        event: Dict[str, Any],
    ) -> None:
        """معالجة حدث geofence"""
        geofence_id = event['geofence_id']

        if 'pickup' in geofence_id:
            if event['type'] == 'enter':
                info.status = 'at_pickup'
                await self._publish_tracking_event('tracking.at_pickup', {
                    'delivery_id': info.delivery_id,
                })
            elif event['type'] == 'exit':
                info.status = 'en_route'
                info.picked_up_at = timezone.now()
                await self._publish_tracking_event('tracking.picked_up', {
                    'delivery_id': info.delivery_id,
                })

        elif 'dropoff' in geofence_id:
            if event['type'] == 'enter':
                info.status = 'arrived'
                await self._publish_tracking_event('tracking.arrived', {
                    'delivery_id': info.delivery_id,
                })

    async def _publish_tracking_event(
        self,
        event_type: str,
        data: Dict[str, Any],
    ) -> None:
        """نشر حدث تتبع"""
        redis = await self._get_redis()

        await redis.publish(
            f"tracking:events:{event_type}",
            json.dumps(data),
        )


# =============================================================================
# Global Service Instance
# =============================================================================

_tracking_service: Optional[TrackingService] = None


def get_tracking_service() -> TrackingService:
    """الحصول على خدمة التتبع"""
    global _tracking_service
    if _tracking_service is None:
        _tracking_service = TrackingService()
    return _tracking_service
