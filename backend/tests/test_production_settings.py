"""Load real production settings in fresh processes with dummy credentials."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]


def run_settings(code, **overrides):
    # Do not inherit DATABASE_URL, OAuth credentials, or other application env.
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "DJANGO_SETTINGS_MODULE": "config.settings.production",
        "DJANGO_SECRET_KEY": "audit-dummy-secret-with-more-than-fifty-characters-1234567890",
        "DJANGO_ALLOWED_HOSTS": "misgastos.vetrabyte.com.ar",
        "GASTIO_FRONTEND_URL": "https://misgastos.vetrabyte.com.ar",
        "DATABASE_URL": "postgresql://audit:dummy@127.0.0.1:1/audit",
        **overrides,
    }
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=BACKEND,
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


def test_production_proxy_oauth_cookies_and_public_routes():
    result = run_settings(
        """
import django
django.setup()
from django.conf import settings
from django.test import Client, RequestFactory
from django.urls import reverse, resolve
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
assert str(settings.STATIC_ROOT) == '/srv/misgastos/static'
assert str(settings.MEDIA_ROOT) == '/srv/misgastos/media'
assert settings.DEBUG is False
assert settings.CORS_ALLOWED_ORIGINS == []
assert settings.LOGIN_REDIRECT_URL == 'https://misgastos.vetrabyte.com.ar/app'
assert settings.ACCOUNT_LOGOUT_REDIRECT_URL == 'https://misgastos.vetrabyte.com.ar/'
assert settings.SECURE_HSTS_INCLUDE_SUBDOMAINS is False
assert settings.SECURE_HSTS_PRELOAD is False
assert settings.SESSION_ENGINE == 'django.contrib.sessions.backends.db'
assert settings.SESSION_COOKIE_HTTPONLY
assert settings.SESSION_COOKIE_SECURE and settings.CSRF_COOKIE_SECURE
assert settings.SESSION_COOKIE_SAMESITE == settings.CSRF_COOKIE_SAMESITE == 'Lax'
assert settings.SESSION_COOKIE_DOMAIN is None and settings.CSRF_COOKIE_DOMAIN is None
assert reverse('google_callback') == '/accounts/google/login/callback/'
request = RequestFactory().get('/', HTTP_HOST='misgastos.vetrabyte.com.ar',
                               HTTP_X_FORWARDED_PROTO='https')
assert request.is_secure()
assert GoogleOAuth2Adapter(request).get_callback_url(request, None) == (
    'https://misgastos.vetrabyte.com.ar/accounts/google/login/callback/')
client = Client(enforce_csrf_checks=True, HTTP_HOST='misgastos.vetrabyte.com.ar')
assert client.get('/api/v1/auth/config/').status_code == 301
response = client.get('/api/v1/auth/config/', HTTP_X_FORWARDED_PROTO='https')
assert response.status_code == 200
assert response.json()['googleLoginEnabled'] is True
assert 'no-store' in response['Cache-Control']
assert 'includeSubDomains' not in response['Strict-Transport-Security']
assert 'preload' not in response['Strict-Transport-Security']
response = client.get('/api/v1/auth/csrf/', HTTP_X_FORWARDED_PROTO='https')
assert response.cookies['csrftoken']['secure']
assert client.post('/accounts/google/login/', HTTP_X_FORWARDED_PROTO='https').status_code == 403
assert client.get('/api/v1/auth/me/', HTTP_X_FORWARDED_PROTO='https').status_code == 403
assert resolve('/api/v1/health/').url_name == 'health'
""",
        GOOGLE_OAUTH_CLIENT_ID="audit-dummy-client",
        GOOGLE_OAUTH_CLIENT_SECRET="audit-dummy-secret",
        DJANGO_DEBUG="true",
    )
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"DJANGO_SECRET_KEY": ""}, "DJANGO_SECRET_KEY"),
        ({"DJANGO_ALLOWED_HOSTS": ""}, "DJANGO_ALLOWED_HOSTS"),
        ({"DJANGO_ALLOWED_HOSTS": "*"}, "explicit hosts"),
        ({"GASTIO_FRONTEND_URL": ""}, "HTTPS origins"),
        ({"GASTIO_FRONTEND_URL": "http://localhost:4200"}, "HTTPS origins"),
        ({"GASTIO_FRONTEND_URL": "https://other.example"}, "DJANGO_ALLOWED_HOSTS"),
        ({"CORS_ALLOWED_ORIGINS": "https://*.example.com"}, "HTTPS origins"),
        ({"CSRF_TRUSTED_ORIGINS": "http://localhost:4200"}, "HTTPS origins"),
        ({"STATIC_ROOT": str(BACKEND / "staticfiles")}, "outside the repository"),
        ({"STATIC_ROOT": "staticfiles"}, "absolute path"),
        ({"MEDIA_ROOT": "/srv/misgastos/static"}, "separate directories"),
        ({"DATABASE_URL": "sqlite:///tmp/audit.db"}, "PostgreSQL"),
    ],
)
def test_production_rejects_unsafe_configuration(overrides, message):
    result = run_settings("import config.settings.production", **overrides)
    assert result.returncode != 0
    assert message in result.stderr


def test_external_static_override_and_development_independence():
    result = run_settings(
        "from django.conf import settings; "
        "assert str(settings.STATIC_ROOT) == '/tmp/misgastos-static-audit'",
        STATIC_ROOT="/tmp/misgastos-static-audit",
    )
    assert result.returncode == 0, result.stderr
    result = run_settings(
        "from django.conf import settings; "
        "assert settings.DEBUG; "
        "assert settings.STATIC_ROOT == settings.BASE_DIR / 'staticfiles'; "
        "assert not settings.SESSION_COOKIE_SECURE; "
        "assert settings.SECURE_PROXY_SSL_HEADER is None; "
        "assert settings.GASTIO_FRONTEND_URL == 'http://localhost:4200'",
        DJANGO_SETTINGS_MODULE="config.settings.development",
        GASTIO_FRONTEND_URL="http://localhost:4200",
    )
    assert result.returncode == 0, result.stderr
