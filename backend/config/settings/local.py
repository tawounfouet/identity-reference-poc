"""Local development only: deliberately insecure secret for the bootstrap."""
import os

from .base import *  # noqa: F403

DEBUG = True
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "local-bootstrap-only-change-before-any-deployment-very-insecure",
)
