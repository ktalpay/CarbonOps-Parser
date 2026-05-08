using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class Phase1OrchestrationPlanContractTests
{
    [Fact]
    public void ValidPhaseOneOrchestrationPlansCanBeConstructedForPhaseOneSources()
    {
        var batch = Phase1OrchestrationPlanRegistry.CreateDefaultPlanBatch();

        Assert.Equal(3, batch.PlanCount);
        Assert.Equal(
            [
                SourceFamily.GhgProtocol,
                SourceFamily.DefraDesnz,
                SourceFamily.IpccEfdb,
            ],
            batch.Plans.Select(plan => plan.SourceFamily));
        Assert.All(batch.Plans, plan => Assert.True(plan.Validate().IsValid));
    }

    [Fact]
    public void SourceKeysRemainConsistentAcrossAcquisitionParserPlanParserRunAndDryRunMetadata()
    {
        var plans = Phase1OrchestrationPlanRegistry.CreateDefaultPlanBatch().Plans;

        foreach (var plan in plans)
        {
            Assert.Equal(plan.SourceKey, plan.AcquisitionRequest.SourceKey);
            Assert.Equal(plan.SourceKey, plan.AcquisitionResult.SourceKey);
            Assert.Equal(plan.SourceKey, plan.AcquisitionToParserPlan.SourceKey);
            Assert.All(plan.ParserRunRequests, request => Assert.Equal(plan.SourceKey, request.SourceKey));
            Assert.All(plan.DryRunPlans, dryRunPlan => Assert.Equal(plan.SourceKey, dryRunPlan.SourceKey));
            Assert.All(plan.DryRunResults, dryRunResult => Assert.Equal(plan.SourceKey, dryRunResult.SourceKey));
            Assert.All(plan.PlanIssues, issue => Assert.Equal(plan.SourceKey, issue.SourceKey));
        }
    }

    [Fact]
    public void PlanStatusValuesAreConstrainedToDeterministicAllowedValues()
    {
        Assert.Equal(
            [
                Phase1OrchestrationPlanStatus.Planned,
                Phase1OrchestrationPlanStatus.InvalidMetadata,
                Phase1OrchestrationPlanStatus.ExecutionNotImplemented,
            ],
            Enum.GetValues<Phase1OrchestrationPlanStatus>());

        var plan = Phase1OrchestrationPlanRegistry.CreateDefaultPlanBatch().Plans[0];
        var invalid = new Phase1OrchestrationPlan(
            plan.SourceFamily,
            plan.SourceKey,
            plan.AcquisitionRequest,
            plan.AcquisitionResult,
            plan.AcquisitionToParserPlan,
            plan.ParserRunRequests,
            plan.DryRunPlans,
            plan.DryRunResults,
            plan.PlanIssues,
            (Phase1OrchestrationPlanStatus)999,
            plan.OrchestrationPlanId,
            plan.CorrelationId);

        var result = invalid.Validate();

        Assert.False(result.IsValid);
        Assert.Contains(
            "Phase1OrchestrationPlanStatus must be a defined Phase 1 orchestration plan status.",
            result.Errors);
    }

    [Fact]
    public void RequiredMetadataFieldsRejectEmptyStrings()
    {
        var plan = Phase1OrchestrationPlanRegistry.CreateDefaultPlanBatch().Plans[0];
        var invalid = new Phase1OrchestrationPlan(
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
            orchestrationPlanId: " ",
            correlationId: "");

        var result = invalid.Validate();

        Assert.False(result.IsValid);
        Assert.Contains("SourceKey is required.", result.Errors);
        Assert.Contains("OrchestrationPlanId must not be whitespace when provided.", result.Errors);
        Assert.Contains("CorrelationId must not be whitespace when provided.", result.Errors);
    }

    [Fact]
    public void SummaryCountsAreDeterministic()
    {
        var plans = Phase1OrchestrationPlanRegistry.CreateDefaultPlanBatch().Plans;

        Assert.Equal([1, 1, 1], plans.Select(plan => plan.SourceCandidateCount));
        Assert.Equal([1, 1, 1], plans.Select(plan => plan.DownloadedArtifactCount));
        Assert.Equal([1, 1, 1], plans.Select(plan => plan.ParserInputArtifactCount));
        Assert.Equal([1, 1, 1], plans.Select(plan => plan.ParserRunRequestCount));
        Assert.Equal([1, 1, 1], plans.Select(plan => plan.DryRunPlanCount));
        Assert.Equal([1, 1, 1], plans.Select(plan => plan.DryRunResultCount));
        Assert.Equal([1, 1, 1], plans.Select(plan => plan.StructurallyExecutableDryRunCount));
        Assert.Equal([0, 0, 0], plans.Select(plan => plan.ExecutionImplementedDryRunCount));
        Assert.Equal([1, 1, 1], plans.Select(plan => plan.PlanIssueCount));
    }

    [Fact]
    public void PlanStatusesReflectDryRunExecutionReadiness()
    {
        var plans = Phase1OrchestrationPlanRegistry.CreateDefaultPlanBatch().Plans;

        Assert.All(plans, plan =>
        {
            Assert.Equal(Phase1OrchestrationPlanStatus.ExecutionNotImplemented, plan.Status);
            Assert.All(plan.DryRunPlans, dryRunPlan =>
            {
                Assert.Equal(ParserDryRunStatus.ExecutionNotImplemented, dryRunPlan.Status);
                Assert.True(dryRunPlan.IsStructurallyExecutable);
                Assert.False(dryRunPlan.IsExecutionImplemented);
            });
        });
    }

    [Fact]
    public void OrderingIsDeterministic()
    {
        var first = Phase1OrchestrationPlanRegistry.CreateDefaultPlanBatch();
        var second = Phase1OrchestrationPlanRegistry.CreateDefaultPlanBatch();

        Assert.NotSame(first, second);
        Assert.NotSame(first.Plans, second.Plans);
        Assert.Equal(
            first.Plans.Select(plan => (plan.SourceKey, plan.OrchestrationPlanId, plan.Status)),
            second.Plans.Select(plan => (plan.SourceKey, plan.OrchestrationPlanId, plan.Status)));
        Assert.Equal(
            ParserAdapterDescriptorRegistry.Descriptors.Select(descriptor => descriptor.SourceFamily),
            first.Plans.Select(plan => plan.SourceFamily));
    }

    [Fact]
    public void PlanBatchSnapshotsPlans()
    {
        var plans = new List<Phase1OrchestrationPlan>
        {
            Phase1OrchestrationPlanRegistry.CreateDefaultPlanBatch().Plans[0],
        };

        var batch = new Phase1OrchestrationPlanBatch(plans);
        plans.Clear();

        Assert.Equal(1, batch.PlanCount);
        Assert.Single(batch.Plans);
        Assert.Equal(SourceFamily.GhgProtocol, batch.Plans[0].SourceFamily);
    }

    [Fact]
    public void ValidationDoesNotPerformNetworkFileIoDbContentInspectionDownloaderOrParserExecution()
    {
        var request = CreateSingleCandidateAcquisitionRequest(SourceFamily.DefraDesnz, "https://example.invalid/defra-desnz/factors.csv");
        var result = CreateSingleArtifactAcquisitionResult(
            SourceFamily.DefraDesnz,
            "/definitely/not-present/defra-desnz.csv",
            "https://example.invalid/defra-desnz/factors.csv");

        var plan = Phase1OrchestrationPlanRegistry.CreatePlan(request, result);

        Assert.True(plan.Validate().IsValid);
        Assert.Equal("/definitely/not-present/defra-desnz.csv", plan.ParserRunRequests[0].Artifacts[0].ArtifactReference);
        Assert.Equal("https://example.invalid/defra-desnz/factors.csv", plan.AcquisitionResult.Artifacts[0].SourceReference);
    }

    [Fact]
    public void DivergentMetadataFailsClearly()
    {
        var plan = Phase1OrchestrationPlanRegistry.CreateDefaultPlanBatch().Plans[0];
        var invalidRequest = new ParserAdapterRunRequest(
            SourceFamily.DefraDesnz,
            SourceFamily.DefraDesnz.ToWireName(),
            ParserAdapterDescriptorRegistry.Descriptors[1].ParserKey,
            plan.ParserRunRequests[0].Artifacts);
        var invalid = new Phase1OrchestrationPlan(
            plan.SourceFamily,
            plan.SourceKey,
            plan.AcquisitionRequest,
            plan.AcquisitionResult,
            plan.AcquisitionToParserPlan,
            [invalidRequest],
            plan.DryRunPlans,
            plan.DryRunResults,
            plan.PlanIssues,
            plan.Status,
            plan.OrchestrationPlanId,
            plan.CorrelationId);

        var result = invalid.Validate();

        Assert.False(result.IsValid);
        Assert.Contains("ParserRunRequests[0].SourceFamily must match orchestration plan SourceFamily.", result.Errors);
        Assert.Contains("ParserRunRequests[0].SourceKey must match orchestration plan SourceKey.", result.Errors);
    }

    [Fact]
    public void ConstructionRemainsRuntimePassive()
    {
        var planMethods = typeof(Phase1OrchestrationPlan)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Where(method => !method.Name.StartsWith("get_", StringComparison.Ordinal))
            .Select(method => method.Name)
            .ToArray();
        var batchMethods = typeof(Phase1OrchestrationPlanBatch)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Where(method => !method.Name.StartsWith("get_", StringComparison.Ordinal))
            .Select(method => method.Name)
            .ToArray();
        var registryMethods = typeof(Phase1OrchestrationPlanRegistry)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();

        Assert.DoesNotContain("Fetch", planMethods);
        Assert.DoesNotContain("Parse", planMethods);
        Assert.DoesNotContain("Execute", planMethods);
        Assert.DoesNotContain("Schedule", planMethods);
        Assert.DoesNotContain("Fetch", batchMethods);
        Assert.DoesNotContain("Parse", batchMethods);
        Assert.DoesNotContain("Execute", batchMethods);
        Assert.DoesNotContain("Schedule", batchMethods);
        Assert.Equal(["CreateDefaultPlanBatch", "CreatePlanBatch", "CreatePlan"], registryMethods);
    }

    [Fact]
    public void ContractDoesNotIntroduceDbHttpFileIoParserDownloaderSchedulerOrPersistenceSurface()
    {
        var publicMembers = typeof(Phase1OrchestrationPlan)
            .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Concat(typeof(Phase1OrchestrationPlanBatch)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Concat(typeof(Phase1OrchestrationPlanRegistry)
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

        Assert.DoesNotContain("Parse", publicMembers);
        Assert.DoesNotContain("Execute", publicMembers);
        Assert.DoesNotContain("Schedule", publicMembers);
    }

    private static SourceAcquisitionRunRequest CreateSingleCandidateAcquisitionRequest(
        SourceFamily sourceFamily,
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

        return new SourceAcquisitionRunRequest(
            sourceFamily,
            sourceKey,
            [candidate],
            runId: $"{sourceKey}_source_acquisition_run");
    }

    private static SourceAcquisitionRunResult CreateSingleArtifactAcquisitionResult(
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

        return new SourceAcquisitionRunResult(
            sourceFamily,
            sourceKey,
            SourceAcquisitionRunStatus.Planned,
            [candidate],
            [artifact],
            runId: $"{sourceKey}_source_acquisition_run");
    }
}
