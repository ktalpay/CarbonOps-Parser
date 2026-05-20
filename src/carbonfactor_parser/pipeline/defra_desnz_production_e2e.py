"""DEFRA/DESNZ production E2E ingestion adapters.

The adapters in this module are intentionally narrow: they discover the
year-scoped GOV.UK flat-file publication, download/archive the source artifact,
parse normalized factor rows, and adapt Phase 2 data-quality diagnostics to the
production year orchestrator boundary.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Callable, Mapping
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
from zipfile import ZipFile

from carbonfactor_parser.normalization.contracts import (
    NormalizationResult,
    NormalizedRecord,
)
from carbonfactor_parser.normalization.data_quality_validation import (
    DataQualityValidationSeverity,
    validate_normalized_factor_output,
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


DEFRA_DESNZ_SOURCE_FAMILY = "defra_desnz"
DEFRA_DESNZ_SOURCE_ID = "defra_desnz"
DEFRA_DESNZ_PARSER_KEY = PHASE1_PARSER_KEYS_BY_SOURCE_FAMILY[
    DEFRA_DESNZ_SOURCE_FAMILY
]


@dataclass(frozen=True)
class DefraDesnzSourceYear:
    """Known DEFRA/DESNZ source-year publication metadata."""

    year: int
    publication_url: str
    artifact_url: str
    title: str
    version_label: str
    content_type: str = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    format_hint: str = "xlsx"


DEFAULT_DEFRA_DESNZ_SOURCE_YEARS: Mapping[int, DefraDesnzSourceYear] = {
    2024: DefraDesnzSourceYear(
        year=2024,
        publication_url=(
            "https://www.gov.uk/government/publications/"
            "greenhouse-gas-reporting-conversion-factors-2024"
        ),
        artifact_url="",
        title="Conversion factors 2024: flat file (for automatic processing only)",
        version_label="2024-v1.1",
    ),
    2025: DefraDesnzSourceYear(
        year=2025,
        publication_url=(
            "https://www.gov.uk/government/publications/"
            "greenhouse-gas-reporting-conversion-factors-2025"
        ),
        artifact_url="",
        title="Conversion factors 2025: flat file (for automatic processing only)",
        version_label="2025",
    ),
}
DEFRA_DESNZ_DISCOVERY_STRATEGY = "govuk_publication_flat_file_link"
DEFRA_DESNZ_DISCOVERY_AUTOMATION = (
    "configured_artifact_url_or_govuk_publication_page"
)


DownloadTransport = Callable[[str], bytes]


class DefraDesnzProductionSourceAdapter:
    """Discover and download known DEFRA/DESNZ year-scoped flat files."""

    source_family = DEFRA_DESNZ_SOURCE_FAMILY

    def __init__(
        self,
        *,
        target_root: str | Path,
        source_years: Mapping[int, DefraDesnzSourceYear] | None = None,
        transport: DownloadTransport | None = None,
    ) -> None:
        self._target_root = Path(target_root)
        self._source_years = dict(
            DEFAULT_DEFRA_DESNZ_SOURCE_YEARS
            if source_years is None
            else source_years
        )
        self._transport = transport or _https_download

    def discover_target_year(
        self,
        request: ProductionE2ESourceYearDiscoveryRequest,
    ) -> ProductionE2ESourceYearDiscoveryResult:
        """Return available metadata for exactly one target year."""

        source_year = self._source_years.get(request.target_year)
        if source_year is None:
            return ProductionE2ESourceYearDiscoveryResult(
                status=(
                    ProductionE2ESourceYearDiscoveryStatus.NO_AVAILABLE_SOURCE_YEAR
                ),
                source_family=request.source_family,
                target_year=request.target_year,
                reason_code="defra_desnz_target_year_not_in_availability_map",
                metadata={
                    "availability_strategy": DEFRA_DESNZ_DISCOVERY_STRATEGY,
                    "discovery_automation": DEFRA_DESNZ_DISCOVERY_AUTOMATION,
                    "configured_years": tuple(sorted(self._source_years)),
                    "user_message": (
                        "DEFRA/DESNZ target year is not in the configured "
                        "availability map. Add source_years configuration or "
                        "update the reviewed default availability map."
                    ),
                },
            )

        try:
            artifact_url = source_year.artifact_url or self._discover_flat_file_url(
                source_year,
            )
            discovery_failure_metadata: Mapping[str, object] = {}
        except Exception as exc:  # noqa: BLE001 - discovery transport varies by runtime
            artifact_url = None
            discovery_failure_metadata = {
                "discovery_error_type": exc.__class__.__name__,
                "discovery_error_message": _redacted_error_message(exc),
            }
        if artifact_url is None:
            return ProductionE2ESourceYearDiscoveryResult(
                status=(
                    ProductionE2ESourceYearDiscoveryStatus.NO_AVAILABLE_SOURCE_YEAR
                ),
                source_family=request.source_family,
                target_year=request.target_year,
                reason_code="defra_desnz_flat_file_link_not_found",
                metadata={
                    "availability_strategy": DEFRA_DESNZ_DISCOVERY_STRATEGY,
                    "discovery_automation": DEFRA_DESNZ_DISCOVERY_AUTOMATION,
                    "publication_url": source_year.publication_url,
                    "title": source_year.title,
                    "version_label": source_year.version_label,
                    "user_message": (
                        "DEFRA/DESNZ publication was configured for the target "
                        "year, but no GOV.UK flat-file artifact link was "
                        "resolved for download."
                    ),
                    **discovery_failure_metadata,
                },
            )

        return ProductionE2ESourceYearDiscoveryResult(
            status=ProductionE2ESourceYearDiscoveryStatus.SOURCE_YEAR_AVAILABLE,
            source_family=request.source_family,
            target_year=request.target_year,
            artifact_reference=artifact_url,
            metadata={
                "availability_strategy": DEFRA_DESNZ_DISCOVERY_STRATEGY,
                "discovery_automation": DEFRA_DESNZ_DISCOVERY_AUTOMATION,
                "publication_url": source_year.publication_url,
                "title": source_year.title,
                "version_label": source_year.version_label,
                "content_type": source_year.content_type,
                "format_hint": source_year.format_hint,
            },
        )

    def _discover_flat_file_url(
        self,
        source_year: DefraDesnzSourceYear,
    ) -> str | None:
        page = self._transport(source_year.publication_url).decode(
            "utf-8",
            errors="replace",
        )
        for href, label in re.findall(
            r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
            page,
            flags=re.IGNORECASE | re.DOTALL,
        ):
            clean_label = re.sub(r"<[^>]+>", " ", label)
            if "flat" not in clean_label.lower():
                continue
            if not href.startswith("https://assets.publishing.service.gov.uk/"):
                continue
            return href.replace("&amp;", "&")
        return None

    def download_target_year(
        self,
        discovery_result: ProductionE2ESourceYearDiscoveryResult,
    ) -> ProductionE2ESourceYearDownloadResult:
        """Download and archive the discovered source artifact locally."""

        if discovery_result.artifact_reference is None:
            return ProductionE2ESourceYearDownloadResult(
                status=ProductionE2ESourceYearDownloadStatus.FAILED,
                source_family=discovery_result.source_family,
                target_year=discovery_result.target_year,
                issues=(
                    _failure(
                        "download",
                        "DEFRA_DESNZ_PRODUCTION_MISSING_ARTIFACT_REFERENCE",
                        "Discovery did not provide a source artifact reference.",
                        "discovery_result.artifact_reference",
                    ),
                ),
            )

        try:
            content = self._transport(discovery_result.artifact_reference)
        except Exception as exc:  # noqa: BLE001 - transport implementation varies
            return ProductionE2ESourceYearDownloadResult(
                status=ProductionE2ESourceYearDownloadStatus.FAILED,
                source_family=discovery_result.source_family,
                target_year=discovery_result.target_year,
                issues=(
                    _failure(
                        "download",
                        "DEFRA_DESNZ_PRODUCTION_DOWNLOAD_FAILED",
                        _redacted_error_message(exc),
                        "artifact_reference",
                    ),
                ),
            )

        checksum = sha256(content).hexdigest()
        metadata = dict(discovery_result.metadata or {})
        filename = _artifact_filename(
            discovery_result.artifact_reference,
            discovery_result.target_year,
            str(metadata.get("format_hint") or "xlsx"),
        )
        target_dir = (
            self._target_root
            / DEFRA_DESNZ_SOURCE_FAMILY
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
            "source_family": DEFRA_DESNZ_SOURCE_FAMILY,
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


class DefraDesnzProductionParserBoundary:
    """Parse DEFRA/DESNZ CSV or XLSX flat-file artifacts into normalized rows."""

    def parse(
        self,
        artifact: ProductionE2EDownloadedArtifact,
    ) -> ParserNormalizedOutputBatch:
        path = _artifact_path(artifact.artifact_reference)
        rows = _read_xlsx_rows(path) if path.suffix.lower() == ".xlsx" else _read_csv_rows(path)
        normalized_rows = tuple(_normalized_row(artifact, row) for row in rows)
        return create_parser_normalized_output_batch(normalized_rows)


class DefraDesnzPhase2ValidationBoundary:
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
                    source_family=DEFRA_DESNZ_SOURCE_FAMILY,
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


def _https_download(uri: str) -> bytes:
    parsed = urlparse(uri)
    if parsed.scheme != "https":
        raise ValueError("DEFRA/DESNZ production downloads require HTTPS URIs.")
    request = Request(uri, headers={"User-Agent": "carbonops-parser/0.1"})
    with urlopen(request, timeout=60) as response:  # noqa: S310 - HTTPS only above
        return bytes(response.read())


def _redacted_error_message(exc: Exception) -> str:
    raw = str(exc).strip() or exc.__class__.__name__
    parsed = urlparse(raw)
    if parsed.scheme in {"http", "https"} and parsed.hostname:
        host = parsed.hostname
        try:
            port = parsed.port
        except ValueError:
            port = None
        authority = f"{host}:{port}" if port is not None else host
        return f"{parsed.scheme}://{authority}/..."
    return re.sub(r"(://)[^/@\s]+@([^/\s]+)", r"\1<redacted>@\2", raw)


def _read_csv_rows(path: Path) -> tuple[dict[str, object], ...]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return tuple(dict(row) for row in reader if any(row.values()))


def _read_xlsx_rows(path: Path) -> tuple[dict[str, object], ...]:
    table = _read_first_xlsx_table(path)
    if not table:
        return ()
    header_index = _find_header_row_index(table)
    headers = [_clean_header(value) for value in table[header_index]]
    rows: list[dict[str, object]] = []
    for raw_row in table[header_index + 1 :]:
        if not any(_text_or_none(value) for value in raw_row):
            continue
        row = {
            headers[index]: raw_row[index]
            for index in range(min(len(headers), len(raw_row)))
            if headers[index]
        }
        if row:
            rows.append(row)
    return tuple(rows)


def _read_first_xlsx_table(path: Path) -> list[list[object]]:
    with ZipFile(path) as archive:
        shared_strings = _read_shared_strings(archive)
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        rels = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        rel_targets = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in rels
            if "Id" in rel.attrib and "Target" in rel.attrib
        }
        sheet = workbook.find(".//{*}sheet")
        if sheet is None:
            return []
        relationship_id = sheet.attrib.get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        )
        if relationship_id is None:
            return []
        sheet_path = "xl/" + rel_targets[relationship_id].lstrip("/")
        root = ET.fromstring(archive.read(sheet_path))

    table: list[list[object]] = []
    for row in root.findall(".//{*}sheetData/{*}row"):
        values: list[object] = []
        for cell in row.findall("{*}c"):
            column_index = _cell_column_index(cell.attrib.get("r", ""))
            while len(values) < column_index:
                values.append("")
            values.append(_cell_value(cell, shared_strings))
        table.append(values)
    return table


def _read_shared_strings(archive: ZipFile) -> tuple[str, ...]:
    try:
        root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    except KeyError:
        return ()
    values: list[str] = []
    for item in root.findall("{*}si"):
        values.append("".join(text.text or "" for text in item.findall(".//{*}t")))
    return tuple(values)


def _cell_value(cell: ET.Element, shared_strings: tuple[str, ...]) -> object:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(text.text or "" for text in cell.findall(".//{*}t"))
    value_node = cell.find("{*}v")
    if value_node is None or value_node.text is None:
        return ""
    raw_value = value_node.text
    if cell_type == "s":
        return shared_strings[int(raw_value)]
    if cell_type == "str":
        return raw_value
    decimal_value = _decimal_or_none(raw_value)
    return decimal_value if decimal_value is not None else raw_value


def _find_header_row_index(table: list[list[object]]) -> int:
    for index, row in enumerate(table):
        normalized = {_header_key(value) for value in row}
        has_factor_value = bool(normalized & _FACTOR_VALUE_HEADER_KEYS) or any(
            value.startswith("ghgconversionfactor") for value in normalized
        )
        if has_factor_value and normalized & _UNIT_HEADER_KEYS:
            return index
    return 0


def _normalized_row(
    artifact: ProductionE2EDownloadedArtifact,
    row: Mapping[str, object],
) -> ParserNormalizedOutputRow:
    source_row_number = _positive_int(_first_value(row, "row_number", "Row")) or 0
    factor_value = _factor_value(row, artifact.source_year)
    factor_unit = _text_or_none(_first_value(row, *_UNIT_HEADERS)) or "kg CO2e"
    category = _text_or_none(_first_value(row, *_CATEGORY_HEADERS)) or "uncategorized"
    subcategory = _text_or_none(_first_value(row, *_SUBCATEGORY_HEADERS))
    activity = _text_or_none(_first_value(row, *_ACTIVITY_HEADERS))
    greenhouse_gas = _text_or_none(_first_value(row, *_GAS_HEADERS))
    factor_name = _factor_name(row, category, subcategory, activity, greenhouse_gas)
    factor_id = _text_or_none(_first_value(row, *_FACTOR_ID_HEADERS))
    if factor_id is None:
        factor_id = _stable_factor_id(artifact.source_year, factor_name, factor_unit)

    fields = {
        "source_family": DEFRA_DESNZ_SOURCE_FAMILY,
        "source_id": DEFRA_DESNZ_SOURCE_ID,
        "source_year": artifact.source_year,
        "source_version": _source_version(artifact),
        "source_checksum_sha256": artifact.checksum_sha256,
        "source_document_id": _source_document_id(artifact),
        "source_artifact_reference": artifact.artifact_reference,
        "row_number": source_row_number or None,
        "factor_id": factor_id,
        "factor_name": factor_name,
        "factor_value": str(factor_value),
        "factor_unit": factor_unit,
        "unit": factor_unit,
        "category": category,
        "subcategory": subcategory,
        "activity": activity,
        "greenhouse_gas": greenhouse_gas,
        "provenance": _provenance(artifact, source_row_number),
    }
    row_id = f"defra_desnz:{artifact.source_year}:{factor_id}"
    return ParserNormalizedOutputRow(
        source_family=DEFRA_DESNZ_SOURCE_FAMILY,
        source_key=DEFRA_DESNZ_SOURCE_ID,
        parser_key=DEFRA_DESNZ_PARSER_KEY,
        artifact_reference=artifact.artifact_reference,
        row_id=row_id,
        normalized_fields=tuple(sorted(fields.items(), key=lambda item: item[0])),
        status=ParserNormalizedOutputRowStatus.VALIDATED,
        source_row_number=source_row_number or None,
        artifact_identifier=_source_document_id(artifact),
        reporting_year=artifact.source_year,
    )


def _factor_value(row: Mapping[str, object], year: int) -> Decimal:
    value = _first_value(row, *_FACTOR_VALUE_HEADERS, f"GHG Conversion Factor {year}")
    decimal_value = _decimal_or_none(value)
    if decimal_value is None:
        raise ValueError("DEFRA/DESNZ factor row is missing a numeric factor value.")
    return decimal_value


def _factor_name(
    row: Mapping[str, object],
    category: str,
    subcategory: str | None,
    activity: str | None,
    greenhouse_gas: str | None,
) -> str:
    explicit = _text_or_none(_first_value(row, *_FACTOR_NAME_HEADERS))
    if explicit is not None:
        return explicit
    parts = tuple(
        part
        for part in (category, subcategory, activity, greenhouse_gas)
        if part is not None
    )
    return " / ".join(parts) if parts else "DEFRA/DESNZ factor"


def _first_value(row: Mapping[str, object], *headers: str) -> object | None:
    by_key = {_header_key(key): value for key, value in row.items()}
    for header in headers:
        value = by_key.get(_header_key(header))
        if _text_or_none(value) is not None or isinstance(value, int | float | Decimal):
            return value
    return None


def _header_key(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).strip().lower())


def _clean_header(value: object) -> str:
    return str(value).strip()


def _stable_factor_id(year: int, factor_name: str, factor_unit: str) -> str:
    digest = sha256(f"{year}\x1f{factor_name}\x1f{factor_unit}".encode()).hexdigest()
    return f"DEFRA-DESNZ-{year}-{digest[:16]}"


def _source_version(artifact: ProductionE2EDownloadedArtifact) -> str:
    version = _text_or_none((artifact.metadata or {}).get("version_label"))
    return version or f"conversion-factors-{artifact.source_year}"


def _source_document_id(artifact: ProductionE2EDownloadedArtifact) -> str:
    checksum = artifact.checksum_sha256 or "checksum-unavailable"
    return f"defra_desnz:{artifact.source_year}:{checksum[:16]}"


def _provenance(
    artifact: ProductionE2EDownloadedArtifact,
    source_row_number: int,
) -> str:
    if source_row_number > 0:
        return f"{artifact.artifact_reference}#row-{source_row_number}"
    return artifact.artifact_reference


def _artifact_filename(uri: str, year: int, format_hint: str) -> str:
    name = Path(urlparse(uri).path).name
    if name:
        return name
    return f"defra-desnz-conversion-factors-{year}.{format_hint}"


def _artifact_path(reference: str) -> Path:
    parsed = urlparse(reference)
    if parsed.scheme == "file":
        return Path(parsed.path)
    return Path(reference)


def _positive_int(value: object | None) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(str(value).strip())
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def _decimal_or_none(value: object | None) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    try:
        decimal_value = Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None
    return decimal_value if decimal_value.is_finite() else None


def _text_or_none(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _cell_column_index(cell_reference: str) -> int:
    letters = "".join(char for char in cell_reference if char.isalpha())
    if not letters:
        return 1
    index = 0
    for char in letters.upper():
        index = index * 26 + ord(char) - ord("A") + 1
    return index


def _failure(
    stage: str,
    code: str,
    message: str,
    field_name: str,
) -> ProductionE2EFailureDetail:
    return ProductionE2EFailureDetail(
        source_family=DEFRA_DESNZ_SOURCE_FAMILY,
        stage=stage,
        code=code,
        message=message,
        field_name=field_name,
    )


_FACTOR_VALUE_HEADERS = (
    "factor_value",
    "Factor Value",
    "GHG Conversion Factor",
    "Conversion Factor",
    "CO2e",
)
_FACTOR_VALUE_HEADER_KEYS = frozenset(_header_key(value) for value in _FACTOR_VALUE_HEADERS)
_UNIT_HEADERS = (
    "unit",
    "factor_unit",
    "UOM",
    "Unit",
    "GHG/Unit",
)
_UNIT_HEADER_KEYS = frozenset(_header_key(value) for value in _UNIT_HEADERS)
_CATEGORY_HEADERS = (
    "category",
    "Category",
    "Level 1",
    "Scope",
)
_SUBCATEGORY_HEADERS = (
    "subcategory",
    "Subcategory",
    "Level 2",
    "Level 3",
)
_ACTIVITY_HEADERS = (
    "activity",
    "Activity",
    "Level 4",
    "Column Text",
    "Name",
)
_GAS_HEADERS = (
    "greenhouse_gas",
    "GHG",
    "Gas",
)
_FACTOR_ID_HEADERS = (
    "factor_id",
    "Factor ID",
    "ID",
)
_FACTOR_NAME_HEADERS = (
    "factor_name",
    "Factor Name",
    "Name",
)


__all__ = (
    "DEFAULT_DEFRA_DESNZ_SOURCE_YEARS",
    "DEFRA_DESNZ_PARSER_KEY",
    "DEFRA_DESNZ_SOURCE_FAMILY",
    "DEFRA_DESNZ_SOURCE_ID",
    "DefraDesnzPhase2ValidationBoundary",
    "DefraDesnzProductionParserBoundary",
    "DefraDesnzProductionSourceAdapter",
    "DefraDesnzSourceYear",
)
