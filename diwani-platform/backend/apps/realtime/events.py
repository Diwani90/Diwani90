"""
نظام الأحداث المتقدم - Event Sourcing & CQRS
=============================================

يوفر هذا النظام:
- Event Store للاحتفاظ بسجل كامل للأحداث
- Event Bus للنشر والاشتراك
- Event Replay لإعادة بناء الحالة
- Event Versioning للتوافقية
- Saga Pattern للمعاملات الموزعة
"""

import asyncio
import hashlib
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Set,
    Type,
    TypeVar,
    Union,
)

import redis.asyncio as aioredis
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


# =============================================================================
# Event Types & Categories
# =============================================================================

class EventCategory(str, Enum):
    """تصنيفات الأحداث الرئيسية"""

    # أحداث النظام
    SYSTEM = "system"

    # أحداث المستخدمين
    USER = "user"
    AUTH = "auth"

    # أحداث الطلبات
    ORDER = "order"
    PAYMENT = "payment"

    # أحداث التوصيل
    DELIVERY = "delivery"
    TRACKING = "tracking"

    # أحداث المحادثات
    CHAT = "chat"
    MESSAGE = "message"

    # أحداث الإشعارات
    NOTIFICATION = "notification"

    # أحداث المنتجات
    PRODUCT = "product"
    INVENTORY = "inventory"

    # أحداث المتاجر
    STORE = "store"
    VENDOR = "vendor"


class EventPriority(int, Enum):
    """أولويات الأحداث"""

    CRITICAL = 0  # أحداث حرجة - معالجة فورية
    HIGH = 1  # أولوية عالية
    NORMAL = 2  # أولوية عادية
    LOW = 3  # أولوية منخفضة
    BACKGROUND = 4  # معالجة في الخلفية


class DeliveryGuarantee(str, Enum):
    """ضمانات التسليم"""

    AT_MOST_ONCE = "at_most_once"  # قد لا يصل
    AT_LEAST_ONCE = "at_least_once"  # قد يصل أكثر من مرة
    EXACTLY_ONCE = "exactly_once"  # يصل مرة واحدة بالضبط


# =============================================================================
# Event Base Classes
# =============================================================================

@dataclass
class EventMetadata:
    """البيانات الوصفية للحدث"""

    # معرفات
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None  # لربط الأحداث المتعلقة
    causation_id: Optional[str] = None  # الحدث المسبب

    # التوقيت
    timestamp: datetime = field(default_factory=timezone.now)
    expires_at: Optional[datetime] = None

    # المصدر
    source_service: str = "diwani-platform"
    source_instance: Optional[str] = None

    # المستخدم
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None

    # التتبع
    trace_id: Optional[str] = None
    span_id: Optional[str] = None

    # الإصدار
    schema_version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى قاموس"""
        data = asdict(self)
        # تحويل datetime إلى ISO format
        if self.timestamp:
            data['timestamp'] = self.timestamp.isoformat()
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EventMetadata':
        """إنشاء من قاموس"""
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if 'expires_at' in data and data['expires_at'] and isinstance(data['expires_at'], str):
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        return cls(**data)


@dataclass
class BaseEvent(ABC):
    """الفئة الأساسية لجميع الأحداث"""

    metadata: EventMetadata = field(default_factory=EventMetadata)

    @property
    @abstractmethod
    def event_type(self) -> str:
        """نوع الحدث الفريد"""
        pass

    @property
    def category(self) -> EventCategory:
        """تصنيف الحدث"""
        return EventCategory.SYSTEM

    @property
    def priority(self) -> EventPriority:
        """أولوية الحدث"""
        return EventPriority.NORMAL

    @property
    def delivery_guarantee(self) -> DeliveryGuarantee:
        """ضمان التسليم"""
        return DeliveryGuarantee.AT_LEAST_ONCE

    def get_aggregate_id(self) -> Optional[str]:
        """معرف الكيان المرتبط"""
        return None

    def get_routing_key(self) -> str:
        """مفتاح التوجيه للنشر"""
        return f"{self.category.value}.{self.event_type}"

    def to_dict(self) -> Dict[str, Any]:
        """تحويل الحدث إلى قاموس"""
        return {
            'event_type': self.event_type,
            'category': self.category.value,
            'priority': self.priority.value,
            'metadata': self.metadata.to_dict(),
            'payload': self._get_payload(),
        }

    def _get_payload(self) -> Dict[str, Any]:
        """الحصول على بيانات الحدث"""
        data = asdict(self)
        del data['metadata']
        return data

    def to_json(self) -> str:
        """تحويل إلى JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseEvent':
        """إنشاء من قاموس"""
        metadata = EventMetadata.from_dict(data.get('metadata', {}))
        payload = data.get('payload', {})
        return cls(metadata=metadata, **payload)

    def get_hash(self) -> str:
        """حساب hash للحدث (للتكرار)"""
        content = f"{self.event_type}:{self.get_aggregate_id()}:{self.metadata.timestamp.isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# =============================================================================
