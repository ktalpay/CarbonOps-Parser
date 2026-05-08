namespace CarbonOps.Parser.Contracts;

public static class ParserRunResultRegistry
{
    public static IReadOnlyList<ParserRunRequest> CreateDefaultDryRunRequests() =>
        CreateRequests(SourceDocumentPersistenceMapper.MapDefaultDryRunManifest());

    public static IReadOnlyList<ParserRunRequest> CreateRequests(SourceDocumentPersistenceMapping mapping) =>
        Array.AsReadOnly(mapping.Records.Select(CreateRequest).ToArray());

    public static ParserRunResultSet CreateDefaultDryRunResultSet() =>
        CreateDryRunResultSet(SourceDocumentPersistenceMapper.MapDefaultDryRunManifest());

    public static ParserRunResultSet CreateDryRunResultSet(SourceDocumentPersistenceMapping mapping) =>
        new(CreateRequests(mapping).Select(CreateDryRunResult));

    private static ParserRunRequest CreateRequest(SourceDocumentPersistenceRecord record) =>
        new(
            record.SourceFamily,
            record.SourceDocumentReference,
            record.SourceChecksumAlgorithm,
            record.SourceChecksumValue,
            record.IsDryRunChecksum);

    private static ParserRunResult CreateDryRunResult(ParserRunRequest request) =>
        new(
            request,
            ParserRunStatus.Pending,
            totalRows: 0,
            acceptedRows: 0,
            rejectedRows: 0);
}
