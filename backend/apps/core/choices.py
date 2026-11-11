from django.db import models


class DecisionChannel(models.TextChoices):
    """How a client's decision reached the company."""

    PORTAL = "portal", "Client portal"
    EMAIL = "email", "Email"
    PHONE = "phone", "Phone"
    IN_PERSON = "in_person", "In person"


# Channels a staff member may choose when recording a decision on behalf of a client.
ON_BEHALF_CHANNELS = (DecisionChannel.EMAIL, DecisionChannel.PHONE, DecisionChannel.IN_PERSON)
