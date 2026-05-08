"""Public shared ingestion contracts."""

from carbonfactor_parser.contracts.ingestion import (
    IngestionRun,
    IngestionStatus,
    ParsedFactorRecord,
    PersistenceBootstrapResult,
    SourceAcquisitionResult,
    SourceDocument,
    SourceType,
)

__all__ = (
    "SourceType",
    "SourceDocument",
    "SourceAcquisitionResult",
    "ParsedFactorRecord",
    "IngestionRun",
    "IngestionStatus",
    "PersistenceBootstrapResult",
)
