namespace CarbonOps.Parser.Contracts;

public sealed record ParsedFactorPersistenceCommand
{
    public IReadOnlyList<SourceFamilyMasterRecord> MasterRecords { get; }

    public IReadOnlyList<SourceFamilyDetailRecord> DetailRecords { get; }

    public int SkippedDuplicateCount { get; }

    public IReadOnlyList<ParsedFactorPersistenceIssue> Issues { get; }

    public ParsedFactorPersistenceCommand(
        IEnumerable<SourceFamilyMasterRecord> masterRecords,
        IEnumerable<SourceFamilyDetailRecord> detailRecords,
        int skippedDuplicateCount = 0,
        IEnumerable<ParsedFactorPersistenceIssue>? issues = null)
    {
        MasterRecords = Array.AsReadOnly(masterRecords.ToArray());
        DetailRecords = Array.AsReadOnly(detailRecords.ToArray());
        SkippedDuplicateCount = skippedDuplicateCount;
        Issues = Array.AsReadOnly((issues ?? []).ToArray());
    }
}
