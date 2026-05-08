namespace CarbonOps.Parser.Contracts;

public sealed record SourceAcquisitionPlanResult
{
    public SourceAcquisitionMode Mode { get; }

    public IReadOnlyList<SourceAcquisitionRequestResult> Results { get; }

    public int ResultCount => Results.Count;

    public SourceAcquisitionPlanResult(
        SourceAcquisitionMode mode,
        IEnumerable<SourceAcquisitionRequestResult> results)
    {
        Mode = mode;
        Results = Array.AsReadOnly(results.ToArray());
    }
}
