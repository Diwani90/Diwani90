"""
نماذج نظام المحادثات
======================

يوفر:
- محادثات فردية وجماعية
- رسائل مع أنواع متعددة
- مرفقات وسائط
- ردود الفعل
- تشفير المحتوى
"""

import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class ConversationType(models.TextChoices):
    """أنواع المحادثات"""

    DIRECT = 'direct', 'محادثة مباشرة'
    GROUP = 'group', 'مجموعة'
    SUPPORT = 'support', 'دعم فني'
    ORDER = 'order', 'محادثة طلب'


class MessageType(models.TextChoices):
    """أنواع الرسائل"""

    TEXT = 'text', 'نص'
    IMAGE = 'image', 'صورة'
    VIDEO = 'video', 'فيديو'
    AUDIO = 'audio', 'صوت'
    FILE = 'file', 'ملف'
    LOCATION = 'location', 'موقع'
    CONTACT = 'contact', 'جهة اتصال'
    SYSTEM = 'system', 'رسالة نظام'
    PRODUCT = 'product', 'منتج'
    ORDER = 'order', 'طلب'


class MessageStatus(models.TextChoices):
    """حالات الرسالة"""

    PENDING = 'pending', 'قيد الإرسال'
    SENT = 'sent', 'تم الإرسال'
    DELIVERED = 'delivered', 'تم التوصيل'
    READ = 'read', 'تمت القراءة'
    FAILED = 'failed', 'فشل'
    DELETED = 'deleted', 'محذوفة'


class ParticipantRole(models.TextChoices):
    """أدوار المشاركين"""

    MEMBER = 'member', 'عضو'
    ADMIN = 'admin', 'مدير'
    OWNER = 'owner', 'المالك'
    SUPPORT = 'support', 'دعم'


