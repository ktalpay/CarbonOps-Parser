namespace CarbonOps.Parser.Contracts;

public sealed record SourceDownloadRequest(
    SourceFamily SourceFamily,
    string SourceName,
    string SourceReference);
