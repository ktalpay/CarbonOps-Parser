using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class SourceFamilyRegistryTests
{
    [Fact]
    public void SupportedFamiliesContainExactlyPhaseOneFamilies()
    {
        Assert.Equal(
            [
                SourceFamily.GhgProtocol,
                SourceFamily.DefraDesnz,
                SourceFamily.IpccEfdb,
            ],
            SourceFamilyRegistry.SupportedFamilies);
    }

    [Fact]
    public void SupportedFamiliesUseDeterministicOrder()
    {
        var firstRead = SourceFamilyRegistry.SupportedFamilies.ToArray();
        var secondRead = SourceFamilyRegistry.SupportedFamilies.ToArray();

        Assert.Equal(firstRead, secondRead);
        Assert.Equal(SourceFamily.GhgProtocol, firstRead[0]);
        Assert.Equal(SourceFamily.DefraDesnz, firstRead[1]);
        Assert.Equal(SourceFamily.IpccEfdb, firstRead[2]);
    }

    [Fact]
    public void SupportedFamiliesExposePythonAlignedWireNames()
    {
        var wireNames = SourceFamilyRegistry.SupportedFamilies
            .Select(sourceFamily => sourceFamily.ToWireName())
            .ToArray();

        Assert.Equal(["ghg_protocol", "defra_desnz", "ipcc_efdb"], wireNames);
    }

    [Fact]
    public void SupportedFamiliesDoNotIncludePlaceholderFamilies()
    {
        var blockedTerms = new[] { "placeholder", "manual", "test", "fake" };
        var names = SourceFamilyRegistry.SupportedFamilies
            .SelectMany(sourceFamily => new[] { sourceFamily.ToString(), sourceFamily.ToWireName() });

        foreach (var name in names)
        {
            Assert.DoesNotContain(blockedTerms, term => name.Contains(term, StringComparison.OrdinalIgnoreCase));
        }
    }
}
