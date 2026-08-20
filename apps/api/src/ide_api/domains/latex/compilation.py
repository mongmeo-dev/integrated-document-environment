from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory

from ide_api.domains.latex.bundle import LatexBundle, read_latex_bundle

MAX_LOG_BYTES = 64 * 1024


@dataclass(frozen=True, slots=True)
class LatexCompilationResult:
    pdf: bytes
    log: str


class LatexCompilationError(RuntimeError):
    def __init__(self, code: str, message: str, log: str = "") -> None:
        self.code = code
        self.message = message
        self.log = log
        super().__init__(message)


def _log_bytes(value: bytes | str | None) -> bytes:
    if value is None:
        return b""
    if isinstance(value, bytes):
        return value
    return value.encode("utf-8", errors="replace")


def _bounded_log(*parts: bytes | str | None) -> str:
    return b"".join(_log_bytes(part) for part in parts)[:MAX_LOG_BYTES].decode(
        "utf-8", errors="replace"
    )


@dataclass(frozen=True, slots=True)
class TectonicCompiler:
    command: str = "tectonic"
    timeout_seconds: int = 120
    only_cached: bool = False

    def compile(self, bundle: LatexBundle) -> LatexCompilationResult:
        try:
            validated = read_latex_bundle(bundle.data)
        except Exception as error:
            raise LatexCompilationError("compilation_failed", "LaTeX bundle is invalid.") from error

        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project_directory = root / "project"
            output_directory = root / "output"
            project_directory.mkdir()
            output_directory.mkdir()
            self._materialize(validated, project_directory)
            arguments = [
                self.command,
                "--untrusted",
                "--keep-logs",
                "--outdir",
                str(output_directory),
                validated.entrypoint,
            ]
            if self.only_cached:
                arguments.insert(2, "--only-cached")
            try:
                completed = subprocess.run(
                    arguments,
                    cwd=project_directory,
                    check=False,
                    capture_output=True,
                    timeout=self.timeout_seconds,
                )
            except FileNotFoundError as error:
                raise LatexCompilationError(
                    "compiler_unavailable", "Tectonic compiler is unavailable."
                ) from error
            except subprocess.TimeoutExpired as error:
                log = _bounded_log(error.stdout, error.stderr)
                raise LatexCompilationError(
                    "compilation_timeout", "LaTeX compilation timed out.", log
                ) from error

            output_name = PurePosixPath(validated.entrypoint).with_suffix("")
            log_paths = (
                output_directory / output_name.with_suffix(".log"),
                output_directory / f"{output_name.name}.log",
            )
            generated_log = next(
                (path.read_bytes() for path in log_paths if path.is_file()),
                None,
            )
            log = _bounded_log(completed.stdout, completed.stderr, generated_log)
            if completed.returncode != 0:
                raise LatexCompilationError("compilation_failed", "LaTeX compilation failed.", log)

            pdf_paths = (
                output_directory / output_name.with_suffix(".pdf"),
                output_directory / f"{output_name.name}.pdf",
            )
            pdf_path = next((path for path in pdf_paths if path.is_file()), None)
            if pdf_path is None:
                raise LatexCompilationError(
                    "missing_compiled_pdf",
                    "LaTeX compilation did not produce a PDF.",
                    log,
                )
            return LatexCompilationResult(pdf=pdf_path.read_bytes(), log=log)

    @staticmethod
    def _materialize(bundle: LatexBundle, project_directory: Path) -> None:
        from io import BytesIO
        from zipfile import ZipFile

        with ZipFile(BytesIO(bundle.data)) as archive:
            for filename in bundle.files:
                destination = project_directory / PurePosixPath(filename)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(archive.read(filename))
