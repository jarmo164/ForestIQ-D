"""Release the request-bound tenant scope after the DRF response is produced."""

from accounts.organization_context import (
    require_organization_scope,
    reset_organization,
    reset_organization_scope_requirement,
)


class OrganizationContextMiddleware:
    """Ensure a JWT-authenticated request cannot leak its organization into another request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        required_token = require_organization_scope()
        try:
            return self.get_response(request)
        finally:
            context_token = getattr(request, "_forestiq_organization_context_token", None)
            if context_token is not None:
                reset_organization(context_token)
            reset_organization_scope_requirement(required_token)
