"""Runtime-passive bridge from source artifacts to parser inputs."""

from __future__ import annotations

from dataclasses import dataclass

from carbonfactor_parser.parsers.adapter_registry_contract import (
    Phase1ParserAdapterRegistry,
    get_phase1_parser_adapter_by_source_family,
)
from carbonfactor_parser.parsers.input_artifact_contract import (
    ParserInputArtifact,
    create_phase1_parser_input_artifact,
    validate_parser_input_artifact,
)
from carbonfactor_parser.source_acquisition.download_artifact_contract import (
    SourceDownloadArtifact,
    SourceDownloadArtifactResult,
    create_phase1_source_download_artifacts,
    validate_source_download_artifact,
)


@dataclass(frozen=True)
class SourceArtifactParserInputBridgeEntry:
    """Metadata-only bridge entry for one source artifact parser input."""

    source_family: str
    source_key: str
    parser_key: str
    source_artifact_id: str
    parser_input_artifact_id: str
    artifact_kind: str
    artifact_reference: str
    source_artifact: SourceDownloadArtifact
    parser_input_artifact: ParserInputArtifact
    original_filename: str | None = None
    display_name: str | None = None
    content_type: str | None = None
    extension: str | None = None
    checksum_sha256: str | None = None
    document_year: int | None = None
    reporting_year: int | None = None


@dataclass(frozen=True)
class SourceArtifactParserInputBridgeResult:
    """Deterministic collection of source artifact parser input bridges."""

    entries: tuple[SourceArtifactParserInputBridgeEntry, ...]

    @property
    def entry_count(self) -> int:
        return len(self.entries)

    @property
    def source_keys(self) -> tuple[str, ...]:
        return tuple(entry.source_key for entry in self.entries)

    @property
    def parser_input_artifacts(self) -> tuple[ParserInputArtifact, ...]:
        return tuple(entry.parser_input_artifact for entry in self.entries)


