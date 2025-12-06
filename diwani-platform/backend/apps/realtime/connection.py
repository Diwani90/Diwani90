"""
نظام إدارة الاتصالات المتقدم
==============================

يوفر:
- إدارة اتصالات WebSocket
- Connection Pooling
- Heartbeat و Keepalive
- Reconnection Strategy
- Rate Limiting
- Backpressure Handling
- Connection State Machine
"""

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set

import redis.asyncio as aioredis
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

logger = logging.getLogger(__name__)
User = get_user_model()


# =============================================================================
# Connection States
# =============================================================================

class ConnectionState(str, Enum):
    """حالات الاتصال"""

    CONNECTING = "connecting"  # جاري الاتصال
    AUTHENTICATING = "authenticating"  # جاري المصادقة
    CONNECTED = "connected"  # متصل
    IDLE = "idle"  # خامل
    SUSPENDED = "suspended"  # معلق (backpressure)
    DISCONNECTING = "disconnecting"  # جاري قطع الاتصال
    DISCONNECTED = "disconnected"  # منقطع
    ERROR = "error"  # خطأ


class DisconnectReason(str, Enum):
    """أسباب قطع الاتصال"""

    NORMAL = "normal"  # إغلاق عادي
    TIMEOUT = "timeout"  # انتهاء المهلة
    AUTH_FAILED = "auth_failed"  # فشل المصادقة
    RATE_LIMITED = "rate_limited"  # تجاوز الحد
    ERROR = "error"  # خطأ
    SERVER_SHUTDOWN = "server_shutdown"  # إيقاف الخادم
    DUPLICATE_SESSION = "duplicate_session"  # جلسة مكررة
    BANNED = "banned"  # محظور


# =============================================================================
# Connection Info
# =============================================================================

@dataclass
class ConnectionInfo:
    """معلومات الاتصال"""

    connection_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    device_id: Optional[str] = None

    # معلومات الشبكة
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # الحالة
    state: ConnectionState = ConnectionState.CONNECTING
    created_at: datetime = field(default_factory=timezone.now)
    last_activity: datetime = field(default_factory=timezone.now)
    last_heartbeat: datetime = field(default_factory=timezone.now)

    # الإحصائيات
    messages_sent: int = 0
    messages_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    errors_count: int = 0

    # Rate Limiting
    message_timestamps: List[float] = field(default_factory=list)

    # المجموعات
    groups: Set[str] = field(default_factory=set)

    # البيانات الإضافية
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        return {
            'connection_id': self.connection_id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'device_id': self.device_id,
            'ip_address': self.ip_address,
            'state': self.state.value,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'groups': list(self.groups),
        }


# =============================================================================
# Rate Limiter
# =============================================================================

class RateLimiter:
    """
    محدد المعدل بخوارزمية Token Bucket

    يدعم:
    - حدود مختلفة لكل نوع رسالة
    - Burst handling
    - Gradual recovery
    """

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        burst_size: int = 20,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.burst_size = burst_size
        self._requests: Dict[str, List[float]] = {}

    def is_allowed(self, key: str) -> bool:
        """التحقق من السماح بالطلب"""
        now = time.time()
        window_start = now - self.window_seconds

        # تنظيف الطلبات القديمة
        if key in self._requests:
            self._requests[key] = [
                ts for ts in self._requests[key]
                if ts > window_start
            ]
        else:
            self._requests[key] = []

        # التحقق من الحد
        if len(self._requests[key]) >= self.max_requests:
            return False

        # التحقق من الـ burst
        recent_window = now - 1  # آخر ثانية
        recent_requests = sum(
            1 for ts in self._requests[key]
            if ts > recent_window
        )
        if recent_requests >= self.burst_size:
            return False

        # تسجيل الطلب
        self._requests[key].append(now)
        return True

    def get_remaining(self, key: str) -> int:
        """الحصول على عدد الطلبات المتبقية"""
        if key not in self._requests:
            return self.max_requests

        now = time.time()
        window_start = now - self.window_seconds
        current_requests = sum(
            1 for ts in self._requests[key]
            if ts > window_start
        )
        return max(0, self.max_requests - current_requests)

    def get_reset_time(self, key: str) -> float:
        """الحصول على وقت إعادة التعيين"""
        if key not in self._requests or not self._requests[key]:
            return 0

        oldest = min(self._requests[key])
        return max(0, oldest + self.window_seconds - time.time())


