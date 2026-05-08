using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class SourceAcquisitionPlanResultContractTests
{
    [Fact]
    public void SourceAcquisitionRequestResultCarriesPassiveResultShape()
    {
        var request = new SourceAcquisitionRequest(
            SourceFamily.DefraDesnz,
            "DEFRA/DESNZ",
            "defra_desnz_discovery_reference");
        var result = new SourceAcquisitionRequestResult(request);

        Assert.Equal(request, result.Request);
        Assert.Equal(SourceAcquisitionRequestResultStatus.Planned, result.Status);
    }

    [Fact]
    public void SourceAcquisitionRequestResultSupportsImmutableRecordCopy()
    {
        var request = new SourceAcquisitionRequest(
            SourceFamily.GhgProtocol,
            "GHG Protocol",
            "ghg_protocol_discovery_reference");
        var planned = new SourceAcquisitionRequestResult(request);
        var copied = planned with { Status = SourceAcquisitionRequestResultStatus.Planned };

        Assert.Equal(planned, copied);
        Assert.NotSame(planned, copied);
    }

    [Fact]
    public void SourceAcquisitionPlanResultSnapshotsResults()
    {
        var results = new List<SourceAcquisitionRequestResult>
        {
            new(new SourceAcquisitionRequest(
                SourceFamily.IpccEfdb,
                "IPCC EFDB",
                "ipcc_efdb_discovery_reference")),
        };

        var planResult = new SourceAcquisitionPlanResult(SourceAcquisitionMode.DryRun, results);

        results.Clear();

        Assert.Equal(SourceAcquisitionMode.DryRun, planResult.Mode);
        Assert.Equal(1, planResult.ResultCount);
        Assert.Single(planResult.Results);
        Assert.Equal(SourceFamily.IpccEfdb, planResult.Results[0].Request.SourceFamily);
    }
}
