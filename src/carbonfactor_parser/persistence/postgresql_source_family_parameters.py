"""PostgreSQL source-family master/detail parameter mapping helpers."""

from __future__ import annotations

from decimal import Decimal
import json
from typing import Mapping

from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    source_family_postgresql_value,
)
from carbonfactor_parser.persistence.postgresql_source_family_ids import (
    detail_uuid,
    ingestion_run_uuid,
    master_uuid,
    source_document_uuid,
)
from carbonfactor_parser.persistence.source_family_repository import (
    SourceFamilyDetailRecord,
    SourceFamilyMasterRecord,
)


def master_parameters(record: SourceFamilyMasterRecord) -> tuple[object, ...]:
    """Return PostgreSQL parameters for a source-family master row."""

    ingestion_id = ingestion_run_uuid(record)
    return (
        str(master_uuid(record.source_family, record.source_family_master_id)),
        source_family_postgresql_value(record.source_family),
        record.source_year,
        record.source_version,
        record.source_release,
        str(source_document_uuid(record)),
        str(ingestion_id) if ingestion_id else None,
        record.run_id,
        record.master_external_key,
        record.status,
        record.artifact_reference,
        record.artifact_checksum_sha256,
        record.archive_reference,
        record.archive_checksum_sha256,
        record.effective_from,
        record.effective_to,
        record.record_checksum_sha256,
        json_payload(record.metadata),
    )


def detail_parameters(record: SourceFamilyDetailRecord) -> tuple[object, ...]:
    """Return PostgreSQL parameters for a source-family detail row."""

    return (
        str(detail_uuid(record.source_family, record.source_family_detail_id)),
        str(master_uuid(record.source_family, record.source_family_master_id)),
        record.detail_external_key,
        record.source_row_number,
        record.factor_id,
        record.factor_name,
        str(Decimal(str(record.factor_value))),
        record.factor_unit,
        record.status,
        record.record_checksum_sha256,
        json_payload(record.raw_fields),
        json_payload(record.normalized_fields),
    )


def json_payload(value: Mapping[str, object]) -> str:
    """Return compact, sorted JSON for PostgreSQL JSONB parameters."""

    return json.dumps(json_safe(value), sort_keys=True, separators=(",", ":"))


def json_safe(value: object) -> object:
    """Convert values that are not JSON-native while preserving payload shape."""

    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Mapping):
        return {
            str(key): json_safe(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    if isinstance(value, tuple | list):
        return [json_safe(item) for item in value]
    return value


__all__ = (
    "detail_parameters",
    "json_payload",
    "json_safe",
    "master_parameters",
)