# =============================================================================
# Backpressure Handler
# =============================================================================

class BackpressureStrategy(str, Enum):
    """استراتيجيات التعامل مع الضغط"""

    DROP_OLDEST = "drop_oldest"  # إسقاط الأقدم
    DROP_NEWEST = "drop_newest"  # إسقاط الأحدث
    BLOCK = "block"  # الانتظار
    SAMPLE = "sample"  # أخذ عينات


@dataclass
class BackpressureConfig:
    """إعدادات الضغط الخلفي"""

    strategy: BackpressureStrategy = BackpressureStrategy.DROP_OLDEST
    queue_size: int = 1000
    high_watermark: int = 800
    low_watermark: int = 200
    sample_rate: float = 0.5  # للـ SAMPLE strategy


class MessageQueue:
    """
    طابور رسائل مع إدارة الضغط الخلفي

    يضمن عدم تجاوز الطاقة الاستيعابية
    """

    def __init__(self, config: BackpressureConfig):
        self.config = config
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=config.queue_size)
        self._backpressure_active = False
        self._dropped_count = 0
        self._sample_counter = 0

    async def put(self, message: Dict[str, Any]) -> bool:
        """إضافة رسالة للطابور"""
        current_size = self._queue.qsize()

        # التحقق من الضغط
        if current_size >= self.config.high_watermark:
            self._backpressure_active = True

            if self.config.strategy == BackpressureStrategy.DROP_NEWEST:
                self._dropped_count += 1
                return False

            elif self.config.strategy == BackpressureStrategy.DROP_OLDEST:
                try:
                    self._queue.get_nowait()
                    self._dropped_count += 1
                except asyncio.QueueEmpty:
                    pass

            elif self.config.strategy == BackpressureStrategy.SAMPLE:
                self._sample_counter += 1
                if self._sample_counter % int(1 / self.config.sample_rate) != 0:
                    self._dropped_count += 1
                    return False

            elif self.config.strategy == BackpressureStrategy.BLOCK:
                # الانتظار مع timeout
                try:
                    await asyncio.wait_for(
                        self._queue.put(message),
                        timeout=5.0,
                    )
                    return True
                except asyncio.TimeoutError:
                    self._dropped_count += 1
                    return False

        # التحقق من انتهاء الضغط
        if current_size <= self.config.low_watermark:
            self._backpressure_active = False

        try:
            self._queue.put_nowait(message)
            return True
        except asyncio.QueueFull:
            self._dropped_count += 1
            return False

    async def get(self) -> Optional[Dict[str, Any]]:
        """استخراج رسالة من الطابور"""
        try:
            return await asyncio.wait_for(
                self._queue.get(),
                timeout=1.0,
            )
        except asyncio.TimeoutError:
            return None

    @property
    def is_backpressure_active(self) -> bool:
        return self._backpressure_active

    @property
    def dropped_count(self) -> int:
        return self._dropped_count

    @property
    def size(self) -> int:
        return self._queue.qsize()


# =============================================================================
# Connection Manager
# =============================================================================

