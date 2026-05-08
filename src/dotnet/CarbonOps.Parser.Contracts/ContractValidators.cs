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

    public static ContractValidationResult Validate(this SourceDiscoveryCandidate? value)
    {
        var errors = new List<string>();

        if (value is null)
        {
            errors.Add("SourceDiscoveryCandidate is required.");
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

        if (string.IsNullOrWhiteSpace(value.CandidateId))
        {
            errors.Add("CandidateId is required.");
        }

        if (string.IsNullOrWhiteSpace(value.Title))
        {
            errors.Add("Title is required.");
        }

        if (value.ReportingYear is < MinimumReportingYear or > MaximumReportingYear)
        {
            errors.Add("ReportingYear must be between 1990 and 2100 when provided.");
        }

        if (string.IsNullOrWhiteSpace(value.SourceReference))
        {
            errors.Add("SourceReference is required.");
        }

        if (!Enum.IsDefined(value.ExpectedSourceFormat))
        {
            errors.Add("ExpectedSourceFormat must be a defined parser source format.");
        }

        if (string.IsNullOrWhiteSpace(value.ContentType))
        {
            errors.Add("ContentType is required.");
        }

        if (value.Extension is not null && string.IsNullOrWhiteSpace(value.Extension))
        {
            errors.Add("Extension must not be whitespace when provided.");
        }

        if (value.VersionLabel is not null && string.IsNullOrWhiteSpace(value.VersionLabel))
        {
            errors.Add("VersionLabel must not be whitespace when provided.");
        }

        if (value.Checksum is not null && string.IsNullOrWhiteSpace(value.Checksum.Algorithm))
        {
            errors.Add("Checksum.Algorithm is required when Checksum is provided.");
        }

        if (value.Checksum is not null && string.IsNullOrWhiteSpace(value.Checksum.Value))
        {
            errors.Add("Checksum.Value is required when Checksum is provided.");
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

        return ContractValidationResult.FromErrors(errors);
    }

    public static ContractValidationResult Validate(this SourceDownloadArtifact? value)
    {
        var errors = new List<string>();

        if (value is null)
        {
            errors.Add("SourceDownloadArtifact is required.");
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

        if (string.IsNullOrWhiteSpace(value.CandidateId))
        {
            errors.Add("CandidateId is required.");
        }

        if (string.IsNullOrWhiteSpace(value.ArtifactId))
        {
            errors.Add("ArtifactId is required.");
        }

        if (!Enum.IsDefined(value.SourceFormat))
        {
            errors.Add("SourceFormat must be a defined parser source format.");
        }

        if (string.IsNullOrWhiteSpace(value.SourceReference))
        {
            errors.Add("SourceReference is required.");
        }

        if (string.IsNullOrWhiteSpace(value.LocalReference))
        {
            errors.Add("LocalReference is required.");
        }

        if (value.DisplayName is not null && string.IsNullOrWhiteSpace(value.DisplayName))
        {
            errors.Add("DisplayName must not be whitespace when provided.");
        }

        if (string.IsNullOrWhiteSpace(value.ContentType))
        {
            errors.Add("ContentType is required.");
        }

        if (value.Extension is not null && string.IsNullOrWhiteSpace(value.Extension))
        {
            errors.Add("Extension must not be whitespace when provided.");
        }

        if (value.Checksum is not null && string.IsNullOrWhiteSpace(value.Checksum.Algorithm))
        {
            errors.Add("Checksum.Algorithm is required when Checksum is provided.");
        }

        if (value.Checksum is not null && string.IsNullOrWhiteSpace(value.Checksum.Value))
        {
            errors.Add("Checksum.Value is required when Checksum is provided.");
        }

        if (value.SizeBytes < 0)
        {
            errors.Add("SizeBytes must be non-negative when provided.");
        }

        if (value.ReportingYear is < MinimumReportingYear or > MaximumReportingYear)
        {
            errors.Add("ReportingYear must be between 1990 and 2100 when provided.");
        }

        if (value.VersionLabel is not null && string.IsNullOrWhiteSpace(value.VersionLabel))
        {
            errors.Add("VersionLabel must not be whitespace when provided.");
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

    public static ContractValidationResult Validate(this ParserNormalizedOutputRow? value)
    {
        var errors = new List<string>();

        if (value is null)
        {
            errors.Add("ParserNormalizedOutputRow is required.");
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

        if (string.IsNullOrWhiteSpace(value.ArtifactReference))
        {
            errors.Add("ArtifactReference is required.");
        }

        if (string.IsNullOrWhiteSpace(value.RowIdentifier))
        {
            errors.Add("RowIdentifier is required.");
        }

        if (value.SourceRowNumber <= 0)
        {
            errors.Add("SourceRowNumber must be positive when provided.");
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

        for (var index = 0; index < value.Fields.Count; index++)
        {
            if (string.IsNullOrWhiteSpace(value.Fields[index].Key))
            {
                errors.Add($"Fields[{index}].Key is required.");
            }
        }

        for (var index = 0; index < value.Issues.Count; index++)
        {
            AppendErrors(errors, $"Issues[{index}].", value.Issues[index].Validate());
        }

        return ContractValidationResult.FromErrors(errors);
    }

    public static ContractValidationResult Validate(this ParserValidationIssue? value)
    {
        var errors = new List<string>();

        if (value is null)
        {
            errors.Add("ParserValidationIssue is required.");
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

        if (!Enum.IsDefined(value.Severity))
        {
            errors.Add("ParserValidationIssueSeverity must be a defined parser validation issue severity.");
        }

        if (string.IsNullOrWhiteSpace(value.Code))
        {
            errors.Add("Code is required.");
        }

        if (string.IsNullOrWhiteSpace(value.Message))
        {
            errors.Add("Message is required.");
        }

        if (value.ArtifactReference is not null && string.IsNullOrWhiteSpace(value.ArtifactReference))
        {
            errors.Add("ArtifactReference must not be whitespace when provided.");
        }

        if (value.RowIdentifier is not null && string.IsNullOrWhiteSpace(value.RowIdentifier))
        {
            errors.Add("RowIdentifier must not be whitespace when provided.");
        }

        if (value.SourceRowNumber <= 0)
        {
            errors.Add("SourceRowNumber must be positive when provided.");
        }

        if (value.FieldKey is not null && string.IsNullOrWhiteSpace(value.FieldKey))
        {
            errors.Add("FieldKey must not be whitespace when provided.");
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

        for (var index = 0; index < value.Context.Count; index++)
        {
            if (string.IsNullOrWhiteSpace(value.Context[index].Key))
            {
                errors.Add($"Context[{index}].Key is required.");
            }
        }

        return ContractValidationResult.FromErrors(errors);
    }

    public static ContractValidationResult Validate(this ParserAdapterRunRequest? value)
    {
        var errors = new List<string>();

        if (value is null)
        {
            errors.Add("ParserAdapterRunRequest is required.");
            return ContractValidationResult.FromErrors(errors);
        }

        ValidateParserAdapterMetadata(
            errors,
            value.SourceFamily,
            value.SourceKey,
            value.ParserKey);

        if (value.Artifacts.Count == 0)
        {
            errors.Add("ParserAdapterRunRequest must include at least one input artifact.");
        }

        if (value.RunId is not null && string.IsNullOrWhiteSpace(value.RunId))
        {
            errors.Add("RunId must not be whitespace when provided.");
        }

        if (value.CorrelationId is not null && string.IsNullOrWhiteSpace(value.CorrelationId))
        {
            errors.Add("CorrelationId must not be whitespace when provided.");
        }

        if (value.RequestedReportingYear is < MinimumReportingYear or > MaximumReportingYear)
        {
            errors.Add("RequestedReportingYear must be between 1990 and 2100 when provided.");
        }

        for (var index = 0; index < value.Artifacts.Count; index++)
        {
            var artifact = value.Artifacts[index];

            AppendErrors(errors, $"Artifacts[{index}].", artifact.Validate());
            if (artifact is null)
            {
                continue;
            }

            if (artifact.SourceFamily != value.SourceFamily)
            {
                errors.Add($"Artifacts[{index}].SourceFamily must match request SourceFamily.");
            }

            if (artifact.SourceKey != value.SourceKey)
            {
                errors.Add($"Artifacts[{index}].SourceKey must match request SourceKey.");
            }

            if (artifact.ParserKey != value.ParserKey)
            {
                errors.Add($"Artifacts[{index}].ParserKey must match request ParserKey.");
            }
        }

        return ContractValidationResult.FromErrors(errors);
    }

    public static ContractValidationResult Validate(this ParserAdapterRunResult? value)
    {
        var errors = new List<string>();

        if (value is null)
        {
            errors.Add("ParserAdapterRunResult is required.");
            return ContractValidationResult.FromErrors(errors);
        }

        ValidateParserAdapterMetadata(
            errors,
            value.SourceFamily,
            value.SourceKey,
            value.ParserKey);

        if (!Enum.IsDefined(value.Status))
        {
            errors.Add("ParserRunStatus must be a defined parser run status.");
        }

        if (value.RunId is not null && string.IsNullOrWhiteSpace(value.RunId))
        {
            errors.Add("RunId must not be whitespace when provided.");
        }

        if (value.CorrelationId is not null && string.IsNullOrWhiteSpace(value.CorrelationId))
        {
            errors.Add("CorrelationId must not be whitespace when provided.");
        }

        if (value.ReportingYear is < MinimumReportingYear or > MaximumReportingYear)
        {
            errors.Add("ReportingYear must be between 1990 and 2100 when provided.");
        }

        for (var index = 0; index < value.ArtifactReferences.Count; index++)
        {
            if (string.IsNullOrWhiteSpace(value.ArtifactReferences[index]))
            {
                errors.Add($"ArtifactReferences[{index}] is required.");
            }
        }

        for (var index = 0; index < value.Rows.Count; index++)
        {
            var row = value.Rows[index];

            AppendErrors(errors, $"Rows[{index}].", row.Validate());
            if (row is null)
            {
                continue;
            }

            if (row.SourceFamily != value.SourceFamily)
            {
                errors.Add($"Rows[{index}].SourceFamily must match result SourceFamily.");
            }

            if (row.SourceKey != value.SourceKey)
            {
                errors.Add($"Rows[{index}].SourceKey must match result SourceKey.");
            }

            if (row.ParserKey != value.ParserKey)
            {
                errors.Add($"Rows[{index}].ParserKey must match result ParserKey.");
            }
        }

        for (var index = 0; index < value.ValidationIssues.Count; index++)
        {
            var issue = value.ValidationIssues[index];

            AppendErrors(errors, $"ValidationIssues[{index}].", issue.Validate());
            if (issue is null)
            {
                continue;
            }

            if (issue.SourceFamily != value.SourceFamily)
            {
                errors.Add($"ValidationIssues[{index}].SourceFamily must match result SourceFamily.");
            }

            if (issue.SourceKey != value.SourceKey)
            {
                errors.Add($"ValidationIssues[{index}].SourceKey must match result SourceKey.");
            }

            if (issue.ParserKey != value.ParserKey)
            {
                errors.Add($"ValidationIssues[{index}].ParserKey must match result ParserKey.");
            }
        }

        return ContractValidationResult.FromErrors(errors);
    }

    public static ContractValidationResult Validate(this ParserDryRunBoundaryPlan? value)
    {
        var errors = new List<string>();

        if (value is null)
        {
            errors.Add("ParserDryRunBoundaryPlan is required.");
            return ContractValidationResult.FromErrors(errors);
        }

        ValidateParserAdapterMetadata(
            errors,
            value.SourceFamily,
            value.SourceKey,
            value.ParserKey);

        AppendErrors(errors, "Request.", value.Request.Validate());

        if (value.Request.SourceFamily != value.SourceFamily)
        {
            errors.Add("Request.SourceFamily must match plan SourceFamily.");
        }

        if (value.Request.SourceKey != value.SourceKey)
        {
            errors.Add("Request.SourceKey must match plan SourceKey.");
        }

        if (value.Request.ParserKey != value.ParserKey)
        {
            errors.Add("Request.ParserKey must match plan ParserKey.");
        }

        if (!Enum.IsDefined(value.Status))
        {
            errors.Add("ParserDryRunStatus must be a defined parser dry-run status.");
        }

        if (!Enum.IsDefined(value.Readiness))
        {
            errors.Add("ParserAdapterReadiness must be a defined parser adapter readiness.");
        }

        for (var index = 0; index < value.ValidationIssues.Count; index++)
        {
            var issue = value.ValidationIssues[index];

            AppendErrors(errors, $"ValidationIssues[{index}].", issue.Validate());
            if (issue is null)
            {
                continue;
            }

            if (issue.SourceFamily != value.SourceFamily)
            {
                errors.Add($"ValidationIssues[{index}].SourceFamily must match plan SourceFamily.");
            }

            if (issue.SourceKey != value.SourceKey)
            {
                errors.Add($"ValidationIssues[{index}].SourceKey must match plan SourceKey.");
            }

            if (issue.ParserKey != value.ParserKey)
            {
                errors.Add($"ValidationIssues[{index}].ParserKey must match plan ParserKey.");
            }
        }

        return ContractValidationResult.FromErrors(errors);
    }

    public static ContractValidationResult Validate(this ParserDryRunBoundaryResult? value)
    {
        var errors = new List<string>();

        if (value is null)
        {
            errors.Add("ParserDryRunBoundaryResult is required.");
            return ContractValidationResult.FromErrors(errors);
        }

        ValidateParserAdapterMetadata(
            errors,
            value.SourceFamily,
            value.SourceKey,
            value.ParserKey);

        AppendErrors(errors, "Request.", value.Request.Validate());
        AppendErrors(errors, "RunResult.", value.RunResult.Validate());

        if (value.Request.SourceFamily != value.SourceFamily)
        {
            errors.Add("Request.SourceFamily must match result SourceFamily.");
        }

        if (value.Request.SourceKey != value.SourceKey)
        {
            errors.Add("Request.SourceKey must match result SourceKey.");
        }

        if (value.Request.ParserKey != value.ParserKey)
        {
            errors.Add("Request.ParserKey must match result ParserKey.");
        }

        if (value.RunResult.SourceFamily != value.SourceFamily)
        {
            errors.Add("RunResult.SourceFamily must match result SourceFamily.");
        }

        if (value.RunResult.SourceKey != value.SourceKey)
        {
            errors.Add("RunResult.SourceKey must match result SourceKey.");
        }

        if (value.RunResult.ParserKey != value.ParserKey)
        {
            errors.Add("RunResult.ParserKey must match result ParserKey.");
        }

        if (!Enum.IsDefined(value.Status))
        {
            errors.Add("ParserDryRunStatus must be a defined parser dry-run status.");
        }

        if (!Enum.IsDefined(value.Readiness))
        {
            errors.Add("ParserAdapterReadiness must be a defined parser adapter readiness.");
        }

        for (var index = 0; index < value.ValidationIssues.Count; index++)
        {
            var issue = value.ValidationIssues[index];

            AppendErrors(errors, $"ValidationIssues[{index}].", issue.Validate());
            if (issue is null)
            {
                continue;
            }

            if (issue.SourceFamily != value.SourceFamily)
            {
                errors.Add($"ValidationIssues[{index}].SourceFamily must match result SourceFamily.");
            }

            if (issue.SourceKey != value.SourceKey)
            {
                errors.Add($"ValidationIssues[{index}].SourceKey must match result SourceKey.");
            }

            if (issue.ParserKey != value.ParserKey)
            {
                errors.Add($"ValidationIssues[{index}].ParserKey must match result ParserKey.");
            }
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

    private static void ValidateParserAdapterMetadata(
        List<string> errors,
        SourceFamily sourceFamily,
        string sourceKey,
        ParserKey? parserKey)
    {
        if (!Enum.IsDefined(sourceFamily))
        {
            errors.Add("SourceFamily must be a defined source family.");
        }

        if (string.IsNullOrWhiteSpace(sourceKey))
        {
            errors.Add("SourceKey is required.");
        }

        if (parserKey is null || string.IsNullOrWhiteSpace(parserKey.Value))
        {
            errors.Add("ParserKey is required.");
        }

        if (!string.IsNullOrWhiteSpace(sourceKey) &&
            ContractWireNames.TryParseSourceFamilyWireName(sourceKey, out var parsedSourceFamily) &&
            parsedSourceFamily != sourceFamily)
        {
            errors.Add("SourceKey must match SourceFamily.");
        }

        if (!string.IsNullOrWhiteSpace(sourceKey) &&
            !ParserAdapterDescriptorRegistry.TryGetBySourceKey(sourceKey, out _))
        {
            errors.Add("SourceKey must match a registered parser adapter descriptor.");
        }

        if (Enum.IsDefined(sourceFamily) &&
            ParserAdapterDescriptorRegistry.TryGetBySourceFamily(sourceFamily, out var descriptor) &&
            descriptor is not null &&
            parserKey is not null &&
            !string.IsNullOrWhiteSpace(parserKey.Value) &&
            descriptor.ParserKey != parserKey)
        {
            errors.Add("ParserKey must match the registered parser adapter descriptor.");
        }
    }
}
