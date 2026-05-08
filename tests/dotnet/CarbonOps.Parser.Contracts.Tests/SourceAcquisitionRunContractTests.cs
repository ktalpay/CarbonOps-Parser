using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class SourceAcquisitionRunContractTests
{
    [Fact]
    public void ValidSourceAcquisitionRunRequestsAndResultsCanBeConstructedForPhaseOneSources()
    {
        var requests = SourceAcquisitionRunRegistry.CreateDefaultRunRequests();
        var results = SourceAcquisitionRunRegistry.CreateDefaultRunResults();

        Assert.Equal(3, requests.Count);
        Assert.Equal(3, results.Count);
        Assert.Equal(
            [
                SourceFamily.GhgProtocol,
                SourceFamily.DefraDesnz,
                SourceFamily.IpccEfdb,
            ],
            requests.Select(request => request.SourceFamily));
        Assert.Equal(
            [
                SourceFamily.GhgProtocol,
                SourceFamily.DefraDesnz,
                SourceFamily.IpccEfdb,
            ],
            results.Select(result => result.SourceFamily));
        Assert.All(requests, request => Assert.True(request.Validate().IsValid));
        Assert.All(results, result => Assert.True(result.Validate().IsValid));
    }

    [Fact]
    public void CandidatesAndArtifactsAlignWithRunSourceKey()
    {
        var requests = SourceAcquisitionRunRegistry.CreateDefaultRunRequests();
        var results = SourceAcquisitionRunRegistry.CreateDefaultRunResults();

        foreach (var request in requests)
        {
            Assert.True(ParserAdapterDescriptorRegistry.TryGetBySourceKey(request.SourceKey, out var descriptor));
            Assert.NotNull(descriptor);
            Assert.Equal(descriptor!.SourceFamily, request.SourceFamily);
            Assert.All(request.Candidates, candidate =>
            {
                Assert.Equal(request.SourceFamily, candidate.SourceFamily);
                Assert.Equal(request.SourceKey, candidate.SourceKey);
            });
        }

        foreach (var result in results)
        {
            Assert.True(ParserAdapterDescriptorRegistry.TryGetBySourceKey(result.SourceKey, out var descriptor));
            Assert.NotNull(descriptor);
            Assert.Equal(descriptor!.SourceFamily, result.SourceFamily);
            Assert.All(result.Candidates, candidate =>
            {
                Assert.Equal(result.SourceFamily, candidate.SourceFamily);
                Assert.Equal(result.SourceKey, candidate.SourceKey);
            });
            Assert.All(result.Artifacts, artifact =>
            {
                Assert.Equal(result.SourceFamily, artifact.SourceFamily);
                Assert.Equal(result.SourceKey, artifact.SourceKey);
            });
        }
    }

    [Fact]
    public void StatusValuesAreConstrainedToDeterministicAllowedValues()
    {
        Assert.Equal(
            [
                SourceAcquisitionRunStatus.Planned,
                SourceAcquisitionRunStatus.Completed,
                SourceAcquisitionRunStatus.Failed,
                SourceAcquisitionRunStatus.InvalidRequest,
            ],
            Enum.GetValues<SourceAcquisitionRunStatus>());

        var result = new SourceAcquisitionRunResult(
            SourceFamily.GhgProtocol,
            SourceFamily.GhgProtocol.ToWireName(),
            (SourceAcquisitionRunStatus)999,
            SourceDiscoveryCandidateRegistry.CreateDefaultCandidateBatch().Candidates.Take(1),
            SourceDownloadArtifactRegistry.CreateDefaultArtifactBatch().Artifacts.Take(1));

        var validation = result.Validate();

        Assert.False(validation.IsValid);
        Assert.Contains(
            "SourceAcquisitionRunStatus must be a defined source acquisition run status.",
            validation.Errors);
    }

    [Fact]
    public void RequiredRequestMetadataFieldsRejectEmptyStrings()
    {
        var request = new SourceAcquisitionRunRequest(
            SourceFamily.GhgProtocol,
            "",
            [],
            runId: " ",
            correlationId: "",
            requestedReportingYear: 1800,
            requestedVersionLabel: "\t");

        var result = request.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            [
                "SourceKey is required.",
                "SourceAcquisitionRunRequest must include at least one discovery candidate.",
                "RunId must not be whitespace when provided.",
                "CorrelationId must not be whitespace when provided.",
                "RequestedReportingYear must be between 1990 and 2100 when provided.",
                "RequestedVersionLabel must not be whitespace when provided.",
            ],
            result.Errors);
    }

    [Fact]
    public void RequiredResultMetadataFieldsRejectEmptyStrings()
    {
        var result = new SourceAcquisitionRunResult(
            SourceFamily.GhgProtocol,
            "",
            (SourceAcquisitionRunStatus)999,
            [],
            [],
            runId: " ",
            correlationId: "",
            reportingYear: 1800,
            versionLabel: "\t");

        var validation = result.Validate();

        Assert.False(validation.IsValid);
        Assert.Equal(
            [
                "SourceKey is required.",
                "SourceAcquisitionRunStatus must be a defined source acquisition run status.",
                "RunId must not be whitespace when provided.",
                "CorrelationId must not be whitespace when provided.",
                "ReportingYear must be between 1990 and 2100 when provided.",
                "VersionLabel must not be whitespace when provided.",
            ],
            validation.Errors);
    }

    [Fact]
    public void CandidateAndArtifactAlignmentFailuresAreClear()
    {
        var candidates = SourceDiscoveryCandidateRegistry.CreateDefaultCandidateBatch().Candidates;
        var artifacts = SourceDownloadArtifactRegistry.CreateDefaultArtifactBatch().Artifacts;
        var request = new SourceAcquisitionRunRequest(
            SourceFamily.GhgProtocol,
            SourceFamily.GhgProtocol.ToWireName(),
            [candidates[1]]);
        var result = new SourceAcquisitionRunResult(
            SourceFamily.GhgProtocol,
            SourceFamily.GhgProtocol.ToWireName(),
            SourceAcquisitionRunStatus.Planned,
            [candidates[1]],
            [artifacts[2]]);

        var requestValidation = request.Validate();
        var resultValidation = result.Validate();

        Assert.False(requestValidation.IsValid);
        Assert.Contains("Candidates[0].SourceFamily must match request SourceFamily.", requestValidation.Errors);
        Assert.Contains("Candidates[0].SourceKey must match request SourceKey.", requestValidation.Errors);
        Assert.False(resultValidation.IsValid);
        Assert.Contains("Candidates[0].SourceFamily must match result SourceFamily.", resultValidation.Errors);
        Assert.Contains("Candidates[0].SourceKey must match result SourceKey.", resultValidation.Errors);
        Assert.Contains("Artifacts[0].SourceFamily must match result SourceFamily.", resultValidation.Errors);
        Assert.Contains("Artifacts[0].SourceKey must match result SourceKey.", resultValidation.Errors);
    }

    [Fact]
    public void CandidateAndArtifactOrderingIsDeterministic()
    {
        var firstRequests = SourceAcquisitionRunRegistry.CreateDefaultRunRequests();
        var secondRequests = SourceAcquisitionRunRegistry.CreateDefaultRunRequests();
        var firstResults = SourceAcquisitionRunRegistry.CreateDefaultRunResults();
        var secondResults = SourceAcquisitionRunRegistry.CreateDefaultRunResults();

        Assert.NotSame(firstRequests, secondRequests);
        Assert.NotSame(firstResults, secondResults);
        Assert.Equal(
            firstRequests.Select(request => (request.SourceKey, request.RunId, request.CandidateCount)),
            secondRequests.Select(request => (request.SourceKey, request.RunId, request.CandidateCount)));
        Assert.Equal(
            firstResults.Select(result => (result.SourceKey, result.RunId, result.CandidateCount, result.ArtifactCount)),
            secondResults.Select(result => (result.SourceKey, result.RunId, result.CandidateCount, result.ArtifactCount)));
        Assert.Equal(
            ParserAdapterDescriptorRegistry.Descriptors.Select(descriptor => descriptor.SourceFamily),
            firstRequests.Select(request => request.SourceFamily));
        Assert.Equal(
            ParserAdapterDescriptorRegistry.Descriptors.Select(descriptor => descriptor.SourceFamily),
            firstResults.Select(result => result.SourceFamily));
    }

    [Fact]
    public void SummaryCountsAreDeterministic()
    {
        var requests = SourceAcquisitionRunRegistry.CreateDefaultRunRequests();
        var results = SourceAcquisitionRunRegistry.CreateDefaultRunResults();

        Assert.All(requests, request => Assert.Equal(request.Candidates.Count, request.CandidateCount));
        Assert.All(results, result =>
        {
            Assert.Equal(result.Candidates.Count, result.CandidateCount);
            Assert.Equal(result.Artifacts.Count, result.ArtifactCount);
        });
        Assert.Equal([1, 1, 1], requests.Select(request => request.CandidateCount));
        Assert.Equal([1, 1, 1], results.Select(result => result.CandidateCount));
        Assert.Equal([1, 1, 1], results.Select(result => result.ArtifactCount));
    }

    [Fact]
    public void RunRequestAndResultSnapshotInputCollections()
    {
        var candidates = new List<SourceDiscoveryCandidate>
        {
            SourceDiscoveryCandidateRegistry.CreateDefaultCandidateBatch().Candidates[0],
        };
        var artifacts = new List<SourceDownloadArtifact>
        {
            SourceDownloadArtifactRegistry.CreateDefaultArtifactBatch().Artifacts[0],
        };

        var request = new SourceAcquisitionRunRequest(
            SourceFamily.GhgProtocol,
            SourceFamily.GhgProtocol.ToWireName(),
            candidates);
        var result = new SourceAcquisitionRunResult(
            SourceFamily.GhgProtocol,
            SourceFamily.GhgProtocol.ToWireName(),
            SourceAcquisitionRunStatus.Planned,
            candidates,
            artifacts);

        candidates.Clear();
        artifacts.Clear();

        Assert.Equal(1, request.CandidateCount);
        Assert.Equal(1, result.CandidateCount);
        Assert.Equal(1, result.ArtifactCount);
    }

    [Fact]
    public void ValidationDoesNotPerformNetworkCallsFileIoDbAccessContentInspectionOrParserExecution()
    {
        var candidate = new SourceDiscoveryCandidate(
            SourceFamily.DefraDesnz,
            SourceFamily.DefraDesnz.ToWireName(),
            "defra-desnz-remote-candidate",
            "DEFRA/DESNZ remote metadata",
            2024,
            "https://example.invalid/defra-desnz/factors.csv",
            ParserSourceFormat.DiscoveryReference,
            "text/csv",
            extension: ".csv");
        var artifact = new SourceDownloadArtifact(
            SourceFamily.DefraDesnz,
            SourceFamily.DefraDesnz.ToWireName(),
            candidate.CandidateId,
            "defra-desnz-remote-artifact",
            ParserSourceFormat.DiscoveryReference,
            candidate.SourceReference,
            "/definitely/not-present/defra-desnz.csv",
            candidate.Title,
            candidate.ContentType,
            extension: candidate.Extension);
        var request = new SourceAcquisitionRunRequest(
            SourceFamily.DefraDesnz,
            SourceFamily.DefraDesnz.ToWireName(),
            [candidate]);
        var result = new SourceAcquisitionRunResult(
            SourceFamily.DefraDesnz,
            SourceFamily.DefraDesnz.ToWireName(),
            SourceAcquisitionRunStatus.Planned,
            [candidate],
            [artifact]);

        Assert.True(request.Validate().IsValid);
        Assert.True(result.Validate().IsValid);
    }

    [Fact]
    public void ConstructionRemainsRuntimePassive()
    {
        var requestMethods = typeof(SourceAcquisitionRunRequest)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Where(method => !method.Name.StartsWith("get_", StringComparison.Ordinal))
            .Select(method => method.Name)
            .ToArray();
        var resultMethods = typeof(SourceAcquisitionRunResult)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Where(method => !method.Name.StartsWith("get_", StringComparison.Ordinal))
            .Select(method => method.Name)
            .ToArray();
        var registryMethods = typeof(SourceAcquisitionRunRegistry)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();

        Assert.DoesNotContain("Fetch", requestMethods);
        Assert.DoesNotContain("Parse", requestMethods);
        Assert.DoesNotContain("Execute", requestMethods);
        Assert.DoesNotContain("Fetch", resultMethods);
        Assert.DoesNotContain("Parse", resultMethods);
        Assert.DoesNotContain("Execute", resultMethods);
        Assert.Equal(["CreateDefaultRunRequests", "CreateDefaultRunResults"], registryMethods);
    }

    [Fact]
    public void ContractDoesNotIntroduceDbHttpFileIoParserExecutionOrRuntimeDownloaderSurface()
    {
        var publicMembers = typeof(SourceAcquisitionRunRequest)
            .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Concat(typeof(SourceAcquisitionRunResult)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Concat(typeof(SourceAcquisitionRunRegistry)
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
            "StatFile",
            "Exists",
            "ReadFile",
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
