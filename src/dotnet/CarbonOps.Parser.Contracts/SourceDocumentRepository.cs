namespace CarbonOps.Parser.Contracts;

public interface ISourceDocumentRepository
{
    string ProviderName { get; }

    SourceDocumentRepositoryPersistResult PersistSourceDocuments(
        IEnumerable<SourceDocumentPersistenceRecord> records);
}
