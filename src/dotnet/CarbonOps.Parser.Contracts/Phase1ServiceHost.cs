namespace CarbonOps.Parser.Contracts;

public enum Phase1ServiceHostStatus
{
    Created = 0,
    Ready = 1,
    Blocked = 2,
    Running = 3,
    ShutdownRequested = 4,
    Stopped = 5,
}

public enum Phase1ScheduledRunStatus
{
    Started = 0,
    SkippedNotStarted = 1,
    SkippedAlreadyRunning = 2,
    SkippedShuttingDown = 3,
}

public sealed record Phase1ServiceHostConfig
{
    public IReadOnlyList<SourceFamily> SourceFamilies { get; }

    public PostgreSQLPersistenceOptions PostgreSQLOptions { get; }

    public string RunIdPrefix { get; }

    public int ScheduleIntervalSeconds { get; }

    public Phase1IngestionExecutionMode ExecutionMode { get; }

    public int MaxDegreeOfParallelism { get; }

    public PostgreSQLSchemaBootstrapMode SchemaBootstrapMode { get; }

    public bool FailOnMissingSchema { get; }

    public PostgreSQLRuntimeConfigGate RuntimeConfigGate { get; }

    public Phase1ServiceHostConfig(
        IEnumerable<SourceFamily> sourceFamilies,
        PostgreSQLPersistenceOptions postgreSQLOptions,
        string runIdPrefix = "phase1-scheduled",
        int scheduleIntervalSeconds = 3600,
        Phase1IngestionExecutionMode executionMode = Phase1IngestionExecutionMode.Sequential,
        int maxDegreeOfParallelism = 1,
        PostgreSQLSchemaBootstrapMode schemaBootstrapMode = PostgreSQLSchemaBootstrapMode.CheckOnly,
        bool failOnMissingSchema = true,
        PostgreSQLRuntimeConfigGate? runtimeConfigGate = null)
    {
        SourceFamilies = Array.AsReadOnly(sourceFamilies.ToArray());
        PostgreSQLOptions = postgreSQLOptions;
        RunIdPrefix = runIdPrefix;
        ScheduleIntervalSeconds = scheduleIntervalSeconds;
        ExecutionMode = executionMode;
        MaxDegreeOfParallelism = maxDegreeOfParallelism;
        SchemaBootstrapMode = schemaBootstrapMode;
        FailOnMissingSchema = failOnMissingSchema;
        RuntimeConfigGate = runtimeConfigGate ?? new PostgreSQLRuntimeConfigGate();
    }
}

public sealed record Phase1ServiceHostIssue(
    string Code,
    string Message,
    string? FieldName = null,
    string Severity = "error");

public sealed record Phase1ServiceHostStartupResult
{
    public Phase1ServiceHostStatus Status { get; }

    public IReadOnlyList<Phase1ServiceHostIssue> Issues { get; }

    public PostgreSQLSchemaBootstrapReport? SchemaBootstrapReport { get; }

    public bool IsReady => Status == Phase1ServiceHostStatus.Ready;

    public Phase1ServiceHostStartupResult(
        Phase1ServiceHostStatus status,
        IEnumerable<Phase1ServiceHostIssue> issues,
        PostgreSQLSchemaBootstrapReport? schemaBootstrapReport = null)
    {
        Status = status;
        Issues = Array.AsReadOnly(issues.ToArray());
        SchemaBootstrapReport = schemaBootstrapReport;
    }
}

public sealed record Phase1ScheduledRunResult
{
    public Phase1ScheduledRunStatus Status { get; }

    public string? RunId { get; }

    public Phase1IngestionOrchestratorResult? OrchestratorResult { get; }

    public IReadOnlyList<Phase1ServiceHostIssue> Issues { get; }

    public Phase1ScheduledRunResult(
        Phase1ScheduledRunStatus status,
        string? runId = null,
        Phase1IngestionOrchestratorResult? orchestratorResult = null,
        IEnumerable<Phase1ServiceHostIssue>? issues = null)
    {
        Status = status;
        RunId = runId;
        OrchestratorResult = orchestratorResult;
        Issues = Array.AsReadOnly((issues ?? []).ToArray());
    }
}

public delegate PostgreSQLSchemaBootstrapReport Phase1SchemaBootstrapChecker(
    PostgreSQLSchemaBootstrapMode mode,
    bool failOnMissing);

public delegate Phase1IngestionOrchestratorResult Phase1OrchestratorRunner(
    Phase1IngestionOrchestratorRequest request);

