"""
إشارات نظام الإشعارات
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


# يتم تسجيل الإشارات الفعلية في تطبيقات أخرى
# مثل orders, chat, etc.
