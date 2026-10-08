from .base import *  # noqa: F403

DEBUG = False
if not SECRET_KEY:  # noqa: F405
    raise RuntimeError("DJANGO_SECRET_KEY is required in production.")
if not ALLOWED_HOSTS:  # noqa: F405
    raise RuntimeError("DJANGO_ALLOWED_HOSTS is required in production.")
if not CORS_ALLOWED_ORIGINS:  # noqa: F405
    raise RuntimeError("CORS_ALLOWED_ORIGINS is required in production.")
if "*" in CORS_ALLOWED_ORIGINS:  # noqa: F405
    raise RuntimeError("CORS_ALLOWED_ORIGINS cannot contain a wildcard in production.")
if "*" in CSRF_TRUSTED_ORIGINS:  # noqa: F405
    raise RuntimeError("CSRF_TRUSTED_ORIGINS cannot contain a wildcard in production.")

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
