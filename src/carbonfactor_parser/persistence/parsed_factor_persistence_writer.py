"""Parsed emission factor persistence writer boundary."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
import hashlib
import json
from typing import TYPE_CHECKING, Mapping, Sequence

from carbonfactor_parser.parsers.raw_record import (
    ParsedRawRecord,
    ParsedRawRecordPayload,
    validate_parsed_raw_record_payload,
)
from carbonfactor_parser.persistence.postgresql_schema_catalog import SourceFamily
from carbonfactor_parser.persistence.source_document_mapping import (
    DRY_RUN_TIMESTAMP_LABEL,
)
from carbonfactor_parser.persistence.source_family_repository import (
    SourceFamilyDetailRecord,
    SourceFamilyMasterRecord,
    SourceFamilyRepository,
    SourceFamilyRepositoryIssue,
    SourceFamilyRepositoryPersistStatus,
    validate_source_family_repository_inputs,
)

if TYPE_CHECKING:
    from carbonfactor_parser.parsers.normalized_output_row_contract import (
        ParserNormalizedOutputBatch,
        ParserNormalizedOutputRow,
    )
    ParsedFactorOutput = ParsedRawRecordPayload | ParserNormalizedOutputBatch
else:
    ParsedFactorOutput = object


class ParsedFactorPersistenceStatus(str, Enum):
    """Status for parsed factor persistence writer outcomes."""

    DECLARED = "declared"
    FAILED_VALIDATION = "failed_validation"
    NO_RECORDS = "no_records"


@dataclass(frozen=True)
class ParsedFactorPersistenceIssue:
    """Validation or repository issue from parsed factor persistence mapping."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class ParsedFactorPersistenceCommand:
    """Source-family master/detail records ready for repository persistence."""

    master_records: tuple[SourceFamilyMasterRecord, ...]
    detail_records: tuple[SourceFamilyDetailRecord, ...]
    skipped_duplicate_count: int = 0
    issues: tuple[ParsedFactorPersistenceIssue, ...] = ()


@dataclass(frozen=True)
class ParsedFactorPersistenceWriterResult:
    """Result of building and submitting parsed factor persistence commands."""

    provider_name: str
    status: ParsedFactorPersistenceStatus
    attempted_master_count: int
    attempted_detail_count: int
    persisted_master_count: int
    persisted_detail_count: int
    skipped_duplicate_count: int = 0
    issues: tuple[ParsedFactorPersistenceIssue, ...] = ()
    command: ParsedFactorPersistenceCommand | None = None


_SOURCE_FAMILY_ALIASES: Mapping[str, SourceFamily] = {
    "ghg": SourceFamily.GHG,
    "ghg_protocol": SourceFamily.GHG,
    "defra": SourceFamily.DEFRA,
    "defra_desnz": SourceFamily.DEFRA,
    "desnz": SourceFamily.DEFRA,
    "ipcc": SourceFamily.IPCC,
    "ipcc_efdb": SourceFamily.IPCC,
}


