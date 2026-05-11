namespace CarbonOps.Parser.Contracts;

public sealed record GhgSourceDownloadTransportResponse(
    byte[] Content,
    string? ContentType = null,
    string? FinalUri = null);
