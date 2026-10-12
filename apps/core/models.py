"""Framework-level base models shared across every PortaTap domain.

Only genuinely cross-cutting building blocks live here. Domain models stay in
their own app so business logic keeps a single, discoverable home.
"""

import uuid

from django.db import models


class UUIDModel(models.Model):
    """Primary key as a UUID.

    Database identifiers are never used as authorization tokens (see
    docs/API-CONVENTIONS.md §4); UUIDs also make them non-enumerable.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """Records when a row was created and last updated."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseModel(UUIDModel, TimeStampedModel):
    """UUID primary key plus creation/update timestamps."""

    class Meta:
        abstract = True
