"""Configured PostgreSQL-backed ingestion cycle runner.

The runner is the application/runtime layer over the existing year
orchestrator. It loads explicit local configuration, starts PostgreSQL, creates
missing Phase 1 tables, and repeatedly runs the configured source families.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import time
import uuid
from typing import Callable, Mapping, Sequence
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from carbonfactor_parser.persistence.postgresql_runtime import (
    PostgreSQLRuntimeStartupResult,
    start_postgresql_runtime,
)
from carbonfactor_parser.persistence.postgresql_runtime_config import (
    POSTGRESQL_RUNTIME_APPLICATION_NAME_ENV_VAR,
    POSTGRESQL_RUNTIME_DATABASE_ENV_VAR,
    POSTGRESQL_RUNTIME_DEFAULT_INITIAL_YEAR,
    POSTGRESQL_RUNTIME_DSN_ENV_VAR,
    POSTGRESQL_RUNTIME_HOST_ENV_VAR,
    POSTGRESQL_RUNTIME_INITIAL_YEAR_ENV_VAR,
    POSTGRESQL_RUNTIME_PASSWORD_ENV_VAR,
    POSTGRESQL_RUNTIME_PORT_ENV_VAR,
    POSTGRESQL_RUNTIME_SSL_MODE_ENV_VAR,
    POSTGRESQL_RUNTIME_USERNAME_ENV_VAR,
    PostgreSQLRuntimeConfigLoadResult,
    load_postgresql_runtime_config,
    load_postgresql_runtime_config_from_environment,
)
from carbonfactor_parser.persistence.postgresql_source_family_repository import (
    PostgreSQLSourceFamilyRuntimeRepository,
)
from carbonfactor_parser.pipeline.defra_desnz_production_e2e import (
    DEFRA_DESNZ_SOURCE_FAMILY,
    DefraDesnzPhase2ValidationBoundary,
    DefraDesnzProductionParserBoundary,
    DefraDesnzProductionSourceAdapter,
    DefraDesnzSourceYear,
)
from carbonfactor_parser.pipeline.ghg_protocol_production_e2e import (
    GHG_PROTOCOL_SOURCE_FAMILY,
    GHGProtocolPhase2ValidationBoundary,
    GHGProtocolProductionParserBoundary,
    GHGProtocolProductionSourceAdapter,
    GHGProtocolSourceYear,
)
from carbonfactor_parser.pipeline.ipcc_efdb_production_e2e import (
    IPCC_EFDB_SOURCE_FAMILY,
    IpccEfdbPhase2ValidationBoundary,
    IpccEfdbProductionParserBoundary,
    IpccEfdbProductionSourceAdapter,
    IpccEfdbSourceYear,
)
from carbonfactor_parser.pipeline.production_e2e_year_orchestrator import (
    PRODUCTION_E2E_SOURCE_FAMILIES,
    ProductionE2EValidationResult,
    ProductionE2EYearOrchestratorDependencies,
    ProductionE2EYearOrchestratorRequest,
    ProductionE2EYearOrchestratorResult,
    ProductionE2EYearRunStatus,
    run_production_e2e_year_orchestrator,
)


CONFIGURED_CYCLE_SOURCE_FAMILIES = PRODUCTION_E2E_SOURCE_FAMILIES
_LIVE_SOURCE_ACCESS_CONFIG_KEYS = (
    ("allow_live_source_access",),
    ("allowLiveSourceAccess",),
    ("live_source_access", "enabled"),
    ("liveSourceAccess", "enabled"),
    ("real_source_smoke", "allow_live_source_access"),
    ("realSourceSmoke", "allowLiveSourceAccess"),
)


class ConfiguredCycleRunnerStatus(str, Enum):
    """Top-level configured cycle runner status."""

    COMPLETED = "completed"
    COMPLETED_WITH_FAILURES = "completed_with_failures"


@dataclass(frozen=True)
class ConfiguredSourceYearArtifact:
    """Config entry for one source-family year artifact."""

    year: int
    artifact_url: str
    publication_url: str = ""
    title: str = ""
    version_label: str = ""
    content_type: str = "text/csv"
    format_hint: str = "csv"


@dataclass(frozen=True)
class ConfiguredCycleRunnerConfig:
    """Validated runtime configuration for the cycle runner."""

    postgresql_config_result: PostgreSQLRuntimeConfigLoadResult
    archive_root: Path
    enabled_source_families: tuple[str, ...] = CONFIGURED_CYCLE_SOURCE_FAMILIES
    initial_year: int = POSTGRESQL_RUNTIME_DEFAULT_INITIAL_YEAR
    cycle_interval_seconds: float = 0.0
    max_cycles: int | None = 1
    source_years: Mapping[str, Mapping[int, ConfiguredSourceYearArtifact]] | None = None
    allow_live_source_access: bool = False


@dataclass(frozen=True)
class ConfiguredCycleResult:
    """One completed application cycle."""

    cycle_number: int
    run_id: str
    result: ProductionE2EYearOrchestratorResult


@dataclass(frozen=True)
class ConfiguredCycleRunnerResult:
    """All cycles run by one application invocation."""

    status: ConfiguredCycleRunnerStatus
    cycles: tuple[ConfiguredCycleResult, ...]
    schema_created_table_names: tuple[str, ...]
    schema_missing_table_names: tuple[str, ...]


class ConfiguredCycleValidationBoundary:
    """Route validation to the source-family-specific validation boundary."""

    def __init__(self) -> None:
        self._boundaries = {
            GHG_PROTOCOL_SOURCE_FAMILY: GHGProtocolPhase2ValidationBoundary(),
            DEFRA_DESNZ_SOURCE_FAMILY: DefraDesnzPhase2ValidationBoundary(),
            IPCC_EFDB_SOURCE_FAMILY: IpccEfdbPhase2ValidationBoundary(),
        }

    def validate(self, batch: object) -> ProductionE2EValidationResult:
        rows = tuple(getattr(batch, "rows", ()))
        source_family = rows[0].source_family if rows else GHG_PROTOCOL_SOURCE_FAMILY
        boundary = self._boundaries.get(source_family)
        if boundary is None:
            boundary = GHGProtocolPhase2ValidationBoundary()
        return boundary.validate(batch)


def load_configured_cycle_runner_config(
    config_path: str | Path | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    max_cycles: int | None = None,
) -> ConfiguredCycleRunnerConfig:
    """Load cycle-runner config from JSON file plus PostgreSQL env fallback."""

    payload = _load_config_payload(config_path)
    postgresql_config_result = _load_postgresql_config(payload, environ)
    archive_root = _validated_archive_root(
        _nested_get(payload, ("archive_root",))
        or _nested_get(payload, ("storage", "rawArchivePath"))
        or _nested_get(payload, ("storage", "raw_archive_path"))
        or "./data/raw",
    )
    initial_year = _positive_int(
        _coalesce_config_values(
            _nested_get(payload, ("initial_year",)),
            _nested_get(payload, ("cycle", "initial_year")),
            _nested_get(payload, ("execution", "initialYear")),
            POSTGRESQL_RUNTIME_DEFAULT_INITIAL_YEAR,
        ),
        field_name="initial_year",
    )
    interval_seconds = _non_negative_float(
        _coalesce_config_values(
            _nested_get(payload, ("cycle_interval_seconds",)),
            _nested_get(payload, ("cycle", "interval_seconds")),
            0,
        ),
        field_name="cycle_interval_seconds",
    )
    configured_max_cycles = _optional_positive_int(
        max_cycles
        if max_cycles is not None
        else _coalesce_config_values(
            _nested_get(payload, ("max_cycles",)),
            _nested_get(payload, ("cycle", "max_cycles")),
            1,
        ),
        field_name="max_cycles",
    )
    enabled_source_families = _enabled_source_families(payload)
    source_years = _source_years_from_payload(payload)
    allow_live_source_access = _allow_live_source_access_value(payload)

    return ConfiguredCycleRunnerConfig(
        postgresql_config_result=postgresql_config_result,
        archive_root=archive_root,
        enabled_source_families=enabled_source_families,
        initial_year=initial_year,
        cycle_interval_seconds=interval_seconds,
        max_cycles=configured_max_cycles,
        source_years=source_years,
        allow_live_source_access=allow_live_source_access,
    )


def run_configured_cycle_runner(
    config: ConfiguredCycleRunnerConfig,
    *,
    startup: PostgreSQLRuntimeStartupResult | None = None,
    sleep: Callable[[float], None] = time.sleep,
    emit: Callable[[str], None] | None = print,
) -> ConfiguredCycleRunnerResult:
    """Start PostgreSQL runtime and execute configured ingestion cycles."""

    runtime = startup or start_postgresql_runtime(config.postgresql_config_result)
    if emit is not None:
        _emit_startup_summary(config, runtime, emit)

    dependencies = _build_dependencies(config, runtime)
    cycles: list[ConfiguredCycleResult] = []
    cycle_number = 1
    while config.max_cycles is None or cycle_number <= config.max_cycles:
        run_id = f"configured-cycle-{cycle_number}-{uuid.uuid4().hex}"
        result = run_production_e2e_year_orchestrator(
            ProductionE2EYearOrchestratorRequest(
                run_id=run_id,
                enabled_source_families=config.enabled_source_families,
                initial_year=config.initial_year,
            ),
            dependencies,
        )
        cycle = ConfiguredCycleResult(
            cycle_number=cycle_number,
            run_id=run_id,
            result=result,
        )
        cycles.append(cycle)
        if emit is not None:
            emit_configured_cycle_summary(cycle, emit=emit)

        cycle_number += 1
        if config.max_cycles is not None and cycle_number > config.max_cycles:
            break
        if config.cycle_interval_seconds > 0:
            sleep(config.cycle_interval_seconds)

    failed = any(
        cycle.result.status is not ProductionE2EYearRunStatus.COMPLETED
        for cycle in cycles
    )
    return ConfiguredCycleRunnerResult(
        status=(
            ConfiguredCycleRunnerStatus.COMPLETED_WITH_FAILURES
            if failed
            else ConfiguredCycleRunnerStatus.COMPLETED
        ),
        cycles=tuple(cycles),
        schema_created_table_names=runtime.schema_bootstrap.created_table_names,
        schema_missing_table_names=runtime.schema_bootstrap.missing_table_names,
    )


def emit_configured_cycle_summary(
    cycle: ConfiguredCycleResult,
    *,
    emit: Callable[[str], None] = print,
) -> None:
    """Print user-readable summary output for one cycle."""

    summary = cycle.result.summary
    emit(
        "cycle="
        f"{cycle.cycle_number} run_id={cycle.run_id} status={cycle.result.status.value}"
    )
    emit(
        "summary "
        f"completed={summary.completed_family_count} "
        f"no_available_source_year={summary.no_available_source_year_count} "
        f"failed={summary.failed_family_count} "
        f"parsed_rows={summary.parsed_row_count} "
        f"inserted={summary.inserted_count} "
        f"skipped_duplicates={summary.skipped_duplicate_count}"
    )
    for family in cycle.result.family_results:
        insert_summary = family.insert_summary
        emit(
            "source "
            f"family={family.source_family} "
            f"target_year={family.year_state.target_year} "
            f"latest_year={family.year_state.latest_year} "
            f"status={family.status.value} "
            f"download_status={_download_status_value(family.download_result)} "
            f"parse_status={_parse_status_value(family)} "
            f"parsed_rows={family.parsed_row_count} "
            f"master_inserted={getattr(insert_summary, 'master_inserted', 0)} "
            f"master_skipped={getattr(insert_summary, 'master_skipped', 0)} "
            f"detail_inserted={getattr(insert_summary, 'detail_inserted', 0)} "
            f"detail_skipped={getattr(insert_summary, 'detail_skipped', 0)}"
        )
        for failure in family.failures:
            safe_message = _redact_sensitive_text(str(failure.message))
            emit(
                "issue "
                f"family={failure.source_family} stage={failure.stage} "
                f"code={failure.code} message={safe_message}"
            )


def _build_dependencies(
    config: ConfiguredCycleRunnerConfig,
    runtime: PostgreSQLRuntimeStartupResult,
) -> ProductionE2EYearOrchestratorDependencies:
    transport = _build_configured_artifact_transport(
        allow_live_source_access=config.allow_live_source_access,
    )
    source_years = config.source_years or {}
    return ProductionE2EYearOrchestratorDependencies(
        year_state_repository=runtime.year_state_repository,
        source_adapters={
            GHG_PROTOCOL_SOURCE_FAMILY: GHGProtocolProductionSourceAdapter(
                target_root=config.archive_root,
                source_years=_ghg_source_years(
                    source_years.get(GHG_PROTOCOL_SOURCE_FAMILY, {}),
                ),
                transport=transport,
            ),
            DEFRA_DESNZ_SOURCE_FAMILY: DefraDesnzProductionSourceAdapter(
                target_root=config.archive_root,
                source_years=_defra_source_years(
                    source_years.get(DEFRA_DESNZ_SOURCE_FAMILY, {}),
                ),
                transport=transport,
            ),
            IPCC_EFDB_SOURCE_FAMILY: IpccEfdbProductionSourceAdapter(
                target_root=config.archive_root,
                source_years=_ipcc_source_years(
                    source_years.get(IPCC_EFDB_SOURCE_FAMILY, {}),
                ),
                transport=transport,
            ),
        },
        parser_boundaries={
            GHG_PROTOCOL_SOURCE_FAMILY: GHGProtocolProductionParserBoundary(),
            DEFRA_DESNZ_SOURCE_FAMILY: DefraDesnzProductionParserBoundary(),
            IPCC_EFDB_SOURCE_FAMILY: IpccEfdbProductionParserBoundary(),
        },
        validation_boundary=ConfiguredCycleValidationBoundary(),
        insert_repository=PostgreSQLSourceFamilyRuntimeRepository(runtime.connection),
    )


def _build_configured_artifact_transport(
    *,
    allow_live_source_access: bool,
) -> Callable[[str], bytes]:
    def transport(uri: str) -> bytes:
        return _configured_artifact_transport(
            uri,
            allow_live_source_access=allow_live_source_access,
        )

    return transport


def _configured_artifact_transport(
    uri: str,
    *,
    allow_live_source_access: bool = False,
) -> bytes:
    parsed = urlparse(uri)
    if parsed.scheme == "file":
        return Path(parsed.path).read_bytes()
    if parsed.scheme in {"", "local"}:
        return Path(parsed.path if parsed.scheme == "local" else uri).read_bytes()
    if parsed.scheme == "https":
        if not allow_live_source_access:
            raise ValueError(
                "Live HTTPS source access requires explicit real-source smoke opt-in.",
            )
        request = Request(uri, headers={"User-Agent": "carbonops-parser/0.1"})
        with urlopen(request, timeout=60) as response:  # noqa: S310
            return bytes(response.read())
    raise ValueError("Configured artifacts must use file, local path, or HTTPS URI.")


def _emit_startup_summary(
    config: ConfiguredCycleRunnerConfig,
    runtime: PostgreSQLRuntimeStartupResult,
    emit: Callable[[str], None],
) -> None:
    emit("carbonops ingestion application started")
    emit(f"archive_root={config.archive_root}")
    emit(f"enabled_source_families={','.join(config.enabled_source_families)}")
    emit(f"initial_year={config.initial_year}")
    emit(f"cycle_interval_seconds={config.cycle_interval_seconds:g}")
    emit(f"max_cycles={config.max_cycles}")
    emit(f"allow_live_source_access={config.allow_live_source_access}")
    emit(
        "postgresql_schema "
        f"created={','.join(runtime.schema_bootstrap.created_table_names) or 'none'} "
        f"missing={','.join(runtime.schema_bootstrap.missing_table_names) or 'none'}"
    )


def _load_config_payload(config_path: str | Path | None) -> Mapping[str, object]:
    if config_path is None:
        return {}
    path = Path(config_path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".json", ""}:
        payload = json.loads(text)
        if not isinstance(payload, Mapping):
            raise ValueError("Cycle runner config root must be an object.")
        return payload
    raise ValueError("Cycle runner config currently supports JSON files.")


def _load_postgresql_config(
    payload: Mapping[str, object],
    environ: Mapping[str, str] | None,
) -> PostgreSQLRuntimeConfigLoadResult:
    postgresql = _nested_get(payload, ("postgresql",))
    database = _nested_get(payload, ("database",))
    if isinstance(postgresql, Mapping) or isinstance(database, Mapping):
        source = postgresql if isinstance(postgresql, Mapping) else database
        values = {
            POSTGRESQL_RUNTIME_DSN_ENV_VAR: source.get("dsn"),
            POSTGRESQL_RUNTIME_HOST_ENV_VAR: source.get("host"),
            POSTGRESQL_RUNTIME_PORT_ENV_VAR: source.get("port"),
            POSTGRESQL_RUNTIME_DATABASE_ENV_VAR: source.get("database"),
            POSTGRESQL_RUNTIME_USERNAME_ENV_VAR: source.get("username"),
            POSTGRESQL_RUNTIME_PASSWORD_ENV_VAR: source.get("password"),
            POSTGRESQL_RUNTIME_SSL_MODE_ENV_VAR: source.get("ssl_mode")
            or source.get("sslMode"),
            POSTGRESQL_RUNTIME_APPLICATION_NAME_ENV_VAR: source.get(
                "application_name",
            )
            or source.get("applicationName"),
            POSTGRESQL_RUNTIME_INITIAL_YEAR_ENV_VAR: source.get("initial_year")
            or source.get("initialYear")
            or _nested_get(payload, ("initial_year",)),
        }
        return load_postgresql_runtime_config(values)
    return load_postgresql_runtime_config_from_environment(environ)


def _source_years_from_payload(
    payload: Mapping[str, object],
) -> Mapping[str, Mapping[int, ConfiguredSourceYearArtifact]]:
    source_year_payload = (
        _nested_get(payload, ("source_years",))
        or _nested_get(payload, ("sourceYears",))
        or _nested_get(payload, ("sources",))
        or {}
    )
    if not isinstance(source_year_payload, Mapping):
        raise ValueError("source_years must be an object keyed by source family.")

    result: dict[str, dict[int, ConfiguredSourceYearArtifact]] = {}
    for raw_family, raw_years in source_year_payload.items():
        family = _source_family_alias(str(raw_family))
        if family is None:
            raise ValueError(
                f"Unsupported source family in source_years: {raw_family}.",
            )
        years_payload = _extract_years_payload(raw_years)
        if not isinstance(years_payload, Mapping):
            raise ValueError(f"source_years.{family} must be an object keyed by year.")
        years: dict[int, ConfiguredSourceYearArtifact] = {}
        for raw_year, raw_entry in years_payload.items():
            entry = raw_entry if isinstance(raw_entry, Mapping) else {}
            try:
                year = _positive_int(raw_year, field_name="source_year")
            except ValueError as exc:
                raise ValueError(
                    f"source_years.{family} year key must be a positive integer.",
                ) from exc
            artifact_url = str(
                entry.get("artifact_url")
                or entry.get("artifactUrl")
                or entry.get("path")
                or entry.get("local_path")
                or entry.get("localPath")
                or ""
            ).strip()
            if not artifact_url:
                raise ValueError(
                    f"source_years.{family}.{year} requires artifact_url.",
                )
            years[year] = ConfiguredSourceYearArtifact(
                year=year,
                artifact_url=artifact_url,
                publication_url=str(
                    entry.get("publication_url")
                    or entry.get("publicationUrl")
                    or artifact_url
                ),
                title=str(entry.get("title") or f"{family} {year}"),
                version_label=str(
                    entry.get("version_label")
                    or entry.get("versionLabel")
                    or f"{year}"
                ),
                content_type=str(
                    entry.get("content_type")
                    or entry.get("contentType")
                    or "text/csv",
                ),
                format_hint=str(
                    entry.get("format_hint") or entry.get("formatHint") or "csv",
                ),
            )
        result[family] = years
    return result


def _extract_years_payload(raw_value: object) -> object:
    if not isinstance(raw_value, Mapping):
        return raw_value
    return raw_value.get("years") or raw_value.get("source_years") or raw_value


def _enabled_source_families(payload: Mapping[str, object]) -> tuple[str, ...]:
    configured = (
        _nested_get(payload, ("enabled_source_families",))
        or _nested_get(payload, ("enabledSourceFamilies",))
        or _nested_get(payload, ("sources_enabled",))
    )
    if isinstance(configured, str):
        raw_values: Sequence[object] = tuple(
            value.strip() for value in configured.split(",")
        )
    elif isinstance(configured, Sequence):
        raw_values = configured
    else:
        raw_values = CONFIGURED_CYCLE_SOURCE_FAMILIES
    selected = []
    for raw_value in raw_values:
        family = _source_family_alias(str(raw_value))
        if family is None:
            raise ValueError(f"Unsupported enabled source family: {raw_value}.")
        if family not in selected:
            selected.append(family)
    return tuple(selected) or CONFIGURED_CYCLE_SOURCE_FAMILIES


def _validated_archive_root(value: object) -> Path:
    if not isinstance(value, (str, Path)):
        raise ValueError("archive_root must be a string path.")
    path = Path(str(value))
    if path.exists() and not path.is_dir():
        raise ValueError("archive_root must be a directory path.")
    if not path.exists():
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ValueError("archive_root could not be created.") from exc
    if not path.is_dir():
        raise ValueError("archive_root must resolve to a directory.")
    if not path.exists() or not path.stat():
        raise ValueError("archive_root is not accessible.")
    return path


def _non_negative_float(value: object, *, field_name: str) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a non-negative number.") from exc
    if parsed < 0:
        raise ValueError(f"{field_name} must be a non-negative number.")
    return parsed


def _redact_sensitive_text(text: str) -> str:
    redacted = text
    if "://" in redacted:
        parsed = urlparse(redacted)
        if parsed.scheme and (parsed.username or parsed.password or parsed.query):
            netloc = parsed.hostname or ""
            if parsed.port:
                netloc = f"{netloc}:{parsed.port}"
            redacted = parsed._replace(netloc=netloc, query="[redacted]").geturl()
    lowered = redacted.lower()
    for marker in ("password", "token", "secret", "key", "dsn"):
        if marker in lowered and "=" in redacted:
            return "[redacted sensitive value]"
    return redacted


def _source_family_alias(value: str) -> str | None:
    normalized = value.strip().lower()
    aliases = {
        "ghg": GHG_PROTOCOL_SOURCE_FAMILY,
        "ghg_protocol": GHG_PROTOCOL_SOURCE_FAMILY,
        "ghgprotocol": GHG_PROTOCOL_SOURCE_FAMILY,
        "defra": DEFRA_DESNZ_SOURCE_FAMILY,
        "desnz": DEFRA_DESNZ_SOURCE_FAMILY,
        "defra_desnz": DEFRA_DESNZ_SOURCE_FAMILY,
        "defradesnz": DEFRA_DESNZ_SOURCE_FAMILY,
        "ipcc": IPCC_EFDB_SOURCE_FAMILY,
        "ipcc_efdb": IPCC_EFDB_SOURCE_FAMILY,
        "ipccefdb": IPCC_EFDB_SOURCE_FAMILY,
    }
    return aliases.get(normalized)


def _ghg_source_years(
    values: Mapping[int, ConfiguredSourceYearArtifact],
) -> Mapping[int, GHGProtocolSourceYear]:
    return {
        year: GHGProtocolSourceYear(
            year=entry.year,
            publication_url=entry.publication_url,
            artifact_url=entry.artifact_url,
            title=entry.title,
            version_label=entry.version_label,
            content_type=entry.content_type,
            format_hint=entry.format_hint,
        )
        for year, entry in values.items()
    }


def _defra_source_years(
    values: Mapping[int, ConfiguredSourceYearArtifact],
) -> Mapping[int, DefraDesnzSourceYear]:
    return {
        year: DefraDesnzSourceYear(
            year=entry.year,
            publication_url=entry.publication_url,
            artifact_url=entry.artifact_url,
            title=entry.title,
            version_label=entry.version_label,
            content_type=entry.content_type,
            format_hint=entry.format_hint,
        )
        for year, entry in values.items()
    }


def _ipcc_source_years(
    values: Mapping[int, ConfiguredSourceYearArtifact],
) -> Mapping[int, IpccEfdbSourceYear]:
    return {
        year: IpccEfdbSourceYear(
            year=entry.year,
            publication_url=entry.publication_url,
            artifact_url=entry.artifact_url,
            title=entry.title,
            version_label=entry.version_label,
            content_type=entry.content_type,
            format_hint=entry.format_hint,
        )
        for year, entry in values.items()
    }


def _nested_get(payload: Mapping[str, object], keys: tuple[str, ...]) -> object | None:
    current: object = payload
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def _nested_lookup(
    payload: Mapping[str, object],
    keys: tuple[str, ...],
) -> tuple[bool, object | None]:
    current: object = payload
    for key in keys:
        if not isinstance(current, Mapping) or key not in current:
            return False, None
        current = current[key]
    return True, current


def _coalesce_config_values(*values: object) -> object:
    for value in values:
        if value is not None:
            return value
    return None


def _positive_int(value: object, *, field_name: str) -> int:
    try:
        parsed = int(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a positive integer.") from exc
    if parsed < 1:
        raise ValueError(f"{field_name} must be a positive integer.")
    return parsed


def _optional_positive_int(value: object, *, field_name: str) -> int | None:
    if value is None or value == "":
        return None
    return _positive_int(value, field_name=field_name)


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    normalized = str(value).strip().lower()
    return normalized in {"1", "true", "yes", "y", "on"}


def _allow_live_source_access_value(payload: Mapping[str, object]) -> bool:
    resolved_values: list[tuple[str, bool]] = []
    for key_path in _LIVE_SOURCE_ACCESS_CONFIG_KEYS:
        found, value = _nested_lookup(payload, key_path)
        if found:
            resolved_values.append((".".join(key_path), _bool_value(value)))

    if not resolved_values:
        return False

    unique_values = {value for _, value in resolved_values}
    if len(unique_values) > 1:
        configured_keys = ", ".join(key for key, _ in resolved_values)
        raise ValueError(
            "Conflicting live source access settings were provided: "
            f"{configured_keys}.",
        )

    return resolved_values[0][1]


def _download_status_value(download_result: object | None) -> str:
    if download_result is None:
        return "not_run"
    return str(getattr(getattr(download_result, "status", None), "value", "unknown"))


def _parse_status_value(family: object) -> str:
    if getattr(family, "parsed_row_count", 0) > 0:
        return "parsed"
    failures = tuple(getattr(family, "failures", ()))
    if any(getattr(failure, "stage", "") == "parser" for failure in failures):
        return "failed"
    download_result = getattr(family, "download_result", None)
    if download_result is None or _download_status_value(download_result) != "downloaded":
        return "not_run"
    return "no_rows"


__all__ = (
    "CONFIGURED_CYCLE_SOURCE_FAMILIES",
    "ConfiguredCycleResult",
    "ConfiguredCycleRunnerConfig",
    "ConfiguredCycleRunnerResult",
    "ConfiguredCycleRunnerStatus",
    "ConfiguredCycleValidationBoundary",
    "ConfiguredSourceYearArtifact",
    "emit_configured_cycle_summary",
    "load_configured_cycle_runner_config",
    "run_configured_cycle_runner",
)
