from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from apps.core.tests.files import pdf_upload
from apps.projects.tests.factories import ProjectFactory
from apps.quotations.models import QuotationStatus
from apps.quotations.tests.factories import QuotationFactory

pytestmark = pytest.mark.django_db


def test_versions_are_numbered_per_project():
    project = ProjectFactory()
    first = QuotationFactory(project=project, status=QuotationStatus.SUPERSEDED)
    second = QuotationFactory(project=project)

    assert (first.version_no, second.version_no) == (1, 2)
    assert second.label == "v2"
    with pytest.raises(IntegrityError), transaction.atomic():
        QuotationFactory(project=project, version_no=2)


def test_only_one_quotation_per_project_can_be_waiting_for_a_decision():
    project = ProjectFactory()
    QuotationFactory(project=project, status=QuotationStatus.SENT)

    with pytest.raises(IntegrityError), transaction.atomic():
        QuotationFactory(project=project, status=QuotationStatus.SENT)

    # Another project may have its own sent quotation.
    QuotationFactory(status=QuotationStatus.SENT)


def test_an_accepted_quotation_cannot_be_changed():
    quotation = QuotationFactory(status=QuotationStatus.ACCEPTED)

    quotation.amount = Decimal("1.00")
    with pytest.raises(ProtectedError):
        quotation.save()

    quotation.refresh_from_db()
    quotation.file = pdf_upload("replacement.pdf")
    with pytest.raises(ProtectedError):
        quotation.save()

    quotation.refresh_from_db()
    assert quotation.amount == Decimal("125000.00")


def test_notes_on_an_accepted_quotation_may_still_be_saved():
    quotation = QuotationFactory(status=QuotationStatus.ACCEPTED)

    quotation.last_reminded_at = None
    quotation.notes = "Signed copy received."
    quotation.save()

    quotation.refresh_from_db()
    assert quotation.notes == "Signed copy received."


def test_quotations_are_never_deleted():
    quotation = QuotationFactory()

    with pytest.raises(ProtectedError):
        quotation.delete()


def test_clients_never_see_drafts():
    draft = QuotationFactory()

    assert draft.was_sent is False
