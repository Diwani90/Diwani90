"""
===================================
منصة ديواني - Celery Tasks
مهام الخلفية للإشعارات والرسائل
===================================
"""

import logging
import requests
from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


# ===================================
# SMS Tasks
# ===================================
@shared_task(bind=True, max_retries=3)
def send_sms_task(self, phone_number: str, message: str, message_type: str = 'general'):
    """
    إرسال رسالة SMS عبر Unifonic
    ---
    يحاول إرسال الرسالة 3 مرات في حالة الفشل
    """
    from .models import SMSLog

    # Create SMS log entry
    sms_log = SMSLog.objects.create(
        phone_number=phone_number,
        message=message,
        message_type=message_type,
        provider=SMSLog.SMSProvider.UNIFONIC,
        status=SMSLog.SMSStatus.PENDING
    )

    try:
        # Unifonic API configuration
        unifonic_config = settings.DIWANI_SETTINGS.get('UNIFONIC', {})
        app_sid = unifonic_config.get('APP_SID', '')
        sender_id = unifonic_config.get('SENDER_ID', 'DIWANI')

        if not app_sid:
            logger.warning(f"[SMS] Unifonic APP_SID not configured - message to {phone_number} not sent")
            sms_log.status = SMSLog.SMSStatus.FAILED
            sms_log.error_message = 'Unifonic APP_SID not configured'
            sms_log.save()
            return {'success': False, 'error': 'SMS provider not configured'}

        # Prepare API request
        url = 'https://el.cloud.unifonic.com/rest/SMS/messages'
        payload = {
            'AppSid': app_sid,
            'SenderID': sender_id,
            'Body': message,
            'Recipient': phone_number,
            'responseType': 'JSON',
            'CorrelationID': str(sms_log.id)
        }

        # Send SMS
        response = requests.post(url, data=payload, timeout=30)
        response_data = response.json()

        if response.status_code == 200 and response_data.get('success') == 'true':
            sms_log.status = SMSLog.SMSStatus.SENT
            sms_log.sent_at = timezone.now()
            sms_log.provider_message_id = response_data.get('data', {}).get('MessageID', '')
            sms_log.provider_response = response_data
            sms_log.save()

            logger.info(f"[SMS] Message sent successfully to {phone_number}")
            return {'success': True, 'message_id': sms_log.provider_message_id}
        else:
            raise Exception(response_data.get('message', 'Unknown error'))

    except Exception as exc:
        logger.error(f"[SMS] Failed to send to {phone_number}: {str(exc)}")

        sms_log.status = SMSLog.SMSStatus.FAILED
        sms_log.error_message = str(exc)
        sms_log.save()

        # Retry with exponential backoff
        self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def send_otp_sms(phone_number: str, otp_code: str):
    """
    إرسال رمز OTP عبر SMS
    """
    message = f'رمز التحقق الخاص بك في ديواني: {otp_code}\nلا تشاركه مع أحد.'
    return send_sms_task.delay(phone_number, message, 'otp')


