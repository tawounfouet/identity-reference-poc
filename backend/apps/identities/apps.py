"""Identity domain Django app.

The app label is intentionally stable because it participates in AUTH_USER_MODEL.
"""

from django.apps import AppConfig


class IdentitiesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.identities"
    label = "identities"
    verbose_name = "Identités"
