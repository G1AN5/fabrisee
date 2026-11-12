import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.core.exceptions import RuleViolation
from apps.core.files import (
    PDF_MIME_TYPE,
    detect_mime_type,
    document_upload_path,
    make_thumbnail,
    validate_upload,
)
from apps.core.models import SystemSetting
from apps.core.tests.files import pdf_upload, png_upload


def test_type_is_detected_from_content_not_from_the_name():
    disguised = SimpleUploadedFile("photo.png", b"MZ\x90\x00 this is not an image", "image/png")

    assert detect_mime_type(png_upload("anything.bin")) == "image/png"
    assert detect_mime_type(pdf_upload("anything.bin")) == "application/pdf"
    assert detect_mime_type(disguised) != "image/png"


@pytest.mark.django_db
def test_images_and_pdf_are_accepted():
    assert validate_upload(png_upload()) == "image/png"
    assert validate_upload(pdf_upload()) == "application/pdf"


@pytest.mark.django_db
def test_other_file_types_are_rejected_with_a_clear_message():
    upload = SimpleUploadedFile("notes.txt", b"plain text", content_type="text/plain")

    with pytest.raises(RuleViolation) as error:
        validate_upload(upload)

    assert error.value.rule_code == "FILE_TYPE_NOT_ALLOWED"
    assert "notes.txt" in error.value.message
    assert "image (JPG, PNG, WebP) or a PDF" in error.value.message


@pytest.mark.django_db
def test_a_quotation_must_be_a_pdf():
    with pytest.raises(RuleViolation) as error:
        validate_upload(png_upload("quotation.png"), allowed=(PDF_MIME_TYPE,))

    assert "Upload a PDF file" in error.value.message


@pytest.mark.django_db
def test_files_over_the_size_limit_are_rejected():
    settings = SystemSetting.load()
    settings.max_upload_mb = 1
    settings.save()
    too_large = SimpleUploadedFile("big.pdf", b"%PDF-1.4\n" + b"0" * (1024 * 1024 + 1))

    with pytest.raises(RuleViolation) as error:
        validate_upload(too_large)

    assert error.value.rule_code == "FILE_TOO_LARGE"
    assert "1 MB" in error.value.message


def test_thumbnail_is_a_small_webp_copy():
    thumbnail = make_thumbnail(png_upload(size=(1600, 1000)))

    assert thumbnail is not None
    with Image.open(io.BytesIO(thumbnail.read())) as image:
        assert image.format == "WEBP"
        assert image.width <= 640
        assert image.height <= 480


def test_thumbnail_is_skipped_for_files_that_are_not_images():
    assert make_thumbnail(pdf_upload()) is None


def test_stored_names_are_random_and_keep_only_the_extension():
    class FakeDocument:
        project_id = 7

    first = document_upload_path(FakeDocument(), "Client Brief (final).PDF")
    second = document_upload_path(FakeDocument(), "Client Brief (final).PDF")

    assert first.startswith("documents/7/")
    assert first.endswith(".pdf")
    assert "Client" not in first
    assert first != second