def build_parsed_factor_persistence_command(
    parsed_output: ParsedFactorOutput,
    *,
    source_document_id: str | None = None,
    lifecycle_status: str = "active",
    timestamp_label: str = DRY_RUN_TIMESTAMP_LABEL,
) -> ParsedFactorPersistenceCommand:
    """Map parsed factor output into source-family master/detail records."""

    rows, shape_issues = _rows_from_output(parsed_output)
    if not rows and not shape_issues:
        return ParsedFactorPersistenceCommand(
            master_records=(),
            detail_records=(),
            issues=(
                ParsedFactorPersistenceIssue(
                    code="PARSED_FACTOR_PERSISTENCE_NO_RECORDS",
                    message="parsed output must include records before persistence.",
                    field_name="records",
                    severity="warning",
                ),
            ),
        )

    issues: list[ParsedFactorPersistenceIssue] = list(shape_issues)
    masters: dict[tuple[SourceFamily, str], SourceFamilyMasterRecord] = {}
    details: dict[tuple[SourceFamily, str, str], SourceFamilyDetailRecord] = {}
    skipped_duplicate_count = 0

    for position, row in enumerate(rows, start=1):
        mapped = _map_row(
            row,
            position=position,
            source_document_id=source_document_id,
            lifecycle_status=lifecycle_status,
            timestamp_label=timestamp_label,
        )
        issues.extend(mapped.issues)
        if mapped.master_record is None or mapped.detail_record is None:
            continue

        master_key = (
            mapped.master_record.source_family,
            mapped.master_record.source_family_master_id,
        )
        existing_master = masters.get(master_key)
        if existing_master is None:
            masters[master_key] = mapped.master_record
        elif existing_master == mapped.master_record:
            skipped_duplicate_count += 1
        else:
            issues.append(
                ParsedFactorPersistenceIssue(
                    code="PARSED_FACTOR_PERSISTENCE_DUPLICATE_MASTER_CONFLICT",
                    message=(
                        "duplicate source-family master identity maps to "
                        "different record content."
                    ),
                    field_name=f"records[{position}].source_family_master_id",
                ),
            )

        detail_key = (
            mapped.detail_record.source_family,
            mapped.detail_record.source_family_master_id,
            mapped.detail_record.detail_external_key,
        )
        existing_detail = details.get(detail_key)
        if existing_detail is None:
            details[detail_key] = mapped.detail_record
        elif existing_detail == mapped.detail_record:
            skipped_duplicate_count += 1
        else:
            issues.append(
                ParsedFactorPersistenceIssue(
                    code="PARSED_FACTOR_PERSISTENCE_DUPLICATE_DETAIL_CONFLICT",
                    message=(
                        "duplicate factor identity maps to different detail "
                        "record content."
                    ),
                    field_name=f"records[{position}].detail_external_key",
                ),
            )

    command = ParsedFactorPersistenceCommand(
        master_records=tuple(masters.values()),
        detail_records=tuple(details.values()),
        skipped_duplicate_count=skipped_duplicate_count,
        issues=tuple(issues),
    )
    repository_validation = validate_source_family_repository_inputs(
        provider_name="parsed_factor_persistence_command",
        master_records=command.master_records,
        detail_records=command.detail_records,
    )
    if repository_validation.issues:
        return ParsedFactorPersistenceCommand(
            master_records=command.master_records,
            detail_records=command.detail_records,
            skipped_duplicate_count=command.skipped_duplicate_count,
            issues=(
                *command.issues,
                *tuple(
                    _from_repository_issue(issue)
                    for issue in repository_validation.issues
                ),
            ),
        )

    return command


def persist_parsed_factor_records(
    parsed_output: ParsedFactorOutput,
    repository: SourceFamilyRepository,
    *,
    source_document_id: str | None = None,
    lifecycle_status: str = "active",
    timestamp_label: str = DRY_RUN_TIMESTAMP_LABEL,
) -> ParsedFactorPersistenceWriterResult:
    """Build parsed factor records and submit them to a repository protocol."""

    command = build_parsed_factor_persistence_command(
        parsed_output,
        source_document_id=source_document_id,
        lifecycle_status=lifecycle_status,
        timestamp_label=timestamp_label,
    )
    if command.issues:
        status = (
            ParsedFactorPersistenceStatus.NO_RECORDS
            if _only_no_records(command.issues)
            else ParsedFactorPersistenceStatus.FAILED_VALIDATION
        )
        return ParsedFactorPersistenceWriterResult(
            provider_name=repository.provider_name,
            status=status,
            attempted_master_count=len(command.master_records),
            attempted_detail_count=len(command.detail_records),
            persisted_master_count=0,
            persisted_detail_count=0,
            skipped_duplicate_count=command.skipped_duplicate_count,
            issues=command.issues,
            command=command,
        )

    repository_result = repository.persist_source_family_records(
        command.master_records,
        command.detail_records,
    )
    repository_issues = tuple(
        _from_repository_issue(issue) for issue in repository_result.issues
    )
    status = (
        ParsedFactorPersistenceStatus.DECLARED
        if repository_result.status is SourceFamilyRepositoryPersistStatus.DECLARED
        else ParsedFactorPersistenceStatus.FAILED_VALIDATION
    )
    return ParsedFactorPersistenceWriterResult(
        provider_name=repository_result.provider_name,
        status=status,
        attempted_master_count=len(command.master_records),
        attempted_detail_count=len(command.detail_records),
        persisted_master_count=repository_result.persisted_master_count,
        persisted_detail_count=repository_result.persisted_detail_count,
        skipped_duplicate_count=command.skipped_duplicate_count,
        issues=repository_issues,
        command=command,
    )


