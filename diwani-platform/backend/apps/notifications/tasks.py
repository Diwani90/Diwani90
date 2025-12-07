"""
مهام Celery للإشعارات
======================

مهام خلفية لإرسال الإشعارات
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional

from celery import shared_task
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


def _run_async(coro):
    """تشغيل coroutine في Celery بطريقة آمنة"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # إذا كان هناك loop يعمل، ننشئ جديد
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # لا يوجد event loop
        return asyncio.run(coro)


@shared_task(
    name='notifications.send_notification',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
)
def send_notification_task(
    self,
    recipient_id: int,
    title: str,
    body: str,
    category: str = 'system',
    priority: int = 2,
    channels: Optional[List[str]] = None,
    data: Optional[Dict[str, Any]] = None,
    action_url: str = '',
    **kwargs,
):
    """
    مهمة إرسال إشعار واحد

    Args:
        recipient_id: معرف المستلم
        title: عنوان الإشعار
        body: نص الإشعار
        category: فئة الإشعار
        priority: أولوية الإشعار
        channels: قنوات الإرسال
        data: بيانات إضافية
        action_url: رابط الإجراء
    """
    from .services import get_notification_service, NotificationPayload

    logger.info(f"Sending notification to user {recipient_id}: {title}")

    async def _send():
        service = get_notification_service()
        payload = NotificationPayload(
            recipient_id=recipient_id,
            title=title,
            body=body,
            category=category,
            priority=priority,
            channels=channels or ['websocket', 'push'],
            data=data or {},
            action_url=action_url,
        )
        return await service.send(payload)

    try:
        result = _run_async(_send())
        logger.info(f"Notification sent successfully: {result.id}")
        return str(result.id)
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")
        raise


@shared_task(
    name='notifications.send_bulk_notifications',
    bind=True,
    max_retries=2,
)
def send_bulk_notifications_task(
    self,
    user_ids: List[int],
    title: str,
    body: str,
    **kwargs,
):
    """
    مهمة إرسال إشعارات متعددة

    Args:
        user_ids: قائمة معرفات المستخدمين
        title: عنوان الإشعار
        body: نص الإشعار
    """
    from .services import get_notification_service

    logger.info(f"Sending bulk notifications to {len(user_ids)} users")

    async def _send_bulk():
        service = get_notification_service()
        return await service.send_to_users(
            user_ids=user_ids,
            title=title,
            body=body,
            **kwargs,
        )

    try:
        results = _run_async(_send_bulk())
        logger.info(f"Bulk notifications sent: {len(results)} notifications")
        return [str(n.id) for n in results]
    except Exception as e:
        logger.error(f"Failed to send bulk notifications: {e}")
        raise


@shared_task(
    name='notifications.send_from_template',
    bind=True,
    max_retries=3,
)
def send_from_template_task(
    self,
    recipient_id: int,
    template_code: str,
    context: Dict[str, Any],
    channels: Optional[List[str]] = None,
):
    """
    مهمة إرسال إشعار من قالب

    Args:
        recipient_id: معرف المستلم
        template_code: رمز القالب
        context: سياق القالب
        channels: قنوات الإرسال
    """
    from .services import get_notification_service

    logger.info(f"Sending template notification {template_code} to user {recipient_id}")

    async def _send():
        service = get_notification_service()
        return await service.send_from_template(
            recipient_id=recipient_id,
            template_code=template_code,
            context=context,
            channels=channels,
        )

    try:
        result = _run_async(_send())
        if result:
            logger.info(f"Template notification sent: {result.id}")
            return str(result.id)
        return None
    except Exception as e:
        logger.error(f"Failed to send template notification: {e}")
        raise


@shared_task(name='notifications.cleanup_old_notifications')
def cleanup_old_notifications_task(days: int = 30):
    """
    مهمة حذف الإشعارات القديمة

    Args:
        days: عدد الأيام (يتم حذف الأقدم من هذا)
    """
    from .services import get_notification_service

    logger.info(f"Cleaning up notifications older than {days} days")

    async def _cleanup():
        service = get_notification_service()
        return await service.delete_old_notifications(days=days)

    try:
        count = _run_async(_cleanup())
        logger.info(f"Cleaned up {count} old notifications")
        return count
    except Exception as e:
        logger.error(f"Failed to cleanup notifications: {e}")
        raise


