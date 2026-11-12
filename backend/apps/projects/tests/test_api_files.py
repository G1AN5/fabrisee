"""`GET /api/files/{kind}/{id}/`: uploaded files are served only to those who may see them."""

import pytest
from django.utils import timezone

from apps.accounts.models import Role
from apps.accounts.tests.factories import StaffFactory, UserFactory
from apps.core.files import make_thumbnail
from apps.core.tests.files import MINIMAL_PDF, pdf_upload, png_bytes, png_upload
from apps.designs.models import RevisionStatus
from apps.designs.tests.factories import DesignRevisionFactory
from apps.projects.models import DocumentType
from apps.projects.tests.factories import DocumentFactory, ProjectFactory
from apps.quotations.models import QuotationStatus
from apps.quotations.tests.factories import QuotationFactory

pytestmark = pytest.mark.django_db


def body(response) -> bytes:
    return b"".join(response.streaming_content)


@pytest.fixture
def manager():
    return StaffFactory(role=Role.PROJECT_MANAGER)


@pytest.fixture
def project():
    return ProjectFactory(project_number="FS-2026-0007")


@pytest.fixture
def client_user(project):
    return UserFactory(client=project.client)


def test_document_is_downloaded_with_its_original_name(login, manager, project):
    document = DocumentFactory(
        project=project,
        file=pdf_upload("x.pdf"),
        original_name="Client brief (final).pdf",
        content_type="application/pdf",
    )

    response = login(manager).get(f"/api/files/document/{document.pk}/")

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response["Content-Disposition"] == 'attachment; filename="Client brief (final).pdf"'
    assert response["Cache-Control"] == "private, max-age=3600"
    assert body(response) == MINIMAL_PDF


def test_inline_shows_the_file_in_the_browser_and_allows_same_origin_frames(
    login, manager, project
):
    quotation = QuotationFactory(project=project, version_no=2)

    response = login(manager).get(f"/api/files/quotation/{quotation.pk}/?inline=1")

    assert response.status_code == 200
    assert response["Content-Disposition"] == 'inline; filename="FS-2026-0007-quotation-v2.pdf"'
    # The PDF viewer of the app embeds the file in a frame on the same origin.
    assert response["X-Frame-Options"] == "SAMEORIGIN"


def test_render_spec_sheet_and_thumbnail_of_a_revision(login, manager, project):
    revision = DesignRevisionFactory(
        project=project,
        render=png_upload("render.png", size=(800, 500)),
        spec_sheet=pdf_upload("spec.pdf"),
    )
    revision.thumbnail.save("thumbnail.webp", make_thumbnail(png_upload(size=(800, 500))))
    api = login(manager)

    render = api.get(f"/api/files/render/{revision.pk}/?inline=1")
    spec = api.get(f"/api/files/spec/{revision.pk}/")
    thumbnail = api.get(f"/api/files/render/{revision.pk}/?variant=thumb")

    assert render["Content-Type"] == "image/png"
    assert render["Content-Disposition"] == 'inline; filename="FS-2026-0007-R1-render.png"'
    assert spec["Content-Type"] == "application/pdf"
    assert spec["Content-Disposition"] == ('attachment; filename="FS-2026-0007-R1-spec-sheet.pdf"')
    assert thumbnail["Content-Type"] == "image/webp"
    assert thumbnail["Content-Disposition"].startswith("inline")
    assert body(thumbnail)[:4] == b"RIFF"


def test_missing_spec_sheet_thumbnail_and_unknown_kind_are_not_found(login, manager, project):
    revision = DesignRevisionFactory(project=project)
    api = login(manager)

    assert api.get(f"/api/files/spec/{revision.pk}/").status_code == 404
    assert api.get(f"/api/files/render/{revision.pk}/?variant=thumb").status_code == 404
    assert api.get(f"/api/files/secret/{revision.pk}/").status_code == 404
    assert api.get("/api/files/document/999999/").status_code == 404


def test_a_file_missing_from_storage_is_reported_as_not_found(login, manager, project):
    document = DocumentFactory(project=project)
    document.file.storage.delete(document.file.name)

    response = login(manager).get(f"/api/files/document/{document.pk}/")

    assert response.status_code == 404
    assert response.json()["detail"] == "This file is missing from storage."


def test_client_downloads_only_client_visible_documents(login, client_user, project):
    visible = DocumentFactory(project=project, visible_to_client=True)
    internal = DocumentFactory(project=project, visible_to_client=False)
    api = login(client_user)

    assert api.get(f"/api/files/document/{visible.pk}/").status_code == 200
    assert api.get(f"/api/files/document/{internal.pk}/").status_code == 404
    assert api.get(f"/api/files/document/{internal.pk}/?variant=thumb").status_code == 404


def test_client_downloads_sent_quotations_but_never_a_draft(login, client_user, project):
    sent = QuotationFactory(
        project=project, status=QuotationStatus.SUPERSEDED, sent_at=timezone.now()
    )
    draft = QuotationFactory(project=project, status=QuotationStatus.DRAFT)
    api = login(client_user)

    assert api.get(f"/api/files/quotation/{sent.pk}/").status_code == 200
    assert api.get(f"/api/files/quotation/{draft.pk}/").status_code == 404


def test_client_sees_every_revision_of_their_own_project(login, client_user, project):
    pending = DesignRevisionFactory(project=project)

    response = login(client_user).get(f"/api/files/render/{pending.pk}/")

    assert response.status_code == 200
    assert body(response) == png_bytes()


def test_production_staff_cannot_open_quotations_or_pending_revisions(login, project):
    production = StaffFactory(role=Role.PRODUCTION)
    quotation = QuotationFactory(project=project, status=QuotationStatus.ACCEPTED)
    quotation_copy = DocumentFactory(project=project, doc_type=DocumentType.QUOTATION)
    reference = DocumentFactory(project=project, doc_type=DocumentType.REFERENCE)
    approved = DesignRevisionFactory(
        project=project, status=RevisionStatus.APPROVED, locked_at=timezone.now()
    )
    pending = DesignRevisionFactory(project=project)
    api = login(production)

    assert api.get(f"/api/files/quotation/{quotation.pk}/").status_code == 404
    assert api.get(f"/api/files/document/{quotation_copy.pk}/").status_code == 404
    assert api.get(f"/api/files/document/{reference.pk}/").status_code == 200
    assert api.get(f"/api/files/render/{approved.pk}/").status_code == 200
    assert api.get(f"/api/files/render/{pending.pk}/").status_code == 404


def test_uploaded_files_have_no_public_address(api_client, project):
    document = DocumentFactory(project=project)

    # MEDIA_URL is never routed: the stored path leads to the React app, not to the file.
    response = api_client.get(f"/media/{document.file.name}")

    assert response.status_code in (404, 503)
    assert b"PNG" not in response.content
