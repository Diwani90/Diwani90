"""
WebSocket Consumers لنظام Real-time
=====================================

يوفر:
- MainConsumer للاتصال العام
- NotificationConsumer للإشعارات
- ChatConsumer للمحادثات
- TrackingConsumer للتتبع
"""

import json
import logging
from typing import Any, Dict, Optional

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from django.utils import timezone

from .connection import (
    BaseWebSocketConsumer,
    ConnectionInfo,
    ConnectionState,
    get_connection_manager,
)
from .presence import DeviceInfo, PresenceStatus, get_presence_manager

logger = logging.getLogger(__name__)
User = get_user_model()


# =============================================================================
# Main Consumer
# =============================================================================

class MainConsumer(BaseWebSocketConsumer):
    """
    Consumer الرئيسي للاتصالات العامة

    يدير:
    - المصادقة
    - الحضور
    - الاشتراكات
    """

    async def on_connect(self):
        """بعد نجاح الاتصال"""
        if not self.connection_info or not self.connection_info.user_id:
            return

        # تحديث الحضور
        presence = get_presence_manager()
        device_info = DeviceInfo(
            device_id=self.connection_info.connection_id,
            device_type=self._detect_device_type(),
            os=self._get_os_from_user_agent(),
        )

        await presence.set_online(
            self.connection_info.user_id,
            device_info=device_info,
        )

        # الانضمام للمجموعة الشخصية
        await self.channel_layer.group_add(
            f"user_{self.connection_info.user_id}",
            self.channel_name,
        )

        logger.info(f"User {self.connection_info.user_id} connected")

    async def on_disconnect(self, code: int):
        """عند قطع الاتصال"""
        if self.connection_info and self.connection_info.user_id:
            # تحديث الحضور
            presence = get_presence_manager()
            await presence.set_offline(
                self.connection_info.user_id,
                device_id=self.connection_info.connection_id,
            )

            # مغادرة المجموعة
            await self.channel_layer.group_discard(
                f"user_{self.connection_info.user_id}",
                self.channel_name,
            )

            logger.info(f"User {self.connection_info.user_id} disconnected")

    async def on_message(self, message_type: str, content: Dict[str, Any]):
        """معالجة الرسائل"""
        handlers = {
            'subscribe': self._handle_subscribe,
            'unsubscribe': self._handle_unsubscribe,
            'presence.update': self._handle_presence_update,
            'presence.get': self._handle_presence_get,
        }

        handler = handlers.get(message_type)
        if handler:
            await handler(content)
        else:
            await self.send_json({
                'type': 'error',
                'code': 'unknown_message',
                'message': f'نوع الرسالة غير معروف: {message_type}',
            })

    async def _handle_subscribe(self, content: Dict[str, Any]):
        """الاشتراك في قناة"""
        channel = content.get('channel')
        if not channel:
            return

        # التحقق من الصلاحيات
        if not await self._can_subscribe(channel):
            await self.send_json({
                'type': 'error',
                'code': 'subscribe_denied',
                'message': 'غير مصرح لك بالاشتراك في هذه القناة',
            })
            return

        await self.channel_layer.group_add(channel, self.channel_name)
        self.connection_info.groups.add(channel)

        await self.send_json({
            'type': 'subscribed',
            'channel': channel,
        })

    async def _handle_unsubscribe(self, content: Dict[str, Any]):
        """إلغاء الاشتراك"""
        channel = content.get('channel')
        if not channel:
            return

        await self.channel_layer.group_discard(channel, self.channel_name)
        self.connection_info.groups.discard(channel)

        await self.send_json({
            'type': 'unsubscribed',
            'channel': channel,
        })

    async def _handle_presence_update(self, content: Dict[str, Any]):
        """تحديث الحضور"""
        presence = get_presence_manager()

        status = content.get('status')
        if status:
            await presence.set_online(
                self.connection_info.user_id,
                status=PresenceStatus(status),
            )

        custom_status = content.get('custom_status')
        if custom_status is not None:
            await presence.set_custom_status(
                self.connection_info.user_id,
                custom_status,
            )

    async def _handle_presence_get(self, content: Dict[str, Any]):
        """الحصول على حضور مستخدمين"""
        user_ids = content.get('user_ids', [])
        if not user_ids:
            return

        presence = get_presence_manager()
        presences = await presence.get_multiple_presences(user_ids)

        await self.send_json({
            'type': 'presence.result',
            'presences': {
                uid: p.to_public_dict()
                for uid, p in presences.items()
            },
        })

    async def _can_subscribe(self, channel: str) -> bool:
        """التحقق من صلاحية الاشتراك"""
        if not self.connection_info or not self.connection_info.user_id:
            return False

        # القنوات العامة
        if channel.startswith('public_'):
            return True

        # قناة المستخدم الشخصية
        if channel == f"user_{self.connection_info.user_id}":
            return True

        # قنوات الطلبات - التحقق من الملكية
        if channel.startswith('order_'):
            order_id = channel.replace('order_', '')
            return await self._check_order_access(order_id)

        # قنوات التتبع
        if channel.startswith('tracking_'):
            delivery_id = channel.replace('tracking_', '')
            return await self._check_tracking_access(delivery_id)

        return False

    @database_sync_to_async
    def _check_order_access(self, order_id: str) -> bool:
        """
        التحقق من صلاحية الوصول للطلب

        المستخدمون المسموح لهم:
        - صاحب الطلب (العميل)
        - صاحب المتجر (التاجر)
        - السائق المخصص للتوصيل
        - مدير النظام
        """
        try:
            from apps.orders.models import Order
            from apps.stores.models import StoreStaff

            order = Order.objects.select_related(
                'customer', 'vendor', 'delivery'
            ).get(id=order_id)

            user_id = self.connection_info.user_id

            # العميل صاحب الطلب
            if order.customer_id == user_id:
                return True

            # صاحب المتجر
            if hasattr(order.vendor, 'owner_id') and order.vendor.owner_id == user_id:
                return True

            # موظفي المتجر
            if StoreStaff.objects.filter(
                store=order.vendor,
                user_id=user_id,
                is_active=True
            ).exists():
                return True

            # السائق المخصص
            if order.delivery and order.delivery.driver_id == user_id:
                return True

            # مدير النظام
            if hasattr(self.connection_info, 'is_staff') and self.connection_info.is_staff:
                return True

            return False

        except Exception as e:
            logger.warning(f"Order access check failed for {order_id}: {e}")
            return False

    @database_sync_to_async
    def _check_tracking_access(self, delivery_id: str) -> bool:
        """
        التحقق من صلاحية تتبع التوصيل

        المستخدمون المسموح لهم:
        - صاحب الطلب
        - السائق
        - التاجر
        """
        try:
            from apps.tracking.models import Delivery

            delivery = Delivery.objects.select_related(
                'order', 'order__customer', 'order__vendor', 'driver'
            ).get(id=delivery_id)

            user_id = self.connection_info.user_id

            # صاحب الطلب
            if delivery.order.customer_id == user_id:
                return True

            # السائق
            if delivery.driver_id == user_id:
                return True

            # صاحب المتجر
            if hasattr(delivery.order.vendor, 'owner_id'):
                if delivery.order.vendor.owner_id == user_id:
                    return True

            return False

        except Exception as e:
            logger.warning(f"Tracking access check failed for {delivery_id}: {e}")
            return False

    def _detect_device_type(self) -> str:
        """اكتشاف نوع الجهاز"""
        ua = self.connection_info.user_agent or ''
        ua_lower = ua.lower()

        if 'mobile' in ua_lower or 'android' in ua_lower:
            return 'mobile'
        elif 'tablet' in ua_lower or 'ipad' in ua_lower:
            return 'tablet'
        else:
            return 'desktop'

    def _get_os_from_user_agent(self) -> str:
        """استخراج نظام التشغيل"""
        ua = self.connection_info.user_agent or ''
        ua_lower = ua.lower()

        if 'android' in ua_lower:
            return 'Android'
        elif 'iphone' in ua_lower or 'ipad' in ua_lower:
            return 'iOS'
        elif 'windows' in ua_lower:
            return 'Windows'
        elif 'mac' in ua_lower:
            return 'macOS'
        elif 'linux' in ua_lower:
            return 'Linux'
        else:
            return 'Unknown'

    # =========================================================================
    # Group Message Handlers
    # =========================================================================

    async def notification(self, event: Dict[str, Any]):
        """استقبال إشعار من المجموعة"""
        await self.send_json(event)

    async def chat_message(self, event: Dict[str, Any]):
        """استقبال رسالة chat"""
        await self.send_json(event)

    async def tracking_update(self, event: Dict[str, Any]):
        """استقبال تحديث تتبع"""
        await self.send_json(event)

    async def presence_update(self, event: Dict[str, Any]):
        """استقبال تحديث حضور"""
        await self.send_json(event)


