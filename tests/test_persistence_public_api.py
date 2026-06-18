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
    postgresql_repository_disabled_execution_preview,
    postgresql_runtime_config_gate,
    postgresql_runtime_execution_gate,
    postgresql_schema_bootstrap,
    postgresql_schema_bootstrap_planner,
    postgresql_schema_isolation_strategy,
    postgresql_transaction_policy,
    parsed_factor_persistence_writer,
    repository,
    schema,
    source_document_repository,
    source_family_repository,
)
from carbonfactor_parser.persistence import (
    PersistenceInput,
    PersistenceInputBuildResult,
    PersistenceInputBuildStatus,
    PersistenceInputIssue,
    PersistenceInputRecord,
    POSTGRESQL_ISOLATED_SCHEMA_PREFIX,
    POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR,
    POSTGRESQL_INTEGRATION_TEST_MARKER,
    POSTGRESQL_INTEGRATION_TEST_OPT_IN_FALSE_VALUES,
    POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR,
    POSTGRESQL_INTEGRATION_TEST_OPT_IN_TRUE_VALUES,
    POSTGRESQL_INTEGRATION_TEST_SKIP_REASON,
    POSTGRESQL_RESERVED_SCHEMA_NAMES,
    PersistenceIssue,
    PersistenceIssueSeverity,
    PersistenceRepository,
    PersistenceResult,
    PersistenceResultStatus,
    ParsedFactorPersistenceCommand,
    ParsedFactorPersistenceIssue,
    ParsedFactorPersistenceStatus,
    ParsedFactorPersistenceWriterResult,
    SourceDocumentRepository,
    SourceDocumentRepositoryIssue,
    SourceDocumentRepositoryPersistResult,
    SourceDocumentRepositoryPersistStatus,
    SourceDocumentRepositoryValidationResult,
    SourceFamilyDetailRecord,
    SourceFamilyMasterRecord,
    SourceFamilyRepository,
    SourceFamilyRepositoryIssue,
    SourceFamilyRepositoryPersistResult,
    SourceFamilyRepositoryPersistStatus,
    SourceFamilyRepositoryValidationResult,
    PsycopgPostgreSQLSessionAdapter,
    PsycopgPostgreSQLSessionAdapterBoundaryResult,
    PsycopgPostgreSQLSessionAdapterMetadata,
    PsycopgPostgreSQLSessionAdapterStatus,
    PostgreSQLIntegrationTestBoundary,
    PostgreSQLIntegrationTestConfigIssue,
    PostgreSQLIntegrationTestOptInConfig,
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
    PostgreSQLConnectionSessionContractIssue,
    PostgreSQLConnectionSessionContractStatus,
    PostgreSQLConnectionSessionContractValidationResult,
    PostgreSQLConnectionSessionRuntimeContract,
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
    PostgreSQLRepositoryDisabledExecutionPreviewDescription,
    PostgreSQLRepositoryDisabledExecutionPreviewIssue,
    PostgreSQLRepositoryDisabledExecutionPreviewResult,
    PostgreSQLRepositoryDisabledExecutionPreviewStatus,
    PostgreSQLRepositoryRuntimeSafetyGate,
    PostgreSQLRepositoryRuntimeSafetyGateDecision,
    PostgreSQLRepositoryRuntimeSafetyGateDescription,
    PostgreSQLRepositoryRuntimeSafetyGateIssue,
    PostgreSQLRepositoryRuntimeSafetyGateStatus,
    PostgreSQLRuntimeConfigGate,
    PostgreSQLRuntimeConfigGateDecision,
    PostgreSQLRuntimeConfigGateDescription,
    PostgreSQLRuntimeConfigGateIssue,
    PostgreSQLRuntimeConfigGateStatus,
    PostgreSQLRuntimeExecutionGate,
    PostgreSQLRuntimeExecutionGateDecision,
    PostgreSQLRuntimeExecutionGateDescription,
    PostgreSQLRuntimeExecutionGateIssue,
    PostgreSQLRuntimeExecutionGateStatus,
    PostgreSQLSchemaBootstrapMode,
    PostgreSQLSchemaBootstrapPlan,
    PostgreSQLSchemaBootstrapPlanStatement,
    PostgreSQLSchemaBootstrapReport,
    PostgreSQLSchemaBootstrapRequest,
    PostgreSQLSchemaBootstrapTableResult,
    PostgreSQLSchemaBootstrapTableStatus,
    PostgreSQLSchemaIsolationCleanupMode,
    PostgreSQLSchemaIsolationCleanupScope,
    PostgreSQLSchemaIsolationStrategy,
    PostgreSQLSchemaIsolationStrategyDescription,
    PostgreSQLSchemaIsolationStrategyIssue,
    PostgreSQLSchemaIsolationStrategyStatus,
    PostgreSQLSchemaIsolationStrategyValidationResult,
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
    PostgreSQLTransactionPolicyValidationResult,
    PostgreSQLTransactionRuntimeBoundary,
    build_persistence_input_from_normalization_result,
    build_parsed_factor_persistence_command,
    build_default_postgresql_transaction_policy,
    build_default_postgresql_idempotency_conflict_strategy,
    build_disabled_postgresql_execution_result,
    build_psycopg_session_adapter_metadata,
    build_postgresql_disabled_runtime_execution_result,
    build_postgresql_conflict_strategy_plan,
    build_postgresql_execution_plan,
    build_postgresql_insert_statement,
    build_postgresql_persistence_preview,
    build_postgresql_phase1_schema_bootstrap_plan,
    build_postgresql_phase1_schema_bootstrap_report,
    build_postgresql_phase1_schema_bootstrap_request,
    build_postgresql_repository_disabled_execution_preview,
    build_postgresql_transaction_plan,
    build_default_postgresql_schema_isolation_strategy,
    create_persistence_result,
    create_source_document_repository_persist_result,
    create_source_family_repository_persist_result,
    create_postgresql_connection_session_runtime_contract,
    create_postgresql_integration_test_boundary,
    create_postgresql_persistence_options,
    create_postgresql_transaction_runtime_boundary,
    describe_postgresql_connection_session_contract,
    describe_postgresql_disabled_runtime_execution,
    describe_postgresql_execution_adapter_boundary,
    describe_postgresql_idempotency_conflict_strategy_boundary,
    describe_postgresql_repository_disabled_execution_preview,
    describe_postgresql_repository_runtime_safety_gate,
    describe_postgresql_runtime_config_gate,
    describe_postgresql_runtime_execution_gate,
    describe_postgresql_schema_isolation_strategy,
    describe_postgresql_transaction_policy_boundary,
    evaluate_postgresql_integration_test_opt_in_config,
    evaluate_postgresql_runtime_config_gate,
    evaluate_postgresql_runtime_execution_gate,
    evaluate_postgresql_repository_runtime_safety_gate,
    get_normalized_record_postgresql_schema,
    render_postgresql_ddl_preview,
    should_skip_postgresql_integration_tests,
    source_family_repository_table_names,
    persist_parsed_factor_records,
    validate_source_document_repository_inputs,
    validate_source_family_repository_inputs,
    validate_psycopg_session_adapter_boundary,
    validate_postgresql_connection_session_runtime_contract,
    validate_postgresql_persistence_options,
    validate_postgresql_schema_isolation_strategy,
    validate_postgresql_statement_execution_contract,
    validate_postgresql_transaction_policy,
    validate_postgresql_transaction_runtime_boundary,
)


