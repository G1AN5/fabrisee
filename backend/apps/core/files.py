"""File handling shared by documents, quotations and design revisions.

Uploads are images (JPEG, PNG, WebP) or PDF. The type is checked from the file content,
not from the name, and files are stored under random names; the original name is kept in
the database only.
"""

import io
import mimetypes
import uuid
from pathlib import PurePosixPath

import filetype
from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageOps

from apps.core.exceptions import RuleViolation

IMAGE_MIME_TYPES = ("image/jpeg", "image/png", "image/webp")
PDF_MIME_TYPE = "application/pdf"
ALLOWED_MIME_TYPES = (*IMAGE_MIME_TYPES, PDF_MIME_TYPE)
EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
}
THUMBNAIL_SIZE = (640, 480)


def _random_name(filename: str) -> str:
    extension = PurePosixPath(filename or "").suffix.lower()[:10]
    return f"{uuid.uuid4().hex}{extension}"


def document_upload_path(instance, filename: str) -> str:
    return f"documents/{instance.project_id}/{_random_name(filename)}"


def quotation_upload_path(instance, filename: str) -> str:
    return f"quotations/{instance.project_id}/{_random_name(filename)}"


def revision_upload_path(instance, filename: str) -> str:
    return f"designs/{instance.project_id}/{_random_name(filename)}"


def thumbnail_upload_path(instance, filename: str) -> str:
    return f"thumbnails/{instance.project_id}/{_random_name(filename)}"


def detect_mime_type(file) -> str | None:
    """Return the MIME type found in the first bytes of `file`, or None if unknown."""
    position = file.tell() if hasattr(file, "tell") else None
    if hasattr(file, "seek"):
        file.seek(0)
    head = file.read(8192)
    if position is not None:
        file.seek(position)
    kind = filetype.guess(head)
    return kind.mime if kind else None


def guess_content_type(name: str) -> str:
    return mimetypes.guess_type(name)[0] or "application/octet-stream"


def is_image(content_type: str) -> bool:
    return content_type in IMAGE_MIME_TYPES


def validate_upload(file, *, allowed: tuple[str, ...] = ALLOWED_MIME_TYPES, field: str = "file"):
    """Check the content type and the size of an uploaded file.

    Returns the detected MIME type. Raises `RuleViolation` with a plain-language message.
    """
    from apps.core.models import SystemSetting

    limit_mb = min(SystemSetting.load().max_upload_mb, settings.MAX_UPLOAD_MB_CEILING)
    name = getattr(file, "name", "The file") or "The file"
    if file.size > limit_mb * 1024 * 1024:
        raise RuleViolation(
            "FILE_TOO_LARGE",
            f"{name} is larger than the {limit_mb} MB limit. Upload a smaller file.",
            fields={field: f"Files can be up to {limit_mb} MB."},
        )
    mime_type = detect_mime_type(file)
    if mime_type not in allowed:
        if allowed == (PDF_MIME_TYPE,):
            accepted = "a PDF file"
        elif PDF_MIME_TYPE in allowed:
            accepted = "an image (JPG, PNG, WebP) or a PDF file"
        else:
            accepted = "an image (JPG, PNG, WebP)"
        raise RuleViolation(
            "FILE_TYPE_NOT_ALLOWED",
            f"{name} cannot be uploaded. Upload {accepted}.",
            fields={field: f"Upload {accepted}."},
        )
    return mime_type


def make_thumbnail(file) -> ContentFile | None:
    """Return a small WebP copy of an image file, or None if `file` is not an image."""
    try:
        file.seek(0)
        with Image.open(file) as image:
            image = ImageOps.exif_transpose(image)
            image.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            if image.mode not in ("RGB", "RGBA"):
                image = image.convert("RGBA" if "transparency" in image.info else "RGB")
            buffer = io.BytesIO()
            image.save(buffer, format="WEBP", quality=82, method=4)
    except (OSError, ValueError):
        return None
    finally:
        file.seek(0)
    return ContentFile(buffer.getvalue(), name="thumbnail.webp")
