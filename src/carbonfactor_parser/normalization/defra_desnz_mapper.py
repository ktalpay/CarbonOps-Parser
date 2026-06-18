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

DEFRA_DESNZ_NORMALIZED_MAPPING_FIELDS = (
    "source_family",
    "source_id",
    "source_year",
    "source_version",
    "record_index",
    "row_number",
    "factor_id",
    "factor_name",
    "factor_value",
    "unit",
    "category",
    "subcategory",
    "activity",
    "greenhouse_gas",
    "provenance",
)

_DEFRA_DESNZ_REQUIRED_NORMALIZED_FIELDS = (
    "source_year",
    "source_version",
    "category",
    "factor_id",
    "factor_name",
    "factor_value",
    "unit",
    "provenance",
)

_DEFRA_DESNZ_NORMALIZED_ONLY_FIELDS = (
    "source_year",
    "source_version",
    "category",
    "factor_value",
    "provenance",
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

    required_fields = _required_fields(record)
    for field_name in required_fields:
        if _missing_raw_field(record, field_name):
            issues.append(
                NormalizationIssue(
                    code="DEFRA_DESNZ_NORMALIZATION_MISSING_RAW_FIELD",
                    message=(
                        "DEFRA/DESNZ normalization input is missing "
                        f"required raw field: {field_name}."
                    ),
                    severity=NormalizationIssueSeverity.ERROR,
                    location=_record_location(record, field_name),
                ),
            )

    if _is_normalized_extraction_record(record) and not _missing_raw_field(
        record,
        "factor_value",
    ):
        try:
            float(str(record.raw_fields["factor_value"]).strip())
        except ValueError:
            issues.append(
                NormalizationIssue(
                    code="DEFRA_DESNZ_NORMALIZATION_INVALID_FACTOR_VALUE",
                    message="DEFRA/DESNZ factor_value must be numeric.",
                    severity=NormalizationIssueSeverity.ERROR,
                    location=_record_location(record, "factor_value"),
                ),
            )

    return tuple(issues)


def _normalized_record(record: NormalizationInputRecord) -> NormalizedRecord:
    if _is_normalized_extraction_record(record):
        return _normalized_extraction_record(record)

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


def _normalized_extraction_record(record: NormalizationInputRecord) -> NormalizedRecord:
    raw_fields = record.raw_fields
    return NormalizedRecord(
        record_id=(
            f"{record.source_family}:{record.source_id}:"
            f"{_text(raw_fields['source_year'])}:"
            f"{_text(raw_fields['source_version'])}:"
            f"{_text(raw_fields['factor_id'])}"
        ),
        fields=(
            ("source_family", record.source_family),
            ("source_id", record.source_id),
            ("source_year", _text(raw_fields["source_year"])),
            ("source_version", _text(raw_fields["source_version"])),
            ("record_index", record.record_index),
            ("row_number", record.row_number),
            ("factor_id", _text(raw_fields["factor_id"])),
            ("factor_name", _text(raw_fields["factor_name"])),
            ("factor_value", float(_text(raw_fields["factor_value"]))),
            ("unit", _text(raw_fields["unit"])),
            ("category", _text(raw_fields["category"])),
            ("subcategory", _optional_text(raw_fields.get("subcategory"))),
            ("activity", _optional_text(raw_fields.get("activity"))),
            ("greenhouse_gas", _optional_text(raw_fields.get("greenhouse_gas"))),
            ("provenance", _text(raw_fields["provenance"])),
        ),
        source_reference=_source_reference(record),
        is_artificial=False,
    )


def _required_fields(record: NormalizationInputRecord) -> tuple[str, ...]:
    if _is_normalized_extraction_record(record):
        return _DEFRA_DESNZ_REQUIRED_NORMALIZED_FIELDS
    return DEFRA_DESNZ_MINIMAL_NORMALIZATION_FIELDS


def _is_normalized_extraction_record(record: NormalizationInputRecord) -> bool:
    return any(
        field_name in record.raw_fields
        for field_name in _DEFRA_DESNZ_NORMALIZED_ONLY_FIELDS
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


def _text(value: object) -> str:
    return str(value).strip()


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
