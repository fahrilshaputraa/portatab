"""Base Django settings for PortaTap.

PortaTap is a multi-tenant SaaS platform for F&B businesses. This module holds the
settings shared by every environment. Environment-specific overrides live in
``dev.py`` and ``prod.py``.

Approved stack (see docs/ARCHITECTURE.md):
    backend  -> Django, Django Templates, Django ORM, Django Forms
    frontend -> Django Templates + HTMX + Tailwind CSS + selective vanilla JS
    database -> PostgreSQL
"""

from decimal import Decimal
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, []),
    DJANGO_CSRF_TRUSTED_ORIGINS=(list, []),
    DATABASE_URL=(str, "postgres://portatap:portatap@127.0.0.1:5432/portatap"),
    EMAIL_URL=(str, "consolemail://"),
)

# Read a .env file when present so local development needs no exported variables.
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="django-insecure-dev-only-change-me")
DEBUG = env("DJANGO_DEBUG")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env("DJANGO_CSRF_TRUSTED_ORIGINS")


# Application definition

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

LOCAL_APPS = [
    "apps.core",
    "apps.accounts",
    "apps.tenants",
    "apps.customers",
    "apps.catalog",
    "apps.tables",
    "apps.orders",
    "apps.payments",
    "apps.inventory",
    "apps.notifications",
    "apps.promotions",
    "apps.subscriptions",
    "apps.themes",
    "apps.reports",
    "apps.platform_admin",
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Resolves the active tenant/branch context from the authenticated user's
    # membership and exposes it on the request. Authorization still happens
    # per-view; this only provides convenient, already-scoped context.
    "apps.tenants.middleware.TenantContextMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.tenants.context_processors.tenant_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# Database
# https://docs.djangoproject.com/en/6.1/ref/settings/#databases

DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DATABASE_CONN_MAX_AGE", default=60)
DATABASES["default"]["ATOMIC_REQUESTS"] = False


# Authentication

AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = ["apps.accounts.backends.EmailOrUsernameBackend"]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "tenants:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = False  # HTMX reads the token from the cookie to set the header.


# Internationalization
# https://docs.djangoproject.com/en/6.1/topics/i18n/

LANGUAGE_CODE = "id"
TIME_ZONE = "Asia/Jakarta"
USE_I18N = True
USE_TZ = True


# Static and media files

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email (console backend by default; override with EMAIL_URL per environment).
EMAIL_CONFIG = env.email_url("EMAIL_URL")
vars().update(EMAIL_CONFIG)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="PortaTap <no-reply@portatap.local>")


# ---------------------------------------------------------------------------
# PortaTap domain configuration
# ---------------------------------------------------------------------------

# Money is stored as numeric(14, 2) and handled with Decimal everywhere.
# Binary floating point is never used for authoritative money arithmetic.
CURRENCY_CODE = env("CURRENCY_CODE", default="IDR")
MONEY_DECIMAL_PLACES = 2
MONEY_MAX_DIGITS = 14

# Cashier response timers (server-side clock is authoritative).
ORDER_WARNING_SECONDS = env.int("ORDER_WARNING_SECONDS", default=180)  # 3 minutes
ORDER_LATE_SECONDS = env.int("ORDER_LATE_SECONDS", default=300)  # 5 minutes

# Digital payment attempt expiry. Final value depends on the selected provider.
PAYMENT_EXPIRY_MINUTES = env.int("PAYMENT_EXPIRY_MINUTES", default=15)

# Stock reservation lifetime for orders still awaiting a cashier decision.
STOCK_RESERVATION_TTL_MINUTES = env.int("STOCK_RESERVATION_TTL_MINUTES", default=30)

# Refunds at or below this amount may be processed by a cashier without manager
# approval. This is an approved business policy and must be reviewed before
# production (see docs/BUSINESS-RULES.md section 10).
REFUND_CASHIER_MAX_AMOUNT = Decimal(env("REFUND_CASHIER_MAX_AMOUNT", default="100000"))

# Subscription trial length for new tenants.
SUBSCRIPTION_TRIAL_DAYS = env.int("SUBSCRIPTION_TRIAL_DAYS", default=14)

# Uploads
MAX_UPLOAD_SIZE_BYTES = env.int("MAX_UPLOAD_SIZE_BYTES", default=5 * 1024 * 1024)
ALLOWED_IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]


# ---------------------------------------------------------------------------
# Payment provider: Midtrans (Snap)
# ---------------------------------------------------------------------------

MIDTRANS_SERVER_KEY = env("MIDTRANS_SERVER_KEY", default="")
MIDTRANS_CLIENT_KEY = env("MIDTRANS_CLIENT_KEY", default="")
MIDTRANS_IS_PRODUCTION = env.bool("MIDTRANS_IS_PRODUCTION", default=False)
MIDTRANS_SNAP_BASE_URL = env(
    "MIDTRANS_SNAP_BASE_URL",
    default="https://app.sandbox.midtrans.com/snap/v1",
)
MIDTRANS_API_BASE_URL = env(
    "MIDTRANS_API_BASE_URL",
    default="https://api.sandbox.midtrans.com/v2",
)
MIDTRANS_TIMEOUT_SECONDS = env.int("MIDTRANS_TIMEOUT_SECONDS", default=15)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "structured": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "structured"},
    },
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO")},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "portatap": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}