class Conversation(models.Model):
    """
    المحادثة

    تمثل محادثة بين مستخدمين أو مجموعة
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # النوع
    type = models.CharField(
        max_length=20,
        choices=ConversationType.choices,
        default=ConversationType.DIRECT,
        verbose_name='النوع',
    )

    # معلومات المجموعة (للمجموعات فقط)
    name = models.CharField(max_length=100, blank=True, verbose_name='اسم المحادثة')
    description = models.TextField(blank=True, verbose_name='الوصف')
    avatar = models.ImageField(
        upload_to='chat/avatars/',
        blank=True,
        null=True,
        verbose_name='الصورة',
    )

    # الإعدادات
    is_encrypted = models.BooleanField(default=True, verbose_name='مشفرة')
    allow_media = models.BooleanField(default=True, verbose_name='السماح بالوسائط')
    allow_links = models.BooleanField(default=True, verbose_name='السماح بالروابط')
    max_participants = models.IntegerField(default=100, verbose_name='الحد الأقصى للمشاركين')

    # ربط بكيانات (اختياري)
    order_id = models.IntegerField(null=True, blank=True, verbose_name='معرف الطلب')
    store_id = models.IntegerField(null=True, blank=True, verbose_name='معرف المتجر')

    # الحالة
    is_active = models.BooleanField(default=True, verbose_name='نشطة')
    is_archived = models.BooleanField(default=False, verbose_name='مؤرشفة')

    # التوقيت
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='وقت الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='وقت التحديث')
    last_message_at = models.DateTimeField(null=True, blank=True, verbose_name='آخر رسالة')

    # البيانات الوصفية
    metadata = models.JSONField(default=dict, verbose_name='بيانات إضافية')

    class Meta:
        db_table = 'chat_conversations'
        verbose_name = 'محادثة'
        verbose_name_plural = 'المحادثات'
        ordering = ['-last_message_at', '-created_at']
        indexes = [
            models.Index(fields=['-last_message_at']),
            models.Index(fields=['type', '-created_at']),
            models.Index(fields=['order_id']),
        ]

    def __str__(self):
        return self.name or f"محادثة {self.id}"

    @property
    def participants_count(self) -> int:
        """عدد المشاركين"""
        return self.participants.filter(is_active=True).count()


class ConversationParticipant(models.Model):
    """
    مشارك في محادثة
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name='المحادثة',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_participations',
        verbose_name='المستخدم',
    )

    # الدور
    role = models.CharField(
        max_length=20,
        choices=ParticipantRole.choices,
        default=ParticipantRole.MEMBER,
        verbose_name='الدور',
    )

    # الإعدادات
    notifications_enabled = models.BooleanField(default=True, verbose_name='الإشعارات مفعلة')
    is_muted = models.BooleanField(default=False, verbose_name='مكتوم')
    muted_until = models.DateTimeField(null=True, blank=True, verbose_name='مكتوم حتى')

    # التتبع
    last_read_at = models.DateTimeField(null=True, blank=True, verbose_name='آخر قراءة')
    last_read_message_id = models.UUIDField(null=True, blank=True, verbose_name='آخر رسالة مقروءة')
    unread_count = models.IntegerField(default=0, verbose_name='عدد غير المقروءة')

    # الحالة
    is_active = models.BooleanField(default=True, verbose_name='نشط')
    joined_at = models.DateTimeField(auto_now_add=True, verbose_name='وقت الانضمام')
    left_at = models.DateTimeField(null=True, blank=True, verbose_name='وقت المغادرة')

    # للتشفير
    encryption_key_id = models.CharField(max_length=100, blank=True, verbose_name='معرف مفتاح التشفير')

    class Meta:
        db_table = 'chat_participants'
        verbose_name = 'مشارك'
        verbose_name_plural = 'المشاركون'
        unique_together = [['conversation', 'user']]
        indexes = [
            models.Index(fields=['user', '-joined_at']),
            models.Index(fields=['conversation', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user} في {self.conversation}"

    def mark_as_read(self, message_id: uuid.UUID = None):
        """تحديد كمقروء"""
        self.last_read_at = timezone.now()
        if message_id:
            self.last_read_message_id = message_id
        self.unread_count = 0
        self.save(update_fields=['last_read_at', 'last_read_message_id', 'unread_count'])


class Message(models.Model):
    """
    الرسالة

    تمثل رسالة واحدة في محادثة
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # المحادثة
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='المحادثة',
    )

    # المرسل
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_messages',
        verbose_name='المرسل',
    )

    # النوع والمحتوى
    type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT,
        verbose_name='النوع',
    )
    content = models.TextField(blank=True, verbose_name='المحتوى')
    content_encrypted = models.BinaryField(null=True, blank=True, verbose_name='المحتوى المشفر')

    # الحالة
    status = models.CharField(
        max_length=20,
        choices=MessageStatus.choices,
        default=MessageStatus.PENDING,
        verbose_name='الحالة',
    )

    # الرد على رسالة
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name='رد على',
    )

    # إعادة التوجيه
    forwarded_from = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='forwards',
        verbose_name='معاد توجيهها من',
    )

    # الإشارات (@mentions)
    mentions = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='mentioned_in_messages',
        verbose_name='الإشارات',
    )

    # التحرير
    is_edited = models.BooleanField(default=False, verbose_name='محررة')
    edited_at = models.DateTimeField(null=True, blank=True, verbose_name='وقت التحرير')
    edit_history = models.JSONField(default=list, verbose_name='سجل التحرير')

    # الحذف
    is_deleted = models.BooleanField(default=False, verbose_name='محذوفة')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='وقت الحذف')
    deleted_for_all = models.BooleanField(default=False, verbose_name='محذوفة للجميع')

    # البيانات الإضافية
    metadata = models.JSONField(default=dict, verbose_name='بيانات إضافية')

    # التوقيت
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='وقت الإرسال')
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name='وقت التوصيل')

    # معرف العميل (للتكرار)
    client_message_id = models.CharField(max_length=100, blank=True, verbose_name='معرف العميل')

    class Meta:
        db_table = 'chat_messages'
        verbose_name = 'رسالة'
        verbose_name_plural = 'الرسائل'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['sender', '-created_at']),
            models.Index(fields=['client_message_id']),
        ]

    def __str__(self):
        return f"{self.sender} - {self.content[:50] if self.content else self.type}"

    def mark_delivered(self):
        """تحديد كموصلة"""
        if self.status == MessageStatus.SENT:
            self.status = MessageStatus.DELIVERED
            self.delivered_at = timezone.now()
            self.save(update_fields=['status', 'delivered_at'])

    def mark_read(self):
        """تحديد كمقروءة"""
        if self.status in [MessageStatus.SENT, MessageStatus.DELIVERED]:
            self.status = MessageStatus.READ
            self.save(update_fields=['status'])

    def edit(self, new_content: str):
        """تحرير الرسالة"""
        if self.content:
            self.edit_history.append({
                'content': self.content,
                'edited_at': timezone.now().isoformat(),
            })

        self.content = new_content
        self.is_edited = True
        self.edited_at = timezone.now()
        self.save(update_fields=['content', 'is_edited', 'edited_at', 'edit_history'])

    def soft_delete(self, for_all: bool = False):
        """حذف ناعم"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_for_all = for_all
        if for_all:
            self.content = ''
            self.content_encrypted = None
        self.save()


class MessageAttachment(models.Model):
    """
    مرفقات الرسالة
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name='الرسالة',
    )

    # الملف
    file = models.FileField(upload_to='chat/attachments/%Y/%m/', verbose_name='الملف')
    file_name = models.CharField(max_length=255, verbose_name='اسم الملف')
    file_size = models.BigIntegerField(verbose_name='حجم الملف')
    mime_type = models.CharField(max_length=100, verbose_name='نوع الملف')

    # للصور والفيديو
    width = models.IntegerField(null=True, blank=True, verbose_name='العرض')
    height = models.IntegerField(null=True, blank=True, verbose_name='الارتفاع')
    duration = models.FloatField(null=True, blank=True, verbose_name='المدة')
    thumbnail = models.ImageField(
        upload_to='chat/thumbnails/',
        null=True,
        blank=True,
        verbose_name='الصورة المصغرة',
    )

    # التشفير
    is_encrypted = models.BooleanField(default=True, verbose_name='مشفر')
    encryption_key_id = models.CharField(max_length=100, blank=True, verbose_name='معرف مفتاح التشفير')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_attachments'
        verbose_name = 'مرفق'
        verbose_name_plural = 'المرفقات'

    def __str__(self):
        return self.file_name


class MessageReaction(models.Model):
    """
    ردود الفعل على الرسائل
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='reactions',
        verbose_name='الرسالة',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='message_reactions',
        verbose_name='المستخدم',
    )

    # رد الفعل
    emoji = models.CharField(max_length=10, verbose_name='الإيموجي')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_reactions'
        verbose_name = 'رد فعل'
        verbose_name_plural = 'ردود الفعل'
        unique_together = [['message', 'user', 'emoji']]

    def __str__(self):
        return f"{self.user} - {self.emoji}"


class MessageReadReceipt(models.Model):
    """
    إيصالات القراءة
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='read_receipts',
        verbose_name='الرسالة',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='read_receipts',
        verbose_name='المستخدم',
    )

    read_at = models.DateTimeField(auto_now_add=True, verbose_name='وقت القراءة')

    class Meta:
        db_table = 'chat_read_receipts'
        verbose_name = 'إيصال قراءة'
        verbose_name_plural = 'إيصالات القراءة'
        unique_together = [['message', 'user']]

    def __str__(self):
        return f"{self.user} قرأ {self.message_id}"


class TypingIndicator(models.Model):
    """
    مؤشرات الكتابة

    يتم تخزينها في Redis عادةً، لكن نحتفظ بنموذج للرجوع إليه
    """

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='typing_indicators',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    started_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_typing_indicators'
        unique_together = [['conversation', 'user']]
