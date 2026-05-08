using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class SourceAcquisitionPlanResultRegistryTests
{
    [Fact]
    public void DefaultDryRunResultContainsExactPhaseOneSourceFamilies()
    {
        var result = SourceAcquisitionPlanResultRegistry.CreateDefaultDryRunResult();

        Assert.Equal(SourceAcquisitionMode.DryRun, result.Mode);
        Assert.Equal(
            [
                SourceFamily.GhgProtocol,
                SourceFamily.DefraDesnz,
                SourceFamily.IpccEfdb,
            ],
            result.Results.Select(item => item.Request.SourceFamily));
    }

    [Fact]
    public void DefaultDryRunResultUsesDeterministicOrder()
    {
        var first = SourceAcquisitionPlanResultRegistry.CreateDefaultDryRunResult();
        var second = SourceAcquisitionPlanResultRegistry.CreateDefaultDryRunResult();

        Assert.Equal(first.Mode, second.Mode);
        Assert.Equal(first.Results, second.Results);
        Assert.Equal(SourceFamilyRegistry.SupportedFamilies, first.Results.Select(item => item.Request.SourceFamily));
    }

    [Fact]
    public void DefaultDryRunResultCountMatchesPlannedRequests()
    {
        var plan = SourceAcquisitionPlanRegistry.CreateDefaultDryRunPlan();
        var result = SourceAcquisitionPlanResultRegistry.CreateDryRunResult(plan);

        Assert.Equal(plan.Requests.Count, result.ResultCount);
        Assert.Equal(plan.Requests, result.Results.Select(item => item.Request));
    }

    [Fact]
    public void DefaultDryRunResultDoesNotExposeDuplicateFamilies()
    {
        var result = SourceAcquisitionPlanResultRegistry.CreateDefaultDryRunResult();
        var sourceFamilies = result.Results.Select(item => item.Request.SourceFamily).ToArray();

        Assert.Equal(sourceFamilies.Length, sourceFamilies.Distinct().Count());
    }

    [Fact]
    public void DefaultDryRunResultUsesPlannedStatusForAllRequestResults()
    {
        var result = SourceAcquisitionPlanResultRegistry.CreateDefaultDryRunResult();

        Assert.All(result.Results, item => Assert.Equal(SourceAcquisitionRequestResultStatus.Planned, item.Status));
        Assert.All(result.Results, item => Assert.Equal(SourceAcquisitionMode.DryRun, item.Request.Mode));
    }

    [Fact]
    public void DefaultDryRunResultUsesSafeNonNetworkReferences()
    {
        var result = SourceAcquisitionPlanResultRegistry.CreateDefaultDryRunResult();

        Assert.Equal(
            [
                "ghg_protocol_discovery_reference",
                "defra_desnz_discovery_reference",
                "ipcc_efdb_discovery_reference",
            ],
            result.Results.Select(item => item.Request.SourceReference));

        foreach (var reference in result.Results.Select(item => item.Request.SourceReference))
        {
            Assert.DoesNotContain("://", reference);
            Assert.DoesNotContain("http", reference, StringComparison.OrdinalIgnoreCase);
            Assert.EndsWith("_discovery_reference", reference);
        }
    }

    [Fact]
    public void DefaultDryRunResultDoesNotIncludePlaceholderSourceFamilies()
    {
        var blockedTerms = new[] { "placeholder", "manual", "test", "fake" };
        var result = SourceAcquisitionPlanResultRegistry.CreateDefaultDryRunResult();
        var familyNames = result.Results
            .SelectMany(item => new[] { item.Request.SourceFamily.ToString(), item.Request.SourceFamily.ToWireName() });

        foreach (var name in familyNames)
        {
            Assert.DoesNotContain(blockedTerms, term => name.Contains(term, StringComparison.OrdinalIgnoreCase));
        }
    }

    [Fact]
    public void DefaultDryRunResultReturnsFreshSnapshots()
    {
        var first = SourceAcquisitionPlanResultRegistry.CreateDefaultDryRunResult();
        var second = SourceAcquisitionPlanResultRegistry.CreateDefaultDryRunResult();

        Assert.NotSame(first, second);
        Assert.NotSame(first.Results, second.Results);
        Assert.Equal(first.Results, second.Results);
    }
}
