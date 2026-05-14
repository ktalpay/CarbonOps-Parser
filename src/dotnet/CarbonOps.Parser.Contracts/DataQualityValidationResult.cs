namespace CarbonOps.Parser.Contracts;

public sealed record DataQualityValidationResult
{
    public IReadOnlyList<DataQualityDiagnostic> Diagnostics { get; }

    public bool IsValid => !HasBlockingErrors;

    public bool HasBlockingErrors => Diagnostics.Any(
        diagnostic => diagnostic.Severity == DataQualityValidationSeverity.BlockingError);

    public int BlockingErrorCount => CountSeverity(DataQualityValidationSeverity.BlockingError);

    public int WarningCount => CountSeverity(DataQualityValidationSeverity.Warning);

    public int InfoCount => CountSeverity(DataQualityValidationSeverity.Info);

    public DataQualityValidationResult(IEnumerable<DataQualityDiagnostic>? diagnostics = null)
    {
        Diagnostics = Array.AsReadOnly((diagnostics ?? []).ToArray());
    }

    private int CountSeverity(DataQualityValidationSeverity severity) =>
        Diagnostics.Count(diagnostic => diagnostic.Severity == severity);
}
