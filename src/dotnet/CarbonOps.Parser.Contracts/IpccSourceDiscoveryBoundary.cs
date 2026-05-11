namespace CarbonOps.Parser.Contracts;

public static class IpccSourceDiscoveryBoundary
{
    private const string IpccSourceKey = "ipcc_efdb";
    private const string DiscoveryReferenceUri = "discovery://ipcc_efdb/homepage";
    private const string ArtifactKind = "discovery";

    public static IpccSourceDiscoveryRequest CreateRequest() =>
        new(
            SourceFamily.IpccEfdb,
            IpccSourceKey,
            DiscoveryReferenceUri);

    public static IpccSourceDiscoveryResult CreateResult(IpccSourceDiscoveryRequest? request = null)
    {
        var activeRequest = request ?? CreateRequest();
        var requestValidation = Validate(activeRequest);
        if (!requestValidation.IsValid)
        {
            return new IpccSourceDiscoveryResult(
                IpccSourceDiscoveryStatus.Invalid,
                activeRequest,
                Array.Empty<IpccSourceDocumentCandidate>(),
                requestValidation.Issues);
        }

        var candidate = new IpccSourceDocumentCandidate(
            SourceFamily.IpccEfdb,
            IpccSourceKey,
            "ipcc_source_discovery_candidate_001_ipcc_efdb",
            "IPCC EFDB",
            activeRequest.DiscoveryReferenceUri,
            ArtifactKind,
            versionLabel: "dn049_ipcc_discovery_boundary",
            discoveredAtLabel: "runtime_passive_discovery_unavailable");
        var candidateValidation = Validate(candidate);

        return new IpccSourceDiscoveryResult(
            candidateValidation.IsValid ? IpccSourceDiscoveryStatus.Declared : IpccSourceDiscoveryStatus.Invalid,
            activeRequest,
            candidateValidation.IsValid ? new[] { candidate } : Array.Empty<IpccSourceDocumentCandidate>(),
            candidateValidation.Issues);
    }

    public static IpccSourceDiscoveryValidationResult Validate(IpccSourceDiscoveryRequest? request)
    {
        var issues = new List<IpccSourceDiscoveryIssue>();

        if (request is null)
        {
            issues.Add(new IpccSourceDiscoveryIssue(
                "IPCC_SOURCE_DISCOVERY_MISSING_REQUEST",
                "request is required.",
                "request"));
            return new IpccSourceDiscoveryValidationResult(issues);
        }

        if (!Enum.IsDefined(request.SourceFamily))
        {
            issues.Add(new IpccSourceDiscoveryIssue(
                "IPCC_SOURCE_DISCOVERY_INVALID_SOURCE_FAMILY",
                "source_family must be a defined source family.",
                "source_family"));
        }

        ValidateRequiredText(
            request.SourceKey,
            "source_key",
            "IPCC_SOURCE_DISCOVERY_MISSING_SOURCE_KEY",
            "source_key must be a non-empty string.",
            issues);
        ValidateRequiredText(
            request.DiscoveryReferenceUri,
            "discovery_reference_uri",
            "IPCC_SOURCE_DISCOVERY_MISSING_REFERENCE_URI",
            "discovery_reference_uri must be a non-empty string.",
            issues);

        if (request.SourceFamily != SourceFamily.IpccEfdb)
        {
            issues.Add(new IpccSourceDiscoveryIssue(
                "IPCC_SOURCE_DISCOVERY_SOURCE_FAMILY_MISMATCH",
                "source_family must be ipcc_efdb.",
                "source_family"));
        }

        if (request.SourceKey != IpccSourceKey)
        {
            issues.Add(new IpccSourceDiscoveryIssue(
                "IPCC_SOURCE_DISCOVERY_SOURCE_KEY_MISMATCH",
                "source_key must be ipcc_efdb.",
                "source_key"));
        }

        if (request.Mode != IpccSourceDiscoveryMode.RuntimePassive)
        {
            issues.Add(new IpccSourceDiscoveryIssue(
                "IPCC_SOURCE_DISCOVERY_UNSUPPORTED_MODE",
                "mode must remain runtime_passive.",
                "mode"));
        }

        ValidateFalse(
            request.AllowNetwork,
            "allow_network",
            "IPCC_SOURCE_DISCOVERY_NETWORK_NOT_ALLOWED",
            "allow_network must be false for this boundary.",
            issues);
        ValidateFalse(
            request.AllowDownload,
            "allow_download",
            "IPCC_SOURCE_DISCOVERY_DOWNLOAD_NOT_ALLOWED",
            "allow_download must be false for this boundary.",
            issues);
        ValidateFalse(
            request.AllowParse,
            "allow_parse",
            "IPCC_SOURCE_DISCOVERY_PARSE_NOT_ALLOWED",
            "allow_parse must be false for this boundary.",
            issues);
        ValidateFalse(
            request.AllowDatabaseWrites,
            "allow_database_writes",
            "IPCC_SOURCE_DISCOVERY_DATABASE_WRITES_NOT_ALLOWED",
            "allow_database_writes must be false for this boundary.",
            issues);
        ValidateFalse(
            request.AllowScheduler,
            "allow_scheduler",
            "IPCC_SOURCE_DISCOVERY_SCHEDULER_NOT_ALLOWED",
            "allow_scheduler must be false for this boundary.",
            issues);

        return new IpccSourceDiscoveryValidationResult(issues);
    }

