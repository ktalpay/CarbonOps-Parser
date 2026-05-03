"""Local file source adapter skeleton."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from carbonfactor_parser.source_adapters.contracts import (
    AdapterDiscoveryResult,
    AdapterParseResult,
    SourceDocument,
    SourceFamily,
)


@dataclass(frozen=True)
class LocalFileSourceAdapter:
    """Discover local files without parsing or ingesting them."""

    directory_path: str | Path
    source_family: SourceFamily = SourceFamily.GHG_PROTOCOL
    allowed_extensions: Iterable[str] | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "directory_path", Path(self.directory_path))
        if self.allowed_extensions is not None:
            allowed_extensions = self.allowed_extensions
            if isinstance(allowed_extensions, str):
                allowed_extensions = (allowed_extensions,)
            object.__setattr__(
                self,
                "allowed_extensions",
                tuple(
                    _normalize_extension(extension)
                    for extension in allowed_extensions
                ),
            )

    def discover(self) -> AdapterDiscoveryResult:
        if not self.directory_path.is_dir():
            return AdapterDiscoveryResult(
                documents=(),
                warnings=(
                    f"Local source directory not found: {self.directory_path}",
                ),
            )

        documents = tuple(
            SourceDocument(
                source_family=self.source_family,
                source_name=file_path.name,
                file_reference=str(file_path),
            )
            for file_path in sorted(
                self.directory_path.iterdir(),
                key=lambda path: path.name,
            )
            if file_path.is_file() and self._allows_extension(file_path)
        )
        return AdapterDiscoveryResult(documents=documents, warnings=())

    def parse(self, document: SourceDocument) -> AdapterParseResult:
        return AdapterParseResult(
            records=(),
            rejected_records=(),
            warnings=(),
            normalization_notes=(),
        )

    def _allows_extension(self, file_path: Path) -> bool:
        if self.allowed_extensions is None:
            return True
        return file_path.suffix.lower() in self.allowed_extensions


def _normalize_extension(extension: str) -> str:
    normalized = extension.strip().lower()
    if not normalized:
        return normalized
    if normalized.startswith("."):
        return normalized
    return f".{normalized}"
