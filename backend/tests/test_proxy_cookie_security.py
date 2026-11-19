"""IDR-005/P2 cookie and Host safety invariants.

These checks are about Django's configuration and actual cookie/Host behavior.
They do not demonstrate a live HTTPS reverse proxy (IDR-005/P3) or a completed
CSRF authentication cycle (IDR-006).
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import Client, RequestFactory, override_settings


def test_cookie_policy_and_proxy_trust_are_explicit_in_the_local_baseline():
    assert settings.SESSION_ENGINE == "django.contrib.sessions.backends.db"
    assert settings.SESSION_COOKIE_NAME == "sessionid"
    assert settings.SESSION_COOKIE_SECURE is False  # Explicit test-only exception
    assert settings.SESSION_COOKIE_HTTPONLY is True
    assert settings.SESSION_COOKIE_SAMESITE == "Lax"
    assert settings.SESSION_COOKIE_DOMAIN is None
    assert settings.CSRF_COOKIE_NAME == "csrftoken"
    assert settings.CSRF_COOKIE_SECURE is False  # Explicit test-only exception
    assert settings.CSRF_COOKIE_HTTPONLY is False
    assert settings.CSRF_COOKIE_SAMESITE == "Lax"
    assert settings.CSRF_COOKIE_DOMAIN is None
    assert settings.CSRF_TRUSTED_ORIGINS == []
    assert settings.SECURE_PROXY_SSL_HEADER is None
    assert settings.USE_X_FORWARDED_HOST is False
    assert settings.USE_X_FORWARDED_PORT is False
    assert settings.SECURE_HSTS_SECONDS == 0
    assert "apps.security.middleware.ValidateHostMiddleware" in settings.MIDDLEWARE


def test_invalid_host_is_rejected_even_on_simple_healthcheck():
    response = Client(HTTP_HOST="hostile.invalid").get("/health/")
    assert response.status_code == 400


def test_host_override_headers_are_not_trusted():
    client = Client(
        HTTP_HOST="testserver",
        HTTP_X_FORWARDED_HOST="hostile.invalid",
        HTTP_X_FORWARDED_PROTO="https",
    )
    response = client.get("/health/")
    assert response.status_code == 200
    request = RequestFactory().get(
        "/health/",
        HTTP_HOST="testserver",
        HTTP_X_FORWARDED_HOST="hostile.invalid",
        HTTP_X_FORWARDED_PROTO="https",
    )
    assert request.get_host() == "testserver"
    assert request.is_secure() is False


@pytest.mark.django_db
@override_settings(
    SESSION_COOKIE_SECURE=True,
    CSRF_COOKIE_SECURE=True,
    SESSION_COOKIE_DOMAIN=None,
    CSRF_COOKIE_DOMAIN=None,
    ALLOWED_HOSTS=["testserver"],
)
def test_real_headless_csrf_cookie_has_secure_host_only_attributes():
    response = Client().get("/_allauth/browser/v1/config")
    assert response.status_code == 200
    assert "csrftoken" in response.cookies
    cookie = response.cookies["csrftoken"]
    assert cookie["secure"] is True
    assert cookie["httponly"] == ""
    assert cookie["samesite"] == "Lax"
    assert cookie["path"] == "/"
    assert cookie["domain"] == ""


@pytest.mark.django_db
@override_settings(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_DOMAIN=None,
)
def test_session_middleware_emits_secure_httponly_host_only_cookie():
    middleware = SessionMiddleware(lambda request: HttpResponse("OK"))
    request = RequestFactory().get("/health/")
    middleware.process_request(request)
    request.session["identity-test"] = "not-a-secret"
    response = middleware.process_response(request, HttpResponse("OK"))
    assert "sessionid" in response.cookies
    cookie = response.cookies["sessionid"]
    assert cookie["secure"] is True
    assert cookie["httponly"] is True
    assert cookie["samesite"] == "Lax"
    assert cookie["path"] == "/"
    assert cookie["domain"] == ""


def staging_settings_process(*, origin="https://staging.example.test", hosts="staging.example.test"):
    """Inspect staging configuration in a fresh Python process."""
    env = os.environ.copy()
    env.update({
        "DJANGO_SETTINGS_MODULE": "config.settings.staging",
        "DJANGO_SECRET_KEY": "ci-test-only-not-a-real-staging-secret",
        "DJANGO_ALLOWED_HOSTS": hosts,
        "FRONTEND_ORIGIN": origin,
    })
    script = (
        "import json; from django.conf import settings; "
        "print(json.dumps({"
        "'hosts': settings.ALLOWED_HOSTS, "
        "'session_secure': settings.SESSION_COOKIE_SECURE, "
        "'session_httponly': settings.SESSION_COOKIE_HTTPONLY, "
        "'session_domain': settings.SESSION_COOKIE_DOMAIN, "
        "'session_samesite': settings.SESSION_COOKIE_SAMESITE, "
        "'csrf_secure': settings.CSRF_COOKIE_SECURE, "
        "'csrf_httponly': settings.CSRF_COOKIE_HTTPONLY, "
        "'csrf_domain': settings.CSRF_COOKIE_DOMAIN, "
        "'csrf_samesite': settings.CSRF_COOKIE_SAMESITE, "
        "'trusted_proxy_header': settings.SECURE_PROXY_SSL_HEADER, "
        "'forwarded_host': settings.USE_X_FORWARDED_HOST, "
        "'hsts_seconds': settings.SECURE_HSTS_SECONDS, "
        "'csrf_trusted_origins': settings.CSRF_TRUSTED_ORIGINS"
        "}))"
    )
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=15,
    )


def test_staging_cookie_policy_loads_with_exact_https_host():
    result = staging_settings_process()
    assert result.returncode == 0, result.stderr
    config = json.loads(result.stdout)
    assert config["hosts"] == ["staging.example.test"]
    assert config["session_secure"] is True
    assert config["session_httponly"] is True
    assert config["session_domain"] is None
    assert config["session_samesite"] == "Lax"
    assert config["csrf_secure"] is True
    assert config["csrf_httponly"] is False
    assert config["csrf_domain"] is None
    assert config["csrf_samesite"] == "Lax"
    assert config["trusted_proxy_header"] is None
    assert config["forwarded_host"] is False
    assert config["hsts_seconds"] == 0
    assert config["csrf_trusted_origins"] == []


@pytest.mark.parametrize(
    ("origin", "hosts"),
    [
        ("http://staging.example.test", "staging.example.test"),
        ("https://staging.example.test:8443", "staging.example.test"),
        ("https://staging.example.test/login", "staging.example.test"),
        ("https://user:pass@staging.example.test", "staging.example.test"),
        ("https://localhost", "localhost"),
        ("https://staging.example.test", "*"),
        ("https://staging.example.test", "localhost,127.0.0.1"),
        ("https://staging.example.test", "other.example.test"),
        ("https://staging.example.test", "staging.example.test,other.example.test"),
    ],
)
def test_staging_rejects_unsafe_origin_or_host_allowlists(origin, hosts):
    result = staging_settings_process(origin=origin, hosts=hosts)
    assert result.returncode != 0
    assert "ImproperlyConfigured" in result.stderr
