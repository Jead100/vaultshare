from datetime import timedelta
from pathlib import Path

import dj_database_url
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY")

DEBUG = config("DEBUG", default=False, cast=bool)


# Hosts & CSRF

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="127.0.0.1, localhost",
    cast=lambda v: [s.strip() for s in v.split(",")],
)

CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in config(
        "CSRF_TRUSTED_ORIGINS",
        default="",
    ).split(",")
    if o.strip()
]


# Application definition

INSTALLED_APPS = [
    # Static handling (parity mode)
    "whitenoise.runserver_nostatic",
    "django.contrib.staticfiles",
    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "storages",
    "drf_spectacular",
    # Django-Tailwind
    "theme",
    "tailwind",
    # Local apps
    "apps.core",
    "apps.files",
    "apps.users",
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

# Dev-only apps and middleware
if DEBUG:
    INSTALLED_APPS += ["django_browser_reload"]
    MIDDLEWARE.append(
        "django_browser_reload.middleware.BrowserReloadMiddleware",
    )

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


# Database

DATABASE_URL = config("DATABASE_URL", default="")

if DEBUG:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            ssl_require=True,
        )
    }


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files & Media (dev defaults)

STATIC_URL = "/static/"

STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"

# Prod-only settings
if not DEBUG:
    STATIC_ROOT = BASE_DIR / "staticfiles"

    STORAGES = {
        "staticfiles": {
            # WhiteNoise: hashed filenames + gzip/brotli pre-compression
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
        "default": {
            # Media (uploads) -> S3
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        },
    }

    # S3 creds/settings
    AWS_STORAGE_BUCKET_NAME = config("AWS_STORAGE_BUCKET_NAME")
    AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY")
    AWS_S3_REGION_NAME = config("AWS_S3_REGION_NAME", default="us-east-1")
    AWS_S3_SIGNATURE_VERSION = "s3v4"

    # Keep objects private; generate time-limited links
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = True
    AWS_QUERYSTRING_EXPIRE = 300  # TTL (seconds) – 5 minutes
    AWS_S3_FILE_OVERWRITE = False

    # R2/other S3-compatible targets (optional)
    AWS_S3_ENDPOINT_URL = config("AWS_S3_ENDPOINT_URL", default=None)

    # Override MEDIA_URL (CDN first, else direct S3)
    AWS_S3_CUSTOM_DOMAIN = config("AWS_S3_CUSTOM_DOMAIN", default="")
    MEDIA_URL = (
        f"https://{AWS_S3_CUSTOM_DOMAIN}/"
        if AWS_S3_CUSTOM_DOMAIN
        else f"https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/"
    )

# Default primary key field type

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django-Tailwind

TAILWIND_APP_NAME = "theme"

NPM_BIN_PATH = config("NPM_BIN_PATH", default=None)

# Django Rest Framework

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        # generic fallbacks
        "anon": "60/minute",
        "user": "240/minute",
        # view-specific scopes
        "shares:meta": "120/minute",
        "shares:download": "1000/hour",
    },
}

# Only enable the Browsable API in development
if DEBUG:
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"].append(
        "rest_framework.renderers.BrowsableAPIRenderer",
    )

# SimpleJWT

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=10),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,  # update User.last_login on token obtain
    "ALGORITHM": "HS256",  # default HMAC using SECRET_KEY
    "AUTH_HEADER_TYPES": ("Bearer",),  # use Authorization: Bearer <token>
    "LEEWAY": 30,  # allow 30s clock skew when validating token exp/nbf
}

# drf-spectacular

SPECTACULAR_SETTINGS = {
    "TITLE": "Vaultshare API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SECURITY": [{"BearerAuth": []}],
    "AUTHENTICATION_WHITELIST": [],
    "APPEND_COMPONENTS": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
    },
}

# ---

AUTH_USER_MODEL = "users.User"

LOGIN_URL = "users:login"
LOGIN_REDIRECT_URL = "core:dashboard"
LOGOUT_REDIRECT_URL = "home"

# Minimal logging (shows Django errors in console when DEBUG=False)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {  # catches everything including Django request errors
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.server": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
