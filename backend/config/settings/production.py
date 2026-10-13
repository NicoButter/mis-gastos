import os
from pathlib import Path
from urllib.parse import urlparse

from . import base
from .base import *  # noqa: F403

DEBUG = False
if not SECRET_KEY:  # noqa: F405
    raise RuntimeError("DJANGO_SECRET_KEY is required in production.")
if not ALLOWED_HOSTS:  # noqa: F405
    raise RuntimeError("DJANGO_ALLOWED_HOSTS is required in production.")
if any("*" in host or host.startswith(".") for host in base.ALLOWED_HOSTS):
    raise RuntimeError("DJANGO_ALLOWED_HOSTS must contain explicit hosts in production.")


def https_origin(value: str, name: str) -> str:
    parsed = urlparse(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or "*" in value
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise RuntimeError(f"{name} must contain explicit HTTPS origins in production.")
    return value.rstrip("/")


# A missing production URL must never send OAuth users back to localhost.
GASTIO_FRONTEND_URL = https_origin(os.getenv("GASTIO_FRONTEND_URL", ""), "GASTIO_FRONTEND_URL")
if urlparse(GASTIO_FRONTEND_URL).hostname not in base.ALLOWED_HOSTS:
    raise RuntimeError("GASTIO_FRONTEND_URL must use a host in DJANGO_ALLOWED_HOSTS.")
LOGIN_REDIRECT_URL = f"{GASTIO_FRONTEND_URL}/app"
ACCOUNT_LOGOUT_REDIRECT_URL = f"{GASTIO_FRONTEND_URL}/"
# Same-origin Angular does not need CORS or a CSRF trusted-origin exception.
CORS_ALLOWED_ORIGINS = [
    https_origin(value, "CORS_ALLOWED_ORIGINS") for value in base.CORS_ALLOWED_ORIGINS
]
CSRF_TRUSTED_ORIGINS = [
    https_origin(value, "CSRF_TRUSTED_ORIGINS") for value in base.CSRF_TRUSTED_ORIGINS
]


def external_directory(name: str, default: str) -> Path:
    path = Path(os.getenv(name, default))
    if not path.is_absolute() or path.resolve().is_relative_to(base.BASE_DIR.parent.resolve()):
        raise RuntimeError(f"{name} must be an absolute path outside the repository.")
    return path


STATIC_ROOT = external_directory("STATIC_ROOT", "/srv/misgastos/static")
MEDIA_ROOT = external_directory("MEDIA_ROOT", "/srv/misgastos/media")
if STATIC_ROOT.resolve() == MEDIA_ROOT.resolve():
    raise RuntimeError("STATIC_ROOT and MEDIA_ROOT must be separate directories.")

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
