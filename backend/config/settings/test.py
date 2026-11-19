"""Hermetic bootstrap test profile with no real credentials."""
from .base import *  # noqa: F403

SECRET_KEY = "pytest-bootstrap-only-not-for-production"
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

FRONTEND_ORIGIN = "http://localhost:3000"
HEADLESS_FRONTEND_URLS = headless_frontend_urls(FRONTEND_ORIGIN)  # noqa: F405
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# pytest does not serve a public HTTPS origin.
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
