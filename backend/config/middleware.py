from __future__ import annotations

from uuid import uuid4


class RequestContextMiddleware:
    """Attaches a correlation ID. Tenant resolution remains explicit in views."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = request.headers.get("X-Request-ID", str(uuid4()))
        response = self.get_response(request)
        response["X-Request-ID"] = request.request_id
        return response