public sealed class Phase1ScheduledIngestionServiceHost
{
    private readonly object syncRoot = new();
    private readonly Phase1SchemaBootstrapChecker schemaBootstrapChecker;
    private readonly Phase1OrchestratorRunner orchestratorRunner;
    private PostgreSQLSchemaBootstrapReport? schemaBootstrapReport;
    private bool runInProgress;
    private bool shutdownRequested;
    private int runSequence;

    public Phase1ServiceHostConfig Config { get; }

    public Phase1ServiceHostStatus Status { get; private set; } = Phase1ServiceHostStatus.Created;

    public Phase1ScheduledIngestionServiceHost(
        Phase1ServiceHostConfig config,
        Phase1OrchestratorRunner orchestratorRunner,
        Phase1SchemaBootstrapChecker? schemaBootstrapChecker = null)
    {
        Config = config;
        this.orchestratorRunner = orchestratorRunner;
        this.schemaBootstrapChecker = schemaBootstrapChecker ?? DefaultSchemaBootstrapChecker;
    }

    public Phase1ServiceHostStartupResult Start()
    {
        var issues = ValidateConfig(Config).ToList();
        PostgreSQLSchemaBootstrapReport? report = null;

        if (issues.Count == 0)
        {
            report = schemaBootstrapChecker(Config.SchemaBootstrapMode, Config.FailOnMissingSchema);
            issues.AddRange(SchemaBootstrapIssues(report));
        }

        var status = issues.Count == 0
            ? Phase1ServiceHostStatus.Ready
            : Phase1ServiceHostStatus.Blocked;
        var result = new Phase1ServiceHostStartupResult(status, issues, report);

        lock (syncRoot)
        {
            if (shutdownRequested)
            {
                Status = Phase1ServiceHostStatus.Stopped;
                return new Phase1ServiceHostStartupResult(
                    Phase1ServiceHostStatus.Blocked,
                    [
                        new Phase1ServiceHostIssue(
                            "PHASE1_SERVICE_HOST_SHUTDOWN_REQUESTED",
                            "Service host startup is blocked after shutdown.",
                            "status"),
                    ],
                    report);
            }

            Status = status;
            schemaBootstrapReport = report;
        }

        return result;
    }

    public Phase1ScheduledRunResult TriggerScheduledRun()
    {
        string runId;
        Phase1IngestionOrchestratorRequest request;

        lock (syncRoot)
        {
            if (shutdownRequested)
            {
                return new Phase1ScheduledRunResult(
                    Phase1ScheduledRunStatus.SkippedShuttingDown,
                    issues: [ShutdownIssue()]);
            }

            if (runInProgress)
            {
                return new Phase1ScheduledRunResult(
                    Phase1ScheduledRunStatus.SkippedAlreadyRunning,
                    issues:
                    [
                        new Phase1ServiceHostIssue(
                            "PHASE1_SERVICE_HOST_RUN_ALREADY_IN_PROGRESS",
                            "Scheduled trigger skipped while a run is active.",
                            "run_in_progress"),
                    ]);
            }

            if (Status != Phase1ServiceHostStatus.Ready)
            {
                return new Phase1ScheduledRunResult(
                    Phase1ScheduledRunStatus.SkippedNotStarted,
                    issues:
                    [
                        new Phase1ServiceHostIssue(
                            "PHASE1_SERVICE_HOST_NOT_READY",
                            "Service host must start successfully first.",
                            "status"),
                    ]);
            }

            runInProgress = true;
            Status = Phase1ServiceHostStatus.Running;
            runSequence++;
            runId = $"{Config.RunIdPrefix}-{runSequence:000000}";
            request = BuildOrchestratorRequest(runId);
        }

        Phase1IngestionOrchestratorResult orchestratorResult;
        try
        {
            orchestratorResult = orchestratorRunner(request);
        }
        finally
        {
            lock (syncRoot)
            {
                runInProgress = false;
                Status = shutdownRequested
                    ? Phase1ServiceHostStatus.Stopped
                    : Phase1ServiceHostStatus.Ready;
            }
        }

        return new Phase1ScheduledRunResult(
            Phase1ScheduledRunStatus.Started,
            runId,
            orchestratorResult);
    }

    public Phase1ServiceHostStatus RequestShutdown()
    {
        lock (syncRoot)
        {
            shutdownRequested = true;
            Status = runInProgress
                ? Phase1ServiceHostStatus.ShutdownRequested
                : Phase1ServiceHostStatus.Stopped;
            return Status;
        }
    }