# =============================================================================
# Chat Consumer
# =============================================================================

class ChatConsumer(BaseWebSocketConsumer):
    """
    Consumer للمحادثات

    يدير:
    - إرسال واستقبال الرسائل
    - مؤشرات الكتابة
    - إيصالات القراءة
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_conversation: Optional[str] = None

    async def on_connect(self):
        """بعد نجاح الاتصال"""
        # تسجيل معالجات الرسائل
        self.register_handler('chat.join', self._handle_join)
        self.register_handler('chat.leave', self._handle_leave)
        self.register_handler('chat.send', self._handle_send)
        self.register_handler('chat.typing', self._handle_typing)
        self.register_handler('chat.read', self._handle_read)
        self.register_handler('chat.reaction', self._handle_reaction)

    async def _handle_join(self, content: Dict[str, Any]):
        """الانضمام لمحادثة"""
        from apps.chat.services import get_chat_service

        conversation_id = content.get('conversation_id')
        if not conversation_id:
            return

        # التحقق من المشاركة
        chat_service = get_chat_service()
        try:
            # هذا سيرمي خطأ إذا لم يكن مشاركاً
            await chat_service.get_messages(
                conversation_id,
                self.connection_info.user_id,
                limit=1,
            )
        except PermissionError:
            await self.send_json({
                'type': 'error',
                'code': 'not_participant',
                'message': 'أنت لست مشاركاً في هذه المحادثة',
            })
            return

        # مغادرة المحادثة السابقة
        if self._current_conversation:
            await self.channel_layer.group_discard(
                f"chat_{self._current_conversation}",
                self.channel_name,
            )

        # الانضمام للجديدة
        self._current_conversation = conversation_id
        await self.channel_layer.group_add(
            f"chat_{conversation_id}",
            self.channel_name,
        )

        await self.send_json({
            'type': 'chat.joined',
            'conversation_id': conversation_id,
        })

    async def _handle_leave(self, content: Dict[str, Any]):
        """مغادرة المحادثة"""
        if self._current_conversation:
            await self.channel_layer.group_discard(
                f"chat_{self._current_conversation}",
                self.channel_name,
            )
            self._current_conversation = None

            await self.send_json({
                'type': 'chat.left',
            })

    async def _handle_send(self, content: Dict[str, Any]):
        """إرسال رسالة"""
        from apps.chat.services import MessagePayload, get_chat_service

        if not self._current_conversation:
            await self.send_json({
                'type': 'error',
                'code': 'not_in_conversation',
                'message': 'يجب الانضمام لمحادثة أولاً',
            })
            return

        chat_service = get_chat_service()

        try:
            payload = MessagePayload(
                conversation_id=self._current_conversation,
                sender_id=self.connection_info.user_id,
                content=content.get('content', ''),
                type=content.get('type', 'text'),
                reply_to_id=content.get('reply_to_id'),
                mentions=content.get('mentions', []),
                client_message_id=content.get('client_message_id', ''),
            )

            message = await chat_service.send_message(payload)

            # تأكيد الإرسال
            await self.send_json({
                'type': 'chat.sent',
                'message_id': str(message.id),
                'client_message_id': payload.client_message_id,
            })

        except Exception as e:
            await self.send_json({
                'type': 'error',
                'code': 'send_failed',
                'message': str(e),
            })

    async def _handle_typing(self, content: Dict[str, Any]):
        """مؤشر الكتابة"""
        from apps.chat.services import get_chat_service

        if not self._current_conversation:
            return

        is_typing = content.get('is_typing', True)

        chat_service = get_chat_service()
        await chat_service.set_typing(
            self._current_conversation,
            self.connection_info.user_id,
            is_typing,
        )

    async def _handle_read(self, content: Dict[str, Any]):
        """تحديد كمقروء"""
        from apps.chat.services import get_chat_service

        conversation_id = content.get('conversation_id', self._current_conversation)
        message_id = content.get('message_id')

        if not conversation_id:
            return

        chat_service = get_chat_service()
        count = await chat_service.mark_as_read(
            conversation_id,
            self.connection_info.user_id,
            message_id,
        )

        await self.send_json({
            'type': 'chat.read_confirmed',
            'count': count,
        })

    async def _handle_reaction(self, content: Dict[str, Any]):
        """رد فعل على رسالة"""
        from apps.chat.services import get_chat_service

        message_id = content.get('message_id')
        emoji = content.get('emoji')
        action = content.get('action', 'add')  # add or remove

        if not message_id or not emoji:
            return

        chat_service = get_chat_service()

        if action == 'add':
            await chat_service.add_reaction(
                message_id,
                self.connection_info.user_id,
                emoji,
            )
        else:
            await chat_service.remove_reaction(
                message_id,
                self.connection_info.user_id,
                emoji,
            )

    # =========================================================================
    # Group Message Handlers
    # =========================================================================

    async def chat_message(self, event: Dict[str, Any]):
        """استقبال رسالة"""
        await self.send_json(event)

    async def chat_typing(self, event: Dict[str, Any]):
        """استقبال مؤشر كتابة"""
        # لا نرسل للمستخدم نفسه
        if event.get('user_id') != self.connection_info.user_id:
            await self.send_json(event)

    async def chat_read(self, event: Dict[str, Any]):
        """استقبال إيصال قراءة"""
        await self.send_json(event)


# =============================================================================
# Tracking Consumer
# =============================================================================

class TrackingConsumer(BaseWebSocketConsumer):
    """
    Consumer للتتبع

    يدير:
    - تحديثات الموقع من السائقين
    - بث التحديثات للعملاء
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._subscribed_deliveries: set = set()

    async def on_connect(self):
        """بعد نجاح الاتصال"""
        self.register_handler('tracking.subscribe', self._handle_subscribe)
        self.register_handler('tracking.unsubscribe', self._handle_unsubscribe)
        self.register_handler('tracking.location_update', self._handle_location_update)

    async def _handle_subscribe(self, content: Dict[str, Any]):
        """الاشتراك في تتبع توصيل"""
        from apps.tracking.services import get_tracking_service

        delivery_id = content.get('delivery_id')
        if not delivery_id:
            return

        # التحقق من صلاحية التتبع
        if not await self._check_tracking_permission(delivery_id):
            await self.send_json({
                'type': 'error',
                'code': 'tracking_denied',
                'message': 'غير مصرح لك بتتبع هذا التوصيل',
            })
            return

        tracking = get_tracking_service()
        await tracking.subscribe_to_delivery(
            delivery_id,
            self.connection_info.user_id,
        )

        self._subscribed_deliveries.add(delivery_id)

        # الحصول على المعلومات الحالية
        info = await tracking.get_tracking_info(delivery_id)

        await self.send_json({
            'type': 'tracking.subscribed',
            'delivery_id': delivery_id,
            'current_info': info.to_dict() if info else None,
        })

    async def _handle_unsubscribe(self, content: Dict[str, Any]):
        """إلغاء الاشتراك"""
        from apps.tracking.services import get_tracking_service

        delivery_id = content.get('delivery_id')
        if not delivery_id:
            return

        tracking = get_tracking_service()
        await tracking.unsubscribe_from_delivery(
            delivery_id,
            self.connection_info.user_id,
        )

        self._subscribed_deliveries.discard(delivery_id)

        await self.send_json({
            'type': 'tracking.unsubscribed',
            'delivery_id': delivery_id,
        })

    async def _handle_location_update(self, content: Dict[str, Any]):
        """تحديث موقع (من السائق)"""
        from apps.tracking.services import GeoPoint, LocationUpdate, get_tracking_service

        delivery_id = content.get('delivery_id')
        if not delivery_id:
            return

        # التحقق من أن المستخدم هو السائق المخصص للتوصيل
        if not await self._check_driver_permission(delivery_id):
            await self.send_json({
                'type': 'error',
                'code': 'update_denied',
                'message': 'أنت لست السائق المخصص لهذا التوصيل',
            })
            return

        tracking = get_tracking_service()

        update = LocationUpdate(
            delivery_id=delivery_id,
            driver_id=self.connection_info.user_id,
            point=GeoPoint(
                latitude=content['latitude'],
                longitude=content['longitude'],
                accuracy=content.get('accuracy'),
                timestamp=timezone.now(),
            ),
            speed=content.get('speed', 0),
            heading=content.get('heading', 0),
            battery_level=content.get('battery_level'),
            is_moving=content.get('is_moving', True),
        )

        try:
            info = await tracking.update_location(update)

            await self.send_json({
                'type': 'tracking.update_confirmed',
                'delivery_id': delivery_id,
                'eta': info.eta.estimated_minutes if info.eta else None,
            })

        except Exception as e:
            await self.send_json({
                'type': 'error',
                'code': 'update_failed',
                'message': str(e),
            })

    # =========================================================================
    # Group Message Handlers
    # =========================================================================

    async def tracking_location_update(self, event: Dict[str, Any]):
        """استقبال تحديث موقع"""
        await self.send_json(event)

    async def tracking_status_update(self, event: Dict[str, Any]):
        """استقبال تحديث حالة"""
        await self.send_json(event)

    @database_sync_to_async
    def _check_tracking_permission(self, delivery_id: str) -> bool:
        """
        التحقق من صلاحية تتبع التوصيل

        المستخدمون المسموح لهم:
        - صاحب الطلب
        - السائق المخصص
        - صاحب المتجر
        """
        try:
            from apps.tracking.models import Delivery

            delivery = Delivery.objects.select_related(
                'order', 'order__customer', 'order__vendor', 'driver'
            ).get(id=delivery_id)

            user_id = self.connection_info.user_id

            # صاحب الطلب
            if delivery.order.customer_id == user_id:
                return True

            # السائق المخصص
            if delivery.driver_id == user_id:
                return True

            # صاحب المتجر
            if hasattr(delivery.order.vendor, 'owner_id'):
                if delivery.order.vendor.owner_id == user_id:
                    return True

            return False

        except Exception as e:
            logger.warning(f"Tracking permission check failed for {delivery_id}: {e}")
            return False

    @database_sync_to_async
    def _check_driver_permission(self, delivery_id: str) -> bool:
        """
        التحقق من أن المستخدم هو السائق المخصص للتوصيل
        """
        try:
            from apps.tracking.models import Delivery

            delivery = Delivery.objects.get(id=delivery_id)

            # فقط السائق المخصص يمكنه تحديث الموقع
            return delivery.driver_id == self.connection_info.user_id

        except Exception as e:
            logger.warning(f"Driver permission check failed for {delivery_id}: {e}")
            return False
