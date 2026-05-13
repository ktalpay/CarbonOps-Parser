namespace CarbonOps.Parser.Contracts;

public enum Phase1IngestionExecutionMode
{
    Sequential = 0,
    BoundedParallel = 1,
}

public enum Phase1IngestionRunStatus
{
    Completed = 0,
    CompletedWithFailures = 1,
    Failed = 2,
    NotExecutable = 3,
}

public enum Phase1IngestionFamilyRunStatus
{
    Completed = 0,
    Failed = 1,
    Skipped = 2,
}

public sealed record Phase1IngestionFailure(
    SourceFamily SourceFamily,
    string SourceKey,
    string Stage,
    string Code,
    string Message,
    string? FieldName = null,
    string Severity = "error");

public sealed record Phase1IngestionOrchestratorRequest
{
    public IReadOnlyList<SourceFamily> SourceFamilies { get; }

    public Phase1IngestionExecutionMode ExecutionMode { get; }

    public int MaxDegreeOfParallelism { get; }

    public PostgreSQLRuntimeConfigGate RuntimeConfigGate { get; }

    public PostgreSQLSchemaBootstrapReport? SchemaBootstrapReport { get; }

    public string RunId { get; }

    public string? CorrelationId { get; }

    public Phase1IngestionOrchestratorRequest(
        IEnumerable<SourceFamily> sourceFamilies,
        Phase1IngestionExecutionMode executionMode = Phase1IngestionExecutionMode.Sequential,
        int maxDegreeOfParallelism = 1,
        PostgreSQLRuntimeConfigGate? runtimeConfigGate = null,
        string runId = "phase1_ingestion_orchestrator_run",
        string? correlationId = null,
        PostgreSQLSchemaBootstrapReport? schemaBootstrapReport = null)
    {
        SourceFamilies = Array.AsReadOnly(sourceFamilies.ToArray());
        ExecutionMode = executionMode;
        MaxDegreeOfParallelism = maxDegreeOfParallelism;
        RuntimeConfigGate = runtimeConfigGate ?? new PostgreSQLRuntimeConfigGate();
        SchemaBootstrapReport = schemaBootstrapReport;
        RunId = runId;
        CorrelationId = correlationId;
    }
}

public sealed record Phase1IngestionFamilyResult
{
    public SourceFamily SourceFamily { get; }

    public string SourceKey { get; }

    public Phase1IngestionFamilyRunStatus Status { get; }

    public SourceAcquisitionRunResult? AcquisitionRun { get; }

    public SourceAcquisitionRunRepositoryPersistResult? AcquisitionRunPersistResult { get; }

    public SourceDocumentRepositoryPersistResult? SourceDocumentPersistResult { get; }

    public ParserAdapterRunResult? ParserRun { get; }

    public ParserRunRepositoryPersistResult? ParserRunPersistResult { get; }

    public ParsedFactorPersistenceWriterResult? ParsedFactorPersistResult { get; }

    public IReadOnlyList<Phase1IngestionFailure> Failures { get; }

    public int SourceCandidateCount => AcquisitionRun?.CandidateCount ?? 0;

    public int SourceDocumentMetadataCount => AcquisitionRun?.ArtifactCount ?? 0;

    public int ParserAcceptedRowCount => ParserRun?.RowCount ?? 0;

    public int ParserFailureCount => ParserRun?.ValidationIssues.Count(issue => issue.Severity == ParserValidationIssueSeverity.Error) ?? 0;

    public int PersistedMasterCount => ParsedFactorPersistResult?.PersistedMasterCount ?? 0;

    public int PersistedDetailCount => ParsedFactorPersistResult?.PersistedDetailCount ?? 0;

    public int FailureCount => Failures.Count;

    public Phase1IngestionFamilyResult(
        SourceFamily sourceFamily,
        string sourceKey,
        Phase1IngestionFamilyRunStatus status,
        SourceAcquisitionRunResult? acquisitionRun = null,
        SourceAcquisitionRunRepositoryPersistResult? acquisitionRunPersistResult = null,
        SourceDocumentRepositoryPersistResult? sourceDocumentPersistResult = null,
        ParserAdapterRunResult? parserRun = null,
        ParserRunRepositoryPersistResult? parserRunPersistResult = null,
        ParsedFactorPersistenceWriterResult? parsedFactorPersistResult = null,
        IEnumerable<Phase1IngestionFailure>? failures = null)
    {
        SourceFamily = sourceFamily;
        SourceKey = sourceKey;
        Status = status;
        AcquisitionRun = acquisitionRun;
        AcquisitionRunPersistResult = acquisitionRunPersistResult;
        SourceDocumentPersistResult = sourceDocumentPersistResult;
        ParserRun = parserRun;
        ParserRunPersistResult = parserRunPersistResult;
        ParsedFactorPersistResult = parsedFactorPersistResult;
        Failures = Array.AsReadOnly((failures ?? []).ToArray());
    }
}

