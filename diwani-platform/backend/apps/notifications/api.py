"""
===================================
منصة ديواني - Notifications API
Django Ninja API Endpoints for Notifications
===================================
"""

from typing import List, Optional
from uuid import UUID
from math import ceil

from django.utils import timezone
from django.db.models import Q

from ninja import Router, Query

from .models import (
    Notification, NotificationTemplate, NotificationPreference,
    SMSLog, EmailLog, PushLog
)
from .schemas import (
    NotificationOutSchema,
    NotificationListSchema,
    NotificationCountSchema,
    MarkReadSchema,
    NotificationPreferenceOutSchema,
    NotificationPreferenceUpdateSchema,
    SendPushSchema,
    SendSMSSchema,
    SendEmailSchema,
    BroadcastNotificationSchema,
    SMSLogOutSchema,
    EmailLogOutSchema,
    PushLogOutSchema,
    NotificationStatsSchema,
    PaginatedNotificationSchema,
    MessageSchema,
    ErrorSchema,
)

# Create router
router = Router(tags=['الإشعارات'])


# ===================================
# User Notification Endpoints
# ===================================
@router.get('/notifications', response=PaginatedNotificationSchema)
def list_notifications(
    request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    notification_type: Optional[str] = None,
    is_read: Optional[bool] = None
):
    """
    قائمة الإشعارات
    ---
    الحصول على إشعاراتك مع التصفية
    """
    queryset = Notification.objects.filter(user=request.user)

    if notification_type:
        queryset = queryset.filter(notification_type=notification_type)
    if is_read is not None:
        queryset = queryset.filter(is_read=is_read)

    queryset = queryset.order_by('-created_at')

    total = queryset.count()
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    pages = ceil(total / page_size)
    offset = (page - 1) * page_size
    items = list(queryset[offset:offset + page_size])

    return PaginatedNotificationSchema(
        items=[NotificationListSchema.from_orm(n) for n in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
        unread_count=unread_count
    )


@router.get('/notifications/unread', response=List[NotificationListSchema])
def list_unread_notifications(request, limit: int = Query(10, ge=1, le=50)):
    """
    الإشعارات غير المقروءة
    """
    return Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')[:limit]


@router.get('/notifications/count', response=NotificationCountSchema)
def get_notification_count(request):
    """
    عدد الإشعارات
    """
    total = Notification.objects.filter(user=request.user).count()
    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return NotificationCountSchema(total=total, unread=unread)


@router.get('/notifications/{notification_id}', response={200: NotificationOutSchema, 404: ErrorSchema})
def get_notification(request, notification_id: UUID):
    """
    تفاصيل الإشعار
    """
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        return 200, notification
    except Notification.DoesNotExist:
        return 404, ErrorSchema(message='الإشعار غير موجود')


@router.post('/notifications/{notification_id}/read', response=MessageSchema)
def mark_notification_as_read(request, notification_id: UUID):
    """
    تحديد كمقروء
    """
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.mark_as_read()
        return MessageSchema(message='تم تحديد الإشعار كمقروء')
    except Notification.DoesNotExist:
        return MessageSchema(message='الإشعار غير موجود', success=False)


@router.post('/notifications/read', response=MessageSchema)
def mark_notifications_as_read(request, data: MarkReadSchema):
    """
    تحديد مجموعة كمقروءة
    """
    updated = Notification.objects.filter(
        id__in=data.notification_ids,
        user=request.user,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())

    return MessageSchema(message=f'تم تحديد {updated} إشعار كمقروء')


@router.post('/notifications/read-all', response=MessageSchema)
def mark_all_notifications_as_read(request):
    """
    تحديد الكل كمقروء
    """
    updated = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())

    return MessageSchema(message=f'تم تحديد {updated} إشعار كمقروء')


@router.delete('/notifications/{notification_id}', response={200: MessageSchema, 404: ErrorSchema})
def delete_notification(request, notification_id: UUID):
    """
    حذف إشعار
    """
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.delete()
        return 200, MessageSchema(message='تم حذف الإشعار')
    except Notification.DoesNotExist:
        return 404, ErrorSchema(message='الإشعار غير موجود')


@router.delete('/notifications', response=MessageSchema)
def clear_notifications(request, older_than_days: int = Query(30, ge=1)):
    """
    حذف الإشعارات القديمة
    """
    from datetime import timedelta
    cutoff = timezone.now() - timedelta(days=older_than_days)
    deleted, _ = Notification.objects.filter(
        user=request.user,
        created_at__lt=cutoff
    ).delete()
    return MessageSchema(message=f'تم حذف {deleted} إشعار')


