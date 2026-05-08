namespace CarbonOps.Parser.Contracts;

public sealed record SourceDownloadPlan
{
    public SourceAcquisitionMode Mode { get; }

    public IReadOnlyList<SourceDownloadRequest> Requests { get; }

    public int RequestCount => Requests.Count;

    public SourceDownloadPlan(
        SourceAcquisitionMode mode,
        IEnumerable<SourceDownloadRequest> requests)
    {
        Mode = mode;
        Requests = Array.AsReadOnly(requests.ToArray());
    }
}
