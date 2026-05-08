namespace CarbonOps.Parser.Contracts;

public sealed record SourceAcquisitionPlan
{
    public SourceAcquisitionMode Mode { get; }

    public IReadOnlyList<SourceAcquisitionRequest> Requests { get; }

    public SourceAcquisitionPlan(
        SourceAcquisitionMode mode,
        IEnumerable<SourceAcquisitionRequest> requests)
    {
        Mode = mode;
        Requests = Array.AsReadOnly(requests.ToArray());
    }
}
