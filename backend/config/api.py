from __future__ import annotations

from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    """A stable error envelope that omits request payloads and tenant data."""
    response = drf_exception_handler(exc, context)
    if response is None:
        return response
    request = context.get("request")
    fields = response.data if isinstance(response.data, dict) else None
    code = "VALIDATION_ERROR" if response.status_code == 400 else "API_ERROR"
    if response.status_code == 401:
        code = "AUTHENTICATION_REQUIRED"
    elif response.status_code == 403:
        code = "PERMISSION_DENIED"
    elif response.status_code == 404:
        code = "NOT_FOUND"
    elif response.status_code == 409:
        code = "CONFLICT"
    response.data = {
        "error": {
            "code": code,
            "message": (
                "Solicitud no válida"
                if code == "VALIDATION_ERROR"
                else "No se pudo procesar la solicitud"
            ),
            "fields": fields if code == "VALIDATION_ERROR" else None,
            "request_id": getattr(request, "request_id", None),
        }
    }
    return response
