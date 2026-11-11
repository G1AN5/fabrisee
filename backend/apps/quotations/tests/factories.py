from decimal import Decimal

import factory

from apps.core.tests.files import MINIMAL_PDF
from apps.projects.tests.factories import ProjectFactory
from apps.quotations.models import Quotation, QuotationStatus


class QuotationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Quotation

    project = factory.SubFactory(ProjectFactory)
    version_no = factory.LazyAttribute(lambda o: o.project.quotations.count() + 1)
    amount = Decimal("125000.00")
    file = factory.django.FileField(filename="quotation.pdf", data=MINIMAL_PDF)
    status = QuotationStatus.DRAFT
    prepared_by = factory.SelfAttribute("project.manager")
