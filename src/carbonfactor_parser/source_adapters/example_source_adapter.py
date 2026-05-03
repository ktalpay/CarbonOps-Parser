"""Artificial source-specific adapter skeleton."""

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
class ExampleSourceAdapter:
    """Discover artificial local files using source-specific filters."""

    directory_path: str | Path
    source_family: SourceFamily
    source_key: str = "example_source"
    allowed_extensions: Iterable[str] | str | None = None
    allowed_name_prefixes: Iterable[str] | str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "directory_path", Path(self.directory_path))
        if isinstance(self.allowed_extensions, str):
            allowed_extensions = (self.allowed_extensions,)
        else:
            allowed_extensions = self.allowed_extensions
        if allowed_extensions is not None:
            object.__setattr__(
                self,
                "allowed_extensions",
                tuple(
                    _normalize_extension(extension)
                    for extension in allowed_extensions
                ),
            )

        if isinstance(self.allowed_name_prefixes, str):
            allowed_name_prefixes = (self.allowed_name_prefixes,)
        else:
            allowed_name_prefixes = self.allowed_name_prefixes
        if allowed_name_prefixes is not None:
            object.__setattr__(
                self,
                "allowed_name_prefixes",
                tuple(allowed_name_prefixes),
            )

    def discover(self) -> AdapterDiscoveryResult:
        if not self.directory_path.is_dir():
            return AdapterDiscoveryResult(
                documents=(),
                warnings=(
                    f"Example source directory not found: {self.directory_path}",
                ),
            )

        documents = tuple(
            SourceDocument(
                source_family=self.source_family,
                source_name=f"{self.source_key}:{file_path.name}",
                file_reference=str(file_path),
            )
            for file_path in sorted(
                self.directory_path.iterdir(),
                key=lambda path: path.name,
            )
            if file_path.is_file() and self._allows_file(file_path)
        )
        return AdapterDiscoveryResult(documents=documents, warnings=())

    def parse(self, document: SourceDocument) -> AdapterParseResult:
        return AdapterParseResult(
            records=(),
            rejected_records=(),
            warnings=(),
            normalization_notes=(),
        )

    def _allows_file(self, file_path: Path) -> bool:
        return self._allows_extension(file_path) and self._allows_name(file_path)

    def _allows_extension(self, file_path: Path) -> bool:
        if self.allowed_extensions is None:
            return True
        return file_path.suffix.lower() in self.allowed_extensions

    def _allows_name(self, file_path: Path) -> bool:
        if self.allowed_name_prefixes is None:
            return True
        return file_path.name.startswith(tuple(self.allowed_name_prefixes))


def _normalize_extension(extension: str) -> str:
    normalized = extension.strip().lower()
    if not normalized:
        return normalized
    if normalized.startswith("."):
        return normalized
    return f".{normalized}"