# ===================================
# Notification Preferences Endpoints
# ===================================
@router.get('/preferences', response=NotificationPreferenceOutSchema)
def get_notification_preferences(request):
    """
    تفضيلات الإشعارات
    """
    prefs, _ = NotificationPreference.objects.get_or_create(user=request.user)
    return prefs


@router.patch('/preferences', response={200: NotificationPreferenceOutSchema, 400: ErrorSchema})
def update_notification_preferences(request, data: NotificationPreferenceUpdateSchema):
    """
    تحديث التفضيلات
    """
    try:
        prefs, _ = NotificationPreference.objects.get_or_create(user=request.user)
        update_data = data.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(prefs, field, value)

        prefs.save()
        return 200, prefs
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


# ===================================
# Send Notification Endpoints (Admin/System)
# ===================================
@router.post('/send/push', response={200: MessageSchema, 400: ErrorSchema})
def send_push_notification(request, data: SendPushSchema):
    """
    إرسال إشعار فوري
    ---
    للإدارة: إرسال إشعار لمستخدم أو مجموعة
    """
    from apps.accounts.models import User

    try:
        users = []

        if data.user_id:
            users = [User.objects.get(id=data.user_id)]
        elif data.user_ids:
            users = User.objects.filter(id__in=data.user_ids)
        else:
            return 400, ErrorSchema(message='يجب تحديد المستخدم أو المستخدمين')

        sent_count = 0
        for user in users:
            # Create notification record
            notification = Notification.objects.create(
                user=user,
                title=data.title,
                body=data.body,
                notification_type=data.notification_type,
                reference_type=data.reference_type,
                reference_id=data.reference_id,
                image_url=data.image_url,
                action_url=data.action_url,
                action_data=data.action_data
            )

            # Send push if user has FCM token
            if user.fcm_token:
                # TODO: Integrate with Firebase
                PushLog.objects.create(
                    user=user,
                    fcm_token=user.fcm_token,
                    title=data.title,
                    body=data.body,
                    data=data.action_data,
                    notification=notification,
                    status=PushLog.PushStatus.SENT,
                    sent_at=timezone.now()
                )
                notification.push_sent = True
                notification.push_sent_at = timezone.now()
                notification.save(update_fields=['push_sent', 'push_sent_at'])
                sent_count += 1

        return 200, MessageSchema(message=f'تم إرسال {sent_count} إشعار')

    except User.DoesNotExist:
        return 400, ErrorSchema(message='المستخدم غير موجود')
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


@router.post('/send/sms', response={200: MessageSchema, 400: ErrorSchema})
def send_sms(request, data: SendSMSSchema):
    """
    إرسال رسالة SMS
    """
    from apps.accounts.models import User

    try:
        phone_number = data.phone_number
        user = None

        if data.user_id:
            user = User.objects.get(id=data.user_id)
            phone_number = user.phone_number

        if not phone_number:
            return 400, ErrorSchema(message='رقم الجوال مطلوب')

        # Create SMS log
        sms_log = SMSLog.objects.create(
            phone_number=phone_number,
            user=user,
            message=data.message,
            message_type=data.message_type,
            status=SMSLog.SMSStatus.PENDING
        )

        # TODO: Integrate with SMS provider (Unifonic/Msegat)
        # For now, mark as sent
        sms_log.status = SMSLog.SMSStatus.SENT
        sms_log.sent_at = timezone.now()
        sms_log.save()

        return 200, MessageSchema(message='تم إرسال الرسالة')

    except User.DoesNotExist:
        return 400, ErrorSchema(message='المستخدم غير موجود')
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


@router.post('/send/email', response={200: MessageSchema, 400: ErrorSchema})
def send_email(request, data: SendEmailSchema):
    """
    إرسال بريد إلكتروني
    """
    from apps.accounts.models import User

    try:
        email = data.email
        user = None

        if data.user_id:
            user = User.objects.get(id=data.user_id)
            email = user.email

        if not email:
            return 400, ErrorSchema(message='البريد الإلكتروني مطلوب')

        # Create email log
        email_log = EmailLog.objects.create(
            email=email,
            user=user,
            subject=data.subject,
            body_html=data.body_html,
            body_text=data.body_text,
            email_type=data.email_type,
            status=EmailLog.EmailStatus.PENDING
        )

        # TODO: Integrate with email provider
        # For now, mark as sent
        email_log.status = EmailLog.EmailStatus.SENT
        email_log.sent_at = timezone.now()
        email_log.save()

        return 200, MessageSchema(message='تم إرسال البريد')

    except User.DoesNotExist:
        return 400, ErrorSchema(message='المستخدم غير موجود')
    except Exception as e:
        return 400, ErrorSchema(message=str(e))