# Domain Events - أحداث النطاق
# =============================================================================

@dataclass
class OrderCreatedEvent(BaseEvent):
    """حدث إنشاء طلب جديد"""

    order_id: int = 0
    customer_id: int = 0
    store_id: int = 0
    total_amount: float = 0.0
    items_count: int = 0

    @property
    def event_type(self) -> str:
        return "order.created"

    @property
    def category(self) -> EventCategory:
        return EventCategory.ORDER

    @property
    def priority(self) -> EventPriority:
        return EventPriority.HIGH

    def get_aggregate_id(self) -> str:
        return f"order:{self.order_id}"


@dataclass
class OrderStatusChangedEvent(BaseEvent):
    """حدث تغيير حالة الطلب"""

    order_id: int = 0
    old_status: str = ""
    new_status: str = ""
    changed_by: Optional[int] = None
    reason: Optional[str] = None

    @property
    def event_type(self) -> str:
        return "order.status_changed"

    @property
    def category(self) -> EventCategory:
        return EventCategory.ORDER

    def get_aggregate_id(self) -> str:
        return f"order:{self.order_id}"


@dataclass
class DeliveryLocationUpdatedEvent(BaseEvent):
    """حدث تحديث موقع التوصيل"""

    delivery_id: int = 0
    driver_id: int = 0
    latitude: float = 0.0
    longitude: float = 0.0
    speed: float = 0.0  # km/h
    heading: float = 0.0  # degrees
    accuracy: float = 0.0  # meters
    eta_minutes: Optional[int] = None

    @property
    def event_type(self) -> str:
        return "delivery.location_updated"

    @property
    def category(self) -> EventCategory:
        return EventCategory.TRACKING

    @property
    def priority(self) -> EventPriority:
        return EventPriority.HIGH

    def get_aggregate_id(self) -> str:
        return f"delivery:{self.delivery_id}"


@dataclass
class MessageSentEvent(BaseEvent):
    """حدث إرسال رسالة"""

    message_id: str = ""
    conversation_id: str = ""
    sender_id: int = 0
    recipient_ids: List[int] = field(default_factory=list)
    message_type: str = "text"
    content_preview: str = ""
    has_attachments: bool = False

    @property
    def event_type(self) -> str:
        return "message.sent"

    @property
    def category(self) -> EventCategory:
        return EventCategory.MESSAGE

    @property
    def priority(self) -> EventPriority:
        return EventPriority.HIGH

    def get_aggregate_id(self) -> str:
        return f"conversation:{self.conversation_id}"


@dataclass
class NotificationCreatedEvent(BaseEvent):
    """حدث إنشاء إشعار"""

    notification_id: str = ""
    recipient_id: int = 0
    notification_type: str = ""
    title: str = ""
    body: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    channels: List[str] = field(default_factory=list)

    @property
    def event_type(self) -> str:
        return "notification.created"

    @property
    def category(self) -> EventCategory:
        return EventCategory.NOTIFICATION

    def get_aggregate_id(self) -> str:
        return f"notification:{self.notification_id}"


@dataclass
class UserPresenceChangedEvent(BaseEvent):
    """حدث تغيير حالة تواجد المستخدم"""

    user_id: int = 0
    status: str = "online"  # online, away, busy, offline
    last_seen: Optional[datetime] = None
    device_info: Optional[Dict[str, Any]] = None

    @property
    def event_type(self) -> str:
        return "user.presence_changed"

    @property
    def category(self) -> EventCategory:
        return EventCategory.USER

    def get_aggregate_id(self) -> str:
        return f"user:{self.user_id}"


# =============================================================================
# Event Registry - سجل الأحداث
# =============================================================================

