"""WebSocket URL routing for the live app."""
from django.urls import re_path
from .consumers import LiveConsumer

# ws://host/ws/live/<uuid>/
websocket_urlpatterns = [
    re_path(
        r'^ws/live/(?P<stream_uuid>[0-9a-f\-]+)/$',
        LiveConsumer.as_asgi(),
    ),
]
