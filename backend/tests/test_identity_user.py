"""IDR-002 contract tests for the swappable Django User model."""

import uuid

import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import UserManager
from django.db import IntegrityError
from django.test import override_settings


def test_custom_user_is_registered():
    model = get_user_model()
    assert model is apps.get_model("identities", "User")
    assert model._meta.label == "identities.User"
    assert model.USERNAME_FIELD == "username"
    assert model.REQUIRED_FIELDS == ["email"]
    assert isinstance(model.objects, UserManager)


@pytest.mark.django_db
def test_user_is_created_with_opaque_uuid_and_hashed_password():
    user = get_user_model().objects.create_user(
        username="identity_demo",
        email="identity@example.org",
        password="not-a-real-secret-passphrase",
    )

    assert isinstance(user.pk, uuid.UUID)
    assert user.pk.version == 4
    assert user.pk == user.id
    assert user.is_active is True
    assert user.is_staff is False
    assert user.is_superuser is False
    assert user.password != "not-a-real-secret-passphrase"
    assert user.check_password("not-a-real-secret-passphrase")
    assert not user.check_password("incorrect")


@pytest.mark.django_db
def test_username_must_be_unique():
    users = get_user_model().objects
    users.create_user(username="unique_login", email="a@example.org")
    with pytest.raises(IntegrityError):
        users.create_user(username="unique_login", email="b@example.org")


@pytest.mark.django_db
def test_email_does_not_imply_identity_uniqueness_yet():
    """No implicit email-account linking before the allauth policy of IDR-003."""
    users = get_user_model().objects
    first = users.create_user(username="first_account", email="shared@example.org")
    second = users.create_user(username="second_account", email="shared@example.org")
    assert first.pk != second.pk


@pytest.mark.django_db
def test_superuser_contract():
    user = get_user_model().objects.create_superuser(
        username="admin_test",
        email="admin@example.org",
        password="another-test-only-passphrase",
    )
    assert user.is_staff is True
    assert user.is_superuser is True
    assert user.is_active is True
    assert user.check_password("another-test-only-passphrase")


def test_id_field_is_not_editable_and_is_primary_key():
    field = get_user_model()._meta.get_field("id")
    assert field.primary_key
    assert not field.editable


def test_password_and_email_are_not_public_identifiers():
    """Email is not the Django username field at this stage."""
    assert get_user_model().USERNAME_FIELD == "username"
    assert get_user_model()._meta.get_field("email").unique is False
