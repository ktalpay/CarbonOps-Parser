using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class ContractEnumTests
{
    [Fact]
    public void SourceFamilyIncludesPhaseOneFamilies()
    {
        SourceFamily[] values =
        [
            SourceFamily.GhgProtocol,
            SourceFamily.DefraDesnz,
            SourceFamily.IpccEfdb,
        ];

        Assert.Equal(["GhgProtocol", "DefraDesnz", "IpccEfdb"], values.Select(value => value.ToString()));
    }

    [Fact]
    public void RuntimeStatusEnumsExposeExpectedContractValues()
    {
        Assert.Equal(
            ["Pending", "Running", "Completed", "Failed", "Cancelled"],
            Enum.GetNames<IngestionRunStatus>());

        Assert.Equal(
            ["Discovered", "Downloaded", "Failed", "Skipped"],
            Enum.GetNames<SourceDocumentStatus>());

        Assert.Equal(
            ["Pending", "Running", "Completed", "Failed"],
            Enum.GetNames<ParserRunStatus>());
    }
}