public sealed record Phase1IngestionOrchestratorResult
{
    public Phase1IngestionOrchestratorRequest Request { get; }

    public PostgreSQLRuntimeConfigGateDecision RuntimeConfigDecision { get; }

    public Phase1IngestionRunStatus Status { get; }

    public IReadOnlyList<SourceFamily> SelectedSourceFamilies { get; }

    public IReadOnlyList<Phase1IngestionFamilyResult> FamilyResults { get; }

    public IReadOnlyList<Phase1IngestionFailure> Failures { get; }

    public int SourceFamilyCount => FamilyResults.Count;

    public int CompletedSourceFamilyCount => FamilyResults.Count(result => result.Status == Phase1IngestionFamilyRunStatus.Completed);

    public int FailedSourceFamilyCount => FamilyResults.Count(result => result.Status == Phase1IngestionFamilyRunStatus.Failed);

    public int TotalSourceDocumentMetadataCount => FamilyResults.Sum(result => result.SourceDocumentMetadataCount);

    public int TotalParserAcceptedRowCount => FamilyResults.Sum(result => result.ParserAcceptedRowCount);

    public int TotalParserFailureCount => FamilyResults.Sum(result => result.ParserFailureCount);

    public int TotalPersistedMasterCount => FamilyResults.Sum(result => result.PersistedMasterCount);

    public int TotalPersistedDetailCount => FamilyResults.Sum(result => result.PersistedDetailCount);

    public int FailureCount => Failures.Count;

    public Phase1IngestionOrchestratorResult(
        Phase1IngestionOrchestratorRequest request,
        PostgreSQLRuntimeConfigGateDecision runtimeConfigDecision,
        IEnumerable<Phase1IngestionFamilyResult> familyResults,
        IEnumerable<Phase1IngestionFailure>? failures = null,
        Phase1IngestionRunStatus? status = null,
        IEnumerable<SourceFamily>? selectedSourceFamilies = null)
    {
        Request = request;
        RuntimeConfigDecision = runtimeConfigDecision;
        var familyResultArray = familyResults.ToArray();
        var failureArray = (failures ?? []).ToArray();
        FamilyResults = Array.AsReadOnly(familyResultArray);
        Failures = Array.AsReadOnly(failureArray);
        Status = status ?? StatusFromFamilyResults(familyResultArray);
        SelectedSourceFamilies = Array.AsReadOnly(
            (selectedSourceFamilies ?? familyResultArray.Select(result => result.SourceFamily))
            .ToArray());
    }

    private static Phase1IngestionRunStatus StatusFromFamilyResults(
        IReadOnlyCollection<Phase1IngestionFamilyResult> familyResults)
    {
        if (familyResults.Count == 0)
        {
            return Phase1IngestionRunStatus.Failed;
        }

        var completedCount = familyResults.Count(result =>
            result.Status == Phase1IngestionFamilyRunStatus.Completed);

        return completedCount == familyResults.Count
            ? Phase1IngestionRunStatus.Completed
            : completedCount > 0
                ? Phase1IngestionRunStatus.CompletedWithFailures
                : Phase1IngestionRunStatus.Failed;
    }
}

public interface IPhase1SourceFamilyIngestionRuntime
{
    SourceFamily SourceFamily { get; }

    SourceAcquisitionRunResult DiscoverAndDownload(string runId, string? correlationId);

    ParserAdapterRunResult Normalize(ParserAdapterRunRequest request);
}

public sealed record Phase1IngestionOrchestratorDependencies(
    IEnumerable<IPhase1SourceFamilyIngestionRuntime> SourceRuntimes,
    ISourceAcquisitionRunRepository SourceAcquisitionRunRepository,
    ISourceDocumentRepository SourceDocumentRepository,
    IParserRunRepository ParserRunRepository,
    ISourceFamilyRepository SourceFamilyRepository);

