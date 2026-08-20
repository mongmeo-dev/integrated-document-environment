from __future__ import annotations

import stat
import subprocess
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

import pytest

from ide_api.domains.latex.bundle import (
    LatexBundleError,
    build_latex_bundle,
    build_single_file_bundle,
    read_latex_bundle,
    replace_entrypoint_source,
)
from ide_api.domains.latex.compilation import LatexCompilationError, TectonicCompiler
from ide_api.domains.latex.conversion import DocxConversionError, PandocDocxConverter


def _archive(entries: list[tuple[str, bytes]], *, compression: int = ZIP_DEFLATED) -> bytes:
    output = BytesIO()
    with ZipFile(output, "w", compression=compression) as archive:
        for name, data in entries:
            archive.writestr(name, data)
    return output.getvalue()


def test_bundle_build_read_and_replace_are_canonical() -> None:
    bundle = build_latex_bundle(
        {"images/logo.txt": b"logo", "main.tex": b"\\documentclass{article}\nOld"}
    )

    assert bundle.files == ("images/logo.txt", "main.tex")
    assert read_latex_bundle(bundle.data) == bundle

    replaced = replace_entrypoint_source(bundle, "\\documentclass{article}\nNew")

    assert replaced.source.endswith("New")
    assert replaced.sha256 != bundle.sha256
    assert read_latex_bundle(replaced.data).source.endswith("New")


@pytest.mark.parametrize(
    ("data", "code"),
    [
        (_archive([("../main.tex", b"\\documentclass{article}")]), "unsafe_archive"),
        (
            _archive(
                [
                    ("first.tex", b"\\documentclass{article}"),
                    ("second.tex", b"\\documentclass{article}"),
                ]
            ),
            "ambiguous_entrypoint",
        ),
        (_archive([("main.tex", b"not latex")]), "invalid_source"),
        (
            _archive([("main.tex", b"\\documentclass{article}"), ("main.tex", b"x")]),
            "duplicate_entry",
        ),
        (_archive([("main.tex", b"\\documentclass{article}" + b"0" * 10_000)]), "zip_bomb"),
    ],
)
def test_read_bundle_rejects_unsafe_or_invalid_archives(data: bytes, code: str) -> None:
    with pytest.raises(LatexBundleError) as error:
        read_latex_bundle(data)

    assert error.value.code == code


def test_read_bundle_rejects_symlink() -> None:
    output = BytesIO()
    with ZipFile(output, "w") as archive:
        info = ZipInfo("main.tex")
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(info, b"\\documentclass{article}")

    with pytest.raises(LatexBundleError, match="non-regular") as error:
        read_latex_bundle(output.getvalue())

    assert error.value.code == "unsafe_archive"


def test_single_file_bundle_requires_valid_source() -> None:
    with pytest.raises(LatexBundleError) as error:
        build_single_file_bundle(b"\\begin{document}")

    assert error.value.code == "invalid_source"


def test_pandoc_converter_packages_generated_files() -> None:
    def convert(arguments: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        root = Path(kwargs["cwd"])
        (root / "main.tex").write_bytes(b"\\documentclass{article}")
        (root / "media").mkdir()
        (root / "media" / "image.png").write_bytes(b"image")
        return subprocess.CompletedProcess(arguments, 0, b"", b"")

    with patch("ide_api.domains.latex.conversion.subprocess.run", side_effect=convert) as run:
        bundle = PandocDocxConverter().convert(b"docx")

    assert bundle.files == ("main.tex", "media/image.png")
    assert run.call_args.args[0][1:5] == [
        "--from=docx",
        "--to=latex",
        "--standalone",
        "--extract-media=media",
    ]


@pytest.mark.parametrize(
    ("side_effect", "code"),
    [
        (subprocess.CompletedProcess(["pandoc"], 1, b"", b"error"), "conversion_failed"),
        (subprocess.TimeoutExpired(["pandoc"], 120), "conversion_timeout"),
        (FileNotFoundError(), "converter_unavailable"),
    ],
)
def test_pandoc_converter_reports_stable_errors(side_effect: object, code: str) -> None:
    patch_kwargs = (
        {"return_value": side_effect}
        if isinstance(side_effect, subprocess.CompletedProcess)
        else {"side_effect": side_effect}
    )
    with (
        patch("ide_api.domains.latex.conversion.subprocess.run", **patch_kwargs),
        pytest.raises(DocxConversionError) as error,
    ):
        PandocDocxConverter().convert(b"docx")

    assert error.value.code == code


def test_tectonic_compiler_returns_pdf_and_bounded_log() -> None:
    bundle = build_single_file_bundle(b"\\documentclass{article}")

    def compile_tex(arguments: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        output = Path(arguments[arguments.index("--outdir") + 1])
        (output / "main.pdf").write_bytes(b"%PDF")
        (output / "main.log").write_bytes(b"log")
        return subprocess.CompletedProcess(arguments, 0, b"stdout", b"stderr")

    with patch("ide_api.domains.latex.compilation.subprocess.run", side_effect=compile_tex) as run:
        result = TectonicCompiler(only_cached=True).compile(bundle)

    assert result.pdf == b"%PDF"
    assert result.log == "stdoutstderrlog"
    assert run.call_args.args[0][1:5] == [
        "--untrusted",
        "--only-cached",
        "--keep-logs",
        "--outdir",
    ]


@pytest.mark.parametrize(
    ("side_effect", "code"),
    [
        (subprocess.CompletedProcess(["tectonic"], 1, b"out", b"err"), "compilation_failed"),
        (
            subprocess.TimeoutExpired(["tectonic"], 120, output=b"out", stderr=b"err"),
            "compilation_timeout",
        ),
        (FileNotFoundError(), "compiler_unavailable"),
    ],
)
def test_tectonic_compiler_reports_stable_errors(side_effect: object, code: str) -> None:
    bundle = build_single_file_bundle(b"\\documentclass{article}")
    patch_kwargs = (
        {"return_value": side_effect}
        if isinstance(side_effect, subprocess.CompletedProcess)
        else {"side_effect": side_effect}
    )
    with (
        patch("ide_api.domains.latex.compilation.subprocess.run", **patch_kwargs),
        pytest.raises(LatexCompilationError) as error,
    ):
        TectonicCompiler().compile(bundle)

    assert error.value.code == code


def test_tectonic_compiler_requires_pdf() -> None:
    bundle = build_single_file_bundle(b"\\documentclass{article}")
    with (
        patch(
            "ide_api.domains.latex.compilation.subprocess.run",
            return_value=subprocess.CompletedProcess(["tectonic"], 0, b"", b""),
        ),
        pytest.raises(LatexCompilationError) as error,
    ):
        TectonicCompiler().compile(bundle)

    assert error.value.code == "missing_compiled_pdf"
