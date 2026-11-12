"""Small valid files for tests."""

import io

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
    b"trailer<</Root 1 0 R>>\n%%EOF\n"
)


def png_bytes(size: tuple[int, int] = (64, 48), color: str = "#1E40AF") -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format="PNG")
    return buffer.getvalue()


def png_upload(name: str = "render.png", **kwargs) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, png_bytes(**kwargs), content_type="image/png")


def pdf_upload(name: str = "quotation.pdf") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, MINIMAL_PDF, content_type="application/pdf")
