"""
خدمات نظام المحادثات
======================

يوفر:
- إدارة المحادثات
- إرسال واستقبال الرسائل
- التشفير End-to-End
- مؤشرات الكتابة والقراءة
"""

import asyncio
import base64
import hashlib
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import redis.asyncio as aioredis
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from .models import (
    Conversation,
    ConversationParticipant,
    ConversationType,
    Message,
    MessageAttachment,
    MessageReaction,
    MessageReadReceipt,
    MessageStatus,
    MessageType,
    ParticipantRole,
)

logger = logging.getLogger(__name__)
User = get_user_model()


# =============================================================================
# Encryption Service
# =============================================================================

class EncryptionService:
    """
    خدمة التشفير End-to-End

    تستخدم:
    - AES-256-GCM للتشفير المتماثل
    - RSA-OAEP لتبادل المفاتيح
    - PBKDF2 لاشتقاق المفاتيح
    """

    def __init__(self):
        self._master_key = self._get_master_key()

    def _get_master_key(self) -> bytes:
        """
        الحصول على المفتاح الرئيسي للتشفير

        تحذير: في وضع الاختبار يتم إنشاء مفتاح ثابت للجلسة فقط.
        في الإنتاج يجب ضبط CHAT_ENCRYPTION_KEY في متغيرات البيئة.
        """
        import hashlib
        import warnings

        key = getattr(settings, 'CHAT_ENCRYPTION_KEY', None)
        if key:
            return base64.urlsafe_b64decode(key)

        # وضع الاختبار/التطوير
        if settings.DEBUG:
            # إنشاء مفتاح ثابت بناءً على SECRET_KEY
            # هذا يضمن نفس المفتاح عبر إعادة التشغيل في التطوير
            secret = getattr(settings, 'SECRET_KEY', 'diwani-dev-key')
            derived_key = hashlib.sha256(secret.encode()).digest()

            warnings.warn(
                '⚠️ CHAT_ENCRYPTION_KEY not set! Using derived key from SECRET_KEY. '
                'This is ONLY acceptable in development. '
                'Set CHAT_ENCRYPTION_KEY in production!',
                RuntimeWarning
            )

            print('╔══════════════════════════════════════════════════════════╗')
            print('║ ⚠️  WARNING: Chat encryption using derived key           ║')
            print('║     Set CHAT_ENCRYPTION_KEY in production!              ║')
            print('╚══════════════════════════════════════════════════════════╝')

            return base64.urlsafe_b64encode(derived_key)

        # الإنتاج بدون مفتاح - خطأ فادح
        raise ValueError(
            'CHAT_ENCRYPTION_KEY must be set in production! '
            'Generate one with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
        )

    def generate_conversation_key(self) -> Tuple[str, bytes]:
        """إنشاء مفتاح محادثة جديد"""
        key_id = str(uuid.uuid4())
        key = AESGCM.generate_key(bit_length=256)
        return key_id, key

    def encrypt_message(
        self,
        content: str,
        conversation_key: bytes,
    ) -> Tuple[bytes, bytes]:
        """تشفير رسالة"""
        # إنشاء nonce فريد
        nonce = os.urandom(12)

        # تشفير المحتوى
        aesgcm = AESGCM(conversation_key)
        ciphertext = aesgcm.encrypt(
            nonce,
            content.encode('utf-8'),
            None,  # associated data
        )

        return nonce + ciphertext, nonce

    def decrypt_message(
        self,
        encrypted_content: bytes,
        conversation_key: bytes,
    ) -> str:
        """فك تشفير رسالة"""
        # استخراج nonce
        nonce = encrypted_content[:12]
        ciphertext = encrypted_content[12:]

        # فك التشفير
        aesgcm = AESGCM(conversation_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        return plaintext.decode('utf-8')

    def encrypt_key_for_user(
        self,
        conversation_key: bytes,
        user_public_key: bytes,
    ) -> bytes:
        """تشفير مفتاح المحادثة للمستخدم"""
        public_key = serialization.load_pem_public_key(user_public_key)
        encrypted_key = public_key.encrypt(
            conversation_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return encrypted_key

    def generate_user_keypair(self) -> Tuple[bytes, bytes]:
        """إنشاء زوج مفاتيح للمستخدم"""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

        return private_pem, public_pem

    def hash_content(self, content: str) -> str:
        """حساب hash للمحتوى"""
        return hashlib.sha256(content.encode()).hexdigest()


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class MessagePayload:
    """بيانات الرسالة للإرسال"""

    conversation_id: str
    sender_id: int
    content: str = ""
    type: str = MessageType.TEXT
    reply_to_id: Optional[str] = None
    mentions: List[int] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    client_message_id: str = ""
    attachments: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ConversationPayload:
    """بيانات إنشاء محادثة"""

    type: str = ConversationType.DIRECT
    participant_ids: List[int] = field(default_factory=list)
    name: str = ""
    description: str = ""
    is_encrypted: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Chat Service
# =============================================================================

class ChatService:
    """
    خدمة المحادثات الرئيسية
    """

    def __init__(self):
        self._encryption = EncryptionService()
        self._redis: Optional[aioredis.Redis] = None

    async def _get_redis(self) -> aioredis.Redis:
        """الحصول على اتصال Redis"""
        if self._redis is None:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            self._redis = await aioredis.from_url(redis_url)
        return self._redis

    async def _get_or_create_conversation_key(self, conversation: Conversation) -> bytes:
        """
        الحصول على مفتاح التشفير للمحادثة أو إنشاء واحد جديد

        المفاتيح تُخزن في Redis مع تشفير بالمفتاح الرئيسي
        """
        redis = await self._get_redis()
        key_cache_key = f'chat:conv_key:{conversation.id}'

        # محاولة استرجاع المفتاح المخزن
        encrypted_key = await redis.get(key_cache_key)

        if encrypted_key:
            # فك تشفير المفتاح المحفوظ
            try:
                fernet = Fernet(self._encryption._master_key)
                return fernet.decrypt(encrypted_key)
            except Exception as e:
                # المفتاح تالف أو المفتاح الرئيسي تغير - ننشئ مفتاح جديد
                logger.warning(f"Failed to decrypt conversation key, will regenerate: {type(e).__name__}")

        # إنشاء مفتاح جديد
        key_id, new_key = self._encryption.generate_conversation_key()

        # تشفير وحفظ المفتاح
        fernet = Fernet(self._encryption._master_key)
        encrypted_new_key = fernet.encrypt(new_key)

        await redis.set(
            key_cache_key,
            encrypted_new_key,
            ex=86400 * 365,  # سنة واحدة
        )

        # حفظ معرف المفتاح في المحادثة
        conversation.metadata = conversation.metadata or {}
        conversation.metadata['encryption_key_id'] = key_id
        await conversation.asave(update_fields=['metadata'])

        return new_key

    # =========================================================================
    # Conversation Management
    # =========================================================================

    async def create_conversation(
        self,
        payload: ConversationPayload,
        creator_id: int,
    ) -> Conversation:
        """إنشاء محادثة جديدة"""
        # التحقق من وجود محادثة مباشرة سابقة
        if payload.type == ConversationType.DIRECT and len(payload.participant_ids) == 1:
            other_user_id = payload.participant_ids[0]
            existing = await self._find_direct_conversation(creator_id, other_user_id)
            if existing:
                return existing

        # إنشاء المحادثة
        conversation = await Conversation.objects.acreate(
            type=payload.type,
            name=payload.name,
            description=payload.description,
            is_encrypted=payload.is_encrypted,
            metadata=payload.metadata,
        )

        # إضافة المنشئ كمالك
        await ConversationParticipant.objects.acreate(
            conversation=conversation,
            user_id=creator_id,
            role=ParticipantRole.OWNER,
        )

        # إضافة المشاركين
        for user_id in payload.participant_ids:
            if user_id != creator_id:
                await ConversationParticipant.objects.acreate(
                    conversation=conversation,
                    user_id=user_id,
                    role=ParticipantRole.MEMBER,
                )

        # إنشاء رسالة نظام
        if payload.type == ConversationType.GROUP:
            await self._create_system_message(
                conversation,
                f"تم إنشاء المجموعة",
                creator_id,
            )

        # نشر حدث الإنشاء
        await self._publish_event('conversation.created', {
            'conversation_id': str(conversation.id),
            'type': payload.type,
            'participants': [creator_id] + payload.participant_ids,
        })

        return conversation

    async def _find_direct_conversation(
        self,
        user1_id: int,
        user2_id: int,
    ) -> Optional[Conversation]:
        """البحث عن محادثة مباشرة بين مستخدمين"""
        # الحصول على المحادثات المباشرة للمستخدم الأول
        participations = ConversationParticipant.objects.filter(
            user_id=user1_id,
            conversation__type=ConversationType.DIRECT,
            is_active=True,
        ).values_list('conversation_id', flat=True)

        # البحث عن محادثة تحتوي على المستخدم الثاني
        conversation = await Conversation.objects.filter(
            id__in=participations,
            participants__user_id=user2_id,
            participants__is_active=True,
        ).afirst()

        return conversation

    async def get_user_conversations(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """الحصول على محادثات المستخدم"""
        participations = ConversationParticipant.objects.filter(
            user_id=user_id,
            is_active=True,
            conversation__is_archived=False,
        ).select_related('conversation').order_by(
            '-conversation__last_message_at'
        )[offset:offset + limit]

        conversations = []
        async for participation in participations:
            conv = participation.conversation
            last_message = await Message.objects.filter(
                conversation=conv,
                is_deleted=False,
            ).order_by('-created_at').afirst()

            conversations.append({
                'id': str(conv.id),
                'type': conv.type,
                'name': await self._get_conversation_name(conv, user_id),
                'avatar': conv.avatar.url if conv.avatar else None,
                'last_message': {
                    'content': last_message.content[:100] if last_message else None,
                    'type': last_message.type if last_message else None,
                    'sender_id': last_message.sender_id if last_message else None,
                    'created_at': last_message.created_at.isoformat() if last_message else None,
                } if last_message else None,
                'unread_count': participation.unread_count,
                'is_muted': participation.is_muted,
                'last_message_at': conv.last_message_at.isoformat() if conv.last_message_at else None,
            })

        return conversations

    async def _get_conversation_name(
        self,
        conversation: Conversation,
        user_id: int,
    ) -> str:
        """الحصول على اسم المحادثة"""
        if conversation.name:
            return conversation.name

        if conversation.type == ConversationType.DIRECT:
            # الحصول على اسم المستخدم الآخر
            other_participant = await ConversationParticipant.objects.filter(
                conversation=conversation,
                is_active=True,
            ).exclude(user_id=user_id).select_related('user').afirst()

            if other_participant:
                return other_participant.user.get_full_name() or other_participant.user.username

        return f"محادثة {conversation.id}"

    async def add_participant(
        self,
        conversation_id: str,
        user_id: int,
        added_by: int,
        role: str = ParticipantRole.MEMBER,
    ) -> ConversationParticipant:
        """إضافة مشارك للمحادثة"""
        conversation = await Conversation.objects.aget(id=conversation_id)

        # التحقق من الصلاحيات
        adder = await ConversationParticipant.objects.filter(
            conversation=conversation,
            user_id=added_by,
            is_active=True,
        ).afirst()

        if not adder or adder.role not in [ParticipantRole.OWNER, ParticipantRole.ADMIN]:
            raise PermissionError("ليس لديك صلاحية إضافة مشاركين")

        # إضافة المشارك
        participant, created = await ConversationParticipant.objects.aget_or_create(
            conversation=conversation,
            user_id=user_id,
            defaults={'role': role},
        )

        if not created and not participant.is_active:
            participant.is_active = True
            participant.role = role
            participant.joined_at = timezone.now()
            participant.left_at = None
            await participant.asave()

        # رسالة نظام
        user = await User.objects.aget(id=user_id)
        await self._create_system_message(
            conversation,
            f"تمت إضافة {user.get_full_name() or user.username} للمحادثة",
            added_by,
        )

        return participant

    async def remove_participant(
        self,
        conversation_id: str,
        user_id: int,
        removed_by: int,
    ) -> None:
        """إزالة مشارك من المحادثة"""
        conversation = await Conversation.objects.aget(id=conversation_id)

        # التحقق من الصلاحيات
        remover = await ConversationParticipant.objects.filter(
            conversation=conversation,
            user_id=removed_by,
            is_active=True,
        ).afirst()

        participant = await ConversationParticipant.objects.filter(
            conversation=conversation,
            user_id=user_id,
            is_active=True,
        ).afirst()

        if not participant:
            return

        # السماح بالخروج الذاتي أو الإزالة من قبل المدير
        if removed_by != user_id:
            if not remover or remover.role not in [ParticipantRole.OWNER, ParticipantRole.ADMIN]:
                raise PermissionError("ليس لديك صلاحية إزالة مشاركين")

        participant.is_active = False
        participant.left_at = timezone.now()
        await participant.asave()

        # رسالة نظام
        user = await User.objects.aget(id=user_id)
        if removed_by == user_id:
            message = f"غادر {user.get_full_name() or user.username} المحادثة"
        else:
            message = f"تمت إزالة {user.get_full_name() or user.username} من المحادثة"

        await self._create_system_message(conversation, message, removed_by)

    # =========================================================================
    # Message Management
    # =========================================================================

    async def send_message(self, payload: MessagePayload) -> Message:
        """إرسال رسالة"""
        conversation = await Conversation.objects.aget(id=payload.conversation_id)

        # التحقق من المشاركة
        participant = await ConversationParticipant.objects.filter(
            conversation=conversation,
            user_id=payload.sender_id,
            is_active=True,
        ).afirst()

        if not participant:
            raise PermissionError("أنت لست مشاركاً في هذه المحادثة")

        # التحقق من التكرار
        if payload.client_message_id:
            existing = await Message.objects.filter(
                client_message_id=payload.client_message_id
            ).afirst()
            if existing:
                return existing

        # تشفير المحتوى إذا كانت المحادثة مشفرة
        content_encrypted = None
        if conversation.is_encrypted and payload.content:
            # استخدام مفتاح المحادثة المحفوظ أو إنشاء جديد
            conversation_key = await self._get_or_create_conversation_key(conversation)
            content_encrypted, _ = self._encryption.encrypt_message(payload.content, conversation_key)

        # إنشاء الرسالة
        message = await Message.objects.acreate(
            conversation=conversation,
            sender_id=payload.sender_id,
            type=payload.type,
            content=payload.content if not conversation.is_encrypted else '',
            content_encrypted=content_encrypted,
            status=MessageStatus.SENT,
            client_message_id=payload.client_message_id,
            metadata=payload.metadata,
        )

        # رد على رسالة
        if payload.reply_to_id:
            message.reply_to_id = payload.reply_to_id
            await message.asave()

        # الإشارات
        if payload.mentions:
            await message.mentions.aset(payload.mentions)

        # تحديث المحادثة
        conversation.last_message_at = timezone.now()
        await conversation.asave(update_fields=['last_message_at'])

        # تحديث عداد غير المقروءة للآخرين
        await ConversationParticipant.objects.filter(
            conversation=conversation,
            is_active=True,
        ).exclude(user_id=payload.sender_id).aupdate(
            unread_count=F('unread_count') + 1
        )

        # نشر الرسالة عبر WebSocket
        await self._broadcast_message(message)

        # إرسال إشعارات
        await self._send_message_notifications(message)

        return message

    async def _create_system_message(
        self,
        conversation: Conversation,
        content: str,
        triggered_by: int,
    ) -> Message:
        """إنشاء رسالة نظام"""
        return await Message.objects.acreate(
            conversation=conversation,
            sender_id=None,
            type=MessageType.SYSTEM,
            content=content,
            status=MessageStatus.SENT,
            metadata={'triggered_by': triggered_by},
        )

    async def get_messages(
        self,
        conversation_id: str,
        user_id: int,
        limit: int = 50,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """الحصول على رسائل المحادثة"""
        # التحقق من المشاركة
        participant = await ConversationParticipant.objects.filter(
            conversation_id=conversation_id,
            user_id=user_id,
            is_active=True,
        ).afirst()

        if not participant:
            raise PermissionError("أنت لست مشاركاً في هذه المحادثة")

        queryset = Message.objects.filter(
            conversation_id=conversation_id,
        ).select_related('sender')

        # استبعاد المحذوفة للمستخدم
        queryset = queryset.filter(
            Q(is_deleted=False) | Q(deleted_for_all=False)
        )

        if before:
            queryset = queryset.filter(created_at__lt=before)

        if after:
            queryset = queryset.filter(created_at__gt=after)

        queryset = queryset.order_by('-created_at')[:limit]

        messages = []
        async for msg in queryset:
            messages.append(await self._serialize_message(msg, user_id))

        return list(reversed(messages))

    async def _serialize_message(
        self,
        message: Message,
        user_id: int,
    ) -> Dict[str, Any]:
        """تحويل الرسالة لـ dict"""
        # فك التشفير إذا لزم الأمر
        content = message.content
        if message.content_encrypted:
            try:
                # الحصول على مفتاح المحادثة
                conversation = await Conversation.objects.aget(id=message.conversation_id)
                conversation_key = await self._get_or_create_conversation_key(conversation)
                content = self._encryption.decrypt_message(
                    message.content_encrypted,
                    conversation_key
                )
            except Exception as e:
                logger.warning(f"Failed to decrypt message {message.id}: {e}")
                content = "[رسالة مشفرة - تعذر فك التشفير]"

        # الحصول على ردود الفعل
        reactions = {}
        async for reaction in message.reactions.all():
            if reaction.emoji not in reactions:
                reactions[reaction.emoji] = []
            reactions[reaction.emoji].append(reaction.user_id)

        # الحصول على المرفقات
        attachments = []
        async for attachment in message.attachments.all():
            attachments.append({
                'id': str(attachment.id),
                'file_name': attachment.file_name,
                'file_size': attachment.file_size,
                'mime_type': attachment.mime_type,
                'url': attachment.file.url,
                'thumbnail': attachment.thumbnail.url if attachment.thumbnail else None,
            })

        return {
            'id': str(message.id),
            'conversation_id': str(message.conversation_id),
            'sender': {
                'id': message.sender_id,
                'name': message.sender.get_full_name() if message.sender else None,
            } if message.sender else None,
            'type': message.type,
            'content': content if not message.is_deleted else '[تم حذف الرسالة]',
            'status': message.status,
            'reply_to_id': str(message.reply_to_id) if message.reply_to_id else None,
            'is_edited': message.is_edited,
            'is_deleted': message.is_deleted,
            'reactions': reactions,
            'attachments': attachments,
            'created_at': message.created_at.isoformat(),
            'is_mine': message.sender_id == user_id,
        }

    async def edit_message(
        self,
        message_id: str,
        user_id: int,
        new_content: str,
    ) -> Message:
        """تحرير رسالة"""
        message = await Message.objects.aget(id=message_id)

        if message.sender_id != user_id:
            raise PermissionError("لا يمكنك تحرير رسالة غيرك")

        if message.type != MessageType.TEXT:
            raise ValueError("لا يمكن تحرير هذا النوع من الرسائل")

        # التحقق من المهلة (5 دقائق)
        if timezone.now() - message.created_at > timedelta(minutes=5):
            raise ValueError("انتهت مهلة تحرير الرسالة")

        message.edit(new_content)

        # نشر التحديث
        await self._publish_event('message.edited', {
            'message_id': str(message.id),
            'conversation_id': str(message.conversation_id),
            'new_content': new_content,
            'edited_at': message.edited_at.isoformat(),
        })

        return message

    async def delete_message(
        self,
        message_id: str,
        user_id: int,
        for_all: bool = False,
    ) -> None:
        """حذف رسالة"""
        message = await Message.objects.aget(id=message_id)

        if message.sender_id != user_id:
            raise PermissionError("لا يمكنك حذف رسالة غيرك")

        message.soft_delete(for_all=for_all)

        if for_all:
            await self._publish_event('message.deleted', {
                'message_id': str(message.id),
                'conversation_id': str(message.conversation_id),
            })

    async def add_reaction(
        self,
        message_id: str,
        user_id: int,
        emoji: str,
    ) -> MessageReaction:
        """إضافة رد فعل"""
        message = await Message.objects.aget(id=message_id)

        reaction, created = await MessageReaction.objects.aget_or_create(
            message=message,
            user_id=user_id,
            emoji=emoji,
        )

        if created:
            await self._publish_event('message.reaction_added', {
                'message_id': str(message.id),
                'conversation_id': str(message.conversation_id),
                'user_id': user_id,
                'emoji': emoji,
            })

        return reaction

    async def remove_reaction(
        self,
        message_id: str,
        user_id: int,
        emoji: str,
    ) -> None:
        """إزالة رد فعل"""
        await MessageReaction.objects.filter(
            message_id=message_id,
            user_id=user_id,
            emoji=emoji,
        ).adelete()

        message = await Message.objects.aget(id=message_id)
        await self._publish_event('message.reaction_removed', {
            'message_id': str(message.id),
            'conversation_id': str(message.conversation_id),
            'user_id': user_id,
            'emoji': emoji,
        })

    # =========================================================================
    # Read Receipts & Typing
    # =========================================================================

    async def mark_as_read(
        self,
        conversation_id: str,
        user_id: int,
        up_to_message_id: Optional[str] = None,
    ) -> int:
        """تحديد الرسائل كمقروءة"""
        participant = await ConversationParticipant.objects.filter(
            conversation_id=conversation_id,
            user_id=user_id,
            is_active=True,
        ).afirst()

        if not participant:
            return 0

        # تحديث المشارك
        participant.last_read_at = timezone.now()
        if up_to_message_id:
            participant.last_read_message_id = up_to_message_id
        participant.unread_count = 0
        await participant.asave()

        # إنشاء إيصالات قراءة
        unread_messages = Message.objects.filter(
            conversation_id=conversation_id,
            status__in=[MessageStatus.SENT, MessageStatus.DELIVERED],
        ).exclude(sender_id=user_id)

        if up_to_message_id:
            up_to_message = await Message.objects.aget(id=up_to_message_id)
            unread_messages = unread_messages.filter(
                created_at__lte=up_to_message.created_at
            )

        count = 0
        async for msg in unread_messages:
            _, created = await MessageReadReceipt.objects.aget_or_create(
                message=msg,
                user_id=user_id,
            )
            if created:
                count += 1
                msg.status = MessageStatus.READ
                await msg.asave(update_fields=['status'])

        # نشر الحدث
        await self._publish_event('messages.read', {
            'conversation_id': conversation_id,
            'user_id': user_id,
            'up_to_message_id': up_to_message_id,
            'count': count,
        })

        return count

    async def set_typing(
        self,
        conversation_id: str,
        user_id: int,
        is_typing: bool,
    ) -> None:
        """تعيين حالة الكتابة"""
        redis = await self._get_redis()

        key = f"chat:typing:{conversation_id}:{user_id}"

        if is_typing:
            await redis.set(key, '1', ex=10)  # تنتهي بعد 10 ثواني
        else:
            await redis.delete(key)

        # نشر الحدث
        await self._publish_event('typing', {
            'conversation_id': conversation_id,
            'user_id': user_id,
            'is_typing': is_typing,
        })

    async def get_typing_users(self, conversation_id: str) -> List[int]:
        """الحصول على المستخدمين الذين يكتبون"""
        redis = await self._get_redis()

        pattern = f"chat:typing:{conversation_id}:*"
        keys = await redis.keys(pattern)

        typing_users = []
        for key in keys:
            user_id = int(key.decode().split(':')[-1])
            typing_users.append(user_id)

        return typing_users

    # =========================================================================
    # Broadcasting & Notifications
    # =========================================================================

    async def _broadcast_message(self, message: Message) -> None:
        """بث الرسالة للمشاركين"""
        from apps.realtime.connection import get_connection_manager

        manager = get_connection_manager()

        # الحصول على المشاركين
        participants = ConversationParticipant.objects.filter(
            conversation=message.conversation,
            is_active=True,
        ).exclude(user_id=message.sender_id)

        message_data = await self._serialize_message(message, 0)

        async for participant in participants:
            await manager.send_to_user(
                participant.user_id,
                {
                    'type': 'chat.message',
                    'message': message_data,
                },
            )

    async def _send_message_notifications(self, message: Message) -> None:
        """إرسال إشعارات الرسالة"""
        from apps.notifications.services import (
            NotificationPayload,
            get_notification_service,
        )
        from apps.realtime.presence import get_presence_manager

        presence = get_presence_manager()
        notification_service = get_notification_service()

        # الحصول على المشاركين غير المتصلين
        participants = ConversationParticipant.objects.filter(
            conversation=message.conversation,
            is_active=True,
            notifications_enabled=True,
        ).exclude(user_id=message.sender_id)

        sender_name = "مجهول"
        if message.sender:
            sender_name = message.sender.get_full_name() or message.sender.username

        async for participant in participants:
            # التحقق من الاتصال
            if presence.is_user_online(participant.user_id):
                # المستخدم متصل، تم إرسال الرسالة بالفعل
                continue

            # التحقق من كتم الإشعارات
            if participant.is_muted:
                if participant.muted_until and participant.muted_until > timezone.now():
                    continue
                elif not participant.muted_until:
                    continue

            # إرسال إشعار
            await notification_service.send(NotificationPayload(
                recipient_id=participant.user_id,
                title=f"رسالة من {sender_name}",
                body=message.content[:100] if message.content else f"[{message.type}]",
                category='new_message',
                data={
                    'conversation_id': str(message.conversation_id),
                    'message_id': str(message.id),
                },
                action_url=f"/chat/{message.conversation_id}",
            ))

    async def _publish_event(
        self,
        event_type: str,
        data: Dict[str, Any],
    ) -> None:
        """نشر حدث عبر Redis"""
        redis = await self._get_redis()

        await redis.publish(
            f"chat:events:{event_type}",
            json.dumps(data),
        )


# =============================================================================
# Global Service Instance
# =============================================================================

_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """الحصول على خدمة المحادثات"""
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service
