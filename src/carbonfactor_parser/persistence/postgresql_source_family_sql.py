"""SQL builders for PostgreSQL source-family master/detail inserts."""

from __future__ import annotations

from carbonfactor_parser.persistence.postgresql_schema_catalog import (
    SourceFamily,
    source_family_table_prefix,
)
from carbonfactor_parser.persistence.source_family_repository import (
    source_family_repository_table_names,
)


def master_insert_sql(source_family: SourceFamily) -> str:
    """Return the source-family master INSERT statement."""

    master_table, _detail_table = source_family_repository_table_names(source_family)
    family_prefix = source_family_table_prefix(source_family)
    master_id = f"{family_prefix}_emission_factor_master_id"
    return f"""
        INSERT INTO {master_table} (
            {master_id},
            source_family,
            source_year,
            source_version,
            source_release,
            source_document_id,
            ingestion_run_id,
            run_id,
            master_external_key,
            status,
            artifact_reference,
            artifact_checksum_sha256,
            archive_reference,
            archive_checksum_sha256,
            effective_from,
            effective_to,
            record_checksum_sha256,
            metadata,
            created_at,
            updated_at
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s::jsonb, NOW(), NOW()
        )
        ON CONFLICT (source_family, source_year, source_version, master_external_key)
        DO NOTHING
        RETURNING {master_id}
        """


def detail_insert_sql(source_family: SourceFamily) -> str:
    """Return the source-family detail INSERT statement."""

    master_table, detail_table = source_family_repository_table_names(source_family)
    del master_table
    family_prefix = source_family_table_prefix(source_family)
    master_id = f"{family_prefix}_emission_factor_master_id"
    detail_id = f"{family_prefix}_emission_factor_detail_id"
    return f"""
        INSERT INTO {detail_table} (
            {detail_id},
            {master_id},
            detail_external_key,
            source_row_number,
            factor_id,
            factor_name,
            factor_value,
            factor_unit,
            status,
            record_checksum_sha256,
            raw_fields,
            normalized_fields,
            created_at,
            updated_at
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s::jsonb, %s::jsonb, NOW(), NOW()
        )
        ON CONFLICT ({master_id}, detail_external_key)
        DO NOTHING
        RETURNING {detail_id}
        """


__all__ = ("detail_insert_sql", "master_insert_sql")
