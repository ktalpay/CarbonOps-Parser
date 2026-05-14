from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from carbonfactor_parser.normalization import (
    REDACTED_DIAGNOSTIC_VALUE,
    DataQualityDiagnostic,
    DataQualityProvenanceContext,
    DataQualityValidationCheck,
    DataQualityValidationResult,
    DataQualityValidationSeverity,
    NormalizationResult,
    NormalizedRecord,
    create_data_quality_diagnostic,
    validate_normalized_factor_output,
)


def test_validation_model_represents_blocking_warning_and_info() -> None:
    blocking = create_data_quality_diagnostic(
        code="BLOCKING",
        message="blocking diagnostic",
        severity=DataQualityValidationSeverity.BLOCKING_ERROR,
        check=DataQualityValidationCheck.REQUIRED_FIELD,
    )
    warning = create_data_quality_diagnostic(
        code="WARNING",
        message="warning diagnostic",
        severity=DataQualityValidationSeverity.WARNING,
        check=DataQualityValidationCheck.UNIT,
    )
    info = create_data_quality_diagnostic(
        code="INFO",
        message="info diagnostic",
        severity=DataQualityValidationSeverity.INFO,
        check=DataQualityValidationCheck.STRUCTURE,
    )

    result = DataQualityValidationResult(diagnostics=(blocking, warning, info))

    assert result.is_valid is False
    assert result.has_blocking_errors is True
    assert result.blocking_error_count == 1
    assert result.warning_count == 1
    assert result.info_count == 1


def test_validation_severity_and_check_names_are_phase_2_wire_names() -> None:
    assert tuple(severity.value for severity in DataQualityValidationSeverity) == (
        "blocking_error",
        "warning",
        "info",
    )
    assert tuple(check.value for check in DataQualityValidationCheck) == (
        "required_field",
        "numeric_value",
        "unit",
        "duplicate_factor_identity",
        "provenance",
        "structure",
    )


def test_missing_required_fields_are_blocking_errors() -> None:
    record = _record(
        factor_id=" ",
        factor_name=None,
    )

    result = validate_normalized_factor_output(NormalizationResult(records=(record,)))

    assert result.is_valid is False
    assert _diagnostic_codes(result) == (
        "NORMALIZED_FACTOR_MISSING_REQUIRED_FIELD",
        "NORMALIZED_FACTOR_MISSING_REQUIRED_FIELD",
    )
    assert tuple(diagnostic.field_name for diagnostic in result.diagnostics) == (
        "factor_id",
        "factor_name",
    )
    assert all(
        diagnostic.severity == DataQualityValidationSeverity.BLOCKING_ERROR
        for diagnostic in result.diagnostics
    )


def test_invalid_numeric_values_are_blocking_errors_without_value_leakage() -> None:
    record = _record(factor_value="not-a-number")

    result = validate_normalized_factor_output(NormalizationResult(records=(record,)))

    assert result.is_valid is False
    assert _diagnostic_codes(result) == ("NORMALIZED_FACTOR_INVALID_NUMERIC_VALUE",)
    diagnostic = result.diagnostics[0]
    assert diagnostic.field_name == "factor_value"
    assert diagnostic.check == DataQualityValidationCheck.NUMERIC_VALUE
    assert "not-a-number" not in diagnostic.message
    assert "not-a-number" not in repr(diagnostic.context)


def test_unsupported_units_are_warnings() -> None:
    record = _record(unit="widgets per fortnight")

    result = validate_normalized_factor_output(
        NormalizationResult(records=(record,)),
        supported_units=("kg CO2e/kWh",),
    )

    assert result.is_valid is True
    assert result.warning_count == 1
    assert _diagnostic_codes(result) == ("NORMALIZED_FACTOR_UNSUPPORTED_UNIT",)
    assert result.diagnostics[0].severity == DataQualityValidationSeverity.WARNING


def test_duplicate_factor_identity_is_blocking_error() -> None:
    first = _record(record_id="record-001", factor_id="F1")
    duplicate = _record(record_id="record-002", factor_id="F1")

    result = validate_normalized_factor_output(
        NormalizationResult(records=(first, duplicate))
    )

    assert result.is_valid is False
    assert _diagnostic_codes(result) == ("NORMALIZED_FACTOR_DUPLICATE_IDENTITY",)
    diagnostic = result.diagnostics[0]
    assert diagnostic.check == DataQualityValidationCheck.DUPLICATE_FACTOR_IDENTITY
    assert dict(diagnostic.context)["first_record_position"] == 1
    assert dict(diagnostic.context)["record_position"] == 2


def test_provenance_gaps_are_warnings_with_safe_source_context() -> None:
    record = _record(record_id="record-001", source_reference=None, row_number=None)

    result = validate_normalized_factor_output(NormalizationResult(records=(record,)))

    assert result.is_valid is True
    assert _diagnostic_codes(result) == ("NORMALIZED_FACTOR_PROVENANCE_GAP",)
    diagnostic = result.diagnostics[0]
    assert diagnostic.source_family == "defra_desnz"
    assert diagnostic.provenance == DataQualityProvenanceContext(
        record_id="record-001",
        source_family="defra_desnz",
        source_id="defra_desnz",
        source_reference=None,
        row_number=None,
        provenance=None,
        document_id=None,
    )
    assert diagnostic.context == (("record_position", 1),)


