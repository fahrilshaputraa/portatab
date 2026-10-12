"""Development settings.

Local development only. Never use these values in production.
"""

from .base import *  # noqa: F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    *CSRF_TRUSTED_ORIGINS,  # noqa: F405
]

# Make the dev experience forgiving: plain-text passwords are hashed with a fast
# algorithm so test fixtures and seed data stay quick to create.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.PBKDF2PasswordHasher"]

# Serve static files directly in development instead of requiring a collectstatic
# manifest (production keeps the hashed manifest storage from base.py).
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

INTERNAL_IPS = ["127.0.0.1"]
