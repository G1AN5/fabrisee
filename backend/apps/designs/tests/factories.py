import factory

from apps.accounts.models import Role
from apps.accounts.tests.factories import StaffFactory, UserFactory
from apps.core.tests.files import png_bytes
from apps.designs.models import Approval, ApprovalDecision, DesignRevision, RevisionStatus
from apps.projects.tests.factories import ProjectFactory


class DesignRevisionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DesignRevision

    project = factory.SubFactory(ProjectFactory)
    revision_no = factory.LazyAttribute(lambda o: o.project.revisions.count() + 1)
    render = factory.django.FileField(filename="render.png", data=png_bytes())
    status = RevisionStatus.PENDING_APPROVAL
    uploaded_by = factory.SubFactory(StaffFactory, role=Role.DESIGNER)


class ApprovalFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Approval

    revision = factory.SubFactory(DesignRevisionFactory)
    approver = factory.LazyAttribute(lambda o: UserFactory(client=o.revision.project.client))
    decision = ApprovalDecision.APPROVED
