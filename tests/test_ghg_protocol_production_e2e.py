from __future__ import annotations

import os
from pathlib import Path
import uuid

import pytest

from carbonfactor_parser.persistence import (
    POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR,
    POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR,
)
from carbonfactor_parser.persistence.postgresql_normalized_factor_repository import (
    PostgreSQLNormalizedFactorRuntimeRepository,
)
from carbonfactor_parser.persistence.postgresql_runtime_schema_bootstrap import (
    bootstrap_postgresql_phase1_schema,
)
from carbonfactor_parser.persistence.postgresql_year_state_repository import (
    PostgreSQLSourceFamilyYearStateRepository,
)
from carbonfactor_parser.pipeline.ghg_protocol_production_e2e import (
    GHG_PROTOCOL_SOURCE_FAMILY,
    GHGProtocolPhase2ValidationBoundary,
    GHGProtocolProductionParserBoundary,
    GHGProtocolProductionSourceAdapter,
    GHGProtocolSourceYear,
)
from carbonfactor_parser.pipeline.production_e2e_year_orchestrator import (
    ProductionE2EYearFamilyStatus,
    ProductionE2EYearOrchestratorDependencies,
    ProductionE2EYearOrchestratorRequest,
    ProductionE2EYearRunStatus,
    run_production_e2e_year_orchestrator,
)


def test_ghg_protocol_2024_first_run_downloads_parses_validates_and_inserts(
    tmp_path: Path,
) -> None:
    adapter = _adapter(tmp_path, {2024: _normalized_csv(year=2024)})
    insert_repository = _RecordingInsertRepository()
    year_state = _YearStateRepository()

    result = run_production_e2e_year_orchestrator(
        ProductionE2EYearOrchestratorRequest(
            run_id="ph-015-ghg-2024",
            enabled_source_families=(GHG_PROTOCOL_SOURCE_FAMILY,),
        ),
        _dependencies(year_state, adapter, insert_repository),
    )

    family = result.family_results[0]
    assert result.status is ProductionE2EYearRunStatus.COMPLETED
    assert family.status is ProductionE2EYearFamilyStatus.COMPLETED
    assert family.year_state.target_year == 2024
    assert family.download_result is not None
    assert family.download_result.artifact is not None
    assert Path(family.download_result.artifact.artifact_reference).exists()
    assert Path(
        f"{family.download_result.artifact.artifact_reference}.metadata.json",
    ).exists()
    assert family.parsed_row_count == 1
    assert family.validation_result is not None
    assert family.validation_result.blocking_error_count == 0
    assert dict(insert_repository.inserted_batches[0].rows[0].normalized_fields)[
        "source_year"
    ] == 2024
    assert year_state.recorded_years == (("ghg", 2024),)


def test_ghg_protocol_next_run_after_2024_targets_2025(tmp_path: Path) -> None:
    adapter = _adapter(tmp_path, {2025: _normalized_csv(year=2025)})
    year_state = _YearStateRepository({"ghg": 2024})

    result = run_production_e2e_year_orchestrator(
        ProductionE2EYearOrchestratorRequest(
            run_id="ph-015-ghg-2025",
            enabled_source_families=(GHG_PROTOCOL_SOURCE_FAMILY,),
        ),
        _dependencies(year_state, adapter, _RecordingInsertRepository()),
    )

    family = result.family_results[0]
    assert family.status is ProductionE2EYearFamilyStatus.COMPLETED
    assert family.year_state.latest_year == 2024
    assert family.year_state.target_year == 2025
    assert year_state.recorded_years == (("ghg", 2025),)