    public static IReadOnlyList<Phase1ServiceHostIssue> ValidateConfig(
        Phase1ServiceHostConfig config)
    {
        var issues = new List<Phase1ServiceHostIssue>();

        if (config.SourceFamilies.Count == 0)
        {
            issues.Add(new Phase1ServiceHostIssue(
                "PHASE1_SERVICE_HOST_MISSING_SOURCE_FAMILIES",
                "At least one Phase 1 source family must be configured.",
                "source_families"));
        }

        for (var index = 0; index < config.SourceFamilies.Count; index++)
        {
            if (!Enum.IsDefined(config.SourceFamilies[index]))
            {
                issues.Add(new Phase1ServiceHostIssue(
                    "PHASE1_SERVICE_HOST_UNSUPPORTED_SOURCE_FAMILY",
                    "Configured source family must be a Phase 1 family.",
                    $"source_families[{index}]"));
            }
        }

        if (string.IsNullOrWhiteSpace(config.RunIdPrefix))
        {
            issues.Add(new Phase1ServiceHostIssue(
                "PHASE1_SERVICE_HOST_MISSING_RUN_ID_PREFIX",
                "run_id_prefix must be a non-empty string.",
                "run_id_prefix"));
        }

        if (config.ScheduleIntervalSeconds <= 0)
        {
            issues.Add(new Phase1ServiceHostIssue(
                "PHASE1_SERVICE_HOST_INVALID_SCHEDULE_INTERVAL",
                "schedule_interval_seconds must be a positive integer.",
                "schedule_interval_seconds"));
        }

        if (config.ExecutionMode == Phase1IngestionExecutionMode.Sequential)
        {
            if (config.MaxDegreeOfParallelism != 1)
            {
                issues.Add(new Phase1ServiceHostIssue(
                    "PHASE1_SERVICE_HOST_INVALID_SEQUENTIAL_PARALLELISM",
                    "Sequential scheduled execution requires MaxDegreeOfParallelism=1.",
                    "max_degree_of_parallelism"));
            }
        }
        else
        {
            issues.Add(new Phase1ServiceHostIssue(
                "PHASE1_SERVICE_HOST_UNSUPPORTED_EXECUTION_MODE",
                "Only sequential scheduled execution is enabled.",
                "execution_mode"));
        }

        foreach (var optionIssue in PostgreSQLPersistenceOptionsValidator.Validate(config.PostgreSQLOptions).Issues)
        {
            issues.Add(new Phase1ServiceHostIssue(
                optionIssue.Code,
                optionIssue.Message,
                $"postgresql_options.{optionIssue.FieldName}",
                optionIssue.Severity));
        }

        if (!config.PostgreSQLOptions.PasswordSet)
        {
            issues.Add(new Phase1ServiceHostIssue(
                "PHASE1_SERVICE_HOST_POSTGRESQL_PASSWORD_NOT_CONFIRMED",
                "postgresql_options.password_set must confirm that a credential is available outside this config object.",
                "postgresql_options.password_set"));
        }

        return Array.AsReadOnly(issues.ToArray());
    }

    private Phase1IngestionOrchestratorRequest BuildOrchestratorRequest(string runId) =>
        new(
            Config.SourceFamilies,
            Config.ExecutionMode,
            Config.MaxDegreeOfParallelism,
            Config.RuntimeConfigGate,
            runId);

    private static IEnumerable<Phase1ServiceHostIssue> SchemaBootstrapIssues(
        PostgreSQLSchemaBootstrapReport report)
    {
        if (!report.FailOnMissing || report.MissingTableNames.Count == 0)
        {
            yield break;
        }

        yield return new Phase1ServiceHostIssue(
            "PHASE1_SERVICE_HOST_POSTGRESQL_SCHEMA_NOT_READY",
            "Required Phase 1 PostgreSQL tables are missing.",
            "schema_bootstrap_report.missing_table_names");
    }

    private static PostgreSQLSchemaBootstrapReport DefaultSchemaBootstrapChecker(
        PostgreSQLSchemaBootstrapMode mode,
        bool failOnMissing) =>
        PostgreSQLSchemaBootstrapBoundary.BuildReport(mode, failOnMissing: failOnMissing);

    private static Phase1ServiceHostIssue ShutdownIssue() =>
        new(
            "PHASE1_SERVICE_HOST_SHUTTING_DOWN",
            "Scheduled trigger skipped because shutdown was requested.",
            "status");
}
