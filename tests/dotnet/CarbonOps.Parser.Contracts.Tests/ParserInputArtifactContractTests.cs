using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class ParserInputArtifactContractTests
{
    [Fact]
    public void ValidArtifactMetadataCanBeConstructedForPhaseOneParserAdapters()
    {
        var batch = ParserInputArtifactRegistry.CreateDefaultDryRunBatch();

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
    public void ArtifactSourceAndParserKeysAlignWithDescriptorRegistry()
    {
        var batch = ParserInputArtifactRegistry.CreateDefaultDryRunBatch();

        foreach (var artifact in batch.Artifacts)
        {
            Assert.True(ParserAdapterDescriptorRegistry.TryGetBySourceKey(artifact.SourceKey, out var descriptor));
            Assert.NotNull(descriptor);
            Assert.Equal(descriptor!.SourceFamily, artifact.SourceFamily);
            Assert.Equal(descriptor.ParserKey, artifact.ParserKey);
            Assert.Equal(descriptor.Capability.SupportedSourceFormats, [artifact.SourceFormat]);
            Assert.Contains(artifact.ContentType, descriptor.Capability.SupportedContentTypes);
        }
    }

    [Fact]
    public void ArtifactMetadataCarriesExistingParserInputMetadata()
    {
        var inputDocuments = ParserInputRegistry.CreateDefaultDryRunBatch().Documents;
        var artifacts = ParserInputArtifactRegistry.CreateDefaultDryRunBatch().Artifacts;

        foreach (var pair in inputDocuments.Zip(artifacts))
        {
            var document = pair.First;
            var artifact = pair.Second;

            Assert.Equal(document.SourceFamily, artifact.SourceFamily);
            Assert.Equal(document.SourceFamily.ToWireName(), artifact.SourceKey);
            Assert.Equal(document.SourceFormat, artifact.SourceFormat);
            Assert.Equal(document.SourceDocumentReference, artifact.ArtifactReference);
            Assert.Equal(document.SourceDocumentReference, artifact.DisplayName);
            Assert.Equal(document.SourceChecksumAlgorithm, artifact.ChecksumAlgorithm);
            Assert.Equal(document.SourceChecksumValue, artifact.ChecksumValue);
            Assert.Equal(document.IsDryRunChecksum, artifact.IsDryRunChecksum);
            Assert.Equal(document.ContentType, artifact.ContentType);
        }
    }

    [Fact]
    public void RequiredArtifactMetadataFieldsRejectEmptyStrings()
    {
        var artifact = new ParserInputArtifact(
            SourceFamily.GhgProtocol,
            "",
            new ParserKey(""),
            ParserSourceFormat.DiscoveryReference,
            " ",
            " ",
            "",
            " ",
            isDryRunChecksum: true,
            "",
            " ",
            1800);

        var result = artifact.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            [
                "SourceKey is required.",
                "ParserKey is required.",
                "ArtifactReference is required.",
                "DisplayName must not be whitespace when provided.",
                "ChecksumAlgorithm is required.",
                "ChecksumValue is required.",
                "ContentType is required.",
                "Extension must not be whitespace when provided.",
                "ReportingYear must be between 1990 and 2100 when provided.",
                "ParserKey must match the registered parser adapter descriptor.",
            ],
            result.Errors);
    }

    [Fact]
    public void ArtifactValidationDoesNotReadFilesOrCheckPathExistence()
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

        var result = artifact.Validate();

        Assert.True(result.IsValid);
        Assert.Empty(result.Errors);
    }

    [Fact]
    public void UnknownSourceMetadataFailsClearly()
    {
        var descriptor = ParserAdapterDescriptorRegistry.Descriptors[0];
        var artifact = new ParserInputArtifact(
            descriptor.SourceFamily,
            "unknown_source_family",
            descriptor.ParserKey,
            ParserSourceFormat.DiscoveryReference,
            "artifact-reference",
            null,
            "sha256",
            "abc123",
            isDryRunChecksum: false,
            "application/x-carbonops-discovery-reference",
            null,
            null);

        var result = artifact.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            ["SourceKey must match a registered parser adapter descriptor."],
            result.Errors);
    }

    [Fact]
    public void DivergentParserMetadataFailsClearly()
    {
        var descriptor = ParserAdapterDescriptorRegistry.Descriptors[2];
        var artifact = new ParserInputArtifact(
            descriptor.SourceFamily,
            descriptor.SourceFamily.ToWireName(),
            ParserSelectionRegistry.GetParserKey(SourceFamily.GhgProtocol),
            ParserSourceFormat.DiscoveryReference,
            "artifact-reference",
            null,
            "sha256",
            "abc123",
            isDryRunChecksum: false,
            "application/x-carbonops-discovery-reference",
            null,
            null);

        var result = artifact.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            ["ParserKey must match the registered parser adapter descriptor."],
            result.Errors);
    }

    [Fact]
    public void ArtifactBatchOrderingIsDeterministic()
    {
        var first = ParserInputArtifactRegistry.CreateDefaultDryRunBatch();
        var second = ParserInputArtifactRegistry.CreateDefaultDryRunBatch();

        Assert.NotSame(first, second);
        Assert.NotSame(first.Artifacts, second.Artifacts);
        Assert.Equal(first.Artifacts, second.Artifacts);
        Assert.Equal(
            ParserAdapterDescriptorRegistry.Descriptors.Select(descriptor => descriptor.SourceFamily),
            first.Artifacts.Select(artifact => artifact.SourceFamily));
        Assert.Equal(
            ParserAdapterDescriptorRegistry.Descriptors.Select(descriptor => descriptor.ParserKey),
            first.Artifacts.Select(artifact => artifact.ParserKey));
    }

    [Fact]
    public void ArtifactBatchSnapshotsArtifacts()
    {
        var artifacts = new List<ParserInputArtifact>
        {
            ParserInputArtifactRegistry.CreateDefaultDryRunBatch().Artifacts[0],
        };

        var batch = new ParserInputArtifactBatch(artifacts);
        artifacts.Clear();

        Assert.Equal(1, batch.ArtifactCount);
        Assert.Single(batch.Artifacts);
        Assert.Equal(SourceFamily.GhgProtocol, batch.Artifacts[0].SourceFamily);
    }

    [Fact]
    public void ArtifactConstructionRemainsRuntimePassive()
    {
        var artifactMethods = typeof(ParserInputArtifact)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();
        var batchMethods = typeof(ParserInputArtifactBatch)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();
        var registryMethods = typeof(ParserInputArtifactRegistry)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();

        Assert.DoesNotContain("Parse", artifactMethods);
        Assert.DoesNotContain("Execute", artifactMethods);
        Assert.DoesNotContain("Parse", batchMethods);
        Assert.DoesNotContain("Execute", batchMethods);
        Assert.DoesNotContain("Parse", registryMethods);
        Assert.DoesNotContain("Execute", registryMethods);
    }

    [Fact]
    public void ArtifactContractDoesNotIntroduceDbHttpFileIoOrParserExecutionSurface()
    {
        var publicMembers = typeof(ParserInputArtifact)
            .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Concat(typeof(ParserInputArtifactBatch)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Concat(typeof(ParserInputArtifactRegistry)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly))
            .Select(member => member.Name)
            .ToArray();
        var blockedIoTerms = new[] { "Db", "Sql", "Http", "Open", "Read", "Write", "Stat", "Exists" };

        foreach (var term in blockedIoTerms)
        {
            Assert.DoesNotContain(publicMembers, member => member.Contains(term, StringComparison.OrdinalIgnoreCase));
        }

        Assert.DoesNotContain("Parse", publicMembers);
        Assert.DoesNotContain("Execute", publicMembers);
    }
}