def test_ghg_protocol_future_year_unavailable_returns_safe_noop(
    tmp_path: Path,
) -> None:
    adapter = _adapter(tmp_path, {})
    insert_repository = _RecordingInsertRepository()
    year_state = _YearStateRepository({"ghg": 2025})

    result = run_production_e2e_year_orchestrator(
        ProductionE2EYearOrchestratorRequest(
            run_id="ph-015-ghg-2026",
            enabled_source_families=(GHG_PROTOCOL_SOURCE_FAMILY,),
        ),
        _dependencies(year_state, adapter, insert_repository),
    )

    family = result.family_results[0]
    assert result.status is ProductionE2EYearRunStatus.COMPLETED
    assert family.status is ProductionE2EYearFamilyStatus.NO_AVAILABLE_SOURCE_YEAR
    assert family.year_state.target_year == 2026
    assert insert_repository.inserted_batches == ()
    assert year_state.recorded_years == ()


def test_ghg_protocol_repeated_run_is_insert_idempotent(tmp_path: Path) -> None:
    adapter = _adapter(tmp_path, {2024: _normalized_csv(year=2024)})
    insert_repository = _IdempotentInsertRepository()

    first = run_production_e2e_year_orchestrator(
        ProductionE2EYearOrchestratorRequest(
            run_id="ph-015-ghg-idempotent-a",
            enabled_source_families=(GHG_PROTOCOL_SOURCE_FAMILY,),
        ),
        _dependencies(_YearStateRepository(), adapter, insert_repository),
    )
    second = run_production_e2e_year_orchestrator(
        ProductionE2EYearOrchestratorRequest(
            run_id="ph-015-ghg-idempotent-b",
            enabled_source_families=(GHG_PROTOCOL_SOURCE_FAMILY,),
        ),
        _dependencies(_YearStateRepository(), adapter, insert_repository),
    )

    assert first.family_results[0].insert_summary is not None
    assert second.family_results[0].insert_summary is not None
    assert first.family_results[0].insert_summary.inserted == 1
    assert second.family_results[0].insert_summary.inserted == 0
    assert second.family_results[0].insert_summary.skipped_duplicate == 1


@pytest.mark.postgresql_integration
def test_docker_postgresql_ghg_protocol_production_e2e_integration(
    tmp_path: Path,
) -> None:
    if os.getenv(POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR) != "1":
        pytest.skip("PostgreSQL integration test opt-in is not enabled.")
    dsn = os.getenv(POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR)
    if not dsn:
        pytest.skip("PostgreSQL integration test DSN was not provided.")

    import psycopg

    schema_name = f"carbonops_ph015_{uuid.uuid4().hex}"
    with psycopg.connect(dsn) as connection:
        connection.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        connection.execute(f"SET search_path TO {schema_name}")
        bootstrap_postgresql_phase1_schema(connection)

        adapter = _adapter(tmp_path, {2024: _normalized_csv(year=2024)})
        dependencies = ProductionE2EYearOrchestratorDependencies(
            year_state_repository=PostgreSQLSourceFamilyYearStateRepository(
                connection,
            ),
            source_adapters={GHG_PROTOCOL_SOURCE_FAMILY: adapter},
            parser_boundaries={
                GHG_PROTOCOL_SOURCE_FAMILY: GHGProtocolProductionParserBoundary(),
            },
            validation_boundary=GHGProtocolPhase2ValidationBoundary(),
            insert_repository=PostgreSQLNormalizedFactorRuntimeRepository(connection),
        )

        first = run_production_e2e_year_orchestrator(
            ProductionE2EYearOrchestratorRequest(
                run_id="ph-015-ghg-postgresql-a",
                enabled_source_families=(GHG_PROTOCOL_SOURCE_FAMILY,),
            ),
            dependencies,
        )
        connection.execute("DELETE FROM source_family_year_states")
        second = run_production_e2e_year_orchestrator(
            ProductionE2EYearOrchestratorRequest(
                run_id="ph-015-ghg-postgresql-b",
                enabled_source_families=(GHG_PROTOCOL_SOURCE_FAMILY,),
            ),
            dependencies,
        )
        count = connection.execute(
            "SELECT COUNT(*) FROM normalized_factor_records",
        ).fetchone()[0]

        assert first.family_results[0].insert_summary is not None
        assert second.family_results[0].insert_summary is not None
        assert first.family_results[0].insert_summary.inserted == 1
        assert second.family_results[0].insert_summary.inserted == 0
        assert second.family_results[0].insert_summary.skipped_duplicate == 1
        assert count == 1


