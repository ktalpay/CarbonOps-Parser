"""Production runtime configuration boundary without environment loading."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


PRODUCTION_CONFIG_REQUIRED_ENV_VARS: tuple[str, ...] = (
    "CARBONOPS_PARSER_ENV",
    "CARBONOPS_PARSER_DATABASE_PROVIDER",
    "CARBONOPS_PARSER_POSTGRES_HOST",
    "CARBONOPS_PARSER_POSTGRES_PORT",
    "CARBONOPS_PARSER_POSTGRES_DATABASE",
    "CARBONOPS_PARSER_POSTGRES_USERNAME",
    "CARBONOPS_PARSER_POSTGRES_PASSWORD",
    "CARBONOPS_PARSER_POSTGRES_SCHEMA",
    "CARBONOPS_PARSER_RAW_ARCHIVE_PATH",
    "CARBONOPS_PARSER_LOG_LEVEL",
)

PRODUCTION_CONFIG_SECRET_ENV_VARS: tuple[str, ...] = (
    "CARBONOPS_PARSER_POSTGRES_PASSWORD",
)

_VALID_LOG_LEVELS = frozenset({"debug", "info", "warning", "error", "critical"})


@dataclass(frozen=True)
class ProductionConfigValidationIssue:
    """Safe production config validation issue with no configured values."""

    code: str
    message: str
    field_name: str
    severity: str = "error"


@dataclass(frozen=True)
class ProductionConfigValidationResult:
    """Side-effect-free validation result for production config mappings."""

    issues: tuple[ProductionConfigValidationIssue, ...] = ()

    @property
    def is_valid(self) -> bool:
        return not self.issues


@dataclass(frozen=True)
class ProductionConfigBoundaryDescription:
    """Shared Python/.NET production configuration expectations."""

    required_env_vars: tuple[str, ...]
    secret_env_vars: tuple[str, ...]
    provider: str
    loads_environment: bool
    loads_config_files: bool
    loads_credentials: bool
    logs_secret_values: bool
    notes: tuple[str, ...]


def describe_production_config_boundary() -> ProductionConfigBoundaryDescription:
    """Describe production config expectations without reading configuration."""

    return ProductionConfigBoundaryDescription(
        required_env_vars=PRODUCTION_CONFIG_REQUIRED_ENV_VARS,
        secret_env_vars=PRODUCTION_CONFIG_SECRET_ENV_VARS,
        provider="postgres",
        loads_environment=False,
        loads_config_files=False,
        loads_credentials=False,
        logs_secret_values=False,
        notes=(
            "Callers pass an explicit mapping for validation.",
            "CARBONOPS_PARSER_POSTGRES_PASSWORD is required but never returned.",
            "Connection strings are not accepted as production config values.",
            "Validation messages name keys only and do not echo configured values.",
        ),
    )


def validate_production_config_mapping(
    values: Mapping[str, str | None],
) -> ProductionConfigValidationResult:
    """Validate required production config keys without loading env or secrets."""

    issues: list[ProductionConfigValidationIssue] = []

    for env_var in PRODUCTION_CONFIG_REQUIRED_ENV_VARS:
        if not _has_text(values.get(env_var)):
            issues.append(
                ProductionConfigValidationIssue(
                    code="PRODUCTION_CONFIG_MISSING_REQUIRED_ENV_VAR",
                    message=f"{env_var} must be set for production startup.",
                    field_name=env_var,
                ),
            )

    provider = values.get("CARBONOPS_PARSER_DATABASE_PROVIDER")
    if _has_text(provider) and provider.strip().lower() != "postgres":
        issues.append(
            ProductionConfigValidationIssue(
                code="PRODUCTION_CONFIG_UNSUPPORTED_DATABASE_PROVIDER",
                message="Unsupported database provider. Phase 1 supports postgres only.",
                field_name="CARBONOPS_PARSER_DATABASE_PROVIDER",
            ),
        )

    _validate_port(values.get("CARBONOPS_PARSER_POSTGRES_PORT"), issues)
    _validate_log_level(values.get("CARBONOPS_PARSER_LOG_LEVEL"), issues)

    if _has_text(values.get("CARBONOPS_PARSER_POSTGRES_CONNECTION_STRING")):
        issues.append(
            ProductionConfigValidationIssue(
                code="PRODUCTION_CONFIG_RAW_CONNECTION_STRING_NOT_ALLOWED",
                message=(
                    "Raw PostgreSQL connection strings are not accepted; use split "
                    "non-secret fields and CARBONOPS_PARSER_POSTGRES_PASSWORD."
                ),
                field_name="CARBONOPS_PARSER_POSTGRES_CONNECTION_STRING",
            ),
        )

    return ProductionConfigValidationResult(issues=tuple(issues))


def _validate_port(
    raw_value: str | None,
    issues: list[ProductionConfigValidationIssue],
) -> None:
    if not _has_text(raw_value):
        return
    try:
        port = int(raw_value)
    except ValueError:
        port = 0
    if not 1 <= port <= 65535:
        issues.append(
            ProductionConfigValidationIssue(
                code="PRODUCTION_CONFIG_INVALID_POSTGRES_PORT",
                message="CARBONOPS_PARSER_POSTGRES_PORT must be an integer between 1 and 65535.",
                field_name="CARBONOPS_PARSER_POSTGRES_PORT",
            ),
        )


def _validate_log_level(
    raw_value: str | None,
    issues: list[ProductionConfigValidationIssue],
) -> None:
    if not _has_text(raw_value):
        return
    if raw_value.strip().lower() not in _VALID_LOG_LEVELS:
        issues.append(
            ProductionConfigValidationIssue(
                code="PRODUCTION_CONFIG_INVALID_LOG_LEVEL",
                message=(
                    "CARBONOPS_PARSER_LOG_LEVEL must be one of debug, info, "
                    "warning, error, or critical."
                ),
                field_name="CARBONOPS_PARSER_LOG_LEVEL",
            ),
        )


def _has_text(value: str | None) -> bool:
    return isinstance(value, str) and bool(value.strip())

