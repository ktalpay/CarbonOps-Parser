namespace CarbonOps.Parser.Contracts;

public sealed record DataQualityDiagnostic
{
    public string Code { get; }

    public string Message { get; }

    public DataQualityValidationSeverity Severity { get; }

    public DataQualityValidationCheck Check { get; }

    public string? FieldName { get; }

    public string? SourceFamily { get; }

    public DataQualityProvenanceContext? Provenance { get; }

    public IReadOnlyList<DataQualityDiagnosticContext> Context { get; }

    public DataQualityDiagnostic(
        string code,
        string message,
        DataQualityValidationSeverity severity,
        DataQualityValidationCheck check,
        string? fieldName = null,
        string? sourceFamily = null,
        DataQualityProvenanceContext? provenance = null,
        IEnumerable<DataQualityDiagnosticContext>? context = null)
    {
        Code = code;
        Message = message;
        Severity = severity;
        Check = check;
        FieldName = fieldName;
        SourceFamily = DataQualityValidation.SafeDiagnosticText(sourceFamily);
        Provenance = provenance;
        Context = Array.AsReadOnly((context ?? [])
            .OrderBy(item => item.Key, StringComparer.Ordinal)
            .Select(item => new DataQualityDiagnosticContext(
                item.Key,
                DataQualityValidation.SafeDiagnosticValue(item.Key, item.Value)))
            .ToArray());
    }
}
