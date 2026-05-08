namespace CarbonOps.Parser.Contracts;

public static class ParserExecutionRegistry
{
    public static ParserExecutionBatch CreateDefaultDryRunExecutionBatch() =>
        CreateExecutionBatch(ParserSelectionRegistry.CreateDefaultDryRunSelectionBatch());

    public static ParserExecutionBatch CreateExecutionBatch(ParserSelectionBatch selectionBatch) =>
        new(selectionBatch.Selections.Select(CreateRequest));

    private static ParserExecutionRequest CreateRequest(ParserSelection selection)
    {
        var inputDocument = selection.InputDocument;
        var parserRunRequest = new ParserRunRequest(
            inputDocument.SourceFamily,
            inputDocument.SourceDocumentReference,
            inputDocument.SourceChecksumAlgorithm,
            inputDocument.SourceChecksumValue,
            inputDocument.IsDryRunChecksum);
        var descriptor = new ParserExecutionBoundaryDescriptor(
            selection.SourceFamily,
            selection.ParserKey,
            inputDocument.SourceFormat,
            inputDocument.ContentType,
            inputDocument.FormatHint);

        return new ParserExecutionRequest(
            selection.SourceFamily,
            selection.ParserKey,
            inputDocument,
            parserRunRequest,
            descriptor);
    }
}
