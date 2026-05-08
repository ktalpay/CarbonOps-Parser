namespace CarbonOps.Parser.Contracts;

public sealed record Phase1OrchestrationExecutorResultBatch
{
    public IReadOnlyList<Phase1OrchestrationExecutorResult> Results { get; }

    public int ResultCount => Results.Count;

    public Phase1OrchestrationExecutorResultBatch(IEnumerable<Phase1OrchestrationExecutorResult> results)
    {
        Results = Array.AsReadOnly(results.ToArray());
    }
}
