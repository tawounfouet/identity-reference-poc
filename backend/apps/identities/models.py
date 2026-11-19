"""Identity aggregate root: a stable UUID is the primary identity key.

Keep Django AbstractUser semantics until the email/login policy is approved.
"""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """An application user identified by an opaque, immutable UUID.

    During IDR-002, Django's unique username remains the authentication
    identifier. The email field is not a login identifier or unique key.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
