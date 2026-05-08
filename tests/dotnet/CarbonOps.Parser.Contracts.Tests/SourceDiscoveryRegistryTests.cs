using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class SourceDiscoveryRegistryTests
{
    [Fact]
    public void DefaultDiscoveryResultContainsExactPhaseOneSourceFamilies()
    {
        var result = SourceDiscoveryRegistry.CreateDefaultDiscoveryResult();

        Assert.Equal(SourceDiscoveryStatus.Declared, result.Status);
        Assert.Equal(
            [
                SourceFamily.GhgProtocol,
                SourceFamily.DefraDesnz,
                SourceFamily.IpccEfdb,
            ],
            result.Documents.Select(document => document.SourceFamily));
        Assert.Empty(result.Warnings);
    }

    [Fact]
    public void DefaultDiscoveryResultUsesDeterministicDocumentOrder()
    {
        var first = SourceDiscoveryRegistry.CreateDefaultDiscoveryResult();
        var second = SourceDiscoveryRegistry.CreateDefaultDiscoveryResult();

        Assert.Equal(first.Status, second.Status);
        Assert.Equal(first.Documents, second.Documents);
        Assert.Equal(first.Warnings, second.Warnings);
        Assert.Equal(SourceFamilyRegistry.SupportedFamilies, first.Documents.Select(document => document.SourceFamily));
    }

    [Fact]
    public void DefaultDiscoveryResultDoesNotExposeDuplicateFamilies()
    {
        var result = SourceDiscoveryRegistry.CreateDefaultDiscoveryResult();
        var sourceFamilies = result.Documents.Select(document => document.SourceFamily).ToArray();

        Assert.Equal(sourceFamilies.Length, sourceFamilies.Distinct().Count());
    }

    [Fact]
    public void DefaultDiscoveryResultWireNamesAlignWithSourceFamilyContracts()
    {
        var result = SourceDiscoveryRegistry.CreateDefaultDiscoveryResult();
        var wireNames = result.Documents
            .Select(document => document.SourceFamily.ToWireName())
            .ToArray();

        Assert.Equal(["ghg_protocol", "defra_desnz", "ipcc_efdb"], wireNames);
    }

    [Fact]
    public void DefaultDiscoveryResultUsesSafeNonNetworkReferences()
    {
        var result = SourceDiscoveryRegistry.CreateDefaultDiscoveryResult();

        Assert.Equal(
            [
                "ghg_protocol_discovery_reference",
                "defra_desnz_discovery_reference",
                "ipcc_efdb_discovery_reference",
            ],
            result.Documents.Select(document => document.SourceReference));

        foreach (var reference in result.Documents.Select(document => document.SourceReference))
        {
            Assert.DoesNotContain("://", reference);
            Assert.DoesNotContain("http", reference, StringComparison.OrdinalIgnoreCase);
            Assert.EndsWith("_discovery_reference", reference);
        }
    }

    [Fact]
    public void DefaultDiscoveryResultDoesNotIncludePlaceholderSourceFamilies()
    {
        var blockedTerms = new[] { "placeholder", "manual", "test", "fake" };
        var result = SourceDiscoveryRegistry.CreateDefaultDiscoveryResult();
        var familyNames = result.Documents
            .SelectMany(document => new[] { document.SourceFamily.ToString(), document.SourceFamily.ToWireName() });

        foreach (var name in familyNames)
        {
            Assert.DoesNotContain(blockedTerms, term => name.Contains(term, StringComparison.OrdinalIgnoreCase));
        }
    }

    [Fact]
    public void DefaultDiscoveryResultReturnsFreshSnapshots()
    {
        var first = SourceDiscoveryRegistry.CreateDefaultDiscoveryResult();
        var second = SourceDiscoveryRegistry.CreateDefaultDiscoveryResult();

        Assert.NotSame(first, second);
        Assert.NotSame(first.Documents, second.Documents);
        Assert.Equal(first.Documents, second.Documents);
    }
}