EXPECTED_PUBLIC_SYMBOLS = (
    "PersistenceInput",
    "PersistenceInputBuildResult",
    "PersistenceInputBuildStatus",
    "PersistenceInputIssue",
    "PersistenceInputRecord",
    "POSTGRESQL_ISOLATED_SCHEMA_PREFIX",
    "POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR",
    "POSTGRESQL_INTEGRATION_TEST_MARKER",
    "POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR",
    "POSTGRESQL_INTEGRATION_TEST_OPT_IN_FALSE_VALUES",
    "POSTGRESQL_INTEGRATION_TEST_OPT_IN_TRUE_VALUES",
    "POSTGRESQL_INTEGRATION_TEST_SKIP_REASON",
    "POSTGRESQL_RESERVED_SCHEMA_NAMES",
    "PersistenceIssue",
    "PersistenceIssueSeverity",
    "PersistenceRepository",
    "PersistenceResult",
    "PersistenceResultStatus",
    "ParsedFactorPersistenceCommand",
    "ParsedFactorPersistenceIssue",
    "ParsedFactorPersistenceStatus",
    "ParsedFactorPersistenceWriterResult",
    "SourceDocumentRepository",
    "SourceDocumentRepositoryIssue",
    "SourceDocumentRepositoryPersistResult",
    "SourceDocumentRepositoryPersistStatus",
    "SourceDocumentRepositoryValidationResult",
    "SourceFamilyDetailRecord",
    "SourceFamilyMasterRecord",
    "SourceFamilyRepository",
    "SourceFamilyRepositoryIssue",
    "SourceFamilyRepositoryPersistResult",
    "SourceFamilyRepositoryPersistStatus",
    "SourceFamilyRepositoryValidationResult",
    "PsycopgPostgreSQLSessionAdapter",
    "PsycopgPostgreSQLSessionAdapterBoundaryResult",
    "PsycopgPostgreSQLSessionAdapterMetadata",
    "PsycopgPostgreSQLSessionAdapterStatus",
    "PostgreSQLIntegrationTestBoundary",
    "PostgreSQLIntegrationTestConfigIssue",
    "PostgreSQLIntegrationTestOptInConfig",
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
    "PostgreSQLConnectionSessionContractIssue",
    "PostgreSQLConnectionSessionContractStatus",
    "PostgreSQLConnectionSessionContractValidationResult",
    "PostgreSQLConnectionSessionRuntimeContract",
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
    "PostgreSQLRepositoryDisabledExecutionPreviewDescription",
    "PostgreSQLRepositoryDisabledExecutionPreviewIssue",
    "PostgreSQLRepositoryDisabledExecutionPreviewResult",
    "PostgreSQLRepositoryDisabledExecutionPreviewStatus",
    "PostgreSQLRepositoryRuntimeSafetyGate",
    "PostgreSQLRepositoryRuntimeSafetyGateDecision",
    "PostgreSQLRepositoryRuntimeSafetyGateDescription",
    "PostgreSQLRepositoryRuntimeSafetyGateIssue",
    "PostgreSQLRepositoryRuntimeSafetyGateStatus",
    "PostgreSQLRuntimeConfigGate",
    "PostgreSQLRuntimeConfigGateDecision",
    "PostgreSQLRuntimeConfigGateDescription",
    "PostgreSQLRuntimeConfigGateIssue",
    "PostgreSQLRuntimeConfigGateStatus",
    "PostgreSQLRuntimeExecutionGate",
    "PostgreSQLRuntimeExecutionGateDecision",
    "PostgreSQLRuntimeExecutionGateDescription",
    "PostgreSQLRuntimeExecutionGateIssue",
    "PostgreSQLRuntimeExecutionGateStatus",
    "PostgreSQLSchemaBootstrapMode",
    "PostgreSQLSchemaBootstrapPlan",
    "PostgreSQLSchemaBootstrapPlanStatement",
    "PostgreSQLSchemaBootstrapReport",
    "PostgreSQLSchemaBootstrapRequest",
    "PostgreSQLSchemaBootstrapTableResult",
    "PostgreSQLSchemaBootstrapTableStatus",
    "PostgreSQLSchemaIsolationCleanupMode",
    "PostgreSQLSchemaIsolationCleanupScope",
    "PostgreSQLSchemaIsolationStrategy",
    "PostgreSQLSchemaIsolationStrategyDescription",
    "PostgreSQLSchemaIsolationStrategyIssue",
    "PostgreSQLSchemaIsolationStrategyStatus",
    "PostgreSQLSchemaIsolationStrategyValidationResult",
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
    "PostgreSQLTransactionPolicyValidationResult",
    "PostgreSQLTransactionRuntimeBoundary",
    "build_persistence_input_from_normalization_result",
    "build_parsed_factor_persistence_command",
    "build_default_postgresql_transaction_policy",
    "build_default_postgresql_idempotency_conflict_strategy",
    "build_disabled_postgresql_execution_result",
    "build_psycopg_session_adapter_metadata",
    "build_postgresql_disabled_runtime_execution_result",
    "build_postgresql_conflict_strategy_plan",
    "build_postgresql_execution_plan",
    "build_postgresql_insert_statement",
    "build_postgresql_persistence_preview",
    "build_postgresql_phase1_schema_bootstrap_plan",
    "build_postgresql_phase1_schema_bootstrap_report",
    "build_postgresql_phase1_schema_bootstrap_request",
    "build_postgresql_repository_disabled_execution_preview",
    "build_postgresql_transaction_plan",
    "build_default_postgresql_schema_isolation_strategy",
    "create_persistence_result",
    "create_source_document_repository_persist_result",
    "create_source_family_repository_persist_result",
    "create_postgresql_connection_session_runtime_contract",
    "create_postgresql_integration_test_boundary",
    "create_postgresql_persistence_options",
    "create_postgresql_transaction_runtime_boundary",
    "describe_postgresql_connection_session_contract",
    "describe_postgresql_disabled_runtime_execution",
    "describe_postgresql_execution_adapter_boundary",
    "describe_postgresql_idempotency_conflict_strategy_boundary",
    "describe_postgresql_repository_disabled_execution_preview",
    "describe_postgresql_repository_runtime_safety_gate",
    "describe_postgresql_runtime_config_gate",
    "describe_postgresql_runtime_execution_gate",
    "describe_postgresql_schema_isolation_strategy",
    "describe_postgresql_transaction_policy_boundary",
    "evaluate_postgresql_runtime_config_gate",
    "evaluate_postgresql_runtime_execution_gate",
    "evaluate_postgresql_repository_runtime_safety_gate",
    "evaluate_postgresql_integration_test_opt_in_config",
    "get_normalized_record_postgresql_schema",
    "render_postgresql_ddl_preview",
    "persist_parsed_factor_records",
    "should_skip_postgresql_integration_tests",
    "source_family_repository_table_names",
    "validate_source_document_repository_inputs",
    "validate_source_family_repository_inputs",
    "validate_psycopg_session_adapter_boundary",
    "validate_postgresql_connection_session_runtime_contract",
    "validate_postgresql_persistence_options",
    "validate_postgresql_schema_isolation_strategy",
    "validate_postgresql_statement_execution_contract",
    "validate_postgresql_transaction_policy",
    "validate_postgresql_transaction_runtime_boundary",
)