class EventRegistry:
    """سجل مركزي لجميع أنواع الأحداث"""

    _events: Dict[str, Type[BaseEvent]] = {}
    _handlers: Dict[str, List[Callable]] = {}

    @classmethod
    def register(cls, event_class: Type[BaseEvent]) -> Type[BaseEvent]:
        """تسجيل نوع حدث جديد"""
        # إنشاء instance مؤقت للحصول على event_type
        temp_instance = event_class.__new__(event_class)
        temp_instance.metadata = EventMetadata()
        event_type = temp_instance.event_type
        cls._events[event_type] = event_class
        logger.debug(f"Registered event type: {event_type}")
        return event_class

    @classmethod
    def get_event_class(cls, event_type: str) -> Optional[Type[BaseEvent]]:
        """الحصول على فئة الحدث من النوع"""
        return cls._events.get(event_type)

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> Optional[BaseEvent]:
        """تحويل البيانات إلى حدث"""
        event_type = data.get('event_type')
        event_class = cls.get_event_class(event_type)
        if event_class:
            return event_class.from_dict(data)
        return None

    @classmethod
    def list_events(cls) -> List[str]:
        """قائمة جميع الأحداث المسجلة"""
        return list(cls._events.keys())


# تسجيل الأحداث الافتراضية
for event_class in [
    OrderCreatedEvent,
    OrderStatusChangedEvent,
    DeliveryLocationUpdatedEvent,
    MessageSentEvent,
    NotificationCreatedEvent,
    UserPresenceChangedEvent,
]:
    EventRegistry.register(event_class)


# =============================================================================
# Event Store - مخزن الأحداث
# =============================================================================

