namespace CarbonOps.Parser.Contracts;

public static class GhgSourceDiscoveryBoundary
{
    private const string GhgSourceKey = "ghg_protocol";
    private const string DiscoveryReferenceUri = "discovery://ghg_protocol/acquisition";
    private const string ArtifactKind = "discovery";

    public static GhgSourceDiscoveryRequest CreateRequest() =>
        new(
            SourceFamily.GhgProtocol,
            GhgSourceKey,
            DiscoveryReferenceUri);

    public static GhgSourceDiscoveryResult CreateResult(GhgSourceDiscoveryRequest? request = null)
    {
        var activeRequest = request ?? CreateRequest();
        var requestValidation = Validate(activeRequest);
        if (!requestValidation.IsValid)
        {
            return new GhgSourceDiscoveryResult(
                GhgSourceDiscoveryStatus.Invalid,
                activeRequest,
                Array.Empty<GhgSourceDocumentCandidate>(),
                requestValidation.Issues);
        }

        var candidate = new GhgSourceDocumentCandidate(
            SourceFamily.GhgProtocol,
            GhgSourceKey,
            "ghg_source_discovery_candidate_001_ghg_protocol",
            "GHG Protocol",
            activeRequest.DiscoveryReferenceUri,
            ArtifactKind,
            versionLabel: "dn045_ghg_discovery_boundary",
            discoveredAtLabel: "runtime_passive_discovery_unavailable");
        var candidateValidation = Validate(candidate);

        return new GhgSourceDiscoveryResult(
            candidateValidation.IsValid ? GhgSourceDiscoveryStatus.Declared : GhgSourceDiscoveryStatus.Invalid,
            activeRequest,
            candidateValidation.IsValid ? new[] { candidate } : Array.Empty<GhgSourceDocumentCandidate>(),
            candidateValidation.Issues);
    }

    public static GhgSourceDiscoveryValidationResult Validate(GhgSourceDiscoveryRequest? request)
    {
        var issues = new List<GhgSourceDiscoveryIssue>();

        if (request is null)
        {
            issues.Add(new GhgSourceDiscoveryIssue(
                "GHG_SOURCE_DISCOVERY_MISSING_REQUEST",
                "request is required.",
                "request"));
            return new GhgSourceDiscoveryValidationResult(issues);
        }

        if (!Enum.IsDefined(request.SourceFamily))
        {
            issues.Add(new GhgSourceDiscoveryIssue(
                "GHG_SOURCE_DISCOVERY_INVALID_SOURCE_FAMILY",
                "source_family must be a defined source family.",
                "source_family"));
        }

        ValidateRequiredText(
            request.SourceKey,
            "source_key",
            "GHG_SOURCE_DISCOVERY_MISSING_SOURCE_KEY",
            "source_key must be a non-empty string.",
            issues);
        ValidateRequiredText(
            request.DiscoveryReferenceUri,
            "discovery_reference_uri",
            "GHG_SOURCE_DISCOVERY_MISSING_REFERENCE_URI",
            "discovery_reference_uri must be a non-empty string.",
            issues);

        if (request.SourceFamily != SourceFamily.GhgProtocol)
        {
            issues.Add(new GhgSourceDiscoveryIssue(
                "GHG_SOURCE_DISCOVERY_SOURCE_FAMILY_MISMATCH",
                "source_family must be ghg_protocol.",
                "source_family"));
        }

        if (request.SourceKey != GhgSourceKey)
        {
            issues.Add(new GhgSourceDiscoveryIssue(
                "GHG_SOURCE_DISCOVERY_SOURCE_KEY_MISMATCH",
                "source_key must be ghg_protocol.",
                "source_key"));
        }

        if (request.Mode != GhgSourceDiscoveryMode.RuntimePassive)
        {
            issues.Add(new GhgSourceDiscoveryIssue(
                "GHG_SOURCE_DISCOVERY_UNSUPPORTED_MODE",
                "mode must remain runtime_passive.",
                "mode"));
        }

        ValidateFalse(
            request.AllowNetwork,
            "allow_network",
            "GHG_SOURCE_DISCOVERY_NETWORK_NOT_ALLOWED",
            "allow_network must be false for this boundary.",
            issues);
        ValidateFalse(
            request.AllowDownload,
            "allow_download",
            "GHG_SOURCE_DISCOVERY_DOWNLOAD_NOT_ALLOWED",
            "allow_download must be false for this boundary.",
            issues);
        ValidateFalse(
            request.AllowParse,
            "allow_parse",
            "GHG_SOURCE_DISCOVERY_PARSE_NOT_ALLOWED",
            "allow_parse must be false for this boundary.",
            issues);
        ValidateFalse(
            request.AllowDatabaseWrites,
            "allow_database_writes",
            "GHG_SOURCE_DISCOVERY_DATABASE_WRITES_NOT_ALLOWED",
            "allow_database_writes must be false for this boundary.",
            issues);
        ValidateFalse(
            request.AllowScheduler,
            "allow_scheduler",
            "GHG_SOURCE_DISCOVERY_SCHEDULER_NOT_ALLOWED",
            "allow_scheduler must be false for this boundary.",
            issues);

        return new GhgSourceDiscoveryValidationResult(issues);
    }

