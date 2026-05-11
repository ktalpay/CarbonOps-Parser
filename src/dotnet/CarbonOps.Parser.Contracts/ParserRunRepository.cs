namespace CarbonOps.Parser.Contracts;

public interface IParserRunRepository
{
    string ProviderName { get; }

    ParserRunRepositoryPersistResult PersistRuns(IEnumerable<ParserRunResult> runs);
}