class EventStore(ABC):
    """واجهة مخزن الأحداث"""

    @abstractmethod
    async def append(self, event: BaseEvent) -> str:
        """إضافة حدث للمخزن"""
        pass

    @abstractmethod
    async def get_events(
        self,
        aggregate_id: str,
        from_version: int = 0,
        to_version: Optional[int] = None,
    ) -> List[BaseEvent]:
        """استرجاع أحداث كيان معين"""
        pass

    @abstractmethod
    async def get_events_by_type(
        self,
        event_type: str,
        from_timestamp: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[BaseEvent]:
        """استرجاع أحداث من نوع معين"""
        pass


class RedisEventStore(EventStore):
    """مخزن أحداث باستخدام Redis Streams"""

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        self._stream_prefix = "events:"
        self._max_stream_length = 10000

    async def _get_redis(self) -> aioredis.Redis:
        """الحصول على اتصال Redis"""
        if self._redis is None:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            self._redis = await aioredis.from_url(redis_url)
        return self._redis

    async def append(self, event: BaseEvent) -> str:
        """إضافة حدث للمخزن"""
        redis = await self._get_redis()

        stream_name = f"{self._stream_prefix}{event.category.value}"
        aggregate_stream = f"{self._stream_prefix}aggregate:{event.get_aggregate_id()}"

        event_data = {
            'event_type': event.event_type,
            'event_id': event.metadata.event_id,
            'aggregate_id': event.get_aggregate_id() or '',
            'data': event.to_json(),
            'timestamp': event.metadata.timestamp.isoformat(),
        }

        # إضافة للـ stream الرئيسي
        message_id = await redis.xadd(
            stream_name,
            event_data,
            maxlen=self._max_stream_length,
        )

        # إضافة للـ stream الخاص بالكيان
        if event.get_aggregate_id():
            await redis.xadd(
                aggregate_stream,
                event_data,
                maxlen=1000,
            )

        logger.debug(f"Event stored: {event.event_type} -> {message_id}")
        return message_id

    async def get_events(
        self,
        aggregate_id: str,
        from_version: int = 0,
        to_version: Optional[int] = None,
    ) -> List[BaseEvent]:
        """استرجاع أحداث كيان معين"""
        redis = await self._get_redis()

        stream_name = f"{self._stream_prefix}aggregate:{aggregate_id}"

        messages = await redis.xrange(
            stream_name,
            min='-',
            max='+',
            count=to_version if to_version else None,
        )

        events = []
        for msg_id, data in messages[from_version:]:
            event_data = json.loads(data[b'data'].decode())
            event = EventRegistry.deserialize(event_data)
            if event:
                events.append(event)

        return events

    async def get_events_by_type(
        self,
        event_type: str,
        from_timestamp: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[BaseEvent]:
        """استرجاع أحداث من نوع معين"""
        redis = await self._get_redis()

        # البحث في جميع الـ streams
        events = []
        for category in EventCategory:
            stream_name = f"{self._stream_prefix}{category.value}"

            try:
                messages = await redis.xrange(
                    stream_name,
                    min='-',
                    max='+',
                    count=limit * 2,  # نأخذ أكثر للفلترة
                )

                for msg_id, data in messages:
                    if data.get(b'event_type', b'').decode() == event_type:
                        event_data = json.loads(data[b'data'].decode())
                        event = EventRegistry.deserialize(event_data)
                        if event:
                            if from_timestamp and event.metadata.timestamp < from_timestamp:
                                continue
                            events.append(event)

                            if len(events) >= limit:
                                break
            except Exception:
                continue

        return events[:limit]


# =============================================================================
# Event Bus - ناقل الأحداث
# =============================================================================

EventHandler = Callable[[BaseEvent], Awaitable[None]]


class EventBus:
    """ناقل الأحداث للنشر والاشتراك"""

    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._wildcard_handlers: List[EventHandler] = []
        self._redis: Optional[aioredis.Redis] = None
        self._pubsub: Optional[aioredis.client.PubSub] = None
        self._channel_prefix = "diwani:events:"
        self._running = False
        self._event_store = RedisEventStore()

    async def _get_redis(self) -> aioredis.Redis:
        """الحصول على اتصال Redis"""
        if self._redis is None:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            self._redis = await aioredis.from_url(redis_url)
        return self._redis

    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        """الاشتراك في نوع حدث معين"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(f"Handler subscribed to: {event_type}")

    def subscribe_all(self, handler: EventHandler) -> None:
        """الاشتراك في جميع الأحداث"""
        self._wildcard_handlers.append(handler)

    def unsubscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        """إلغاء الاشتراك"""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)

    async def publish(
        self,
        event: BaseEvent,
        store: bool = True,
    ) -> None:
        """نشر حدث"""
        # حفظ في Event Store
        if store:
            await self._event_store.append(event)

        # معالجة محلية
        await self._dispatch_locally(event)

        # نشر عبر Redis Pub/Sub
        await self._publish_to_redis(event)

    async def _dispatch_locally(self, event: BaseEvent) -> None:
        """توزيع الحدث محلياً"""
        handlers = self._handlers.get(event.event_type, [])
        handlers += self._wildcard_handlers

        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")

    async def _publish_to_redis(self, event: BaseEvent) -> None:
        """نشر الحدث عبر Redis"""
        redis = await self._get_redis()

        channel = f"{self._channel_prefix}{event.get_routing_key()}"
        await redis.publish(channel, event.to_json())

    async def start_listening(self) -> None:
        """بدء الاستماع للأحداث من Redis"""
        if self._running:
            return

        self._running = True
        redis = await self._get_redis()
        self._pubsub = redis.pubsub()

        # الاشتراك في جميع القنوات
        await self._pubsub.psubscribe(f"{self._channel_prefix}*")

        # حلقة الاستماع
        asyncio.create_task(self._listen_loop())

    async def _listen_loop(self) -> None:
        """حلقة الاستماع للأحداث"""
        while self._running:
            try:
                message = await self._pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )
                if message and message['type'] == 'pmessage':
                    data = json.loads(message['data'])
                    event = EventRegistry.deserialize(data)
                    if event:
                        await self._dispatch_locally(event)
            except Exception as e:
                logger.error(f"Error in event listener: {e}")
                await asyncio.sleep(1)

    async def stop_listening(self) -> None:
        """إيقاف الاستماع"""
        self._running = False
        if self._pubsub:
            await self._pubsub.unsubscribe()
            await self._pubsub.close()


# =============================================================================
# Saga Pattern - نمط الساغا للمعاملات الموزعة
# =============================================================================

@dataclass
class SagaStep:
    """خطوة في الساغا"""

    name: str
    action: Callable[..., Awaitable[Any]]
    compensation: Callable[..., Awaitable[None]]
    timeout_seconds: int = 30


class SagaState(str, Enum):
    """حالات الساغا"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPENSATING = "compensating"
    FAILED = "failed"


@dataclass
class SagaContext:
    """سياق الساغا"""

    saga_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: SagaState = SagaState.PENDING
    current_step: int = 0
    data: Dict[str, Any] = field(default_factory=dict)
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class Saga:
    """
    تنفيذ نمط الساغا للمعاملات الموزعة

    يضمن تنفيذ سلسلة من الخطوات مع التراجع التلقائي عند الفشل
    """

    def __init__(self, name: str):
        self.name = name
        self.steps: List[SagaStep] = []
        self._event_bus: Optional[EventBus] = None

    def add_step(
        self,
        name: str,
        action: Callable[..., Awaitable[Any]],
        compensation: Callable[..., Awaitable[None]],
        timeout_seconds: int = 30,
    ) -> 'Saga':
        """إضافة خطوة للساغا"""
        self.steps.append(SagaStep(
            name=name,
            action=action,
            compensation=compensation,
            timeout_seconds=timeout_seconds,
        ))
        return self

    async def execute(
        self,
        initial_data: Dict[str, Any],
        event_bus: Optional[EventBus] = None,
    ) -> SagaContext:
        """تنفيذ الساغا"""
        self._event_bus = event_bus
        context = SagaContext(data=initial_data)
        context.state = SagaState.RUNNING
        context.started_at = timezone.now()

        logger.info(f"Starting saga: {self.name} ({context.saga_id})")

        try:
            # تنفيذ الخطوات
            for i, step in enumerate(self.steps):
                context.current_step = i
                logger.debug(f"Executing step {i}: {step.name}")

                try:
                    result = await asyncio.wait_for(
                        step.action(context),
                        timeout=step.timeout_seconds,
                    )
                    context.results[step.name] = result

                except asyncio.TimeoutError:
                    context.errors.append(f"Step {step.name} timed out")
                    raise

                except Exception as e:
                    context.errors.append(f"Step {step.name} failed: {str(e)}")
                    raise

            # اكتمال بنجاح
            context.state = SagaState.COMPLETED
            context.completed_at = timezone.now()
            logger.info(f"Saga completed: {self.name} ({context.saga_id})")

        except Exception as e:
            # بدء التعويض
            logger.warning(f"Saga failed, starting compensation: {self.name}")
            context.state = SagaState.COMPENSATING

            await self._compensate(context)

            context.state = SagaState.FAILED
            context.completed_at = timezone.now()

        return context

    async def _compensate(self, context: SagaContext) -> None:
        """تنفيذ التعويضات"""
        # التراجع بترتيب عكسي
        for i in range(context.current_step, -1, -1):
            step = self.steps[i]
            logger.debug(f"Compensating step {i}: {step.name}")

            try:
                await asyncio.wait_for(
                    step.compensation(context),
                    timeout=step.timeout_seconds,
                )
            except Exception as e:
                logger.error(f"Compensation failed for {step.name}: {e}")
                context.errors.append(f"Compensation {step.name} failed: {str(e)}")


# =============================================================================
# Event Sourced Aggregate - الكيان المصدر بالأحداث
# =============================================================================

T = TypeVar('T', bound='EventSourcedAggregate')


class EventSourcedAggregate(ABC):
    """
    الفئة الأساسية للكيانات المصدرة بالأحداث

    تستخدم Event Sourcing لتتبع جميع التغييرات
    """

    def __init__(self, aggregate_id: str):
        self._id = aggregate_id
        self._version = 0
        self._pending_events: List[BaseEvent] = []

    @property
    def id(self) -> str:
        return self._id

    @property
    def version(self) -> int:
        return self._version

    def apply_event(self, event: BaseEvent, is_new: bool = True) -> None:
        """تطبيق حدث على الكيان"""
        # استدعاء المعالج المناسب
        handler_name = f"_apply_{event.event_type.replace('.', '_')}"
        handler = getattr(self, handler_name, None)

        if handler:
            handler(event)

        self._version += 1

        if is_new:
            self._pending_events.append(event)

    def get_pending_events(self) -> List[BaseEvent]:
        """الحصول على الأحداث المعلقة"""
        return self._pending_events.copy()

    def clear_pending_events(self) -> None:
        """مسح الأحداث المعلقة"""
        self._pending_events.clear()

    @classmethod
    async def load(
        cls: Type[T],
        aggregate_id: str,
        event_store: EventStore,
    ) -> T:
        """تحميل الكيان من الأحداث"""
        aggregate = cls(aggregate_id)
        events = await event_store.get_events(aggregate_id)

        for event in events:
            aggregate.apply_event(event, is_new=False)

        return aggregate

    async def save(self, event_store: EventStore) -> None:
        """حفظ الأحداث المعلقة"""
        for event in self._pending_events:
            await event_store.append(event)
        self.clear_pending_events()


# =============================================================================
# Global Event Bus Instance
# =============================================================================

# Instance واحد للتطبيق
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """الحصول على Event Bus العام"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


async def publish_event(event: BaseEvent, store: bool = True) -> None:
    """نشر حدث (دالة مساعدة)"""
    bus = get_event_bus()
    await bus.publish(event, store=store)
