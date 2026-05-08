using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class ParserInputRegistryTests
{
    [Fact]
    public void DefaultDryRunParserInputsContainExactPhaseOneSourceFamilies()
    {
        var batch = ParserInputRegistry.CreateDefaultDryRunBatch();

        Assert.Equal(
            [
                SourceFamily.GhgProtocol,
                SourceFamily.DefraDesnz,
                SourceFamily.IpccEfdb,
            ],
            batch.Documents.Select(document => document.SourceFamily));
    }

    [Fact]
    public void DefaultDryRunParserInputsUseDeterministicOrder()
    {
        var first = ParserInputRegistry.CreateDefaultDryRunBatch();
        var second = ParserInputRegistry.CreateDefaultDryRunBatch();

        Assert.Equal(first.Documents, second.Documents);
        Assert.Equal(SourceFamilyRegistry.SupportedFamilies, first.Documents.Select(document => document.SourceFamily));
    }

    [Fact]
    public void ParserInputCountMatchesSourceDocumentPersistenceRecords()
    {
        var mapping = SourceDocumentPersistenceMapper.MapDefaultDryRunManifest();
        var batch = ParserInputRegistry.CreateBatch(mapping);

        Assert.Equal(mapping.RecordCount, batch.DocumentCount);
        Assert.Equal(
            mapping.Records.Select(record => record.SourceFamily),
            batch.Documents.Select(document => document.SourceFamily));
    }

    [Fact]
    public void ParserInputSourceFormatMappingIsConservativeAndDeterministic()
    {
        var batch = ParserInputRegistry.CreateDefaultDryRunBatch();

        Assert.Equal(
            [
                ParserSourceFormat.DiscoveryReference,
                ParserSourceFormat.DiscoveryReference,
                ParserSourceFormat.DiscoveryReference,
            ],
            batch.Documents.Select(document => document.SourceFormat));
        Assert.Equal(
            [
                "discovery",
                "discovery",
                "discovery",
            ],
            batch.Documents.Select(document => document.FormatHint));
        Assert.Equal(ParserSourceFormat.DiscoveryReference, ParserInputRegistry.GetSourceFormat(SourceFamily.GhgProtocol));
        Assert.Equal(ParserSourceFormat.DiscoveryReference, ParserInputRegistry.GetSourceFormat(SourceFamily.DefraDesnz));
        Assert.Equal(ParserSourceFormat.DiscoveryReference, ParserInputRegistry.GetSourceFormat(SourceFamily.IpccEfdb));
    }

    [Fact]
    public void ParserInputDefaultsDoNotClaimDownloadedFileFormats()
    {
        var batch = ParserInputRegistry.CreateDefaultDryRunBatch();

        Assert.Equal(
            [
                "application/x-carbonops-discovery-reference",
                "application/x-carbonops-discovery-reference",
                "application/x-carbonops-discovery-reference",
            ],
            batch.Documents.Select(document => document.ContentType));
        Assert.DoesNotContain(batch.Documents, document => document.FormatHint is "csv" or "xlsx");
        Assert.DoesNotContain(batch.Documents, document => document.ContentType is "text/csv");
        Assert.DoesNotContain(
            batch.Documents,
            document => document.ContentType is "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
    }

    [Fact]
    public void ParserInputsCarryChecksumMetadataThrough()
    {
        var mapping = SourceDocumentPersistenceMapper.MapDefaultDryRunManifest();
        var batch = ParserInputRegistry.CreateBatch(mapping);

        Assert.Equal(
            mapping.Records.Select(record => record.SourceChecksumAlgorithm),
            batch.Documents.Select(document => document.SourceChecksumAlgorithm));
        Assert.Equal(
            mapping.Records.Select(record => record.SourceChecksumValue),
            batch.Documents.Select(document => document.SourceChecksumValue));
        Assert.All(batch.Documents, document => Assert.True(document.IsDryRunChecksum));
    }

    [Fact]
    public void DefaultDryRunParserInputsDoNotContainDuplicates()
    {
        var batch = ParserInputRegistry.CreateDefaultDryRunBatch();
        var inputKeys = batch.Documents
            .Select(document => $"{document.SourceFamily.ToWireName()}|{document.SourceDocumentReference}|{document.FormatHint}")
            .ToArray();

        Assert.Equal(inputKeys.Length, inputKeys.Distinct().Count());
    }

    [Fact]
    public void DefaultDryRunParserInputsUseSafeNonNetworkReferences()
    {
        var batch = ParserInputRegistry.CreateDefaultDryRunBatch();

        Assert.Equal(
            [
                "ghg_protocol_discovery_reference",
                "defra_desnz_discovery_reference",
                "ipcc_efdb_discovery_reference",
            ],
            batch.Documents.Select(document => document.SourceDocumentReference));

        foreach (var reference in batch.Documents.Select(document => document.SourceDocumentReference))
        {
            Assert.DoesNotContain("://", reference);
            Assert.DoesNotContain("http", reference, StringComparison.OrdinalIgnoreCase);
            Assert.EndsWith("_discovery_reference", reference);
        }
    }

    [Fact]
    public void DefaultDryRunParserInputsDoNotIncludePlaceholderSourceFamilies()
    {
        var blockedTerms = new[] { "placeholder", "manual", "test", "fake" };
        var batch = ParserInputRegistry.CreateDefaultDryRunBatch();
        var familyNames = batch.Documents
            .SelectMany(document => new[] { document.SourceFamily.ToString(), document.SourceFamily.ToWireName() });

        foreach (var name in familyNames)
        {
            Assert.DoesNotContain(blockedTerms, term => name.Contains(term, StringComparison.OrdinalIgnoreCase));
        }
    }

    [Fact]
    public void DefaultDryRunParserInputBatchesReturnFreshSnapshots()
    {
        var first = ParserInputRegistry.CreateDefaultDryRunBatch();
        var second = ParserInputRegistry.CreateDefaultDryRunBatch();

        Assert.NotSame(first, second);
        Assert.NotSame(first.Documents, second.Documents);
        Assert.Equal(first.Documents, second.Documents);
    }
}
