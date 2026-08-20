from __future__ import annotations

import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from ide_api.domains.latex.bundle import LatexBundle, build_latex_bundle


class DocxConversionError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class PandocDocxConverter:
    command: str = "pandoc"
    timeout_seconds: int = 120

    def convert(self, docx_bytes: bytes) -> LatexBundle:
        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            input_path = root / "input.docx"
            output_path = root / "main.tex"
            input_path.write_bytes(docx_bytes)
            arguments = [
                self.command,
                "--from=docx",
                "--to=latex",
                "--standalone",
                "--extract-media=media",
                "--output",
                "main.tex",
                "--variable",
                "mainfont:Noto Sans CJK KR",
                "--variable",
                "sansfont:Noto Sans CJK KR",
                "input.docx",
            ]
            try:
                completed = subprocess.run(
                    arguments,
                    cwd=root,
                    check=False,
                    capture_output=True,
                    timeout=self.timeout_seconds,
                )
            except FileNotFoundError as error:
                raise DocxConversionError(
                    "converter_unavailable", "Pandoc converter is unavailable."
                ) from error
            except subprocess.TimeoutExpired as error:
                raise DocxConversionError(
                    "conversion_timeout", "Pandoc conversion timed out."
                ) from error

            if completed.returncode != 0:
                raise DocxConversionError("conversion_failed", "Pandoc conversion failed.")
            if not output_path.is_file():
                raise DocxConversionError(
                    "conversion_failed", "Pandoc conversion did not produce LaTeX output."
                )

            files: dict[str, bytes] = {}
            for path in sorted(root.rglob("*")):
                if path == input_path:
                    continue
                status = path.lstat()
                if stat.S_ISREG(status.st_mode):
                    files[path.relative_to(root).as_posix()] = path.read_bytes()
            try:
                return build_latex_bundle(files)
            except Exception as error:
                raise DocxConversionError(
                    "conversion_failed", "Pandoc produced an invalid LaTeX project."
                ) from error
