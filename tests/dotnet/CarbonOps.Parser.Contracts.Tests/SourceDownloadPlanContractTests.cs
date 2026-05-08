using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class SourceDownloadPlanContractTests
{
    [Fact]
    public void SourceDownloadRequestCarriesPassiveRequestShape()
    {
        var request = new SourceDownloadRequest(
            SourceFamily.DefraDesnz,
            "DEFRA/DESNZ",
            "defra_desnz_discovery_reference");

        Assert.Equal(SourceFamily.DefraDesnz, request.SourceFamily);
        Assert.Equal("DEFRA/DESNZ", request.SourceName);
        Assert.Equal("defra_desnz_discovery_reference", request.SourceReference);
    }

    [Fact]
    public void SourceDownloadRequestSupportsImmutableRecordCopy()
    {
        var request = new SourceDownloadRequest(
            SourceFamily.GhgProtocol,
            "GHG Protocol",
            "ghg_protocol_discovery_reference");

        var renamed = request with { SourceName = "GHG Protocol factors" };

        Assert.Equal("GHG Protocol", request.SourceName);
        Assert.Equal("GHG Protocol factors", renamed.SourceName);
        Assert.Equal(request.SourceFamily, renamed.SourceFamily);
        Assert.Equal(request.SourceReference, renamed.SourceReference);
    }

    [Fact]
    public void SourceDownloadPlanSnapshotsRequests()
    {
        var requests = new List<SourceDownloadRequest>
        {
            new(
                SourceFamily.IpccEfdb,
                "IPCC EFDB",
                "ipcc_efdb_discovery_reference"),
        };

        var plan = new SourceDownloadPlan(SourceAcquisitionMode.DryRun, requests);

        requests.Clear();

        Assert.Equal(SourceAcquisitionMode.DryRun, plan.Mode);
        Assert.Equal(1, plan.RequestCount);
        Assert.Single(plan.Requests);
        Assert.Equal(SourceFamily.IpccEfdb, plan.Requests[0].SourceFamily);
    }
}
