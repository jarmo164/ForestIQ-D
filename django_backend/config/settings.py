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
    "django.contrib.gis",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "accounts",
    "forestry",
    "operations",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "api.middleware.OrganizationContextMiddleware",
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
    """Return PostGIS configuration, with explicit local test-only database modes."""
    if env_bool("USE_SPATIALITE_FOR_TESTS", False):
        return {
            "ENGINE": "django.contrib.gis.db.backends.spatialite",
            "NAME": BASE_DIR / "spatialite-test.sqlite3",
        }
    if env_bool("USE_SQLITE_FOR_TESTS", False):
        return {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        parsed = urlparse(database_url)
        if parsed.scheme not in {"postgres", "postgresql"}:
            raise ValueError("DATABASE_URL must use the postgres or postgresql scheme")
        return {
            "ENGINE": "django.contrib.gis.db.backends.postgis",
            "NAME": parsed.path.lstrip("/"),
            "USER": parsed.username,
            "PASSWORD": parsed.password,
            "HOST": parsed.hostname,
            "PORT": parsed.port or 5432,
            "CONN_MAX_AGE": 60,
        }

    return {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.getenv("POSTGRES_DB", "forestiq"),
        "USER": os.getenv("POSTGRES_USER", "forestiq"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "forestiq"),
        "HOST": os.getenv("POSTGRES_HOST", "db"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }


DATABASES = {"default": database_from_environment()}
SPATIALITE_LIBRARY_PATH = os.getenv("SPATIALITE_LIBRARY_PATH", "mod_spatialite")

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
        "api.authentication.OrganizationJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated"],
    "EXCEPTION_HANDLER": "api.exceptions.api_exception_handler",
}

# Render deploys the MapLibre UI as a separate static site. Keep this list
# explicit: an empty value leaves cross-origin requests disabled by default.
CORS_ALLOWED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv("DJANGO_CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = False

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
# A production deployment can never enable the local password/TOTP bypass, even
# if an environment variable is accidentally copied from development.
FORESTIQ_DEVMODE = DEBUG and env_bool("FORESTIQ_DEVMODE", DEBUG)

# Keycloak is an external public client: the browser performs Authorization
# Code + PKCE and Django exchanges the code before minting its internal JWT.
KEYCLOAK_OIDC_ENABLED = env_bool("KEYCLOAK_OIDC_ENABLED", False)
KEYCLOAK_ISSUER = os.getenv("KEYCLOAK_ISSUER", "").rstrip("/")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "forestiq-web")
KEYCLOAK_SCOPES = os.getenv("KEYCLOAK_SCOPES", "openid profile email")
KEYCLOAK_ORGANIZATION_CLAIM = os.getenv("KEYCLOAK_ORGANIZATION_CLAIM", "organization_id")
KEYCLOAK_HTTP_TIMEOUT_SECONDS = int(os.getenv("KEYCLOAK_HTTP_TIMEOUT_SECONDS", "10"))
KEYCLOAK_JWKS_CACHE_SECONDS = int(os.getenv("KEYCLOAK_JWKS_CACHE_SECONDS", "3600"))
KEYCLOAK_CLOCK_SKEW_SECONDS = int(os.getenv("KEYCLOAK_CLOCK_SKEW_SECONDS", "30"))
KEYCLOAK_DISCOVERY_URL = f"{KEYCLOAK_ISSUER}/.well-known/openid-configuration"

# Redis carries only queued work; the authoritative audit state remains in
# DataSyncRun, so jobs stay observable even after a broker restart.
CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
CELERY_TASK_DEFAULT_QUEUE = "forestiq"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = int(os.getenv("CELERY_TASK_TIME_LIMIT_SECONDS", "300"))
CELERY_TASK_SOFT_TIME_LIMIT = int(os.getenv("CELERY_TASK_SOFT_TIME_LIMIT_SECONDS", "270"))
CELERY_TASK_ACKS_LATE = True
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BEAT_SCHEDULE = {
    "forestiq-daily-portfolio-sync": {
        "task": "forestry.tasks.enqueue_all_organizations_portfolio_sync",
        "schedule": float(os.getenv("FORESTIQ_PORTFOLIO_SYNC_INTERVAL_SECONDS", "86400")),
    },
    "forestiq-metsaregister-cql-delta": {
        "task": "forestry.tasks.enqueue_all_organizations_metsaregister_delta_check",
        "schedule": float(os.getenv("FORESTIQ_METSAREGISTER_DELTA_INTERVAL_SECONDS", "3600")),
    },
}
FORESTIQ_TASKS_INLINE = env_bool("FORESTIQ_TASKS_INLINE", False)
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
FORESTIQ_METSAREGISTER_FULL_WFS_LAYER = os.getenv("FORESTIQ_METSAREGISTER_FULL_WFS_LAYER", "metsaregister:eraldis")
FORESTIQ_METSAREGISTER_NOTIFICATION_WFS_LAYER = os.getenv("FORESTIQ_METSAREGISTER_NOTIFICATION_WFS_LAYER", "")
FORESTIQ_METSAREGISTER_NOTIFICATION_CADASTRE_FIELD = os.getenv("FORESTIQ_METSAREGISTER_NOTIFICATION_CADASTRE_FIELD", "katastri_nr")
FORESTIQ_METSAREGISTER_NOTIFICATION_SUBPART_FIELD = os.getenv("FORESTIQ_METSAREGISTER_NOTIFICATION_SUBPART_FIELD", "eraldis_nr")
FORESTIQ_METSAREGISTER_FULL_PAGE_SIZE = int(os.getenv("FORESTIQ_METSAREGISTER_FULL_PAGE_SIZE", "1000"))
FORESTIQ_METSAREGISTER_DELTA_FIELD = os.getenv("FORESTIQ_METSAREGISTER_DELTA_FIELD", "registreerimise_kp")
FORESTIQ_METSAREGISTER_DELTA_LOOKBACK_HOURS = int(os.getenv("FORESTIQ_METSAREGISTER_DELTA_LOOKBACK_HOURS", "48"))
FORESTIQ_METSAREGISTER_DELTA_OVERLAP_MINUTES = int(os.getenv("FORESTIQ_METSAREGISTER_DELTA_OVERLAP_MINUTES", "10"))
FORESTIQ_MAP_NEW_SUBPART_HOURS = int(os.getenv("FORESTIQ_MAP_NEW_SUBPART_HOURS", "168"))
FORESTIQ_MAP_CADASTRE_LIMIT = int(os.getenv("FORESTIQ_MAP_CADASTRE_LIMIT", "750"))
FORESTIQ_MAP_FEATURE_LIMIT = int(os.getenv("FORESTIQ_MAP_FEATURE_LIMIT", "1500"))
FORESTIQ_MAP_MAX_FEATURE_LIMIT = int(os.getenv("FORESTIQ_MAP_MAX_FEATURE_LIMIT", "3000"))
FORESTIQ_SOOS_WFS_URL = os.getenv("FORESTIQ_SOOS_WFS_URL", "")
FORESTIQ_SOOS_WFS_LAYER = os.getenv("FORESTIQ_SOOS_WFS_LAYER", "")
FORESTIQ_SOOS_WFS_CADASTRE_FIELD = os.getenv("FORESTIQ_SOOS_WFS_CADASTRE_FIELD", "katastri_nr")

# Authenticated sources are opt-in only. Forestek is a one-time initial import;
# it is deliberately excluded from scheduled and routine registry refreshes.
# Leave their URLs empty until a service contract and a dedicated least-privilege
# credential have been configured.
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
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.getenv("FORESTIQ_MEDIA_ROOT", BASE_DIR / "media"))
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
