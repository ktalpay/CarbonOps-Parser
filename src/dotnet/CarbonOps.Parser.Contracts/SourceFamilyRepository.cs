namespace CarbonOps.Parser.Contracts;

public interface ISourceFamilyRepository
{
    string ProviderName { get; }

    SourceFamilyRepositoryPersistResult PersistSourceFamilyRecords(
        IEnumerable<SourceFamilyMasterRecord> masterRecords,
        IEnumerable<SourceFamilyDetailRecord> detailRecords);
}
