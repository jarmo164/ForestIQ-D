"""Request- and task-bound organization context for tenant-scoped business queries."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Iterator
from uuid import UUID

from django.db import models


_organization_id: ContextVar[UUID | None] = ContextVar("forestiq_organization_id", default=None)
_organization_scope_required: ContextVar[bool] = ContextVar("forestiq_organization_scope_required", default=False)


def current_organization_id() -> UUID | None:
    """Return the current API or task organization, if a trusted boundary set one."""

    return _organization_id.get()


def activate_organization(organization_id: UUID | str) -> Token:
    """Activate a verified organization and return the token required for cleanup."""

    return _organization_id.set(UUID(str(organization_id)))


def reset_organization(token: Token) -> None:
    """Clear a previously activated organization context."""

    _organization_id.reset(token)


def require_organization_scope() -> Token:
    """Make organization-scoped managers fail closed until an organization is activated."""

    return _organization_scope_required.set(True)


def reset_organization_scope_requirement(token: Token) -> None:
    """Restore the caller's previous scope-enforcement state."""

    _organization_scope_required.reset(token)


@contextmanager
def organization_scope(organization_id: UUID | str) -> Iterator[None]:
    """Scope trusted worker/command code to one explicit organization."""

    required_token = require_organization_scope()
    token = activate_organization(organization_id)
    try:
        yield
    finally:
        reset_organization(token)
        reset_organization_scope_requirement(required_token)


class OrganizationScopedManager(models.Manager):
    """Filter every business-model queryset when an API or task context is active."""

    def get_queryset(self):
        queryset = super().get_queryset()
        organization_id = current_organization_id()
        if organization_id:
            return queryset.filter(organization_id=organization_id)
        return queryset.none() if _organization_scope_required.get() else queryset
