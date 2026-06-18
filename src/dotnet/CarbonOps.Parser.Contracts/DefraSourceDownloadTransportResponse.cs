namespace CarbonOps.Parser.Contracts;

public sealed record DefraSourceDownloadTransportResponse(
    byte[] Content,
    string? ContentType = null,
    string? FinalUri = null);
