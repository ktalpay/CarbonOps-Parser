using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class AcquisitionToParserPlanContractTests
{
    [Fact]
    public void ValidAcquisitionToParserPlansCanBeConstructedForPhaseOneSources()
    {
        var batch = AcquisitionToParserPlanRegistry.CreateDefaultPlanBatch();

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
    public void SourceAcquisitionResultArtifactsBecomeParserInputArtifactsThroughBridgeContract()
    {
        var acquisitionResults = SourceAcquisitionRunRegistry.CreateDefaultRunResults();
        var plans = AcquisitionToParserPlanRegistry.CreateDefaultPlanBatch().Plans;

        foreach (var pair in acquisitionResults.Zip(plans))
        {
            var acquisitionResult = pair.First;
            var plan = pair.Second;

            Assert.Equal(acquisitionResult.Artifacts.Select(artifact => artifact.ArtifactId), plan.Bridges.Select(bridge => bridge.SourceArtifactId));
            Assert.Equal(
                acquisitionResult.Artifacts.Select(artifact => artifact.LocalReference),
                plan.Bridges.Select(bridge => bridge.ParserInputArtifact.ArtifactReference));
            Assert.Equal(
                plan.Bridges.Select(bridge => bridge.ParserInputArtifact),
                plan.ParserRunRequests.SelectMany(request => request.Artifacts));
        }
    }

    [Fact]
    public void GeneratedParserAdapterRunRequestsAlignWithDescriptorRegistryParserKeys()
    {
        var plans = AcquisitionToParserPlanRegistry.CreateDefaultPlanBatch().Plans;

        foreach (var plan in plans)
        {
            Assert.Single(plan.ParserRunRequests);
            Assert.True(ParserAdapterDescriptorRegistry.TryGetBySourceFamily(plan.SourceFamily, out var descriptor));
            Assert.NotNull(descriptor);
            Assert.Equal(descriptor!.ParserKey, plan.ParserRunRequests[0].ParserKey);
            Assert.Equal(descriptor.ParserKey, plan.Bridges[0].ParserKey);
        }
    }

    [Fact]
    public void SourceKeysRemainConsistentAcrossAcquisitionBridgeAndParserRunRequest()
    {
        var plans = AcquisitionToParserPlanRegistry.CreateDefaultPlanBatch().Plans;

        foreach (var plan in plans)
        {
            Assert.Equal(plan.SourceKey, plan.AcquisitionResult.SourceKey);
            Assert.All(plan.Bridges, bridge =>
            {
                Assert.Equal(plan.SourceKey, bridge.SourceKey);
                Assert.Equal(plan.SourceKey, bridge.SourceArtifact.SourceKey);
                Assert.Equal(plan.SourceKey, bridge.ParserInputArtifact.SourceKey);
            });
            Assert.All(plan.ParserRunRequests, request => Assert.Equal(plan.SourceKey, request.SourceKey));
        }
    }

    [Fact]
    public void PlanStatusValuesAreConstrainedToDeterministicAllowedValues()
    {
        Assert.Equal(
            [
                AcquisitionToParserPlanStatus.Planned,
                AcquisitionToParserPlanStatus.InvalidAcquisitionResult,
                AcquisitionToParserPlanStatus.NoSourceArtifacts,
            ],
            Enum.GetValues<AcquisitionToParserPlanStatus>());

        var plan = AcquisitionToParserPlanRegistry.CreateDefaultPlanBatch().Plans[0];
        var invalid = new AcquisitionToParserPlan(
            plan.SourceFamily,
            plan.SourceKey,
            plan.AcquisitionResult,
            plan.Bridges,
            plan.ParserRunRequests,
            (AcquisitionToParserPlanStatus)999,
            plan.AcquisitionRunId);

        var result = invalid.Validate();

        Assert.False(result.IsValid);
        Assert.Contains(
            "AcquisitionToParserPlanStatus must be a defined acquisition-to-parser plan status.",
            result.Errors);
    }

    [Fact]
    public void RequiredMetadataFieldsRejectEmptyStrings()
    {
        var plan = AcquisitionToParserPlanRegistry.CreateDefaultPlanBatch().Plans[0];
        var invalid = new AcquisitionToParserPlan(
            plan.SourceFamily,
            "",
            plan.AcquisitionResult,
            plan.Bridges,
            plan.ParserRunRequests,
            plan.Status,
            acquisitionRunId: " ");

        var result = invalid.Validate();

        Assert.False(result.IsValid);
        Assert.Contains("SourceKey is required.", result.Errors);
        Assert.Contains("AcquisitionRunId must not be whitespace when provided.", result.Errors);
    }

    [Fact]
    public void SummaryCountsAreDeterministic()
    {
        var plans = AcquisitionToParserPlanRegistry.CreateDefaultPlanBatch().Plans;

        Assert.Equal([1, 1, 1], plans.Select(plan => plan.DownloadedArtifactCount));
        Assert.Equal([1, 1, 1], plans.Select(plan => plan.ParserInputArtifactCount));
        Assert.Equal([1, 1, 1], plans.Select(plan => plan.ParserRunRequestCount));
        Assert.All(plans, plan =>
        {
            Assert.Equal(plan.AcquisitionResult.ArtifactCount, plan.DownloadedArtifactCount);
            Assert.Equal(plan.Bridges.Count, plan.ParserInputArtifactCount);
            Assert.Equal(plan.ParserRunRequests.Count, plan.ParserRunRequestCount);
        });
    }

    [Fact]
    public void OrderingIsDeterministic()
    {
        var first = AcquisitionToParserPlanRegistry.CreateDefaultPlanBatch();
        var second = AcquisitionToParserPlanRegistry.CreateDefaultPlanBatch();

        Assert.NotSame(first, second);
        Assert.NotSame(first.Plans, second.Plans);
        Assert.Equal(
            first.Plans.Select(plan => (plan.SourceKey, plan.AcquisitionRunId, plan.ParserRunRequestCount)),
            second.Plans.Select(plan => (plan.SourceKey, plan.AcquisitionRunId, plan.ParserRunRequestCount)));
        Assert.Equal(
            ParserAdapterDescriptorRegistry.Descriptors.Select(descriptor => descriptor.SourceFamily),
            first.Plans.Select(plan => plan.SourceFamily));
    }

    [Fact]
    public void PlanBatchSnapshotsPlans()
    {
        var plans = new List<AcquisitionToParserPlan>
        {
            AcquisitionToParserPlanRegistry.CreateDefaultPlanBatch().Plans[0],
        };

        var batch = new AcquisitionToParserPlanBatch(plans);
        plans.Clear();

        Assert.Equal(1, batch.PlanCount);
        Assert.Single(batch.Plans);
        Assert.Equal(SourceFamily.GhgProtocol, batch.Plans[0].SourceFamily);
    }

    [Fact]
    public void LocalReferenceMetadataIsNotOpenedStattedReadWrittenHashedOrExistenceChecked()
    {
        var acquisitionResult = CreateSingleArtifactAcquisitionResult(
            SourceFamily.IpccEfdb,
            "/definitely/not-present/ipcc-efdb.json",
            "ipcc_efdb_discovery_reference");

        var plan = AcquisitionToParserPlanRegistry.CreatePlan(acquisitionResult);

        Assert.True(plan.Validate().IsValid);
        Assert.Equal("/definitely/not-present/ipcc-efdb.json", plan.Bridges[0].ParserInputArtifact.ArtifactReference);
        Assert.Equal("/definitely/not-present/ipcc-efdb.json", plan.ParserRunRequests[0].Artifacts[0].ArtifactReference);
    }

    [Fact]
    public void UrlReferenceMetadataIsNotFetchedOrValidatedThroughNetwork()
    {
        var acquisitionResult = CreateSingleArtifactAcquisitionResult(
            SourceFamily.DefraDesnz,
            "defra_desnz_local_artifact",
            "https://example.invalid/defra-desnz/factors.csv");

        var plan = AcquisitionToParserPlanRegistry.CreatePlan(acquisitionResult);

        Assert.True(plan.Validate().IsValid);
        Assert.Equal("https://example.invalid/defra-desnz/factors.csv", plan.AcquisitionResult.Artifacts[0].SourceReference);
        Assert.Equal("https://example.invalid/defra-desnz/factors.csv", plan.Bridges[0].SourceArtifact.SourceReference);
    }

    [Fact]
    public void ValidationDoesNotAccessDbOrExecuteParsers()
    {
        var plan = AcquisitionToParserPlanRegistry.CreateDefaultPlanBatch().Plans[0];

        var result = plan.Validate();

        Assert.True(result.IsValid);
        Assert.Empty(result.Errors);
    }

    [Fact]
    public void DivergentBridgeAndParserRunMetadataFailsClearly()
    {
        var plan = AcquisitionToParserPlanRegistry.CreateDefaultPlanBatch().Plans[0];
        var bridge = plan.Bridges[0];
        var unrelatedParserInput = new ParserInputArtifact(
            bridge.ParserInputArtifact.SourceFamily,
            bridge.ParserInputArtifact.SourceKey,
            bridge.ParserInputArtifact.ParserKey,
            bridge.ParserInputArtifact.SourceFormat,
            "unrelated-parser-input",
            bridge.ParserInputArtifact.DisplayName,
            bridge.ParserInputArtifact.ChecksumAlgorithm,
            bridge.ParserInputArtifact.ChecksumValue,
            bridge.ParserInputArtifact.IsDryRunChecksum,
            bridge.ParserInputArtifact.ContentType,
            bridge.ParserInputArtifact.Extension,
            bridge.ParserInputArtifact.ReportingYear);
        var invalidRequest = new ParserAdapterRunRequest(
            plan.SourceFamily,
            plan.SourceKey,
            plan.ParserRunRequests[0].ParserKey,
            [unrelatedParserInput],
            plan.ParserRunRequests[0].RunId,
            plan.ParserRunRequests[0].CorrelationId,
            plan.ParserRunRequests[0].RequestedReportingYear);
        var invalid = new AcquisitionToParserPlan(
            plan.SourceFamily,
            plan.SourceKey,
            plan.AcquisitionResult,
            plan.Bridges,
            [invalidRequest],
            plan.Status,
            plan.AcquisitionRunId);

        var result = invalid.Validate();

        Assert.False(result.IsValid);
        Assert.Contains(
            "ParserRunRequests[0].Artifacts[0] must be produced by a bridge.",
            result.Errors);
    }

    [Fact]
    public void ConstructionRemainsRuntimePassive()
    {
        var planMethods = typeof(AcquisitionToParserPlan)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Where(method => !method.Name.StartsWith("get_", StringComparison.Ordinal))
            .Select(method => method.Name)
            .ToArray();
        var batchMethods = typeof(AcquisitionToParserPlanBatch)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Where(method => !method.Name.StartsWith("get_", StringComparison.Ordinal))
            .Select(method => method.Name)
            .ToArray();
        var registryMethods = typeof(AcquisitionToParserPlanRegistry)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();

        Assert.DoesNotContain("Fetch", planMethods);
        Assert.DoesNotContain("Parse", planMethods);
        Assert.DoesNotContain("Execute", planMethods);
        Assert.DoesNotContain("Fetch", batchMethods);
        Assert.DoesNotContain("Parse", batchMethods);
        Assert.DoesNotContain("Execute", batchMethods);
        Assert.Equal(["CreateDefaultPlanBatch", "CreatePlanBatch", "CreatePlan"], registryMethods);
    }

    [Fact]
    public void ContractDoesNotIntroduceDbHttpFileIoParserExecutionOrRuntimeDownloaderSurface()
    {
        var publicMembers = typeof(AcquisitionToParserPlan)
            .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Concat(typeof(AcquisitionToParserPlanBatch)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Concat(typeof(AcquisitionToParserPlanRegistry)
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