    public static GhgSourceDiscoveryValidationResult Validate(GhgSourceDocumentCandidate? candidate)
    {
        var issues = new List<GhgSourceDiscoveryIssue>();

        if (candidate is null)
        {
            issues.Add(new GhgSourceDiscoveryIssue(
                "GHG_SOURCE_DISCOVERY_CANDIDATE_MISSING",
                "candidate is required.",
                "candidate"));
            return new GhgSourceDiscoveryValidationResult(issues);
        }

        if (!Enum.IsDefined(candidate.SourceFamily))
        {
            issues.Add(new GhgSourceDiscoveryIssue(
                "GHG_SOURCE_DISCOVERY_CANDIDATE_INVALID_SOURCE_FAMILY",
                "source_family must be a defined source family.",
                "source_family"));
        }

        ValidateRequiredText(
            candidate.SourceKey,
            "source_key",
            "GHG_SOURCE_DISCOVERY_CANDIDATE_MISSING_SOURCE_KEY",
            "source_key must be a non-empty string.",
            issues);
        ValidateRequiredText(
            candidate.CandidateId,
            "candidate_id",
            "GHG_SOURCE_DISCOVERY_CANDIDATE_MISSING_CANDIDATE_ID",
            "candidate_id must be a non-empty string.",
            issues);
        ValidateRequiredText(
            candidate.Title,
            "title",
            "GHG_SOURCE_DISCOVERY_CANDIDATE_MISSING_TITLE",
            "title must be a non-empty string.",
            issues);
        ValidateRequiredText(
            candidate.ReferenceUri,
            "reference_uri",
            "GHG_SOURCE_DISCOVERY_CANDIDATE_MISSING_REFERENCE_URI",
            "reference_uri must be a non-empty string.",
            issues);
        ValidateRequiredText(
            candidate.ArtifactKind,
            "artifact_kind",
            "GHG_SOURCE_DISCOVERY_CANDIDATE_MISSING_ARTIFACT_KIND",
            "artifact_kind must be a non-empty string.",
            issues);
        ValidateOptionalText(
            candidate.ContentType,
            "content_type",
            "GHG_SOURCE_DISCOVERY_CANDIDATE_BLANK_CONTENT_TYPE",
            "content_type must be non-empty when provided.",
            issues);
        ValidateOptionalText(
            candidate.Extension,
            "extension",
            "GHG_SOURCE_DISCOVERY_CANDIDATE_BLANK_EXTENSION",
            "extension must be non-empty when provided.",
            issues);
        ValidateOptionalText(
            candidate.ChecksumSha256,
            "checksum_sha256",
            "GHG_SOURCE_DISCOVERY_CANDIDATE_BLANK_CHECKSUM_SHA256",
            "checksum_sha256 must be non-empty when provided.",
            issues);
        ValidateOptionalText(
            candidate.VersionLabel,
            "version_label",
            "GHG_SOURCE_DISCOVERY_CANDIDATE_BLANK_VERSION_LABEL",
            "version_label must be non-empty when provided.",
            issues);
        ValidateOptionalText(
            candidate.DiscoveredAtLabel,
            "discovered_at_label",
            "GHG_SOURCE_DISCOVERY_CANDIDATE_BLANK_DISCOVERED_AT_LABEL",
            "discovered_at_label must be non-empty when provided.",
            issues);
        ValidateOptionalPositiveInt(
            candidate.DocumentYear,
            "document_year",
            "GHG_SOURCE_DISCOVERY_CANDIDATE_INVALID_DOCUMENT_YEAR",
            "document_year must be a positive integer when provided.",
            issues);
        ValidateOptionalPositiveInt(
            candidate.ReportingYear,
            "reporting_year",
            "GHG_SOURCE_DISCOVERY_CANDIDATE_INVALID_REPORTING_YEAR",
            "reporting_year must be a positive integer when provided.",
            issues);

        if (candidate.SourceFamily != SourceFamily.GhgProtocol)
        {
            issues.Add(new GhgSourceDiscoveryIssue(
                "GHG_SOURCE_DISCOVERY_CANDIDATE_SOURCE_FAMILY_MISMATCH",
                "source_family must match the GHG source family.",
                "source_family"));
        }

        if (candidate.SourceKey != GhgSourceKey)
        {
            issues.Add(new GhgSourceDiscoveryIssue(
                "GHG_SOURCE_DISCOVERY_CANDIDATE_SOURCE_KEY_MISMATCH",
                "source_key must match the GHG source key.",
                "source_key"));
        }

        if (candidate.ArtifactKind != ArtifactKind)
        {
            issues.Add(new GhgSourceDiscoveryIssue(
                "GHG_SOURCE_DISCOVERY_CANDIDATE_ARTIFACT_KIND_MISMATCH",
                "artifact_kind must match the GHG expected format.",
                "artifact_kind"));
        }

        if (candidate.Status != GhgSourceDiscoveryStatus.Declared)
        {
            issues.Add(new GhgSourceDiscoveryIssue(
                "GHG_SOURCE_DISCOVERY_CANDIDATE_UNSUPPORTED_STATUS",
                "candidate status must remain declared.",
                "status"));
        }

        if (candidate.DownloadAllowed)
        {
            issues.Add(new GhgSourceDiscoveryIssue(
                "GHG_SOURCE_DISCOVERY_CANDIDATE_DOWNLOAD_NOT_ALLOWED",
                "download_allowed must be false for this boundary.",
                "download_allowed"));
        }

        return new GhgSourceDiscoveryValidationResult(issues);
    }

