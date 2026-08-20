from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import BinaryIO
from zipfile import BadZipFile, ZipFile

import fitz
import pikepdf
from lxml import etree

_DOCX_MAIN_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
)
_DOCX_DOCUMENT_TAG = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}document"
_ENCRYPTED_FLAG = 0x1
_MAX_ZIP_UNCOMPRESSED_BYTES = 512 * 1024 * 1024
_MAX_ZIP_COMPRESSION_RATIO = 100
_XML_PARSER = etree.XMLParser(
    resolve_entities=False,
    no_network=True,
    load_dtd=False,
    huge_tree=False,
)


@dataclass(frozen=True)
class DocumentValidationResult:
    input_kind: str | None
    rejection_code: str | None = None
    rejection_message: str | None = None

    @property
    def accepted(self) -> bool:
        return self.input_kind is not None


def validate_document(
    content: BinaryIO, filename: str, media_type: str
) -> DocumentValidationResult:
    suffix = PurePosixPath(filename).suffix.lower()
    if (
        suffix == ".docx"
        and media_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        return validate_docx(content)
    if suffix == ".pdf" and media_type == "application/pdf":
        return validate_pdf(content)
    if suffix == ".tex" and media_type in {"text/x-tex", "application/x-tex", "text/plain"}:
        return validate_latex_source(content)
    if suffix == ".zip" and media_type == "application/zip":
        return validate_latex_project(content)
    return _rejected(
        "unsupported_document",
        "LaTeX projects are primary; DOCX is supported only as an import input.",
    )


def validate_docx(content: BinaryIO) -> DocumentValidationResult:
    try:
        content.seek(0)
        with ZipFile(content) as archive:
            entries = archive.infolist()
            unsafe = _unsafe_archive(entries, "DOCX")
            if unsafe is not None:
                return unsafe
            if any(entry.flag_bits & _ENCRYPTED_FLAG for entry in entries):
                return _rejected("encrypted_document", "Encrypted documents cannot be processed.")

            corrupted_entry = archive.testzip()
            if corrupted_entry is not None:
                return _rejected("corrupt_document", "The DOCX archive has an invalid CRC.")

            names = [entry.filename for entry in entries]
            if names.count("[Content_Types].xml") != 1 or names.count("word/document.xml") != 1:
                return _rejected("corrupt_document", "The DOCX package is missing required parts.")

            content_types = etree.fromstring(
                archive.read("[Content_Types].xml"), parser=_XML_PARSER
            )
            document = etree.fromstring(archive.read("word/document.xml"), parser=_XML_PARSER)
            if not _has_docx_main_content_type(content_types) or document.tag != _DOCX_DOCUMENT_TAG:
                return _rejected("corrupt_document", "The DOCX package has invalid required parts.")
    except BadZipFile, EOFError, OSError, RuntimeError, etree.XMLSyntaxError, ValueError:
        return _rejected("corrupt_document", "The DOCX file is corrupt.")

    return DocumentValidationResult(input_kind="docx_import")


def validate_latex_source(content: BinaryIO) -> DocumentValidationResult:
    try:
        content.seek(0)
        source = content.read().decode("utf-8")
    except UnicodeDecodeError, OSError, ValueError:
        return _rejected("invalid_latex_source", "The LaTeX source must be valid UTF-8.")

    if "\x00" in source or "\\documentclass" not in source:
        return _rejected(
            "invalid_latex_source",
            "The LaTeX source must contain a document class and no NUL bytes.",
        )
    return DocumentValidationResult(input_kind="latex_project")


def validate_latex_project(content: BinaryIO) -> DocumentValidationResult:
    try:
        content.seek(0)
        with ZipFile(content) as archive:
            entries = archive.infolist()
            unsafe = _unsafe_archive(entries, "LaTeX project")
            if unsafe is not None:
                return unsafe
            if any(entry.flag_bits & _ENCRYPTED_FLAG for entry in entries):
                return _rejected("encrypted_document", "Encrypted documents cannot be processed.")

            corrupted_entry = archive.testzip()
            if corrupted_entry is not None:
                return _rejected(
                    "corrupt_document", "The LaTeX project archive has an invalid CRC."
                )

            names = [entry.filename for entry in entries if not entry.is_dir()]
            if "main.tex" in names:
                return DocumentValidationResult(input_kind="latex_project")
            tex_names = [name for name in names if name.lower().endswith(".tex")]
            if not tex_names:
                return _rejected(
                    "missing_latex_entrypoint",
                    "The LaTeX project must contain a .tex entrypoint.",
                )
            if len(tex_names) != 1:
                return _rejected(
                    "ambiguous_latex_entrypoint",
                    "The LaTeX project has multiple possible .tex entrypoints.",
                )
    except BadZipFile, EOFError, OSError, RuntimeError, ValueError:
        return _rejected("corrupt_document", "The LaTeX project archive is corrupt.")

    return DocumentValidationResult(input_kind="latex_project")


def validate_pdf(content: BinaryIO) -> DocumentValidationResult:
    try:
        content.seek(0)
        with pikepdf.open(content) as pdf:
            if pdf.is_encrypted:
                return _rejected("encrypted_document", "Encrypted documents cannot be processed.")
    except pikepdf.PasswordError:
        return _rejected("encrypted_document", "Encrypted documents cannot be processed.")
    except pikepdf.PdfError, OSError, ValueError:
        return _rejected("corrupt_document", "The PDF file is corrupt.")

    try:
        content.seek(0)
        document = fitz.open(stream=content.read(), filetype="pdf")
        try:
            text_length = 0
            has_images = False
            for page in document:
                text_length += len(page.get_text("text").strip())
                has_images = has_images or bool(page.get_images(full=True))
        finally:
            document.close()
    except fitz.FileDataError, RuntimeError, OSError, ValueError:
        return _rejected("corrupt_document", "The PDF file is corrupt.")

    if text_length > 0:
        return DocumentValidationResult(input_kind="text_pdf")
    if has_images:
        return DocumentValidationResult(input_kind="scanned_pdf")
    return _rejected(
        "corrupt_document",
        "The PDF has no extractable text or page images.",
    )


def _unsafe_archive(entries: list[object], document_type: str) -> DocumentValidationResult | None:
    total_uncompressed = 0
    seen_names: set[str] = set()
    for entry in entries:
        filename = entry.filename
        if (
            not filename
            or filename.startswith(("/", "\\"))
            or (len(filename) > 2 and filename[1:3] == ":/")
            or "\\" in filename
            or "\x00" in filename
            or any(part == ".." for part in filename.split("/"))
            or filename in seen_names
            or _is_symlink(entry)
        ):
            return _rejected("unsafe_archive", f"The {document_type} archive has unsafe entries.")
        seen_names.add(filename)
        if entry.is_dir():
            continue
        total_uncompressed += entry.file_size
        if total_uncompressed > _MAX_ZIP_UNCOMPRESSED_BYTES:
            return _rejected(
                "unsafe_archive", f"The {document_type} archive expands beyond the allowed size."
            )
        if entry.file_size and entry.compress_size == 0:
            return _rejected(
                "unsafe_archive",
                f"The {document_type} archive has an unsafe compression ratio.",
            )
        if (
            entry.compress_size
            and entry.file_size / entry.compress_size > _MAX_ZIP_COMPRESSION_RATIO
        ):
            return _rejected(
                "unsafe_archive",
                f"The {document_type} archive has an unsafe compression ratio.",
            )
    return None


def _is_symlink(entry: object) -> bool:
    return (entry.external_attr >> 16) & 0o170000 == 0o120000


def _has_docx_main_content_type(content_types: etree._Element) -> bool:
    return any(
        element.get("PartName") == "/word/document.xml"
        and element.get("ContentType") == _DOCX_MAIN_CONTENT_TYPE
        for element in content_types
    )


def _rejected(code: str, message: str) -> DocumentValidationResult:
    return DocumentValidationResult(
        input_kind=None,
        rejection_code=code,
        rejection_message=message,
    )
