"""Configuration loading for the configured ingestion cycle runner."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping, Sequence

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
from carbonfactor_parser.pipeline.defra_desnz_production_e2e import (
    DEFRA_DESNZ_SOURCE_FAMILY,
)
from carbonfactor_parser.pipeline.ghg_protocol_production_e2e import (
    GHG_PROTOCOL_SOURCE_FAMILY,
)
from carbonfactor_parser.pipeline.ipcc_efdb_production_e2e import (
    IPCC_EFDB_SOURCE_FAMILY,
)
from carbonfactor_parser.pipeline.production_e2e_year_orchestrator import (
    PRODUCTION_E2E_SOURCE_FAMILIES,
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


__all__ = (
    "CONFIGURED_CYCLE_SOURCE_FAMILIES",
    "ConfiguredCycleRunnerConfig",
    "ConfiguredSourceYearArtifact",
    "load_configured_cycle_runner_config",
)
