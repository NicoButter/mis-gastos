from . import base
from .base import *  # noqa: F403

DEBUG = False
SECRET_KEY = "test-only-secret"
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
CELERY_TASK_ALWAYS_EAGER = True

# Tests still require PostgreSQL. Django creates a separate database.
base.DATABASES["default"]["TEST"] = {"NAME": base.os.getenv("DATABASE_TEST_NAME", "gastio_test")}
