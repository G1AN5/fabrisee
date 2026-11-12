from django.db import models

from apps.core.models import TimeStampedModel


class Client(TimeStampedModel):
    """A client company of Five Brothers Solutions Inc."""

    company_name = models.CharField(max_length=200, unique=True)
    contact_person = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    # Staff only: never include this field in a serializer used by the client portal.
    notes = models.TextField(blank=True)
    # Soft delete: inactive clients stay in the records and keep their history.
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["company_name"]

    def __str__(self):
        return self.company_name
