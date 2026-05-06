import carbonfactor_parser.persistence as persistence
from carbonfactor_parser.persistence import (
    ddl_preview,
    input,
    integration_test_boundary,
    postgresql_connection_session_contract,
    postgresql_disabled_runtime_execution_adapter,
    postgresql_execution_adapter_boundary,
    postgresql_idempotency_conflict_strategy,
    postgresql_insert_builder,
    postgresql_options,
    postgresql_persistence_preview,
    postgresql_psycopg_session_adapter,
    postgresql_repository,
    postgresql_transaction_policy,
    repository,
    schema,
)
from carbonfactor_parser.persistence import (
    PersistenceInput,
    PersistenceInputBuildResult,
    PersistenceInputBuildStatus,
    PersistenceInputIssue,
    PersistenceInputRecord,
    POSTGRESQL_INTEGRATION_TEST_MARKER,
    POSTGRESQL_INTEGRATION_TEST_SKIP_REASON,
    PersistenceIssue,
    PersistenceIssueSeverity,
    PersistenceRepository,
    PersistenceResult,
    PersistenceResultStatus,
    PsycopgPostgreSQLSessionAdapter,
    PsycopgPostgreSQLSessionAdapterBoundaryResult,
    PsycopgPostgreSQLSessionAdapterMetadata,
    PsycopgPostgreSQLSessionAdapterStatus,
    PostgreSQLIntegrationTestBoundary,
    PostgreSQLInsertBuildIssue,
    PostgreSQLInsertBuildResult,
    PostgreSQLInsertBuildStatus,
    PostgreSQLInsertStatement,
    PostgreSQLConflictAction,
    PostgreSQLConflictStrategyIssue,
    PostgreSQLConflictStrategyPlan,
    PostgreSQLConflictStrategyPlanResult,
    PostgreSQLConflictStrategyStatus,
    PostgreSQLConnectionSession,
    PostgreSQLConnectionSessionContractDescription,
    PostgreSQLDisabledRuntimeExecutionAdapter,
    PostgreSQLDisabledRuntimeExecutionDescription,
    PostgreSQLDisabledRuntimeExecutionMetadata,
    PostgreSQLDisabledRuntimeExecutionResult,
    PostgreSQLDisabledRuntimeExecutionStatus,
    PostgreSQLExecutionAdapterProtocol,
    PostgreSQLExecutionBoundaryDescription,
    PostgreSQLExecutionIssue,
    PostgreSQLExecutionPlan,
    PostgreSQLExecutionPlanResult,
    PostgreSQLExecutionResult,
    PostgreSQLExecutionStatus,
    PostgreSQLBatchTransactionMode,
    PostgreSQLIdempotencyConflictStrategy,
    PostgreSQLIdempotencyConflictStrategyDescription,
    PostgreSQLIdempotencyRequirement,
    PostgreSQLPartialSuccessPolicy,
    PostgreSQLPersistenceColumn,
    PostgreSQLPersistenceOptions,
    PostgreSQLPersistenceOptionsValidationIssue,
    PostgreSQLPersistenceOptionsValidationResult,
    PostgreSQLPersistencePreview,
    PostgreSQLPersistencePreviewIssue,
    PostgreSQLPersistencePreviewResult,
    PostgreSQLPersistencePreviewStatus,
    PostgreSQLPersistenceRepository,
    PostgreSQLPersistenceSchema,
    PostgreSQLStatementExecutionContract,
    PostgreSQLTransactionBoundary,
    PostgreSQLTransactionFailurePolicy,
    PostgreSQLTransactionMode,
    PostgreSQLTransactionPlan,
    PostgreSQLTransactionPlanResult,
    PostgreSQLTransactionOwnership,
    PostgreSQLTransactionPolicy,
    PostgreSQLTransactionPolicyDescription,
    PostgreSQLTransactionPolicyIssue,
    PostgreSQLTransactionPolicyStatus,
    build_persistence_input_from_normalization_result,
    build_default_postgresql_transaction_policy,
    build_default_postgresql_idempotency_conflict_strategy,
    build_disabled_postgresql_execution_result,
    build_psycopg_session_adapter_metadata,
    build_postgresql_disabled_runtime_execution_result,
    build_postgresql_conflict_strategy_plan,
    build_postgresql_execution_plan,
    build_postgresql_insert_statement,
    build_postgresql_persistence_preview,
    build_postgresql_transaction_plan,
    create_persistence_result,
    create_postgresql_integration_test_boundary,
    create_postgresql_persistence_options,
    describe_postgresql_connection_session_contract,
    describe_postgresql_disabled_runtime_execution,
    describe_postgresql_execution_adapter_boundary,
    describe_postgresql_idempotency_conflict_strategy_boundary,
    describe_postgresql_transaction_policy_boundary,
    get_normalized_record_postgresql_schema,
    render_postgresql_ddl_preview,
    should_skip_postgresql_integration_tests,
    validate_psycopg_session_adapter_boundary,
    validate_postgresql_persistence_options,
)


