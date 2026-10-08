from django.conf import settings


def test_postgresql_and_tenant_safety_baseline_are_configured():
    assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"
    assert settings.AUTH_USER_MODEL == "accounts.User"
    assert settings.REST_FRAMEWORK["DEFAULT_PAGINATION_CLASS"].endswith("CursorPagination")