@dataclass(frozen=True)
class _PersistenceRow:
    source_family: str
    source_id: str
    row_id: str
    fields: Mapping[str, object]
    artifact_reference: str | None
    artifact_checksum_sha256: str | None
    source_row_number: int | None


@dataclass(frozen=True)
class _MappedRow:
    master_record: SourceFamilyMasterRecord | None
    detail_record: SourceFamilyDetailRecord | None
    issues: tuple[ParsedFactorPersistenceIssue, ...] = ()


def _rows_from_output(
    parsed_output: ParsedFactorOutput,
) -> tuple[tuple[_PersistenceRow, ...], tuple[ParsedFactorPersistenceIssue, ...]]:
    from carbonfactor_parser.parsers.normalized_output_row_contract import (
        validate_parser_normalized_output_batch,
    )

    if _looks_like_raw_record_payload(parsed_output):
        validation = validate_parsed_raw_record_payload(parsed_output)
        issues = tuple(
            ParsedFactorPersistenceIssue(
                code=issue.code,
                message=issue.message,
                field_name=issue.field_name,
                severity=issue.severity,
            )
            for issue in validation.issues
        )
        return (
            tuple(_row_from_raw_record(record) for record in parsed_output.records),
            issues,
        )

    if _looks_like_normalized_output_batch(parsed_output):
        validation = validate_parser_normalized_output_batch(parsed_output)
        issues = tuple(
            ParsedFactorPersistenceIssue(
                code=issue.code,
                message=issue.message,
                field_name=issue.field_name,
                severity=issue.severity,
            )
            for issue in validation.issues
        )
        return (
            tuple(_row_from_normalized_row(row) for row in parsed_output.rows),
            issues,
        )

    return (
        (),
        (
            ParsedFactorPersistenceIssue(
                code="PARSED_FACTOR_PERSISTENCE_INVALID_OUTPUT",
                message=(
                    "parsed_output must be ParsedRawRecordPayload or "
                    "ParserNormalizedOutputBatch."
                ),
                field_name="parsed_output",
            ),
        ),
    )


def _looks_like_raw_record_payload(value: object) -> bool:
    return hasattr(value, "records") and all(
        hasattr(record, "raw_fields") for record in getattr(value, "records", ())
    )


def _looks_like_normalized_output_batch(value: object) -> bool:
    return hasattr(value, "rows") and all(
        hasattr(row, "normalized_fields") for row in getattr(value, "rows", ())
    )


def _row_from_raw_record(record: ParsedRawRecord) -> _PersistenceRow:
    return _PersistenceRow(
        source_family=record.source_family,
        source_id=record.source_id,
        row_id=f"record-{record.record_index}",
        fields=dict(record.raw_fields),
        artifact_reference=_text_or_none(
            (record.source_context or {}).get("artifact_reference")
        ),
        artifact_checksum_sha256=_text_or_none(
            (record.source_context or {}).get("checksum_sha256")
        ),
        source_row_number=record.row_number,
    )


def _row_from_normalized_row(row: "ParserNormalizedOutputRow") -> _PersistenceRow:
    return _PersistenceRow(
        source_family=row.source_family,
        source_id=row.source_key,
        row_id=row.row_id,
        fields=dict(row.normalized_fields),
        artifact_reference=row.artifact_reference,
        artifact_checksum_sha256=_text_or_none(
            _field(row.normalized_fields, "source_checksum_sha256", "checksum_sha256")
        ),
        source_row_number=row.source_row_number,
    )


