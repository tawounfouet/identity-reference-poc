"""IDR-005/P2 cookie and Host safety invariants.

These checks are about Django's configuration and actual cookie/Host behavior.
They do not demonstrate a live HTTPS reverse proxy (IDR-005/P3) or a completed
CSRF authentication cycle (IDR-006).
"""
import pytest
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from django.test import Client, RequestFactory, override_settings


def test_cookie_policy_and_proxy_trust_are_explicit_in_the_local_baseline():
    assert settings.SESSION_ENGINE == "django.contrib.sessions.backends.db"
    assert settings.SESSION_COOKIE_NAME == "sessionid"
    assert settings.SESSION_COOKIE_HTTPONLY is True
    assert settings.SESSION_COOKIE_SAMESITE == "Lax"
    assert settings.SESSION_COOKIE_DOMAIN is None
    assert settings.CSRF_COOKIE_NAME == "csrftoken"
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
