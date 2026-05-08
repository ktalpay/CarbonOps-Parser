using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class SourceAcquisitionContractPublicApiTests
{
    [Fact]
    public void RuntimePassiveSourceAcquisitionContractTypesArePublic()
    {
        var publicContractTypes = new[]
        {
            typeof(SourceDiscoveryCandidate),
            typeof(SourceDiscoveryCandidateBatch),
            typeof(SourceDiscoveryCandidateRegistry),
            typeof(SourceDownloadArtifact),
            typeof(SourceDownloadArtifactBatch),
            typeof(SourceDownloadArtifactRegistry),
            typeof(SourceAcquisitionRunStatus),
            typeof(SourceAcquisitionRunRequest),
            typeof(SourceAcquisitionRunResult),
            typeof(SourceAcquisitionRunRegistry),
        };

        Assert.Equal(
            [
                "SourceDiscoveryCandidate",
                "SourceDiscoveryCandidateBatch",
                "SourceDiscoveryCandidateRegistry",
                "SourceDownloadArtifact",
                "SourceDownloadArtifactBatch",
                "SourceDownloadArtifactRegistry",
                "SourceAcquisitionRunStatus",
                "SourceAcquisitionRunRequest",
                "SourceAcquisitionRunResult",
                "SourceAcquisitionRunRegistry",
            ],
            publicContractTypes.Select(type => type.Name));
        Assert.All(publicContractTypes, type => Assert.True(type.IsPublic, $"{type.Name} must be public."));
    }

    [Fact]
    public void SourceAcquisitionContractTypesCanBeConstructedThroughPublicApi()
    {
        var descriptor = ParserAdapterDescriptorRegistry.Descriptors[0];
        var candidate = new SourceDiscoveryCandidate(
            descriptor.SourceFamily,
            descriptor.SourceFamily.ToWireName(),
            "ghg_protocol_candidate",
            "GHG Protocol candidate",
            reportingYear: null,
            "ghg_protocol_discovery_reference",
            ParserSourceFormat.DiscoveryReference,
            "application/x-carbonops-discovery-reference",
            checksum: new SourceDocumentChecksum("sha256", "abc123", IsDryRunPlaceholder: false),
            versionLabel: "static-version");
        var candidateBatch = new SourceDiscoveryCandidateBatch([candidate]);
        var artifact = new SourceDownloadArtifact(
            candidate.SourceFamily,
            candidate.SourceKey,
            candidate.CandidateId,
            "ghg_protocol_artifact",
            candidate.ExpectedSourceFormat,
            candidate.SourceReference,
            "ghg_protocol_local_artifact",
            candidate.Title,
            candidate.ContentType,
            candidate.Extension,
            candidate.Checksum,
            sizeBytes: 1024,
            candidate.ReportingYear,
            candidate.VersionLabel);
        var artifactBatch = new SourceDownloadArtifactBatch([artifact]);
        var runRequest = new SourceAcquisitionRunRequest(
            candidate.SourceFamily,
            candidate.SourceKey,
            [candidate],
            runId: "ghg_protocol_source_acquisition_run",
            correlationId: "ghg_protocol_correlation",
            requestedVersionLabel: candidate.VersionLabel);
        var runResult = new SourceAcquisitionRunResult(
            candidate.SourceFamily,
            candidate.SourceKey,
            SourceAcquisitionRunStatus.Planned,
            [candidate],
            [artifact],
            runId: runRequest.RunId,
            correlationId: runRequest.CorrelationId,
            versionLabel: candidate.VersionLabel);

        Assert.Equal(1, candidateBatch.CandidateCount);
        Assert.Equal(1, artifactBatch.ArtifactCount);
        Assert.Equal(1, runRequest.CandidateCount);
        Assert.Equal(1, runResult.CandidateCount);
        Assert.Equal(1, runResult.ArtifactCount);
        Assert.True(candidate.Validate().IsValid);
        Assert.True(artifact.Validate().IsValid);
        Assert.True(runRequest.Validate().IsValid);
        Assert.True(runResult.Validate().IsValid);
    }

    [Fact]
    public void SourceAcquisitionRegistryPublicApiIsDeterministic()
    {
        var candidates = SourceDiscoveryCandidateRegistry.CreateDefaultCandidateBatch();
        var artifacts = SourceDownloadArtifactRegistry.CreateDefaultArtifactBatch();
        var requests = SourceAcquisitionRunRegistry.CreateDefaultRunRequests();
        var results = SourceAcquisitionRunRegistry.CreateDefaultRunResults();

        Assert.Equal(3, candidates.CandidateCount);
        Assert.Equal(3, artifacts.ArtifactCount);
        Assert.Equal(3, requests.Count);
        Assert.Equal(3, results.Count);
        Assert.Equal(
            ParserAdapterDescriptorRegistry.Descriptors.Select(descriptor => descriptor.SourceFamily),
            requests.Select(request => request.SourceFamily));
        Assert.Equal(
            ParserAdapterDescriptorRegistry.Descriptors.Select(descriptor => descriptor.SourceFamily),
            results.Select(result => result.SourceFamily));
        Assert.Equal(
            candidates.Candidates.Select(candidate => candidate.SourceKey),
            artifacts.Artifacts.Select(artifact => artifact.SourceKey));
    }

    [Fact]
    public void SourceAcquisitionRunStatusPublicValuesAreDeterministic()
    {
        Assert.Equal(
            [
                SourceAcquisitionRunStatus.Planned,
                SourceAcquisitionRunStatus.Completed,
                SourceAcquisitionRunStatus.Failed,
                SourceAcquisitionRunStatus.InvalidRequest,
            ],
            Enum.GetValues<SourceAcquisitionRunStatus>());
    }

    [Fact]
    public void SourceAcquisitionContractPublicApiConstructionRemainsRuntimePassive()
    {
        var sourceAcquisitionContractTypes = new[]
        {
            typeof(SourceDiscoveryCandidateRegistry),
            typeof(SourceDownloadArtifactRegistry),
            typeof(SourceAcquisitionRunRegistry),
        };
        var publicMethodNames = sourceAcquisitionContractTypes
            .SelectMany(type => type.GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Where(method => !method.Name.StartsWith("get_", StringComparison.Ordinal))
            .Select(method => method.Name)
            .ToArray();

        Assert.Equal(
            [
                "CreateDefaultCandidateBatch",
                "CreateDefaultArtifactBatch",
                "CreateDefaultRunRequests",
                "CreateDefaultRunResults",
            ],
            publicMethodNames);
        Assert.DoesNotContain("Discover", publicMethodNames);
        Assert.DoesNotContain("Fetch", publicMethodNames);
        Assert.DoesNotContain("Parse", publicMethodNames);
        Assert.DoesNotContain("Execute", publicMethodNames);
        Assert.DoesNotContain("Instantiate", publicMethodNames);
    }

    [Fact]
    public void SourceAcquisitionContractPublicApiDoesNotExposeDbHttpFileIoOrRuntimeExecutionSurface()
    {
        var sourceAcquisitionContractTypes = new[]
        {
            typeof(SourceDiscoveryCandidate),
            typeof(SourceDiscoveryCandidateBatch),
            typeof(SourceDiscoveryCandidateRegistry),
            typeof(SourceDownloadArtifact),
            typeof(SourceDownloadArtifactBatch),
            typeof(SourceDownloadArtifactRegistry),
            typeof(SourceAcquisitionRunRequest),
            typeof(SourceAcquisitionRunResult),
            typeof(SourceAcquisitionRunRegistry),
        };
        var publicMembers = sourceAcquisitionContractTypes
            .SelectMany(type => type.GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
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
}
