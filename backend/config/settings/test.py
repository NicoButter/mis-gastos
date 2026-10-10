from . import base
from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = "test-only-secret"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
CELERY_TASK_ALWAYS_EAGER = True

# Tests still require PostgreSQL. Django creates a separate database.
_test_name = base.os.getenv("DATABASE_TEST_NAME", "gastio_test")
if not _test_name.startswith("gastio_test") or _test_name == base.DATABASES["default"]["NAME"]:
    raise RuntimeError("DATABASE_TEST_NAME debe ser una base aislada con prefijo gastio_test.")
base.DATABASES["default"]["TEST"] = {"NAME": _test_name, "CHARSET": "UTF8", "TEMPLATE": "template0"}
