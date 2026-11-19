"""Ephemeral OpenAPI export settings, intentionally separate from normal test.

Never select this profile for publicly reachable environments.
"""
from .test import *  # noqa: F403

HEADLESS_SERVE_SPECIFICATION = True