EXPECTED_PUBLIC_EXPORTS = {
    "PersistenceInput": input.PersistenceInput,
    "PersistenceInputBuildResult": input.PersistenceInputBuildResult,
    "PersistenceInputBuildStatus": input.PersistenceInputBuildStatus,
    "PersistenceInputIssue": input.PersistenceInputIssue,
    "PersistenceInputRecord": input.PersistenceInputRecord,
    "POSTGRESQL_ISOLATED_SCHEMA_PREFIX": (
        postgresql_schema_isolation_strategy.POSTGRESQL_ISOLATED_SCHEMA_PREFIX
    ),
    "POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR": (
        integration_test_boundary.POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR
    ),
    "POSTGRESQL_INTEGRATION_TEST_MARKER": (
        integration_test_boundary.POSTGRESQL_INTEGRATION_TEST_MARKER
    ),
    "POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR": (
        integration_test_boundary.POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR
    ),
    "POSTGRESQL_INTEGRATION_TEST_OPT_IN_FALSE_VALUES": (
        integration_test_boundary.POSTGRESQL_INTEGRATION_TEST_OPT_IN_FALSE_VALUES
    ),
    "POSTGRESQL_INTEGRATION_TEST_OPT_IN_TRUE_VALUES": (
        integration_test_boundary.POSTGRESQL_INTEGRATION_TEST_OPT_IN_TRUE_VALUES
    ),
    "POSTGRESQL_INTEGRATION_TEST_SKIP_REASON": (
        integration_test_boundary.POSTGRESQL_INTEGRATION_TEST_SKIP_REASON
    ),
    "POSTGRESQL_RESERVED_SCHEMA_NAMES": (
        postgresql_schema_isolation_strategy.POSTGRESQL_RESERVED_SCHEMA_NAMES
    ),
    "PersistenceIssue": repository.PersistenceIssue,
    "PersistenceIssueSeverity": repository.PersistenceIssueSeverity,
    "PersistenceRepository": repository.PersistenceRepository,
    "PersistenceResult": repository.PersistenceResult,
    "PersistenceResultStatus": repository.PersistenceResultStatus,
    "ParsedFactorPersistenceCommand": (
        parsed_factor_persistence_writer.ParsedFactorPersistenceCommand
    ),
    "ParsedFactorPersistenceIssue": (
        parsed_factor_persistence_writer.ParsedFactorPersistenceIssue
    ),
    "ParsedFactorPersistenceStatus": (
        parsed_factor_persistence_writer.ParsedFactorPersistenceStatus
    ),
    "ParsedFactorPersistenceWriterResult": (
        parsed_factor_persistence_writer.ParsedFactorPersistenceWriterResult
    ),
    "SourceDocumentRepository": source_document_repository.SourceDocumentRepository,
    "SourceDocumentRepositoryIssue": (
        source_document_repository.SourceDocumentRepositoryIssue
    ),
    "SourceDocumentRepositoryPersistResult": (
        source_document_repository.SourceDocumentRepositoryPersistResult
    ),
    "SourceDocumentRepositoryPersistStatus": (
        source_document_repository.SourceDocumentRepositoryPersistStatus
    ),
    "SourceDocumentRepositoryValidationResult": (
        source_document_repository.SourceDocumentRepositoryValidationResult
    ),
    "SourceFamilyDetailRecord": source_family_repository.SourceFamilyDetailRecord,
    "SourceFamilyMasterRecord": source_family_repository.SourceFamilyMasterRecord,
    "SourceFamilyRepository": source_family_repository.SourceFamilyRepository,
    "SourceFamilyRepositoryIssue": (
        source_family_repository.SourceFamilyRepositoryIssue
    ),
    "SourceFamilyRepositoryPersistResult": (
        source_family_repository.SourceFamilyRepositoryPersistResult
    ),
    "SourceFamilyRepositoryPersistStatus": (
        source_family_repository.SourceFamilyRepositoryPersistStatus
    ),
    "SourceFamilyRepositoryValidationResult": (
        source_family_repository.SourceFamilyRepositoryValidationResult
    ),
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
    "PostgreSQLIntegrationTestConfigIssue": (
        integration_test_boundary.PostgreSQLIntegrationTestConfigIssue
    ),
    "PostgreSQLIntegrationTestOptInConfig": (
        integration_test_boundary.PostgreSQLIntegrationTestOptInConfig
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
    "PostgreSQLConnectionSessionContractIssue": (
        postgresql_connection_session_contract
        .PostgreSQLConnectionSessionContractIssue
    ),
    "PostgreSQLConnectionSessionContractStatus": (
        postgresql_connection_session_contract
        .PostgreSQLConnectionSessionContractStatus
    ),
    "PostgreSQLConnectionSessionContractValidationResult": (
        postgresql_connection_session_contract
        .PostgreSQLConnectionSessionContractValidationResult
    ),
    "PostgreSQLConnectionSessionRuntimeContract": (
        postgresql_connection_session_contract
        .PostgreSQLConnectionSessionRuntimeContract
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
    "PostgreSQLRepositoryDisabledExecutionPreviewDescription": (
        postgresql_repository_disabled_execution_preview
        .PostgreSQLRepositoryDisabledExecutionPreviewDescription
    ),
    "PostgreSQLRepositoryDisabledExecutionPreviewIssue": (
        postgresql_repository_disabled_execution_preview
        .PostgreSQLRepositoryDisabledExecutionPreviewIssue
    ),
    "PostgreSQLRepositoryDisabledExecutionPreviewResult": (
        postgresql_repository_disabled_execution_preview
        .PostgreSQLRepositoryDisabledExecutionPreviewResult
    ),
    "PostgreSQLRepositoryDisabledExecutionPreviewStatus": (
        postgresql_repository_disabled_execution_preview
        .PostgreSQLRepositoryDisabledExecutionPreviewStatus
    ),
    "PostgreSQLRepositoryRuntimeSafetyGate": (
        postgresql_repository.PostgreSQLRepositoryRuntimeSafetyGate
    ),
    "PostgreSQLRepositoryRuntimeSafetyGateDecision": (
        postgresql_repository.PostgreSQLRepositoryRuntimeSafetyGateDecision
    ),
    "PostgreSQLRepositoryRuntimeSafetyGateDescription": (
        postgresql_repository.PostgreSQLRepositoryRuntimeSafetyGateDescription
    ),
    "PostgreSQLRepositoryRuntimeSafetyGateIssue": (
        postgresql_repository.PostgreSQLRepositoryRuntimeSafetyGateIssue
    ),
    "PostgreSQLRepositoryRuntimeSafetyGateStatus": (
        postgresql_repository.PostgreSQLRepositoryRuntimeSafetyGateStatus
    ),
    "PostgreSQLRuntimeConfigGate": (
        postgresql_runtime_config_gate.PostgreSQLRuntimeConfigGate
    ),
    "PostgreSQLRuntimeConfigGateDecision": (
        postgresql_runtime_config_gate.PostgreSQLRuntimeConfigGateDecision
    ),
    "PostgreSQLRuntimeConfigGateDescription": (
        postgresql_runtime_config_gate.PostgreSQLRuntimeConfigGateDescription
    ),
    "PostgreSQLRuntimeConfigGateIssue": (
        postgresql_runtime_config_gate.PostgreSQLRuntimeConfigGateIssue
    ),
    "PostgreSQLRuntimeConfigGateStatus": (
        postgresql_runtime_config_gate.PostgreSQLRuntimeConfigGateStatus
    ),
    "PostgreSQLRuntimeExecutionGate": (
        postgresql_runtime_execution_gate.PostgreSQLRuntimeExecutionGate
    ),
    "PostgreSQLRuntimeExecutionGateDecision": (
        postgresql_runtime_execution_gate
        .PostgreSQLRuntimeExecutionGateDecision
    ),
    "PostgreSQLRuntimeExecutionGateDescription": (
        postgresql_runtime_execution_gate
        .PostgreSQLRuntimeExecutionGateDescription
    ),
    "PostgreSQLRuntimeExecutionGateIssue": (
        postgresql_runtime_execution_gate.PostgreSQLRuntimeExecutionGateIssue
    ),
    "PostgreSQLRuntimeExecutionGateStatus": (
        postgresql_runtime_execution_gate.PostgreSQLRuntimeExecutionGateStatus
    ),
    "PostgreSQLSchemaBootstrapMode": (
        postgresql_schema_bootstrap.PostgreSQLSchemaBootstrapMode
    ),
    "PostgreSQLSchemaBootstrapPlan": (
        postgresql_schema_bootstrap_planner.PostgreSQLSchemaBootstrapPlan
    ),
    "PostgreSQLSchemaBootstrapPlanStatement": (
        postgresql_schema_bootstrap_planner
        .PostgreSQLSchemaBootstrapPlanStatement
    ),
    "PostgreSQLSchemaBootstrapReport": (
        postgresql_schema_bootstrap.PostgreSQLSchemaBootstrapReport
    ),
    "PostgreSQLSchemaBootstrapRequest": (
        postgresql_schema_bootstrap.PostgreSQLSchemaBootstrapRequest
    ),
    "PostgreSQLSchemaBootstrapTableResult": (
        postgresql_schema_bootstrap.PostgreSQLSchemaBootstrapTableResult
    ),
    "PostgreSQLSchemaBootstrapTableStatus": (
        postgresql_schema_bootstrap.PostgreSQLSchemaBootstrapTableStatus
    ),
    "PostgreSQLSchemaIsolationCleanupMode": (
        postgresql_schema_isolation_strategy.PostgreSQLSchemaIsolationCleanupMode
    ),
    "PostgreSQLSchemaIsolationCleanupScope": (
        postgresql_schema_isolation_strategy.PostgreSQLSchemaIsolationCleanupScope
    ),
    "PostgreSQLSchemaIsolationStrategy": (
        postgresql_schema_isolation_strategy.PostgreSQLSchemaIsolationStrategy
    ),
    "PostgreSQLSchemaIsolationStrategyDescription": (
        postgresql_schema_isolation_strategy
        .PostgreSQLSchemaIsolationStrategyDescription
    ),
    "PostgreSQLSchemaIsolationStrategyIssue": (
        postgresql_schema_isolation_strategy.PostgreSQLSchemaIsolationStrategyIssue
    ),
    "PostgreSQLSchemaIsolationStrategyStatus": (
        postgresql_schema_isolation_strategy.PostgreSQLSchemaIsolationStrategyStatus
    ),
    "PostgreSQLSchemaIsolationStrategyValidationResult": (
        postgresql_schema_isolation_strategy
        .PostgreSQLSchemaIsolationStrategyValidationResult
    ),
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
    "PostgreSQLTransactionPolicyValidationResult": (
        postgresql_transaction_policy.PostgreSQLTransactionPolicyValidationResult
    ),
    "PostgreSQLTransactionRuntimeBoundary": (
        postgresql_transaction_policy.PostgreSQLTransactionRuntimeBoundary
    ),
    "build_persistence_input_from_normalization_result": (
        input.build_persistence_input_from_normalization_result
    ),
    "build_parsed_factor_persistence_command": (
        parsed_factor_persistence_writer.build_parsed_factor_persistence_command
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
    "build_postgresql_phase1_schema_bootstrap_plan": (
        postgresql_schema_bootstrap_planner
        .build_postgresql_phase1_schema_bootstrap_plan
    ),
    "build_postgresql_phase1_schema_bootstrap_report": (
        postgresql_schema_bootstrap
        .build_postgresql_phase1_schema_bootstrap_report
    ),
    "build_postgresql_phase1_schema_bootstrap_request": (
        postgresql_schema_bootstrap
        .build_postgresql_phase1_schema_bootstrap_request
    ),
    "build_postgresql_repository_disabled_execution_preview": (
        postgresql_repository_disabled_execution_preview
        .build_postgresql_repository_disabled_execution_preview
    ),
    "build_postgresql_transaction_plan": (
        postgresql_transaction_policy.build_postgresql_transaction_plan
    ),
    "build_default_postgresql_schema_isolation_strategy": (
        postgresql_schema_isolation_strategy
        .build_default_postgresql_schema_isolation_strategy
    ),
    "create_persistence_result": repository.create_persistence_result,
    "create_source_document_repository_persist_result": (
        source_document_repository.create_source_document_repository_persist_result
    ),
    "create_source_family_repository_persist_result": (
        source_family_repository.create_source_family_repository_persist_result
    ),
    "create_postgresql_connection_session_runtime_contract": (
        postgresql_connection_session_contract
        .create_postgresql_connection_session_runtime_contract
    ),
    "create_postgresql_integration_test_boundary": (
        integration_test_boundary.create_postgresql_integration_test_boundary
    ),
    "create_postgresql_persistence_options": (
        postgresql_options.create_postgresql_persistence_options
    ),
    "create_postgresql_transaction_runtime_boundary": (
        postgresql_transaction_policy
        .create_postgresql_transaction_runtime_boundary
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
    "describe_postgresql_repository_disabled_execution_preview": (
        postgresql_repository_disabled_execution_preview
        .describe_postgresql_repository_disabled_execution_preview
    ),
    "describe_postgresql_repository_runtime_safety_gate": (
        postgresql_repository.describe_postgresql_repository_runtime_safety_gate
    ),
    "describe_postgresql_runtime_config_gate": (
        postgresql_runtime_config_gate
        .describe_postgresql_runtime_config_gate
    ),
    "describe_postgresql_runtime_execution_gate": (
        postgresql_runtime_execution_gate
        .describe_postgresql_runtime_execution_gate
    ),
    "describe_postgresql_schema_isolation_strategy": (
        postgresql_schema_isolation_strategy
        .describe_postgresql_schema_isolation_strategy
    ),
    "describe_postgresql_transaction_policy_boundary": (
        postgresql_transaction_policy
        .describe_postgresql_transaction_policy_boundary
    ),
    "evaluate_postgresql_integration_test_opt_in_config": (
        integration_test_boundary.evaluate_postgresql_integration_test_opt_in_config
    ),
    "evaluate_postgresql_runtime_config_gate": (
        postgresql_runtime_config_gate
        .evaluate_postgresql_runtime_config_gate
    ),
    "evaluate_postgresql_runtime_execution_gate": (
        postgresql_runtime_execution_gate
        .evaluate_postgresql_runtime_execution_gate
    ),
    "evaluate_postgresql_repository_runtime_safety_gate": (
        postgresql_repository.evaluate_postgresql_repository_runtime_safety_gate
    ),
    "get_normalized_record_postgresql_schema": (
        schema.get_normalized_record_postgresql_schema
    ),
    "render_postgresql_ddl_preview": ddl_preview.render_postgresql_ddl_preview,
    "should_skip_postgresql_integration_tests": (
        integration_test_boundary.should_skip_postgresql_integration_tests
    ),
    "source_family_repository_table_names": (
        source_family_repository.source_family_repository_table_names
    ),
    "persist_parsed_factor_records": (
        parsed_factor_persistence_writer.persist_parsed_factor_records
    ),
    "validate_source_document_repository_inputs": (
        source_document_repository.validate_source_document_repository_inputs
    ),
    "validate_source_family_repository_inputs": (
        source_family_repository.validate_source_family_repository_inputs
    ),
    "validate_psycopg_session_adapter_boundary": (
        postgresql_psycopg_session_adapter
        .validate_psycopg_session_adapter_boundary
    ),
    "validate_postgresql_connection_session_runtime_contract": (
        postgresql_connection_session_contract
        .validate_postgresql_connection_session_runtime_contract
    ),
    "validate_postgresql_persistence_options": (
        postgresql_options.validate_postgresql_persistence_options
    ),
    "validate_postgresql_schema_isolation_strategy": (
        postgresql_schema_isolation_strategy
        .validate_postgresql_schema_isolation_strategy
    ),
    "validate_postgresql_statement_execution_contract": (
        postgresql_connection_session_contract
        .validate_postgresql_statement_execution_contract
    ),
    "validate_postgresql_transaction_policy": (
        postgresql_transaction_policy.validate_postgresql_transaction_policy
    ),
    "validate_postgresql_transaction_runtime_boundary": (
        postgresql_transaction_policy
        .validate_postgresql_transaction_runtime_boundary
    ),
}


def test_expected_persistence_public_symbols_import_from_package() -> None:
    imported_symbols = {
        "PersistenceInput": PersistenceInput,
        "PersistenceInputBuildResult": PersistenceInputBuildResult,
        "PersistenceInputBuildStatus": PersistenceInputBuildStatus,
        "PersistenceInputIssue": PersistenceInputIssue,
        "PersistenceInputRecord": PersistenceInputRecord,
        "POSTGRESQL_ISOLATED_SCHEMA_PREFIX": POSTGRESQL_ISOLATED_SCHEMA_PREFIX,
        "POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR": (
            POSTGRESQL_INTEGRATION_TEST_DSN_ENV_VAR
        ),
        "POSTGRESQL_INTEGRATION_TEST_MARKER": POSTGRESQL_INTEGRATION_TEST_MARKER,
        "POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR": (
            POSTGRESQL_INTEGRATION_TEST_OPT_IN_ENV_VAR
        ),
        "POSTGRESQL_INTEGRATION_TEST_OPT_IN_FALSE_VALUES": (
            POSTGRESQL_INTEGRATION_TEST_OPT_IN_FALSE_VALUES
        ),
        "POSTGRESQL_INTEGRATION_TEST_OPT_IN_TRUE_VALUES": (
            POSTGRESQL_INTEGRATION_TEST_OPT_IN_TRUE_VALUES
        ),
        "POSTGRESQL_INTEGRATION_TEST_SKIP_REASON": (
            POSTGRESQL_INTEGRATION_TEST_SKIP_REASON
        ),
        "POSTGRESQL_RESERVED_SCHEMA_NAMES": POSTGRESQL_RESERVED_SCHEMA_NAMES,
        "PersistenceIssue": PersistenceIssue,
        "PersistenceIssueSeverity": PersistenceIssueSeverity,
        "PersistenceRepository": PersistenceRepository,
        "PersistenceResult": PersistenceResult,
        "PersistenceResultStatus": PersistenceResultStatus,
        "ParsedFactorPersistenceCommand": ParsedFactorPersistenceCommand,
        "ParsedFactorPersistenceIssue": ParsedFactorPersistenceIssue,
        "ParsedFactorPersistenceStatus": ParsedFactorPersistenceStatus,
        "ParsedFactorPersistenceWriterResult": ParsedFactorPersistenceWriterResult,
        "SourceDocumentRepository": SourceDocumentRepository,
        "SourceDocumentRepositoryIssue": SourceDocumentRepositoryIssue,
        "SourceDocumentRepositoryPersistResult": (
            SourceDocumentRepositoryPersistResult
        ),
        "SourceDocumentRepositoryPersistStatus": (
            SourceDocumentRepositoryPersistStatus
        ),
        "SourceDocumentRepositoryValidationResult": (
            SourceDocumentRepositoryValidationResult
        ),
        "SourceFamilyDetailRecord": SourceFamilyDetailRecord,
        "SourceFamilyMasterRecord": SourceFamilyMasterRecord,
        "SourceFamilyRepository": SourceFamilyRepository,
        "SourceFamilyRepositoryIssue": SourceFamilyRepositoryIssue,
        "SourceFamilyRepositoryPersistResult": (
            SourceFamilyRepositoryPersistResult
        ),
        "SourceFamilyRepositoryPersistStatus": (
            SourceFamilyRepositoryPersistStatus
        ),
        "SourceFamilyRepositoryValidationResult": (
            SourceFamilyRepositoryValidationResult
        ),
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
        "PostgreSQLIntegrationTestConfigIssue": PostgreSQLIntegrationTestConfigIssue,
        "PostgreSQLIntegrationTestOptInConfig": PostgreSQLIntegrationTestOptInConfig,
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
        "PostgreSQLConnectionSessionContractIssue": (
            PostgreSQLConnectionSessionContractIssue
        ),
        "PostgreSQLConnectionSessionContractStatus": (
            PostgreSQLConnectionSessionContractStatus
        ),
        "PostgreSQLConnectionSessionContractValidationResult": (
            PostgreSQLConnectionSessionContractValidationResult
        ),
        "PostgreSQLConnectionSessionRuntimeContract": (
            PostgreSQLConnectionSessionRuntimeContract
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
        "PostgreSQLRepositoryDisabledExecutionPreviewDescription": (
            PostgreSQLRepositoryDisabledExecutionPreviewDescription
        ),
        "PostgreSQLRepositoryDisabledExecutionPreviewIssue": (
            PostgreSQLRepositoryDisabledExecutionPreviewIssue
        ),
        "PostgreSQLRepositoryDisabledExecutionPreviewResult": (
            PostgreSQLRepositoryDisabledExecutionPreviewResult
        ),
        "PostgreSQLRepositoryDisabledExecutionPreviewStatus": (
            PostgreSQLRepositoryDisabledExecutionPreviewStatus
        ),
        "PostgreSQLRepositoryRuntimeSafetyGate": PostgreSQLRepositoryRuntimeSafetyGate,
        "PostgreSQLRepositoryRuntimeSafetyGateDecision": (
            PostgreSQLRepositoryRuntimeSafetyGateDecision
        ),
        "PostgreSQLRepositoryRuntimeSafetyGateDescription": (
            PostgreSQLRepositoryRuntimeSafetyGateDescription
        ),
        "PostgreSQLRepositoryRuntimeSafetyGateIssue": (
            PostgreSQLRepositoryRuntimeSafetyGateIssue
        ),
        "PostgreSQLRepositoryRuntimeSafetyGateStatus": (
            PostgreSQLRepositoryRuntimeSafetyGateStatus
        ),
        "PostgreSQLRuntimeConfigGate": PostgreSQLRuntimeConfigGate,
        "PostgreSQLRuntimeConfigGateDecision": PostgreSQLRuntimeConfigGateDecision,
        "PostgreSQLRuntimeConfigGateDescription": PostgreSQLRuntimeConfigGateDescription,
        "PostgreSQLRuntimeConfigGateIssue": PostgreSQLRuntimeConfigGateIssue,
        "PostgreSQLRuntimeConfigGateStatus": PostgreSQLRuntimeConfigGateStatus,
        "PostgreSQLRuntimeExecutionGate": PostgreSQLRuntimeExecutionGate,
        "PostgreSQLRuntimeExecutionGateDecision": (
            PostgreSQLRuntimeExecutionGateDecision
        ),
        "PostgreSQLRuntimeExecutionGateDescription": (
            PostgreSQLRuntimeExecutionGateDescription
        ),
        "PostgreSQLRuntimeExecutionGateIssue": (
            PostgreSQLRuntimeExecutionGateIssue
        ),
        "PostgreSQLRuntimeExecutionGateStatus": (
            PostgreSQLRuntimeExecutionGateStatus
        ),
        "PostgreSQLSchemaBootstrapMode": PostgreSQLSchemaBootstrapMode,
        "PostgreSQLSchemaBootstrapPlan": PostgreSQLSchemaBootstrapPlan,
        "PostgreSQLSchemaBootstrapPlanStatement": (
            PostgreSQLSchemaBootstrapPlanStatement
        ),
        "PostgreSQLSchemaBootstrapReport": PostgreSQLSchemaBootstrapReport,
        "PostgreSQLSchemaBootstrapRequest": PostgreSQLSchemaBootstrapRequest,
        "PostgreSQLSchemaBootstrapTableResult": (
            PostgreSQLSchemaBootstrapTableResult
        ),
        "PostgreSQLSchemaBootstrapTableStatus": (
            PostgreSQLSchemaBootstrapTableStatus
        ),
        "PostgreSQLSchemaIsolationCleanupMode": (
            PostgreSQLSchemaIsolationCleanupMode
        ),
        "PostgreSQLSchemaIsolationCleanupScope": (
            PostgreSQLSchemaIsolationCleanupScope
        ),
        "PostgreSQLSchemaIsolationStrategy": PostgreSQLSchemaIsolationStrategy,
        "PostgreSQLSchemaIsolationStrategyDescription": (
            PostgreSQLSchemaIsolationStrategyDescription
        ),
        "PostgreSQLSchemaIsolationStrategyIssue": (
            PostgreSQLSchemaIsolationStrategyIssue
        ),
        "PostgreSQLSchemaIsolationStrategyStatus": (
            PostgreSQLSchemaIsolationStrategyStatus
        ),
        "PostgreSQLSchemaIsolationStrategyValidationResult": (
            PostgreSQLSchemaIsolationStrategyValidationResult
        ),
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
        "PostgreSQLTransactionPolicyValidationResult": (
            PostgreSQLTransactionPolicyValidationResult
        ),
        "PostgreSQLTransactionRuntimeBoundary": (
            PostgreSQLTransactionRuntimeBoundary
        ),
        "build_persistence_input_from_normalization_result": (
            build_persistence_input_from_normalization_result
        ),
        "build_parsed_factor_persistence_command": (
            build_parsed_factor_persistence_command
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
        "build_postgresql_phase1_schema_bootstrap_plan": (
            build_postgresql_phase1_schema_bootstrap_plan
        ),
        "build_postgresql_phase1_schema_bootstrap_report": (
            build_postgresql_phase1_schema_bootstrap_report
        ),
        "build_postgresql_phase1_schema_bootstrap_request": (
            build_postgresql_phase1_schema_bootstrap_request
        ),
        "build_postgresql_repository_disabled_execution_preview": (
            build_postgresql_repository_disabled_execution_preview
        ),
        "build_postgresql_transaction_plan": build_postgresql_transaction_plan,
        "build_default_postgresql_schema_isolation_strategy": (
            build_default_postgresql_schema_isolation_strategy
        ),
        "create_persistence_result": create_persistence_result,
        "create_source_document_repository_persist_result": (
            create_source_document_repository_persist_result
        ),
        "create_source_family_repository_persist_result": (
            create_source_family_repository_persist_result
        ),
        "create_postgresql_connection_session_runtime_contract": (
            create_postgresql_connection_session_runtime_contract
        ),
        "create_postgresql_integration_test_boundary": (
            create_postgresql_integration_test_boundary
        ),
        "create_postgresql_persistence_options": (
            create_postgresql_persistence_options
        ),
        "create_postgresql_transaction_runtime_boundary": (
            create_postgresql_transaction_runtime_boundary
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
        "describe_postgresql_repository_disabled_execution_preview": (
            describe_postgresql_repository_disabled_execution_preview
        ),
        "describe_postgresql_repository_runtime_safety_gate": (
            describe_postgresql_repository_runtime_safety_gate
        ),
        "describe_postgresql_runtime_config_gate": (
            describe_postgresql_runtime_config_gate
        ),
        "describe_postgresql_runtime_execution_gate": (
            describe_postgresql_runtime_execution_gate
        ),
        "describe_postgresql_schema_isolation_strategy": (
            describe_postgresql_schema_isolation_strategy
        ),
        "describe_postgresql_transaction_policy_boundary": (
            describe_postgresql_transaction_policy_boundary
        ),
        "evaluate_postgresql_runtime_config_gate": (
            evaluate_postgresql_runtime_config_gate
        ),
        "evaluate_postgresql_runtime_execution_gate": (
            evaluate_postgresql_runtime_execution_gate
        ),
        "evaluate_postgresql_repository_runtime_safety_gate": (
            evaluate_postgresql_repository_runtime_safety_gate
        ),
        "evaluate_postgresql_integration_test_opt_in_config": (
            evaluate_postgresql_integration_test_opt_in_config
        ),
        "get_normalized_record_postgresql_schema": (
            get_normalized_record_postgresql_schema
        ),
        "render_postgresql_ddl_preview": render_postgresql_ddl_preview,
        "persist_parsed_factor_records": persist_parsed_factor_records,
        "should_skip_postgresql_integration_tests": (
            should_skip_postgresql_integration_tests
        ),
        "source_family_repository_table_names": source_family_repository_table_names,
        "validate_source_document_repository_inputs": (
            validate_source_document_repository_inputs
        ),
        "validate_source_family_repository_inputs": (
            validate_source_family_repository_inputs
        ),
        "validate_psycopg_session_adapter_boundary": (
            validate_psycopg_session_adapter_boundary
        ),
        "validate_postgresql_connection_session_runtime_contract": (
            validate_postgresql_connection_session_runtime_contract
        ),
        "validate_postgresql_persistence_options": (
            validate_postgresql_persistence_options
        ),
        "validate_postgresql_schema_isolation_strategy": (
            validate_postgresql_schema_isolation_strategy
        ),
        "validate_postgresql_statement_execution_contract": (
            validate_postgresql_statement_execution_contract
        ),
        "validate_postgresql_transaction_policy": (
            validate_postgresql_transaction_policy
        ),
        "validate_postgresql_transaction_runtime_boundary": (
            validate_postgresql_transaction_runtime_boundary
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
    assert "postgresql_repository_disabled_execution_preview" not in persistence.__all__
    assert "postgresql_runtime_execution_gate" not in persistence.__all__
    assert "postgresql_schema_bootstrap" not in persistence.__all__
    assert "postgresql_schema_ddl" not in persistence.__all__
    assert all(not name.startswith("_") for name in persistence.__all__)
