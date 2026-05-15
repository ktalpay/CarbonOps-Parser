"""Phase 2 data quality validation for normalized factor output."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from carbonfactor_parser.normalization.contracts import (
    NormalizationResult,
    NormalizedRecord,
)


DEFAULT_SUPPORTED_FACTOR_UNITS = (
    "kg",
    "kg CO2e",
    "kg CO2e/kWh",
    "kWh",
)

REDACTED_DIAGNOSTIC_VALUE = "[REDACTED]"

_REQUIRED_FACTOR_FIELDS = (
    "source_family",
    "source_id",
    "factor_id",
    "factor_name",
    "factor_value",
    "unit",
)

_PROVENANCE_FIELD_NAMES = (
    "provenance",
    "row_number",
    "source_document_id",
    "document_id",
)

_SENSITIVE_FIELD_TOKENS = (
    "api_key",
    "authorization",
    "credential",
    "password",
    "secret",
    "token",
)

_SENSITIVE_ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b(api[_-]?key|authorization|credential|password|secret|token)=([^\s&;,]+)",
)


class DataQualityValidationSeverity(str, Enum):
    """Severity levels for normalized factor data quality diagnostics."""

    BLOCKING_ERROR = "blocking_error"
    WARNING = "warning"
    INFO = "info"


class DataQualityValidationCheck(str, Enum):
    """Stable data quality check classifications."""

    REQUIRED_FIELD = "required_field"
    NUMERIC_VALUE = "numeric_value"
    UNIT = "unit"
    DUPLICATE_FACTOR_IDENTITY = "duplicate_factor_identity"
    PROVENANCE = "provenance"
    STRUCTURE = "structure"


@dataclass(frozen=True)
class DataQualityProvenanceContext:
    """Safe row and document context for a normalized factor diagnostic."""

    record_id: str
    source_family: str | None = None
    source_id: str | None = None
    source_reference: str | None = None
    row_number: object | None = None
    provenance: str | None = None
    document_id: str | None = None


@dataclass(frozen=True)
class DataQualityDiagnostic:
    """One safe diagnostic emitted by normalized factor validation."""

    code: str
    message: str
    severity: DataQualityValidationSeverity
    check: DataQualityValidationCheck
    field_name: str | None = None
    source_family: str | None = None
    provenance: DataQualityProvenanceContext | None = None
    context: tuple[tuple[str, object], ...] = ()

    def __repr__(self) -> str:
        safe_context = tuple(
            (
                REDACTED_DIAGNOSTIC_VALUE if _is_sensitive_field(key) else key,
                _repr_safe_diagnostic_value(value),
            )
            for key, value in self.context
        )
        safe_provenance = (
            None
            if self.provenance is None
            else DataQualityProvenanceContext(
                record_id=_repr_safe_diagnostic_value(self.provenance.record_id),
                source_family=_repr_safe_diagnostic_value(
                    self.provenance.source_family
                ),
                source_id=_repr_safe_diagnostic_value(self.provenance.source_id),
                source_reference=_repr_safe_diagnostic_value(
                    self.provenance.source_reference
                ),
                row_number=_repr_safe_diagnostic_value(self.provenance.row_number),
                provenance=_repr_safe_diagnostic_value(self.provenance.provenance),
                document_id=_repr_safe_diagnostic_value(self.provenance.document_id),
            )
        )
        return (
            "DataQualityDiagnostic("
            f"code={self.code!r}, "
            f"message={self.message!r}, "
            f"severity={self.severity!r}, "
            f"check={self.check!r}, "
            f"field_name={self.field_name!r}, "
            f"source_family={self.source_family!r}, "
            f"provenance={safe_provenance!r}, "
            f"context={safe_context!r})"
        )


@dataclass(frozen=True)
class DataQualityValidationResult:
    """Deterministic result for normalized factor data quality validation."""

    diagnostics: tuple[DataQualityDiagnostic, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.has_blocking_errors

    @property
    def has_blocking_errors(self) -> bool:
        return any(
            diagnostic.severity == DataQualityValidationSeverity.BLOCKING_ERROR
            for diagnostic in self.diagnostics
        )

    @property
    def blocking_error_count(self) -> int:
        return _severity_count(
            self.diagnostics,
            DataQualityValidationSeverity.BLOCKING_ERROR,
        )

    @property
    def warning_count(self) -> int:
        return _severity_count(
            self.diagnostics,
            DataQualityValidationSeverity.WARNING,
        )

    @property
    def info_count(self) -> int:
        return _severity_count(self.diagnostics, DataQualityValidationSeverity.INFO)


def create_data_quality_diagnostic(
    *,
    code: str,
    message: str,
    severity: DataQualityValidationSeverity,
    check: DataQualityValidationCheck,
    field_name: str | None = None,
    source_family: str | None = None,
    provenance: DataQualityProvenanceContext | None = None,
    context: Mapping[str, object] | None = None,
) -> DataQualityDiagnostic:
    """Create one diagnostic with deterministic redacted context."""

    return DataQualityDiagnostic(
        code=code,
        message=message,
        severity=severity,
        check=check,
        field_name=field_name,
        source_family=source_family,
        provenance=provenance,
        context=_safe_context(context),
    )


def validate_normalized_factor_output(
    normalization_result: NormalizationResult,
    *,
    supported_units: Iterable[str] = DEFAULT_SUPPORTED_FACTOR_UNITS,
) -> DataQualityValidationResult:
    """Validate normalized factor output before persistence or API use."""

    unit_set = frozenset(supported_units)
    diagnostics: list[DataQualityDiagnostic] = []
    identity_positions: dict[tuple[object, ...], int] = {}

    for position, record in enumerate(normalization_result.records, start=1):
        fields = dict(record.fields)
        provenance = _provenance_context(record, fields)
        source_family = _text_or_none(fields.get("source_family"))

        diagnostics.extend(
            _missing_required_field_diagnostics(
                fields,
                position,
                source_family,
                provenance,
            )
        )
        diagnostics.extend(
            _invalid_numeric_diagnostics(
                fields,
                position,
                source_family,
                provenance,
            )
        )
        diagnostics.extend(
            _unsupported_unit_diagnostics(
                fields,
                unit_set,
                position,
                source_family,
                provenance,
            )
        )
        diagnostics.extend(
            _provenance_gap_diagnostics(
                record,
                fields,
                position,
                source_family,
                provenance,
            )
        )

        identity = _factor_identity(fields)
        if identity is not None:
            first_position = identity_positions.get(identity)
            if first_position is None:
                identity_positions[identity] = position
            else:
                diagnostics.append(
                    create_data_quality_diagnostic(
                        code="NORMALIZED_FACTOR_DUPLICATE_IDENTITY",
                        message=(
                            "normalized factor identity must be unique within "
                            "the validation result."
                        ),
                        severity=DataQualityValidationSeverity.BLOCKING_ERROR,
                        check=DataQualityValidationCheck.DUPLICATE_FACTOR_IDENTITY,
                        field_name="factor_id",
                        source_family=source_family,
                        provenance=provenance,
                        context={
                            "first_record_position": first_position,
                            "record_position": position,
                        },
                    )
                )

    return DataQualityValidationResult(
        diagnostics=tuple(
            sorted(
                diagnostics,
                key=lambda diagnostic: (
                    _context_value(diagnostic, "record_position"),
                    diagnostic.code,
                    diagnostic.field_name or "",
                ),
            )
        ),
    )


def _missing_required_field_diagnostics(
    fields: Mapping[str, object],
    position: int,
    source_family: str | None,
    provenance: DataQualityProvenanceContext,
) -> tuple[DataQualityDiagnostic, ...]:
    diagnostics: list[DataQualityDiagnostic] = []
    for field_name in _REQUIRED_FACTOR_FIELDS:
        if _missing_field(fields, field_name):
            diagnostics.append(
                create_data_quality_diagnostic(
                    code="NORMALIZED_FACTOR_MISSING_REQUIRED_FIELD",
                    message=(
                        "normalized factor output is missing a required field."
                    ),
                    severity=DataQualityValidationSeverity.BLOCKING_ERROR,
                    check=DataQualityValidationCheck.REQUIRED_FIELD,
                    field_name=field_name,
                    source_family=source_family,
                    provenance=provenance,
                    context={
                        "record_position": position,
                        "field_name": field_name,
                    },
                )
            )
    return tuple(diagnostics)


def _invalid_numeric_diagnostics(
    fields: Mapping[str, object],
    position: int,
    source_family: str | None,
    provenance: DataQualityProvenanceContext,
) -> tuple[DataQualityDiagnostic, ...]:
    if _missing_field(fields, "factor_value"):
        return ()
    value = fields.get("factor_value")
    if _is_valid_numeric(value):
        return ()
    return (
        create_data_quality_diagnostic(
            code="NORMALIZED_FACTOR_INVALID_NUMERIC_VALUE",
            message="normalized factor_value must be numeric.",
            severity=DataQualityValidationSeverity.BLOCKING_ERROR,
            check=DataQualityValidationCheck.NUMERIC_VALUE,
            field_name="factor_value",
            source_family=source_family,
            provenance=provenance,
            context={
                "record_position": position,
                "field_name": "factor_value",
            },
        ),
    )


def _unsupported_unit_diagnostics(
    fields: Mapping[str, object],
    supported_units: frozenset[str],
    position: int,
    source_family: str | None,
    provenance: DataQualityProvenanceContext,
) -> tuple[DataQualityDiagnostic, ...]:
    if _missing_field(fields, "unit"):
        return ()
    unit = fields.get("unit")
    if isinstance(unit, str) and unit.strip() in supported_units:
        return ()
    return (
        create_data_quality_diagnostic(
            code="NORMALIZED_FACTOR_UNSUPPORTED_UNIT",
            message=(
                "normalized factor unit is not in the configured supported "
                "unit set."
            ),
            severity=DataQualityValidationSeverity.WARNING,
            check=DataQualityValidationCheck.UNIT,
            field_name="unit",
            source_family=source_family,
            provenance=provenance,
            context={
                "record_position": position,
                "field_name": "unit",
                "supported_unit_count": len(supported_units),
            },
        ),
    )


def _provenance_gap_diagnostics(
    record: NormalizedRecord,
    fields: Mapping[str, object],
    position: int,
    source_family: str | None,
    provenance: DataQualityProvenanceContext,
) -> tuple[DataQualityDiagnostic, ...]:
    has_field_provenance = any(
        not _missing_field(fields, name) for name in _PROVENANCE_FIELD_NAMES
    )
    if record.source_reference or has_field_provenance:
        return ()
    return (
        create_data_quality_diagnostic(
            code="NORMALIZED_FACTOR_PROVENANCE_GAP",
            message=(
                "normalized factor output should include row or document "
                "provenance before downstream use."
            ),
            severity=DataQualityValidationSeverity.WARNING,
            check=DataQualityValidationCheck.PROVENANCE,
            source_family=source_family,
            provenance=provenance,
            context={"record_position": position},
        ),
    )


def _factor_identity(fields: Mapping[str, object]) -> tuple[object, ...] | None:
    identity_fields = (
        "source_family",
        "source_id",
        "source_year",
        "source_version",
        "factor_id",
        "unit",
    )
    if any(_missing_field(fields, field_name) for field_name in identity_fields):
        return None
    return tuple(_identity_value(fields[field_name]) for field_name in identity_fields)


def _provenance_context(
    record: NormalizedRecord,
    fields: Mapping[str, object],
) -> DataQualityProvenanceContext:
    return DataQualityProvenanceContext(
        record_id=record.record_id,
        source_family=_safe_text_or_none(fields.get("source_family")),
        source_id=_safe_text_or_none(fields.get("source_id")),
        source_reference=_safe_text_or_none(record.source_reference),
        row_number=fields.get("row_number"),
        provenance=_safe_text_or_none(fields.get("provenance")),
        document_id=(
            _safe_text_or_none(fields.get("source_document_id"))
            or _safe_text_or_none(fields.get("document_id"))
        ),
    )


def _missing_field(fields: Mapping[str, object], field_name: str) -> bool:
    value = fields.get(field_name)
    return value is None or (isinstance(value, str) and not value.strip())


def _is_valid_numeric(value: object) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int | float):
        return True
    if isinstance(value, str) and value.strip():
        try:
            float(value.strip())
        except ValueError:
            return False
        return True
    return False


def _identity_value(value: object) -> object:
    if isinstance(value, str):
        return value.strip()
    return value


def _text_or_none(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _safe_text_or_none(value: object) -> str | None:
    text = _text_or_none(value)
    if text is None:
        return None
    without_userinfo = _redact_uri_userinfo(_redact_uri_userinfo_pattern(text))
    return _SENSITIVE_ASSIGNMENT_PATTERN.sub(
        lambda match: f"{match.group(1)}={REDACTED_DIAGNOSTIC_VALUE}",
        without_userinfo,
    )


def _redact_uri_userinfo(value: str) -> str:
    try:
        parts = urlsplit(value)
    except ValueError:
        return value

    if not parts.scheme or "@" not in parts.netloc:
        return value

    _, separator, hostinfo = parts.netloc.rpartition("@")
    if not separator:
        return value
    return urlunsplit(
        (
            parts.scheme,
            f"{REDACTED_DIAGNOSTIC_VALUE}@{hostinfo}",
            parts.path,
            parts.query,
            parts.fragment,
        )
    )


def _redact_uri_userinfo_pattern(value: str) -> str:
    return re.sub(
        r"(?i)\b([a-z][a-z0-9+.-]*://)([^\s/?#]+@)",
        lambda match: f"{match.group(1)}{REDACTED_DIAGNOSTIC_VALUE}@",
        value,
    )


def _safe_context(
    context: Mapping[str, object] | None,
) -> tuple[tuple[str, object], ...]:
    if context is None:
        return ()
    return tuple(
        (str(key), _safe_diagnostic_value(str(key), value))
        for key, value in sorted(context.items(), key=lambda item: str(item[0]))
    )


def _safe_diagnostic_value(field_name: str, value: object) -> object:
    if isinstance(value, Mapping):
        return tuple(
            (str(key), _safe_diagnostic_value(str(key), item))
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        )
    if isinstance(value, list | tuple):
        return tuple(_safe_diagnostic_value(field_name, item) for item in value)
    if _is_sensitive_field(field_name):
        return REDACTED_DIAGNOSTIC_VALUE if value is not None else None
    if isinstance(value, str):
        return _safe_text_or_none(value)
    return value


def _repr_safe_diagnostic_value(value: object) -> object:
    if isinstance(value, tuple):
        if all(isinstance(item, tuple) and len(item) == 2 for item in value):
            return tuple(
                (
                    (
                        REDACTED_DIAGNOSTIC_VALUE
                        if _is_sensitive_field(str(item[0]))
                        else item[0]
                    ),
                    _repr_safe_diagnostic_value(item[1]),
                )
                for item in value
            )
        return tuple(_repr_safe_diagnostic_value(item) for item in value)
    if isinstance(value, list):
        return tuple(_repr_safe_diagnostic_value(item) for item in value)
    if isinstance(value, str):
        return _safe_text_or_none(value)
    return value


def _is_sensitive_field(field_name: str) -> bool:
    normalized = field_name.lower()
    return any(token in normalized for token in _SENSITIVE_FIELD_TOKENS)


def _context_value(diagnostic: DataQualityDiagnostic, key: str) -> object:
    return dict(diagnostic.context).get(key, 0)


def _severity_count(
    diagnostics: tuple[DataQualityDiagnostic, ...],
    severity: DataQualityValidationSeverity,
) -> int:
    return sum(diagnostic.severity == severity for diagnostic in diagnostics)
