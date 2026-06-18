"""Runtime-passive PostgreSQL Phase 1 schema catalog contract definitions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping


class SourceFamily(str, Enum):
    """Supported source families for Phase 1 contracts."""

    GHG = "ghg"
    DEFRA = "defra"
    IPCC = "ipcc"


_SOURCE_FAMILY_ALIASES: Mapping[str, SourceFamily] = {
    SourceFamily.GHG.value: SourceFamily.GHG,
    "ghg_protocol": SourceFamily.GHG,
    SourceFamily.DEFRA.value: SourceFamily.DEFRA,
    "defra_desnz": SourceFamily.DEFRA,
    "desnz": SourceFamily.DEFRA,
    SourceFamily.IPCC.value: SourceFamily.IPCC,
    "ipcc_efdb": SourceFamily.IPCC,
}

_SOURCE_FAMILY_POSTGRESQL_VALUES: Mapping[SourceFamily, str] = {
    SourceFamily.GHG: "ghg_protocol",
    SourceFamily.DEFRA: "defra_desnz",
    SourceFamily.IPCC: "ipcc_efdb",
}

_SOURCE_FAMILY_TABLE_PREFIXES: Mapping[SourceFamily, str] = {
    SourceFamily.GHG: "ghg",
    SourceFamily.DEFRA: "defra",
    SourceFamily.IPCC: "ipcc",
}


class PostgreSQLDataType(str, Enum):
    """Conceptual PostgreSQL-oriented data types used by catalog definitions."""

    UUID = "uuid"
    TEXT = "text"
    INTEGER = "integer"
    NUMERIC = "numeric"
    BOOLEAN = "boolean"
    TIMESTAMP_WITH_TIME_ZONE = "timestamp_with_time_zone"
    JSONB = "jsonb"


@dataclass(frozen=True)
class ColumnDefinition:
    name: str
    data_type: PostgreSQLDataType
    nullable: bool
    is_primary_key: bool = False
    default_sql: str | None = None


@dataclass(frozen=True)
class ForeignKeyDefinition:
    column_name: str
    referenced_table_name: str
    referenced_column_name: str


@dataclass(frozen=True)
class UniqueConstraintDefinition:
    name: str
    column_names: tuple[str, ...]


@dataclass(frozen=True)
class IndexDefinition:
    name: str
    column_names: tuple[str, ...]
    unique: bool = False


@dataclass(frozen=True)
class TableDefinition:
    name: str
    columns: tuple[ColumnDefinition, ...]
    foreign_keys: tuple[ForeignKeyDefinition, ...] = ()
    unique_constraints: tuple[UniqueConstraintDefinition, ...] = ()
    indexes: tuple[IndexDefinition, ...] = ()


@dataclass(frozen=True)
class SchemaCatalog:
    tables: tuple[TableDefinition, ...]
    source_family_tables: Mapping[SourceFamily, tuple[str, ...]]

    def get_table(self, table_name: str) -> TableDefinition:
        for table in self.tables:
            if table.name == table_name:
                return table
        raise KeyError(f"Unknown table: {table_name}")


def _build_shared_tables() -> tuple[TableDefinition, ...]:
    return (
        TableDefinition(
            name="ingestion_runs",
            columns=(
                ColumnDefinition("ingestion_run_id", PostgreSQLDataType.UUID, nullable=False, is_primary_key=True),
                ColumnDefinition("run_status", PostgreSQLDataType.TEXT, nullable=False),
                ColumnDefinition("created_at", PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE, nullable=False),
                ColumnDefinition("updated_at", PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE, nullable=False),
            ),
            indexes=(
                IndexDefinition(name="idx_ingestion_runs_run_status", column_names=("run_status",)),
            ),
        ),
        TableDefinition(
            name="source_documents",
            columns=(
                ColumnDefinition("source_document_id", PostgreSQLDataType.UUID, nullable=False, is_primary_key=True),
                ColumnDefinition("ingestion_run_id", PostgreSQLDataType.UUID, nullable=False),
                ColumnDefinition("source_family", PostgreSQLDataType.TEXT, nullable=False),
                ColumnDefinition("source_document_uri", PostgreSQLDataType.TEXT, nullable=False),
                ColumnDefinition("source_checksum_sha256", PostgreSQLDataType.TEXT, nullable=False),
                ColumnDefinition("acquisition_status", PostgreSQLDataType.TEXT, nullable=False),
                ColumnDefinition("acquired_at", PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE, nullable=True),
                ColumnDefinition("created_at", PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE, nullable=False),
                ColumnDefinition("updated_at", PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE, nullable=False),
            ),
            foreign_keys=(
                ForeignKeyDefinition("ingestion_run_id", "ingestion_runs", "ingestion_run_id"),
            ),
            unique_constraints=(
                UniqueConstraintDefinition(
                    name="uq_source_documents_family_uri_checksum",
                    column_names=("source_family", "source_document_uri", "source_checksum_sha256"),
                ),
            ),
            indexes=(
                IndexDefinition(name="idx_source_documents_ingestion_run_id", column_names=("ingestion_run_id",)),
            ),
        ),
        TableDefinition(
            name="parser_runs",
            columns=(
                ColumnDefinition("parser_run_id", PostgreSQLDataType.UUID, nullable=False, is_primary_key=True),
                ColumnDefinition("source_document_id", PostgreSQLDataType.UUID, nullable=False),
                ColumnDefinition("parser_status", PostgreSQLDataType.TEXT, nullable=False),
                ColumnDefinition("error_details", PostgreSQLDataType.JSONB, nullable=True),
                ColumnDefinition("created_at", PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE, nullable=False),
                ColumnDefinition("updated_at", PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE, nullable=False),
            ),
            foreign_keys=(
                ForeignKeyDefinition("source_document_id", "source_documents", "source_document_id"),
            ),
            indexes=(
                IndexDefinition(name="idx_parser_runs_source_document_id", column_names=("source_document_id",)),
            ),
        ),
        TableDefinition(
            name="schema_bootstrap_states",
            columns=(
                ColumnDefinition("schema_bootstrap_state_id", PostgreSQLDataType.UUID, nullable=False, is_primary_key=True),
                ColumnDefinition("schema_contract_version", PostgreSQLDataType.TEXT, nullable=False),
                ColumnDefinition("bootstrap_status", PostgreSQLDataType.TEXT, nullable=False),
                ColumnDefinition("created_at", PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE, nullable=False),
                ColumnDefinition("updated_at", PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE, nullable=False),
            ),
            unique_constraints=(
                UniqueConstraintDefinition(
                    name="uq_schema_bootstrap_states_contract_version",
                    column_names=("schema_contract_version",),
                ),
            ),
        ),
        TableDefinition(
            name="parser_ingestion_runs",
            columns=(
                ColumnDefinition("run_id", PostgreSQLDataType.TEXT, nullable=False, is_primary_key=True),
                ColumnDefinition("started_at", PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE, nullable=False),
                ColumnDefinition("finished_at", PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE, nullable=True),
                ColumnDefinition("status", PostgreSQLDataType.TEXT, nullable=False),
                ColumnDefinition("trigger_type", PostgreSQLDataType.TEXT, nullable=False, default_sql="'operator'"),
                ColumnDefinition("config_hash", PostgreSQLDataType.TEXT, nullable=True),
                ColumnDefinition("enabled_source_families", PostgreSQLDataType.JSONB, nullable=False, default_sql="'[]'::jsonb"),
                ColumnDefinition("initial_year", PostgreSQLDataType.INTEGER, nullable=True),
                ColumnDefinition("cycle_count", PostgreSQLDataType.INTEGER, nullable=True),
                ColumnDefinition("total_parsed_rows", PostgreSQLDataType.INTEGER, nullable=False, default_sql="0"),
                ColumnDefinition("total_inserted_count", PostgreSQLDataType.INTEGER, nullable=False, default_sql="0"),
                ColumnDefinition("total_skipped_duplicate_count", PostgreSQLDataType.INTEGER, nullable=False, default_sql="0"),
                ColumnDefinition("failure_count", PostgreSQLDataType.INTEGER, nullable=False, default_sql="0"),
                ColumnDefinition("metadata", PostgreSQLDataType.JSONB, nullable=False, default_sql="'{}'::jsonb"),
                ColumnDefinition("created_at", PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE, nullable=False, default_sql="now()"),
                ColumnDefinition("updated_at", PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE, nullable=False, default_sql="now()"),
            ),
        ),
        TableDefinition(
            name="parser_ingestion_source_results",
            columns=(
                ColumnDefinition("parser_ingestion_source_result_id", PostgreSQLDataType.UUID, nullable=False, is_primary_key=True),
                ColumnDefinition("run_id", PostgreSQLDataType.TEXT, nullable=False),
                ColumnDefinition("source_family", PostgreSQLDataType.TEXT, nullable=False),
                ColumnDefinition("target_year", PostgreSQLDataType.INTEGER, nullable=True),
                ColumnDefinition("latest_year", PostgreSQLDataType.INTEGER, nullable=True),
                ColumnDefinition("status", PostgreSQLDataType.TEXT, nullable=False),
                ColumnDefinition("download_status", PostgreSQLDataType.TEXT, nullable=True),
                ColumnDefinition("parse_status", PostgreSQLDataType.TEXT, nullable=True),
                ColumnDefinition("validation_status", PostgreSQLDataType.TEXT, nullable=True),
                ColumnDefinition("insert_status", PostgreSQLDataType.TEXT, nullable=True),
                ColumnDefinition("parsed_rows", PostgreSQLDataType.INTEGER, nullable=False, default_sql="0"),
                ColumnDefinition("master_inserted", PostgreSQLDataType.INTEGER, nullable=False, default_sql="0"),
                ColumnDefinition("master_skipped", PostgreSQLDataType.INTEGER, nullable=False, default_sql="0"),
                ColumnDefinition("detail_inserted", PostgreSQLDataType.INTEGER, nullable=False, default_sql="0"),
                ColumnDefinition("detail_skipped", PostgreSQLDataType.INTEGER, nullable=False, default_sql="0"),
                ColumnDefinition("issue_count", PostgreSQLDataType.INTEGER, nullable=False, default_sql="0"),
                ColumnDefinition("metadata", PostgreSQLDataType.JSONB, nullable=False, default_sql="'{}'::jsonb"),
                ColumnDefinition("created_at", PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE, nullable=False, default_sql="now()"),
                ColumnDefinition("updated_at", PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE, nullable=False, default_sql="now()"),
            ),
            foreign_keys=(
                ForeignKeyDefinition("run_id", "parser_ingestion_runs", "run_id"),
            ),
            unique_constraints=(
                UniqueConstraintDefinition(
                    name="uq_parser_ingestion_source_results_run_family_year",
                    column_names=("run_id", "source_family", "target_year"),
                ),
            ),
        ),
        TableDefinition(
            name="parser_ingestion_issues",
            columns=(
                ColumnDefinition("parser_ingestion_issue_id", PostgreSQLDataType.UUID, nullable=False, is_primary_key=True),
                ColumnDefinition("run_id", PostgreSQLDataType.TEXT, nullable=False),
                ColumnDefinition("source_family", PostgreSQLDataType.TEXT, nullable=True),
                ColumnDefinition("target_year", PostgreSQLDataType.INTEGER, nullable=True),
                ColumnDefinition("stage", PostgreSQLDataType.TEXT, nullable=False),
                ColumnDefinition("code", PostgreSQLDataType.TEXT, nullable=False),
                ColumnDefinition("severity", PostgreSQLDataType.TEXT, nullable=False, default_sql="'error'"),
                ColumnDefinition("field_name", PostgreSQLDataType.TEXT, nullable=True),
                ColumnDefinition("message", PostgreSQLDataType.TEXT, nullable=False),
                ColumnDefinition("metadata", PostgreSQLDataType.JSONB, nullable=False, default_sql="'{}'::jsonb"),
                ColumnDefinition("created_at", PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE, nullable=False, default_sql="now()"),
            ),
            foreign_keys=(
                ForeignKeyDefinition("run_id", "parser_ingestion_runs", "run_id"),
            ),
            indexes=(
                IndexDefinition(name="idx_parser_ingestion_issues_run_id", column_names=("run_id",)),
                IndexDefinition(name="idx_parser_ingestion_issues_family_year", column_names=("source_family", "target_year")),
                IndexDefinition(name="idx_parser_ingestion_issues_code", column_names=("code",)),
            ),
        ),
        TableDefinition(
            name="source_family_year_states",
            columns=(
                ColumnDefinition(
                    "source_family_year_state_id",
                    PostgreSQLDataType.UUID,
                    nullable=False,
                    is_primary_key=True,
                ),
                ColumnDefinition("source_family", PostgreSQLDataType.TEXT, nullable=False),
                ColumnDefinition("ingested_year", PostgreSQLDataType.INTEGER, nullable=False),
                ColumnDefinition("created_at", PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE, nullable=False),
                ColumnDefinition("updated_at", PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE, nullable=False),
            ),
            unique_constraints=(
                UniqueConstraintDefinition(
                    name="uq_source_family_year_states_family_year",
                    column_names=("source_family", "ingested_year"),
                ),
            ),
            indexes=(
                IndexDefinition(
                    name="idx_source_family_year_states_family_year",
                    column_names=("source_family", "ingested_year"),
                ),
            ),
        ),
        TableDefinition(
            name="normalized_factor_records",
            columns=(
                ColumnDefinition(
                    "normalized_factor_record_id",
                    PostgreSQLDataType.TEXT,
                    nullable=False,
                    is_primary_key=True,
                ),
                ColumnDefinition(
                    "idempotency_key_sha256",
                    PostgreSQLDataType.TEXT,
                    nullable=False,
                ),
                ColumnDefinition(
                    "source_family",
                    PostgreSQLDataType.TEXT,
                    nullable=False,
                ),
                ColumnDefinition("source_id", PostgreSQLDataType.TEXT, nullable=False),
                ColumnDefinition(
                    "source_year",
                    PostgreSQLDataType.INTEGER,
                    nullable=True,
                ),
                ColumnDefinition(
                    "source_version",
                    PostgreSQLDataType.TEXT,
                    nullable=True,
                ),
                ColumnDefinition("record_id", PostgreSQLDataType.TEXT, nullable=False),
                ColumnDefinition(
                    "source_row_number",
                    PostgreSQLDataType.INTEGER,
                    nullable=True,
                ),
                ColumnDefinition(
                    "source_document_reference",
                    PostgreSQLDataType.TEXT,
                    nullable=True,
                ),
                ColumnDefinition(
                    "source_artifact_reference",
                    PostgreSQLDataType.TEXT,
                    nullable=True,
                ),
                ColumnDefinition(
                    "source_checksum_sha256",
                    PostgreSQLDataType.TEXT,
                    nullable=True,
                ),
                ColumnDefinition("factor_id", PostgreSQLDataType.TEXT, nullable=True),
                ColumnDefinition("factor_name", PostgreSQLDataType.TEXT, nullable=True),
                ColumnDefinition(
                    "factor_value",
                    PostgreSQLDataType.NUMERIC,
                    nullable=False,
                ),
                ColumnDefinition("factor_unit", PostgreSQLDataType.TEXT, nullable=False),
                ColumnDefinition(
                    "validation_status",
                    PostgreSQLDataType.TEXT,
                    nullable=False,
                ),
                ColumnDefinition("run_id", PostgreSQLDataType.TEXT, nullable=True),
                ColumnDefinition("parser_key", PostgreSQLDataType.TEXT, nullable=False),
                ColumnDefinition("metadata", PostgreSQLDataType.JSONB, nullable=False),
                ColumnDefinition(
                    "normalized_fields",
                    PostgreSQLDataType.JSONB,
                    nullable=False,
                ),
                ColumnDefinition("warnings", PostgreSQLDataType.JSONB, nullable=False),
                ColumnDefinition("errors", PostgreSQLDataType.JSONB, nullable=False),
                ColumnDefinition(
                    "created_at",
                    PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE,
                    nullable=False,
                ),
                ColumnDefinition(
                    "updated_at",
                    PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE,
                    nullable=False,
                ),
            ),
            unique_constraints=(
                UniqueConstraintDefinition(
                    name="uq_normalized_factor_records_idempotency_key",
                    column_names=("idempotency_key_sha256",),
                ),
            ),
            indexes=(
                IndexDefinition(
                    name="idx_normalized_factor_records_source_year",
                    column_names=("source_family", "source_id", "source_year"),
                ),
            ),
        ),
    )


def _build_source_family_tables(source_family: SourceFamily) -> tuple[TableDefinition, TableDefinition]:
    family = source_family_table_prefix(source_family)
    master_table_name = f"{family}_emission_factor_masters"
    detail_table_name = f"{family}_emission_factor_details"
    master_id = f"{family}_emission_factor_master_id"
    detail_id = f"{family}_emission_factor_detail_id"

    master_table = TableDefinition(
        name=master_table_name,
        columns=(
            ColumnDefinition(master_id, PostgreSQLDataType.UUID, nullable=False, is_primary_key=True),
            ColumnDefinition("source_family", PostgreSQLDataType.TEXT, nullable=False),
            ColumnDefinition("source_year", PostgreSQLDataType.INTEGER, nullable=False),
            ColumnDefinition("source_version", PostgreSQLDataType.TEXT, nullable=False),
            ColumnDefinition("source_release", PostgreSQLDataType.TEXT, nullable=True),
            ColumnDefinition("source_document_id", PostgreSQLDataType.UUID, nullable=False),
            ColumnDefinition("ingestion_run_id", PostgreSQLDataType.UUID, nullable=True),
            ColumnDefinition("run_id", PostgreSQLDataType.TEXT, nullable=True),
            ColumnDefinition("master_external_key", PostgreSQLDataType.TEXT, nullable=False),
            ColumnDefinition("status", PostgreSQLDataType.TEXT, nullable=False),
            ColumnDefinition("artifact_reference", PostgreSQLDataType.TEXT, nullable=True),
            ColumnDefinition("artifact_checksum_sha256", PostgreSQLDataType.TEXT, nullable=True),
            ColumnDefinition("archive_reference", PostgreSQLDataType.TEXT, nullable=True),
            ColumnDefinition("archive_checksum_sha256", PostgreSQLDataType.TEXT, nullable=True),
            ColumnDefinition("effective_from", PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE, nullable=True),
            ColumnDefinition("effective_to", PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE, nullable=True),
            ColumnDefinition("record_checksum_sha256", PostgreSQLDataType.TEXT, nullable=False),
            ColumnDefinition("metadata", PostgreSQLDataType.JSONB, nullable=False),
            ColumnDefinition("created_at", PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE, nullable=False),
            ColumnDefinition("updated_at", PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE, nullable=False),
        ),
        foreign_keys=(
            ForeignKeyDefinition("source_document_id", "source_documents", "source_document_id"),
            ForeignKeyDefinition("ingestion_run_id", "ingestion_runs", "ingestion_run_id"),
        ),
        unique_constraints=(
            UniqueConstraintDefinition(
                name=f"uq_{master_table_name}_family_year_version_key",
                column_names=(
                    "source_family",
                    "source_year",
                    "source_version",
                    "master_external_key",
                ),
            ),
        ),
        indexes=(
            IndexDefinition(
                name=f"idx_{master_table_name}_source_year",
                column_names=("source_family", "source_year", "source_version"),
            ),
            IndexDefinition(
                name=f"idx_{master_table_name}_ingestion_run_id",
                column_names=("ingestion_run_id",),
            ),
        ),
    )

    detail_table = TableDefinition(
        name=detail_table_name,
        columns=(
            ColumnDefinition(detail_id, PostgreSQLDataType.UUID, nullable=False, is_primary_key=True),
            ColumnDefinition(master_id, PostgreSQLDataType.UUID, nullable=False),
            ColumnDefinition("detail_external_key", PostgreSQLDataType.TEXT, nullable=False),
            ColumnDefinition("source_row_number", PostgreSQLDataType.INTEGER, nullable=True),
            ColumnDefinition("factor_id", PostgreSQLDataType.TEXT, nullable=True),
            ColumnDefinition("factor_name", PostgreSQLDataType.TEXT, nullable=True),
            ColumnDefinition("factor_value", PostgreSQLDataType.NUMERIC, nullable=False),
            ColumnDefinition("factor_unit", PostgreSQLDataType.TEXT, nullable=False),
            ColumnDefinition("status", PostgreSQLDataType.TEXT, nullable=False),
            ColumnDefinition("record_checksum_sha256", PostgreSQLDataType.TEXT, nullable=False),
            ColumnDefinition("raw_fields", PostgreSQLDataType.JSONB, nullable=False),
            ColumnDefinition("normalized_fields", PostgreSQLDataType.JSONB, nullable=False),
            ColumnDefinition("created_at", PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE, nullable=False),
            ColumnDefinition("updated_at", PostgreSQLDataType.TIMESTAMP_WITH_TIME_ZONE, nullable=False),
        ),
        foreign_keys=(
            ForeignKeyDefinition(master_id, master_table_name, master_id),
        ),
        unique_constraints=(
            UniqueConstraintDefinition(
                name=f"uq_{detail_table_name}_master_detail_external_key",
                column_names=(master_id, "detail_external_key"),
            ),
        ),
        indexes=(
            IndexDefinition(name=f"idx_{detail_table_name}_{master_id}", column_names=(master_id,)),
        ),
    )

    return master_table, detail_table


def get_postgresql_phase1_schema_catalog() -> SchemaCatalog:
    """Return immutable Phase 1 PostgreSQL schema catalog definitions."""

    shared_tables = _build_shared_tables()
    ghg_master, ghg_detail = _build_source_family_tables(SourceFamily.GHG)
    defra_master, defra_detail = _build_source_family_tables(SourceFamily.DEFRA)
    ipcc_master, ipcc_detail = _build_source_family_tables(SourceFamily.IPCC)

    family_mapping: dict[SourceFamily, tuple[str, ...]] = {
        SourceFamily.GHG: (ghg_master.name, ghg_detail.name),
        SourceFamily.DEFRA: (defra_master.name, defra_detail.name),
        SourceFamily.IPCC: (ipcc_master.name, ipcc_detail.name),
    }

    return SchemaCatalog(
        tables=shared_tables + (ghg_master, ghg_detail, defra_master, defra_detail, ipcc_master, ipcc_detail),
        source_family_tables=family_mapping,
    )


def get_required_table_names() -> tuple[str, ...]:
    """Return sorted deterministic required table names for Phase 1 contracts."""

    return tuple(sorted(table.name for table in get_postgresql_phase1_schema_catalog().tables))


def get_source_family_table_names(source_family: SourceFamily | str) -> tuple[str, ...]:
    """Return deterministic master/detail table names for a source family."""

    family = coerce_source_family(source_family)
    return get_postgresql_phase1_schema_catalog().source_family_tables[family]


def coerce_source_family(source_family: SourceFamily | str) -> SourceFamily:
    """Return the internal table-prefix enum for any supported family alias."""

    if isinstance(source_family, SourceFamily):
        return source_family
    try:
        return _SOURCE_FAMILY_ALIASES[source_family.strip().lower()]
    except KeyError as exc:
        raise ValueError(f"Unsupported source family: {source_family}") from exc


def source_family_postgresql_value(source_family: SourceFamily | str) -> str:
    """Return the persisted PostgreSQL source-family identifier."""

    return _SOURCE_FAMILY_POSTGRESQL_VALUES[coerce_source_family(source_family)]


def source_family_table_prefix(source_family: SourceFamily | str) -> str:
    """Return the source-family table/id prefix."""

    return _SOURCE_FAMILY_TABLE_PREFIXES[coerce_source_family(source_family)]
