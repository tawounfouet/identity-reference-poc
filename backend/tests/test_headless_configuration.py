"""IDR-003 contracts, focusing on configuration and isolation boundaries."""
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import Resolver404, resolve


def test_headless_configuration_is_browser_only():
    assert settings.AUTH_USER_MODEL == "identities.User"
    assert settings.HEADLESS_ONLY is True
    assert settings.HEADLESS_CLIENTS == ("browser",)
    assert settings.HEADLESS_SERVE_SPECIFICATION is False
    assert settings.SESSION_ENGINE == "django.contrib.sessions.backends.db"
    assert "allauth.account.middleware.AccountMiddleware" in settings.MIDDLEWARE


def test_username_policy_and_disabled_public_signup():
    assert settings.ACCOUNT_LOGIN_METHODS == {"username"}
    assert settings.ACCOUNT_SIGNUP_ENABLED is False
    assert settings.ACCOUNT_EMAIL_VERIFICATION == "mandatory"
    assert settings.ACCOUNT_CONFIRM_EMAIL_ON_GET is False
    assert settings.ACCOUNT_LOGOUT_ON_GET is False
    assert get_user_model().USERNAME_FIELD == "username"
    assert get_user_model()._meta.get_field("email").unique is False


def test_frontend_confirmation_and_reset_urls_are_owned_by_frontend():
    urls = settings.HEADLESS_FRONTEND_URLS
    assert urls["account_confirm_email"] == (
        "http://localhost:3000/account/verify-email/{key}"
    )
    assert urls["account_reset_password_from_key"].endswith("/key/{key}")


def test_official_browser_session_route_is_registered():
    match = resolve("/_allauth/browser/v1/auth/session")
    assert match.func is not None


def test_headless_browser_session_endpoint_does_not_raise_server_error():
    response = Client().get("/_allauth/browser/v1/auth/session")
    assert response.status_code < 500
    assert response.headers["Content-Type"].startswith("application/json")


def test_app_session_api_is_not_exposed():
    with pytest.raises(Resolver404):
        resolve("/_allauth/app/v1/auth/session")


def test_regular_account_login_html_is_disabled():
    with pytest.raises(Resolver404):
        resolve("/accounts/login/")


def test_openapi_not_exposed_in_normal_test_profile():
    response = Client().get("/_allauth/openapi.json")
    assert response.status_code == 404
