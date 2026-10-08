"""Allauth policies specific to Gastio's Google-only browser login."""

from urllib.parse import urlencode

from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.http import HttpResponseRedirect

from .models import User


class GastioSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Avoid silently connecting a Google identity merely by matching email."""

    @staticmethod
    def _login_error(code: str) -> HttpResponseRedirect:
        query = urlencode({"error": code})
        return HttpResponseRedirect(f"{settings.GASTIO_FRONTEND_URL}/login?{query}")

    def pre_social_login(self, request, sociallogin) -> None:
        if sociallogin.is_existing:
            return
        email = (sociallogin.user.email or "").strip()
        if email and User.objects.filter(email__iexact=email).exists():
            raise ImmediateHttpResponse(self._login_error("account_link_required"))

    def on_authentication_error(
        self, request, provider, error=None, exception=None, extra_context=None
    ) -> None:
        # Do not send provider failure details, state values, or exception data
        # to the browser. A user can safely retry from the login page.
        raise ImmediateHttpResponse(self._login_error("oauth_failed"))
