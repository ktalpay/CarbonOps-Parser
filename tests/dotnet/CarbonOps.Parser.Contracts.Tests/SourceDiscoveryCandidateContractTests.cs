using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class SourceDiscoveryCandidateContractTests
{
    [Fact]
    public void ValidDiscoveryCandidatesCanBeConstructedForPhaseOneSources()
    {
        var batch = SourceDiscoveryCandidateRegistry.CreateDefaultCandidateBatch();

        Assert.Equal(3, batch.CandidateCount);
        Assert.Equal(
            [
                SourceFamily.GhgProtocol,
                SourceFamily.DefraDesnz,
                SourceFamily.IpccEfdb,
            ],
            batch.Candidates.Select(candidate => candidate.SourceFamily));
        Assert.All(batch.Candidates, candidate => Assert.True(candidate.Validate().IsValid));
    }

    [Fact]
    public void CandidateSourceKeysAlignWithDescriptorRegistryMetadata()
    {
        var candidates = SourceDiscoveryCandidateRegistry.CreateDefaultCandidateBatch().Candidates;

        foreach (var candidate in candidates)
        {
            Assert.True(ParserAdapterDescriptorRegistry.TryGetBySourceKey(candidate.SourceKey, out var descriptor));
            Assert.NotNull(descriptor);
            Assert.Equal(descriptor!.SourceFamily, candidate.SourceFamily);
            Assert.Equal(descriptor.SourceFamily.ToWireName(), candidate.SourceKey);
        }
    }

    [Fact]
    public void CandidateMetadataUsesExistingDiscoveryAndParserInputMetadata()
    {
        var documents = SourceDiscoveryRegistry.CreateDefaultDiscoveryResult().Documents;
        var candidates = SourceDiscoveryCandidateRegistry.CreateDefaultCandidateBatch().Candidates;

        foreach (var pair in documents.Zip(candidates))
        {
            var document = pair.First;
            var candidate = pair.Second;

            Assert.Equal(document.SourceFamily, candidate.SourceFamily);
            Assert.Equal(document.SourceFamily.ToWireName(), candidate.SourceKey);
            Assert.Equal(document.SourceReference, candidate.CandidateId);
            Assert.Equal(document.SourceName, candidate.Title);
            Assert.Equal(document.ReportingYear, candidate.ReportingYear);
            Assert.Equal(document.SourceReference, candidate.SourceReference);
            Assert.Equal(ParserInputRegistry.GetSourceFormat(document.SourceFamily), candidate.ExpectedSourceFormat);
            Assert.Equal(
                ParserInputRegistry.GetContentType(candidate.ExpectedSourceFormat),
                candidate.ContentType);
        }
    }

    [Fact]
    public void RequiredCandidateMetadataFieldsRejectEmptyStrings()
    {
        var candidate = new SourceDiscoveryCandidate(
            SourceFamily.GhgProtocol,
            "",
            "",
            " ",
            1800,
            "",
            (ParserSourceFormat)999,
            "\t",
            extension: " ",
            checksum: new SourceDocumentChecksum("", " ", IsDryRunPlaceholder: true),
            versionLabel: "");

        var result = candidate.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            [
                "SourceKey is required.",
                "CandidateId is required.",
                "Title is required.",
                "ReportingYear must be between 1990 and 2100 when provided.",
                "SourceReference is required.",
                "ExpectedSourceFormat must be a defined parser source format.",
                "ContentType is required.",
                "Extension must not be whitespace when provided.",
                "VersionLabel must not be whitespace when provided.",
                "Checksum.Algorithm is required when Checksum is provided.",
                "Checksum.Value is required when Checksum is provided.",
            ],
            result.Errors);
    }

    [Fact]
    public void UnknownSourceKeyFailsClearly()
    {
        var candidate = new SourceDiscoveryCandidate(
            SourceFamily.GhgProtocol,
            "unknown_source_family",
            "candidate-1",
            "GHG Protocol",
            reportingYear: null,
            "candidate-reference",
            ParserSourceFormat.DiscoveryReference,
            "application/x-carbonops-discovery-reference");

        var result = candidate.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            ["SourceKey must match a registered parser adapter descriptor."],
            result.Errors);
    }

    [Fact]
    public void CandidateResultOrderingIsDeterministic()
    {
        var first = SourceDiscoveryCandidateRegistry.CreateDefaultCandidateBatch();
        var second = SourceDiscoveryCandidateRegistry.CreateDefaultCandidateBatch();

        Assert.NotSame(first, second);
        Assert.NotSame(first.Candidates, second.Candidates);
        Assert.Equal(
            first.Candidates.Select(candidate => candidate.SourceKey),
            second.Candidates.Select(candidate => candidate.SourceKey));
        Assert.Equal(
            first.Candidates.Select(candidate => candidate.CandidateId),
            second.Candidates.Select(candidate => candidate.CandidateId));
        Assert.Equal(
            SourceFamilyRegistry.SupportedFamilies,
            first.Candidates.Select(candidate => candidate.SourceFamily));
    }

    [Fact]
    public void CandidateBatchSnapshotsCandidates()
    {
        var candidates = new List<SourceDiscoveryCandidate>
        {
            SourceDiscoveryCandidateRegistry.CreateDefaultCandidateBatch().Candidates[0],
        };

        var batch = new SourceDiscoveryCandidateBatch(candidates);
        candidates.Clear();

        Assert.Equal(1, batch.CandidateCount);
        Assert.Single(batch.Candidates);
        Assert.Equal(SourceFamily.GhgProtocol, batch.Candidates[0].SourceFamily);
    }

    [Fact]
    public void UrlReferenceMetadataIsNotFetchedOrNetworkValidated()
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
            extension: ".csv",
            checksum: null,
            versionLabel: "2024-static-label");

        var result = candidate.Validate();

        Assert.True(result.IsValid);
        Assert.Empty(result.Errors);
    }

    [Fact]
    public void ValidationDoesNotReadFilesInspectContentAccessDbOrCallNetwork()
    {
        var candidate = new SourceDiscoveryCandidate(
            SourceFamily.IpccEfdb,
            SourceFamily.IpccEfdb.ToWireName(),
            "ipcc-efdb-local-candidate",
            "IPCC EFDB local metadata",
            null,
            "/definitely/not-present/ipcc-efdb.json",
            ParserSourceFormat.DiscoveryReference,
            "application/json",
            extension: ".json",
            checksum: new SourceDocumentChecksum("sha256", "abc123", IsDryRunPlaceholder: false));

        var result = candidate.Validate();

        Assert.True(result.IsValid);
        Assert.Empty(result.Errors);
    }

    [Fact]
    public void ConstructionRemainsRuntimePassive()
    {
        var candidateMethods = typeof(SourceDiscoveryCandidate)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Where(method => !method.Name.StartsWith("get_", StringComparison.Ordinal))
            .Select(method => method.Name)
            .ToArray();
        var batchMethods = typeof(SourceDiscoveryCandidateBatch)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Where(method => !method.Name.StartsWith("get_", StringComparison.Ordinal))
            .Select(method => method.Name)
            .ToArray();
        var registryMethods = typeof(SourceDiscoveryCandidateRegistry)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();

        Assert.DoesNotContain("Download", candidateMethods);
        Assert.DoesNotContain("Fetch", candidateMethods);
        Assert.DoesNotContain("Parse", candidateMethods);
        Assert.DoesNotContain("Execute", candidateMethods);
        Assert.DoesNotContain("Download", batchMethods);
        Assert.DoesNotContain("Fetch", batchMethods);
        Assert.DoesNotContain("Parse", batchMethods);
        Assert.DoesNotContain("Execute", batchMethods);
        Assert.Equal(["CreateDefaultCandidateBatch"], registryMethods);
    }

    [Fact]
    public void ContractDoesNotIntroduceDbHttpFileIoDownloaderOrParserExecutionSurface()
    {
        var publicMembers = typeof(SourceDiscoveryCandidate)
            .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Concat(typeof(SourceDiscoveryCandidateBatch)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Concat(typeof(SourceDiscoveryCandidateRegistry)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly))
            .Select(member => member.Name)
            .ToArray();
        var blockedTerms = new[]
        {
            "Db",
            "Sql",
            "Postgres",
            "Open",
            "Write",
            "Exists",
            "Download",
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
