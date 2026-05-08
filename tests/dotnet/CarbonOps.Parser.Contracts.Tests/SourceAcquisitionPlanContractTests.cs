using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class SourceAcquisitionPlanContractTests
{
    [Fact]
    public void SourceAcquisitionRequestCarriesPassiveRequestShape()
    {
        var request = new SourceAcquisitionRequest(
            SourceFamily.DefraDesnz,
            "DEFRA/DESNZ",
            "defra_desnz_discovery_reference");

        Assert.Equal(SourceFamily.DefraDesnz, request.SourceFamily);
        Assert.Equal("DEFRA/DESNZ", request.SourceName);
        Assert.Equal("defra_desnz_discovery_reference", request.SourceReference);
        Assert.Equal(SourceAcquisitionMode.DryRun, request.Mode);
    }

    [Fact]
    public void SourceAcquisitionRequestSupportsImmutableRecordCopy()
    {
        var request = new SourceAcquisitionRequest(
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
    public void SourceAcquisitionPlanSnapshotsRequests()
    {
        var requests = new List<SourceAcquisitionRequest>
        {
            new(
                SourceFamily.IpccEfdb,
                "IPCC EFDB",
                "ipcc_efdb_discovery_reference"),
        };

        var plan = new SourceAcquisitionPlan(SourceAcquisitionMode.DryRun, requests);

        requests.Clear();

        Assert.Equal(SourceAcquisitionMode.DryRun, plan.Mode);
        Assert.Single(plan.Requests);
        Assert.Equal(SourceFamily.IpccEfdb, plan.Requests[0].SourceFamily);
    }
}