    public static IpccSourceDiscoveryValidationResult Validate(IpccSourceDocumentCandidate? candidate)
    {
        var issues = new List<IpccSourceDiscoveryIssue>();

        if (candidate is null)
        {
            issues.Add(new IpccSourceDiscoveryIssue(
                "IPCC_SOURCE_DISCOVERY_CANDIDATE_MISSING",
                "candidate is required.",
                "candidate"));
            return new IpccSourceDiscoveryValidationResult(issues);
        }

        if (!Enum.IsDefined(candidate.SourceFamily))
        {
            issues.Add(new IpccSourceDiscoveryIssue(
                "IPCC_SOURCE_DISCOVERY_CANDIDATE_INVALID_SOURCE_FAMILY",
                "source_family must be a defined source family.",
                "source_family"));
        }

        ValidateRequiredText(
            candidate.SourceKey,
            "source_key",
            "IPCC_SOURCE_DISCOVERY_CANDIDATE_MISSING_SOURCE_KEY",
            "source_key must be a non-empty string.",
            issues);
        ValidateRequiredText(
            candidate.CandidateId,
            "candidate_id",
            "IPCC_SOURCE_DISCOVERY_CANDIDATE_MISSING_CANDIDATE_ID",
            "candidate_id must be a non-empty string.",
            issues);
        ValidateRequiredText(
            candidate.Title,
            "title",
            "IPCC_SOURCE_DISCOVERY_CANDIDATE_MISSING_TITLE",
            "title must be a non-empty string.",
            issues);
        ValidateRequiredText(
            candidate.ReferenceUri,
            "reference_uri",
            "IPCC_SOURCE_DISCOVERY_CANDIDATE_MISSING_REFERENCE_URI",
            "reference_uri must be a non-empty string.",
            issues);
        ValidateRequiredText(
            candidate.ArtifactKind,
            "artifact_kind",
            "IPCC_SOURCE_DISCOVERY_CANDIDATE_MISSING_ARTIFACT_KIND",
            "artifact_kind must be a non-empty string.",
            issues);
        ValidateOptionalText(
            candidate.ContentType,
            "content_type",
            "IPCC_SOURCE_DISCOVERY_CANDIDATE_BLANK_CONTENT_TYPE",
            "content_type must be non-empty when provided.",
            issues);
        ValidateOptionalText(
            candidate.Extension,
            "extension",
            "IPCC_SOURCE_DISCOVERY_CANDIDATE_BLANK_EXTENSION",
            "extension must be non-empty when provided.",
            issues);
        ValidateOptionalText(
            candidate.ChecksumSha256,
            "checksum_sha256",
            "IPCC_SOURCE_DISCOVERY_CANDIDATE_BLANK_CHECKSUM_SHA256",
            "checksum_sha256 must be non-empty when provided.",
            issues);
        ValidateOptionalText(
            candidate.VersionLabel,
            "version_label",
            "IPCC_SOURCE_DISCOVERY_CANDIDATE_BLANK_VERSION_LABEL",
            "version_label must be non-empty when provided.",
            issues);
        ValidateOptionalText(
            candidate.DiscoveredAtLabel,
            "discovered_at_label",
            "IPCC_SOURCE_DISCOVERY_CANDIDATE_BLANK_DISCOVERED_AT_LABEL",
            "discovered_at_label must be non-empty when provided.",
            issues);
        ValidateOptionalPositiveInt(
            candidate.DocumentYear,
            "document_year",
            "IPCC_SOURCE_DISCOVERY_CANDIDATE_INVALID_DOCUMENT_YEAR",
            "document_year must be a positive integer when provided.",
            issues);
        ValidateOptionalPositiveInt(
            candidate.ReportingYear,
            "reporting_year",
            "IPCC_SOURCE_DISCOVERY_CANDIDATE_INVALID_REPORTING_YEAR",
            "reporting_year must be a positive integer when provided.",
            issues);

        if (candidate.SourceFamily != SourceFamily.IpccEfdb)
        {
            issues.Add(new IpccSourceDiscoveryIssue(
                "IPCC_SOURCE_DISCOVERY_CANDIDATE_SOURCE_FAMILY_MISMATCH",
                "source_family must match the IPCC source family.",
                "source_family"));
        }

        if (candidate.SourceKey != IpccSourceKey)
        {
            issues.Add(new IpccSourceDiscoveryIssue(
                "IPCC_SOURCE_DISCOVERY_CANDIDATE_SOURCE_KEY_MISMATCH",
                "source_key must match the IPCC source key.",
                "source_key"));
        }

        if (candidate.ArtifactKind != ArtifactKind)
        {
            issues.Add(new IpccSourceDiscoveryIssue(
                "IPCC_SOURCE_DISCOVERY_CANDIDATE_ARTIFACT_KIND_MISMATCH",
                "artifact_kind must match the IPCC expected format.",
                "artifact_kind"));
        }

        if (candidate.Status != IpccSourceDiscoveryStatus.Declared)
        {
            issues.Add(new IpccSourceDiscoveryIssue(
                "IPCC_SOURCE_DISCOVERY_CANDIDATE_UNSUPPORTED_STATUS",
                "candidate status must remain declared.",
                "status"));
        }

        if (candidate.DownloadAllowed)
        {
            issues.Add(new IpccSourceDiscoveryIssue(
                "IPCC_SOURCE_DISCOVERY_CANDIDATE_DOWNLOAD_NOT_ALLOWED",
                "download_allowed must be false for this boundary.",
                "download_allowed"));
        }

        return new IpccSourceDiscoveryValidationResult(issues);
    }

