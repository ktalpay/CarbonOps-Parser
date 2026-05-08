namespace CarbonOps.Parser.Contracts;

public sealed record SourceAcquisitionRequest(
    SourceFamily SourceFamily,
    string SourceName,
    string SourceReference,
    SourceAcquisitionMode Mode = SourceAcquisitionMode.DryRun);