@shared_task(name='notifications.process_scheduled')
def process_scheduled_notifications_task():
    """
    مهمة معالجة الإشعارات المجدولة

    يتم تشغيلها بشكل دوري لإرسال الإشعارات المجدولة
    """
    import json
    from django.utils import timezone
    from django.core.cache import cache
    import redis
    from django.conf import settings

    logger.info("Processing scheduled notifications")

    try:
        redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
        r = redis.from_url(redis_url)

        now = timezone.now().timestamp()

        # الحصول على الإشعارات المستحقة
        due_jobs = r.zrangebyscore(
            'notifications:scheduled',
            '-inf',
            now,
        )

        if not due_jobs:
            logger.info("No scheduled notifications due")
            return 0

        count = 0
        for job_data in due_jobs:
            try:
                job = json.loads(job_data)
                notification_id = job.get('notification_id')
                channels = job.get('channels')

                # معالجة الإشعار
                from .models import Notification, NotificationDelivery, DeliveryStatus
                from .services import get_notification_service, UserNotificationPreferences

                async def _process():
                    notification = await Notification.objects.filter(
                        id=notification_id
                    ).afirst()

                    if not notification:
                        return

                    preferences = await UserNotificationPreferences.objects.aget_or_create(
                        user_id=notification.recipient_id
                    )
                    preferences = preferences[0]

                    service = get_notification_service()
                    await service._deliver(
                        notification,
                        preferences,
                        channels or ['websocket', 'push'],
                    )

                _run_async(_process())

                # إزالة من القائمة
                r.zrem('notifications:scheduled', job_data)
                count += 1

            except Exception as e:
                logger.error(f"Error processing scheduled notification: {e}")

        logger.info(f"Processed {count} scheduled notifications")
        return count

    except Exception as e:
        logger.error(f"Failed to process scheduled notifications: {e}")
        raise


# ===================================
# مهمة إحالة المستخدم
# ===================================

@shared_task(
    name='notifications.send_referral_bonus_notification',
    bind=True,
    max_retries=3,
)
def send_referral_bonus_notification_task(
    self,
    referrer_id: str,
    new_user_name: str,
    bonus_points: int,
    total_points: int,
):
    """
    مهمة إرسال إشعار مكافأة الإحالة

    Args:
        referrer_id: معرف المُحيل
        new_user_name: اسم المستخدم الجديد
        bonus_points: نقاط المكافأة
        total_points: إجمالي النقاط
    """
    from .services import get_notification_service, NotificationPayload

    logger.info(f"Sending referral bonus notification to user {referrer_id}")

    async def _send():
        service = get_notification_service()
        payload = NotificationPayload(
            recipient_id=int(referrer_id.replace('-', '')),  # تحويل UUID
            title='مكافأة إحالة! 🎉',
            body=f'تهانينا! لقد حصلت على {bonus_points} نقطة مكافأة لأن صديقك {new_user_name} انضم للمنصة باستخدام رمز الإحالة الخاص بك.',
            category='rewards',
            priority=2,
            channels=['websocket', 'push'],
            data={
                'type': 'referral_bonus',
                'bonus_points': bonus_points,
                'new_user_name': new_user_name,
                'total_points': total_points,
                'action': 'view_rewards',
            },
            action_url='/rewards',
        )
        return await service.send(payload)

    try:
        # محاولة إرسال الإشعار عبر الخدمة
        result = _run_async(_send())
        logger.info(f"Referral notification sent: {result.id}")
        return str(result.id)
    except Exception as e:
        # في حالة فشل الخدمة، نحاول إنشاء إشعار مباشر في قاعدة البيانات
        logger.warning(f"Async notification failed, trying direct DB insert: {e}")
        try:
            from .models import Notification, NotificationCategory, NotificationPriority
            from django.contrib.auth import get_user_model

            User = get_user_model()
            user = User.objects.filter(id=referrer_id).first()

            if user:
                Notification.objects.create(
                    recipient=user,
                    title='مكافأة إحالة! 🎉',
                    body=f'تهانينا! لقد حصلت على {bonus_points} نقطة مكافأة لأن صديقك {new_user_name} انضم للمنصة.',
                    category=NotificationCategory.REWARDS,
                    priority=NotificationPriority.NORMAL,
                    data={
                        'type': 'referral_bonus',
                        'bonus_points': bonus_points,
                        'new_user_name': new_user_name,
                        'total_points': total_points,
                    },
                    action_url='/rewards',
                )
                logger.info(f"Referral notification saved to DB for user {referrer_id}")
                return 'db_saved'
        except Exception as db_error:
            logger.error(f"Failed to save notification to DB: {db_error}")

        raise