def _map_row(
    row: _PersistenceRow,
    *,
    position: int,
    source_document_id: str | None,
    lifecycle_status: str,
    timestamp_label: str,
) -> _MappedRow:
    issues: list[ParsedFactorPersistenceIssue] = []
    source_family = _source_family(row.source_family)
    if source_family is None:
        issues.append(
            ParsedFactorPersistenceIssue(
                code="PARSED_FACTOR_PERSISTENCE_UNSUPPORTED_SOURCE_FAMILY",
                message="source_family must map to GHG, DEFRA/DESNZ, or IPCC.",
                field_name=f"records[{position}].source_family",
            ),
        )
        return _MappedRow(None, None, tuple(issues))

    resolved_source_document_id = _source_document_id(row, source_document_id)
    required_values = {
        "source_document_id": resolved_source_document_id,
        "factor_value": _field(row.fields, "factor_value", "value"),
        "factor_unit": _field(row.fields, "factor_unit", "unit"),
    }
    for field_name, value in required_values.items():
        if _text_or_none(value) is None:
            issues.append(
                ParsedFactorPersistenceIssue(
                    code="PARSED_FACTOR_PERSISTENCE_MISSING_REQUIRED_FIELD",
                    message="parsed factor persistence requires a non-empty value.",
                    field_name=f"records[{position}].{field_name}",
                ),
            )

    if issues:
        return _MappedRow(None, None, tuple(issues))

    master_external_key = _text_or_none(
        _field(row.fields, "master_external_key")
    ) or _default_master_external_key(row)
    detail_external_key = _text_or_none(
        _field(row.fields, "detail_external_key")
    ) or _default_detail_external_key(row)
    master_id = _text_or_none(
        _field(row.fields, "source_family_master_id")
    ) or (
        f"{source_family.value}_master_"
        f"{_stable_digest(source_family.value, master_external_key)[:16]}"
    )
    detail_id = _text_or_none(
        _field(row.fields, "source_family_detail_id")
    ) or (
        f"{source_family.value}_detail_"
        f"{_stable_digest(source_family.value, master_id, detail_external_key)[:16]}"
    )
    source_year = _int_or_none(_field(row.fields, "source_year", "reporting_year"))
    if source_year is None:
        issues.append(
            ParsedFactorPersistenceIssue(
                code="PARSED_FACTOR_PERSISTENCE_MISSING_REQUIRED_FIELD",
                message="parsed factor persistence requires a source_year value.",
                field_name=f"records[{position}].source_year",
            ),
        )
        return _MappedRow(None, None, tuple(issues))
    source_version = _text_or_none(_field(row.fields, "source_version")) or "unknown"
    artifact_checksum_sha256 = row.artifact_checksum_sha256 or _text_or_none(
        _field(row.fields, "provenance_checksum_value", "source_checksum_sha256")
    )

    master_record = SourceFamilyMasterRecord(
        source_family=source_family,
        source_family_master_id=master_id,
        source_year=source_year,
        source_version=source_version,
        source_release=_text_or_none(_field(row.fields, "source_release")),
        source_document_id=resolved_source_document_id or "",
        ingestion_run_id=_text_or_none(_field(row.fields, "ingestion_run_id")),
        run_id=_text_or_none(_field(row.fields, "run_id")),
        master_external_key=master_external_key,
        status=lifecycle_status,
        artifact_reference=row.artifact_reference,
        artifact_checksum_sha256=artifact_checksum_sha256,
        archive_reference=_text_or_none(_field(row.fields, "archive_reference")),
        archive_checksum_sha256=_text_or_none(
            _field(row.fields, "archive_checksum_sha256")
        ),
        effective_from=_text_or_none(_field(row.fields, "effective_from")),
        effective_to=_text_or_none(_field(row.fields, "effective_to")),
        record_checksum_sha256=_record_checksum(
            "master",
            source_family.value,
            resolved_source_document_id,
            master_external_key,
            lifecycle_status,
        ),
        metadata={},
        created_at=timestamp_label,
        updated_at=timestamp_label,
    )
    detail_record = SourceFamilyDetailRecord(
        source_family=source_family,
        source_family_detail_id=detail_id,
        source_family_master_id=master_id,
        detail_external_key=detail_external_key,
        source_row_number=row.source_row_number,
        factor_id=_text_or_none(_field(row.fields, "factor_id")),
        factor_name=_text_or_none(_field(row.fields, "factor_name")),
        factor_value=_text_or_none(required_values["factor_value"]) or "",
        factor_unit=_text_or_none(required_values["factor_unit"]) or "",
        status=lifecycle_status,
        record_checksum_sha256=_record_checksum(
            "detail",
            source_family.value,
            master_id,
            detail_external_key,
            required_values["factor_value"],
            required_values["factor_unit"],
        ),
        raw_fields=dict(row.fields),
        normalized_fields=dict(row.fields),
        created_at=timestamp_label,
        updated_at=timestamp_label,
    )
    return _MappedRow(master_record, detail_record)


