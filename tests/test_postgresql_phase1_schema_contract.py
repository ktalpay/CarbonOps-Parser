from __future__ import annotations

import re

from carbonfactor_parser.persistence.postgresql_ddl_renderer import render_postgresql_phase1_schema_ddl
from carbonfactor_parser.persistence.postgresql_schema_catalog import get_required_table_names


def _sql() -> str:
    return "\n".join(render_postgresql_phase1_schema_ddl().statements)


def test_run_history_tables_are_required_phase1_tables() -> None:
    required_table_names = set(get_required_table_names())

    assert "parser_ingestion_runs" in required_table_names
    assert "parser_ingestion_source_results" in required_table_names
    assert "parser_ingestion_issues" in required_table_names


def test_run_history_schema_uses_additive_idempotent_sql() -> None:
    statements = _sql()

    for table_name in (
        "parser_ingestion_runs",
        "parser_ingestion_source_results",
        "parser_ingestion_issues",
    ):
        assert f"CREATE TABLE IF NOT EXISTS {table_name}" in statements
    assert "CREATE INDEX IF NOT EXISTS idx_parser_ingestion_issues_run_id" in statements
    assert "CREATE INDEX IF NOT EXISTS idx_parser_ingestion_issues_family_year" in statements
    assert "CREATE INDEX IF NOT EXISTS idx_parser_ingestion_issues_code" in statements


def test_run_history_schema_contains_expected_columns_defaults_and_foreign_keys() -> None:
    statements = _sql()

    assert "run_id text NOT NULL" in statements
    assert "started_at timestamp with time zone NOT NULL" in statements
    assert "trigger_type text DEFAULT 'operator' NOT NULL" in statements
    assert "enabled_source_families jsonb DEFAULT '[]'::jsonb NOT NULL" in statements
    assert "metadata jsonb DEFAULT '{}'::jsonb NOT NULL" in statements
    assert "created_at timestamp with time zone DEFAULT now() NOT NULL" in statements
    assert "REFERENCES parser_ingestion_runs (run_id)" in statements


def test_run_history_source_result_unique_contract_is_rendered() -> None:
    statements = " ".join(_sql().split())

    assert (
        "CONSTRAINT uq_parser_ingestion_source_results_run_family_year "
        "UNIQUE (run_id, source_family, target_year)"
    ) in statements


def test_run_history_schema_has_no_destructive_statements() -> None:
    statements = _sql().lower()

    assert not re.search(r"\bdrop\b", statements)
    assert not re.search(r"\btruncate\b", statements)
    assert not re.search(r"\bdelete\s+from\b", statements)