EXPECTED_PUBLIC_SYMBOLS = (
    "PersistenceInput",
    "PersistenceInputBuildResult",
    "PersistenceInputBuildStatus",
    "PersistenceInputIssue",
    "PersistenceInputRecord",
    "POSTGRESQL_INTEGRATION_TEST_MARKER",
    "POSTGRESQL_INTEGRATION_TEST_SKIP_REASON",
    "PersistenceIssue",
    "PersistenceIssueSeverity",
    "PersistenceRepository",
    "PersistenceResult",
    "PersistenceResultStatus",
    "PsycopgPostgreSQLSessionAdapter",
    "PsycopgPostgreSQLSessionAdapterBoundaryResult",
    "PsycopgPostgreSQLSessionAdapterMetadata",
    "PsycopgPostgreSQLSessionAdapterStatus",
    "PostgreSQLIntegrationTestBoundary",
    "PostgreSQLInsertBuildIssue",
    "PostgreSQLInsertBuildResult",
    "PostgreSQLInsertBuildStatus",
    "PostgreSQLInsertStatement",
    "PostgreSQLConflictAction",
    "PostgreSQLConflictStrategyIssue",
    "PostgreSQLConflictStrategyPlan",
    "PostgreSQLConflictStrategyPlanResult",
    "PostgreSQLConflictStrategyStatus",
    "PostgreSQLConnectionSession",
    "PostgreSQLConnectionSessionContractDescription",
    "PostgreSQLDisabledRuntimeExecutionAdapter",
    "PostgreSQLDisabledRuntimeExecutionDescription",
    "PostgreSQLDisabledRuntimeExecutionMetadata",
    "PostgreSQLDisabledRuntimeExecutionResult",
    "PostgreSQLDisabledRuntimeExecutionStatus",
    "PostgreSQLExecutionAdapterProtocol",
    "PostgreSQLExecutionBoundaryDescription",
    "PostgreSQLExecutionIssue",
    "PostgreSQLExecutionPlan",
    "PostgreSQLExecutionPlanResult",
    "PostgreSQLExecutionResult",
    "PostgreSQLExecutionStatus",
    "PostgreSQLBatchTransactionMode",
    "PostgreSQLIdempotencyConflictStrategy",
    "PostgreSQLIdempotencyConflictStrategyDescription",
    "PostgreSQLIdempotencyRequirement",
    "PostgreSQLPartialSuccessPolicy",
    "PostgreSQLPersistenceColumn",
    "PostgreSQLPersistenceOptions",
    "PostgreSQLPersistenceOptionsValidationIssue",
    "PostgreSQLPersistenceOptionsValidationResult",
    "PostgreSQLPersistencePreview",
    "PostgreSQLPersistencePreviewIssue",
    "PostgreSQLPersistencePreviewResult",
    "PostgreSQLPersistencePreviewStatus",
    "PostgreSQLPersistenceRepository",
    "PostgreSQLPersistenceSchema",
    "PostgreSQLStatementExecutionContract",
    "PostgreSQLTransactionBoundary",
    "PostgreSQLTransactionFailurePolicy",
    "PostgreSQLTransactionMode",
    "PostgreSQLTransactionPlan",
    "PostgreSQLTransactionPlanResult",
    "PostgreSQLTransactionOwnership",
    "PostgreSQLTransactionPolicy",
    "PostgreSQLTransactionPolicyDescription",
    "PostgreSQLTransactionPolicyIssue",
    "PostgreSQLTransactionPolicyStatus",
    "build_persistence_input_from_normalization_result",
    "build_default_postgresql_transaction_policy",
    "build_default_postgresql_idempotency_conflict_strategy",
    "build_disabled_postgresql_execution_result",
    "build_psycopg_session_adapter_metadata",
    "build_postgresql_disabled_runtime_execution_result",
    "build_postgresql_conflict_strategy_plan",
    "build_postgresql_execution_plan",
    "build_postgresql_insert_statement",
    "build_postgresql_persistence_preview",
    "build_postgresql_transaction_plan",
    "create_persistence_result",
    "create_postgresql_integration_test_boundary",
    "create_postgresql_persistence_options",
    "describe_postgresql_connection_session_contract",
    "describe_postgresql_disabled_runtime_execution",
    "describe_postgresql_execution_adapter_boundary",
    "describe_postgresql_idempotency_conflict_strategy_boundary",
    "describe_postgresql_transaction_policy_boundary",
    "get_normalized_record_postgresql_schema",
    "render_postgresql_ddl_preview",
    "should_skip_postgresql_integration_tests",
    "validate_psycopg_session_adapter_boundary",
    "validate_postgresql_persistence_options",
)

