from datetime import timedelta

import factory
from django.utils import timezone

from apps.accounts.models import Role
from apps.accounts.tests.factories import StaffFactory, UserFactory
from apps.clients.tests.factories import ClientFactory
from apps.core.tests.files import png_bytes
from apps.projects.models import (
    Document,
    DocumentType,
    Project,
    ProjectApprover,
    ProjectType,
    Stage,
    StageUpdate,
    StageUpdateSource,
)


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project
        skip_postgeneration_save = True

    project_number = factory.Sequence(lambda n: f"FS-2026-{n + 1:04d}")
    client = factory.SubFactory(ClientFactory)
    title = factory.Sequence(lambda n: f"Display project {n + 1}")
    project_type = ProjectType.DISPLAY_STAND
    location = "Ground floor, Sample Mall, Pasig City"
    target_date = factory.LazyFunction(lambda: timezone.localdate() + timedelta(days=30))
    dimensions = "1.2 m × 0.6 m × 1.8 m"
    description = "A sample project for tests."
    stage = Stage.REQUEST
    manager = factory.SubFactory(StaffFactory, role=Role.PROJECT_MANAGER)
    created_by = factory.SelfAttribute("manager")

    @factory.post_generation
    def approvers(self, create, extracted, **kwargs):
        """`ProjectFactory(approvers=[user, ...])` designates the approvers."""
        if create and extracted:
            for user in extracted:
                ProjectApprover.objects.create(project=self, user=user)


class ProjectApproverFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ProjectApprover

    project = factory.SubFactory(ProjectFactory)
    user = factory.LazyAttribute(lambda o: UserFactory(client=o.project.client))


class StageUpdateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StageUpdate

    project = factory.SubFactory(ProjectFactory)
    from_stage = ""
    to_stage = Stage.REQUEST
    source = StageUpdateSource.RULE
    updated_by = factory.SelfAttribute("project.created_by")


class DocumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Document

    project = factory.SubFactory(ProjectFactory)
    doc_type = DocumentType.REFERENCE
    file = factory.django.FileField(filename="reference.png", data=png_bytes())
    original_name = "reference.png"
    size_bytes = factory.LazyAttribute(lambda o: o.file.size)
    content_type = "image/png"
    visible_to_client = True
    uploaded_by = factory.SelfAttribute("project.created_by")