class ConnectionManager:
    """
    مدير الاتصالات المركزي

    يدير جميع اتصالات WebSocket مع:
    - تتبع الاتصالات النشطة
    - إدارة المجموعات
    - البث للمستخدمين
    - التنظيف التلقائي
    """

    _instance: Optional['ConnectionManager'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._connections: Dict[str, 'BaseWebSocketConsumer'] = {}
        self._user_connections: Dict[int, Set[str]] = {}
        self._group_connections: Dict[str, Set[str]] = {}
        self._connection_info: Dict[str, ConnectionInfo] = {}

        self._rate_limiter = RateLimiter(
            max_requests=100,
            window_seconds=60,
            burst_size=20,
        )

        self._redis: Optional[aioredis.Redis] = None
        self._cleanup_task: Optional[asyncio.Task] = None

        # إعدادات
        self._heartbeat_interval = 30  # ثانية
        self._connection_timeout = 120  # ثانية
        self._max_connections_per_user = 5

        self._initialized = True

    async def _get_redis(self) -> aioredis.Redis:
        """الحصول على اتصال Redis"""
        if self._redis is None:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            self._redis = await aioredis.from_url(redis_url)
        return self._redis

    async def register(
        self,
        consumer: 'BaseWebSocketConsumer',
        info: ConnectionInfo,
    ) -> bool:
        """تسجيل اتصال جديد"""
        connection_id = info.connection_id

        # التحقق من حد الاتصالات لكل مستخدم
        if info.user_id:
            user_connections = self._user_connections.get(info.user_id, set())
            if len(user_connections) >= self._max_connections_per_user:
                # إغلاق الاتصال الأقدم
                oldest_id = min(
                    user_connections,
                    key=lambda cid: self._connection_info[cid].created_at
                )
                await self.disconnect(
                    oldest_id,
                    DisconnectReason.DUPLICATE_SESSION,
                )

        # تسجيل الاتصال
        self._connections[connection_id] = consumer
        self._connection_info[connection_id] = info

        if info.user_id:
            if info.user_id not in self._user_connections:
                self._user_connections[info.user_id] = set()
            self._user_connections[info.user_id].add(connection_id)

        # حفظ في Redis للتوزيع
        await self._sync_to_redis(info)

        logger.info(f"Connection registered: {connection_id} (user: {info.user_id})")
        return True

    async def unregister(self, connection_id: str) -> None:
        """إلغاء تسجيل اتصال"""
        if connection_id not in self._connections:
            return

        info = self._connection_info.get(connection_id)

        # إزالة من المجموعات
        if info:
            for group in list(info.groups):
                await self.leave_group(connection_id, group)

            # إزالة من اتصالات المستخدم
            if info.user_id and info.user_id in self._user_connections:
                self._user_connections[info.user_id].discard(connection_id)
                if not self._user_connections[info.user_id]:
                    del self._user_connections[info.user_id]

        # إزالة من Redis
        await self._remove_from_redis(connection_id)

        # إزالة من الذاكرة
        del self._connections[connection_id]
        if connection_id in self._connection_info:
            del self._connection_info[connection_id]

        logger.info(f"Connection unregistered: {connection_id}")

    async def disconnect(
        self,
        connection_id: str,
        reason: DisconnectReason = DisconnectReason.NORMAL,
    ) -> None:
        """قطع اتصال"""
        if connection_id not in self._connections:
            return

        consumer = self._connections[connection_id]
        info = self._connection_info.get(connection_id)

        if info:
            info.state = ConnectionState.DISCONNECTING

        # إرسال رسالة الإغلاق
        try:
            await consumer.send_json({
                'type': 'connection.close',
                'reason': reason.value,
            })
            await consumer.close(code=1000 if reason == DisconnectReason.NORMAL else 1008)
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")

        await self.unregister(connection_id)

    async def join_group(self, connection_id: str, group_name: str) -> None:
        """إضافة اتصال لمجموعة"""
        if connection_id not in self._connections:
            return

        consumer = self._connections[connection_id]
        info = self._connection_info[connection_id]

        # إضافة للمجموعة في Channels
        await consumer.channel_layer.group_add(group_name, consumer.channel_name)

        # تتبع محلي
        if group_name not in self._group_connections:
            self._group_connections[group_name] = set()
        self._group_connections[group_name].add(connection_id)
        info.groups.add(group_name)

        logger.debug(f"Connection {connection_id} joined group {group_name}")

    async def leave_group(self, connection_id: str, group_name: str) -> None:
        """إزالة اتصال من مجموعة"""
        if connection_id not in self._connections:
            return

        consumer = self._connections[connection_id]
        info = self._connection_info.get(connection_id)

        # إزالة من المجموعة في Channels
        await consumer.channel_layer.group_discard(group_name, consumer.channel_name)

        # تحديث التتبع المحلي
        if group_name in self._group_connections:
            self._group_connections[group_name].discard(connection_id)
            if not self._group_connections[group_name]:
                del self._group_connections[group_name]

        if info:
            info.groups.discard(group_name)

    async def send_to_user(
        self,
        user_id: int,
        message: Dict[str, Any],
        exclude_connection: Optional[str] = None,
    ) -> int:
        """إرسال رسالة لجميع اتصالات مستخدم"""
        connection_ids = self._user_connections.get(user_id, set())
        sent_count = 0

        for connection_id in connection_ids:
            if connection_id == exclude_connection:
                continue

            if await self.send_to_connection(connection_id, message):
                sent_count += 1

        return sent_count

    async def send_to_connection(
        self,
        connection_id: str,
        message: Dict[str, Any],
    ) -> bool:
        """إرسال رسالة لاتصال محدد"""
        if connection_id not in self._connections:
            return False

        consumer = self._connections[connection_id]
        info = self._connection_info[connection_id]

        try:
            await consumer.send_json(message)
            info.messages_sent += 1
            info.bytes_sent += len(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Error sending to {connection_id}: {e}")
            info.errors_count += 1
            return False

    async def broadcast_to_group(
        self,
        group_name: str,
        message: Dict[str, Any],
        exclude_connection: Optional[str] = None,
    ) -> int:
        """بث رسالة لمجموعة"""
        connection_ids = self._group_connections.get(group_name, set())
        sent_count = 0

        for connection_id in connection_ids:
            if connection_id == exclude_connection:
                continue

            if await self.send_to_connection(connection_id, message):
                sent_count += 1

        return sent_count

    async def broadcast_all(
        self,
        message: Dict[str, Any],
        exclude_connection: Optional[str] = None,
    ) -> int:
        """بث لجميع الاتصالات"""
        sent_count = 0

        for connection_id in list(self._connections.keys()):
            if connection_id == exclude_connection:
                continue

            if await self.send_to_connection(connection_id, message):
                sent_count += 1

        return sent_count

    def get_connection_info(self, connection_id: str) -> Optional[ConnectionInfo]:
        """الحصول على معلومات اتصال"""
        return self._connection_info.get(connection_id)

    def get_user_connections(self, user_id: int) -> List[str]:
        """الحصول على اتصالات مستخدم"""
        return list(self._user_connections.get(user_id, set()))

    def get_group_members(self, group_name: str) -> List[str]:
        """الحصول على أعضاء مجموعة"""
        return list(self._group_connections.get(group_name, set()))

    def is_user_online(self, user_id: int) -> bool:
        """التحقق من اتصال المستخدم"""
        return user_id in self._user_connections and len(self._user_connections[user_id]) > 0

    def get_online_users(self) -> List[int]:
        """الحصول على قائمة المستخدمين المتصلين"""
        return list(self._user_connections.keys())

    def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات"""
        return {
            'total_connections': len(self._connections),
            'total_users': len(self._user_connections),
            'total_groups': len(self._group_connections),
            'connections_by_state': self._get_connections_by_state(),
        }

    def _get_connections_by_state(self) -> Dict[str, int]:
        """تجميع الاتصالات حسب الحالة"""
        states: Dict[str, int] = {}
        for info in self._connection_info.values():
            state = info.state.value
            states[state] = states.get(state, 0) + 1
        return states

    async def _sync_to_redis(self, info: ConnectionInfo) -> None:
        """مزامنة معلومات الاتصال مع Redis"""
        redis = await self._get_redis()

        key = f"ws:connection:{info.connection_id}"
        await redis.hset(key, mapping={
            'user_id': str(info.user_id or ''),
            'state': info.state.value,
            'created_at': info.created_at.isoformat(),
            'ip_address': info.ip_address or '',
        })
        await redis.expire(key, self._connection_timeout * 2)

        # تحديث قائمة اتصالات المستخدم
        if info.user_id:
            user_key = f"ws:user:{info.user_id}:connections"
            await redis.sadd(user_key, info.connection_id)
            await redis.expire(user_key, self._connection_timeout * 2)

    async def _remove_from_redis(self, connection_id: str) -> None:
        """إزالة من Redis"""
        redis = await self._get_redis()

        info = self._connection_info.get(connection_id)

        # إزالة مفتاح الاتصال
        await redis.delete(f"ws:connection:{connection_id}")

        # إزالة من قائمة المستخدم
        if info and info.user_id:
            await redis.srem(f"ws:user:{info.user_id}:connections", connection_id)

    async def start_cleanup_task(self) -> None:
        """بدء مهمة التنظيف الدورية"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def _cleanup_loop(self) -> None:
        """حلقة التنظيف الدورية"""
        while True:
            try:
                await asyncio.sleep(60)  # كل دقيقة
                await self._cleanup_stale_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    async def _cleanup_stale_connections(self) -> None:
        """تنظيف الاتصالات الخاملة"""
        now = timezone.now()
        timeout = timedelta(seconds=self._connection_timeout)

        stale_connections = []
        for connection_id, info in self._connection_info.items():
            if now - info.last_heartbeat > timeout:
                stale_connections.append(connection_id)

        for connection_id in stale_connections:
            logger.warning(f"Cleaning up stale connection: {connection_id}")
            await self.disconnect(connection_id, DisconnectReason.TIMEOUT)

    def check_rate_limit(self, connection_id: str) -> bool:
        """التحقق من حد المعدل"""
        return self._rate_limiter.is_allowed(connection_id)


# =============================================================================
# Base WebSocket Consumer
# =============================================================================

class BaseWebSocketConsumer(AsyncJsonWebsocketConsumer):
    """
    Consumer أساسي لـ WebSocket

    يوفر:
    - إدارة الاتصال
    - المصادقة
    - معالجة الرسائل
    - Heartbeat
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection_info: Optional[ConnectionInfo] = None
        self.manager = ConnectionManager()
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._message_handlers: Dict[str, Callable] = {}

    async def connect(self) -> None:
        """معالجة الاتصال الجديد"""
        # إنشاء معلومات الاتصال
        self.connection_info = ConnectionInfo(
            ip_address=self._get_client_ip(),
            user_agent=self._get_user_agent(),
        )

        # قبول الاتصال
        await self.accept()

        # بدء المصادقة
        self.connection_info.state = ConnectionState.AUTHENTICATING

        # إرسال طلب المصادقة
        await self.send_json({
            'type': 'auth.required',
            'connection_id': self.connection_info.connection_id,
        })

    async def disconnect(self, code: int) -> None:
        """معالجة قطع الاتصال"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()

        if self.connection_info:
            await self.manager.unregister(self.connection_info.connection_id)

        await self.on_disconnect(code)

    async def receive_json(self, content: Dict[str, Any], **kwargs) -> None:
        """معالجة الرسائل الواردة"""
        if not self.connection_info:
            return

        # تحديث النشاط
        self.connection_info.last_activity = timezone.now()
        self.connection_info.messages_received += 1

        message_type = content.get('type', 'unknown')

        # معالجة رسائل النظام
        if message_type == 'auth.token':
            await self._handle_auth(content)
            return

        if message_type == 'ping':
            await self._handle_ping(content)
            return

        if message_type == 'pong':
            self.connection_info.last_heartbeat = timezone.now()
            return

        # التحقق من المصادقة
        if self.connection_info.state != ConnectionState.CONNECTED:
            await self.send_json({
                'type': 'error',
                'code': 'not_authenticated',
                'message': 'يجب المصادقة أولاً',
            })
            return

        # التحقق من حد المعدل
        if not self.manager.check_rate_limit(self.connection_info.connection_id):
            await self.send_json({
                'type': 'error',
                'code': 'rate_limited',
                'message': 'تم تجاوز حد الطلبات',
            })
            return

        # معالجة الرسالة
        await self.on_message(message_type, content)

    async def _handle_auth(self, content: Dict[str, Any]) -> None:
        """معالجة المصادقة"""
        token = content.get('token')

        if not token:
            await self.send_json({
                'type': 'auth.failed',
                'reason': 'missing_token',
            })
            await self.close(code=4001)
            return

        # التحقق من التوكن
        user = await self._verify_token(token)

        if not user:
            await self.send_json({
                'type': 'auth.failed',
                'reason': 'invalid_token',
            })
            await self.close(code=4001)
            return

        # تحديث معلومات الاتصال
        self.connection_info.user_id = user.id
        self.connection_info.state = ConnectionState.CONNECTED

        # تسجيل الاتصال
        await self.manager.register(self, self.connection_info)

        # إرسال تأكيد المصادقة
        await self.send_json({
            'type': 'auth.success',
            'user_id': user.id,
            'connection_id': self.connection_info.connection_id,
        })

        # بدء Heartbeat
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        # استدعاء hook ما بعد الاتصال
        await self.on_connect()

    async def _verify_token(self, token: str) -> Optional[Any]:
        """التحقق من التوكن - يجب تخصيصه"""
        try:
            from django.contrib.auth import get_user_model
            from ninja_jwt.tokens import AccessToken

            User = get_user_model()
            access_token = AccessToken(token)
            user_id = access_token.get('user_id')

            return await User.objects.filter(id=user_id, is_active=True).afirst()
        except Exception as e:
            logger.warning(f"Token verification failed: {e}")
            return None

    async def _handle_ping(self, content: Dict[str, Any]) -> None:
        """معالجة Ping"""
        await self.send_json({
            'type': 'pong',
            'timestamp': content.get('timestamp'),
            'server_time': timezone.now().isoformat(),
        })

    async def _heartbeat_loop(self) -> None:
        """حلقة Heartbeat"""
        while True:
            try:
                await asyncio.sleep(30)

                if not self.connection_info:
                    break

                # إرسال ping
                await self.send_json({
                    'type': 'ping',
                    'timestamp': timezone.now().isoformat(),
                })

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break

    def _get_client_ip(self) -> Optional[str]:
        """الحصول على IP العميل"""
        headers = dict(self.scope.get('headers', []))
        forwarded = headers.get(b'x-forwarded-for', b'').decode()
        if forwarded:
            return forwarded.split(',')[0].strip()
        return self.scope.get('client', [None])[0]

    def _get_user_agent(self) -> Optional[str]:
        """الحصول على User Agent"""
        headers = dict(self.scope.get('headers', []))
        return headers.get(b'user-agent', b'').decode()

    # ==========================================================================
    # Hooks للتخصيص
    # ==========================================================================

    async def on_connect(self) -> None:
        """يُستدعى بعد نجاح الاتصال والمصادقة"""
        pass

    async def on_disconnect(self, code: int) -> None:
        """يُستدعى عند قطع الاتصال"""
        pass

    async def on_message(self, message_type: str, content: Dict[str, Any]) -> None:
        """يُستدعى لمعالجة الرسائل"""
        handler = self._message_handlers.get(message_type)
        if handler:
            await handler(content)
        else:
            await self.send_json({
                'type': 'error',
                'code': 'unknown_message_type',
                'message': f'نوع الرسالة غير معروف: {message_type}',
            })

    def register_handler(
        self,
        message_type: str,
        handler: Callable[[Dict[str, Any]], Awaitable[None]],
    ) -> None:
        """تسجيل معالج رسائل"""
        self._message_handlers[message_type] = handler


# =============================================================================
# Singleton instance
# =============================================================================

def get_connection_manager() -> ConnectionManager:
    """الحصول على مدير الاتصالات"""
    return ConnectionManager()
