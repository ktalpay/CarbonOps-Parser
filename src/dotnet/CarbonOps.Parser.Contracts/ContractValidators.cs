namespace CarbonOps.Parser.Contracts;

public static class ContractValidators
{
    private const int MinimumReportingYear = 1990;
    private const int MaximumReportingYear = 2100;

    public static ContractValidationResult Validate(this SourceDocumentMetadata value)
    {
        var errors = new List<string>();

        if (!Enum.IsDefined(value.SourceFamily))
        {
            errors.Add("SourceFamily must be a defined source family.");
        }

        if (!Enum.IsDefined(value.SourceDocumentStatus))
        {
            errors.Add("SourceDocumentStatus must be a defined source document status.");
        }

        if (string.IsNullOrWhiteSpace(value.SourceName))
        {
            errors.Add("SourceName is required.");
        }

        if (value.SourceUrl is not null && string.IsNullOrWhiteSpace(value.SourceUrl))
        {
            errors.Add("SourceUrl must not be whitespace when provided.");
        }

        if (value.Checksum is not null && string.IsNullOrWhiteSpace(value.Checksum))
        {
            errors.Add("Checksum must not be whitespace when provided.");
        }

        if (value.ReportingYear is < MinimumReportingYear or > MaximumReportingYear)
        {
            errors.Add("ReportingYear must be between 1990 and 2100 when provided.");
        }

        return ContractValidationResult.FromErrors(errors);
    }

    public static ContractValidationResult Validate(this ParserRunSummary value)
    {
        var errors = new List<string>();

        if (!Enum.IsDefined(value.SourceFamily))
        {
            errors.Add("SourceFamily must be a defined source family.");
        }

        if (!Enum.IsDefined(value.ParserRunStatus))
        {
            errors.Add("ParserRunStatus must be a defined parser run status.");
        }

        if (string.IsNullOrWhiteSpace(value.SourceDocumentId))
        {
            errors.Add("SourceDocumentId is required.");
        }

        if (value.TotalRows < 0)
        {
            errors.Add("TotalRows must be non-negative.");
        }

        if (value.AcceptedRows < 0)
        {
            errors.Add("AcceptedRows must be non-negative.");
        }

        if (value.RejectedRows < 0)
        {
            errors.Add("RejectedRows must be non-negative.");
        }

        if (value.AcceptedRows >= 0 &&
            value.RejectedRows >= 0 &&
            value.TotalRows >= 0 &&
            value.AcceptedRows + value.RejectedRows > value.TotalRows)
        {
            errors.Add("AcceptedRows plus RejectedRows must not exceed TotalRows.");
        }

        return ContractValidationResult.FromErrors(errors);
    }
}
