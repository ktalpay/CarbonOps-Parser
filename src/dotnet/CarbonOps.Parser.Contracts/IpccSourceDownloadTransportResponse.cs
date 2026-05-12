namespace CarbonOps.Parser.Contracts;

public sealed record IpccSourceDownloadTransportResponse(
    byte[] Content,
    string? ContentType = null,
    string? FinalUri = null);
