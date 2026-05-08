using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class SourceDocumentManifestRegistryTests
{
    [Fact]
    public void DefaultDryRunManifestContainsExactPhaseOneSourceFamilies()
    {
        var manifest = SourceDocumentManifestRegistry.CreateDefaultDryRunManifest();

        Assert.Equal(
            [
                SourceFamily.GhgProtocol,
                SourceFamily.DefraDesnz,
                SourceFamily.IpccEfdb,
            ],
            manifest.Entries.Select(entry => entry.SourceFamily));
    }

    [Fact]
    public void DefaultDryRunManifestUsesDeterministicOrder()
    {
        var first = SourceDocumentManifestRegistry.CreateDefaultDryRunManifest();
        var second = SourceDocumentManifestRegistry.CreateDefaultDryRunManifest();

        Assert.Equal(first.Entries, second.Entries);
        Assert.Equal(SourceFamilyRegistry.SupportedFamilies, first.Entries.Select(entry => entry.SourceFamily));
    }

    [Fact]
    public void DefaultDryRunManifestCountMatchesDownloadRequestCount()
    {
        var downloadPlan = SourceDownloadPlanRegistry.CreateDefaultDryRunPlan();
        var manifest = SourceDocumentManifestRegistry.CreateDryRunManifest(downloadPlan);

        Assert.Equal(downloadPlan.RequestCount, manifest.EntryCount);
        Assert.Equal(
            downloadPlan.Requests.Select(request => request.SourceFamily),
            manifest.Entries.Select(entry => entry.SourceFamily));
    }

    [Fact]
    public void DefaultDryRunManifestDoesNotExposeDuplicateEntries()
    {
        var manifest = SourceDocumentManifestRegistry.CreateDefaultDryRunManifest();
        var entryKeys = manifest.Entries
            .Select(entry => $"{entry.SourceFamily.ToWireName()}|{entry.SourceReference}")
            .ToArray();

        Assert.Equal(entryKeys.Length, entryKeys.Distinct().Count());
    }

    [Fact]
    public void DefaultDryRunManifestUsesDeterministicChecksumMetadata()
    {
        var manifest = SourceDocumentManifestRegistry.CreateDefaultDryRunManifest();

        Assert.Equal(
            [
                "ghg_protocol_dry_run_checksum",
                "defra_desnz_dry_run_checksum",
                "ipcc_efdb_dry_run_checksum",
            ],
            manifest.Entries.Select(entry => entry.Checksum.Value));

        foreach (var checksum in manifest.Entries.Select(entry => entry.Checksum))
        {
            Assert.Equal("dry_run_sha256", checksum.Algorithm);
            Assert.True(checksum.IsDryRunPlaceholder);
            Assert.EndsWith("_dry_run_checksum", checksum.Value);
        }
    }

    [Fact]
    public void DefaultDryRunManifestUsesSafeNonNetworkReferences()
    {
        var manifest = SourceDocumentManifestRegistry.CreateDefaultDryRunManifest();

        Assert.Equal(
            [
                "ghg_protocol_discovery_reference",
                "defra_desnz_discovery_reference",
                "ipcc_efdb_discovery_reference",
            ],
            manifest.Entries.Select(entry => entry.SourceReference));

        foreach (var reference in manifest.Entries.Select(entry => entry.SourceReference))
        {
            Assert.DoesNotContain("://", reference);
            Assert.DoesNotContain("http", reference, StringComparison.OrdinalIgnoreCase);
            Assert.EndsWith("_discovery_reference", reference);
        }
    }

    [Fact]
    public void DefaultDryRunManifestDoesNotIncludePlaceholderSourceFamilies()
    {
        var blockedTerms = new[] { "placeholder", "manual", "test", "fake" };
        var manifest = SourceDocumentManifestRegistry.CreateDefaultDryRunManifest();
        var familyNames = manifest.Entries
            .SelectMany(entry => new[] { entry.SourceFamily.ToString(), entry.SourceFamily.ToWireName() });

        foreach (var name in familyNames)
        {
            Assert.DoesNotContain(blockedTerms, term => name.Contains(term, StringComparison.OrdinalIgnoreCase));
        }
    }

    [Fact]
    public void DefaultDryRunManifestReturnsFreshSnapshots()
    {
        var first = SourceDocumentManifestRegistry.CreateDefaultDryRunManifest();
        var second = SourceDocumentManifestRegistry.CreateDefaultDryRunManifest();

        Assert.NotSame(first, second);
        Assert.NotSame(first.Entries, second.Entries);
        Assert.Equal(first.Entries, second.Entries);
    }
}