public sealed class Phase1IngestionOrchestrator
{
    private readonly IReadOnlyDictionary<SourceFamily, IPhase1SourceFamilyIngestionRuntime> sourceRuntimes;
    private readonly ISourceAcquisitionRunRepository sourceAcquisitionRunRepository;
    private readonly ISourceDocumentRepository sourceDocumentRepository;
    private readonly IParserRunRepository parserRunRepository;
    private readonly ISourceFamilyRepository sourceFamilyRepository;

    public Phase1IngestionOrchestrator(Phase1IngestionOrchestratorDependencies dependencies)
    {
        sourceRuntimes = dependencies.SourceRuntimes.ToDictionary(runtime => runtime.SourceFamily);
        sourceAcquisitionRunRepository = dependencies.SourceAcquisitionRunRepository;
        sourceDocumentRepository = dependencies.SourceDocumentRepository;
        parserRunRepository = dependencies.ParserRunRepository;
        sourceFamilyRepository = dependencies.SourceFamilyRepository;
    }

    public Phase1IngestionOrchestratorResult Run(Phase1IngestionOrchestratorRequest request)
    {
        var runtimeDecision = PostgreSQLRuntimeConfigGateEvaluator.Evaluate(request.RuntimeConfigGate);
        var selectedSourceFamilies = request.SourceFamilies
            .Where(sourceFamily => Enum.IsDefined(sourceFamily))
            .Distinct()
            .ToArray();
        var readinessFailures = ValidateRequest(request)
            .Concat(ValidatePostgreSQLReadiness(request, runtimeDecision))
            .ToArray();
        if (readinessFailures.Length > 0)
        {
            return new Phase1IngestionOrchestratorResult(
                request,
                runtimeDecision,
                [],
                readinessFailures,
                Phase1IngestionRunStatus.NotExecutable,
                selectedSourceFamilies);
        }

        var familyResults = new List<Phase1IngestionFamilyResult>();
        foreach (var sourceFamily in selectedSourceFamilies)
        {
            familyResults.Add(RunSourceFamily(sourceFamily, request));
        }

        return new Phase1IngestionOrchestratorResult(
            request,
            runtimeDecision,
            familyResults,
            familyResults.SelectMany(result => result.Failures),
            selectedSourceFamilies: selectedSourceFamilies);
    }