# ===================================
# Push Notification Tasks
# ===================================
@shared_task(bind=True, max_retries=3)
def send_push_notification_task(
    self,
    user_id: str,
    title: str,
    body: str,
    data: dict = None,
    notification_id: str = None
):
    """
    إرسال إشعار Push عبر Firebase Cloud Messaging
    """
    from django.contrib.auth import get_user_model
    from .models import PushLog, Notification

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error(f"[Push] User not found: {user_id}")
        return {'success': False, 'error': 'User not found'}

    if not user.fcm_token:
        logger.warning(f"[Push] User {user_id} has no FCM token")
        return {'success': False, 'error': 'No FCM token'}

    # Create push log entry
    notification = None
    if notification_id:
        notification = Notification.objects.filter(id=notification_id).first()

    push_log = PushLog.objects.create(
        user=user,
        fcm_token=user.fcm_token,
        title=title,
        body=body,
        data=data or {},
        notification=notification,
        status=PushLog.PushStatus.PENDING
    )

    try:
        # Firebase configuration
        firebase_config = settings.DIWANI_SETTINGS.get('FIREBASE', {})
        server_key = firebase_config.get('SERVER_KEY', '')

        if not server_key:
            logger.warning(f"[Push] Firebase SERVER_KEY not configured")
            push_log.status = PushLog.PushStatus.FAILED
            push_log.error_message = 'Firebase SERVER_KEY not configured'
            push_log.save()
            return {'success': False, 'error': 'Push provider not configured'}

        # Prepare FCM request
        url = 'https://fcm.googleapis.com/fcm/send'
        headers = {
            'Authorization': f'key={server_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'to': user.fcm_token,
            'notification': {
                'title': title,
                'body': body,
                'sound': 'default',
                'badge': 1
            },
            'data': data or {},
            'priority': 'high'
        }

        # Send push notification
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response_data = response.json()

        if response.status_code == 200 and response_data.get('success') == 1:
            push_log.status = PushLog.PushStatus.SENT
            push_log.sent_at = timezone.now()
            push_log.fcm_message_id = response_data.get('results', [{}])[0].get('message_id', '')
            push_log.save()

            # Update notification push status
            if notification:
                notification.push_sent = True
                notification.push_sent_at = timezone.now()
                notification.save(update_fields=['push_sent', 'push_sent_at'])

            logger.info(f"[Push] Notification sent successfully to user {user_id}")
            return {'success': True, 'message_id': push_log.fcm_message_id}
        else:
            raise Exception(response_data.get('results', [{}])[0].get('error', 'Unknown error'))

    except Exception as exc:
        logger.error(f"[Push] Failed to send to user {user_id}: {str(exc)}")

        push_log.status = PushLog.PushStatus.FAILED
        push_log.error_message = str(exc)
        push_log.save()

        # Retry with exponential backoff
        self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


# ===================================
# Email Tasks
# ===================================
@shared_task(bind=True, max_retries=3)
def send_email_task(
    self,
    to_email: str,
    subject: str,
    body_html: str,
    body_text: str = '',
    user_id: str = None,
    email_type: str = 'general'
):
    """
    إرسال بريد إلكتروني
    """
    from django.core.mail import send_mail
    from django.contrib.auth import get_user_model
    from .models import EmailLog

    User = get_user_model()

    user = None
    if user_id:
        user = User.objects.filter(id=user_id).first()

    # Create email log entry
    email_log = EmailLog.objects.create(
        email=to_email,
        user=user,
        subject=subject,
        body_html=body_html,
        body_text=body_text or '',
        email_type=email_type,
        status=EmailLog.EmailStatus.PENDING
    )

    try:
        # Send email using Django's email backend
        sent_count = send_mail(
            subject=subject,
            message=body_text,
            html_message=body_html,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False
        )

        if sent_count > 0:
            email_log.status = EmailLog.EmailStatus.SENT
            email_log.sent_at = timezone.now()
            email_log.save()

            logger.info(f"[Email] Sent successfully to {to_email}")
            return {'success': True}
        else:
            raise Exception('Email not sent')

    except Exception as exc:
        logger.error(f"[Email] Failed to send to {to_email}: {str(exc)}")

        email_log.status = EmailLog.EmailStatus.FAILED
        email_log.error_message = str(exc)
        email_log.save()

        # Retry with exponential backoff
        self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


