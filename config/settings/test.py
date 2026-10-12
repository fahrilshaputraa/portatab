"""Test settings.

Optimised for speed: a fast password hasher and in-memory email backend. The
database is created and destroyed by Django's test runner / pytest-django.
"""

from .dev import *  # noqa: F403

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Keep external payment calls out of the test suite. Tests that exercise the
# Midtrans adapter inject a stub client instead.
MIDTRANS_SERVER_KEY = "test-server-key"

# Deterministic timers used by cashier-response tests.
ORDER_WARNING_SECONDS = 180
ORDER_LATE_SECONDS = 300