    private Phase1IngestionFamilyResult RunSourceFamily(
        SourceFamily sourceFamily,
        Phase1IngestionOrchestratorRequest request)
    {
        var sourceKey = sourceFamily.ToWireName();
        if (!sourceRuntimes.TryGetValue(sourceFamily, out var runtime))
        {
            return Failed(sourceFamily, sourceKey, Failure(sourceFamily, sourceKey, "runtime", "PHASE1_RUNTIME_MISSING", "No ingestion runtime is registered for the selected source family."));
        }

        SourceAcquisitionRunResult? acquisitionRun = null;
        SourceAcquisitionRunRepositoryPersistResult? acquisitionPersist = null;
        SourceDocumentRepositoryPersistResult? documentPersist = null;
        ParserAdapterRunResult? parserRun = null;
        ParserRunRepositoryPersistResult? parserPersist = null;
        ParsedFactorPersistenceWriterResult? factorPersist = null;
        var failures = new List<Phase1IngestionFailure>();

        try
        {
            acquisitionRun = runtime.DiscoverAndDownload(request.RunId, request.CorrelationId);
            failures.AddRange(ValidateAcquisition(sourceFamily, sourceKey, acquisitionRun));
            acquisitionPersist = sourceAcquisitionRunRepository.PersistRuns([acquisitionRun]);
            failures.AddRange(FromAcquisitionRepositoryIssues(sourceFamily, sourceKey, acquisitionPersist.Issues));
            documentPersist = sourceDocumentRepository.PersistSourceDocuments(CreateSourceDocumentRecords(acquisitionRun.Artifacts));
            failures.AddRange(FromSourceDocumentRepositoryIssues(sourceFamily, sourceKey, documentPersist.Issues));

            if (failures.Any(failure => failure.Stage is "discovery" or "download" or "source_document_persistence" or "source_acquisition_run_persistence"))
            {
                return BuildResult(sourceFamily, sourceKey, failures, acquisitionRun, acquisitionPersist, documentPersist);
            }

            var bridgeBatch = SourceArtifactParserInputBridgeRegistry.CreateBridgeBatch(acquisitionRun.Artifacts);
            var parserKey = ParserSelectionRegistry.GetParserKey(sourceFamily);
            var parserRequest = new ParserAdapterRunRequest(
                sourceFamily,
                sourceKey,
                parserKey,
                bridgeBatch.Bridges.Select(bridge => bridge.ParserInputArtifact),
                runId: $"{request.RunId}-{sourceKey}-parser",
                correlationId: request.CorrelationId,
                requestedReportingYear: acquisitionRun.ReportingYear);
            parserRun = runtime.Normalize(parserRequest);
            failures.AddRange(FromParserIssues(sourceFamily, sourceKey, parserRun.ValidationIssues));
            parserPersist = parserRunRepository.PersistRuns([CreateParserRunResult(parserRun)]);
            failures.AddRange(FromParserRunRepositoryIssues(sourceFamily, sourceKey, parserPersist.Issues));

            if (parserRun.Status != ParserRunStatus.Completed ||
                failures.Any(failure => failure.Stage is "parser" or "parser_run_persistence"))
            {
                return BuildResult(sourceFamily, sourceKey, failures, acquisitionRun, acquisitionPersist, documentPersist, parserRun, parserPersist);
            }

            var sourceDocumentId = acquisitionRun.Artifacts.Count == 1
                ? acquisitionRun.Artifacts[0].ArtifactId
                : null;
            factorPersist = ParsedFactorPersistenceWriter.Persist(
                new ParserNormalizedOutputBatch(parserRun.Rows),
                sourceFamilyRepository,
                sourceDocumentId);
            failures.AddRange(FromParsedFactorPersistenceIssues(sourceFamily, sourceKey, factorPersist.Issues));

            return BuildResult(
                sourceFamily,
                sourceKey,
                failures,
                acquisitionRun,
                acquisitionPersist,
                documentPersist,
                parserRun,
                parserPersist,
                factorPersist);
        }
        catch (Exception exception) when (exception is InvalidOperationException or ArgumentException)
        {
            failures.Add(Failure(sourceFamily, sourceKey, "orchestrator", "PHASE1_ORCHESTRATOR_EXCEPTION", exception.Message));
            return BuildResult(
                sourceFamily,
                sourceKey,
                failures,
                acquisitionRun,
                acquisitionPersist,
                documentPersist,
                parserRun,
                parserPersist,
                factorPersist);
        }
    }

    private static Phase1IngestionFamilyResult BuildResult(
        SourceFamily sourceFamily,
        string sourceKey,
        IReadOnlyCollection<Phase1IngestionFailure> failures,
        SourceAcquisitionRunResult? acquisitionRun = null,
        SourceAcquisitionRunRepositoryPersistResult? acquisitionRunPersistResult = null,
        SourceDocumentRepositoryPersistResult? sourceDocumentPersistResult = null,
        ParserAdapterRunResult? parserRun = null,
        ParserRunRepositoryPersistResult? parserRunPersistResult = null,
        ParsedFactorPersistenceWriterResult? parsedFactorPersistResult = null) =>
        new(
            sourceFamily,
            sourceKey,
            failures.Any(failure => failure.Severity == "error")
                ? Phase1IngestionFamilyRunStatus.Failed
                : Phase1IngestionFamilyRunStatus.Completed,
            acquisitionRun,
            acquisitionRunPersistResult,
            sourceDocumentPersistResult,
            parserRun,
            parserRunPersistResult,
            parsedFactorPersistResult,
            failures);

    private static Phase1IngestionFamilyResult Failed(
        SourceFamily sourceFamily,
        string sourceKey,
        Phase1IngestionFailure failure) =>
        new(
            sourceFamily,
            sourceKey,
            Phase1IngestionFamilyRunStatus.Failed,
            failures: [failure]);

