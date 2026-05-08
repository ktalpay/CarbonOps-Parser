using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class SourceDownloadPlanRegistryTests
{
    [Fact]
    public void DefaultDryRunDownloadPlanContainsExactPhaseOneSourceFamilies()
    {
        var plan = SourceDownloadPlanRegistry.CreateDefaultDryRunPlan();

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
    public void DefaultDryRunDownloadPlanUsesDeterministicOrder()
    {
        var first = SourceDownloadPlanRegistry.CreateDefaultDryRunPlan();
        var second = SourceDownloadPlanRegistry.CreateDefaultDryRunPlan();

        Assert.Equal(first.Mode, second.Mode);
        Assert.Equal(first.Requests, second.Requests);
        Assert.Equal(SourceFamilyRegistry.SupportedFamilies, first.Requests.Select(request => request.SourceFamily));
    }

    [Fact]
    public void DefaultDryRunDownloadPlanRequestCountMatchesAcquisitionResult()
    {
        var acquisitionResult = SourceAcquisitionPlanResultRegistry.CreateDefaultDryRunResult();
        var plan = SourceDownloadPlanRegistry.CreateDryRunPlan(acquisitionResult);

        Assert.Equal(acquisitionResult.ResultCount, plan.RequestCount);
        Assert.Equal(
            acquisitionResult.Results.Select(result => result.Request.SourceFamily),
            plan.Requests.Select(request => request.SourceFamily));
    }

    [Fact]
    public void DefaultDryRunDownloadPlanRequestCountMatchesDiscoveryMetadata()
    {
        var discoveryResult = SourceDiscoveryRegistry.CreateDefaultDiscoveryResult();
        var plan = SourceDownloadPlanRegistry.CreateDefaultDryRunPlan();

        Assert.Equal(discoveryResult.Documents.Count, plan.RequestCount);
        Assert.Equal(
            discoveryResult.Documents.Select(document => document.SourceFamily),
            plan.Requests.Select(request => request.SourceFamily));
    }

    [Fact]
    public void DefaultDryRunDownloadPlanDoesNotExposeDuplicateFamilies()
    {
        var plan = SourceDownloadPlanRegistry.CreateDefaultDryRunPlan();
        var sourceFamilies = plan.Requests.Select(request => request.SourceFamily).ToArray();

        Assert.Equal(sourceFamilies.Length, sourceFamilies.Distinct().Count());
    }

    [Fact]
    public void DefaultDryRunDownloadPlanDoesNotExposeDuplicateRequests()
    {
        var plan = SourceDownloadPlanRegistry.CreateDefaultDryRunPlan();
        var requestKeys = plan.Requests
            .Select(request => $"{request.SourceFamily.ToWireName()}|{request.SourceReference}")
            .ToArray();

        Assert.Equal(requestKeys.Length, requestKeys.Distinct().Count());
    }

    [Fact]
    public void DefaultDryRunDownloadPlanUsesSafeNonNetworkReferences()
    {
        var plan = SourceDownloadPlanRegistry.CreateDefaultDryRunPlan();

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
    public void DefaultDryRunDownloadPlanDoesNotIncludePlaceholderSourceFamilies()
    {
        var blockedTerms = new[] { "placeholder", "manual", "test", "fake" };
        var plan = SourceDownloadPlanRegistry.CreateDefaultDryRunPlan();
        var familyNames = plan.Requests
            .SelectMany(request => new[] { request.SourceFamily.ToString(), request.SourceFamily.ToWireName() });

        foreach (var name in familyNames)
        {
            Assert.DoesNotContain(blockedTerms, term => name.Contains(term, StringComparison.OrdinalIgnoreCase));
        }
    }

    [Fact]
    public void DefaultDryRunDownloadPlanReturnsFreshSnapshots()
    {
        var first = SourceDownloadPlanRegistry.CreateDefaultDryRunPlan();
        var second = SourceDownloadPlanRegistry.CreateDefaultDryRunPlan();

        Assert.NotSame(first, second);
        Assert.NotSame(first.Requests, second.Requests);
        Assert.Equal(first.Requests, second.Requests);
    }
}
