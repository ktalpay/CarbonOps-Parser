namespace CarbonOps.Parser.Contracts;

public static class SourceDiscoveryRegistry
{
    public static SourceDiscoveryResult CreateDefaultDiscoveryResult() =>
        new(
            SourceDiscoveryStatus.Declared,
            SourceFamilyRegistry.SupportedFamilies.Select(CreateDiscoveryDocument));

    private static SourceDiscoveryDocument CreateDiscoveryDocument(SourceFamily sourceFamily) =>
        sourceFamily switch
        {
            SourceFamily.GhgProtocol => new SourceDiscoveryDocument(
                sourceFamily,
                "GHG Protocol",
                "ghg_protocol_discovery_reference",
                ReportingYear: null),
            SourceFamily.DefraDesnz => new SourceDiscoveryDocument(
                sourceFamily,
                "DEFRA/DESNZ",
                "defra_desnz_discovery_reference",
                ReportingYear: null),
            SourceFamily.IpccEfdb => new SourceDiscoveryDocument(
                sourceFamily,
                "IPCC EFDB",
                "ipcc_efdb_discovery_reference",
                ReportingYear: null),
            _ => throw new ArgumentOutOfRangeException(nameof(sourceFamily), sourceFamily, "Unknown source family."),
        };
}
