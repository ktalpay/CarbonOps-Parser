using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class ParserDryRunBoundaryContractTests
{
    [Fact]
    public void DryRunBoundaryPlansCanBeConstructedForPhaseOneParserAdapters()
    {
        var batch = ParserDryRunBoundaryPlanner.CreateDefaultDryRunPlanBatch();

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
    public void DryRunBoundaryResultsCanBeConstructedForPhaseOneParserAdapters()
    {
        var batch = ParserDryRunBoundaryPlanner.CreateDefaultDryRunResultBatch();

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
    public void DryRunRequestMetadataAlignsWithDescriptorRegistrySourceAndParserKeys()
    {
        var plans = ParserDryRunBoundaryPlanner.CreateDefaultDryRunPlanBatch().Plans;

        foreach (var plan in plans)
        {
            Assert.True(ParserAdapterDescriptorRegistry.TryGetBySourceKey(plan.SourceKey, out var descriptor));
            Assert.NotNull(descriptor);
            Assert.Equal(descriptor!.SourceFamily, plan.SourceFamily);
            Assert.Equal(descriptor.ParserKey, plan.ParserKey);
            Assert.Equal(descriptor.SourceFamily, plan.Request.SourceFamily);
            Assert.Equal(descriptor.SourceFamily.ToWireName(), plan.Request.SourceKey);
            Assert.Equal(descriptor.ParserKey, plan.Request.ParserKey);
        }
    }

    [Fact]
    public void DryRunStatusValuesAreConstrainedToDeterministicAllowedSet()
    {
        Assert.Equal(
            [
                ParserDryRunStatus.Planned,
                ParserDryRunStatus.InvalidRequest,
                ParserDryRunStatus.ExecutionNotImplemented,
            ],
            Enum.GetValues<ParserDryRunStatus>());
        Assert.Equal("planned", ParserDryRunStatus.Planned.ToWireName());
        Assert.Equal("invalid_request", ParserDryRunStatus.InvalidRequest.ToWireName());
        Assert.Equal("execution_not_implemented", ParserDryRunStatus.ExecutionNotImplemented.ToWireName());
        Assert.True(ContractWireNames.TryParseParserDryRunStatusWireName("planned", out var planned));
        Assert.True(ContractWireNames.TryParseParserDryRunStatusWireName("invalid_request", out var invalid));
        Assert.True(
            ContractWireNames.TryParseParserDryRunStatusWireName(
                "execution_not_implemented",
                out var notImplemented));
        Assert.False(ContractWireNames.TryParseParserDryRunStatusWireName("running", out _));

        Assert.Equal(ParserDryRunStatus.Planned, planned);
        Assert.Equal(ParserDryRunStatus.InvalidRequest, invalid);
        Assert.Equal(ParserDryRunStatus.ExecutionNotImplemented, notImplemented);
        Assert.Throws<ArgumentOutOfRangeException>(() => ((ParserDryRunStatus)999).ToWireName());
    }

    [Fact]
    public void DefaultDryRunPlansUseDescriptorReadinessAndEligibilityMetadata()
    {
        var plans = ParserDryRunBoundaryPlanner.CreateDefaultDryRunPlanBatch().Plans;

        foreach (var plan in plans)
        {
            Assert.Equal(ParserDryRunStatus.ExecutionNotImplemented, plan.Status);
            Assert.Equal(ParserAdapterReadiness.ExecutionNotImplemented, plan.Readiness);
            Assert.False(plan.IsExecutionImplemented);
            Assert.True(plan.IsStructurallyExecutable);
            Assert.Equal(1, plan.IssueCount);
            Assert.Equal("PARSER_DRY_RUN_EXECUTION_NOT_IMPLEMENTED", plan.ValidationIssues[0].Code);
        }
    }

    [Fact]
    public void DryRunResultIncludesValidationIssuesUsingExistingValidationIssueContract()
    {
        var result = ParserDryRunBoundaryPlanner.CreateDefaultDryRunResultBatch().Results[0];

        Assert.Equal(1, result.IssueCount);
        Assert.Equal(result.ValidationIssues, result.RunResult.ValidationIssues);
        Assert.Equal(ParserValidationIssueSeverity.Info, result.ValidationIssues[0].Severity);
        Assert.True(result.ValidationIssues[0].Validate().IsValid);
    }

    [Fact]
    public void DryRunSummaryCountsAreDeterministic()
    {
        var plan = ParserDryRunBoundaryPlanner.CreateDefaultDryRunPlanBatch().Plans[0];
        var result = ParserDryRunBoundaryPlanner.CreateDefaultDryRunResultBatch().Results[0];

        Assert.Equal(plan.Request.ArtifactCount, plan.ArtifactCount);
        Assert.Equal(plan.ValidationIssues.Count, plan.IssueCount);
        Assert.Equal(result.Request.ArtifactCount, result.ArtifactCount);
        Assert.Equal(result.RunResult.RowCount, result.RowCount);
        Assert.Equal(result.ValidationIssues.Count, result.IssueCount);
        Assert.Equal(1, plan.ArtifactCount);
        Assert.Equal(1, plan.IssueCount);
        Assert.Equal(1, result.ArtifactCount);
        Assert.Equal(0, result.RowCount);
        Assert.Equal(1, result.IssueCount);
    }

    [Fact]
    public void DryRunOrderingIsDeterministic()
    {
        var firstPlans = ParserDryRunBoundaryPlanner.CreateDefaultDryRunPlanBatch();
        var secondPlans = ParserDryRunBoundaryPlanner.CreateDefaultDryRunPlanBatch();
        var firstResults = ParserDryRunBoundaryPlanner.CreateDefaultDryRunResultBatch();
        var secondResults = ParserDryRunBoundaryPlanner.CreateDefaultDryRunResultBatch();

        Assert.Equal(
            firstPlans.Plans.Select(plan => plan.SourceKey),
            secondPlans.Plans.Select(plan => plan.SourceKey));
        Assert.Equal(
            firstResults.Results.Select(result => result.SourceKey),
            secondResults.Results.Select(result => result.SourceKey));
        Assert.Equal(
            ParserAdapterDescriptorRegistry.Descriptors.Select(descriptor => descriptor.SourceFamily),
            firstPlans.Plans.Select(plan => plan.SourceFamily));
        Assert.Equal(
            ParserAdapterDescriptorRegistry.Descriptors.Select(descriptor => descriptor.SourceFamily),
            firstResults.Results.Select(result => result.SourceFamily));
    }

    [Fact]
    public void DryRunBatchesSnapshotCollections()
    {
        var plans = new List<ParserDryRunBoundaryPlan>
        {
            ParserDryRunBoundaryPlanner.CreateDefaultDryRunPlanBatch().Plans[0],
        };
        var results = new List<ParserDryRunBoundaryResult>
        {
            ParserDryRunBoundaryPlanner.CreateDefaultDryRunResultBatch().Results[0],
        };

        var planBatch = new ParserDryRunBoundaryPlanBatch(plans);
        var resultBatch = new ParserDryRunBoundaryResultBatch(results);
        plans.Clear();
        results.Clear();

        Assert.Equal(1, planBatch.PlanCount);
        Assert.Equal(1, resultBatch.ResultCount);
        Assert.Single(planBatch.Plans);
        Assert.Single(resultBatch.Results);
    }

    [Fact]
    public void DryRunPlanAndResultSnapshotIssues()
    {
        var plan = ParserDryRunBoundaryPlanner.CreateDefaultDryRunPlanBatch().Plans[0];
        var issues = new List<ParserValidationIssue>(plan.ValidationIssues);
        var copiedPlan = new ParserDryRunBoundaryPlan(
            plan.SourceFamily,
            plan.SourceKey,
            plan.ParserKey,
            plan.Request,
            plan.Status,
            plan.Readiness,
            plan.IsExecutionImplemented,
            plan.IsStructurallyExecutable,
            issues);
        var copiedResult = new ParserDryRunBoundaryResult(
            plan.SourceFamily,
            plan.SourceKey,
            plan.ParserKey,
            plan.Request,
            ParserDryRunBoundaryPlanner.CreateResult(plan).RunResult,
            plan.Status,
            plan.Readiness,
            plan.IsExecutionImplemented,
            plan.IsStructurallyExecutable,
            issues);
        issues.Clear();

        Assert.Equal(1, copiedPlan.IssueCount);
        Assert.Equal(1, copiedResult.IssueCount);
    }

    [Fact]
    public void DryRunPlannerReturnsInvalidPlanForUnknownSourceMetadata()
    {
        var descriptor = ParserAdapterDescriptorRegistry.Descriptors[0];
        var request = new ParserAdapterRunRequest(
            descriptor.SourceFamily,
            "unknown_source_family",
            descriptor.ParserKey,
            [
                ParserInputArtifactRegistry.CreateDefaultDryRunBatch().Artifacts[0],
            ]);

        var plan = ParserDryRunBoundaryPlanner.CreatePlan(request);

        Assert.Equal(ParserDryRunStatus.InvalidRequest, plan.Status);
        Assert.False(plan.IsStructurallyExecutable);
        Assert.Contains(
            plan.ValidationIssues,
            issue => issue.Message == "SourceKey must match a registered parser adapter descriptor.");
    }

    [Fact]
    public void DryRunPlannerReturnsInvalidPlanForDivergentParserMetadata()
    {
        var descriptor = ParserAdapterDescriptorRegistry.Descriptors[2];
        var request = new ParserAdapterRunRequest(
            descriptor.SourceFamily,
            descriptor.SourceFamily.ToWireName(),
            ParserSelectionRegistry.GetParserKey(SourceFamily.GhgProtocol),
            [
                ParserInputArtifactRegistry.CreateDefaultDryRunBatch().Artifacts[2],
            ]);

        var plan = ParserDryRunBoundaryPlanner.CreatePlan(request);

        Assert.Equal(ParserDryRunStatus.InvalidRequest, plan.Status);
        Assert.False(plan.IsStructurallyExecutable);
        Assert.Contains(
            plan.ValidationIssues,
            issue => issue.Message == "ParserKey must match the registered parser adapter descriptor.");
    }

    [Fact]
    public void ValidationDoesNotReadFilesInspectContentAccessDbOrCallNetwork()
    {
        var descriptor = ParserAdapterDescriptorRegistry.Descriptors[1];
        var artifact = new ParserInputArtifact(
            descriptor.SourceFamily,
            descriptor.SourceFamily.ToWireName(),
            descriptor.ParserKey,
            ParserSourceFormat.DiscoveryReference,
            "/definitely/not-present/defra-desnz-input.csv",
            "defra-desnz-input.csv",
            "sha256",
            "abc123",
            isDryRunChecksum: false,
            "text/csv",
            ".csv",
            2024);
        var request = new ParserAdapterRunRequest(
            descriptor.SourceFamily,
            descriptor.SourceFamily.ToWireName(),
            descriptor.ParserKey,
            [artifact],
            requestedReportingYear: 2024);

        var plan = ParserDryRunBoundaryPlanner.CreatePlan(request);
        var result = ParserDryRunBoundaryPlanner.CreateResult(plan);

        Assert.True(plan.Validate().IsValid);
        Assert.True(result.Validate().IsValid);
    }

    [Fact]
    public void DryRunPlannerDoesNotExposeParserExecutionOrImplementationConstructionSurface()
    {
        var plannerMethods = typeof(ParserDryRunBoundaryPlanner)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();

        Assert.Equal(
            [
                "CreateDefaultDryRunPlanBatch",
                "CreateDefaultDryRunResultBatch",
                "CreatePlan",
                "CreateResult",
            ],
            plannerMethods);
        Assert.DoesNotContain("Parse", plannerMethods);
        Assert.DoesNotContain("Execute", plannerMethods);
        Assert.DoesNotContain("Instantiate", plannerMethods);
    }

    [Fact]
    public void ConstructionRemainsRuntimePassive()
    {
        var planMethods = typeof(ParserDryRunBoundaryPlan)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Where(method => !method.Name.StartsWith("get_", StringComparison.Ordinal))
            .Select(method => method.Name)
            .ToArray();
        var resultMethods = typeof(ParserDryRunBoundaryResult)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Where(method => !method.Name.StartsWith("get_", StringComparison.Ordinal))
            .Select(method => method.Name)
            .ToArray();
        var plannerMethods = typeof(ParserDryRunBoundaryPlanner)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();

        Assert.DoesNotContain("Parse", planMethods);
        Assert.DoesNotContain("Execute", planMethods);
        Assert.DoesNotContain("Parse", resultMethods);
        Assert.DoesNotContain("Execute", resultMethods);
        Assert.DoesNotContain("Parse", plannerMethods);
        Assert.DoesNotContain("Execute", plannerMethods);
    }

    [Fact]
    public void ContractDoesNotIntroduceDbHttpFileIoParserExecutionOrPersistenceMappingSurface()
    {
        var publicMembers = typeof(ParserDryRunStatus)
            .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Concat(typeof(ParserDryRunBoundaryPlan)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Concat(typeof(ParserDryRunBoundaryResult)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Concat(typeof(ParserDryRunBoundaryPlanBatch)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Concat(typeof(ParserDryRunBoundaryResultBatch)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Concat(typeof(ParserDryRunBoundaryPlanner)
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
            "Write",
            "Exists",
            "Calculate",
            "Factor",
            "Persist",
            "Map",
        };

        foreach (var term in blockedTerms)
        {
            Assert.DoesNotContain(publicMembers, member => member.Contains(term, StringComparison.OrdinalIgnoreCase));
        }

        Assert.DoesNotContain("Parse", publicMembers);
    }
}
