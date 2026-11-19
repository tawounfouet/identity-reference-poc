"""Bootstrap settings. Do not deploy these without a G1 security review."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
DEBUG = False
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.identities.apps.IdentitiesConfig",
    "allauth",
    "allauth.account",
    "allauth.headless",
    "allauth.socialaccount",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "apps.security.middleware.ValidateHostMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": [
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
        ]},
    }
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "bootstrap.sqlite3",
    }
}

USE_TZ = True
TIME_ZONE = "UTC"
LANGUAGE_CODE = "fr-fr"
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "identities.User"

# Django login routes are handled by the allauth backend. No unthrottled
# ModelBackend admin login is exposed in this POC.
AUTHENTICATION_BACKENDS = ["allauth.account.auth_backends.AuthenticationBackend"]

# IDR-003: existing username credentials only. Email-only login is NOT
# enabled while AbstractUser.email is non-unique. Public signup is disabled.
ACCOUNT_LOGIN_METHODS = {"username"}
ACCOUNT_SIGNUP_FIELDS = ["username*", "email*", "password1*", "password2*"]
ACCOUNT_SIGNUP_ENABLED = False
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_CONFIRM_EMAIL_ON_GET = False
ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED = False

# Browser API with the built-in server-side Django session strategy.
HEADLESS_ONLY = True
HEADLESS_CLIENTS = ("browser",)
HEADLESS_SERVE_SPECIFICATION = False
SESSION_ENGINE = "django.contrib.sessions.backends.db"

# IDR-005/P2 baseline: cookies remain host-only and Django owns the session.
# The browser client reads the CSRF cookie, but never the session cookie.
SESSION_COOKIE_NAME = "sessionid"
SESSION_COOKIE_PATH = "/"
SESSION_COOKIE_DOMAIN = None
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = False  # Local/test only; staging overrides to True.
CSRF_COOKIE_NAME = "csrftoken"
CSRF_COOKIE_PATH = "/"
CSRF_COOKIE_DOMAIN = None
CSRF_COOKIE_HTTPONLY = False  # Required by the existing browser CSRF reader.
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = False  # Local/test only; staging overrides to True.
CSRF_USE_SESSIONS = False
CSRF_TRUSTED_ORIGINS = []  # Same-origin requests do not need an exception.

# Never trust proxy-supplied headers until its actual topology, cleaning
# behavior and trust boundary are proven in staging. See IDR-005 P3.
SECURE_PROXY_SSL_HEADER = None
USE_X_FORWARDED_HOST = False
USE_X_FORWARDED_PORT = False
SECURE_HSTS_SECONDS = 0
SECURE_SSL_REDIRECT = False  # P3 owns real HTTPS termination and redirects.



def headless_frontend_urls(origin: str) -> dict[str, str]:
    """URLs owned by the frontend. This is not an OAuth redirect allowlist."""
    origin = origin.rstrip("/")
    if not origin:
        raise ValueError("FRONTEND_ORIGIN must be configured")
    return {
        "account_confirm_email": f"{origin}/account/verify-email/{{key}}",
        "account_reset_password": f"{origin}/account/password/reset",
        "account_reset_password_from_key": f"{origin}/account/password/reset/key/{{key}}",
        "account_signup": f"{origin}/account/signup",
        "socialaccount_login_error": f"{origin}/account/provider/callback",
    }


# Set by local/test/staging profiles, never to a hardcoded public domain.
HEADLESS_FRONTEND_URLS = {}

