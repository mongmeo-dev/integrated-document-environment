from __future__ import annotations

from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import fitz
import pikepdf

from ide_api.domains.documents.validation import validate_docx, validate_pdf

SAMPLE_DOCS = Path(__file__).parents[3] / "fixture" / "sample-docs"
_CONTENT_TYPES = (
    b'<?xml version="1.0" encoding="UTF-8"?>'
    b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    b'<Override PartName="/word/document.xml" '
    b'ContentType="application/vnd.openxmlformats-officedocument.'
    b'wordprocessingml.document.main+xml"/>'
    b"</Types>"
)
_DOCUMENT = b"""<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body/></w:document>"""


def test_all_sample_docx_files_are_editable() -> None:
    paths = sorted(SAMPLE_DOCS.glob("*.docx"))
    assert len(paths) == 7

    for path in paths:
        with path.open("rb") as source:
            result = validate_docx(source)

        assert result.input_kind == "editable_docx"
        assert result.rejection_code is None


def test_rejects_corrupt_docx() -> None:
    result = validate_docx(BytesIO(b"not a zip archive"))

    assert result.input_kind is None
    assert result.rejection_code == "corrupt_document"


def test_rejects_docx_with_encryption_flag() -> None:
    encrypted = bytearray(_docx_bytes())
    _set_zip_encryption_flags(encrypted)

    result = validate_docx(BytesIO(encrypted))

    assert result.input_kind is None
    assert result.rejection_code == "encrypted_document"


def test_rejects_zip_bomb_docx() -> None:
    result = validate_docx(BytesIO(_docx_bytes(extra=("word/bomb.bin", b"x" * (2 * 1024 * 1024)))))

    assert result.input_kind is None
    assert result.rejection_code == "unsafe_archive"


def test_classifies_text_and_scanned_pdf() -> None:
    text_document = fitz.open()
    text_page = text_document.new_page()
    text_page.insert_text((72, 72), "GMP validation evidence")
    text_result = validate_pdf(BytesIO(text_document.tobytes()))
    text_document.close()

    image_document = fitz.open()
    image_page = image_document.new_page()
    pixmap = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 1, 1), 0)
    pixmap.clear_with(0)
    image_page.insert_image(
        fitz.Rect(0, 0, 20, 20),
        stream=pixmap.tobytes("png"),
    )
    image_result = validate_pdf(BytesIO(image_document.tobytes()))
    image_document.close()

    assert text_result.input_kind == "text_pdf"
    assert image_result.input_kind == "scanned_pdf"


def test_rejects_encrypted_pdf() -> None:
    document = fitz.open()
    document.new_page()
    plain = BytesIO(document.tobytes())
    document.close()
    encrypted = BytesIO()
    with pikepdf.open(plain) as pdf:
        pdf.save(
            encrypted,
            encryption=pikepdf.Encryption(owner="owner", user="user"),
        )

    result = validate_pdf(encrypted)
    assert result.rejection_code == "encrypted_document"


def _docx_bytes(extra: tuple[str, bytes] | None = None) -> bytes:
    content = BytesIO()
    with ZipFile(content, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _CONTENT_TYPES)
        archive.writestr("word/document.xml", _DOCUMENT)
        if extra is not None:
            archive.writestr(*extra)
    return content.getvalue()


def _set_zip_encryption_flags(content: bytearray) -> None:
    for signature, flag_offset in ((b"PK\x03\x04", 6), (b"PK\x01\x02", 8)):
        offset = 0
        while (found := content.find(signature, offset)) != -1:
            flags = int.from_bytes(content[found + flag_offset : found + flag_offset + 2], "little")
            content[found + flag_offset : found + flag_offset + 2] = (flags | 1).to_bytes(
                2, "little"
            )
            offset = found + len(signature)
