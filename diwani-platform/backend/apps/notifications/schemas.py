"""
===================================
منصة ديواني - Notifications Schemas
Pydantic schemas for Notification APIs
===================================
"""

from typing import Optional, List
from datetime import datetime, time
from uuid import UUID

from ninja import Schema, Field


# ===================================
# Notification Schemas
# ===================================
class NotificationOutSchema(Schema):
    """Schema for notification output."""
    id: UUID
    title: str
    body: str
    notification_type: str
    reference_type: str
    reference_id: Optional[UUID]
    image_url: str
    action_url: str
    action_data: dict
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime


class NotificationListSchema(Schema):
    """Schema for notification listing."""
    id: UUID
    title: str
    body: str
    notification_type: str
    is_read: bool
    created_at: datetime


class NotificationCountSchema(Schema):
    """Schema for notification counts."""
    total: int
    unread: int


class MarkReadSchema(Schema):
    """Schema for marking notifications as read."""
    notification_ids: List[UUID]


# ===================================
# Notification Preference Schemas
# ===================================
class NotificationPreferenceOutSchema(Schema):
    """Schema for notification preferences output."""
    push_orders: bool
    push_promotions: bool
    push_news: bool
    push_chat: bool
    sms_orders: bool
    sms_otp: bool
    sms_promotions: bool
    email_orders: bool
    email_promotions: bool
    email_newsletter: bool
    quiet_hours_enabled: bool
    quiet_hours_start: Optional[time]
    quiet_hours_end: Optional[time]


class NotificationPreferenceUpdateSchema(Schema):
    """Schema for updating notification preferences."""
    push_orders: Optional[bool] = None
    push_promotions: Optional[bool] = None
    push_news: Optional[bool] = None
    push_chat: Optional[bool] = None
    sms_orders: Optional[bool] = None
    sms_otp: Optional[bool] = None
    sms_promotions: Optional[bool] = None
    email_orders: Optional[bool] = None
    email_promotions: Optional[bool] = None
    email_newsletter: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[time] = None
    quiet_hours_end: Optional[time] = None


# ===================================
# Send Notification Schemas
# ===================================
class SendPushSchema(Schema):
    """Schema for sending push notification."""
    user_id: Optional[UUID] = None
    user_ids: Optional[List[UUID]] = None
    title: str
    body: str
    notification_type: str = 'system'
    reference_type: str = ''
    reference_id: Optional[UUID] = None
    image_url: str = ''
    action_url: str = ''
    action_data: dict = {}


class SendSMSSchema(Schema):
    """Schema for sending SMS."""
    phone_number: Optional[str] = None
    user_id: Optional[UUID] = None
    message: str
    message_type: str = 'general'


class SendEmailSchema(Schema):
    """Schema for sending email."""
    email: Optional[str] = None
    user_id: Optional[UUID] = None
    subject: str
    body_html: str
    body_text: str = ''
    email_type: str = 'general'


class BroadcastNotificationSchema(Schema):
    """Schema for broadcasting notification to all users."""
    title: str
    body: str
    notification_type: str = 'promo'
    image_url: str = ''
    action_url: str = ''
    filters: dict = {}  # e.g., {"city": "Riyadh", "user_type": "customer"}


# ===================================
# SMS Log Schemas
# ===================================
class SMSLogOutSchema(Schema):
    """Schema for SMS log output."""
    id: UUID
    phone_number: str
    message: str
    message_type: str
    provider: str
    status: str
    error_message: str
    cost: float
    created_at: datetime
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]


# ===================================
# Email Log Schemas
# ===================================
class EmailLogOutSchema(Schema):
    """Schema for email log output."""
    id: UUID
    email: str
    subject: str
    email_type: str
    status: str
    error_message: str
    opened_at: Optional[datetime]
    clicked_at: Optional[datetime]
    created_at: datetime
    sent_at: Optional[datetime]


# ===================================
# Push Log Schemas
# ===================================
class PushLogOutSchema(Schema):
    """Schema for push log output."""
    id: UUID
    user_id: Optional[UUID]
    title: str
    body: str
    status: str
    error_message: str
    created_at: datetime
    sent_at: Optional[datetime]
    opened_at: Optional[datetime]

    @staticmethod
    def resolve_user_id(obj):
        return obj.user.id if obj.user else None


# ===================================
# Statistics Schemas
# ===================================
class NotificationStatsSchema(Schema):
    """Schema for notification statistics."""
    total_sent: int
    total_delivered: int
    total_opened: int
    delivery_rate: float
    open_rate: float
    by_type: dict


# ===================================
# Pagination Schemas
# ===================================
class PaginatedNotificationSchema(Schema):
    """Schema for paginated notifications."""
    items: List[NotificationListSchema]
    total: int
    page: int
    page_size: int
    pages: int
    unread_count: int


# ===================================
# Common Response Schemas
# ===================================
class MessageSchema(Schema):
    """Simple message response."""
    message: str
    success: bool = True


class ErrorSchema(Schema):
    """Error response schema."""
    message: str
    code: Optional[str] = None
