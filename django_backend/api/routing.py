from django.urls import path

from .realtime import OrganizationEventConsumer

websocket_urlpatterns = [
    path("ws/events/", OrganizationEventConsumer.as_asgi()),
]
