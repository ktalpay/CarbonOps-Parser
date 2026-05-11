namespace CarbonOps.Parser.Contracts;

public sealed record SourceDocumentRepositoryPersistResult
{
    public string ProviderName { get; }

    public SourceDocumentRepositoryPersistStatus Status { get; }

    public int PersistedCount { get; }

    public IReadOnlyList<SourceDocumentRepositoryIssue> Issues { get; }

    public SourceDocumentRepositoryPersistResult(
        string providerName,
        SourceDocumentRepositoryPersistStatus status,
        int persistedCount,
        IEnumerable<SourceDocumentRepositoryIssue>? issues = null)
    {
        ProviderName = providerName;
        Status = status;
        PersistedCount = persistedCount;
        Issues = Array.AsReadOnly((issues ?? []).ToArray());
    }
}
