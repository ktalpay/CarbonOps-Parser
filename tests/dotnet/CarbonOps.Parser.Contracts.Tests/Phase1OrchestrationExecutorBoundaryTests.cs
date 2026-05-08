using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class Phase1OrchestrationExecutorBoundaryTests
{
    [Fact]
    public void ExecutorBoundaryResultsCanBeConstructedForPhaseOneSources()
    {
        var batch = Phase1OrchestrationExecutorBoundary.CreateDefaultResultBatch();

        Assert.Equal(3, batch.ResultCount);
        Assert.Equal(
            [
                SourceFamily.GhgProtocol,
                SourceFamily.DefraDesnz,
                SourceFamily.IpccEfdb,
            ],
            batch.Results.Select(result => result.SourceFamily));
        Assert.All(batch.Results, result => Assert.True(result.Validate().IsValid));
    }

    [Fact]
    public void ExecutorStatusValuesAreConstrainedToDeterministicAllowedValues()
    {
        Assert.Equal(
            [
                Phase1OrchestrationExecutorStatus.Planned,
                Phase1OrchestrationExecutorStatus.NotExecutable,
                Phase1OrchestrationExecutorStatus.NotImplemented,
                Phase1OrchestrationExecutorStatus.InvalidPlan,
            ],
            Enum.GetValues<Phase1OrchestrationExecutorStatus>());

        var result = Phase1OrchestrationExecutorBoundary.CreateDefaultResultBatch().Results[0];
        var invalid = new Phase1OrchestrationExecutorResult(
            result.SourceFamily,
            result.SourceKey,
            result.Plan,
            (Phase1OrchestrationExecutorStatus)999,
            result.ReadinessReason,
            result.PlanIssues,
            result.ExecutorRequestId,
            result.CorrelationId);

        var validation = invalid.Validate();

        Assert.False(validation.IsValid);
        Assert.Contains(
            "Phase1OrchestrationExecutorStatus must be a defined Phase 1 orchestration executor status.",
            validation.Errors);
    }

    [Fact]
    public void ExecutorBoundaryConsumesPhaseOneOrchestrationPlanMetadata()
    {
        var plan = Phase1OrchestrationPlanRegistry.CreateDefaultPlanBatch().Plans[0];
        var request = Phase1OrchestrationExecutorBoundary.CreateRequest(plan);
        var result = Phase1OrchestrationExecutorBoundary.CreateResult(request);

        Assert.Equal(plan, request.Plan);
        Assert.Equal(plan, result.Plan);
        Assert.Equal(plan.OrchestrationPlanId, request.OrchestrationPlanId);
        Assert.Equal(plan.OrchestrationPlanId, result.OrchestrationPlanId);
        Assert.Equal("ghg_protocol_phase1_executor_request", request.ExecutorRequestId);
        Assert.Equal(request.ExecutorRequestId, result.ExecutorRequestId);
    }

    [Fact]
    public void SourceKeysRemainConsistent()
    {
        var results = Phase1OrchestrationExecutorBoundary.CreateDefaultResultBatch().Results;

        foreach (var result in results)
        {
            Assert.Equal(result.SourceKey, result.Plan.SourceKey);
            Assert.Equal(result.SourceKey, result.Plan.AcquisitionResult.SourceKey);
            Assert.All(result.Plan.ParserRunRequests, request => Assert.Equal(result.SourceKey, request.SourceKey));
            Assert.All(result.Plan.DryRunPlans, dryRunPlan => Assert.Equal(result.SourceKey, dryRunPlan.SourceKey));
            Assert.All(result.PlanIssues, issue => Assert.Equal(result.SourceKey, issue.SourceKey));
        }
    }

    [Fact]
    public void SummaryCountsAreDeterministic()
    {
        var results = Phase1OrchestrationExecutorBoundary.CreateDefaultResultBatch().Results;

        Assert.Equal([1, 1, 1], results.Select(result => result.SourceCandidateCount));
        Assert.Equal([1, 1, 1], results.Select(result => result.DownloadedArtifactCount));
        Assert.Equal([1, 1, 1], results.Select(result => result.ParserInputArtifactCount));
        Assert.Equal([1, 1, 1], results.Select(result => result.ParserRunRequestCount));
        Assert.Equal([1, 1, 1], results.Select(result => result.DryRunPlanCount));
        Assert.Equal([1, 1, 1], results.Select(result => result.DryRunResultCount));
        Assert.Equal([1, 1, 1], results.Select(result => result.StructurallyExecutableDryRunCount));
        Assert.Equal([0, 0, 0], results.Select(result => result.ExecutionImplementedDryRunCount));
        Assert.Equal([1, 1, 1], results.Select(result => result.PlanIssueCount));
    }

    [Fact]
    public void OrderingIsDeterministic()
    {
        var first = Phase1OrchestrationExecutorBoundary.CreateDefaultResultBatch();
        var second = Phase1OrchestrationExecutorBoundary.CreateDefaultResultBatch();

        Assert.NotSame(first, second);
        Assert.NotSame(first.Results, second.Results);
        Assert.Equal(
            first.Results.Select(result => (result.SourceKey, result.ExecutorRequestId, result.Status)),
            second.Results.Select(result => (result.SourceKey, result.ExecutorRequestId, result.Status)));
        Assert.Equal(
            ParserAdapterDescriptorRegistry.Descriptors.Select(descriptor => descriptor.SourceFamily),
            first.Results.Select(result => result.SourceFamily));
    }

    [Fact]
    public void ResultBatchSnapshotsResults()
    {
        var results = new List<Phase1OrchestrationExecutorResult>
        {
            Phase1OrchestrationExecutorBoundary.CreateDefaultResultBatch().Results[0],
        };

        var batch = new Phase1OrchestrationExecutorResultBatch(results);
        results.Clear();

        Assert.Equal(1, batch.ResultCount);
        Assert.Single(batch.Results);
        Assert.Equal(SourceFamily.GhgProtocol, batch.Results[0].SourceFamily);
    }

    [Fact]
    public void ExecutorReportsNotImplementedWithoutRuntimeWork()
    {
        var results = Phase1OrchestrationExecutorBoundary.CreateDefaultResultBatch().Results;

        Assert.All(results, result =>
        {
            Assert.Equal(Phase1OrchestrationExecutorStatus.NotImplemented, result.Status);
            Assert.Equal(
                "Phase 1 orchestration execution is not implemented; boundary is metadata-only.",
                result.ReadinessReason);
            Assert.Equal(Phase1OrchestrationPlanStatus.ExecutionNotImplemented, result.Plan.Status);
        });
    }

    [Fact]
    public void ExecutorReportsInvalidPlanForStructurallyInvalidMetadata()
    {
        var plan = Phase1OrchestrationPlanRegistry.CreateDefaultPlanBatch().Plans[0];
        var invalidPlan = new Phase1OrchestrationPlan(
            plan.SourceFamily,
            "",
            plan.AcquisitionRequest,
            plan.AcquisitionResult,
            plan.AcquisitionToParserPlan,
            plan.ParserRunRequests,
            plan.DryRunPlans,
            plan.DryRunResults,
            plan.PlanIssues,
            plan.Status,
            orchestrationPlanId: "",
            plan.CorrelationId);
        var request = new Phase1OrchestrationExecutorRequest(
            invalidPlan.SourceFamily,
            invalidPlan.SourceKey,
            invalidPlan,
            executorRequestId: " ");

        var result = Phase1OrchestrationExecutorBoundary.CreateResult(request);

        Assert.Equal(Phase1OrchestrationExecutorStatus.InvalidPlan, result.Status);
        Assert.StartsWith("Phase 1 orchestration plan is invalid:", result.ReadinessReason, StringComparison.Ordinal);
        Assert.False(result.Validate().IsValid);
    }

    [Fact]
    public void ValidationDoesNotPerformNetworkCallsFileIoDbContentInspectionDownloaderSchedulerOrParserExecution()
    {
        var plan = CreatePlanWithPassiveReferences(
            SourceFamily.DefraDesnz,
            "/definitely/not-present/defra-desnz.csv",
            "https://example.invalid/defra-desnz/factors.csv");
        var request = Phase1OrchestrationExecutorBoundary.CreateRequest(plan);
        var result = Phase1OrchestrationExecutorBoundary.CreateResult(request);

        Assert.True(result.Validate().IsValid);
        Assert.Equal("https://example.invalid/defra-desnz/factors.csv", result.Plan.AcquisitionResult.Artifacts[0].SourceReference);
        Assert.Equal("/definitely/not-present/defra-desnz.csv", result.Plan.ParserRunRequests[0].Artifacts[0].ArtifactReference);
    }

    [Fact]
    public void ConstructionRemainsRuntimePassive()
    {
        var requestMethods = typeof(Phase1OrchestrationExecutorRequest)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Where(method => !method.Name.StartsWith("get_", StringComparison.Ordinal))
            .Select(method => method.Name)
            .ToArray();
        var resultMethods = typeof(Phase1OrchestrationExecutorResult)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Where(method => !method.Name.StartsWith("get_", StringComparison.Ordinal))
            .Select(method => method.Name)
            .ToArray();
        var boundaryMethods = typeof(Phase1OrchestrationExecutorBoundary)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();

        Assert.DoesNotContain("Execute", requestMethods);
        Assert.DoesNotContain("Fetch", requestMethods);
        Assert.DoesNotContain("Parse", requestMethods);
        Assert.DoesNotContain("Schedule", requestMethods);
        Assert.DoesNotContain("Execute", resultMethods);
        Assert.DoesNotContain("Fetch", resultMethods);
        Assert.DoesNotContain("Parse", resultMethods);
        Assert.DoesNotContain("Schedule", resultMethods);
        Assert.Equal(["CreateDefaultResultBatch", "CreateResultBatch", "CreateRequest", "CreateResult"], boundaryMethods);
    }

    [Fact]
    public void ContractDoesNotIntroduceDbHttpFileIoParserDownloaderSchedulerOrPersistenceSurface()
    {
        var publicMembers = typeof(Phase1OrchestrationExecutorRequest)
            .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Concat(typeof(Phase1OrchestrationExecutorResult)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Concat(typeof(Phase1OrchestrationExecutorResultBatch)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Concat(typeof(Phase1OrchestrationExecutorBoundary)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly))
            .Select(member => member.Name)
            .ToArray();
        var blockedTerms = new[]
        {
            "Db",
            "Sql",
            "Postgres",
            "Http",
            "Open",
            "ReadFile",
            "Write",
            "StatFile",
            "Exists",
            "Fetch",
            "Calculate",
            "Factor",
            "Persist",
        };

        foreach (var term in blockedTerms)
        {
            Assert.DoesNotContain(publicMembers, member => member.Contains(term, StringComparison.OrdinalIgnoreCase));
        }

        Assert.DoesNotContain("Execute", publicMembers);
        Assert.DoesNotContain("Parse", publicMembers);
        Assert.DoesNotContain("Schedule", publicMembers);
    }

    private static Phase1OrchestrationPlan CreatePlanWithPassiveReferences(
        SourceFamily sourceFamily,
        string localReference,
        string sourceReference)
    {
        var sourceKey = sourceFamily.ToWireName();
        var candidate = new SourceDiscoveryCandidate(
            sourceFamily,
            sourceKey,
            $"{sourceKey}_candidate",
            $"{sourceKey} candidate",
            reportingYear: null,
            sourceReference,
            ParserSourceFormat.DiscoveryReference,
            "application/x-carbonops-discovery-reference");
        var request = new SourceAcquisitionRunRequest(
            sourceFamily,
            sourceKey,
            [candidate],
            runId: $"{sourceKey}_source_acquisition_run");
        var artifact = new SourceDownloadArtifact(
            sourceFamily,
            sourceKey,
            candidate.CandidateId,
            $"{sourceKey}_artifact",
            ParserSourceFormat.DiscoveryReference,
            sourceReference,
            localReference,
            $"{sourceKey} artifact",
            "application/x-carbonops-discovery-reference",
            checksum: new SourceDocumentChecksum("sha256", "abc123", IsDryRunPlaceholder: false));
        var result = new SourceAcquisitionRunResult(
            sourceFamily,
            sourceKey,
            SourceAcquisitionRunStatus.Planned,
            [candidate],
            [artifact],
            runId: request.RunId);

        return Phase1OrchestrationPlanRegistry.CreatePlan(request, result);
    }
}
