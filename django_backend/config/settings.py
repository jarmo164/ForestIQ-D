"""ForestIQ Django service settings."""

import os
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-development-key-change-before-production")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = [host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_q",
    "accounts",
    "forestry",
    "operations",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


def database_from_environment() -> dict:
    """Return PostgreSQL configuration, with an explicit SQLite escape hatch for unit tests."""
    if env_bool("USE_SQLITE_FOR_TESTS", False):
        return {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        parsed = urlparse(database_url)
        if parsed.scheme not in {"postgres", "postgresql"}:
            raise ValueError("DATABASE_URL must use the postgres or postgresql scheme")
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed.path.lstrip("/"),
            "USER": parsed.username,
            "PASSWORD": parsed.password,
            "HOST": parsed.hostname,
            "PORT": parsed.port or 5432,
            "CONN_MAX_AGE": 60,
        }

    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "forestiq"),
        "USER": os.getenv("POSTGRES_USER", "forestiq"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "forestiq"),
        "HOST": os.getenv("POSTGRES_HOST", "db"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }


DATABASES = {"default": database_from_environment()}

AUTH_USER_MODEL = "accounts.User"
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "accounts.hashers.LegacyBCryptPasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated"],
    "EXCEPTION_HANDLER": "api.exceptions.api_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_ACCESS_MINUTES", "200"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("JWT_REFRESH_MINUTES", "60"))),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

TOTP_TOKEN_LIFETIME_SECONDS = int(os.getenv("TOTP_TOKEN_LIFETIME_SECONDS", "180"))
FORESTIQ_DEVMODE = env_bool("FORESTIQ_DEVMODE", DEBUG)

# Django Q2 uses PostgreSQL through Django's database connection. The ORM broker
# avoids an additional queue service and keeps task history in the same backup scope.
Q_CLUSTER = {
    "name": "forestiq-sync",
    "workers": int(os.getenv("DJANGO_Q_WORKERS", "2")),
    "recycle": int(os.getenv("DJANGO_Q_RECYCLE", "500")),
    "timeout": int(os.getenv("DJANGO_Q_TIMEOUT_SECONDS", "300")),
    "retry": int(os.getenv("DJANGO_Q_RETRY_SECONDS", "360")),
    "queue_limit": int(os.getenv("DJANGO_Q_QUEUE_LIMIT", "100")),
    "bulk": int(os.getenv("DJANGO_Q_BULK", "5")),
    "orm": "default",
    "save_limit": int(os.getenv("DJANGO_Q_SAVE_LIMIT", "500")),
}
FORESTIQ_Q_SYNC_INLINE = env_bool("FORESTIQ_Q_SYNC_INLINE", False)
FORESTIQ_SYNC_HTTP_TIMEOUT_SECONDS = int(os.getenv("FORESTIQ_SYNC_HTTP_TIMEOUT_SECONDS", "30"))
FORESTIQ_SYNC_USER_AGENT = os.getenv("FORESTIQ_SYNC_USER_AGENT", "ForestIQ data synchronizer/1.0")

FORESTIQ_CADASTRE_WFS_URL = os.getenv(
    "FORESTIQ_CADASTRE_WFS_URL",
    "https://gsavalik.envir.ee/geoserver/kataster/wfs",
)
FORESTIQ_CADASTRE_WFS_LAYER = os.getenv("FORESTIQ_CADASTRE_WFS_LAYER", "kataster:ky_kehtiv")
FORESTIQ_METSAREGISTER_WFS_URL = os.getenv(
    "FORESTIQ_METSAREGISTER_WFS_URL",
    "https://gsavalik.envir.ee/geoserver/metsaregister/ows",
)
FORESTIQ_METSAREGISTER_WFS_LAYERS = [
    value.strip()
    for value in os.getenv("FORESTIQ_METSAREGISTER_WFS_LAYERS", "metsaregister:eraldis").split(",")
    if value.strip()
]
FORESTIQ_SOOS_WFS_URL = os.getenv("FORESTIQ_SOOS_WFS_URL", "")
FORESTIQ_SOOS_WFS_LAYER = os.getenv("FORESTIQ_SOOS_WFS_LAYER", "")
FORESTIQ_SOOS_WFS_CADASTRE_FIELD = os.getenv("FORESTIQ_SOOS_WFS_CADASTRE_FIELD", "katastri_nr")

# Authenticated sources are opt-in only. Leave their URLs empty until a service
# contract and a dedicated least-privilege credential have been configured.
FORESTEK_API_URL = os.getenv("FORESTEK_API_URL", "").rstrip("/")
FORESTEK_API_TOKEN = os.getenv("FORESTEK_API_TOKEN", "")
PARIMUS_API_URL = os.getenv("PARIMUS_API_URL", "").rstrip("/")
PARIMUS_API_TOKEN = os.getenv("PARIMUS_API_TOKEN", "")

LANGUAGE_CODE = "et-ee"
TIME_ZONE = os.getenv("TIME_ZONE", "Europe/Tallinn")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
