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


def test_database_url_decodes_credentials_and_preserves_connection_options(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://audit%40user:p%40ss%3Aword@localhost/audit%2Ddb"
        "?sslmode=verify-full&sslrootcert=/tmp/audit-ca.pem&connect_timeout=5",
    )
    database = database_from_env()
    assert database["USER"] == "audit@user"
    assert database["PASSWORD"] == "p@ss:word"
    assert database["NAME"] == "audit-db"
    assert database["OPTIONS"] == {
        "sslmode": "verify-full",
        "sslrootcert": "/tmp/audit-ca.pem",
        "connect_timeout": "5",
    }


def test_financial_test_configuration_rejects_real_database_names():
    import os
    import subprocess
    import sys
    from pathlib import Path

    backend = Path(__file__).resolve().parents[1]
    for name in ["gastio_db", "postgres", ""]:
        result = subprocess.run(
            [sys.executable, "-c", "import config.settings.test"],
            cwd=backend,
            env={**os.environ, "DATABASE_TEST_NAME": name},
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode != 0
        assert "base aislada" in result.stderr
