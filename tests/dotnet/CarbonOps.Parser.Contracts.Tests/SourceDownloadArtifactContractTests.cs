using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class SourceDownloadArtifactContractTests
{
    [Fact]
    public void ValidDownloadedArtifactMetadataCanBeConstructedForPhaseOneSources()
    {
        var batch = SourceDownloadArtifactRegistry.CreateDefaultArtifactBatch();

        Assert.Equal(3, batch.ArtifactCount);
        Assert.Equal(
            [
                SourceFamily.GhgProtocol,
                SourceFamily.DefraDesnz,
                SourceFamily.IpccEfdb,
            ],
            batch.Artifacts.Select(artifact => artifact.SourceFamily));
        Assert.All(batch.Artifacts, artifact => Assert.True(artifact.Validate().IsValid));
    }

    [Fact]
    public void ArtifactSourceKeysAlignWithDescriptorRegistryMetadata()
    {
        var artifacts = SourceDownloadArtifactRegistry.CreateDefaultArtifactBatch().Artifacts;

        foreach (var artifact in artifacts)
        {
            Assert.True(ParserAdapterDescriptorRegistry.TryGetBySourceKey(artifact.SourceKey, out var descriptor));
            Assert.NotNull(descriptor);
            Assert.Equal(descriptor!.SourceFamily, artifact.SourceFamily);
            Assert.Equal(descriptor.SourceFamily.ToWireName(), artifact.SourceKey);
        }
    }

    [Fact]
    public void ArtifactMetadataUsesExistingDiscoveryCandidateMetadata()
    {
        var candidates = SourceDiscoveryCandidateRegistry.CreateDefaultCandidateBatch().Candidates;
        var artifacts = SourceDownloadArtifactRegistry.CreateDefaultArtifactBatch().Artifacts;

        foreach (var pair in candidates.Zip(artifacts))
        {
            var candidate = pair.First;
            var artifact = pair.Second;

            Assert.Equal(candidate.SourceFamily, artifact.SourceFamily);
            Assert.Equal(candidate.SourceKey, artifact.SourceKey);
            Assert.Equal(candidate.CandidateId, artifact.CandidateId);
            Assert.Equal($"{candidate.CandidateId}_artifact", artifact.ArtifactId);
            Assert.Equal(candidate.ExpectedSourceFormat, artifact.SourceFormat);
            Assert.Equal(candidate.SourceReference, artifact.SourceReference);
            Assert.Equal($"{candidate.CandidateId}_local_artifact", artifact.LocalReference);
            Assert.Equal(candidate.Title, artifact.DisplayName);
            Assert.Equal(candidate.ContentType, artifact.ContentType);
            Assert.Equal(candidate.Extension, artifact.Extension);
            Assert.Equal(candidate.Checksum, artifact.Checksum);
            Assert.Equal(candidate.ReportingYear, artifact.ReportingYear);
            Assert.Equal(candidate.VersionLabel, artifact.VersionLabel);
        }
    }

    [Fact]
    public void ArtifactAndCandidateIdentifiersRejectEmptyStrings()
    {
        var artifact = new SourceDownloadArtifact(
            SourceFamily.GhgProtocol,
            SourceFamily.GhgProtocol.ToWireName(),
            "",
            " ",
            ParserSourceFormat.DiscoveryReference,
            "ghg_protocol_discovery_reference",
            "ghg_protocol_local_artifact",
            "GHG Protocol",
            "application/x-carbonops-discovery-reference");

        var result = artifact.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            [
                "CandidateId is required.",
                "ArtifactId is required.",
            ],
            result.Errors);
    }

    [Fact]
    public void RequiredArtifactMetadataFieldsRejectEmptyStrings()
    {
        var artifact = new SourceDownloadArtifact(
            SourceFamily.GhgProtocol,
            "",
            "",
            " ",
            (ParserSourceFormat)999,
            "",
            "\t",
            " ",
            "",
            extension: " ",
            checksum: new SourceDocumentChecksum("", " ", IsDryRunPlaceholder: true),
            sizeBytes: -1,
            reportingYear: 1800,
            versionLabel: "");

        var result = artifact.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            [
                "SourceKey is required.",
                "CandidateId is required.",
                "ArtifactId is required.",
                "SourceFormat must be a defined parser source format.",
                "SourceReference is required.",
                "LocalReference is required.",
                "DisplayName must not be whitespace when provided.",
                "ContentType is required.",
                "Extension must not be whitespace when provided.",
                "Checksum.Algorithm is required when Checksum is provided.",
                "Checksum.Value is required when Checksum is provided.",
                "SizeBytes must be non-negative when provided.",
                "ReportingYear must be between 1990 and 2100 when provided.",
                "VersionLabel must not be whitespace when provided.",
            ],
            result.Errors);
    }

    [Fact]
    public void UnknownSourceKeyFailsClearly()
    {
        var artifact = new SourceDownloadArtifact(
            SourceFamily.GhgProtocol,
            "unknown_source_family",
            "candidate-1",
            "artifact-1",
            ParserSourceFormat.DiscoveryReference,
            "candidate-reference",
            "local-reference",
            "GHG Protocol",
            "application/x-carbonops-discovery-reference");

        var result = artifact.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            ["SourceKey must match a registered parser adapter descriptor."],
            result.Errors);
    }

    [Fact]
    public void ArtifactResultOrderingIsDeterministic()
    {
        var first = SourceDownloadArtifactRegistry.CreateDefaultArtifactBatch();
        var second = SourceDownloadArtifactRegistry.CreateDefaultArtifactBatch();

        Assert.NotSame(first, second);
        Assert.NotSame(first.Artifacts, second.Artifacts);
        Assert.Equal(first.Artifacts, second.Artifacts);
        Assert.Equal(
            SourceDiscoveryCandidateRegistry.CreateDefaultCandidateBatch().Candidates.Select(candidate => candidate.SourceFamily),
            first.Artifacts.Select(artifact => artifact.SourceFamily));
        Assert.Equal(
            SourceDiscoveryCandidateRegistry.CreateDefaultCandidateBatch().Candidates.Select(candidate => candidate.CandidateId),
            first.Artifacts.Select(artifact => artifact.CandidateId));
    }

    [Fact]
    public void ArtifactBatchSnapshotsArtifacts()
    {
        var artifacts = new List<SourceDownloadArtifact>
        {
            SourceDownloadArtifactRegistry.CreateDefaultArtifactBatch().Artifacts[0],
        };

        var batch = new SourceDownloadArtifactBatch(artifacts);
        artifacts.Clear();

        Assert.Equal(1, batch.ArtifactCount);
        Assert.Single(batch.Artifacts);
        Assert.Equal(SourceFamily.GhgProtocol, batch.Artifacts[0].SourceFamily);
    }

    [Fact]
    public void UrlReferenceMetadataIsNotFetchedOrNetworkValidated()
    {
        var artifact = new SourceDownloadArtifact(
            SourceFamily.DefraDesnz,
            SourceFamily.DefraDesnz.ToWireName(),
            "defra-desnz-remote-candidate",
            "defra-desnz-remote-artifact",
            ParserSourceFormat.DiscoveryReference,
            "https://example.invalid/defra-desnz/factors.csv",
            "defra_desnz_local_artifact",
            "DEFRA/DESNZ remote metadata",
            "text/csv",
            extension: ".csv",
            checksum: null,
            sizeBytes: 1024,
            reportingYear: 2024,
            versionLabel: "2024-static-label");

        var result = artifact.Validate();

        Assert.True(result.IsValid);
        Assert.Empty(result.Errors);
    }

    [Fact]
    public void LocalReferenceMetadataIsNotOpenedStattedReadWrittenOrExistenceChecked()
    {
        var artifact = new SourceDownloadArtifact(
            SourceFamily.IpccEfdb,
            SourceFamily.IpccEfdb.ToWireName(),
            "ipcc-efdb-local-candidate",
            "ipcc-efdb-local-artifact",
            ParserSourceFormat.DiscoveryReference,
            "ipcc_efdb_discovery_reference",
            "/definitely/not-present/ipcc-efdb.json",
            "IPCC EFDB local metadata",
            "application/json",
            extension: ".json",
            checksum: new SourceDocumentChecksum("sha256", "abc123", IsDryRunPlaceholder: false),
            sizeBytes: null,
            reportingYear: null);

        var result = artifact.Validate();

        Assert.True(result.IsValid);
        Assert.Empty(result.Errors);
    }

    [Fact]
    public void ValidationDoesNotReadFilesInspectContentAccessDbOrCallNetwork()
    {
        var artifact = new SourceDownloadArtifact(
            SourceFamily.GhgProtocol,
            SourceFamily.GhgProtocol.ToWireName(),
            "ghg-protocol-candidate",
            "ghg-protocol-artifact",
            ParserSourceFormat.DiscoveryReference,
            "ghg_protocol_discovery_reference",
            "ghg_protocol_local_artifact",
            null,
            "application/x-carbonops-discovery-reference",
            checksum: new SourceDocumentChecksum("sha256", "abc123", IsDryRunPlaceholder: false));

        var result = artifact.Validate();

        Assert.True(result.IsValid);
        Assert.Empty(result.Errors);
    }

    [Fact]
    public void ConstructionRemainsRuntimePassive()
    {
        var artifactMethods = typeof(SourceDownloadArtifact)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Where(method => !method.Name.StartsWith("get_", StringComparison.Ordinal))
            .Select(method => method.Name)
            .ToArray();
        var batchMethods = typeof(SourceDownloadArtifactBatch)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Where(method => !method.Name.StartsWith("get_", StringComparison.Ordinal))
            .Select(method => method.Name)
            .ToArray();
        var registryMethods = typeof(SourceDownloadArtifactRegistry)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();

        Assert.DoesNotContain("Fetch", artifactMethods);
        Assert.DoesNotContain("Parse", artifactMethods);
        Assert.DoesNotContain("Execute", artifactMethods);
        Assert.DoesNotContain("Fetch", batchMethods);
        Assert.DoesNotContain("Parse", batchMethods);
        Assert.DoesNotContain("Execute", batchMethods);
        Assert.Equal(["CreateDefaultArtifactBatch"], registryMethods);
    }

    [Fact]
    public void ContractDoesNotIntroduceDbHttpFileIoParserExecutionOrRuntimeDownloaderSurface()
    {
        var publicMembers = typeof(SourceDownloadArtifact)
            .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Concat(typeof(SourceDownloadArtifactBatch)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Concat(typeof(SourceDownloadArtifactRegistry)
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
            "Read",
            "Write",
            "Stat",
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
