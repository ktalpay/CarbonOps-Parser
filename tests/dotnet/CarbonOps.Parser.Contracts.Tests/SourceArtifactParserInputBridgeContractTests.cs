using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class SourceArtifactParserInputBridgeContractTests
{
    [Fact]
    public void ValidParserInputArtifactMetadataCanBeDerivedForPhaseOneSources()
    {
        var batch = SourceArtifactParserInputBridgeRegistry.CreateDefaultBridgeBatch();

        Assert.Equal(3, batch.BridgeCount);
        Assert.Equal(
            [
                SourceFamily.GhgProtocol,
                SourceFamily.DefraDesnz,
                SourceFamily.IpccEfdb,
            ],
            batch.Bridges.Select(bridge => bridge.SourceFamily));
        Assert.All(batch.Bridges, bridge =>
        {
            Assert.True(bridge.Validate().IsValid);
            Assert.True(bridge.ParserInputArtifact.Validate().IsValid);
        });
    }

    [Fact]
    public void SourceKeysAlignWithPhaseOneSourceMetadata()
    {
        var bridges = SourceArtifactParserInputBridgeRegistry.CreateDefaultBridgeBatch().Bridges;

        foreach (var bridge in bridges)
        {
            Assert.True(ParserAdapterDescriptorRegistry.TryGetBySourceKey(bridge.SourceKey, out var descriptor));
            Assert.NotNull(descriptor);
            Assert.Equal(descriptor!.SourceFamily, bridge.SourceFamily);
            Assert.Equal(descriptor.SourceFamily.ToWireName(), bridge.SourceKey);
            Assert.Equal(bridge.SourceKey, bridge.SourceArtifact.SourceKey);
            Assert.Equal(bridge.SourceKey, bridge.ParserInputArtifact.SourceKey);
        }
    }

    [Fact]
    public void ParserKeysAlignWithDescriptorRegistryMetadata()
    {
        var bridges = SourceArtifactParserInputBridgeRegistry.CreateDefaultBridgeBatch().Bridges;

        foreach (var bridge in bridges)
        {
            Assert.True(ParserAdapterDescriptorRegistry.TryGetBySourceFamily(bridge.SourceFamily, out var descriptor));
            Assert.NotNull(descriptor);
            Assert.Equal(descriptor!.ParserKey, bridge.ParserKey);
            Assert.Equal(descriptor.ParserKey, bridge.ParserInputArtifact.ParserKey);
        }
    }

    [Fact]
    public void ArtifactIdentifiersAndParserInputIdentifiersRejectEmptyStrings()
    {
        var bridge = SourceArtifactParserInputBridgeRegistry.CreateDefaultBridgeBatch().Bridges[0];
        var invalid = new SourceArtifactParserInputBridge(
            bridge.SourceFamily,
            bridge.SourceKey,
            bridge.ParserKey,
            "",
            " ",
            bridge.SourceArtifact,
            bridge.ParserInputArtifact);

        var result = invalid.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            [
                "SourceArtifactId is required.",
                "ParserInputArtifactId is required.",
                "SourceArtifact.ArtifactId must match SourceArtifactId.",
            ],
            result.Errors);
    }

    [Fact]
    public void DerivedParserInputMetadataPreservesExpectedArtifactMetadataDeterministically()
    {
        var sourceArtifacts = SourceDownloadArtifactRegistry.CreateDefaultArtifactBatch().Artifacts;
        var bridges = SourceArtifactParserInputBridgeRegistry.CreateDefaultBridgeBatch().Bridges;

        foreach (var pair in sourceArtifacts.Zip(bridges))
        {
            var sourceArtifact = pair.First;
            var bridge = pair.Second;
            var parserInput = bridge.ParserInputArtifact;

            Assert.Equal(sourceArtifact.SourceFamily, bridge.SourceFamily);
            Assert.Equal(sourceArtifact.SourceKey, bridge.SourceKey);
            Assert.Equal(sourceArtifact.ArtifactId, bridge.SourceArtifactId);
            Assert.Equal($"{sourceArtifact.ArtifactId}_parser_input", bridge.ParserInputArtifactId);
            Assert.Equal(sourceArtifact.SourceFormat, parserInput.SourceFormat);
            Assert.Equal(sourceArtifact.LocalReference, parserInput.ArtifactReference);
            Assert.Equal(sourceArtifact.DisplayName, parserInput.DisplayName);
            Assert.Equal(sourceArtifact.ContentType, parserInput.ContentType);
            Assert.Equal(sourceArtifact.Extension, parserInput.Extension);
            Assert.Equal(sourceArtifact.ReportingYear, parserInput.ReportingYear);
            Assert.Equal("not_supplied", parserInput.ChecksumAlgorithm);
            Assert.Equal($"{sourceArtifact.ArtifactId}_checksum_not_supplied", parserInput.ChecksumValue);
            Assert.True(parserInput.IsDryRunChecksum);
        }
    }

    [Fact]
    public void ChecksumMetadataIsPreservedWhenAvailable()
    {
        var sourceArtifact = new SourceDownloadArtifact(
            SourceFamily.DefraDesnz,
            SourceFamily.DefraDesnz.ToWireName(),
            "defra-desnz-candidate",
            "defra-desnz-artifact",
            ParserSourceFormat.DiscoveryReference,
            "defra_desnz_discovery_reference",
            "defra_desnz_local_artifact",
            "DEFRA/DESNZ artifact",
            "text/csv",
            extension: ".csv",
            checksum: new SourceDocumentChecksum("sha256", "abc123", IsDryRunPlaceholder: false),
            reportingYear: 2024);

        var bridge = SourceArtifactParserInputBridgeRegistry.CreateBridge(sourceArtifact);

        Assert.True(bridge.Validate().IsValid);
        Assert.Equal("sha256", bridge.ParserInputArtifact.ChecksumAlgorithm);
        Assert.Equal("abc123", bridge.ParserInputArtifact.ChecksumValue);
        Assert.False(bridge.ParserInputArtifact.IsDryRunChecksum);
    }

    [Fact]
    public void DivergentParserInputMetadataFailsClearly()
    {
        var bridge = SourceArtifactParserInputBridgeRegistry.CreateDefaultBridgeBatch().Bridges[0];
        var invalidParserInput = new ParserInputArtifact(
            bridge.ParserInputArtifact.SourceFamily,
            bridge.ParserInputArtifact.SourceKey,
            bridge.ParserInputArtifact.ParserKey,
            bridge.ParserInputArtifact.SourceFormat,
            "different-local-reference",
            bridge.ParserInputArtifact.DisplayName,
            bridge.ParserInputArtifact.ChecksumAlgorithm,
            bridge.ParserInputArtifact.ChecksumValue,
            bridge.ParserInputArtifact.IsDryRunChecksum,
            bridge.ParserInputArtifact.ContentType,
            bridge.ParserInputArtifact.Extension,
            bridge.ParserInputArtifact.ReportingYear);
        var invalid = new SourceArtifactParserInputBridge(
            bridge.SourceFamily,
            bridge.SourceKey,
            bridge.ParserKey,
            bridge.SourceArtifactId,
            bridge.ParserInputArtifactId,
            bridge.SourceArtifact,
            invalidParserInput);

        var result = invalid.Validate();

        Assert.False(result.IsValid);
        Assert.Contains(
            "ParserInputArtifact.ArtifactReference must match SourceArtifact.LocalReference.",
            result.Errors);
    }

    [Fact]
    public void BatchConversionOrderingIsDeterministic()
    {
        var first = SourceArtifactParserInputBridgeRegistry.CreateDefaultBridgeBatch();
        var second = SourceArtifactParserInputBridgeRegistry.CreateDefaultBridgeBatch();

        Assert.NotSame(first, second);
        Assert.NotSame(first.Bridges, second.Bridges);
        Assert.Equal(
            first.Bridges.Select(bridge => (bridge.SourceKey, bridge.SourceArtifactId, bridge.ParserInputArtifactId)),
            second.Bridges.Select(bridge => (bridge.SourceKey, bridge.SourceArtifactId, bridge.ParserInputArtifactId)));
        Assert.Equal(
            SourceDownloadArtifactRegistry.CreateDefaultArtifactBatch().Artifacts.Select(artifact => artifact.ArtifactId),
            first.Bridges.Select(bridge => bridge.SourceArtifactId));
    }

    [Fact]
    public void BridgeBatchSnapshotsBridges()
    {
        var bridges = new List<SourceArtifactParserInputBridge>
        {
            SourceArtifactParserInputBridgeRegistry.CreateDefaultBridgeBatch().Bridges[0],
        };

        var batch = new SourceArtifactParserInputBridgeBatch(bridges);
        bridges.Clear();

        Assert.Equal(1, batch.BridgeCount);
        Assert.Single(batch.Bridges);
        Assert.Equal(SourceFamily.GhgProtocol, batch.Bridges[0].SourceFamily);
    }

    [Fact]
    public void LocalReferenceMetadataIsNotOpenedStattedReadWrittenHashedOrExistenceChecked()
    {
        var sourceArtifact = new SourceDownloadArtifact(
            SourceFamily.IpccEfdb,
            SourceFamily.IpccEfdb.ToWireName(),
            "ipcc-efdb-local-candidate",
            "ipcc-efdb-local-artifact",
            ParserSourceFormat.DiscoveryReference,
            "ipcc_efdb_discovery_reference",
            "/definitely/not-present/ipcc-efdb.json",
            "IPCC EFDB artifact",
            "application/json",
            extension: ".json",
            checksum: new SourceDocumentChecksum("sha256", "abc123", IsDryRunPlaceholder: false));

        var bridge = SourceArtifactParserInputBridgeRegistry.CreateBridge(sourceArtifact);

        Assert.True(bridge.Validate().IsValid);
        Assert.Equal("/definitely/not-present/ipcc-efdb.json", bridge.ParserInputArtifact.ArtifactReference);
    }

    [Fact]
    public void UrlReferenceMetadataIsNotFetchedOrValidatedThroughNetwork()
    {
        var sourceArtifact = new SourceDownloadArtifact(
            SourceFamily.DefraDesnz,
            SourceFamily.DefraDesnz.ToWireName(),
            "defra-desnz-remote-candidate",
            "defra-desnz-remote-artifact",
            ParserSourceFormat.DiscoveryReference,
            "https://example.invalid/defra-desnz/factors.csv",
            "defra_desnz_remote_local_artifact",
            "DEFRA/DESNZ artifact",
            "text/csv",
            extension: ".csv",
            checksum: new SourceDocumentChecksum("sha256", "abc123", IsDryRunPlaceholder: false));

        var bridge = SourceArtifactParserInputBridgeRegistry.CreateBridge(sourceArtifact);

        Assert.True(bridge.Validate().IsValid);
        Assert.Equal("https://example.invalid/defra-desnz/factors.csv", bridge.SourceArtifact.SourceReference);
    }

    [Fact]
    public void ValidationDoesNotAccessDbOrExecuteParsers()
    {
        var bridge = SourceArtifactParserInputBridgeRegistry.CreateDefaultBridgeBatch().Bridges[0];

        var result = bridge.Validate();

        Assert.True(result.IsValid);
        Assert.Empty(result.Errors);
    }

    [Fact]
    public void ConstructionRemainsRuntimePassive()
    {
        var bridgeMethods = typeof(SourceArtifactParserInputBridge)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Where(method => !method.Name.StartsWith("get_", StringComparison.Ordinal))
            .Select(method => method.Name)
            .ToArray();
        var batchMethods = typeof(SourceArtifactParserInputBridgeBatch)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Where(method => !method.Name.StartsWith("get_", StringComparison.Ordinal))
            .Select(method => method.Name)
            .ToArray();
        var registryMethods = typeof(SourceArtifactParserInputBridgeRegistry)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();

        Assert.DoesNotContain("Fetch", bridgeMethods);
        Assert.DoesNotContain("Parse", bridgeMethods);
        Assert.DoesNotContain("Execute", bridgeMethods);
        Assert.DoesNotContain("Fetch", batchMethods);
        Assert.DoesNotContain("Parse", batchMethods);
        Assert.DoesNotContain("Execute", batchMethods);
        Assert.Equal(["CreateDefaultBridgeBatch", "CreateBridgeBatch", "CreateBridge"], registryMethods);
    }

    [Fact]
    public void ContractDoesNotIntroduceDbHttpFileIoParserExecutionOrRuntimeDownloaderSurface()
    {
        var publicMembers = typeof(SourceArtifactParserInputBridge)
            .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Concat(typeof(SourceArtifactParserInputBridgeBatch)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Concat(typeof(SourceArtifactParserInputBridgeRegistry)
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
}
