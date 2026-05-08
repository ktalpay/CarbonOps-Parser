namespace CarbonOps.Parser.Contracts;

public static class SourceFamilyRegistry
{
    public static IReadOnlyList<SourceFamily> SupportedFamilies { get; } = Array.AsReadOnly(
        new[]
        {
            SourceFamily.GhgProtocol,
            SourceFamily.DefraDesnz,
            SourceFamily.IpccEfdb,
        });
}
