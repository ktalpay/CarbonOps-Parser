from __future__ import annotations

import json
from pathlib import Path

import pytest

from carbonfactor_parser.persistence.postgresql_runtime_config import (
    load_postgresql_runtime_config,
)
from carbonfactor_parser.persistence.postgresql_runtime_schema_bootstrap import (
    PostgreSQLRuntimeSchemaBootstrapResult,
)
from carbonfactor_parser.persistence.postgresql_year_state_repository import (
    PostgreSQLSourceFamilyYearStateRepository,
)
from carbonfactor_parser.persistence.postgresql_runtime import (
    PostgreSQLRuntimeStartupResult,
)
from carbonfactor_parser.pipeline.configured_cycle_runner import (
    ConfiguredCycleRunnerConfig,
    ConfiguredCycleRunnerStatus,
    ConfiguredSourceYearArtifact,
    load_configured_cycle_runner_config,
    run_configured_cycle_runner,
)


def test_configured_cycle_runner_loads_json_config(tmp_path: Path) -> None:
    config_path = tmp_path / "carbonops-cycle.json"
    config_path.write_text(
        json.dumps(
            {
                "postgresql": {"dsn": "postgresql://user:pass@localhost/db"},
                "archive_root": str(tmp_path / "archive"),
                "enabled_source_families": ["ghg_protocol", "defra_desnz"],
                "initial_year": 2024,
                "cycle": {"interval_seconds": 0, "max_cycles": 2},
                "real_source_smoke": {"allow_live_source_access": True},
                "source_years": {
                    "ghg_protocol": {
                        "2024": {
                            "artifact_url": str(tmp_path / "ghg-2024.csv"),
                            "version_label": "v2024",
                        },
                    },
                },
            },
        ),
        encoding="utf-8",
    )

    config = load_configured_cycle_runner_config(config_path)

    assert config.postgresql_config_result.is_ready
    assert config.archive_root == tmp_path / "archive"
    assert config.enabled_source_families == ("ghg_protocol", "defra_desnz")
    assert config.initial_year == 2024
    assert config.max_cycles == 2
    assert config.allow_live_source_access is True
    assert config.source_years is not None
    assert config.source_years["ghg_protocol"][2024].version_label == "v2024"


