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

    public static ContractValidationResult Validate(this ParserRunRequest? value)
    {
        var errors = new List<string>();

        if (value is null)
        {
            errors.Add("ParserRunRequest is required.");
            return ContractValidationResult.FromErrors(errors);
        }

        if (!Enum.IsDefined(value.SourceFamily))
        {
            errors.Add("SourceFamily must be a defined source family.");
        }

        if (string.IsNullOrWhiteSpace(value.SourceDocumentReference))
        {
            errors.Add("SourceDocumentReference is required.");
        }

        if (string.IsNullOrWhiteSpace(value.SourceChecksumAlgorithm))
        {
            errors.Add("SourceChecksumAlgorithm is required.");
        }

        if (string.IsNullOrWhiteSpace(value.SourceChecksumValue))
        {
            errors.Add("SourceChecksumValue is required.");
        }

        return ContractValidationResult.FromErrors(errors);
    }

    public static ContractValidationResult Validate(this ParserInputArtifact? value)
    {
        var errors = new List<string>();

        if (value is null)
        {
            errors.Add("ParserInputArtifact is required.");
            return ContractValidationResult.FromErrors(errors);
        }

        if (!Enum.IsDefined(value.SourceFamily))
        {
            errors.Add("SourceFamily must be a defined source family.");
        }

        if (string.IsNullOrWhiteSpace(value.SourceKey))
        {
            errors.Add("SourceKey is required.");
        }

        if (value.ParserKey is null || string.IsNullOrWhiteSpace(value.ParserKey.Value))
        {
            errors.Add("ParserKey is required.");
        }

        if (!Enum.IsDefined(value.SourceFormat))
        {
            errors.Add("SourceFormat must be a defined parser source format.");
        }

        if (string.IsNullOrWhiteSpace(value.ArtifactReference))
        {
            errors.Add("ArtifactReference is required.");
        }

        if (value.DisplayName is not null && string.IsNullOrWhiteSpace(value.DisplayName))
        {
            errors.Add("DisplayName must not be whitespace when provided.");
        }

        if (string.IsNullOrWhiteSpace(value.ChecksumAlgorithm))
        {
            errors.Add("ChecksumAlgorithm is required.");
        }

        if (string.IsNullOrWhiteSpace(value.ChecksumValue))
        {
            errors.Add("ChecksumValue is required.");
        }

        if (string.IsNullOrWhiteSpace(value.ContentType))
        {
            errors.Add("ContentType is required.");
        }

        if (value.Extension is not null && string.IsNullOrWhiteSpace(value.Extension))
        {
            errors.Add("Extension must not be whitespace when provided.");
        }

        if (value.ReportingYear is < MinimumReportingYear or > MaximumReportingYear)
        {
            errors.Add("ReportingYear must be between 1990 and 2100 when provided.");
        }

        if (!string.IsNullOrWhiteSpace(value.SourceKey) &&
            ContractWireNames.TryParseSourceFamilyWireName(value.SourceKey, out var sourceFamily) &&
            sourceFamily != value.SourceFamily)
        {
            errors.Add("SourceKey must match SourceFamily.");
        }

        if (!string.IsNullOrWhiteSpace(value.SourceKey) &&
            !ParserAdapterDescriptorRegistry.TryGetBySourceKey(value.SourceKey, out _))
        {
            errors.Add("SourceKey must match a registered parser adapter descriptor.");
        }

        if (Enum.IsDefined(value.SourceFamily) &&
            ParserAdapterDescriptorRegistry.TryGetBySourceFamily(value.SourceFamily, out var descriptor) &&
            descriptor is not null &&
            value.ParserKey is not null &&
            descriptor.ParserKey != value.ParserKey)
        {
            errors.Add("ParserKey must match the registered parser adapter descriptor.");
        }

        return ContractValidationResult.FromErrors(errors);
    }

    public static ContractValidationResult Validate(this ParserRunIssue? value)
    {
        var errors = new List<string>();

        if (value is null)
        {
            errors.Add("ParserRunIssue is required.");
            return ContractValidationResult.FromErrors(errors);
        }

        if (string.IsNullOrWhiteSpace(value.Code))
        {
            errors.Add("Code is required.");
        }

        if (string.IsNullOrWhiteSpace(value.Message))
        {
            errors.Add("Message is required.");
        }

        if (!Enum.IsDefined(value.Severity))
        {
            errors.Add("ParserRunIssueSeverity must be a defined parser run issue severity.");
        }

        if (value.Location is not null && string.IsNullOrWhiteSpace(value.Location))
        {
            errors.Add("Location must not be whitespace when provided.");
        }

        return ContractValidationResult.FromErrors(errors);
    }

    public static ContractValidationResult Validate(this ParserRunResult? value)
    {
        var errors = new List<string>();

        if (value is null)
        {
            errors.Add("ParserRunResult is required.");
            return ContractValidationResult.FromErrors(errors);
        }

        AppendErrors(errors, "Request.", value.Request.Validate());

        if (!Enum.IsDefined(value.Status))
        {
            errors.Add("ParserRunStatus must be a defined parser run status.");
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

        for (var index = 0; index < value.Issues.Count; index++)
        {
            AppendErrors(errors, $"Issues[{index}].", value.Issues[index].Validate());
        }

        return ContractValidationResult.FromErrors(errors);
    }

    public static ContractValidationResult Validate(this ParserRunResultSet? value)
    {
        var errors = new List<string>();
        var requestKeys = new HashSet<string>(StringComparer.Ordinal);

        if (value is null)
        {
            errors.Add("ParserRunResultSet is required.");
            return ContractValidationResult.FromErrors(errors);
        }

        for (var index = 0; index < value.Results.Count; index++)
        {
            var result = value.Results[index];

            AppendErrors(errors, $"Results[{index}].", result.Validate());
            if (result is null)
            {
                continue;
            }

            var request = result.Request;
            if (request is null)
            {
                continue;
            }

            var requestKey = string.Join(
                "|",
                (int)request.SourceFamily,
                request.SourceDocumentReference,
                request.SourceChecksumAlgorithm,
                request.SourceChecksumValue);

            if (!requestKeys.Add(requestKey))
            {
                errors.Add("ParserRunResultSet must not contain duplicate parser run requests.");
            }
        }

        return ContractValidationResult.FromErrors(errors);
    }

    private static void AppendErrors(
        List<string> errors,
        string prefix,
        ContractValidationResult validationResult)
    {
        errors.AddRange(validationResult.Errors.Select(error => $"{prefix}{error}"));
    }
}
