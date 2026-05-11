namespace CarbonOps.Parser.Contracts;

public interface ISourceAcquisitionRunRepository
{
    string ProviderName { get; }

    SourceAcquisitionRunRepositoryPersistResult PersistRuns(IEnumerable<SourceAcquisitionRunResult> runs);
}
