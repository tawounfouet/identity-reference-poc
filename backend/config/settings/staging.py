"""Staging placeholder: a real secret and deployment policy are mandatory."""
import os
from urllib.parse import urlsplit

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

if not SECRET_KEY:  # noqa: F405
    raise ImproperlyConfigured("DJANGO_SECRET_KEY is required for staging")

FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "")
parsed_origin = urlsplit(FRONTEND_ORIGIN)
if (
    parsed_origin.scheme != "https"
    or not parsed_origin.hostname
    or parsed_origin.username is not None
    or parsed_origin.password is not None
    or parsed_origin.path not in ("", "/")
    or parsed_origin.query
    or parsed_origin.fragment
    or parsed_origin.port not in (None, 443)
):
    raise ImproperlyConfigured("Staging requires a canonical HTTPS FRONTEND_ORIGIN")

# A staging process must never inherit permissive local or wildcard hosts.
# Its single public hostname is the browser-visible origin for this POC.
if (
    not ALLOWED_HOSTS  # noqa: F405
    or ALLOWED_HOSTS != [parsed_origin.hostname]  # noqa: F405
    or parsed_origin.hostname in {"localhost", "127.0.0.1", "::1"}
):
    raise ImproperlyConfigured(
        "Staging requires DJANGO_ALLOWED_HOSTS to equal the exact frontend HTTPS hostname"
    )

HEADLESS_FRONTEND_URLS = headless_frontend_urls(FRONTEND_ORIGIN)  # noqa: F405

# Session is never accessible to JavaScript. CSRF is intentionally readable by
# the browser client so it can provide X-CSRFToken on mutations.
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_DOMAIN = None
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_DOMAIN = None

# No forwarded header is trusted or SSL redirect claimed before P3. The
# HTTPS-capable edge must later be demonstrated and explicitly approved.
SECURE_PROXY_SSL_HEADER = None
USE_X_FORWARDED_HOST = False
USE_X_FORWARDED_PORT = False
SECURE_HSTS_SECONDS = 0