EXPECTED_PUBLIC_EXPORTS = {
    "PersistenceInput": input.PersistenceInput,
    "PersistenceInputBuildResult": input.PersistenceInputBuildResult,
    "PersistenceInputBuildStatus": input.PersistenceInputBuildStatus,
    "PersistenceInputIssue": input.PersistenceInputIssue,
    "PersistenceInputRecord": input.PersistenceInputRecord,
    "POSTGRESQL_INTEGRATION_TEST_MARKER": (
        integration_test_boundary.POSTGRESQL_INTEGRATION_TEST_MARKER
    ),
    "POSTGRESQL_INTEGRATION_TEST_SKIP_REASON": (
        integration_test_boundary.POSTGRESQL_INTEGRATION_TEST_SKIP_REASON
    ),
    "PersistenceIssue": repository.PersistenceIssue,
    "PersistenceIssueSeverity": repository.PersistenceIssueSeverity,
    "PersistenceRepository": repository.PersistenceRepository,
    "PersistenceResult": repository.PersistenceResult,
    "PersistenceResultStatus": repository.PersistenceResultStatus,
    "PsycopgPostgreSQLSessionAdapter": (
        postgresql_psycopg_session_adapter.PsycopgPostgreSQLSessionAdapter
    ),
    "PsycopgPostgreSQLSessionAdapterBoundaryResult": (
        postgresql_psycopg_session_adapter
        .PsycopgPostgreSQLSessionAdapterBoundaryResult
    ),
    "PsycopgPostgreSQLSessionAdapterMetadata": (
        postgresql_psycopg_session_adapter
        .PsycopgPostgreSQLSessionAdapterMetadata
    ),
    "PsycopgPostgreSQLSessionAdapterStatus": (
        postgresql_psycopg_session_adapter
        .PsycopgPostgreSQLSessionAdapterStatus
    ),
    "PostgreSQLIntegrationTestBoundary": (
        integration_test_boundary.PostgreSQLIntegrationTestBoundary
    ),
    "PostgreSQLInsertBuildIssue": (
        postgresql_insert_builder.PostgreSQLInsertBuildIssue
    ),
    "PostgreSQLInsertBuildResult": (
        postgresql_insert_builder.PostgreSQLInsertBuildResult
    ),
    "PostgreSQLInsertBuildStatus": (
        postgresql_insert_builder.PostgreSQLInsertBuildStatus
    ),
    "PostgreSQLInsertStatement": (
        postgresql_insert_builder.PostgreSQLInsertStatement
    ),
    "PostgreSQLConflictAction": (
        postgresql_idempotency_conflict_strategy.PostgreSQLConflictAction
    ),
    "PostgreSQLConflictStrategyIssue": (
        postgresql_idempotency_conflict_strategy.PostgreSQLConflictStrategyIssue
    ),
    "PostgreSQLConflictStrategyPlan": (
        postgresql_idempotency_conflict_strategy.PostgreSQLConflictStrategyPlan
    ),
    "PostgreSQLConflictStrategyPlanResult": (
        postgresql_idempotency_conflict_strategy
        .PostgreSQLConflictStrategyPlanResult
    ),
    "PostgreSQLConflictStrategyStatus": (
        postgresql_idempotency_conflict_strategy
        .PostgreSQLConflictStrategyStatus
    ),
    "PostgreSQLConnectionSession": (
        postgresql_connection_session_contract.PostgreSQLConnectionSession
    ),
    "PostgreSQLConnectionSessionContractDescription": (
        postgresql_connection_session_contract
        .PostgreSQLConnectionSessionContractDescription
    ),
    "PostgreSQLDisabledRuntimeExecutionAdapter": (
        postgresql_disabled_runtime_execution_adapter
        .PostgreSQLDisabledRuntimeExecutionAdapter
    ),
    "PostgreSQLDisabledRuntimeExecutionDescription": (
        postgresql_disabled_runtime_execution_adapter
        .PostgreSQLDisabledRuntimeExecutionDescription
    ),
    "PostgreSQLDisabledRuntimeExecutionMetadata": (
        postgresql_disabled_runtime_execution_adapter
        .PostgreSQLDisabledRuntimeExecutionMetadata
    ),
    "PostgreSQLDisabledRuntimeExecutionResult": (
        postgresql_disabled_runtime_execution_adapter
        .PostgreSQLDisabledRuntimeExecutionResult
    ),
    "PostgreSQLDisabledRuntimeExecutionStatus": (
        postgresql_disabled_runtime_execution_adapter
        .PostgreSQLDisabledRuntimeExecutionStatus
    ),
    "PostgreSQLExecutionAdapterProtocol": (
        postgresql_execution_adapter_boundary.PostgreSQLExecutionAdapterProtocol
    ),
    "PostgreSQLExecutionBoundaryDescription": (
        postgresql_execution_adapter_boundary
        .PostgreSQLExecutionBoundaryDescription
    ),
    "PostgreSQLExecutionIssue": (
        postgresql_execution_adapter_boundary.PostgreSQLExecutionIssue
    ),
    "PostgreSQLExecutionPlan": (
        postgresql_execution_adapter_boundary.PostgreSQLExecutionPlan
    ),
    "PostgreSQLExecutionPlanResult": (
        postgresql_execution_adapter_boundary.PostgreSQLExecutionPlanResult
    ),
    "PostgreSQLExecutionResult": (
        postgresql_execution_adapter_boundary.PostgreSQLExecutionResult
    ),
    "PostgreSQLExecutionStatus": (
        postgresql_execution_adapter_boundary.PostgreSQLExecutionStatus
    ),
    "PostgreSQLBatchTransactionMode": (
        postgresql_transaction_policy.PostgreSQLBatchTransactionMode
    ),
    "PostgreSQLIdempotencyConflictStrategy": (
        postgresql_idempotency_conflict_strategy
        .PostgreSQLIdempotencyConflictStrategy
    ),
    "PostgreSQLIdempotencyConflictStrategyDescription": (
        postgresql_idempotency_conflict_strategy
        .PostgreSQLIdempotencyConflictStrategyDescription
    ),
    "PostgreSQLIdempotencyRequirement": (
        postgresql_idempotency_conflict_strategy
        .PostgreSQLIdempotencyRequirement
    ),
    "PostgreSQLPartialSuccessPolicy": (
        postgresql_transaction_policy.PostgreSQLPartialSuccessPolicy
    ),
    "PostgreSQLPersistenceColumn": schema.PostgreSQLPersistenceColumn,
    "PostgreSQLPersistenceOptions": (
        postgresql_options.PostgreSQLPersistenceOptions
    ),
    "PostgreSQLPersistenceOptionsValidationIssue": (
        postgresql_options.PostgreSQLPersistenceOptionsValidationIssue
    ),
    "PostgreSQLPersistenceOptionsValidationResult": (
        postgresql_options.PostgreSQLPersistenceOptionsValidationResult
    ),
    "PostgreSQLPersistencePreview": (
        postgresql_persistence_preview.PostgreSQLPersistencePreview
    ),
    "PostgreSQLPersistencePreviewIssue": (
        postgresql_persistence_preview.PostgreSQLPersistencePreviewIssue
    ),
    "PostgreSQLPersistencePreviewResult": (
        postgresql_persistence_preview.PostgreSQLPersistencePreviewResult
    ),
    "PostgreSQLPersistencePreviewStatus": (
        postgresql_persistence_preview.PostgreSQLPersistencePreviewStatus
    ),
    "PostgreSQLPersistenceRepository": (
        postgresql_repository.PostgreSQLPersistenceRepository
    ),
    "PostgreSQLPersistenceSchema": schema.PostgreSQLPersistenceSchema,
    "PostgreSQLStatementExecutionContract": (
        postgresql_connection_session_contract.PostgreSQLStatementExecutionContract
    ),
    "PostgreSQLTransactionBoundary": (
        postgresql_connection_session_contract.PostgreSQLTransactionBoundary
    ),
    "PostgreSQLTransactionFailurePolicy": (
        postgresql_transaction_policy.PostgreSQLTransactionFailurePolicy
    ),
    "PostgreSQLTransactionMode": (
        postgresql_connection_session_contract.PostgreSQLTransactionMode
    ),
    "PostgreSQLTransactionPlan": (
        postgresql_transaction_policy.PostgreSQLTransactionPlan
    ),
    "PostgreSQLTransactionPlanResult": (
        postgresql_transaction_policy.PostgreSQLTransactionPlanResult
    ),
    "PostgreSQLTransactionOwnership": (
        postgresql_connection_session_contract.PostgreSQLTransactionOwnership
    ),
    "PostgreSQLTransactionPolicy": (
        postgresql_transaction_policy.PostgreSQLTransactionPolicy
    ),
    "PostgreSQLTransactionPolicyDescription": (
        postgresql_transaction_policy.PostgreSQLTransactionPolicyDescription
    ),
    "PostgreSQLTransactionPolicyIssue": (
        postgresql_transaction_policy.PostgreSQLTransactionPolicyIssue
    ),
    "PostgreSQLTransactionPolicyStatus": (
        postgresql_transaction_policy.PostgreSQLTransactionPolicyStatus
    ),
    "build_persistence_input_from_normalization_result": (
        input.build_persistence_input_from_normalization_result
    ),
    "build_default_postgresql_transaction_policy": (
        postgresql_transaction_policy.build_default_postgresql_transaction_policy
    ),
    "build_default_postgresql_idempotency_conflict_strategy": (
        postgresql_idempotency_conflict_strategy
        .build_default_postgresql_idempotency_conflict_strategy
    ),
    "build_disabled_postgresql_execution_result": (
        postgresql_execution_adapter_boundary
        .build_disabled_postgresql_execution_result
    ),
    "build_psycopg_session_adapter_metadata": (
        postgresql_psycopg_session_adapter
        .build_psycopg_session_adapter_metadata
    ),
    "build_postgresql_disabled_runtime_execution_result": (
        postgresql_disabled_runtime_execution_adapter
        .build_postgresql_disabled_runtime_execution_result
    ),
    "build_postgresql_conflict_strategy_plan": (
        postgresql_idempotency_conflict_strategy
        .build_postgresql_conflict_strategy_plan
    ),
    "build_postgresql_execution_plan": (
        postgresql_execution_adapter_boundary.build_postgresql_execution_plan
    ),
    "build_postgresql_insert_statement": (
        postgresql_insert_builder.build_postgresql_insert_statement
    ),
    "build_postgresql_persistence_preview": (
        postgresql_persistence_preview.build_postgresql_persistence_preview
    ),
    "build_postgresql_transaction_plan": (
        postgresql_transaction_policy.build_postgresql_transaction_plan
    ),
    "create_persistence_result": repository.create_persistence_result,
    "create_postgresql_integration_test_boundary": (
        integration_test_boundary.create_postgresql_integration_test_boundary
    ),
    "create_postgresql_persistence_options": (
        postgresql_options.create_postgresql_persistence_options
    ),
    "describe_postgresql_connection_session_contract": (
        postgresql_connection_session_contract
        .describe_postgresql_connection_session_contract
    ),
    "describe_postgresql_disabled_runtime_execution": (
        postgresql_disabled_runtime_execution_adapter
        .describe_postgresql_disabled_runtime_execution
    ),
    "describe_postgresql_execution_adapter_boundary": (
        postgresql_execution_adapter_boundary
        .describe_postgresql_execution_adapter_boundary
    ),
    "describe_postgresql_idempotency_conflict_strategy_boundary": (
        postgresql_idempotency_conflict_strategy
        .describe_postgresql_idempotency_conflict_strategy_boundary
    ),
    "describe_postgresql_transaction_policy_boundary": (
        postgresql_transaction_policy
        .describe_postgresql_transaction_policy_boundary
    ),
    "get_normalized_record_postgresql_schema": (
        schema.get_normalized_record_postgresql_schema
    ),
    "render_postgresql_ddl_preview": ddl_preview.render_postgresql_ddl_preview,
    "should_skip_postgresql_integration_tests": (
        integration_test_boundary.should_skip_postgresql_integration_tests
    ),
    "validate_psycopg_session_adapter_boundary": (
        postgresql_psycopg_session_adapter
        .validate_psycopg_session_adapter_boundary
    ),
    "validate_postgresql_persistence_options": (
        postgresql_options.validate_postgresql_persistence_options
    ),
}


