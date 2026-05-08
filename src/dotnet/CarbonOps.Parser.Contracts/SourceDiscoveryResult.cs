namespace CarbonOps.Parser.Contracts;

public sealed record SourceDiscoveryResult
{
    public SourceDiscoveryStatus Status { get; }

    public IReadOnlyList<SourceDiscoveryDocument> Documents { get; }

    public IReadOnlyList<string> Warnings { get; }

    public SourceDiscoveryResult(
        SourceDiscoveryStatus status,
        IEnumerable<SourceDiscoveryDocument> documents,
        IEnumerable<string>? warnings = null)
    {
        Status = status;
        Documents = Array.AsReadOnly(documents.ToArray());
        Warnings = Array.AsReadOnly((warnings ?? Array.Empty<string>()).ToArray());
    }
}
