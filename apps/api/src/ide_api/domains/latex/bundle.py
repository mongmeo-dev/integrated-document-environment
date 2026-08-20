from __future__ import annotations

import stat
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
from pathlib import PurePosixPath
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile, ZipInfo

MAX_ENTRIES = 10_000
MAX_UNCOMPRESSED_BYTES = 512 * 1024 * 1024
MAX_COMPRESSION_RATIO = 100


@dataclass(frozen=True, slots=True)
class LatexBundle:
    data: bytes
    entrypoint: str
    source: str
    files: tuple[str, ...]
    sha256: str


class LatexBundleError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def _error(code: str, message: str) -> LatexBundleError:
    return LatexBundleError(code, message)


def _validate_filename(filename: str) -> None:
    if not isinstance(filename, str) or not filename or "\x00" in filename:
        raise _error("unsafe_archive", "Archive contains an invalid file name.")
    try:
        filename.encode("utf-8")
    except UnicodeEncodeError as error:
        raise _error("unsafe_archive", "Archive contains a non-UTF-8 file name.") from error
    if "\\" in filename or filename.startswith("/"):
        raise _error("unsafe_archive", "Archive contains an unsafe file name.")

    path = PurePosixPath(filename)
    if any(part in {"", ".", ".."} for part in path.parts) or ":" in path.parts[0]:
        raise _error("unsafe_archive", "Archive contains an unsafe file name.")


def _validate_source(source: bytes) -> str:
    try:
        decoded = source.decode("utf-8")
    except UnicodeDecodeError as error:
        raise _error("invalid_source", "LaTeX source must be UTF-8.") from error
    if "\x00" in decoded or "\\documentclass" not in decoded:
        raise _error("invalid_source", "LaTeX source must contain \\documentclass.")
    return decoded


def _select_entrypoint(file_names: tuple[str, ...], requested: str | None = None) -> str:
    if requested is not None:
        _validate_filename(requested)
        if requested not in file_names:
            raise _error(
                "invalid_entrypoint", "The LaTeX entrypoint is not present in the archive."
            )
        return requested
    if "main.tex" in file_names:
        return "main.tex"
    tex_files = tuple(name for name in file_names if name.endswith(".tex"))
    if len(tex_files) != 1:
        raise _error(
            "ambiguous_entrypoint", "Archive must contain main.tex or exactly one .tex file."
        )
    return tex_files[0]


def _bundle(data: bytes, files: Mapping[str, bytes], entrypoint: str) -> LatexBundle:
    names = tuple(sorted(files))
    source = _validate_source(files[entrypoint])
    return LatexBundle(
        data=data,
        entrypoint=entrypoint,
        source=source,
        files=names,
        sha256=sha256(data).hexdigest(),
    )


def build_latex_bundle(files: Mapping[str, bytes], entrypoint: str = "main.tex") -> LatexBundle:
    if len(files) > MAX_ENTRIES:
        raise _error("zip_bomb", "Archive contains too many files.")
    if not files:
        raise _error("invalid_bundle", "LaTeX archive cannot be empty.")

    normalized: dict[str, bytes] = {}
    total_size = 0
    for filename, content in files.items():
        _validate_filename(filename)
        if not isinstance(content, bytes):
            raise _error("invalid_bundle", "LaTeX archive content must be bytes.")
        total_size += len(content)
        if total_size > MAX_UNCOMPRESSED_BYTES:
            raise _error("zip_bomb", "Archive exceeds the uncompressed size limit.")
        normalized[filename] = content

    names = tuple(sorted(normalized))
    selected_entrypoint = _select_entrypoint(names, entrypoint)
    output = BytesIO()
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for filename in names:
            info = ZipInfo(filename, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, normalized[filename])
    data = output.getvalue()
    with ZipFile(BytesIO(data)) as archive:
        for info in archive.infolist():
            if info.file_size and (
                not info.compress_size
                or info.file_size / info.compress_size > MAX_COMPRESSION_RATIO
            ):
                raise _error("zip_bomb", "Archive exceeds the compression ratio limit.")
    return _bundle(data, normalized, selected_entrypoint)


def build_single_file_bundle(source: bytes, filename: str = "main.tex") -> LatexBundle:
    return build_latex_bundle({filename: source}, entrypoint=filename)


def read_latex_bundle(data: bytes) -> LatexBundle:
    try:
        with ZipFile(BytesIO(data)) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_ENTRIES:
                raise _error("zip_bomb", "Archive contains too many files.")

            files: dict[str, bytes] = {}
            total_size = 0
            for info in infos:
                _validate_filename(info.filename)
                if (
                    any(ord(character) > 127 for character in info.filename)
                    and not info.flag_bits & 0x800
                ):
                    raise _error("unsafe_archive", "Archive contains a non-UTF-8 file name.")
                if info.filename in files:
                    raise _error("duplicate_entry", "Archive contains duplicate file names.")
                if info.flag_bits & 0x1:
                    raise _error("unsafe_archive", "Archive contains an encrypted file.")
                mode = info.external_attr >> 16
                file_type = stat.S_IFMT(mode)
                if info.is_dir() or stat.S_ISLNK(mode) or file_type not in {0, stat.S_IFREG}:
                    raise _error("unsafe_archive", "Archive contains a non-regular file.")
                if info.file_size > MAX_UNCOMPRESSED_BYTES - total_size:
                    raise _error("zip_bomb", "Archive exceeds the uncompressed size limit.")
                if info.file_size and (
                    not info.compress_size
                    or info.file_size / info.compress_size > MAX_COMPRESSION_RATIO
                ):
                    raise _error("zip_bomb", "Archive exceeds the compression ratio limit.")
                total_size += info.file_size
                files[info.filename] = archive.read(info)
    except LatexBundleError:
        raise
    except (BadZipFile, OSError, RuntimeError) as error:
        raise _error("invalid_bundle", "LaTeX bundle must be a valid ZIP archive.") from error

    if not files:
        raise _error("invalid_bundle", "LaTeX archive cannot be empty.")
    names = tuple(sorted(files))
    entrypoint = _select_entrypoint(names)
    return _bundle(data, files, entrypoint)


def replace_entrypoint_source(bundle: LatexBundle, source: str) -> LatexBundle:
    if not isinstance(source, str):
        raise _error("invalid_source", "LaTeX source must be text.")
    current = read_latex_bundle(bundle.data)
    files: dict[str, bytes]
    with ZipFile(BytesIO(current.data)) as archive:
        files = {name: archive.read(name) for name in current.files}
    files[current.entrypoint] = source.encode("utf-8")
    return build_latex_bundle(files, entrypoint=current.entrypoint)
