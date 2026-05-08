using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class ContractWireNameTests
{
    public static TheoryData<SourceFamily, string> SourceFamilyWireNames => new()
    {
        { SourceFamily.GhgProtocol, "ghg_protocol" },
        { SourceFamily.DefraDesnz, "defra_desnz" },
        { SourceFamily.IpccEfdb, "ipcc_efdb" },
    };

    public static TheoryData<IngestionRunStatus, string> IngestionRunStatusWireNames => new()
    {
        { IngestionRunStatus.Pending, "pending" },
        { IngestionRunStatus.Running, "running" },
        { IngestionRunStatus.Completed, "completed" },
        { IngestionRunStatus.Failed, "failed" },
        { IngestionRunStatus.Cancelled, "cancelled" },
    };

    public static TheoryData<SourceDocumentStatus, string> SourceDocumentStatusWireNames => new()
    {
        { SourceDocumentStatus.Discovered, "discovered" },
        { SourceDocumentStatus.Downloaded, "downloaded" },
        { SourceDocumentStatus.Failed, "failed" },
        { SourceDocumentStatus.Skipped, "skipped" },
    };

    public static TheoryData<ParserRunStatus, string> ParserRunStatusWireNames => new()
    {
        { ParserRunStatus.Pending, "pending" },
        { ParserRunStatus.Running, "running" },
        { ParserRunStatus.Completed, "completed" },
        { ParserRunStatus.Failed, "failed" },
    };

    [Theory]
    [MemberData(nameof(SourceFamilyWireNames))]
    public void SourceFamiliesMapToStableWireNames(SourceFamily value, string wireName)
    {
        Assert.Equal(wireName, value.ToWireName());
        Assert.True(ContractWireNames.TryParseSourceFamilyWireName(wireName, out var parsed));
        Assert.Equal(value, parsed);
    }

    [Theory]
    [MemberData(nameof(IngestionRunStatusWireNames))]
    public void IngestionRunStatusesMapToStableWireNames(IngestionRunStatus value, string wireName)
    {
        Assert.Equal(wireName, value.ToWireName());
        Assert.True(ContractWireNames.TryParseIngestionRunStatusWireName(wireName, out var parsed));
        Assert.Equal(value, parsed);
    }

    [Theory]
    [MemberData(nameof(SourceDocumentStatusWireNames))]
    public void SourceDocumentStatusesMapToStableWireNames(SourceDocumentStatus value, string wireName)
    {
        Assert.Equal(wireName, value.ToWireName());
        Assert.True(ContractWireNames.TryParseSourceDocumentStatusWireName(wireName, out var parsed));
        Assert.Equal(value, parsed);
    }

    [Theory]
    [MemberData(nameof(ParserRunStatusWireNames))]
    public void ParserRunStatusesMapToStableWireNames(ParserRunStatus value, string wireName)
    {
        Assert.Equal(wireName, value.ToWireName());
        Assert.True(ContractWireNames.TryParseParserRunStatusWireName(wireName, out var parsed));
        Assert.Equal(value, parsed);
    }

    [Fact]
    public void WireNameParsingRejectsUnknownValues()
    {
        Assert.False(ContractWireNames.TryParseSourceFamilyWireName("unknown", out _));
        Assert.False(ContractWireNames.TryParseIngestionRunStatusWireName("complete", out _));
        Assert.False(ContractWireNames.TryParseSourceDocumentStatusWireName("", out _));
        Assert.False(ContractWireNames.TryParseParserRunStatusWireName(null, out _));
    }

    [Fact]
    public void UndefinedEnumValuesDoNotMapToWireNames()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => ((SourceFamily)999).ToWireName());
        Assert.Throws<ArgumentOutOfRangeException>(() => ((IngestionRunStatus)999).ToWireName());
        Assert.Throws<ArgumentOutOfRangeException>(() => ((SourceDocumentStatus)999).ToWireName());
        Assert.Throws<ArgumentOutOfRangeException>(() => ((ParserRunStatus)999).ToWireName());
    }
}