@router.post('/broadcast', response={200: MessageSchema, 400: ErrorSchema})
def broadcast_notification(request, data: BroadcastNotificationSchema):
    """
    بث إشعار جماعي
    ---
    للإدارة: إرسال إشعار لجميع المستخدمين
    """
    from apps.accounts.models import User

    try:
        queryset = User.objects.filter(is_active=True)

        # Apply filters
        if data.filters:
            if 'city' in data.filters:
                queryset = queryset.filter(
                    addresses__city__icontains=data.filters['city']
                ).distinct()
            if 'user_type' in data.filters:
                queryset = queryset.filter(user_type=data.filters['user_type'])

        sent_count = 0
        for user in queryset:
            Notification.objects.create(
                user=user,
                title=data.title,
                body=data.body,
                notification_type=data.notification_type,
                image_url=data.image_url,
                action_url=data.action_url
            )
            sent_count += 1

            # Send push if enabled
            if user.fcm_token and user.push_notifications_enabled:
                # TODO: Queue push notifications
                pass

        return 200, MessageSchema(message=f'تم إرسال الإشعار لـ {sent_count} مستخدم')

    except Exception as e:
        return 400, ErrorSchema(message=str(e))


# ===================================
# Logs Endpoints (Admin)
# ===================================
@router.get('/logs/sms', response=List[SMSLogOutSchema])
def list_sms_logs(
    request,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = None
):
    """
    سجل الرسائل النصية
    """
    queryset = SMSLog.objects.all()

    if status:
        queryset = queryset.filter(status=status)

    offset = (page - 1) * page_size
    return queryset.order_by('-created_at')[offset:offset + page_size]


@router.get('/logs/email', response=List[EmailLogOutSchema])
def list_email_logs(
    request,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = None
):
    """
    سجل البريد الإلكتروني
    """
    queryset = EmailLog.objects.all()

    if status:
        queryset = queryset.filter(status=status)

    offset = (page - 1) * page_size
    return queryset.order_by('-created_at')[offset:offset + page_size]


@router.get('/logs/push', response=List[PushLogOutSchema])
def list_push_logs(
    request,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: Optional[str] = None
):
    """
    سجل الإشعارات الفورية
    """
    queryset = PushLog.objects.all()

    if status:
        queryset = queryset.filter(status=status)

    offset = (page - 1) * page_size
    return queryset.order_by('-created_at')[offset:offset + page_size]


# ===================================
# Statistics Endpoints (Admin)
# ===================================
@router.get('/stats', response=NotificationStatsSchema)
def get_notification_stats(request):
    """
    إحصائيات الإشعارات
    """
    from django.db.models import Count

    total_push = PushLog.objects.count()
    delivered_push = PushLog.objects.filter(status=PushLog.PushStatus.DELIVERED).count()
    opened_push = PushLog.objects.filter(status=PushLog.PushStatus.OPENED).count()

    delivery_rate = (delivered_push / total_push * 100) if total_push > 0 else 0
    open_rate = (opened_push / delivered_push * 100) if delivered_push > 0 else 0

    by_type = dict(
        Notification.objects.values('notification_type').annotate(
            count=Count('id')
        ).values_list('notification_type', 'count')
    )

    return NotificationStatsSchema(
        total_sent=total_push,
        total_delivered=delivered_push,
        total_opened=opened_push,
        delivery_rate=round(delivery_rate, 2),
        open_rate=round(open_rate, 2),
        by_type=by_type
    )


# ===================================
# FCM Token Endpoint
# ===================================
@router.post('/fcm-token', response=MessageSchema)
def update_fcm_token(request, token: str):
    """
    تحديث رمز FCM
    ---
    يستخدمه التطبيق لتسجيل رمز الإشعارات
    """
    request.user.fcm_token = token
    request.user.save(update_fields=['fcm_token'])
    return MessageSchema(message='تم تحديث رمز الإشعارات')