    private static IEnumerable<Phase1IngestionFailure> ValidateRequest(Phase1IngestionOrchestratorRequest request)
    {
        var hasValidSourceFamily = request.SourceFamilies.Any(sourceFamily =>
            Enum.IsDefined(sourceFamily));
        if (request.SourceFamilies.Count == 0 || !hasValidSourceFamily)
        {
            yield return Failure(SourceFamily.GhgProtocol, "", "request", "PHASE1_SOURCE_FAMILY_SELECTION_REQUIRED", "At least one source family must be explicitly selected.", "SourceFamilies");
        }

        for (var index = 0; index < request.SourceFamilies.Count; index++)
        {
            var sourceFamily = request.SourceFamilies[index];
            if (!Enum.IsDefined(sourceFamily))
            {
                yield return Failure(SourceFamily.GhgProtocol, "", "request", "PHASE1_SOURCE_FAMILY_INVALID", "Selected source families must be defined Phase 1 source families.", $"SourceFamilies[{index}]");
            }
        }

        if (!Enum.IsDefined(request.ExecutionMode))
        {
            yield return Failure(SourceFamily.GhgProtocol, "", "request", "PHASE1_EXECUTION_MODE_INVALID", "Execution mode must be a defined Phase 1 ingestion execution mode.", "ExecutionMode");
        }

        if (request.MaxDegreeOfParallelism < 1)
        {
            yield return Failure(SourceFamily.GhgProtocol, "", "request", "PHASE1_MAX_DEGREE_INVALID", "MaxDegreeOfParallelism must be at least 1.", "MaxDegreeOfParallelism");
        }

        if (request.ExecutionMode == Phase1IngestionExecutionMode.Sequential && request.MaxDegreeOfParallelism != 1)
        {
            yield return Failure(SourceFamily.GhgProtocol, "", "request", "PHASE1_SEQUENTIAL_MAX_DEGREE_MUST_BE_ONE", "Sequential execution must use MaxDegreeOfParallelism=1.", "MaxDegreeOfParallelism");
        }

        if (request.ExecutionMode == Phase1IngestionExecutionMode.BoundedParallel)
        {
            yield return Failure(SourceFamily.GhgProtocol, "", "execution_mode", "PHASE1_INGESTION_BOUNDED_PARALLEL_NOT_ENABLED", "Bounded parallel execution is a declared extension point only.", "ExecutionMode");
        }
    }

    private static IEnumerable<Phase1IngestionFailure> ValidatePostgreSQLReadiness(
        Phase1IngestionOrchestratorRequest request,
        PostgreSQLRuntimeConfigGateDecision runtimeDecision)
    {
        if (request.RuntimeConfigGate.Requested && !runtimeDecision.RuntimeEnabled)
        {
            var issue = runtimeDecision.Issues.FirstOrDefault();
            yield return Failure(
                SourceFamily.GhgProtocol,
                "",
                "postgresql_runtime_config",
                issue?.Code ?? "PHASE1_INGESTION_POSTGRESQL_RUNTIME_NOT_READY",
                issue?.Message ?? "PostgreSQL runtime configuration is not ready.",
                issue?.FieldName ?? "RuntimeConfigGate");
        }

        if (request.SchemaBootstrapReport is { FailOnMissing: true } report &&
            report.MissingTableNames.Count > 0)
        {
            yield return Failure(
                SourceFamily.GhgProtocol,
                "",
                "postgresql_schema_bootstrap",
                "PHASE1_INGESTION_POSTGRESQL_SCHEMA_NOT_READY",
                "PostgreSQL schema bootstrap reported missing required tables.",
                "schema_bootstrap_report.missing_table_names");
        }
    }

    private static IEnumerable<Phase1IngestionFailure> ValidateAcquisition(
        SourceFamily sourceFamily,
        string sourceKey,
        SourceAcquisitionRunResult acquisitionRun)
    {
        if (acquisitionRun.SourceFamily != sourceFamily || acquisitionRun.SourceKey != sourceKey)
        {
            yield return Failure(sourceFamily, sourceKey, "discovery", "PHASE1_ACQUISITION_SOURCE_MISMATCH", "Acquisition result source family and source key must match the selected source family.");
        }

        if (acquisitionRun.Status == SourceAcquisitionRunStatus.Failed ||
            acquisitionRun.Status == SourceAcquisitionRunStatus.InvalidRequest)
        {
            yield return Failure(sourceFamily, sourceKey, "download", "PHASE1_ACQUISITION_FAILED", "Source discovery/download did not complete successfully.");
        }

        if (acquisitionRun.CandidateCount == 0)
        {
            yield return Failure(sourceFamily, sourceKey, "discovery", "PHASE1_DISCOVERY_NO_CANDIDATES", "Source discovery returned no candidates.");
        }

        if (acquisitionRun.ArtifactCount == 0)
        {
            yield return Failure(sourceFamily, sourceKey, "download", "PHASE1_DOWNLOAD_NO_ARTIFACTS", "Source download returned no artifacts.");
        }
    }

