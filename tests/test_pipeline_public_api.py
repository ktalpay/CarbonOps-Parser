import carbonfactor_parser.pipeline as pipeline
from carbonfactor_parser.pipeline import local_dry_run
from carbonfactor_parser.pipeline import (
    LocalFilePersistenceDryRunIssue,
    LocalFilePersistenceDryRunResult,
    LocalFilePersistenceDryRunStatus,
    run_local_file_normalized_persistence_dry_run,
)


EXPECTED_PUBLIC_SYMBOLS = (
    "LocalFilePersistenceDryRunIssue",
    "LocalFilePersistenceDryRunResult",
    "LocalFilePersistenceDryRunStatus",
    "run_local_file_normalized_persistence_dry_run",
)

EXPECTED_PUBLIC_EXPORTS = {
    "LocalFilePersistenceDryRunIssue": (
        local_dry_run.LocalFilePersistenceDryRunIssue
    ),
    "LocalFilePersistenceDryRunResult": (
        local_dry_run.LocalFilePersistenceDryRunResult
    ),
    "LocalFilePersistenceDryRunStatus": (
        local_dry_run.LocalFilePersistenceDryRunStatus
    ),
    "run_local_file_normalized_persistence_dry_run": (
        local_dry_run.run_local_file_normalized_persistence_dry_run
    ),
}


def test_expected_pipeline_public_symbols_import_from_package() -> None:
    imported_symbols = {
        "LocalFilePersistenceDryRunIssue": LocalFilePersistenceDryRunIssue,
        "LocalFilePersistenceDryRunResult": LocalFilePersistenceDryRunResult,
        "LocalFilePersistenceDryRunStatus": LocalFilePersistenceDryRunStatus,
        "run_local_file_normalized_persistence_dry_run": (
            run_local_file_normalized_persistence_dry_run
        ),
    }

    assert tuple(imported_symbols) == EXPECTED_PUBLIC_SYMBOLS
    assert imported_symbols == {
        name: getattr(pipeline, name) for name in EXPECTED_PUBLIC_SYMBOLS
    }


def test_pipeline_all_lists_expected_public_symbols() -> None:
    assert pipeline.__all__ == EXPECTED_PUBLIC_SYMBOLS


def test_pipeline_public_exports_match_origin_modules() -> None:
    assert {
        name: getattr(pipeline, name) for name in EXPECTED_PUBLIC_SYMBOLS
    } == EXPECTED_PUBLIC_EXPORTS


def test_pipeline_all_names_resolve_to_package_attributes() -> None:
    for name in pipeline.__all__:
        assert hasattr(pipeline, name)


def test_pipeline_all_excludes_internal_module_names() -> None:
    assert "local_dry_run" not in pipeline.__all__
    assert all(not name.startswith("_") for name in pipeline.__all__)
