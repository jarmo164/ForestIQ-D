"""ASGI websocket authentication and organization-scoped event consumer."""
from __future__ import annotations

from urllib.parse import parse_qs
from uuid import UUID

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import OrganizationMembership, User
from operations.realtime import organization_group, user_group


@database_sync_to_async
def _authenticated_scope(raw_token: str):
    try:
        token = AccessToken(raw_token)
        user_id = str(token.get("userId") or token.get("user_id") or "")
        organization_id = UUID(str(token.get("organization_id") or token.get("organizationId") or ""))
        user = User.objects.get(id=user_id, is_active=True)
        membership = OrganizationMembership.objects.select_related("organization").get(
            user=user,
            organization_id=organization_id,
            organization__is_active=True,
        )
        return user, membership
    except (TokenError, ValueError, TypeError, User.DoesNotExist, OrganizationMembership.DoesNotExist):
        return AnonymousUser(), None


class ForestIQJWTAuthMiddleware:
    """Bind a websocket to exactly one active membership from the internal JWT."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get("query_string", b"").decode())
        token = (query.get("token") or [""])[0]
        user, membership = await _authenticated_scope(token)
        scope = dict(scope)
        scope["user"] = user
        scope["organization_membership"] = membership
        scope["organization_id"] = getattr(membership, "organization_id", None)
        return await self.app(scope, receive, send)


class OrganizationEventConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        membership = self.scope.get("organization_membership")
        user = self.scope.get("user")
        if membership is None or not getattr(user, "is_authenticated", False):
            await self.close(code=4401)
            return
        self.organization_group = organization_group(membership.organization_id)
        self.user_group = user_group(membership.organization_id, user.id)
        await self.channel_layer.group_add(self.organization_group, self.channel_name)
        await self.channel_layer.group_add(self.user_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "organization_group"):
            await self.channel_layer.group_discard(self.organization_group, self.channel_name)
        if hasattr(self, "user_group"):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # No client-selected topic subscriptions are accepted. Membership determines both groups.
        if content.get("type") == "ping":
            await self.send_json({"type": "pong"})

    async def forestiq_event(self, event):
        await self.send_json(event["event"])
