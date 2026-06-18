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
    private readonly Phase1OperationalEventSink? operationalEventSink;
    private PostgreSQLSchemaBootstrapReport? schemaBootstrapReport;
    private bool runInProgress;
    private bool shutdownRequested;
    private int runSequence;

    public Phase1ServiceHostConfig Config { get; }

    public Phase1ServiceHostStatus Status { get; private set; } = Phase1ServiceHostStatus.Created;

    public Phase1ScheduledIngestionServiceHost(
        Phase1ServiceHostConfig config,
        Phase1OrchestratorRunner orchestratorRunner,
        Phase1SchemaBootstrapChecker? schemaBootstrapChecker = null,
        Phase1OperationalEventSink? operationalEventSink = null)
    {
        Config = config;
        this.orchestratorRunner = orchestratorRunner;
        this.schemaBootstrapChecker = schemaBootstrapChecker ?? DefaultSchemaBootstrapChecker;
        this.operationalEventSink = operationalEventSink;
    }

    public Phase1ServiceHostStartupResult Start()
    {
        Phase1OperationalDiagnostics.Emit(
            operationalEventSink,
            "phase1_service_host_starting",
            StartingDiagnosticPayload(Config));

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
                var blockedResult = new Phase1ServiceHostStartupResult(
                    Phase1ServiceHostStatus.Blocked,
                    [
                        new Phase1ServiceHostIssue(
                            "PHASE1_SERVICE_HOST_SHUTDOWN_REQUESTED",
                            "Service host startup is blocked after shutdown.",
                            "status"),
                    ],
                    report);
                Phase1OperationalDiagnostics.Emit(
                    operationalEventSink,
                    "phase1_service_host_started",
                    StartupDiagnosticPayload(blockedResult));
                return blockedResult;
            }

            Status = status;
            schemaBootstrapReport = report;
        }

        Phase1OperationalDiagnostics.Emit(
            operationalEventSink,
            "phase1_service_host_started",
            StartupDiagnosticPayload(result));
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
                var result = new Phase1ScheduledRunResult(
                    Phase1ScheduledRunStatus.SkippedShuttingDown,
                    issues: [ShutdownIssue()]);
                Phase1OperationalDiagnostics.Emit(
                    operationalEventSink,
                    "phase1_service_host_scheduled_run_skipped",
                    ScheduledRunDiagnosticPayload(result));
                return result;
            }

            if (runInProgress)
            {
                var result = new Phase1ScheduledRunResult(
                    Phase1ScheduledRunStatus.SkippedAlreadyRunning,
                    issues:
                    [
                        new Phase1ServiceHostIssue(
                            "PHASE1_SERVICE_HOST_RUN_ALREADY_IN_PROGRESS",
                            "Scheduled trigger skipped while a run is active.",
                            "run_in_progress"),
                    ]);
                Phase1OperationalDiagnostics.Emit(
                    operationalEventSink,
                    "phase1_service_host_scheduled_run_skipped",
                    ScheduledRunDiagnosticPayload(result));
                return result;
            }

            if (Status != Phase1ServiceHostStatus.Ready)
            {
                var result = new Phase1ScheduledRunResult(
                    Phase1ScheduledRunStatus.SkippedNotStarted,
                    issues:
                    [
                        new Phase1ServiceHostIssue(
                            "PHASE1_SERVICE_HOST_NOT_READY",
                            "Service host must start successfully first.",
                            "status"),
                    ]);
                Phase1OperationalDiagnostics.Emit(
                    operationalEventSink,
                    "phase1_service_host_scheduled_run_skipped",
                    ScheduledRunDiagnosticPayload(result));
                return result;
            }

            runInProgress = true;
            Status = Phase1ServiceHostStatus.Running;
            runSequence++;
            runId = $"{Config.RunIdPrefix}-{runSequence:000000}";
            request = BuildOrchestratorRequest(runId);
        }

        Phase1OperationalDiagnostics.Emit(
            operationalEventSink,
            "phase1_service_host_scheduled_run_started",
            new SortedDictionary<string, object?>(StringComparer.Ordinal)
            {
                ["correlation_id"] = request.CorrelationId,
                ["run_id"] = runId,
                ["source_families"] = request.SourceFamilies.Select(sourceFamily => sourceFamily.ToWireName()).ToArray(),
            });

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

        var scheduledRunResult = new Phase1ScheduledRunResult(
            Phase1ScheduledRunStatus.Started,
            runId,
            orchestratorResult);
        Phase1OperationalDiagnostics.Emit(
            operationalEventSink,
            "phase1_service_host_scheduled_run_completed",
            ScheduledRunDiagnosticPayload(scheduledRunResult));
        return scheduledRunResult;
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
            runId,
            schemaBootstrapReport: schemaBootstrapReport,
            operationalEventSink: operationalEventSink);

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

    private static IReadOnlyDictionary<string, object?> StartingDiagnosticPayload(
        Phase1ServiceHostConfig config) =>
        new SortedDictionary<string, object?>(StringComparer.Ordinal)
        {
            ["postgresql_options"] = Phase1OperationalDiagnostics.SummarizePostgreSQLOptionsForDiagnostics(
                config.PostgreSQLOptions),
            ["run_id_prefix"] = config.RunIdPrefix,
            ["schedule_interval_seconds"] = config.ScheduleIntervalSeconds,
            ["source_families"] = config.SourceFamilies.Select(sourceFamily => sourceFamily.ToWireName()).ToArray(),
        };

    private static IReadOnlyDictionary<string, object?> StartupDiagnosticPayload(
        Phase1ServiceHostStartupResult result)
    {
        var report = result.SchemaBootstrapReport;
        return new SortedDictionary<string, object?>(StringComparer.Ordinal)
        {
            ["issues"] = result.Issues.Select(ServiceHostIssuePayload).ToArray(),
            ["schema_bootstrap"] = new SortedDictionary<string, object?>(StringComparer.Ordinal)
            {
                ["fail_on_missing"] = report?.FailOnMissing,
                ["missing_table_count"] = report?.MissingTableNames.Count,
                ["mode"] = report is null ? null : SchemaBootstrapModeWireName(report.Mode),
                ["status"] = null,
            },
            ["status"] = ServiceHostStatusWireName(result.Status),
        };
    }

    private static IReadOnlyDictionary<string, object?> ScheduledRunDiagnosticPayload(
        Phase1ScheduledRunResult result)
    {
        var payload = new SortedDictionary<string, object?>(StringComparer.Ordinal)
        {
            ["issues"] = result.Issues.Select(ServiceHostIssuePayload).ToArray(),
            ["run_id"] = result.RunId,
            ["status"] = ScheduledRunStatusWireName(result.Status),
        };
        if (result.OrchestratorResult is not null)
        {
            payload["orchestrator"] = Phase1OperationalDiagnostics.SummarizeOrchestratorResultForDiagnostics(
                result.OrchestratorResult);
        }

        return payload;
    }

    private static IReadOnlyDictionary<string, object?> ServiceHostIssuePayload(
        Phase1ServiceHostIssue issue) =>
        new SortedDictionary<string, object?>(StringComparer.Ordinal)
        {
            ["code"] = issue.Code,
            ["field_name"] = issue.FieldName,
            ["message"] = issue.Message,
            ["severity"] = issue.Severity,
        };

    private static string ServiceHostStatusWireName(Phase1ServiceHostStatus status) =>
        status switch
        {
            Phase1ServiceHostStatus.Created => "created",
            Phase1ServiceHostStatus.Ready => "ready",
            Phase1ServiceHostStatus.Blocked => "blocked",
            Phase1ServiceHostStatus.Running => "running",
            Phase1ServiceHostStatus.ShutdownRequested => "shutdown_requested",
            Phase1ServiceHostStatus.Stopped => "stopped",
            _ => throw new ArgumentOutOfRangeException(nameof(status), status, "Unknown Phase 1 service host status."),
        };

    private static string ScheduledRunStatusWireName(Phase1ScheduledRunStatus status) =>
        status switch
        {
            Phase1ScheduledRunStatus.Started => "started",
            Phase1ScheduledRunStatus.SkippedNotStarted => "skipped_not_started",
            Phase1ScheduledRunStatus.SkippedAlreadyRunning => "skipped_already_running",
            Phase1ScheduledRunStatus.SkippedShuttingDown => "skipped_shutting_down",
            _ => throw new ArgumentOutOfRangeException(nameof(status), status, "Unknown Phase 1 scheduled run status."),
        };

    private static string SchemaBootstrapModeWireName(PostgreSQLSchemaBootstrapMode mode) =>
        mode switch
        {
            PostgreSQLSchemaBootstrapMode.CheckOnly => "check_only",
            PostgreSQLSchemaBootstrapMode.CreateMissing => "create_missing",
            _ => throw new ArgumentOutOfRangeException(nameof(mode), mode, "Unknown PostgreSQL schema bootstrap mode."),
        };
}
