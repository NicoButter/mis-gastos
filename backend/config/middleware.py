from __future__ import annotations

from uuid import uuid4

from django.utils.cache import patch_cache_control, patch_vary_headers


class RequestContextMiddleware:
    """Attaches a correlation ID. Tenant resolution remains explicit in views."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = request.headers.get("X-Request-ID", str(uuid4()))
        response = self.get_response(request)
        response["X-Request-ID"] = request.request_id
        if request.path.startswith(("/api/", "/accounts/", "/admin/")):
            # Includes errors and redirects: neither browser nor shared caches
            # may retain a response across a logout or tenant/session change.
            patch_cache_control(response, private=True, no_store=True, no_cache=True, max_age=0)
            patch_vary_headers(response, ("Cookie",))
        return response