    public static IpccSourceDiscoveryValidationResult Validate(IpccSourceDiscoveryResult? result)
    {
        var issues = new List<IpccSourceDiscoveryIssue>();

        if (result is null)
        {
            issues.Add(new IpccSourceDiscoveryIssue(
                "IPCC_SOURCE_DISCOVERY_RESULT_MISSING",
                "result is required.",
                "result"));
            return new IpccSourceDiscoveryValidationResult(issues);
        }

        issues.AddRange(Validate(result.Request).Issues);

        if (!Enum.IsDefined(result.Status))
        {
            issues.Add(new IpccSourceDiscoveryIssue(
                "IPCC_SOURCE_DISCOVERY_RESULT_INVALID_STATUS",
                "status must be a defined IPCC source discovery status.",
                "status"));
        }

        foreach (var (fieldName, value) in new[]
        {
            ("no_network", result.NoNetwork),
            ("no_download", result.NoDownload),
            ("no_parse", result.NoParse),
            ("no_database_writes", result.NoDatabaseWrites),
            ("no_sql", result.NoSql),
            ("no_scheduler", result.NoScheduler),
        })
        {
            if (!value)
            {
                issues.Add(new IpccSourceDiscoveryIssue(
                    "IPCC_SOURCE_DISCOVERY_RESULT_SIDE_EFFECT_FLAG_ENABLED",
                    $"{fieldName} must remain true.",
                    fieldName));
            }
        }

        for (var index = 0; index < result.Candidates.Count; index++)
        {
            foreach (var issue in Validate(result.Candidates[index]).Issues)
            {
                issues.Add(issue with { FieldName = $"candidates[{index + 1}].{issue.FieldName}" });
            }
        }

        if (result.Status == IpccSourceDiscoveryStatus.Declared && result.Issues.Count > 0)
        {
            issues.Add(new IpccSourceDiscoveryIssue(
                "IPCC_SOURCE_DISCOVERY_RESULT_DECLARED_WITH_ISSUES",
                "declared result status must not include issue metadata.",
                "issues"));
        }

        if (result.Status == IpccSourceDiscoveryStatus.Declared && issues.Count > 0)
        {
            issues.Add(new IpccSourceDiscoveryIssue(
                "IPCC_SOURCE_DISCOVERY_RESULT_STATUS_MISMATCH",
                "declared result status requires valid metadata.",
                "status"));
        }

        if (result.Status == IpccSourceDiscoveryStatus.Invalid && result.Issues.Count == 0)
        {
            issues.Add(new IpccSourceDiscoveryIssue(
                "IPCC_SOURCE_DISCOVERY_RESULT_MISSING_INVALID_ISSUES",
                "invalid result status requires issue metadata.",
                "issues"));
        }

        return new IpccSourceDiscoveryValidationResult(issues);
    }

    private static void ValidateRequiredText(
        string? value,
        string fieldName,
        string code,
        string message,
        ICollection<IpccSourceDiscoveryIssue> issues)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            issues.Add(new IpccSourceDiscoveryIssue(code, message, fieldName));
        }
    }

    private static void ValidateOptionalText(
        string? value,
        string fieldName,
        string code,
        string message,
        ICollection<IpccSourceDiscoveryIssue> issues)
    {
        if (value is not null && string.IsNullOrWhiteSpace(value))
        {
            issues.Add(new IpccSourceDiscoveryIssue(code, message, fieldName));
        }
    }

    private static void ValidateOptionalPositiveInt(
        int? value,
        string fieldName,
        string code,
        string message,
        ICollection<IpccSourceDiscoveryIssue> issues)
    {
        if (value is <= 0)
        {
            issues.Add(new IpccSourceDiscoveryIssue(code, message, fieldName));
        }
    }

    private static void ValidateFalse(
        bool value,
        string fieldName,
        string code,
        string message,
        ICollection<IpccSourceDiscoveryIssue> issues)
    {
        if (value)
        {
            issues.Add(new IpccSourceDiscoveryIssue(code, message, fieldName));
        }
    }
}
