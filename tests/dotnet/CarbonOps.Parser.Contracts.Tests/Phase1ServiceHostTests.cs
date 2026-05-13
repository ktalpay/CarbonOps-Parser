using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class Phase1ServiceHostTests
{
    [Fact]
    public void ServiceHostValidatesRequiredPostgreSQLRuntimeConfig()
    {
        var config = new Phase1ServiceHostConfig(
            [SourceFamily.GhgProtocol],
            new PostgreSQLPersistenceOptions(
                "localhost",
                5432,
                "carbonops",
                "carbonops",
                PasswordSet: false));

        var issues = Phase1ScheduledIngestionServiceHost.ValidateConfig(config);

        Assert.Equal(
            ["PHASE1_SERVICE_HOST_POSTGRESQL_PASSWORD_NOT_CONFIRMED"],
            issues.Select(issue => issue.Code));
        Assert.Equal("postgresql_options.password_set", issues[0].FieldName);
    }

    [Fact]
    public void ServiceHostStartupChecksPhase1SchemaBeforeReady()
    {
        var checker = new FakeSchemaBootstrapChecker(present: false);
        var host = new Phase1ScheduledIngestionServiceHost(
            Config(),
            _ => throw new InvalidOperationException("orchestrator should not run"),
            checker.Check);

        var result = host.Start();

        Assert.Equal(Phase1ServiceHostStatus.Blocked, result.Status);
        Assert.Equal(Phase1ServiceHostStatus.Blocked, host.Status);
        var call = Assert.Single(checker.Calls);
        Assert.Equal(PostgreSQLSchemaBootstrapMode.CheckOnly, call.Mode);
        Assert.True(call.FailOnMissing);
        Assert.NotNull(result.SchemaBootstrapReport);
        Assert.NotEmpty(result.SchemaBootstrapReport.MissingTableNames);
        Assert.Equal("PHASE1_SERVICE_HOST_POSTGRESQL_SCHEMA_NOT_READY", result.Issues[0].Code);
        Assert.True(result.SchemaBootstrapReport.NoExecution);
        Assert.False(result.SchemaBootstrapReport.OpensConnection);
        Assert.False(result.SchemaBootstrapReport.RunsSql);
    }

    [Fact]
    public void ScheduledTriggerRunsOrchestratorForSelectedSourceFamilies()
    {
        var runner = new FakeOrchestratorRunner();
        var host = new Phase1ScheduledIngestionServiceHost(
            Config(
                sourceFamilies: [SourceFamily.DefraDesnz, SourceFamily.IpccEfdb],
                runIdPrefix: "phase1-test"),
            runner.Run,
            new FakeSchemaBootstrapChecker(present: true).Check);

        var startup = host.Start();
        var result = host.TriggerScheduledRun();

        Assert.True(startup.IsReady);
        Assert.Equal(Phase1ScheduledRunStatus.Started, result.Status);
        Assert.Equal("phase1-test-000001", result.RunId);
        Assert.Equal([SourceFamily.DefraDesnz, SourceFamily.IpccEfdb], runner.Requests[0].SourceFamilies);
        Assert.NotNull(runner.Requests[0].SchemaBootstrapReport);
        Assert.Empty(runner.Requests[0].SchemaBootstrapReport.MissingTableNames);
        Assert.Equal(Phase1IngestionRunStatus.Completed, result.OrchestratorResult?.Status);
        Assert.Equal(Phase1ServiceHostStatus.Ready, host.Status);
    }

    [Fact]
    public void ScheduledTriggerSkipsOverlappingRun()
    {
        Phase1ScheduledIngestionServiceHost? host = null;
        Phase1ScheduledRunResult? nestedResult = null;

        Phase1IngestionOrchestratorResult Runner(Phase1IngestionOrchestratorRequest request)
        {
            nestedResult = host!.TriggerScheduledRun();
            return OrchestratorResult(request);
        }

        host = new Phase1ScheduledIngestionServiceHost(
            Config(),
            Runner,
            new FakeSchemaBootstrapChecker(present: true).Check);

        host.Start();
        var result = host.TriggerScheduledRun();

        Assert.Equal(Phase1ScheduledRunStatus.Started, result.Status);
        Assert.NotNull(nestedResult);
        Assert.Equal(Phase1ScheduledRunStatus.SkippedAlreadyRunning, nestedResult.Status);
        Assert.Equal("PHASE1_SERVICE_HOST_RUN_ALREADY_IN_PROGRESS", nestedResult.Issues[0].Code);
        Assert.Equal(Phase1ServiceHostStatus.Ready, host.Status);
    }

    [Fact]
    public void GracefulShutdownBlocksNewRunsAndStopsAfterActiveRun()
    {
        Phase1ScheduledIngestionServiceHost? host = null;
        Phase1ServiceHostStatus? shutdownStatus = null;
        Phase1ScheduledRunResult? nestedResult = null;

        Phase1IngestionOrchestratorResult Runner(Phase1IngestionOrchestratorRequest request)
        {
            shutdownStatus = host!.RequestShutdown();
            nestedResult = host.TriggerScheduledRun();
            return OrchestratorResult(request);
        }

        host = new Phase1ScheduledIngestionServiceHost(
            Config(),
            Runner,
            new FakeSchemaBootstrapChecker(present: true).Check);

        host.Start();
        var result = host.TriggerScheduledRun();
        var afterShutdownResult = host.TriggerScheduledRun();

        Assert.Equal(Phase1ScheduledRunStatus.Started, result.Status);
        Assert.Equal(Phase1ServiceHostStatus.ShutdownRequested, shutdownStatus);
        Assert.NotNull(nestedResult);
        Assert.Equal(Phase1ScheduledRunStatus.SkippedShuttingDown, nestedResult.Status);
        Assert.Equal(Phase1ServiceHostStatus.Stopped, host.Status);
        Assert.Equal(Phase1ScheduledRunStatus.SkippedShuttingDown, afterShutdownResult.Status);
    }

    [Fact]
    public void ScheduledRunnerErrorReleasesOverlapGuardAndReturnsReady()
    {
        var failedOnce = false;
        var host = new Phase1ScheduledIngestionServiceHost(
            Config(),
            request =>
            {
                if (!failedOnce)
                {
                    failedOnce = true;
                    throw new InvalidOperationException($"boom: {request.RunId}");
                }

                return OrchestratorResult(request);
            },
            new FakeSchemaBootstrapChecker(present: true).Check);

        host.Start();
        var exception = Assert.Throws<InvalidOperationException>(() => host.TriggerScheduledRun());

        Assert.Equal("boom: phase1-scheduled-000001", exception.Message);
        Assert.Equal(Phase1ServiceHostStatus.Ready, host.Status);
        var followUp = host.TriggerScheduledRun();
        Assert.Equal(Phase1ScheduledRunStatus.Started, followUp.Status);
        Assert.Equal("phase1-scheduled-000002", followUp.RunId);
    }

    private static Phase1ServiceHostConfig Config(
        SourceFamily[]? sourceFamilies = null,
        string runIdPrefix = "phase1-scheduled") =>
        new(
            sourceFamilies ?? [SourceFamily.GhgProtocol],
            new PostgreSQLPersistenceOptions(
                "localhost",
                5432,
                "carbonops",
                "carbonops",
                PasswordSet: true),
            runIdPrefix);

    private static Phase1IngestionOrchestratorResult OrchestratorResult(
        Phase1IngestionOrchestratorRequest request) =>
        new(
            request,
            PostgreSQLRuntimeConfigGateEvaluator.Evaluate(request.RuntimeConfigGate),
            [],
            status: Phase1IngestionRunStatus.Completed,
            selectedSourceFamilies: request.SourceFamilies);

    private sealed class FakeSchemaBootstrapChecker(bool present)
    {
        private readonly List<(PostgreSQLSchemaBootstrapMode Mode, bool FailOnMissing)> calls = [];

        public IReadOnlyList<(PostgreSQLSchemaBootstrapMode Mode, bool FailOnMissing)> Calls => calls;

        public PostgreSQLSchemaBootstrapReport Check(
            PostgreSQLSchemaBootstrapMode mode,
            bool failOnMissing)
        {
            calls.Add((mode, failOnMissing));
            return PostgreSQLSchemaBootstrapBoundary.BuildReport(
                mode,
                presentTableNames: present
                    ? PostgreSQLSchemaBootstrapBoundary.RequiredPhase1TableNames
                    : [],
                failOnMissing: failOnMissing);
        }
    }

    private sealed class FakeOrchestratorRunner
    {
        private readonly List<Phase1IngestionOrchestratorRequest> requests = [];

        public IReadOnlyList<Phase1IngestionOrchestratorRequest> Requests => requests;

        public Phase1IngestionOrchestratorResult Run(
            Phase1IngestionOrchestratorRequest request)
        {
            requests.Add(request);
            return OrchestratorResult(request);
        }
    }
}
