from django.conf import settings

from config.settings.base import database_from_env


def test_postgresql_and_tenant_safety_baseline_are_configured():
    assert settings.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"
    assert settings.AUTH_USER_MODEL == "accounts.User"
    assert settings.REST_FRAMEWORK["DEFAULT_PAGINATION_CLASS"].endswith("CursorPagination")


def test_database_url_accepts_a_postgresql_unix_socket_host(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://gastio_phase0_test@localhost/postgres?host=/tmp/gastio-pg&port=55439",
    )

    database = database_from_env()

    assert database["ENGINE"] == "django.db.backends.postgresql"
    assert database["HOST"] == "/tmp/gastio-pg"
    assert database["PORT"] == "55439"


def test_database_url_rejects_non_postgresql_engines(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///tmp/gastio.db")

    try:
        database_from_env()
    except RuntimeError as exc:
        assert "PostgreSQL" in str(exc)
    else:
        raise AssertionError("SQLite must not be accepted")
