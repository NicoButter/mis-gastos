"""Celery wiring only; financial tasks belong to later approved phases."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("gastio")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
