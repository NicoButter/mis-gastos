from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig


class PlatformAdminSite(AdminSite):
    """The global admin is for trusted platform operators, never tenant staff."""

    def has_permission(self, request):
        return super().has_permission(request) and request.user.is_superuser


class PlatformAdminConfig(AdminConfig):
    default_site = "config.admin.PlatformAdminSite"
