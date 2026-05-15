from __future__ import annotations

import os
from pathlib import Path
import uuid
from zipfile import ZipFile

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
from carbonfactor_parser.pipeline.defra_desnz_production_e2e import (
    DEFRA_DESNZ_SOURCE_FAMILY,
    DefraDesnzPhase2ValidationBoundary,
    DefraDesnzProductionParserBoundary,
    DefraDesnzProductionSourceAdapter,
    DefraDesnzSourceYear,
)
from carbonfactor_parser.pipeline.production_e2e_year_orchestrator import (
    ProductionE2EYearFamilyStatus,
    ProductionE2EYearOrchestratorDependencies,
    ProductionE2EYearOrchestratorRequest,
    ProductionE2EYearRunStatus,
    run_production_e2e_year_orchestrator,
)


def test_defra_desnz_2024_first_run_downloads_parses_validates_and_inserts(
    tmp_path: Path,
) -> None:
    source_bytes = _flat_file_csv(year=2024)
    adapter = _adapter(tmp_path, {2024: source_bytes})
    insert_repository = _RecordingInsertRepository()
    year_state = _YearStateRepository()

    result = run_production_e2e_year_orchestrator(
        ProductionE2EYearOrchestratorRequest(
            run_id="ph-014-defra-2024",
            enabled_source_families=(DEFRA_DESNZ_SOURCE_FAMILY,),
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
    assert insert_repository.inserted_batches[0].rows[0].normalized_fields
    assert year_state.recorded_years == (("defra", 2024),)


def test_defra_desnz_next_run_after_2024_targets_2025(tmp_path: Path) -> None:
    adapter = _adapter(tmp_path, {2025: _flat_file_csv(year=2025)})
    year_state = _YearStateRepository({"defra": 2024})

    result = run_production_e2e_year_orchestrator(
        ProductionE2EYearOrchestratorRequest(
            run_id="ph-014-defra-2025",
            enabled_source_families=(DEFRA_DESNZ_SOURCE_FAMILY,),
        ),
        _dependencies(year_state, adapter, _RecordingInsertRepository()),
    )

    family = result.family_results[0]
    assert family.status is ProductionE2EYearFamilyStatus.COMPLETED
    assert family.year_state.latest_year == 2024
    assert family.year_state.target_year == 2025
    assert year_state.recorded_years == (("defra", 2025),)


def test_defra_desnz_2026_and_2027_unavailable_noop_safely(tmp_path: Path) -> None:
    adapter = _adapter(tmp_path, {})
    insert_repository = _RecordingInsertRepository()
    year_state = _YearStateRepository({"defra": 2025})

    first = run_production_e2e_year_orchestrator(
        ProductionE2EYearOrchestratorRequest(
            run_id="ph-014-defra-2026",
            enabled_source_families=(DEFRA_DESNZ_SOURCE_FAMILY,),
        ),
        _dependencies(year_state, adapter, insert_repository),
    )
    year_state.latest_years["defra"] = 2026
    second = run_production_e2e_year_orchestrator(
        ProductionE2EYearOrchestratorRequest(
            run_id="ph-014-defra-2027",
            enabled_source_families=(DEFRA_DESNZ_SOURCE_FAMILY,),
        ),
        _dependencies(year_state, adapter, insert_repository),
    )

    assert first.family_results[0].status is (
        ProductionE2EYearFamilyStatus.NO_AVAILABLE_SOURCE_YEAR
    )
    assert first.family_results[0].year_state.target_year == 2026
    assert second.family_results[0].status is (
        ProductionE2EYearFamilyStatus.NO_AVAILABLE_SOURCE_YEAR
    )
    assert second.family_results[0].year_state.target_year == 2027
    assert insert_repository.inserted_batches == ()
    assert year_state.recorded_years == ()


def test_defra_desnz_repeated_run_is_insert_idempotent(tmp_path: Path) -> None:
    adapter = _adapter(tmp_path, {2024: _flat_file_csv(year=2024)})
    insert_repository = _IdempotentInsertRepository()

    first = run_production_e2e_year_orchestrator(
        ProductionE2EYearOrchestratorRequest(
            run_id="ph-014-defra-idempotent-a",
            enabled_source_families=(DEFRA_DESNZ_SOURCE_FAMILY,),
        ),
        _dependencies(_YearStateRepository(), adapter, insert_repository),
    )
    second = run_production_e2e_year_orchestrator(
        ProductionE2EYearOrchestratorRequest(
            run_id="ph-014-defra-idempotent-b",
            enabled_source_families=(DEFRA_DESNZ_SOURCE_FAMILY,),
        ),
        _dependencies(_YearStateRepository(), adapter, insert_repository),
    )

    assert first.family_results[0].insert_summary is not None
    assert second.family_results[0].insert_summary is not None
    assert first.family_results[0].insert_summary.inserted == 1
    assert second.family_results[0].insert_summary.inserted == 0
    assert second.family_results[0].insert_summary.skipped_duplicate == 1


def test_defra_desnz_parser_reads_xlsx_flat_file(tmp_path: Path) -> None:
    xlsx_path = tmp_path / "defra-flat.xlsx"
    _write_minimal_xlsx(xlsx_path)
    artifact = _downloaded_artifact(xlsx_path, 2024)

    batch = DefraDesnzProductionParserBoundary().parse(artifact)

    assert batch.row_count == 1
    fields = dict(batch.rows[0].normalized_fields)
    assert fields["source_year"] == 2024
    assert fields["factor_value"] == "0.20705"
    assert fields["unit"] == "kWh"


@pytest.mark.postgresql_integration
def test_docker_postgresql_defra_desnz_production_e2e_integration(
    tmp_path: Path,
) -> None:
    if os.getenv(POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR) != "1":
        pytest.skip("PostgreSQL integration test opt-in is not enabled.")
    dsn = os.getenv(POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR)
    if not dsn:
        pytest.skip("PostgreSQL integration test DSN was not provided.")

    import psycopg

    schema_name = f"carbonops_ph014_{uuid.uuid4().hex}"
    with psycopg.connect(dsn) as connection:
        connection.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        connection.execute(f"SET search_path TO {schema_name}")
        bootstrap_postgresql_phase1_schema(connection)

        adapter = _adapter(tmp_path, {2024: _flat_file_csv(year=2024)})
        dependencies = ProductionE2EYearOrchestratorDependencies(
            year_state_repository=PostgreSQLSourceFamilyYearStateRepository(
                connection,
            ),
            source_adapters={DEFRA_DESNZ_SOURCE_FAMILY: adapter},
            parser_boundaries={
                DEFRA_DESNZ_SOURCE_FAMILY: DefraDesnzProductionParserBoundary(),
            },
            validation_boundary=DefraDesnzPhase2ValidationBoundary(),
            insert_repository=PostgreSQLNormalizedFactorRuntimeRepository(connection),
        )

        first = run_production_e2e_year_orchestrator(
            ProductionE2EYearOrchestratorRequest(
                run_id="ph-014-defra-postgresql-a",
                enabled_source_families=(DEFRA_DESNZ_SOURCE_FAMILY,),
            ),
            dependencies,
        )
        connection.execute("DELETE FROM source_family_year_states")
        second = run_production_e2e_year_orchestrator(
            ProductionE2EYearOrchestratorRequest(
                run_id="ph-014-defra-postgresql-b",
                enabled_source_families=(DEFRA_DESNZ_SOURCE_FAMILY,),
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
    adapter: DefraDesnzProductionSourceAdapter,
    insert_repository,
) -> ProductionE2EYearOrchestratorDependencies:
    return ProductionE2EYearOrchestratorDependencies(
        year_state_repository=year_state,
        source_adapters={DEFRA_DESNZ_SOURCE_FAMILY: adapter},
        parser_boundaries={
            DEFRA_DESNZ_SOURCE_FAMILY: DefraDesnzProductionParserBoundary(),
        },
        validation_boundary=DefraDesnzPhase2ValidationBoundary(),
        insert_repository=insert_repository,
    )


def _adapter(
    tmp_path: Path,
    source_bytes_by_year: dict[int, bytes],
) -> DefraDesnzProductionSourceAdapter:
    years = {
        year: DefraDesnzSourceYear(
            year=year,
            publication_url=f"https://example.invalid/defra/{year}",
            artifact_url=f"https://example.invalid/defra/{year}.csv",
            title=f"Conversion factors {year}: flat file",
            version_label=f"{year}-test",
            content_type="text/csv",
            format_hint="csv",
        )
        for year in source_bytes_by_year
    }

    def transport(uri: str) -> bytes:
        for year, content in source_bytes_by_year.items():
            if uri.endswith(f"/{year}.csv"):
                return content
        raise FileNotFoundError(uri)

    return DefraDesnzProductionSourceAdapter(
        target_root=tmp_path / "archive",
        source_years=years,
        transport=transport,
    )


def _flat_file_csv(*, year: int) -> bytes:
    return (
        "factor_id,factor_name,category,factor_value,unit,source_year,row_number\n"
        f"electricity-{year},Electricity generated,UK electricity,0.20705,kWh,{year},2\n"
    ).encode("utf-8")


def _downloaded_artifact(path: Path, year: int):
    from carbonfactor_parser.pipeline.production_e2e_year_orchestrator import (
        ProductionE2EDownloadedArtifact,
    )

    return ProductionE2EDownloadedArtifact(
        source_family=DEFRA_DESNZ_SOURCE_FAMILY,
        source_year=year,
        artifact_reference=str(path),
        checksum_sha256="a" * 64,
        content_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        format_hint="xlsx",
        metadata={"version_label": f"{year}-test"},
    )


def _write_minimal_xlsx(path: Path) -> None:
    with ZipFile(path, "w") as archive:
        archive.writestr(
            "[Content_Types].xml",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Override PartName="/xl/workbook.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                '<Override PartName="/xl/worksheets/sheet1.xml" '
                'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
                "</Types>"
            ),
        )
        archive.writestr(
            "xl/workbook.xml",
            (
                '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                '<sheets><sheet name="Flat" sheetId="1" r:id="rId1"/></sheets>'
                "</workbook>"
            ),
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            (
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                'Target="worksheets/sheet1.xml"/>'
                "</Relationships>"
            ),
        )
        archive.writestr(
            "xl/worksheets/sheet1.xml",
            (
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                "<sheetData>"
                "<row r=\"1\">"
                '<c r="A1" t="inlineStr"><is><t>factor_id</t></is></c>'
                '<c r="B1" t="inlineStr"><is><t>factor_name</t></is></c>'
                '<c r="C1" t="inlineStr"><is><t>category</t></is></c>'
                '<c r="D1" t="inlineStr"><is><t>factor_value</t></is></c>'
                '<c r="E1" t="inlineStr"><is><t>unit</t></is></c>'
                "</row>"
                "<row r=\"2\">"
                '<c r="A2" t="inlineStr"><is><t>electricity-2024</t></is></c>'
                '<c r="B2" t="inlineStr"><is><t>Electricity generated</t></is></c>'
                '<c r="C2" t="inlineStr"><is><t>UK electricity</t></is></c>'
                '<c r="D2"><v>0.20705</v></c>'
                '<c r="E2" t="inlineStr"><is><t>kWh</t></is></c>'
                "</row>"
                "</sheetData>"
                "</worksheet>"
            ),
        )
