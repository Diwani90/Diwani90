"""
نظام Real-time المتقدم لمنصة ديواني
=====================================

بنية تحتية متقدمة للاتصالات الفورية تشمل:
- WebSockets مع Django Channels
- Event Sourcing و CQRS
- Connection Management المتقدم
- Presence System للمستخدمين المتصلين
- Rate Limiting و Backpressure

التقنيات المستخدمة:
- Django Channels 4.x
- Redis Pub/Sub و Streams
- Protocol Buffers للرسائل
- AsyncIO للمعالجة غير المتزامنة
"""

default_app_config = 'apps.realtime.apps.RealtimeConfig'

__version__ = '1.0.0'
__author__ = 'Diwani Platform'