def _source_family(value: str) -> SourceFamily | None:
    if not isinstance(value, str):
        return None
    return _SOURCE_FAMILY_ALIASES.get(value.strip().lower())


def _source_document_id(
    row: _PersistenceRow,
    explicit_source_document_id: str | None,
) -> str | None:
    explicit = _text_or_none(explicit_source_document_id)
    if explicit is not None:
        return explicit
    field_value = _text_or_none(_field(row.fields, "source_document_id"))
    if field_value is not None:
        return field_value
    artifact_reference = _text_or_none(
        _field(row.fields, "provenance_artifact_reference", "artifact_reference")
    ) or row.artifact_reference
    checksum = _text_or_none(
        _field(row.fields, "provenance_checksum_value", "source_checksum_sha256")
    )
    if artifact_reference is None and checksum is None:
        return None
    digest = _stable_digest(
        row.source_family,
        row.source_id,
        artifact_reference,
        checksum,
    )
    return f"source_document_{digest[:24]}"


def _default_master_external_key(row: _PersistenceRow) -> str:
    source_year = _text_or_none(_field(row.fields, "source_year")) or "unknown-year"
    source_version = (
        _text_or_none(_field(row.fields, "source_version")) or "unknown-version"
    )
    factor_id = _text_or_none(_field(row.fields, "factor_id")) or row.row_id
    return f"{source_year}:{source_version}:{factor_id}"


def _default_detail_external_key(row: _PersistenceRow) -> str:
    factor_id = _text_or_none(_field(row.fields, "factor_id")) or row.row_id
    factor_unit = (
        _text_or_none(_field(row.fields, "factor_unit", "unit")) or "unknown-unit"
    )
    gas = _text_or_none(_field(row.fields, "greenhouse_gas", "gas"))
    if gas is None:
        return f"{factor_id}:{factor_unit}"
    return f"{factor_id}:{factor_unit}:{gas}"


def _field(fields: Mapping[str, object], *names: str) -> object | None:
    for name in names:
        if name in fields:
            return fields[name]
    return None


def _text_or_none(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _int_or_none(value: object | None) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    text = _text_or_none(value)
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _record_checksum(*values: object) -> str:
    return _stable_digest(*values)


def _stable_digest(*values: object) -> str:
    payload = json.dumps(
        [_json_safe(value) for value in values],
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _json_safe(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, Sequence) and not isinstance(value, str):
        return [_json_safe(item) for item in value]
    return value


def _from_repository_issue(
    issue: SourceFamilyRepositoryIssue,
) -> ParsedFactorPersistenceIssue:
    return ParsedFactorPersistenceIssue(
        code=issue.code,
        message=issue.message,
        field_name=issue.field_name,
        severity=issue.severity,
    )


def _only_no_records(issues: tuple[ParsedFactorPersistenceIssue, ...]) -> bool:
    return tuple(issue.code for issue in issues) == (
        "PARSED_FACTOR_PERSISTENCE_NO_RECORDS",
    )
