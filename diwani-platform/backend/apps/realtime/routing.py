"""
توجيه WebSocket
================

يحدد مسارات WebSocket للتطبيقات المختلفة
"""

from django.urls import path, re_path

from .consumers import ChatConsumer, MainConsumer, TrackingConsumer

websocket_urlpatterns = [
    # الاتصال الرئيسي
    path('ws/', MainConsumer.as_asgi()),
    path('ws/main/', MainConsumer.as_asgi()),

    # المحادثات
    path('ws/chat/', ChatConsumer.as_asgi()),
    re_path(r'ws/chat/(?P<conversation_id>[^/]+)/$', ChatConsumer.as_asgi()),

    # التتبع
    path('ws/tracking/', TrackingConsumer.as_asgi()),
    re_path(r'ws/tracking/(?P<delivery_id>[^/]+)/$', TrackingConsumer.as_asgi()),
]