# ===================================
# Notification Tasks
# ===================================
@shared_task
def create_and_send_notification(
    user_id: str,
    title: str,
    body: str,
    notification_type: str = 'system',
    reference_type: str = '',
    reference_id: str = None,
    action_url: str = '',
    action_data: dict = None,
    send_push: bool = True
):
    """
    إنشاء إشعار وإرساله للمستخدم
    """
    from django.contrib.auth import get_user_model
    from .models import Notification

    User = get_user_model()

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.error(f"[Notification] User not found: {user_id}")
        return {'success': False, 'error': 'User not found'}

    # Create notification
    notification = Notification.objects.create(
        user=user,
        title=title,
        body=body,
        notification_type=notification_type,
        reference_type=reference_type,
        reference_id=reference_id,
        action_url=action_url,
        action_data=action_data or {}
    )

    # Send push notification if enabled
    if send_push and user.fcm_token:
        send_push_notification_task.delay(
            user_id=str(user.id),
            title=title,
            body=body,
            data={
                'notification_id': str(notification.id),
                'type': notification_type,
                'reference_type': reference_type,
                'reference_id': str(reference_id) if reference_id else '',
                'action_url': action_url
            },
            notification_id=str(notification.id)
        )

    logger.info(f"[Notification] Created for user {user_id}: {title}")
    return {'success': True, 'notification_id': str(notification.id)}


@shared_task
def send_order_notification(order_id: str, status: str):
    """
    إرسال إشعار تحديث حالة الطلب
    """
    from apps.orders.models import Order
    from .models import NotificationTemplate

    try:
        order = Order.objects.select_related('user').get(id=order_id)
    except Order.DoesNotExist:
        logger.error(f"[Notification] Order not found: {order_id}")
        return {'success': False, 'error': 'Order not found'}

    # Map order status to template type
    status_template_map = {
        'confirmed': NotificationTemplate.TemplateType.ORDER_CONFIRMED,
        'preparing': NotificationTemplate.TemplateType.ORDER_PREPARING,
        'ready': NotificationTemplate.TemplateType.ORDER_READY,
        'on_way': NotificationTemplate.TemplateType.ORDER_ON_WAY,
        'delivered': NotificationTemplate.TemplateType.ORDER_DELIVERED,
        'cancelled': NotificationTemplate.TemplateType.ORDER_CANCELLED,
    }

    template_type = status_template_map.get(status)
    if not template_type:
        logger.warning(f"[Notification] No template for status: {status}")
        return {'success': False, 'error': 'No template for status'}

    # Get template
    template = NotificationTemplate.objects.filter(
        template_type=template_type,
        is_active=True
    ).first()

    if not template:
        logger.warning(f"[Notification] Template not found: {template_type}")
        # Send generic notification
        title = 'تحديث الطلب'
        body = f'تم تحديث حالة طلبك رقم {order.order_number}'
    else:
        # Render template
        context = {
            'order_number': order.order_number,
            'store_name': order.store.name if order.store else '',
            'total': str(order.total_amount),
        }
        rendered = template.render(context, language='ar')
        title = rendered['title']
        body = rendered['body']

    # Create and send notification
    create_and_send_notification.delay(
        user_id=str(order.user.id),
        title=title,
        body=body,
        notification_type='order',
        reference_type='order',
        reference_id=str(order.id),
        action_url=f'/orders/{order.id}',
        action_data={'order_id': str(order.id), 'status': status}
    )

    return {'success': True}


# ===================================
# Cleanup Tasks (Scheduled)
# ===================================
@shared_task
def cleanup_old_notifications():
    """
    حذف الإشعارات القديمة (أكثر من 90 يوم)
    """
    from datetime import timedelta
    from .models import Notification

    cutoff_date = timezone.now() - timedelta(days=90)
    deleted_count, _ = Notification.objects.filter(
        created_at__lt=cutoff_date,
        is_read=True
    ).delete()

    logger.info(f"[Cleanup] Deleted {deleted_count} old notifications")
    return {'deleted': deleted_count}


@shared_task
def cleanup_expired_otps():
    """
    حذف رموز OTP المنتهية الصلاحية
    """
    from apps.accounts.models import OTP

    deleted_count, _ = OTP.objects.filter(
        expires_at__lt=timezone.now()
    ).delete()

    logger.info(f"[Cleanup] Deleted {deleted_count} expired OTPs")
    return {'deleted': deleted_count}
