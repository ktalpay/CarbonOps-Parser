using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class SourceAcquisitionPlanRegistryTests
{
    [Fact]
    public void DefaultDryRunPlanContainsExactPhaseOneSourceFamilies()
    {
        var plan = SourceAcquisitionPlanRegistry.CreateDefaultDryRunPlan();

        Assert.Equal(SourceAcquisitionMode.DryRun, plan.Mode);
        Assert.Equal(
            [
                SourceFamily.GhgProtocol,
                SourceFamily.DefraDesnz,
                SourceFamily.IpccEfdb,
            ],
            plan.Requests.Select(request => request.SourceFamily));
    }

    [Fact]
    public void DefaultDryRunPlanUsesDeterministicOrder()
    {
        var first = SourceAcquisitionPlanRegistry.CreateDefaultDryRunPlan();
        var second = SourceAcquisitionPlanRegistry.CreateDefaultDryRunPlan();

        Assert.Equal(first.Mode, second.Mode);
        Assert.Equal(first.Requests, second.Requests);
        Assert.Equal(SourceFamilyRegistry.SupportedFamilies, first.Requests.Select(request => request.SourceFamily));
    }

    [Fact]
    public void DefaultDryRunPlanDoesNotExposeDuplicateFamilies()
    {
        var plan = SourceAcquisitionPlanRegistry.CreateDefaultDryRunPlan();
        var sourceFamilies = plan.Requests.Select(request => request.SourceFamily).ToArray();

        Assert.Equal(sourceFamilies.Length, sourceFamilies.Distinct().Count());
    }

    [Fact]
    public void DefaultDryRunPlanUsesDryRunModeForAllRequests()
    {
        var plan = SourceAcquisitionPlanRegistry.CreateDefaultDryRunPlan();

        Assert.Equal(SourceAcquisitionMode.DryRun, plan.Mode);
        Assert.All(plan.Requests, request => Assert.Equal(SourceAcquisitionMode.DryRun, request.Mode));
    }

    [Fact]
    public void DefaultDryRunPlanWireNamesAlignWithSourceFamilyContracts()
    {
        var plan = SourceAcquisitionPlanRegistry.CreateDefaultDryRunPlan();
        var wireNames = plan.Requests
            .Select(request => request.SourceFamily.ToWireName())
            .ToArray();

        Assert.Equal(["ghg_protocol", "defra_desnz", "ipcc_efdb"], wireNames);
    }

    [Fact]
    public void DefaultDryRunPlanUsesSafeNonNetworkReferences()
    {
        var plan = SourceAcquisitionPlanRegistry.CreateDefaultDryRunPlan();

        Assert.Equal(
            [
                "ghg_protocol_discovery_reference",
                "defra_desnz_discovery_reference",
                "ipcc_efdb_discovery_reference",
            ],
            plan.Requests.Select(request => request.SourceReference));

        foreach (var reference in plan.Requests.Select(request => request.SourceReference))
        {
            Assert.DoesNotContain("://", reference);
            Assert.DoesNotContain("http", reference, StringComparison.OrdinalIgnoreCase);
            Assert.EndsWith("_discovery_reference", reference);
        }
    }

    [Fact]
    public void DefaultDryRunPlanDoesNotIncludePlaceholderSourceFamilies()
    {
        var blockedTerms = new[] { "placeholder", "manual", "test", "fake" };
        var plan = SourceAcquisitionPlanRegistry.CreateDefaultDryRunPlan();
        var familyNames = plan.Requests
            .SelectMany(request => new[] { request.SourceFamily.ToString(), request.SourceFamily.ToWireName() });

        foreach (var name in familyNames)
        {
            Assert.DoesNotContain(blockedTerms, term => name.Contains(term, StringComparison.OrdinalIgnoreCase));
        }
    }

    [Fact]
    public void DefaultDryRunPlanReturnsFreshSnapshots()
    {
        var first = SourceAcquisitionPlanRegistry.CreateDefaultDryRunPlan();
        var second = SourceAcquisitionPlanRegistry.CreateDefaultDryRunPlan();

        Assert.NotSame(first, second);
        Assert.NotSame(first.Requests, second.Requests);
        Assert.Equal(first.Requests, second.Requests);
    }
}
