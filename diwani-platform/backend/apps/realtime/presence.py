"""
نظام الحضور (Presence System)
================================

يوفر:
- تتبع حالة تواجد المستخدمين
- إشعارات الدخول والخروج
- آخر ظهور
- الأجهزة المتصلة
- حالات مخصصة (متصل، مشغول، بعيد)
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

import redis.asyncio as aioredis
from django.conf import settings
from django.utils import timezone

from .events import (
    BaseEvent,
    EventBus,
    UserPresenceChangedEvent,
    get_event_bus,
    publish_event,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Presence Status
# =============================================================================

class PresenceStatus(str, Enum):
    """حالات التواجد"""

    ONLINE = "online"  # متصل
    AWAY = "away"  # بعيد
    BUSY = "busy"  # مشغول
    DO_NOT_DISTURB = "dnd"  # الرجاء عدم الإزعاج
    INVISIBLE = "invisible"  # مخفي
    OFFLINE = "offline"  # غير متصل


class ActivityType(str, Enum):
    """أنواع النشاط"""

    BROWSING = "browsing"  # تصفح
    ORDERING = "ordering"  # طلب
    CHATTING = "chatting"  # محادثة
    SEARCHING = "searching"  # بحث
    IDLE = "idle"  # خامل


# =============================================================================
# Presence Data
# =============================================================================

@dataclass
class DeviceInfo:
    """معلومات الجهاز"""

    device_id: str = ""
    device_type: str = "unknown"  # mobile, tablet, desktop, other
    device_name: Optional[str] = None
    os: Optional[str] = None
    browser: Optional[str] = None
    app_version: Optional[str] = None
    push_token: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'device_id': self.device_id,
            'device_type': self.device_type,
            'device_name': self.device_name,
            'os': self.os,
            'browser': self.browser,
            'app_version': self.app_version,
        }


@dataclass
class UserPresence:
    """حالة تواجد المستخدم"""

    user_id: int
    status: PresenceStatus = PresenceStatus.OFFLINE
    custom_status: Optional[str] = None  # حالة مخصصة نصية
    activity: Optional[ActivityType] = None
    activity_details: Optional[str] = None

    # التوقيت
    last_seen: datetime = field(default_factory=timezone.now)
    status_changed_at: datetime = field(default_factory=timezone.now)
    session_started: Optional[datetime] = None

    # الأجهزة
    devices: Dict[str, DeviceInfo] = field(default_factory=dict)
    active_device_id: Optional[str] = None

    # الموقع (اختياري)
    location: Optional[Dict[str, float]] = None  # {lat, lng}
    timezone: Optional[str] = None

    # الإعدادات
    show_activity: bool = True
    show_last_seen: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'status': self.status.value,
            'custom_status': self.custom_status,
            'activity': self.activity.value if self.activity else None,
            'activity_details': self.activity_details,
            'last_seen': self.last_seen.isoformat() if self.show_last_seen else None,
            'devices_count': len(self.devices),
            'active_device': self.active_device_id,
        }

    def to_public_dict(self) -> Dict[str, Any]:
        """النسخة العامة (للمستخدمين الآخرين)"""
        data = {
            'user_id': self.user_id,
            'status': self.status.value if self.status != PresenceStatus.INVISIBLE else PresenceStatus.OFFLINE.value,
        }

        if self.show_activity and self.activity:
            data['activity'] = self.activity.value

        if self.show_last_seen:
            data['last_seen'] = self.last_seen.isoformat()

        if self.custom_status:
            data['custom_status'] = self.custom_status

        return data

    def is_online(self) -> bool:
        """هل المستخدم متصل؟"""
        return self.status in [
            PresenceStatus.ONLINE,
            PresenceStatus.AWAY,
            PresenceStatus.BUSY,
            PresenceStatus.DO_NOT_DISTURB,
        ]


# =============================================================================
# Presence Manager
# =============================================================================

class PresenceManager:
    """
    مدير نظام الحضور

    يتتبع حالة تواجد المستخدمين في الوقت الفعلي
    مع دعم للتوزيع عبر عدة خوادم
    """

    _instance: Optional['PresenceManager'] = None

    # Thresholds
    ONLINE_THRESHOLD = 30  # ثانية
    AWAY_THRESHOLD = 300  # 5 دقائق
    OFFLINE_THRESHOLD = 600  # 10 دقائق

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._local_presence: Dict[int, UserPresence] = {}
        self._subscribers: Dict[int, Set[int]] = {}  # user_id -> set of subscriber user_ids
        self._presence_callbacks: List[Callable] = []

        self._redis: Optional[aioredis.Redis] = None
        self._pubsub: Optional[aioredis.client.PubSub] = None
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None

        self._key_prefix = "presence:"
        self._channel_prefix = "presence:events:"

        self._initialized = True

    async def _get_redis(self) -> aioredis.Redis:
        """الحصول على اتصال Redis"""
        if self._redis is None:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            self._redis = await aioredis.from_url(redis_url)
        return self._redis

    # =========================================================================
    # Core Operations
    # =========================================================================

    async def set_online(
        self,
        user_id: int,
        device_info: Optional[DeviceInfo] = None,
        status: PresenceStatus = PresenceStatus.ONLINE,
    ) -> UserPresence:
        """تعيين المستخدم كمتصل"""
        presence = await self.get_presence(user_id)

        old_status = presence.status
        presence.status = status
        presence.last_seen = timezone.now()

        if device_info:
            presence.devices[device_info.device_id] = device_info
            presence.active_device_id = device_info.device_id

        if old_status == PresenceStatus.OFFLINE:
            presence.session_started = timezone.now()

        if old_status != status:
            presence.status_changed_at = timezone.now()

        # حفظ الحالة
        await self._save_presence(presence)

        # إشعار بالتغيير
        if old_status != status:
            await self._notify_presence_change(presence, old_status)

        return presence

    async def set_offline(
        self,
        user_id: int,
        device_id: Optional[str] = None,
    ) -> UserPresence:
        """تعيين المستخدم كغير متصل"""
        presence = await self.get_presence(user_id)

        # إزالة الجهاز
        if device_id and device_id in presence.devices:
            del presence.devices[device_id]

            # إذا لا يزال هناك أجهزة أخرى، لا نغير الحالة
            if presence.devices:
                presence.active_device_id = next(iter(presence.devices.keys()))
                await self._save_presence(presence)
                return presence

        old_status = presence.status
        presence.status = PresenceStatus.OFFLINE
        presence.last_seen = timezone.now()
        presence.active_device_id = None
        presence.session_started = None

        if old_status != PresenceStatus.OFFLINE:
            presence.status_changed_at = timezone.now()

        await self._save_presence(presence)

        if old_status != PresenceStatus.OFFLINE:
            await self._notify_presence_change(presence, old_status)

        return presence

    async def update_activity(
        self,
        user_id: int,
        activity: ActivityType,
        details: Optional[str] = None,
    ) -> UserPresence:
        """تحديث نشاط المستخدم"""
        presence = await self.get_presence(user_id)

        presence.activity = activity
        presence.activity_details = details
        presence.last_seen = timezone.now()

        # إذا كان الحالة offline، نعيده online
        if presence.status == PresenceStatus.OFFLINE:
            old_status = presence.status
            presence.status = PresenceStatus.ONLINE
            await self._notify_presence_change(presence, old_status)

        await self._save_presence(presence)
        return presence

    async def set_custom_status(
        self,
        user_id: int,
        custom_status: Optional[str],
    ) -> UserPresence:
        """تعيين حالة مخصصة"""
        presence = await self.get_presence(user_id)
        presence.custom_status = custom_status
        await self._save_presence(presence)
        return presence

    async def heartbeat(
        self,
        user_id: int,
        device_id: Optional[str] = None,
    ) -> None:
        """تحديث نبضة القلب"""
        redis = await self._get_redis()

        # تحديث last_seen في Redis
        key = f"{self._key_prefix}user:{user_id}"
        now = timezone.now().isoformat()

        await redis.hset(key, 'last_seen', now)
        await redis.expire(key, self.OFFLINE_THRESHOLD * 2)

        # تحديث محلي
        if user_id in self._local_presence:
            self._local_presence[user_id].last_seen = timezone.now()

    async def get_presence(self, user_id: int) -> UserPresence:
        """الحصول على حالة تواجد مستخدم"""
        # البحث محلياً أولاً
        if user_id in self._local_presence:
            return self._local_presence[user_id]

        # البحث في Redis
        redis = await self._get_redis()
        key = f"{self._key_prefix}user:{user_id}"
        data = await redis.hgetall(key)

        if data:
            presence = self._deserialize_presence(user_id, data)
        else:
            presence = UserPresence(user_id=user_id)

        self._local_presence[user_id] = presence
        return presence

    async def get_multiple_presences(
        self,
        user_ids: List[int],
    ) -> Dict[int, UserPresence]:
        """الحصول على حالات تواجد متعددة"""
        result = {}
        missing_ids = []

        # البحث محلياً أولاً
        for user_id in user_ids:
            if user_id in self._local_presence:
                result[user_id] = self._local_presence[user_id]
            else:
                missing_ids.append(user_id)

        # البحث في Redis للمفقودين
        if missing_ids:
            redis = await self._get_redis()
            pipe = redis.pipeline()

            for user_id in missing_ids:
                pipe.hgetall(f"{self._key_prefix}user:{user_id}")

            responses = await pipe.execute()

            for user_id, data in zip(missing_ids, responses):
                if data:
                    presence = self._deserialize_presence(user_id, data)
                else:
                    presence = UserPresence(user_id=user_id)

                self._local_presence[user_id] = presence
                result[user_id] = presence

        return result

    async def get_online_users(
        self,
        limit: int = 100,
    ) -> List[UserPresence]:
        """الحصول على المستخدمين المتصلين"""
        redis = await self._get_redis()

        # الحصول على قائمة المتصلين من Redis Set
        online_key = f"{self._key_prefix}online"
        user_ids = await redis.smembers(online_key)

        online_users = []
        for uid in list(user_ids)[:limit]:
            try:
                user_id = int(uid)
                presence = await self.get_presence(user_id)
                if presence.is_online():
                    online_users.append(presence)
            except (ValueError, TypeError):
                continue

        return online_users

    async def get_online_count(self) -> int:
        """الحصول على عدد المتصلين"""
        redis = await self._get_redis()
        online_key = f"{self._key_prefix}online"
        return await redis.scard(online_key)

    # =========================================================================
    # Subscriptions
    # =========================================================================

    async def subscribe_to_user(
        self,
        subscriber_id: int,
        target_user_id: int,
    ) -> None:
        """الاشتراك في تحديثات مستخدم"""
        if target_user_id not in self._subscribers:
            self._subscribers[target_user_id] = set()
        self._subscribers[target_user_id].add(subscriber_id)

        # حفظ في Redis للتوزيع
        redis = await self._get_redis()
        await redis.sadd(
            f"{self._key_prefix}subscribers:{target_user_id}",
            subscriber_id,
        )

    async def unsubscribe_from_user(
        self,
        subscriber_id: int,
        target_user_id: int,
    ) -> None:
        """إلغاء الاشتراك"""
        if target_user_id in self._subscribers:
            self._subscribers[target_user_id].discard(subscriber_id)

        redis = await self._get_redis()
        await redis.srem(
            f"{self._key_prefix}subscribers:{target_user_id}",
            subscriber_id,
        )

    async def get_subscribers(self, user_id: int) -> Set[int]:
        """الحصول على المشتركين في تحديثات مستخدم"""
        redis = await self._get_redis()
        subscribers = await redis.smembers(
            f"{self._key_prefix}subscribers:{user_id}"
        )
        return {int(s) for s in subscribers}

    def add_presence_callback(
        self,
        callback: Callable[[UserPresence, PresenceStatus], None],
    ) -> None:
        """إضافة callback لتغييرات الحضور"""
        self._presence_callbacks.append(callback)

    # =========================================================================
    # Internal Methods
    # =========================================================================

    async def _save_presence(self, presence: UserPresence) -> None:
        """حفظ حالة التواجد"""
        redis = await self._get_redis()

        key = f"{self._key_prefix}user:{presence.user_id}"
        data = self._serialize_presence(presence)

        await redis.hset(key, mapping=data)
        await redis.expire(key, self.OFFLINE_THRESHOLD * 2)

        # تحديث قائمة المتصلين
        online_key = f"{self._key_prefix}online"
        if presence.is_online():
            await redis.sadd(online_key, presence.user_id)
        else:
            await redis.srem(online_key, presence.user_id)

        # تحديث محلي
        self._local_presence[presence.user_id] = presence

    def _serialize_presence(self, presence: UserPresence) -> Dict[str, str]:
        """تسلسل حالة التواجد"""
        return {
            'status': presence.status.value,
            'custom_status': presence.custom_status or '',
            'activity': presence.activity.value if presence.activity else '',
            'activity_details': presence.activity_details or '',
            'last_seen': presence.last_seen.isoformat(),
            'status_changed_at': presence.status_changed_at.isoformat(),
            'session_started': presence.session_started.isoformat() if presence.session_started else '',
            'devices': json.dumps({k: v.to_dict() for k, v in presence.devices.items()}),
            'active_device_id': presence.active_device_id or '',
            'show_activity': '1' if presence.show_activity else '0',
            'show_last_seen': '1' if presence.show_last_seen else '0',
        }

    def _deserialize_presence(
        self,
        user_id: int,
        data: Dict[bytes, bytes],
    ) -> UserPresence:
        """فك تسلسل حالة التواجد"""
        def get_str(key: str) -> str:
            value = data.get(key.encode(), b'')
            return value.decode() if value else ''

        presence = UserPresence(user_id=user_id)

        status_str = get_str('status')
        if status_str:
            presence.status = PresenceStatus(status_str)

        presence.custom_status = get_str('custom_status') or None

        activity_str = get_str('activity')
        if activity_str:
            presence.activity = ActivityType(activity_str)

        presence.activity_details = get_str('activity_details') or None

        last_seen_str = get_str('last_seen')
        if last_seen_str:
            presence.last_seen = datetime.fromisoformat(last_seen_str)

        status_changed_str = get_str('status_changed_at')
        if status_changed_str:
            presence.status_changed_at = datetime.fromisoformat(status_changed_str)

        session_started_str = get_str('session_started')
        if session_started_str:
            presence.session_started = datetime.fromisoformat(session_started_str)

        devices_str = get_str('devices')
        if devices_str:
            try:
                devices_data = json.loads(devices_str)
                presence.devices = {
                    k: DeviceInfo(**v) for k, v in devices_data.items()
                }
            except json.JSONDecodeError:
                pass

        presence.active_device_id = get_str('active_device_id') or None
        presence.show_activity = get_str('show_activity') == '1'
        presence.show_last_seen = get_str('show_last_seen') == '1'

        return presence

    async def _notify_presence_change(
        self,
        presence: UserPresence,
        old_status: PresenceStatus,
    ) -> None:
        """إشعار بتغيير الحضور"""
        # نشر حدث
        event = UserPresenceChangedEvent(
            user_id=presence.user_id,
            status=presence.status.value,
            last_seen=presence.last_seen,
            device_info=presence.devices.get(presence.active_device_id).to_dict()
            if presence.active_device_id and presence.active_device_id in presence.devices
            else None,
        )
        await publish_event(event)

        # استدعاء callbacks
        for callback in self._presence_callbacks:
            try:
                await callback(presence, old_status)
            except Exception as e:
                logger.error(f"Presence callback error: {e}")

        # نشر للمشتركين عبر Redis
        redis = await self._get_redis()
        channel = f"{self._channel_prefix}{presence.user_id}"
        await redis.publish(channel, json.dumps({
            'type': 'presence_changed',
            'user_id': presence.user_id,
            'old_status': old_status.value,
            'new_status': presence.status.value,
            'last_seen': presence.last_seen.isoformat(),
        }))

    # =========================================================================
    # Cleanup & Maintenance
    # =========================================================================

    async def start(self) -> None:
        """بدء نظام الحضور"""
        if self._running:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        # بدء الاستماع للأحداث
        asyncio.create_task(self._listen_for_events())

        logger.info("Presence system started")

    async def stop(self) -> None:
        """إيقاف نظام الحضور"""
        self._running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()

        if self._pubsub:
            await self._pubsub.unsubscribe()
            await self._pubsub.close()

        logger.info("Presence system stopped")

    async def _cleanup_loop(self) -> None:
        """حلقة التنظيف الدورية"""
        while self._running:
            try:
                await asyncio.sleep(60)  # كل دقيقة
                await self._check_stale_presences()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Presence cleanup error: {e}")

    async def _check_stale_presences(self) -> None:
        """التحقق من الحضور القديم"""
        now = timezone.now()
        away_threshold = now - timedelta(seconds=self.AWAY_THRESHOLD)
        offline_threshold = now - timedelta(seconds=self.OFFLINE_THRESHOLD)

        for user_id, presence in list(self._local_presence.items()):
            if not presence.is_online():
                continue

            # التحويل إلى away
            if (
                presence.status == PresenceStatus.ONLINE
                and presence.last_seen < away_threshold
            ):
                old_status = presence.status
                presence.status = PresenceStatus.AWAY
                await self._save_presence(presence)
                await self._notify_presence_change(presence, old_status)

            # التحويل إلى offline
            elif presence.last_seen < offline_threshold:
                old_status = presence.status
                presence.status = PresenceStatus.OFFLINE
                await self._save_presence(presence)
                await self._notify_presence_change(presence, old_status)

    async def _listen_for_events(self) -> None:
        """الاستماع لأحداث الحضور من الخوادم الأخرى"""
        redis = await self._get_redis()
        self._pubsub = redis.pubsub()

        await self._pubsub.psubscribe(f"{self._channel_prefix}*")

        while self._running:
            try:
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )
                if message and message['type'] == 'pmessage':
                    await self._handle_presence_event(message)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Presence event listener error: {e}")
                await asyncio.sleep(1)

    async def _handle_presence_event(self, message: Dict) -> None:
        """معالجة حدث حضور"""
        try:
            data = json.loads(message['data'])
            user_id = data.get('user_id')

            if user_id and user_id in self._local_presence:
                # تحديث الحالة المحلية
                new_status = PresenceStatus(data.get('new_status'))
                self._local_presence[user_id].status = new_status

                if 'last_seen' in data:
                    self._local_presence[user_id].last_seen = datetime.fromisoformat(
                        data['last_seen']
                    )
        except Exception as e:
            logger.error(f"Error handling presence event: {e}")


# =============================================================================
# Singleton Instance
# =============================================================================

def get_presence_manager() -> PresenceManager:
    """الحصول على مدير الحضور"""
    return PresenceManager()
