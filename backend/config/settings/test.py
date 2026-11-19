"""Hermetic bootstrap test profile with no real credentials."""
from .base import *  # noqa: F403

SECRET_KEY = "pytest-bootstrap-only-not-for-production"
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
