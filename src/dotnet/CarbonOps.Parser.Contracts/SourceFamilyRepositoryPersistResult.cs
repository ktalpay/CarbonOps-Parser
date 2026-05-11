namespace CarbonOps.Parser.Contracts;

public sealed record SourceFamilyRepositoryPersistResult
{
    public string ProviderName { get; }

    public SourceFamilyRepositoryPersistStatus Status { get; }

    public int PersistedMasterCount { get; }

    public int PersistedDetailCount { get; }

    public IReadOnlyList<SourceFamilyRepositoryIssue> Issues { get; }

    public SourceFamilyRepositoryPersistResult(
        string providerName,
        SourceFamilyRepositoryPersistStatus status,
        int persistedMasterCount,
        int persistedDetailCount,
        IEnumerable<SourceFamilyRepositoryIssue>? issues = null)
    {
        ProviderName = providerName;
        Status = status;
        PersistedMasterCount = persistedMasterCount;
        PersistedDetailCount = persistedDetailCount;
        Issues = Array.AsReadOnly((issues ?? []).ToArray());
    }
}
