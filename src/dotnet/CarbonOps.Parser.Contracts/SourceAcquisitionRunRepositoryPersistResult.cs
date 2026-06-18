namespace CarbonOps.Parser.Contracts;

public sealed record SourceAcquisitionRunRepositoryPersistResult
{
    public string ProviderName { get; }

    public SourceAcquisitionRunRepositoryPersistStatus Status { get; }

    public int PersistedCount { get; }

    public IReadOnlyList<SourceAcquisitionRunRepositoryIssue> Issues { get; }

    public SourceAcquisitionRunRepositoryPersistResult(
        string providerName,
        SourceAcquisitionRunRepositoryPersistStatus status,
        int persistedCount,
        IEnumerable<SourceAcquisitionRunRepositoryIssue>? issues = null)
    {
        ProviderName = providerName;
        Status = status;
        PersistedCount = persistedCount;
        Issues = Array.AsReadOnly((issues ?? []).ToArray());
    }
}
