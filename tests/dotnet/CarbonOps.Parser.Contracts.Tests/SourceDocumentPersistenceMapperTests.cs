using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class SourceDocumentPersistenceMapperTests
{
    [Fact]
    public void DefaultDryRunPersistenceMappingContainsExactPhaseOneSourceFamilies()
    {
        var mapping = SourceDocumentPersistenceMapper.MapDefaultDryRunManifest();

        Assert.Equal(
            [
                SourceFamily.GhgProtocol,
                SourceFamily.DefraDesnz,
                SourceFamily.IpccEfdb,
            ],
            mapping.Records.Select(record => record.SourceFamily));
    }

    [Fact]
    public void DefaultDryRunPersistenceMappingUsesDeterministicOrder()
    {
        var first = SourceDocumentPersistenceMapper.MapDefaultDryRunManifest();
        var second = SourceDocumentPersistenceMapper.MapDefaultDryRunManifest();

        Assert.Equal(first.Records, second.Records);
        Assert.Equal(SourceFamilyRegistry.SupportedFamilies, first.Records.Select(record => record.SourceFamily));
    }

    [Fact]
    public void PersistenceRecordCountMatchesManifestEntryCount()
    {
        var manifest = SourceDocumentManifestRegistry.CreateDefaultDryRunManifest();
        var mapping = SourceDocumentPersistenceMapper.MapManifest(manifest);

        Assert.Equal(manifest.EntryCount, mapping.RecordCount);
        Assert.Equal(
            manifest.Entries.Select(entry => entry.SourceFamily),
            mapping.Records.Select(record => record.SourceFamily));
    }

    [Fact]
    public void PersistenceMappingCarriesChecksumMetadataThrough()
    {
        var manifest = SourceDocumentManifestRegistry.CreateDefaultDryRunManifest();
        var mapping = SourceDocumentPersistenceMapper.MapManifest(manifest);

        Assert.Equal(
            manifest.Entries.Select(entry => entry.Checksum.Algorithm),
            mapping.Records.Select(record => record.SourceChecksumAlgorithm));
        Assert.Equal(
            manifest.Entries.Select(entry => entry.Checksum.Value),
            mapping.Records.Select(record => record.SourceChecksumValue));
        Assert.All(mapping.Records, record => Assert.True(record.IsDryRunChecksum));
    }

    [Fact]
    public void PersistenceMappingDoesNotExposeDuplicateRecords()
    {
        var mapping = SourceDocumentPersistenceMapper.MapDefaultDryRunManifest();
        var recordKeys = mapping.Records
            .Select(record => $"{record.SourceFamily.ToWireName()}|{record.SourceDocumentReference}|{record.SourceChecksumValue}")
            .ToArray();

        Assert.Equal(recordKeys.Length, recordKeys.Distinct().Count());
    }

    [Fact]
    public void PersistenceMappingUsesSafeNonNetworkReferences()
    {
        var mapping = SourceDocumentPersistenceMapper.MapDefaultDryRunManifest();

        Assert.Equal(
            [
                "ghg_protocol_discovery_reference",
                "defra_desnz_discovery_reference",
                "ipcc_efdb_discovery_reference",
            ],
            mapping.Records.Select(record => record.SourceDocumentReference));

        foreach (var reference in mapping.Records.Select(record => record.SourceDocumentReference))
        {
            Assert.DoesNotContain("://", reference);
            Assert.DoesNotContain("http", reference, StringComparison.OrdinalIgnoreCase);
            Assert.EndsWith("_discovery_reference", reference);
        }
    }

    [Fact]
    public void PersistenceMappingDoesNotIncludePlaceholderSourceFamilies()
    {
        var blockedTerms = new[] { "placeholder", "manual", "test", "fake" };
        var mapping = SourceDocumentPersistenceMapper.MapDefaultDryRunManifest();
        var familyNames = mapping.Records
            .SelectMany(record => new[] { record.SourceFamily.ToString(), record.SourceFamily.ToWireName() });

        foreach (var name in familyNames)
        {
            Assert.DoesNotContain(blockedTerms, term => name.Contains(term, StringComparison.OrdinalIgnoreCase));
        }
    }

    [Fact]
    public void PersistenceMappingReturnsFreshSnapshots()
    {
        var first = SourceDocumentPersistenceMapper.MapDefaultDryRunManifest();
        var second = SourceDocumentPersistenceMapper.MapDefaultDryRunManifest();

        Assert.NotSame(first, second);
        Assert.NotSame(first.Records, second.Records);
        Assert.Equal(first.Records, second.Records);
    }
}
