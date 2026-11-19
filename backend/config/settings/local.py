"""Local development only: deliberately insecure secret for the bootstrap."""
import os

from .base import *  # noqa: F403

DEBUG = True
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "local-bootstrap-only-change-before-any-deployment-very-insecure",
)

# Browser-facing URLs only; frontend lives on port 3000 in local development.
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000")
HEADLESS_FRONTEND_URLS = headless_frontend_urls(FRONTEND_ORIGIN)  # noqa: F405
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