@dataclass(frozen=True)
class SourceArtifactParserInputBridgeValidationIssue:
    """Validation issue for source artifact parser input bridge metadata."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class SourceArtifactParserInputBridgeValidationResult:
    """Structural validation result for source artifact parser input bridges."""

    issues: tuple[SourceArtifactParserInputBridgeValidationIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


def create_source_artifact_parser_input_bridge_entry(
    source_artifact: SourceDownloadArtifact,
    *,
    parser_input_artifact_id: str | None = None,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> SourceArtifactParserInputBridgeEntry:
    """Create parser input metadata from source artifact metadata only."""

    descriptor = get_phase1_parser_adapter_by_source_family(
        source_artifact.source_family,
        registry,
    )
    if descriptor is None:
        raise ValueError(
            "source_family is not registered for a Phase 1 parser adapter."
        )

    parser_input = create_phase1_parser_input_artifact(
        source_family=source_artifact.source_family,
        artifact_reference=source_artifact.local_reference,
        original_filename=source_artifact.original_filename,
        display_name=source_artifact.display_name,
        checksum_sha256=source_artifact.checksum_sha256,
        content_type=source_artifact.content_type,
        extension=source_artifact.extension,
        reporting_year=source_artifact.reporting_year,
        registry=registry,
    )

    return SourceArtifactParserInputBridgeEntry(
        source_family=source_artifact.source_family,
        source_key=source_artifact.source_key,
        parser_key=descriptor.parser_key,
        source_artifact_id=source_artifact.artifact_id,
        parser_input_artifact_id=(
            parser_input_artifact_id
            if parser_input_artifact_id is not None
            else f"parser_input_from_{source_artifact.artifact_id}"
        ),
        artifact_kind=source_artifact.artifact_kind,
        artifact_reference=source_artifact.local_reference,
        source_artifact=source_artifact,
        parser_input_artifact=parser_input,
        original_filename=source_artifact.original_filename,
        display_name=source_artifact.display_name,
        content_type=source_artifact.content_type,
        extension=source_artifact.extension,
        checksum_sha256=source_artifact.checksum_sha256,
        document_year=source_artifact.document_year,
        reporting_year=source_artifact.reporting_year,
    )


def create_phase1_source_artifact_parser_input_bridge(
    artifacts: SourceDownloadArtifactResult | None = None,
    *,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> SourceArtifactParserInputBridgeResult:
    """Create deterministic Phase 1 source artifact parser input bridges."""

    active_artifacts = (
        create_phase1_source_download_artifacts()
        if artifacts is None
        else artifacts
    )
    return SourceArtifactParserInputBridgeResult(
        entries=tuple(
            create_source_artifact_parser_input_bridge_entry(
                artifact,
                registry=registry,
            )
            for artifact in active_artifacts.artifacts
        )
    )


def validate_source_artifact_parser_input_bridge_entry(
    entry: SourceArtifactParserInputBridgeEntry,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> SourceArtifactParserInputBridgeValidationResult:
    """Validate bridge metadata without touching files or external systems."""

    issues: list[SourceArtifactParserInputBridgeValidationIssue] = []

    _validate_required_text(
        entry.source_family,
        "source_family",
        "SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_MISSING_SOURCE_FAMILY",
        "source_family must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        entry.source_key,
        "source_key",
        "SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_MISSING_SOURCE_KEY",
        "source_key must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        entry.parser_key,
        "parser_key",
        "SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_MISSING_PARSER_KEY",
        "parser_key must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        entry.source_artifact_id,
        "source_artifact_id",
        "SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_MISSING_SOURCE_ARTIFACT_ID",
        "source_artifact_id must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        entry.parser_input_artifact_id,
        "parser_input_artifact_id",
        "SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_MISSING_PARSER_INPUT_ARTIFACT_ID",
        "parser_input_artifact_id must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        entry.artifact_kind,
        "artifact_kind",
        "SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_MISSING_ARTIFACT_KIND",
        "artifact_kind must be a non-empty string.",
        issues,
    )
    _validate_required_text(
        entry.artifact_reference,
        "artifact_reference",
        "SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_MISSING_ARTIFACT_REFERENCE",
        "artifact_reference must be a non-empty string.",
        issues,
    )

    _append_source_artifact_validation_issues(
        entry.source_artifact,
        "source_artifact",
        issues,
    )
    _append_parser_input_validation_issues(
        entry.parser_input_artifact,
        "parser_input_artifact",
        issues,
        registry,
    )
    _validate_bridge_registry_alignment(entry, issues, registry)
    _validate_source_artifact_alignment(entry, issues)
    _validate_parser_input_alignment(entry, issues)

    return SourceArtifactParserInputBridgeValidationResult(issues=tuple(issues))


def validate_source_artifact_parser_input_bridge_result(
    result: SourceArtifactParserInputBridgeResult,
    registry: Phase1ParserAdapterRegistry | None = None,
) -> SourceArtifactParserInputBridgeValidationResult:
    """Validate bridge batches without runtime side effects."""

    issues: list[SourceArtifactParserInputBridgeValidationIssue] = []
    for position, entry in enumerate(result.entries, start=1):
        for issue in validate_source_artifact_parser_input_bridge_entry(
            entry,
            registry,
        ).issues:
            issues.append(
                SourceArtifactParserInputBridgeValidationIssue(
                    code=issue.code,
                    message=issue.message,
                    field_name=f"entries[{position}].{issue.field_name}",
                    severity=issue.severity,
                )
            )

    return SourceArtifactParserInputBridgeValidationResult(issues=tuple(issues))


def _validate_bridge_registry_alignment(
    entry: SourceArtifactParserInputBridgeEntry,
    issues: list[SourceArtifactParserInputBridgeValidationIssue],
    registry: Phase1ParserAdapterRegistry | None,
) -> None:
    descriptor = get_phase1_parser_adapter_by_source_family(
        entry.source_family,
        registry,
    )
    if descriptor is None:
        issues.append(
            SourceArtifactParserInputBridgeValidationIssue(
                code="SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_UNKNOWN_SOURCE_FAMILY",
                message="source_family must match a registered Phase 1 parser adapter.",
                field_name="source_family",
            )
        )
        return

    if entry.source_key != descriptor.source_family:
        issues.append(
            SourceArtifactParserInputBridgeValidationIssue(
                code="SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_SOURCE_KEY_MISMATCH",
                message="source_key must match the registered source family.",
                field_name="source_key",
            )
        )
    if entry.parser_key != descriptor.parser_key:
        issues.append(
            SourceArtifactParserInputBridgeValidationIssue(
                code="SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_PARSER_KEY_MISMATCH",
                message="parser_key must match the registered parser adapter.",
                field_name="parser_key",
            )
        )


def _validate_source_artifact_alignment(
    entry: SourceArtifactParserInputBridgeEntry,
    issues: list[SourceArtifactParserInputBridgeValidationIssue],
) -> None:
    source_artifact = entry.source_artifact
    for field_name, entry_value, artifact_value in (
        ("source_family", entry.source_family, source_artifact.source_family),
        ("source_key", entry.source_key, source_artifact.source_key),
        ("source_artifact_id", entry.source_artifact_id, source_artifact.artifact_id),
        ("artifact_kind", entry.artifact_kind, source_artifact.artifact_kind),
        ("artifact_reference", entry.artifact_reference, source_artifact.local_reference),
        ("original_filename", entry.original_filename, source_artifact.original_filename),
        ("display_name", entry.display_name, source_artifact.display_name),
        ("content_type", entry.content_type, source_artifact.content_type),
        ("extension", entry.extension, source_artifact.extension),
        ("checksum_sha256", entry.checksum_sha256, source_artifact.checksum_sha256),
        ("document_year", entry.document_year, source_artifact.document_year),
        ("reporting_year", entry.reporting_year, source_artifact.reporting_year),
    ):
        if entry_value != artifact_value:
            issues.append(
                SourceArtifactParserInputBridgeValidationIssue(
                    code="SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_SOURCE_ARTIFACT_MISMATCH",
                    message=(
                        "bridge metadata must match the source artifact metadata."
                    ),
                    field_name=field_name,
                )
            )


def _validate_parser_input_alignment(
    entry: SourceArtifactParserInputBridgeEntry,
    issues: list[SourceArtifactParserInputBridgeValidationIssue],
) -> None:
    parser_input = entry.parser_input_artifact
    for field_name, entry_value, parser_input_value in (
        ("source_family", entry.source_family, parser_input.source_family),
        ("source_key", entry.source_key, parser_input.source_key),
        ("parser_key", entry.parser_key, parser_input.parser_key),
        ("artifact_reference", entry.artifact_reference, parser_input.artifact_reference),
        ("original_filename", entry.original_filename, parser_input.original_filename),
        ("display_name", entry.display_name, parser_input.display_name),
        ("content_type", entry.content_type, parser_input.content_type),
        ("extension", entry.extension, parser_input.extension),
        ("checksum_sha256", entry.checksum_sha256, parser_input.checksum_sha256),
        ("reporting_year", entry.reporting_year, parser_input.reporting_year),
    ):
        if entry_value != parser_input_value:
            issues.append(
                SourceArtifactParserInputBridgeValidationIssue(
                    code="SOURCE_ARTIFACT_PARSER_INPUT_BRIDGE_PARSER_INPUT_MISMATCH",
                    message=(
                        "bridge metadata must match the parser input artifact metadata."
                    ),
                    field_name=field_name,
                )
            )


def _append_source_artifact_validation_issues(
    source_artifact: SourceDownloadArtifact,
    field_prefix: str,
    issues: list[SourceArtifactParserInputBridgeValidationIssue],
) -> None:
    for issue in validate_source_download_artifact(source_artifact).issues:
        issues.append(
            SourceArtifactParserInputBridgeValidationIssue(
                code=issue.code,
                message=issue.message,
                field_name=f"{field_prefix}.{issue.field_name}",
                severity=issue.severity,
            )
        )


def _append_parser_input_validation_issues(
    parser_input: ParserInputArtifact,
    field_prefix: str,
    issues: list[SourceArtifactParserInputBridgeValidationIssue],
    registry: Phase1ParserAdapterRegistry | None,
) -> None:
    for issue in validate_parser_input_artifact(parser_input, registry).issues:
        issues.append(
            SourceArtifactParserInputBridgeValidationIssue(
                code=issue.code,
                message=issue.message,
                field_name=f"{field_prefix}.{issue.field_name}",
                severity=issue.severity,
            )
        )


def _validate_required_text(
    value: str | None,
    field_name: str,
    code: str,
    message: str,
    issues: list[SourceArtifactParserInputBridgeValidationIssue],
) -> None:
    if not isinstance(value, str) or not value.strip():
        issues.append(
            SourceArtifactParserInputBridgeValidationIssue(
                code=code,
                message=message,
                field_name=field_name,
            )
        )
