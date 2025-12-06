"""
خدمات نظام الإشعارات
======================

يوفر:
- إرسال الإشعارات متعدد القنوات
- تجميع الإشعارات
- جدولة الإشعارات
- مزودي التوصيل (Push, SMS, Email)
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Type

import redis.asyncio as aioredis
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from .models import (
    DeliveryChannel,
    DeliveryStatus,
    Notification,
    NotificationCategory,
    NotificationDelivery,
    NotificationPriority,
    NotificationTemplate,
    UserNotificationPreferences,
)

logger = logging.getLogger(__name__)
User = get_user_model()


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class NotificationPayload:
    """بيانات الإشعار للإرسال"""

    recipient_id: int
    title: str
    body: str
    body_html: Optional[str] = None
    category: str = NotificationCategory.SYSTEM
    priority: int = NotificationPriority.NORMAL
    channels: List[str] = field(default_factory=lambda: [DeliveryChannel.WEBSOCKET])

    # بيانات إضافية
    data: Dict[str, Any] = field(default_factory=dict)
    action_url: str = ""
    image_url: str = ""
    icon: str = ""

    # ربط بكيان
    related_object: Optional[Any] = None

    # جدولة
    scheduled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # تجميع
    group_key: str = ""

    # القالب
    template_code: Optional[str] = None
    template_context: Dict[str, Any] = field(default_factory=dict)

    # تتبع
    correlation_id: str = ""


@dataclass
class DeliveryResult:
    """نتيجة التوصيل"""

    channel: str
    success: bool
    message_id: str = ""
    error_message: str = ""
    error_code: str = ""
    provider_response: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Delivery Providers
# =============================================================================

class DeliveryProvider(ABC):
    """الفئة الأساسية لمزودي التوصيل"""

    @property
    @abstractmethod
    def channel(self) -> str:
        """قناة التوصيل"""
        pass

    @abstractmethod
    async def send(
        self,
        notification: Notification,
        preferences: UserNotificationPreferences,
    ) -> DeliveryResult:
        """إرسال الإشعار"""
        pass

    async def batch_send(
        self,
        notifications: List[Notification],
        preferences_map: Dict[int, UserNotificationPreferences],
    ) -> List[DeliveryResult]:
        """إرسال دفعة من الإشعارات"""
        results = []
        for notification in notifications:
            prefs = preferences_map.get(notification.recipient_id)
            if prefs:
                result = await self.send(notification, prefs)
                results.append(result)
        return results


class WebSocketProvider(DeliveryProvider):
    """مزود WebSocket للإشعارات الفورية"""

    @property
    def channel(self) -> str:
        return DeliveryChannel.WEBSOCKET

    async def send(
        self,
        notification: Notification,
        preferences: UserNotificationPreferences,
    ) -> DeliveryResult:
        """إرسال عبر WebSocket"""
        try:
            from apps.realtime.connection import get_connection_manager

            manager = get_connection_manager()

            message = {
                'type': 'notification',
                'notification': {
                    'id': str(notification.id),
                    'title': notification.title,
                    'body': notification.body,
                    'category': notification.category,
                    'priority': notification.priority,
                    'data': notification.data,
                    'action_url': notification.action_url,
                    'image_url': notification.image_url,
                    'icon': notification.icon,
                    'created_at': notification.created_at.isoformat(),
                },
            }

            sent_count = await manager.send_to_user(
                notification.recipient_id,
                message,
            )

            if sent_count > 0:
                return DeliveryResult(
                    channel=self.channel,
                    success=True,
                    message_id=str(notification.id),
                )
            else:
                return DeliveryResult(
                    channel=self.channel,
                    success=False,
                    error_message="المستخدم غير متصل",
                    error_code="user_offline",
                )

        except Exception as e:
            logger.error(f"WebSocket delivery error: {e}")
            return DeliveryResult(
                channel=self.channel,
                success=False,
                error_message=str(e),
                error_code="delivery_error",
            )


class PushNotificationProvider(DeliveryProvider):
    """
    مزود Push Notifications

    يدعم:
    - Firebase Cloud Messaging (FCM)
    - Apple Push Notification Service (APNS)
    """

    @property
    def channel(self) -> str:
        return DeliveryChannel.PUSH

    def __init__(self):
        self._fcm_initialized = False
        self._apns_initialized = False

    async def send(
        self,
        notification: Notification,
        preferences: UserNotificationPreferences,
    ) -> DeliveryResult:
        """إرسال Push Notification"""
        try:
            push_tokens = preferences.push_tokens

            if not push_tokens:
                return DeliveryResult(
                    channel=self.channel,
                    success=False,
                    error_message="لا يوجد رموز Push",
                    error_code="no_tokens",
                )

            results = []
            for token_info in push_tokens:
                platform = token_info.get('platform', 'unknown')
                token = token_info.get('token')

                if platform in ['android', 'web']:
                    result = await self._send_fcm(notification, token)
                elif platform == 'ios':
                    result = await self._send_apns(notification, token)
                else:
                    result = await self._send_fcm(notification, token)

                results.append(result)

            # اعتبار ناجح إذا نجح واحد على الأقل
            success = any(r.success for r in results)

            return DeliveryResult(
                channel=self.channel,
                success=success,
                message_id=str(notification.id),
                provider_response={'results': [r.__dict__ for r in results]},
            )

        except Exception as e:
            logger.error(f"Push notification error: {e}")
            return DeliveryResult(
                channel=self.channel,
                success=False,
                error_message=str(e),
                error_code="push_error",
            )

    async def _send_fcm(
        self,
        notification: Notification,
        token: str,
    ) -> DeliveryResult:
        """إرسال عبر FCM"""
        # TODO: تنفيذ FCM الفعلي
        # هذا placeholder - يجب استبداله بـ firebase-admin

        fcm_config = getattr(settings, 'FCM_CONFIG', {})

        if not fcm_config.get('enabled', False):
            return DeliveryResult(
                channel=self.channel,
                success=False,
                error_message="FCM غير مفعل",
                error_code="fcm_disabled",
            )

        # Simulate FCM send
        logger.info(f"FCM: Sending to {token[:20]}... - {notification.title}")

        return DeliveryResult(
            channel=self.channel,
            success=True,
            message_id=f"fcm_{notification.id}",
        )

    async def _send_apns(
        self,
        notification: Notification,
        token: str,
    ) -> DeliveryResult:
        """إرسال عبر APNS"""
        # TODO: تنفيذ APNS الفعلي

        apns_config = getattr(settings, 'APNS_CONFIG', {})

        if not apns_config.get('enabled', False):
            return DeliveryResult(
                channel=self.channel,
                success=False,
                error_message="APNS غير مفعل",
                error_code="apns_disabled",
            )

        logger.info(f"APNS: Sending to {token[:20]}... - {notification.title}")

        return DeliveryResult(
            channel=self.channel,
            success=True,
            message_id=f"apns_{notification.id}",
        )


class SMSProvider(DeliveryProvider):
    """مزود الرسائل النصية"""

    @property
    def channel(self) -> str:
        return DeliveryChannel.SMS

    async def send(
        self,
        notification: Notification,
        preferences: UserNotificationPreferences,
    ) -> DeliveryResult:
        """إرسال SMS"""
        try:
            # الحصول على رقم الهاتف
            user = await User.objects.filter(id=notification.recipient_id).afirst()
            if not user or not user.phone_number:
                return DeliveryResult(
                    channel=self.channel,
                    success=False,
                    error_message="لا يوجد رقم هاتف",
                    error_code="no_phone",
                )

            # إرسال SMS
            result = await self._send_sms(
                phone=user.phone_number,
                message=f"{notification.title}\n{notification.body}",
            )

            return result

        except Exception as e:
            logger.error(f"SMS error: {e}")
            return DeliveryResult(
                channel=self.channel,
                success=False,
                error_message=str(e),
                error_code="sms_error",
            )

    async def _send_sms(self, phone: str, message: str) -> DeliveryResult:
        """إرسال SMS عبر المزود"""
        sms_config = getattr(settings, 'SMS_CONFIG', {})

        if not sms_config.get('enabled', False):
            return DeliveryResult(
                channel=self.channel,
                success=False,
                error_message="SMS غير مفعل",
                error_code="sms_disabled",
            )

        # TODO: تنفيذ SMS الفعلي (Twilio, Unifonic, etc.)
        logger.info(f"SMS: Sending to {phone} - {message[:50]}...")

        return DeliveryResult(
            channel=self.channel,
            success=True,
            message_id=f"sms_{phone}",
        )


class EmailProvider(DeliveryProvider):
    """مزود البريد الإلكتروني"""

    @property
    def channel(self) -> str:
        return DeliveryChannel.EMAIL

    async def send(
        self,
        notification: Notification,
        preferences: UserNotificationPreferences,
    ) -> DeliveryResult:
        """إرسال البريد الإلكتروني"""
        try:
            user = await User.objects.filter(id=notification.recipient_id).afirst()
            if not user or not user.email:
                return DeliveryResult(
                    channel=self.channel,
                    success=False,
                    error_message="لا يوجد بريد إلكتروني",
                    error_code="no_email",
                )

            result = await self._send_email(
                to=user.email,
                subject=notification.title,
                body_text=notification.body,
                body_html=notification.body_html or notification.body,
            )

            return result

        except Exception as e:
            logger.error(f"Email error: {e}")
            return DeliveryResult(
                channel=self.channel,
                success=False,
                error_message=str(e),
                error_code="email_error",
            )

    async def _send_email(
        self,
        to: str,
        subject: str,
        body_text: str,
        body_html: str,
    ) -> DeliveryResult:
        """إرسال البريد الإلكتروني"""
        from django.core.mail import send_mail

        try:
            await asyncio.to_thread(
                send_mail,
                subject=subject,
                message=body_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to],
                html_message=body_html,
                fail_silently=False,
            )

            return DeliveryResult(
                channel=self.channel,
                success=True,
                message_id=f"email_{to}",
            )

        except Exception as e:
            return DeliveryResult(
                channel=self.channel,
                success=False,
                error_message=str(e),
                error_code="email_send_error",
            )


# =============================================================================
# Notification Service
# =============================================================================

class NotificationService:
    """
    خدمة الإشعارات الرئيسية

    تدير:
    - إنشاء الإشعارات
    - توجيه للمزودين المناسبين
    - تتبع حالة التوصيل
    """

    def __init__(self):
        self._providers: Dict[str, DeliveryProvider] = {
            DeliveryChannel.WEBSOCKET: WebSocketProvider(),
            DeliveryChannel.PUSH: PushNotificationProvider(),
            DeliveryChannel.SMS: SMSProvider(),
            DeliveryChannel.EMAIL: EmailProvider(),
        }
        self._redis: Optional[aioredis.Redis] = None

    async def _get_redis(self) -> aioredis.Redis:
        """الحصول على اتصال Redis"""
        if self._redis is None:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            self._redis = await aioredis.from_url(redis_url)
        return self._redis

    async def send(self, payload: NotificationPayload) -> Notification:
        """إرسال إشعار"""
        # إنشاء الإشعار
        notification = await self._create_notification(payload)

        # التحقق من الجدولة
        if payload.scheduled_at and payload.scheduled_at > timezone.now():
            await self._schedule_notification(notification, payload.scheduled_at)
            return notification

        # الحصول على تفضيلات المستخدم
        preferences = await self._get_user_preferences(payload.recipient_id)

        # التحقق من ساعات الهدوء
        if preferences.is_quiet_hours():
            # تأخير للـ push و sms
            delayed_channels = [DeliveryChannel.PUSH, DeliveryChannel.SMS]
            immediate_channels = [c for c in payload.channels if c not in delayed_channels]

            if immediate_channels:
                await self._deliver(notification, preferences, immediate_channels)

            if any(c in payload.channels for c in delayed_channels):
                # جدولة للقنوات المؤجلة
                quiet_end = self._get_quiet_hours_end(preferences)
                await self._schedule_notification(notification, quiet_end, delayed_channels)
        else:
            # إرسال فوري
            await self._deliver(notification, preferences, payload.channels)

        return notification

    async def send_bulk(
        self,
        payloads: List[NotificationPayload],
    ) -> List[Notification]:
        """إرسال إشعارات متعددة"""
        notifications = []

        for payload in payloads:
            try:
                notification = await self.send(payload)
                notifications.append(notification)
            except Exception as e:
                logger.error(f"Bulk send error: {e}")

        return notifications

    async def send_to_users(
        self,
        user_ids: List[int],
        title: str,
        body: str,
        **kwargs,
    ) -> List[Notification]:
        """إرسال إشعار لمستخدمين متعددين"""
        payloads = [
            NotificationPayload(
                recipient_id=user_id,
                title=title,
                body=body,
                **kwargs,
            )
            for user_id in user_ids
        ]

        return await self.send_bulk(payloads)

    async def send_from_template(
        self,
        recipient_id: int,
        template_code: str,
        context: Dict[str, Any],
        channels: Optional[List[str]] = None,
        **kwargs,
    ) -> Optional[Notification]:
        """إرسال من قالب"""
        template = await NotificationTemplate.objects.filter(
            code=template_code,
            is_active=True,
        ).afirst()

        if not template:
            logger.warning(f"Template not found: {template_code}")
            return None

        # تطبيق القالب
        rendered = template.render(context)

        payload = NotificationPayload(
            recipient_id=recipient_id,
            title=rendered['title'],
            body=rendered['body'],
            body_html=rendered.get('body_html'),
            category=template.category,
            priority=template.default_priority,
            channels=channels or template.default_channels,
            template_code=template_code,
            template_context=context,
            **kwargs,
        )

        return await self.send(payload)

    async def _create_notification(
        self,
        payload: NotificationPayload,
    ) -> Notification:
        """إنشاء كائن الإشعار"""
        notification_data = {
            'recipient_id': payload.recipient_id,
            'title': payload.title,
            'body': payload.body,
            'body_html': payload.body_html or '',
            'category': payload.category,
            'priority': payload.priority,
            'data': payload.data,
            'action_url': payload.action_url,
            'image_url': payload.image_url,
            'icon': payload.icon,
            'scheduled_at': payload.scheduled_at,
            'expires_at': payload.expires_at,
            'group_key': payload.group_key,
            'correlation_id': payload.correlation_id,
        }

        # ربط بكيان
        if payload.related_object:
            from django.contrib.contenttypes.models import ContentType

            content_type = ContentType.objects.get_for_model(payload.related_object)
            notification_data['content_type'] = content_type
            notification_data['object_id'] = str(payload.related_object.pk)

        # ربط بقالب
        if payload.template_code:
            template = await NotificationTemplate.objects.filter(
                code=payload.template_code
            ).afirst()
            if template:
                notification_data['template'] = template

        notification = await Notification.objects.acreate(**notification_data)

        # إنشاء سجلات التوصيل
        for channel in payload.channels:
            await NotificationDelivery.objects.acreate(
                notification=notification,
                channel=channel,
                status=DeliveryStatus.PENDING,
            )

        return notification

    async def _get_user_preferences(
        self,
        user_id: int,
    ) -> UserNotificationPreferences:
        """الحصول على تفضيلات المستخدم"""
        preferences, _ = await UserNotificationPreferences.objects.aget_or_create(
            user_id=user_id,
        )
        return preferences

    async def _deliver(
        self,
        notification: Notification,
        preferences: UserNotificationPreferences,
        channels: List[str],
    ) -> Dict[str, DeliveryResult]:
        """توصيل الإشعار للقنوات المحددة"""
        results = {}

        for channel in channels:
            # التحقق من تفعيل القناة
            if not preferences.is_channel_enabled(channel, notification.category):
                continue

            provider = self._providers.get(channel)
            if not provider:
                continue

            # تحديث حالة التوصيل
            delivery = await NotificationDelivery.objects.filter(
                notification=notification,
                channel=channel,
            ).afirst()

            if delivery:
                delivery.status = DeliveryStatus.QUEUED
                delivery.queued_at = timezone.now()
                await delivery.asave()

            # إرسال
            result = await provider.send(notification, preferences)
            results[channel] = result

            # تحديث حالة التوصيل
            if delivery:
                delivery.attempts += 1
                delivery.last_attempt_at = timezone.now()

                if result.success:
                    delivery.status = DeliveryStatus.SENT
                    delivery.sent_at = timezone.now()
                    delivery.provider_message_id = result.message_id
                else:
                    if delivery.attempts >= delivery.max_attempts:
                        delivery.status = DeliveryStatus.FAILED
                        delivery.failed_at = timezone.now()
                    else:
                        delivery.status = DeliveryStatus.PENDING
                        delivery.next_attempt_at = timezone.now() + timedelta(
                            minutes=2 ** delivery.attempts
                        )

                    delivery.error_message = result.error_message
                    delivery.error_code = result.error_code

                delivery.provider_response = result.provider_response
                await delivery.asave()

        return results

    async def _schedule_notification(
        self,
        notification: Notification,
        scheduled_at: datetime,
        channels: Optional[List[str]] = None,
    ) -> None:
        """جدولة إشعار للإرسال لاحقاً"""
        redis = await self._get_redis()

        job_data = {
            'notification_id': str(notification.id),
            'channels': channels,
            'scheduled_at': scheduled_at.isoformat(),
        }

        # إضافة للـ sorted set
        await redis.zadd(
            'notifications:scheduled',
            {json.dumps(job_data): scheduled_at.timestamp()},
        )

    def _get_quiet_hours_end(
        self,
        preferences: UserNotificationPreferences,
    ) -> datetime:
        """حساب نهاية ساعات الهدوء"""
        now = timezone.localtime()
        end_time = preferences.quiet_hours_end

        if end_time:
            end_datetime = now.replace(
                hour=end_time.hour,
                minute=end_time.minute,
                second=0,
                microsecond=0,
            )

            if end_datetime <= now:
                end_datetime += timedelta(days=1)

            return end_datetime

        return now + timedelta(hours=8)  # افتراضي

    # =========================================================================
    # Query Methods
    # =========================================================================

    async def get_user_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Notification]:
        """الحصول على إشعارات المستخدم"""
        queryset = Notification.objects.filter(
            recipient_id=user_id,
            is_archived=False,
        )

        if unread_only:
            queryset = queryset.filter(is_read=False)

        if category:
            queryset = queryset.filter(category=category)

        return [
            n async for n in queryset
            .order_by('-created_at')[offset:offset + limit]
        ]

    async def get_unread_count(
        self,
        user_id: int,
        category: Optional[str] = None,
    ) -> int:
        """الحصول على عدد غير المقروءة"""
        queryset = Notification.objects.filter(
            recipient_id=user_id,
            is_read=False,
            is_archived=False,
        )

        if category:
            queryset = queryset.filter(category=category)

        return await queryset.acount()

    async def mark_as_read(
        self,
        notification_ids: List[str],
        user_id: int,
    ) -> int:
        """تحديد إشعارات كمقروءة"""
        count = await Notification.objects.filter(
            id__in=notification_ids,
            recipient_id=user_id,
            is_read=False,
        ).aupdate(
            is_read=True,
            read_at=timezone.now(),
        )

        return count

    async def mark_all_as_read(
        self,
        user_id: int,
        category: Optional[str] = None,
    ) -> int:
        """تحديد الكل كمقروء"""
        queryset = Notification.objects.filter(
            recipient_id=user_id,
            is_read=False,
        )

        if category:
            queryset = queryset.filter(category=category)

        count = await queryset.aupdate(
            is_read=True,
            read_at=timezone.now(),
        )

        return count

    async def archive(
        self,
        notification_ids: List[str],
        user_id: int,
    ) -> int:
        """أرشفة إشعارات"""
        count = await Notification.objects.filter(
            id__in=notification_ids,
            recipient_id=user_id,
        ).aupdate(
            is_archived=True,
            archived_at=timezone.now(),
        )

        return count

    async def delete_old_notifications(
        self,
        days: int = 30,
    ) -> int:
        """حذف الإشعارات القديمة"""
        cutoff = timezone.now() - timedelta(days=days)

        count, _ = await Notification.objects.filter(
            created_at__lt=cutoff,
            is_archived=True,
        ).adelete()

        return count


# =============================================================================
# Notification Batcher
# =============================================================================

class NotificationBatcher:
    """
    تجميع الإشعارات المتشابهة

    يقوم بتجميع الإشعارات المتشابهة خلال فترة زمنية
    لتقليل عدد الإشعارات المرسلة
    """

    def __init__(self):
        self._redis: Optional[aioredis.Redis] = None
        self._batch_window = 300  # 5 دقائق

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            self._redis = await aioredis.from_url(redis_url)
        return self._redis

    async def add_to_batch(
        self,
        user_id: int,
        group_key: str,
        notification_data: Dict[str, Any],
    ) -> bool:
        """إضافة للدفعة"""
        redis = await self._get_redis()

        batch_key = f"notification:batch:{user_id}:{group_key}"

        # إضافة للقائمة
        await redis.rpush(batch_key, json.dumps(notification_data))
        await redis.expire(batch_key, self._batch_window * 2)

        # التحقق من وجود مؤقت
        timer_key = f"notification:batch:timer:{user_id}:{group_key}"
        exists = await redis.exists(timer_key)

        if not exists:
            # إنشاء مؤقت
            await redis.set(timer_key, '1', ex=self._batch_window)
            return True  # يجب جدولة إرسال

        return False  # المؤقت موجود بالفعل

    async def get_batch(
        self,
        user_id: int,
        group_key: str,
    ) -> List[Dict[str, Any]]:
        """الحصول على الدفعة"""
        redis = await self._get_redis()

        batch_key = f"notification:batch:{user_id}:{group_key}"
        items = await redis.lrange(batch_key, 0, -1)

        # حذف الدفعة
        await redis.delete(batch_key)

        return [json.loads(item) for item in items]

    def summarize_batch(
        self,
        items: List[Dict[str, Any]],
    ) -> NotificationPayload:
        """تلخيص الدفعة في إشعار واحد"""
        if len(items) == 1:
            # إشعار واحد فقط
            item = items[0]
            return NotificationPayload(**item)

        # تجميع
        first = items[0]
        count = len(items)

        return NotificationPayload(
            recipient_id=first['recipient_id'],
            title=f"لديك {count} إشعارات جديدة",
            body=f"لديك {count} {first.get('category', 'إشعارات')} جديدة",
            category=first.get('category', NotificationCategory.SYSTEM),
            data={
                'batch': True,
                'count': count,
                'items': items[:5],  # أول 5 فقط
            },
            group_key=first.get('group_key', ''),
        )


# =============================================================================
# Global Service Instance
# =============================================================================

_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """الحصول على خدمة الإشعارات"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service


async def send_notification(
    recipient_id: int,
    title: str,
    body: str,
    **kwargs,
) -> Notification:
    """دالة مساعدة لإرسال إشعار"""
    service = get_notification_service()
    payload = NotificationPayload(
        recipient_id=recipient_id,
        title=title,
        body=body,
        **kwargs,
    )
    return await service.send(payload)