def test_configured_cycle_runner_rejects_conflicting_live_source_access_aliases(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "carbonops-cycle.json"
    config_path.write_text(
        json.dumps(
            {
                "postgresql": {"dsn": "postgresql://user:pass@localhost/db"},
                "allow_live_source_access": False,
                "real_source_smoke": {"allow_live_source_access": True},
            },
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Conflicting live source access settings"):
        load_configured_cycle_runner_config(config_path)


def test_configured_cycle_runner_keeps_explicit_false_live_source_access_aliases(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "carbonops-cycle.json"
    config_path.write_text(
        json.dumps(
            {
                "postgresql": {"dsn": "postgresql://user:pass@localhost/db"},
                "allow_live_source_access": False,
                "real_source_smoke": {"allow_live_source_access": False},
            },
        ),
        encoding="utf-8",
    )

    config = load_configured_cycle_runner_config(config_path)

    assert config.allow_live_source_access is False


def test_configured_cycle_runner_loads_top_level_live_source_access_true(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "carbonops-cycle.json"
    config_path.write_text(
        json.dumps(
            {
                "postgresql": {"dsn": "postgresql://user:pass@localhost/db"},
                "allow_live_source_access": True,
            },
        ),
        encoding="utf-8",
    )

    config = load_configured_cycle_runner_config(config_path)

    assert config.allow_live_source_access is True


def test_configured_cycle_runner_runs_2024_to_2027_and_is_idempotent(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    connection = _FakeConnection()
    startup = _startup(connection)
    config = ConfiguredCycleRunnerConfig(
        postgresql_config_result=load_postgresql_runtime_config(
            {"CARBONOPS_POSTGRESQL_DSN": "postgresql://user:pass@localhost/db"},
        ),
        archive_root=tmp_path / "archive",
        enabled_source_families=("ghg_protocol", "defra_desnz", "ipcc_efdb"),
        initial_year=2024,
        cycle_interval_seconds=0,
        max_cycles=4,
        source_years=_source_years(tmp_path),
    )

    result = run_configured_cycle_runner(config, startup=startup, sleep=lambda _: None)

    captured = capsys.readouterr()
    assert result.status is ConfiguredCycleRunnerStatus.COMPLETED
    assert tuple(
        family.year_state.target_year
        for cycle in result.cycles[:3]
        for family in cycle.result.family_results
    ) == (2024, 2024, 2024, 2025, 2025, 2025, 2026, 2026, 2026)
    assert tuple(
        family.status.value for family in result.cycles[-1].result.family_results
    ) == (
        "no_available_source_year",
        "no_available_source_year",
        "no_available_source_year",
    )
    assert "target_year=2027" in captured.out
    assert "status=no_available_source_year" in captured.out
    assert connection.latest_years == {"ghg": 2026, "defra": 2026, "ipcc": 2026}
    assert all(
        connection.table_counts[table_name] > 0
        for table_name in (
            "ghg_emission_factor_masters",
            "ghg_emission_factor_details",
            "defra_emission_factor_masters",
            "defra_emission_factor_details",
            "ipcc_emission_factor_masters",
            "ipcc_emission_factor_details",
        )
    )

    second = run_configured_cycle_runner(config, startup=startup, sleep=lambda _: None)

    assert second.cycles[0].result.family_results[0].year_state.target_year == 2027
    assert connection.latest_years == {"ghg": 2026, "defra": 2026, "ipcc": 2026}


def test_configured_cycle_runner_blocks_https_without_live_opt_in(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    connection = _FakeConnection()
    config = ConfiguredCycleRunnerConfig(
        postgresql_config_result=load_postgresql_runtime_config(
            {"CARBONOPS_POSTGRESQL_DSN": "postgresql://user:pass@localhost/db"},
        ),
        archive_root=tmp_path / "archive",
        enabled_source_families=("ghg_protocol",),
        initial_year=2024,
        cycle_interval_seconds=0,
        max_cycles=1,
        source_years={
            "ghg_protocol": {
                2024: ConfiguredSourceYearArtifact(
                    year=2024,
                    artifact_url="https://example.invalid/factors.csv?token=secret",
                    publication_url="https://example.invalid/publication",
                    title="configured live artifact",
                    version_label="live-2024",
                    content_type="text/csv",
                    format_hint="csv",
                )
            }
        },
        allow_live_source_access=False,
    )

    result = run_configured_cycle_runner(
        config,
        startup=_startup(connection),
        sleep=lambda _: None,
    )

    captured = capsys.readouterr()
    family = result.cycles[0].result.family_results[0]
    assert result.status is ConfiguredCycleRunnerStatus.COMPLETED_WITH_FAILURES
    assert family.status.value == "failed"
    assert family.failures[0].code == "GHG_PROTOCOL_PRODUCTION_DOWNLOAD_FAILED"
    assert "Live HTTPS source access requires explicit real-source smoke opt-in" in (
        family.failures[0].message
    )
    assert "download_status=failed" in captured.out
    assert "parse_status=not_run" in captured.out
    assert "secret" not in family.failures[0].message


def _source_years(
    tmp_path: Path,
) -> dict[str, dict[int, ConfiguredSourceYearArtifact]]:
    source_years: dict[str, dict[int, ConfiguredSourceYearArtifact]] = {
        "ghg_protocol": {},
        "defra_desnz": {},
        "ipcc_efdb": {},
    }
    for year in (2024, 2025, 2026):
        ghg_path = tmp_path / f"ghg-{year}.csv"
        defra_path = tmp_path / f"defra-{year}.csv"
        ipcc_path = tmp_path / f"ipcc-{year}.csv"
        ghg_path.write_text(_ghg_csv(year), encoding="utf-8")
        defra_path.write_text(_defra_csv(year), encoding="utf-8")
        ipcc_path.write_text(_ipcc_csv(year), encoding="utf-8")
        source_years["ghg_protocol"][year] = _artifact(year, ghg_path, f"v{year}")
        source_years["defra_desnz"][year] = _artifact(
            year,
            defra_path,
            f"conversion-factors-{year}",
        )
        source_years["ipcc_efdb"][year] = _artifact(
            year,
            ipcc_path,
            f"efdb-v{year}",
        )
    return source_years


def _artifact(
    year: int,
    path: Path,
    version_label: str,
) -> ConfiguredSourceYearArtifact:
    return ConfiguredSourceYearArtifact(
        year=year,
        artifact_url=str(path),
        publication_url=str(path),
        title=f"fixture {year}",
        version_label=version_label,
        content_type="text/csv",
        format_hint="csv",
    )


def _ghg_csv(year: int) -> str:
    return (
        "record_type,source_year,source_version,factor_id,factor_name,"
        "factor_value,unit,category,subcategory,scope,gas,provenance_note\n"
        f"emission_factor,{year},v{year},GHG-{year}-ELEC,Grid electricity,"
        "0.233,kg CO2e/kWh,Stationary combustion,Electricity,Scope 2,CO2e,"
        "fixture row 1\n"
    )


def _defra_csv(year: int) -> str:
    return (
        "source_year,source_version,category,subcategory,activity,factor_id,"
        "factor_name,factor_value,unit,greenhouse_gas,provenance\n"
        f"{year},conversion-factors-{year},Energy,Electricity,Generated,"
        f"DEFRA-{year}-ELEC,Electricity generated,0.20705,kWh,CO2e,"
        "worksheet:UK electricity row 10\n"
    )


def _ipcc_csv(year: int) -> str:
    return (
        "record_type,source_year,source_version,factor_id,factor_name,"
        "factor_value,unit,category,subcategory,ipcc_sector,gas,region,"
        "technology,provenance\n"
        f"emission_factor,{year},efdb-v{year},IPCC-{year}-ENERGY-CO2,"
        "Stationary combustion CO2,56.1,t CO2/TJ,Energy,"
        "Stationary combustion,1A,CO2,Global,Default,worksheet:EFDB row 12\n"
    )


def _startup(connection: "_FakeConnection") -> PostgreSQLRuntimeStartupResult:
    return PostgreSQLRuntimeStartupResult(
        connection=connection,
        schema_bootstrap=PostgreSQLRuntimeSchemaBootstrapResult(
            required_table_names=(),
            present_table_names=(),
            missing_table_names=(),
            created_table_names=(
                "ghg_emission_factor_masters",
                "ghg_emission_factor_details",
            ),
            statement_count=0,
        ),
        year_state_repository=PostgreSQLSourceFamilyYearStateRepository(connection),
    )


class _FakeCursor:
    def __init__(self, row: tuple[object, ...] | None = None) -> None:
        self._row = row

    def fetchone(self) -> tuple[object, ...] | None:
        return self._row


class _FakeConnection:
    def __init__(self) -> None:
        self.latest_years: dict[str, int] = {}
        self.master_keys: set[tuple[object, ...]] = set()
        self.detail_keys: set[tuple[object, ...]] = set()
        self.table_counts = {
            "ghg_emission_factor_masters": 0,
            "ghg_emission_factor_details": 0,
            "defra_emission_factor_masters": 0,
            "defra_emission_factor_details": 0,
            "ipcc_emission_factor_masters": 0,
            "ipcc_emission_factor_details": 0,
        }

    def execute(self, statement: str, parameters: object | None = None) -> _FakeCursor:
        normalized = " ".join(statement.split()).lower()
        if "select max(ingested_year)" in normalized:
            assert isinstance(parameters, tuple)
            return _FakeCursor((self.latest_years.get(str(parameters[0])),))
        if "insert into source_family_year_states" in normalized:
            assert isinstance(parameters, tuple)
            self.latest_years[str(parameters[1])] = int(parameters[2])
            return _FakeCursor()
        if "_emission_factor_masters" in normalized and normalized.startswith("insert"):
            assert isinstance(parameters, tuple)
            table = _table_name(normalized)
            key = (parameters[1], parameters[2], parameters[3], parameters[8])
            if key in self.master_keys:
                return _FakeCursor()
            self.master_keys.add(key)
            self.table_counts[table] += 1
            return _FakeCursor((parameters[0],))
        if "_emission_factor_details" in normalized and normalized.startswith("insert"):
            assert isinstance(parameters, tuple)
            table = _table_name(normalized)
            key = (parameters[1], parameters[2])
            if key in self.detail_keys:
                return _FakeCursor()
            self.detail_keys.add(key)
            self.table_counts[table] += 1
            return _FakeCursor((parameters[0],))
        return _FakeCursor()

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass


def _table_name(normalized_statement: str) -> str:
    parts = normalized_statement.split()
    return parts[2]
