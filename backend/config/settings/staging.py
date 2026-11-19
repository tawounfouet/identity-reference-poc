"""Staging placeholder: a real secret and deployment policy are mandatory."""
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

if not SECRET_KEY:  # noqa: F405
    raise ImproperlyConfigured("DJANGO_SECRET_KEY is required for staging")

import os
from urllib.parse import urlsplit

FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "")
if urlsplit(FRONTEND_ORIGIN).scheme != "https" or not urlsplit(FRONTEND_ORIGIN).hostname:
    raise ImproperlyConfigured("Staging requires an HTTPS FRONTEND_ORIGIN")
HEADLESS_FRONTEND_URLS = headless_frontend_urls(FRONTEND_ORIGIN)  # noqa: F405
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
