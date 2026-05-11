namespace CarbonOps.Parser.Contracts;

public sealed record ParserRunRepositoryPersistResult
{
    public string ProviderName { get; }

    public ParserRunRepositoryPersistStatus Status { get; }

    public int PersistedCount { get; }

    public IReadOnlyList<ParserRunRepositoryIssue> Issues { get; }

    public ParserRunRepositoryPersistResult(
        string providerName,
        ParserRunRepositoryPersistStatus status,
        int persistedCount,
        IEnumerable<ParserRunRepositoryIssue>? issues = null)
    {
        ProviderName = providerName;
        Status = status;
        PersistedCount = persistedCount;
        Issues = Array.AsReadOnly((issues ?? []).ToArray());
    }
}
