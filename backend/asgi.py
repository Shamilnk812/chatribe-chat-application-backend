"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
import django 
django.setup()
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from chat.channels_middleware import JWTwebsocketMiddleware
from django.core.asgi import get_asgi_application
from chat.routing import *


# application = get_asgi_application()


application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket' : JWTwebsocketMiddleware(
        AuthMiddlewareStack(
          URLRouter( websocket_urlpatterns )
        )
    ),
})
