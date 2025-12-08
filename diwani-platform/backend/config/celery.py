"""
Celery Configuration for Diwani Platform
========================================

Celery هو نظام قوائم المهام الموزعة
يستخدم لتنفيذ المهام في الخلفية مثل:
- إرسال الإشعارات
- معالجة الصور
- مزامنة البيانات
- المهام المجدولة
"""

import os
from celery import Celery

# تعيين إعدادات Django الافتراضية
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

# إنشاء تطبيق Celery
app = Celery('diwani')

# قراءة الإعدادات من Django settings
# namespace='CELERY' يعني أن كل إعدادات Celery تبدأ بـ CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# البحث عن المهام تلقائياً في جميع التطبيقات المسجلة
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """مهمة للاختبار والتصحيح"""
    print(f'Request: {self.request!r}')
