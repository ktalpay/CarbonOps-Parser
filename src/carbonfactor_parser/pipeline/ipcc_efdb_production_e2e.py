"""IPCC EFDB production E2E ingestion adapters.

This module wires configured year-scoped IPCC EFDB source artifacts into the
shared production year orchestrator. It downloads only explicitly configured
artifacts, parses the existing normalized EFDB CSV extraction format, validates
normalized rows, and leaves persistence to the injected PostgreSQL repository.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Callable, Mapping
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from carbonfactor_parser.normalization.contracts import (
    NormalizationResult,
    NormalizedRecord,
)
from carbonfactor_parser.normalization.data_quality_validation import (
    DataQualityValidationSeverity,
    validate_normalized_factor_output,
)
from carbonfactor_parser.parsers import create_parser_file_content_input
from carbonfactor_parser.parsers.execution_result import ParserExecutionResultStatus
from carbonfactor_parser.parsers.ipcc_efdb_content_parser import (
    parse_ipcc_efdb_file_content,
)
from carbonfactor_parser.parsers.normalized_output_row_contract import (
    ParserNormalizedOutputBatch,
    ParserNormalizedOutputRow,
    ParserNormalizedOutputRowStatus,
    create_parser_normalized_output_batch,
    validate_parser_normalized_output_batch,
)
from carbonfactor_parser.parsers.selection_registry_contract import (
    PHASE1_PARSER_KEYS_BY_SOURCE_FAMILY,
)
from carbonfactor_parser.pipeline.production_e2e_year_orchestrator import (
    ProductionE2EDownloadedArtifact,
    ProductionE2EFailureDetail,
    ProductionE2ESourceYearDiscoveryRequest,
    ProductionE2ESourceYearDiscoveryResult,
    ProductionE2ESourceYearDiscoveryStatus,
    ProductionE2ESourceYearDownloadResult,
    ProductionE2ESourceYearDownloadStatus,
    ProductionE2EValidationResult,
    ProductionE2EValidationStatus,
)


IPCC_EFDB_SOURCE_FAMILY = "ipcc_efdb"
IPCC_EFDB_SOURCE_ID = "ipcc_efdb"
IPCC_EFDB_PARSER_KEY = PHASE1_PARSER_KEYS_BY_SOURCE_FAMILY[
    IPCC_EFDB_SOURCE_FAMILY
]


@dataclass(frozen=True)
class IpccEfdbSourceYear:
    """Configured IPCC EFDB source-year artifact metadata."""

    year: int
    publication_url: str
    artifact_url: str
    title: str
    version_label: str
    content_type: str = "text/csv"
    format_hint: str = "csv"


DEFAULT_IPCC_EFDB_SOURCE_YEARS: Mapping[int, IpccEfdbSourceYear] = {}
IPCC_EFDB_DISCOVERY_STRATEGY = "configured_artifact_required"

DownloadTransport = Callable[[str], bytes]


class IpccEfdbProductionSourceAdapter:
    """Discover and download configured IPCC EFDB year-scoped artifacts."""

    source_family = IPCC_EFDB_SOURCE_FAMILY

    def __init__(
        self,
        *,
        target_root: str | Path,
        source_years: Mapping[int, IpccEfdbSourceYear] | None = None,
        transport: DownloadTransport | None = None,
    ) -> None:
        self._target_root = Path(target_root)
        self._source_years = dict(
            DEFAULT_IPCC_EFDB_SOURCE_YEARS
            if source_years is None
            else source_years
        )
        self._transport = transport or _https_download

    def discover_target_year(
        self,
        request: ProductionE2ESourceYearDiscoveryRequest,
    ) -> ProductionE2ESourceYearDiscoveryResult:
        """Return configured metadata for exactly one target year."""

        source_year = self._source_years.get(request.target_year)
        if source_year is None or not source_year.artifact_url.strip():
            return ProductionE2ESourceYearDiscoveryResult(
                status=(
                    ProductionE2ESourceYearDiscoveryStatus.NO_AVAILABLE_SOURCE_YEAR
                ),
                source_family=request.source_family,
                target_year=request.target_year,
                reason_code="ipcc_efdb_target_year_not_configured",
                metadata={
                    "availability_strategy": IPCC_EFDB_DISCOVERY_STRATEGY,
                    "configured_years": tuple(sorted(self._source_years)),
                    "requires_configured_artifact_url": True,
                    "user_message": (
                        "IPCC EFDB has no stable public year-index artifact "
                        "discovery contract in this ingestion boundary; "
                        "configure an artifact_url for the target source year."
                    ),
                },
            )

        return ProductionE2ESourceYearDiscoveryResult(
            status=ProductionE2ESourceYearDiscoveryStatus.SOURCE_YEAR_AVAILABLE,
            source_family=request.source_family,
            target_year=request.target_year,
            artifact_reference=source_year.artifact_url,
            metadata={
                "availability_strategy": IPCC_EFDB_DISCOVERY_STRATEGY,
                "publication_url": source_year.publication_url,
                "title": source_year.title,
                "version_label": source_year.version_label,
                "content_type": source_year.content_type,
                "format_hint": source_year.format_hint,
                "requires_configured_artifact_url": True,
            },
        )

    def download_target_year(
        self,
        discovery_result: ProductionE2ESourceYearDiscoveryResult,
    ) -> ProductionE2ESourceYearDownloadResult:
        """Download and archive the discovered IPCC EFDB source artifact."""

        if discovery_result.artifact_reference is None:
            return ProductionE2ESourceYearDownloadResult(
                status=ProductionE2ESourceYearDownloadStatus.FAILED,
                source_family=discovery_result.source_family,
                target_year=discovery_result.target_year,
                issues=(
                    _failure(
                        "download",
                        "IPCC_EFDB_PRODUCTION_MISSING_ARTIFACT_REFERENCE",
                        "Discovery did not provide a source artifact reference.",
                        "discovery_result.artifact_reference",
                    ),
                ),
            )

        try:
            content = self._transport(discovery_result.artifact_reference)
        except Exception as exc:  # noqa: BLE001 - transport varies by runtime
            return ProductionE2ESourceYearDownloadResult(
                status=ProductionE2ESourceYearDownloadStatus.FAILED,
                source_family=discovery_result.source_family,
                target_year=discovery_result.target_year,
                issues=(
                    _failure(
                        "download",
                        "IPCC_EFDB_PRODUCTION_DOWNLOAD_FAILED",
                        str(exc) or exc.__class__.__name__,
                        "artifact_reference",
                    ),
                ),
            )

        metadata = dict(discovery_result.metadata or {})
        checksum = sha256(content).hexdigest()
        filename = _artifact_filename(
            discovery_result.artifact_reference,
            discovery_result.target_year,
            str(metadata.get("format_hint") or "csv"),
        )
        target_dir = (
            self._target_root
            / IPCC_EFDB_SOURCE_FAMILY
            / str(discovery_result.target_year)
        )
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename
        metadata_path = target_dir / f"{filename}.metadata.json"

        if target_path.exists() and target_path.read_bytes() != content:
            target_path.unlink()
        if not target_path.exists():
            target_path.write_bytes(content)

        metadata_payload = {
            "source_family": IPCC_EFDB_SOURCE_FAMILY,
            "source_year": discovery_result.target_year,
            "artifact_reference": discovery_result.artifact_reference,
            "local_path": str(target_path),
            "checksum_sha256": checksum,
            "size_bytes": len(content),
            **metadata,
        }
        metadata_path.write_text(
            json.dumps(metadata_payload, sort_keys=True, indent=2),
            encoding="utf-8",
        )

        return ProductionE2ESourceYearDownloadResult(
            status=ProductionE2ESourceYearDownloadStatus.DOWNLOADED,
            source_family=discovery_result.source_family,
            target_year=discovery_result.target_year,
            artifact=ProductionE2EDownloadedArtifact(
                source_family=discovery_result.source_family,
                source_year=discovery_result.target_year,
                artifact_reference=str(target_path),
                checksum_sha256=checksum,
                content_type=_text_or_none(metadata.get("content_type")),
                format_hint=_text_or_none(metadata.get("format_hint")),
                metadata={
                    **metadata_payload,
                    "metadata_path": str(metadata_path),
                    "source_reference_uri": discovery_result.artifact_reference,
                },
            ),
        )


class IpccEfdbProductionParserBoundary:
    """Parse downloaded IPCC EFDB normalized CSV artifacts into rows."""

    def parse(
        self,
        artifact: ProductionE2EDownloadedArtifact,
    ) -> ParserNormalizedOutputBatch:
        path = _artifact_path(artifact.artifact_reference)
        content = path.read_bytes()
        result = parse_ipcc_efdb_file_content(
            create_parser_file_content_input(
                source_family=IPCC_EFDB_SOURCE_FAMILY,
                source_id=IPCC_EFDB_SOURCE_ID,
                content=content,
                content_type=artifact.content_type,
                format_hint=artifact.format_hint,
                artifact_reference=artifact.artifact_reference,
                checksum_sha256=artifact.checksum_sha256,
            )
        )
        if result.status is not ParserExecutionResultStatus.SUCCESS:
            codes = ", ".join(issue.code for issue in result.issues)
            raise ValueError(
                "IPCC EFDB production parser failed"
                + (f": {codes}" if codes else ".")
            )
        if result.raw_record_payload is None:
            return create_parser_normalized_output_batch(())

        rows = tuple(
            _normalized_row(artifact, record.raw_fields, record.row_number)
            for record in result.raw_record_payload.records
        )
        return create_parser_normalized_output_batch(rows)


class IpccEfdbPhase2ValidationBoundary:
    """Adapt Phase 2 normalized data-quality diagnostics to E2E validation."""

    def validate(
        self,
        batch: ParserNormalizedOutputBatch,
    ) -> ProductionE2EValidationResult:
        issues: list[ProductionE2EFailureDetail] = []
        parser_validation = validate_parser_normalized_output_batch(batch)
        for issue in parser_validation.issues:
            issues.append(
                ProductionE2EFailureDetail(
                    source_family=IPCC_EFDB_SOURCE_FAMILY,
                    stage="validation",
                    code=issue.code,
                    message=issue.message,
                    field_name=issue.field_name,
                    severity=issue.severity,
                )
            )

        normalization_result = NormalizationResult(
            records=tuple(
                NormalizedRecord(
                    record_id=row.row_id,
                    fields=row.normalized_fields,
                    source_reference=row.artifact_reference,
                    is_artificial=False,
                )
                for row in batch.rows
            ),
        )
        quality_result = validate_normalized_factor_output(normalization_result)
        for diagnostic in quality_result.diagnostics:
            issues.append(
                ProductionE2EFailureDetail(
                    source_family=diagnostic.source_family,
                    stage="validation",
                    code=diagnostic.code,
                    message=diagnostic.message,
                    field_name=diagnostic.field_name,
                    severity=diagnostic.severity.value,
                )
            )

        blocking_count = sum(
            issue.severity
            in {DataQualityValidationSeverity.BLOCKING_ERROR.value, "error"}
            for issue in issues
        )
        return ProductionE2EValidationResult(
            status=(
                ProductionE2EValidationStatus.FAILED_VALIDATION
                if blocking_count
                else ProductionE2EValidationStatus.VALIDATED
            ),
            diagnostic_count=len(issues),
            blocking_error_count=blocking_count,
            warning_count=sum(issue.severity == "warning" for issue in issues),
            issues=tuple(issues),
        )


def _normalized_row(
    artifact: ProductionE2EDownloadedArtifact,
    fields: Mapping[str, object],
    row_number: int | None,
) -> ParserNormalizedOutputRow:
    factor_id = str(fields["factor_id"])
    source_year = int(fields["source_year"])
    source_version = str(fields["source_version"])
    source_document_id = _source_document_id(artifact)
    normalized_fields = {
        **dict(fields),
        "source_family": IPCC_EFDB_SOURCE_FAMILY,
        "source_id": IPCC_EFDB_SOURCE_ID,
        "source_document_id": source_document_id,
        "source_artifact_reference": artifact.artifact_reference,
        "source_checksum_sha256": artifact.checksum_sha256,
        "factor_value": str(fields["factor_value"]),
        "factor_unit": fields["unit"],
        "greenhouse_gas": fields["gas"],
        "row_number": row_number,
    }
    row_id = f"ipcc_efdb:{source_year}:{source_version}:{factor_id}"
    return ParserNormalizedOutputRow(
        source_family=IPCC_EFDB_SOURCE_FAMILY,
        source_key=IPCC_EFDB_SOURCE_ID,
        parser_key=IPCC_EFDB_PARSER_KEY,
        artifact_reference=artifact.artifact_reference,
        row_id=row_id,
        normalized_fields=tuple(sorted(normalized_fields.items())),
        status=ParserNormalizedOutputRowStatus.VALIDATED,
        source_row_number=row_number,
        artifact_identifier=source_document_id,
        reporting_year=source_year,
    )


def _https_download(uri: str) -> bytes:
    parsed = urlparse(uri)
    if parsed.scheme != "https":
        raise ValueError("IPCC EFDB production downloads require HTTPS URIs.")
    request = Request(uri, headers={"User-Agent": "carbonops-parser/0.1"})
    with urlopen(request, timeout=60) as response:  # noqa: S310 - HTTPS only above
        return bytes(response.read())


def _artifact_filename(uri: str, year: int, format_hint: str) -> str:
    name = Path(urlparse(uri).path).name
    if name:
        return name
    return f"ipcc-efdb-factors-{year}.{format_hint}"


def _artifact_path(reference: str) -> Path:
    parsed = urlparse(reference)
    if parsed.scheme == "file":
        return Path(parsed.path)
    return Path(reference)


def _source_document_id(artifact: ProductionE2EDownloadedArtifact) -> str:
    checksum = artifact.checksum_sha256 or "checksum-unavailable"
    return f"ipcc_efdb:{artifact.source_year}:{checksum[:16]}"


def _text_or_none(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _failure(
    stage: str,
    code: str,
    message: str,
    field_name: str | None = None,
) -> ProductionE2EFailureDetail:
    return ProductionE2EFailureDetail(
        source_family=IPCC_EFDB_SOURCE_FAMILY,
        stage=stage,
        code=code,
        message=message,
        field_name=field_name,
    )


__all__ = (
    "DEFAULT_IPCC_EFDB_SOURCE_YEARS",
    "IPCC_EFDB_PARSER_KEY",
    "IPCC_EFDB_SOURCE_FAMILY",
    "IPCC_EFDB_SOURCE_ID",
    "IpccEfdbPhase2ValidationBoundary",
    "IpccEfdbProductionParserBoundary",
    "IpccEfdbProductionSourceAdapter",
    "IpccEfdbSourceYear",
)
