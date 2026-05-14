namespace CarbonOps.Parser.Contracts;

public sealed record DataQualityProvenanceContext
{
    public string RowIdentifier { get; }

    public string? SourceFamily { get; }

    public string? SourceKey { get; }

    public string? SourceReference { get; }

    public string? RowNumber { get; }

    public string? Provenance { get; }

    public string? DocumentId { get; }

    public DataQualityProvenanceContext(
        string rowIdentifier,
        string? sourceFamily = null,
        string? sourceKey = null,
        string? sourceReference = null,
        string? rowNumber = null,
        string? provenance = null,
        string? documentId = null)
    {
        RowIdentifier = rowIdentifier;
        SourceFamily = DataQualityValidation.SafeDiagnosticText(sourceFamily);
        SourceKey = DataQualityValidation.SafeDiagnosticText(sourceKey);
        SourceReference = DataQualityValidation.SafeDiagnosticText(sourceReference);
        RowNumber = rowNumber;
        Provenance = DataQualityValidation.SafeDiagnosticText(provenance);
        DocumentId = DataQualityValidation.SafeDiagnosticText(documentId);
    }
}
