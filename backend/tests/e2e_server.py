"""Disposable PostgreSQL + real Django sessions; never imported by production URLs."""

import json
import os
import signal
import sys
import threading
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.test"
os.environ["DATABASE_TEST_NAME"] = f"gastio_test_e2e_{uuid4().hex}"

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.core.servers.basehttp import ThreadedWSGIServer, WSGIRequestHandler  # noqa: E402
from django.core.wsgi import get_wsgi_application  # noqa: E402
from django.db import connections  # noqa: E402
from django.test import Client  # noqa: E402
from django.test.utils import setup_databases, teardown_databases  # noqa: E402

from apps.accounts.models import User  # noqa: E402
from apps.categories.services import seed_categories  # noqa: E402
from apps.households.models import Household, HouseholdMembership  # noqa: E402

settings.ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
settings.CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1:4201"]
state_dir = Path(__file__).resolve().parents[2] / "frontend" / "e2e" / ".auth"
state_dir.mkdir(exist_ok=True)
old = setup_databases(verbosity=0, interactive=False)
server = None
server_thread = None
try:
    for name in ["desktop", "mobile360", "mobile390"]:
        user = User.objects.create_user(f"{name}@e2e.invalid")
        household = Household.objects.create(name=f"E2E {name}")
        HouseholdMembership.objects.create(user=user, household=household, role="owner")
        seed_categories(household.pk)
        client = Client()
        client.force_login(user)
        session = client.session
        session["active_household_id"] = str(household.pk)
        session.save()
        state = {
            "cookies": [
                {
                    "name": settings.SESSION_COOKIE_NAME,
                    "value": client.cookies[settings.SESSION_COOKIE_NAME].value,
                    "domain": "127.0.0.1",
                    "path": "/",
                    "expires": -1,
                    "httpOnly": True,
                    "secure": False,
                    "sameSite": "Lax",
                }
            ],
            "origins": [],
        }
        path = state_dir / f"{name}.json"
        path.write_text(json.dumps(state))
        path.chmod(0o600)
    connections.close_all()
    server = ThreadedWSGIServer(("127.0.0.1", 8001), WSGIRequestHandler)
    server.daemon_threads = True
    server.set_app(get_wsgi_application())
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    stopped = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stopped.set())
    signal.signal(signal.SIGINT, lambda *_: stopped.set())
    print("E2E ready: isolated test database, no Google", flush=True)
    stopped.wait()
finally:
    if server:
        server.shutdown()
        server.server_close()
        if server_thread:
            server_thread.join()
    connections.close_all()
    teardown_databases(old, verbosity=0)
    for path in state_dir.glob("*.json"):
        path.unlink()