def test_expected_persistence_public_symbols_import_from_package() -> None:
    imported_symbols = {
        "PersistenceInput": PersistenceInput,
        "PersistenceInputBuildResult": PersistenceInputBuildResult,
        "PersistenceInputBuildStatus": PersistenceInputBuildStatus,
        "PersistenceInputIssue": PersistenceInputIssue,
        "PersistenceInputRecord": PersistenceInputRecord,
        "POSTGRESQL_INTEGRATION_TEST_MARKER": POSTGRESQL_INTEGRATION_TEST_MARKER,
        "POSTGRESQL_INTEGRATION_TEST_SKIP_REASON": (
            POSTGRESQL_INTEGRATION_TEST_SKIP_REASON
        ),
        "PersistenceIssue": PersistenceIssue,
        "PersistenceIssueSeverity": PersistenceIssueSeverity,
        "PersistenceRepository": PersistenceRepository,
        "PersistenceResult": PersistenceResult,
        "PersistenceResultStatus": PersistenceResultStatus,
        "PsycopgPostgreSQLSessionAdapter": PsycopgPostgreSQLSessionAdapter,
        "PsycopgPostgreSQLSessionAdapterBoundaryResult": (
            PsycopgPostgreSQLSessionAdapterBoundaryResult
        ),
        "PsycopgPostgreSQLSessionAdapterMetadata": (
            PsycopgPostgreSQLSessionAdapterMetadata
        ),
        "PsycopgPostgreSQLSessionAdapterStatus": (
            PsycopgPostgreSQLSessionAdapterStatus
        ),
        "PostgreSQLIntegrationTestBoundary": PostgreSQLIntegrationTestBoundary,
        "PostgreSQLInsertBuildIssue": PostgreSQLInsertBuildIssue,
        "PostgreSQLInsertBuildResult": PostgreSQLInsertBuildResult,
        "PostgreSQLInsertBuildStatus": PostgreSQLInsertBuildStatus,
        "PostgreSQLInsertStatement": PostgreSQLInsertStatement,
        "PostgreSQLConflictAction": PostgreSQLConflictAction,
        "PostgreSQLConflictStrategyIssue": PostgreSQLConflictStrategyIssue,
        "PostgreSQLConflictStrategyPlan": PostgreSQLConflictStrategyPlan,
        "PostgreSQLConflictStrategyPlanResult": (
            PostgreSQLConflictStrategyPlanResult
        ),
        "PostgreSQLConflictStrategyStatus": PostgreSQLConflictStrategyStatus,
        "PostgreSQLConnectionSession": PostgreSQLConnectionSession,
        "PostgreSQLConnectionSessionContractDescription": (
            PostgreSQLConnectionSessionContractDescription
        ),
        "PostgreSQLDisabledRuntimeExecutionAdapter": (
            PostgreSQLDisabledRuntimeExecutionAdapter
        ),
        "PostgreSQLDisabledRuntimeExecutionDescription": (
            PostgreSQLDisabledRuntimeExecutionDescription
        ),
        "PostgreSQLDisabledRuntimeExecutionMetadata": (
            PostgreSQLDisabledRuntimeExecutionMetadata
        ),
        "PostgreSQLDisabledRuntimeExecutionResult": (
            PostgreSQLDisabledRuntimeExecutionResult
        ),
        "PostgreSQLDisabledRuntimeExecutionStatus": (
            PostgreSQLDisabledRuntimeExecutionStatus
        ),
        "PostgreSQLExecutionAdapterProtocol": PostgreSQLExecutionAdapterProtocol,
        "PostgreSQLExecutionBoundaryDescription": (
            PostgreSQLExecutionBoundaryDescription
        ),
        "PostgreSQLExecutionIssue": PostgreSQLExecutionIssue,
        "PostgreSQLExecutionPlan": PostgreSQLExecutionPlan,
        "PostgreSQLExecutionPlanResult": PostgreSQLExecutionPlanResult,
        "PostgreSQLExecutionResult": PostgreSQLExecutionResult,
        "PostgreSQLExecutionStatus": PostgreSQLExecutionStatus,
        "PostgreSQLBatchTransactionMode": PostgreSQLBatchTransactionMode,
        "PostgreSQLIdempotencyConflictStrategy": (
            PostgreSQLIdempotencyConflictStrategy
        ),
        "PostgreSQLIdempotencyConflictStrategyDescription": (
            PostgreSQLIdempotencyConflictStrategyDescription
        ),
        "PostgreSQLIdempotencyRequirement": (
            PostgreSQLIdempotencyRequirement
        ),
        "PostgreSQLPartialSuccessPolicy": PostgreSQLPartialSuccessPolicy,
        "PostgreSQLPersistenceColumn": PostgreSQLPersistenceColumn,
        "PostgreSQLPersistenceOptions": PostgreSQLPersistenceOptions,
        "PostgreSQLPersistenceOptionsValidationIssue": (
            PostgreSQLPersistenceOptionsValidationIssue
        ),
        "PostgreSQLPersistenceOptionsValidationResult": (
            PostgreSQLPersistenceOptionsValidationResult
        ),
        "PostgreSQLPersistencePreview": PostgreSQLPersistencePreview,
        "PostgreSQLPersistencePreviewIssue": PostgreSQLPersistencePreviewIssue,
        "PostgreSQLPersistencePreviewResult": PostgreSQLPersistencePreviewResult,
        "PostgreSQLPersistencePreviewStatus": PostgreSQLPersistencePreviewStatus,
        "PostgreSQLPersistenceRepository": PostgreSQLPersistenceRepository,
        "PostgreSQLPersistenceSchema": PostgreSQLPersistenceSchema,
        "PostgreSQLStatementExecutionContract": PostgreSQLStatementExecutionContract,
        "PostgreSQLTransactionBoundary": PostgreSQLTransactionBoundary,
        "PostgreSQLTransactionFailurePolicy": (
            PostgreSQLTransactionFailurePolicy
        ),
        "PostgreSQLTransactionMode": PostgreSQLTransactionMode,
        "PostgreSQLTransactionPlan": PostgreSQLTransactionPlan,
        "PostgreSQLTransactionPlanResult": PostgreSQLTransactionPlanResult,
        "PostgreSQLTransactionOwnership": PostgreSQLTransactionOwnership,
        "PostgreSQLTransactionPolicy": PostgreSQLTransactionPolicy,
        "PostgreSQLTransactionPolicyDescription": (
            PostgreSQLTransactionPolicyDescription
        ),
        "PostgreSQLTransactionPolicyIssue": PostgreSQLTransactionPolicyIssue,
        "PostgreSQLTransactionPolicyStatus": PostgreSQLTransactionPolicyStatus,
        "build_persistence_input_from_normalization_result": (
            build_persistence_input_from_normalization_result
        ),
        "build_default_postgresql_transaction_policy": (
            build_default_postgresql_transaction_policy
        ),
        "build_default_postgresql_idempotency_conflict_strategy": (
            build_default_postgresql_idempotency_conflict_strategy
        ),
        "build_disabled_postgresql_execution_result": (
            build_disabled_postgresql_execution_result
        ),
        "build_psycopg_session_adapter_metadata": (
            build_psycopg_session_adapter_metadata
        ),
        "build_postgresql_disabled_runtime_execution_result": (
            build_postgresql_disabled_runtime_execution_result
        ),
        "build_postgresql_conflict_strategy_plan": (
            build_postgresql_conflict_strategy_plan
        ),
        "build_postgresql_execution_plan": build_postgresql_execution_plan,
        "build_postgresql_insert_statement": build_postgresql_insert_statement,
        "build_postgresql_persistence_preview": (
            build_postgresql_persistence_preview
        ),
        "build_postgresql_transaction_plan": build_postgresql_transaction_plan,
        "create_persistence_result": create_persistence_result,
        "create_postgresql_integration_test_boundary": (
            create_postgresql_integration_test_boundary
        ),
        "create_postgresql_persistence_options": (
            create_postgresql_persistence_options
        ),
        "describe_postgresql_connection_session_contract": (
            describe_postgresql_connection_session_contract
        ),
        "describe_postgresql_disabled_runtime_execution": (
            describe_postgresql_disabled_runtime_execution
        ),
        "describe_postgresql_execution_adapter_boundary": (
            describe_postgresql_execution_adapter_boundary
        ),
        "describe_postgresql_idempotency_conflict_strategy_boundary": (
            describe_postgresql_idempotency_conflict_strategy_boundary
        ),
        "describe_postgresql_transaction_policy_boundary": (
            describe_postgresql_transaction_policy_boundary
        ),
        "get_normalized_record_postgresql_schema": (
            get_normalized_record_postgresql_schema
        ),
        "render_postgresql_ddl_preview": render_postgresql_ddl_preview,
        "should_skip_postgresql_integration_tests": (
            should_skip_postgresql_integration_tests
        ),
        "validate_psycopg_session_adapter_boundary": (
            validate_psycopg_session_adapter_boundary
        ),
        "validate_postgresql_persistence_options": (
            validate_postgresql_persistence_options
        ),
    }

    assert tuple(imported_symbols) == EXPECTED_PUBLIC_SYMBOLS
    assert imported_symbols == {
        name: getattr(persistence, name) for name in EXPECTED_PUBLIC_SYMBOLS
    }


def test_persistence_all_lists_expected_public_symbols() -> None:
    assert persistence.__all__ == EXPECTED_PUBLIC_SYMBOLS


def test_persistence_public_exports_match_origin_modules() -> None:
    assert {
        name: getattr(persistence, name) for name in EXPECTED_PUBLIC_SYMBOLS
    } == EXPECTED_PUBLIC_EXPORTS


def test_persistence_all_names_resolve_to_package_attributes() -> None:
    for name in persistence.__all__:
        assert hasattr(persistence, name)


def test_persistence_all_excludes_internal_module_names() -> None:
    assert "input" not in persistence.__all__
    assert "integration_test_boundary" not in persistence.__all__
    assert "postgresql_insert_builder" not in persistence.__all__
    assert "repository" not in persistence.__all__
    assert "schema" not in persistence.__all__
    assert "ddl_preview" not in persistence.__all__
    assert "postgresql_options" not in persistence.__all__
    assert "postgresql_persistence_preview" not in persistence.__all__
    assert "postgresql_psycopg_session_adapter" not in persistence.__all__
    assert "postgresql_disabled_runtime_execution_adapter" not in persistence.__all__
    assert "postgresql_repository" not in persistence.__all__
    assert all(not name.startswith("_") for name in persistence.__all__)
