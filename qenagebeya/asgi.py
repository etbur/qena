"""
ASGI config for Qenagebeya.

Handles both HTTP (Django views) and WebSocket (Channels).
Run with:  python manage.py runserver   (daphne is first in INSTALLED_APPS)
       OR: python -m daphne -p 8000 qenagebeya.asgi:application
"""
import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qenagebeya.settings')

# Must call django.setup() before importing channels or consumers
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from live.routing import websocket_urlpatterns

django_asgi_app = get_asgi_application()

# In development skip origin validation; in production wrap with AllowedHostsOriginValidator
from django.conf import settings as _settings

_ws_stack = AuthMiddlewareStack(URLRouter(websocket_urlpatterns))

if not _settings.DEBUG:
    from channels.security.websocket import AllowedHostsOriginValidator
    _ws_stack = AllowedHostsOriginValidator(_ws_stack)

application = ProtocolTypeRouter({
    'http':      django_asgi_app,
    'websocket': _ws_stack,
})
