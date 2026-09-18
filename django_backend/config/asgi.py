"""ASGI entrypoint for HTTP and authenticated ForestIQ websocket events."""
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

django_asgi_application = get_asgi_application()

from api.realtime import ForestIQJWTAuthMiddleware
from api.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": django_asgi_application,
    "websocket": ForestIQJWTAuthMiddleware(URLRouter(websocket_urlpatterns)),
})
