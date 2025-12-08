"""
Chat API
=========

Django Ninja API for chat functionality
"""

import logging
from typing import Optional
from uuid import UUID

from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from django.db.models import Q, Max
from django.db import transaction
from ninja import Router

from .models import (
    Conversation,
    ConversationParticipant,
    ConversationType,
    Message,
    MessageType,
    MessageStatus,
    ParticipantRole,
)
from apps.users.auth import JWTAuth

logger = logging.getLogger(__name__)
router = Router()


# =============================================
# المحادثات
# =============================================

@router.get('/conversations', auth=JWTAuth(), tags=['المحادثات'])
def get_conversations(request):
    """الحصول على محادثات المستخدم"""
    user = request.user

    # الحصول على المشاركات النشطة
    participations = ConversationParticipant.objects.filter(
        user=user,
        is_active=True,
        conversation__is_archived=False,
    ).select_related('conversation').order_by('-conversation__last_message_at')

    conversations = []
    for participation in participations:
        conv = participation.conversation

        # الحصول على الطرف الآخر في المحادثة المباشرة
        other_participant = ConversationParticipant.objects.filter(
            conversation=conv,
            is_active=True,
        ).exclude(user=user).select_related('user').first()

        other_user = None
        if other_participant:
            other_user = {
                'id': other_participant.user.id,
                'full_name': other_participant.user.full_name or other_participant.user.phone_number,
                'role': other_participant.user.role,
                'company_name': getattr(other_participant.user, 'company_name', None),
            }

        # آخر رسالة
        last_message = Message.objects.filter(
            conversation=conv,
            is_deleted=False,
        ).order_by('-created_at').first()

        last_message_data = None
        if last_message:
            last_message_data = {
                'id': str(last_message.id),
                'content': last_message.content[:100] if last_message.content else f'[{last_message.type}]',
                'sender_id': last_message.sender_id,
                'created_at': last_message.created_at.isoformat(),
            }

        conversations.append({
            'conversation_id': str(conv.id),
            'type': conv.type,
            'name': conv.name or (other_user['full_name'] if other_user else 'محادثة'),
            'other_user': other_user,
            'unread_count': participation.unread_count,
            'is_muted': participation.is_muted,
            'last_message': last_message_data,
            'last_message_at': conv.last_message_at.isoformat() if conv.last_message_at else None,
            'created_at': conv.created_at.isoformat(),
        })

    return {'conversations': conversations}


@router.get('/{conversation_id}/messages', auth=JWTAuth(), tags=['المحادثات'])
def get_messages(
    request,
    conversation_id: UUID,
    limit: int = 50,
    before: Optional[str] = None
):
    """الحصول على رسائل محادثة"""
    user = request.user

    # التحقق من المشاركة
    participation = ConversationParticipant.objects.filter(
        conversation_id=conversation_id,
        user=user,
        is_active=True,
    ).first()

    if not participation:
        return {'error': 'أنت لست مشاركاً في هذه المحادثة', 'messages': []}

    # الحصول على الرسائل
    queryset = Message.objects.filter(
        conversation_id=conversation_id,
    ).filter(
        Q(is_deleted=False) | Q(deleted_for_all=False)
    ).select_related('sender').order_by('-created_at')

    if before:
        from datetime import datetime
        try:
            before_dt = datetime.fromisoformat(before.replace('Z', '+00:00'))
            queryset = queryset.filter(created_at__lt=before_dt)
        except ValueError:
            pass

    queryset = queryset[:limit]

    messages = []
    for msg in queryset:
        messages.append({
            'id': str(msg.id),
            'conversation_id': str(msg.conversation_id),
            'sender_id': msg.sender_id,
            'sender_name': msg.sender.full_name if msg.sender else None,
            'type': msg.type,
            'content': msg.content if not msg.is_deleted else '[تم حذف الرسالة]',
            'status': msg.status,
            'is_edited': msg.is_edited,
            'is_deleted': msg.is_deleted,
            'created_at': msg.created_at.isoformat(),
            'is_mine': msg.sender_id == user.id,
        })

    # تحديد كمقروء
    participation.unread_count = 0
    participation.save(update_fields=['unread_count'])

    # عكس الترتيب للعرض (من الأقدم للأحدث)
    messages.reverse()

    return {'messages': messages}