def test_diagnostics_are_deterministically_ordered_by_record_then_code() -> None:
    first = _record(
        record_id="record-001",
        factor_id="",
        factor_value="bad",
        unit="bad-unit",
    )
    second = _record(record_id="record-002", factor_id="", unit="bad-unit")

    result = validate_normalized_factor_output(
        NormalizationResult(records=(second, first))
    )

    assert tuple(
        (dict(diagnostic.context)["record_position"], diagnostic.code)
        for diagnostic in result.diagnostics
    ) == (
        (1, "NORMALIZED_FACTOR_MISSING_REQUIRED_FIELD"),
        (1, "NORMALIZED_FACTOR_UNSUPPORTED_UNIT"),
        (2, "NORMALIZED_FACTOR_INVALID_NUMERIC_VALUE"),
        (2, "NORMALIZED_FACTOR_MISSING_REQUIRED_FIELD"),
        (2, "NORMALIZED_FACTOR_UNSUPPORTED_UNIT"),
    )


def test_sensitive_values_are_redacted_from_diagnostic_context() -> None:
    diagnostic = create_data_quality_diagnostic(
        code="SAFE_CONTEXT",
        message="safe context diagnostic",
        severity=DataQualityValidationSeverity.INFO,
        check=DataQualityValidationCheck.STRUCTURE,
        context={
            "api_key": "abc123",
            "nested": {"password": "secret-value", "visible": "ok"},
            "source_reference": "https://user:pass@example.invalid/?token=abc123",
            "token_values": ("one", "two"),
        },
    )

    context = dict(diagnostic.context)

    assert context["api_key"] == REDACTED_DIAGNOSTIC_VALUE
    assert ("password", REDACTED_DIAGNOSTIC_VALUE) in context["nested"]
    assert ("visible", "ok") in context["nested"]
    assert context["source_reference"] == (
        "https://[REDACTED]@example.invalid/?token=[REDACTED]"
    )
    assert context["token_values"] == (
        REDACTED_DIAGNOSTIC_VALUE,
        REDACTED_DIAGNOSTIC_VALUE,
    )
    assert "abc123" not in repr(diagnostic)
    assert "pass" not in repr(diagnostic)
    assert "secret-value" not in repr(diagnostic)


def test_sensitive_values_are_redacted_from_provenance_context() -> None:
    record = _record(
        source_reference="https://user:pass@example.invalid/factors.csv?token=abc123",
        row_number=None,
        unit="unsupported",
    )

    result = validate_normalized_factor_output(NormalizationResult(records=(record,)))

    diagnostic = result.diagnostics[0]
    assert diagnostic.provenance is not None
    assert diagnostic.provenance.source_reference == (
        "https://[REDACTED]@example.invalid/factors.csv?token=[REDACTED]"
    )

    assert "pass" not in repr(diagnostic)
    assert "abc123" not in repr(diagnostic)


def test_valid_factor_output_has_no_diagnostics() -> None:
    result = validate_normalized_factor_output(
        NormalizationResult(records=(_record(),))
    )

    assert result == DataQualityValidationResult()
    assert result.is_valid is True


def test_validation_model_dataclasses_are_frozen() -> None:
    diagnostic = create_data_quality_diagnostic(
        code="INFO",
        message="info",
        severity=DataQualityValidationSeverity.INFO,
        check=DataQualityValidationCheck.STRUCTURE,
    )
    result = DataQualityValidationResult(diagnostics=(diagnostic,))

    with pytest.raises(FrozenInstanceError):
        diagnostic.code = "changed"
    with pytest.raises(FrozenInstanceError):
        result.diagnostics = ()


def _record(
    *,
    record_id: str = "record-001",
    source_reference: str | None = "memory://defra",
    source_family: object = "defra_desnz",
    source_id: object = "defra_desnz",
    source_year: object = "2024",
    source_version: object = "v1",
    row_number: object = 2,
    factor_id: object = "F1",
    factor_name: object = "Electricity",
    factor_value: object = 0.233,
    unit: object = "kg CO2e/kWh",
) -> NormalizedRecord:
    fields = (
        ("source_family", source_family),
        ("source_id", source_id),
        ("source_year", source_year),
        ("source_version", source_version),
        ("row_number", row_number),
        ("factor_id", factor_id),
        ("factor_name", factor_name),
        ("factor_value", factor_value),
        ("unit", unit),
    )
    return NormalizedRecord(
        record_id=record_id,
        fields=tuple((key, value) for key, value in fields if value is not None),
        source_reference=source_reference,
        is_artificial=False,
    )


def _diagnostic_codes(
    result: DataQualityValidationResult,
) -> tuple[str, ...]:
    return tuple(diagnostic.code for diagnostic in result.diagnostics)