    public static GhgSourceDiscoveryValidationResult Validate(GhgSourceDiscoveryResult? result)
    {
        var issues = new List<GhgSourceDiscoveryIssue>();

        if (result is null)
        {
            issues.Add(new GhgSourceDiscoveryIssue(
                "GHG_SOURCE_DISCOVERY_RESULT_MISSING",
                "result is required.",
                "result"));
            return new GhgSourceDiscoveryValidationResult(issues);
        }

        issues.AddRange(Validate(result.Request).Issues);

        if (!Enum.IsDefined(result.Status))
        {
            issues.Add(new GhgSourceDiscoveryIssue(
                "GHG_SOURCE_DISCOVERY_RESULT_INVALID_STATUS",
                "status must be a defined GHG source discovery status.",
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
                issues.Add(new GhgSourceDiscoveryIssue(
                    "GHG_SOURCE_DISCOVERY_RESULT_SIDE_EFFECT_FLAG_ENABLED",
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

        if (result.Status == GhgSourceDiscoveryStatus.Declared && result.Issues.Count > 0)
        {
            issues.Add(new GhgSourceDiscoveryIssue(
                "GHG_SOURCE_DISCOVERY_RESULT_DECLARED_WITH_ISSUES",
                "declared result status must not include issue metadata.",
                "issues"));
        }

        if (result.Status == GhgSourceDiscoveryStatus.Declared && issues.Count > 0)
        {
            issues.Add(new GhgSourceDiscoveryIssue(
                "GHG_SOURCE_DISCOVERY_RESULT_STATUS_MISMATCH",
                "declared result status requires valid metadata.",
                "status"));
        }

        if (result.Status == GhgSourceDiscoveryStatus.Invalid && result.Issues.Count == 0)
        {
            issues.Add(new GhgSourceDiscoveryIssue(
                "GHG_SOURCE_DISCOVERY_RESULT_MISSING_INVALID_ISSUES",
                "invalid result status requires issue metadata.",
                "issues"));
        }

        return new GhgSourceDiscoveryValidationResult(issues);
    }

    private static void ValidateRequiredText(
        string? value,
        string fieldName,
        string code,
        string message,
        ICollection<GhgSourceDiscoveryIssue> issues)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            issues.Add(new GhgSourceDiscoveryIssue(code, message, fieldName));
        }
    }

    private static void ValidateOptionalText(
        string? value,
        string fieldName,
        string code,
        string message,
        ICollection<GhgSourceDiscoveryIssue> issues)
    {
        if (value is not null && string.IsNullOrWhiteSpace(value))
        {
            issues.Add(new GhgSourceDiscoveryIssue(code, message, fieldName));
        }
    }

    private static void ValidateOptionalPositiveInt(
        int? value,
        string fieldName,
        string code,
        string message,
        ICollection<GhgSourceDiscoveryIssue> issues)
    {
        if (value is <= 0)
        {
            issues.Add(new GhgSourceDiscoveryIssue(code, message, fieldName));
        }
    }

    private static void ValidateFalse(
        bool value,
        string fieldName,
        string code,
        string message,
        ICollection<GhgSourceDiscoveryIssue> issues)
    {
        if (value)
        {
            issues.Add(new GhgSourceDiscoveryIssue(code, message, fieldName));
        }
    }
}
