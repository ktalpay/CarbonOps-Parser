namespace CarbonOps.Parser.Contracts;

public sealed record ParsedFactorPersistenceWriterResult
{
    public string ProviderName { get; }

    public ParsedFactorPersistenceStatus Status { get; }

    public int AttemptedMasterCount { get; }

    public int AttemptedDetailCount { get; }

    public int PersistedMasterCount { get; }

    public int PersistedDetailCount { get; }

    public int SkippedDuplicateCount { get; }

    public IReadOnlyList<ParsedFactorPersistenceIssue> Issues { get; }

    public ParsedFactorPersistenceCommand? Command { get; }

    public ParsedFactorPersistenceWriterResult(
        string providerName,
        ParsedFactorPersistenceStatus status,
        int attemptedMasterCount,
        int attemptedDetailCount,
        int persistedMasterCount,
        int persistedDetailCount,
        int skippedDuplicateCount = 0,
        IEnumerable<ParsedFactorPersistenceIssue>? issues = null,
        ParsedFactorPersistenceCommand? command = null)
    {
        ProviderName = providerName;
        Status = status;
        AttemptedMasterCount = attemptedMasterCount;
        AttemptedDetailCount = attemptedDetailCount;
        PersistedMasterCount = persistedMasterCount;
        PersistedDetailCount = persistedDetailCount;
        SkippedDuplicateCount = skippedDuplicateCount;
        Issues = Array.AsReadOnly((issues ?? []).ToArray());
        Command = command;
    }
}