@router.post('/send', auth=JWTAuth(), tags=['المحادثات'])
def send_message(request, receiver_id: int, content: str, message_type: str = 'text'):
    """إرسال رسالة"""
    user = request.user

    if not content.strip():
        return {'error': 'محتوى الرسالة مطلوب', 'success': False}

    # البحث عن محادثة مباشرة موجودة
    conversation = _find_or_create_direct_conversation(user.id, receiver_id)

    # إنشاء الرسالة
    message = Message.objects.create(
        conversation=conversation,
        sender=user,
        type=MessageType.TEXT if message_type == 'text' else message_type,
        content=content.strip(),
        status=MessageStatus.SENT,
    )

    # تحديث المحادثة
    from django.utils import timezone
    conversation.last_message_at = timezone.now()
    conversation.save(update_fields=['last_message_at'])

    # تحديث عداد غير المقروءة للطرف الآخر
    ConversationParticipant.objects.filter(
        conversation=conversation,
        is_active=True,
    ).exclude(user=user).update(
        unread_count=Message.objects.raw(
            'SELECT 1 as id'  # Dummy query, using F() below
        ).__class__.objects.none()  # Reset and use F expression
    )

    # Using proper update
    from django.db.models import F
    ConversationParticipant.objects.filter(
        conversation=conversation,
        is_active=True,
    ).exclude(user=user).update(unread_count=F('unread_count') + 1)

    return {
        'id': str(message.id),
        'conversation_id': str(conversation.id),
        'sender_id': user.id,
        'content': message.content,
        'type': message.type,
        'status': message.status,
        'created_at': message.created_at.isoformat(),
        'success': True,
    }


@router.post('/start', auth=JWTAuth(), tags=['المحادثات'])
def start_conversation(request, user_id: int):
    """بدء محادثة جديدة مع مستخدم"""
    from apps.users.models import User

    current_user = request.user

    # التحقق من وجود المستخدم
    other_user = get_object_or_404(User, id=user_id)

    if other_user.id == current_user.id:
        return {'error': 'لا يمكنك بدء محادثة مع نفسك', 'success': False}

    # البحث عن محادثة موجودة أو إنشاء جديدة
    conversation = _find_or_create_direct_conversation(current_user.id, other_user.id)

    # الحصول على المشاركة
    participation = ConversationParticipant.objects.filter(
        conversation=conversation,
        user=current_user,
    ).first()

    return {
        'conversation_id': str(conversation.id),
        'other_user': {
            'id': other_user.id,
            'full_name': other_user.full_name or other_user.phone_number,
            'role': other_user.role,
        },
        'unread_count': participation.unread_count if participation else 0,
        'success': True,
    }


@router.post('/{conversation_id}/read', auth=JWTAuth(), tags=['المحادثات'])
def mark_as_read(request, conversation_id: UUID):
    """تحديد الرسائل كمقروءة"""
    user = request.user

    participation = ConversationParticipant.objects.filter(
        conversation_id=conversation_id,
        user=user,
        is_active=True,
    ).first()

    if not participation:
        return {'error': 'أنت لست مشاركاً في هذه المحادثة', 'success': False}

    from django.utils import timezone
    participation.unread_count = 0
    participation.last_read_at = timezone.now()
    participation.save(update_fields=['unread_count', 'last_read_at'])

    return {'success': True, 'message': 'تم تحديد الرسائل كمقروءة'}


# =============================================
# دوال مساعدة
# =============================================

def _find_or_create_direct_conversation(user1_id: int, user2_id: int) -> Conversation:
    """البحث عن محادثة مباشرة أو إنشاء واحدة جديدة"""
    from apps.users.models import User

    # البحث عن محادثة موجودة
    user1_participations = ConversationParticipant.objects.filter(
        user_id=user1_id,
        conversation__type=ConversationType.DIRECT,
        is_active=True,
    ).values_list('conversation_id', flat=True)

    existing_conversation = Conversation.objects.filter(
        id__in=user1_participations,
        participants__user_id=user2_id,
        participants__is_active=True,
    ).first()

    if existing_conversation:
        return existing_conversation

    # إنشاء محادثة جديدة
    with transaction.atomic():
        conversation = Conversation.objects.create(
            type=ConversationType.DIRECT,
        )

        # إضافة المشاركين
        ConversationParticipant.objects.create(
            conversation=conversation,
            user_id=user1_id,
            role=ParticipantRole.MEMBER,
        )

        ConversationParticipant.objects.create(
            conversation=conversation,
            user_id=user2_id,
            role=ParticipantRole.MEMBER,
        )

    return conversation
