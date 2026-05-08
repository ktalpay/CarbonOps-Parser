namespace CarbonOps.Parser.Contracts;

public sealed record SourceDiscoveryDocument(
    SourceFamily SourceFamily,
    string SourceName,
    string SourceReference,
    int? ReportingYear,
    SourceDiscoveryStatus Status = SourceDiscoveryStatus.Declared);
