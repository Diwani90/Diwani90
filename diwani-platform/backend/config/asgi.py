"""
ASGI config for Diwani Platform

يوفر تكوين ASGI لـ:
- HTTP requests (Django)
- WebSocket connections (Channels)
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')

# تهيئة Django أولاً
django_asgi_app = get_asgi_application()

# استيراد routing بعد تهيئة Django
from apps.realtime.routing import websocket_urlpatterns


class JWTAuthMiddleware:
    """
    Middleware للمصادقة عبر JWT في WebSocket

    يستخرج التوكن من:
    - Query string: ?token=xxx
    - Sec-WebSocket-Protocol header
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        from urllib.parse import parse_qs

        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import AnonymousUser

        User = get_user_model()

        # استخراج التوكن
        token = None

        # من query string
        query_string = scope.get('query_string', b'').decode()
        params = parse_qs(query_string)
        if 'token' in params:
            token = params['token'][0]

        # من headers
        if not token:
            headers = dict(scope.get('headers', []))
            protocol_header = headers.get(b'sec-websocket-protocol', b'').decode()
            if protocol_header:
                # Format: "access_token, <token>"
                parts = protocol_header.split(',')
                for part in parts:
                    part = part.strip()
                    if part.startswith('access_token.'):
                        token = part[13:]  # Remove "access_token."
                        break

        # التحقق من التوكن
        user = AnonymousUser()
        if token:
            try:
                from ninja_jwt.tokens import AccessToken

                access_token = AccessToken(token)
                user_id = access_token.get('user_id')
                user = await User.objects.filter(
                    id=user_id,
                    is_active=True,
                ).afirst()
                if not user:
                    user = AnonymousUser()
            except Exception:
                pass

        scope['user'] = user
        return await self.app(scope, receive, send)


application = ProtocolTypeRouter({
    # HTTP -> Django
    "http": django_asgi_app,

    # WebSocket -> Channels
    "websocket": AllowedHostsOriginValidator(
        JWTAuthMiddleware(
            AuthMiddlewareStack(
                URLRouter(websocket_urlpatterns)
            )
        )
    ),
})