class _YearStateRepository:
    def __init__(self, latest_years: dict[str, int] | None = None) -> None:
        self.latest_years = dict(latest_years or {})
        self._recorded_years: list[tuple[str, int]] = []

    @property
    def recorded_years(self) -> tuple[tuple[str, int], ...]:
        return tuple(self._recorded_years)

    def latest_ingested_year(self, source_family: str) -> int | None:
        return self.latest_years.get(source_family)

    def record_ingested_year(self, source_family: str, ingested_year: int) -> None:
        self.latest_years[source_family] = ingested_year
        self._recorded_years.append((source_family, ingested_year))


class _RecordingInsertRepository:
    def __init__(self) -> None:
        self._inserted_batches = []

    @property
    def inserted_batches(self):
        return tuple(self._inserted_batches)

    def insert_normalized_factor_records(self, batch):
        self._inserted_batches.append(batch)
        return _InsertResult("inserted", batch.row_count, batch.row_count)


class _IdempotentInsertRepository:
    def __init__(self) -> None:
        self._seen = set()

    def insert_normalized_factor_records(self, batch):
        inserted = 0
        skipped = 0
        for row in batch.rows:
            if row.row_id in self._seen:
                skipped += 1
            else:
                inserted += 1
                self._seen.add(row.row_id)
        return _InsertResult("inserted", batch.row_count, inserted, skipped)


class _InsertResult:
    def __init__(
        self,
        status: str,
        attempted: int,
        inserted: int,
        skipped_duplicate: int = 0,
    ) -> None:
        self.status = status
        self.attempted = attempted
        self.inserted = inserted
        self.skipped_duplicate = skipped_duplicate
        self.failed = 0
        self.validation_error_count = 0


def _dependencies(
    year_state: _YearStateRepository,
    adapter: GHGProtocolProductionSourceAdapter,
    insert_repository,
) -> ProductionE2EYearOrchestratorDependencies:
    return ProductionE2EYearOrchestratorDependencies(
        year_state_repository=year_state,
        source_adapters={GHG_PROTOCOL_SOURCE_FAMILY: adapter},
        parser_boundaries={
            GHG_PROTOCOL_SOURCE_FAMILY: GHGProtocolProductionParserBoundary(),
        },
        validation_boundary=GHGProtocolPhase2ValidationBoundary(),
        insert_repository=insert_repository,
    )


def _adapter(
    tmp_path: Path,
    source_bytes_by_year: dict[int, bytes],
) -> GHGProtocolProductionSourceAdapter:
    years = {
        year: GHGProtocolSourceYear(
            year=year,
            publication_url=f"https://example.invalid/ghg/{year}",
            artifact_url=f"https://example.invalid/ghg/{year}.csv",
            title=f"GHG Protocol normalized factors {year}",
            version_label=f"{year}-test",
        )
        for year in source_bytes_by_year
    }

    def transport(uri: str) -> bytes:
        for year, content in source_bytes_by_year.items():
            if uri.endswith(f"/{year}.csv"):
                return content
        raise FileNotFoundError(uri)

    return GHGProtocolProductionSourceAdapter(
        target_root=tmp_path / "archive",
        source_years=years,
        transport=transport,
    )


def _normalized_csv(*, year: int) -> bytes:
    return (
        "record_type,source_year,source_version,factor_id,factor_name,"
        "factor_value,unit,category,subcategory,scope,gas,provenance_note\n"
        f"emission_factor,{year},v1,GHG-ELEC-001,Grid electricity,"
        "0.233,kg CO2e/kWh,Stationary combustion,Electricity,Scope 2,CO2e,"
        "fixture row 1\n"
    ).encode("utf-8")