    private static IEnumerable<SourceDocumentPersistenceRecord> CreateSourceDocumentRecords(
        IEnumerable<SourceDownloadArtifact> artifacts)
    {
        foreach (var artifact in artifacts)
        {
            var checksum = artifact.Checksum ?? new SourceDocumentChecksum(
                "not_supplied",
                $"{artifact.ArtifactId}_checksum_not_supplied",
                IsDryRunPlaceholder: true);
            yield return new SourceDocumentPersistenceRecord(
                artifact.SourceFamily,
                artifact.LocalReference,
                checksum.Algorithm,
                checksum.Value,
                checksum.IsDryRunPlaceholder);
        }
    }

    private static ParserRunResult CreateParserRunResult(ParserAdapterRunResult parserRun)
    {
        var request = new ParserRunRequest(
            parserRun.SourceFamily,
            parserRun.ArtifactReferences.FirstOrDefault() ?? $"{parserRun.SourceKey}_artifact_unavailable",
            "not_supplied",
            $"{parserRun.SourceKey}_parser_run_checksum_not_supplied",
            isDryRunChecksum: true);
        var rejectedRows = parserRun.ValidationIssues.Count(issue => issue.Severity == ParserValidationIssueSeverity.Error);
        return new ParserRunResult(
            request,
            parserRun.Status,
            parserRun.RowCount + rejectedRows,
            parserRun.RowCount,
            rejectedRows,
            parserRun.ValidationIssues.Select(issue => new ParserRunIssue(
                issue.Code,
                issue.Message,
                issue.Severity == ParserValidationIssueSeverity.Error
                    ? ParserRunIssueSeverity.Error
                    : ParserRunIssueSeverity.Warning,
                issue.FieldKey)));
    }

    private static IEnumerable<Phase1IngestionFailure> FromParserIssues(
        SourceFamily sourceFamily,
        string sourceKey,
        IEnumerable<ParserValidationIssue> issues) =>
        issues
            .Where(issue => issue.Severity == ParserValidationIssueSeverity.Error)
            .Select(issue => Failure(sourceFamily, sourceKey, "parser", issue.Code, issue.Message, issue.FieldKey));

    private static IEnumerable<Phase1IngestionFailure> FromAcquisitionRepositoryIssues(
        SourceFamily sourceFamily,
        string sourceKey,
        IEnumerable<SourceAcquisitionRunRepositoryIssue> issues) =>
        issues.Select(issue => Failure(sourceFamily, sourceKey, "source_acquisition_run_persistence", issue.Code, issue.Message, issue.FieldName, issue.Severity));

    private static IEnumerable<Phase1IngestionFailure> FromSourceDocumentRepositoryIssues(
        SourceFamily sourceFamily,
        string sourceKey,
        IEnumerable<SourceDocumentRepositoryIssue> issues) =>
        issues.Select(issue => Failure(sourceFamily, sourceKey, "source_document_persistence", issue.Code, issue.Message, issue.FieldName, issue.Severity));

    private static IEnumerable<Phase1IngestionFailure> FromParserRunRepositoryIssues(
        SourceFamily sourceFamily,
        string sourceKey,
        IEnumerable<ParserRunRepositoryIssue> issues) =>
        issues.Select(issue => Failure(sourceFamily, sourceKey, "parser_run_persistence", issue.Code, issue.Message, issue.FieldName, issue.Severity));

    private static IEnumerable<Phase1IngestionFailure> FromParsedFactorPersistenceIssues(
        SourceFamily sourceFamily,
        string sourceKey,
        IEnumerable<ParsedFactorPersistenceIssue> issues) =>
        issues
            .Where(issue => issue.Severity == "error")
            .Select(issue => Failure(sourceFamily, sourceKey, "parsed_factor_persistence", issue.Code, issue.Message, issue.FieldName, issue.Severity));

    private static Phase1IngestionFailure Failure(
        SourceFamily sourceFamily,
        string sourceKey,
        string stage,
        string code,
        string message,
        string? fieldName = null,
        string severity = "error") =>
        new(sourceFamily, sourceKey, stage, code, message, fieldName, severity);

}
