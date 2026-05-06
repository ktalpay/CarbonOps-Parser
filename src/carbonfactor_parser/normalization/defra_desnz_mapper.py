"""Minimal DEFRA/DESNZ fixture normalization mapper."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from carbonfactor_parser.normalization.contracts import (
    NormalizationIssue,
    NormalizationIssueSeverity,
    NormalizationResult,
    NormalizedRecord,
)
from carbonfactor_parser.normalization.input import (
    NormalizationInput,
    NormalizationInputRecord,
)


DEFRA_DESNZ_MINIMAL_NORMALIZATION_FIELDS = (
    "factor_id",
    "factor_name",
    "unit",
)


class DefraDesnzNormalizationMappingStatus(str, Enum):
    """Status for minimal DEFRA/DESNZ fixture normalization mapping."""

    SUCCESS = "success"
    FAILED = "failed"
    NO_RECORDS = "no_records"


@dataclass(frozen=True)
class DefraDesnzNormalizationMappingResult:
    """Structured result for minimal DEFRA/DESNZ fixture mapping."""

    status: DefraDesnzNormalizationMappingStatus
    normalization_result: NormalizationResult


def map_defra_desnz_normalization_input(
    normalization_input: NormalizationInput,
) -> DefraDesnzNormalizationMappingResult:
    """Map minimal DEFRA/DESNZ fixture input without source correctness claims."""

    if not normalization_input.records:
        return DefraDesnzNormalizationMappingResult(
            status=DefraDesnzNormalizationMappingStatus.NO_RECORDS,
            normalization_result=NormalizationResult(
                issues=(
                    NormalizationIssue(
                        code="DEFRA_DESNZ_NORMALIZATION_NO_RECORDS",
                        message=(
                            "DEFRA/DESNZ minimal normalization input did not "
                            "include records."
                        ),
                        severity=NormalizationIssueSeverity.WARNING,
                        location="records",
                    ),
                ),
            ),
        )

    issues: list[NormalizationIssue] = []
    records: list[NormalizedRecord] = []
    for record in normalization_input.records:
        record_issues = _record_issues(record)
        issues.extend(record_issues)
        if not record_issues:
            records.append(_normalized_record(record))

    if issues:
        return DefraDesnzNormalizationMappingResult(
            status=DefraDesnzNormalizationMappingStatus.FAILED,
            normalization_result=NormalizationResult(issues=tuple(issues)),
        )

    return DefraDesnzNormalizationMappingResult(
        status=DefraDesnzNormalizationMappingStatus.SUCCESS,
        normalization_result=NormalizationResult(records=tuple(records)),
    )


def map_defra_desnz_normalization_input_record(
    record: NormalizationInputRecord,
) -> DefraDesnzNormalizationMappingResult:
    """Map one minimal DEFRA/DESNZ fixture input record."""

    return map_defra_desnz_normalization_input(
        NormalizationInput(
            source_family=record.source_family,
            source_id=record.source_id,
            records=(record,),
            parser_metadata=record.parser_metadata,
            source_context=record.source_context,
        ),
    )


def _record_issues(record: NormalizationInputRecord) -> tuple[NormalizationIssue, ...]:
    issues: list[NormalizationIssue] = []

    if record.source_family != "defra_desnz":
        issues.append(
            NormalizationIssue(
                code="DEFRA_DESNZ_NORMALIZATION_SOURCE_FAMILY_MISMATCH",
                message=(
                    "DEFRA/DESNZ minimal normalization only accepts "
                    "defra_desnz source_family."
                ),
                severity=NormalizationIssueSeverity.ERROR,
                location=_record_location(record, "source_family"),
            ),
        )

    for field_name in DEFRA_DESNZ_MINIMAL_NORMALIZATION_FIELDS:
        if _missing_raw_field(record, field_name):
            issues.append(
                NormalizationIssue(
                    code="DEFRA_DESNZ_NORMALIZATION_MISSING_RAW_FIELD",
                    message=(
                        "DEFRA/DESNZ minimal normalization input is missing "
                        f"required raw field: {field_name}."
                    ),
                    severity=NormalizationIssueSeverity.ERROR,
                    location=_record_location(record, field_name),
                ),
            )

    return tuple(issues)


def _normalized_record(record: NormalizationInputRecord) -> NormalizedRecord:
    return NormalizedRecord(
        record_id=(
            f"{record.source_family}:{record.source_id}:"
            f"record-{record.record_index:03d}"
        ),
        fields=(
            ("source_family", record.source_family),
            ("source_id", record.source_id),
            ("record_index", record.record_index),
            ("row_number", record.row_number),
            ("factor_id", record.raw_fields["factor_id"]),
            ("factor_name", record.raw_fields["factor_name"]),
            ("unit", record.raw_fields["unit"]),
        ),
        source_reference=_source_reference(record),
        is_artificial=True,
    )


def _missing_raw_field(
    record: NormalizationInputRecord,
    field_name: str,
) -> bool:
    if field_name not in record.raw_fields:
        return True
    value = record.raw_fields[field_name]
    return value is None or (isinstance(value, str) and not value.strip())


def _record_location(record: NormalizationInputRecord, field_name: str) -> str:
    return f"records[{record.record_index}].raw_fields.{field_name}"


def _source_reference(record: NormalizationInputRecord) -> str | None:
    if record.source_context is None:
        return None
    artifact_reference = record.source_context.get("artifact_reference")
    if isinstance(artifact_reference, str) and artifact_reference:
        return artifact_reference
    return None
