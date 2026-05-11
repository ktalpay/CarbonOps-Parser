using System.Security.Cryptography;

namespace CarbonOps.Parser.Contracts;

public static class GhgSourceDownloadExecutionBoundary
{
    private const string GhgSourceKey = "ghg_protocol";

    public static GhgSourceDownloadExecutionRequest CreateRequest(
        GhgSourceDocumentCandidate candidate,
        string targetRoot,
        string targetRelativePath,
        bool allowDownloadExecution = false,
        bool allowFileWrite = false,
        bool allowNetwork = false,
        bool allowOverwrite = false) =>
        new(
            candidate.SourceFamily,
            candidate.SourceKey,
            candidate.CandidateId,
            candidate.Title,
            candidate.ReferenceUri,
            candidate.ArtifactKind,
            targetRoot,
            targetRelativePath,
            candidate.DownloadAllowed,
            allowDownloadExecution,
            allowFileWrite,
            allowNetwork,
            allowOverwrite,
            contentType: candidate.ContentType,
            extension: candidate.Extension,
            expectedChecksumSha256: candidate.ChecksumSha256,
            documentYear: candidate.DocumentYear,
            reportingYear: candidate.ReportingYear,
            versionLabel: candidate.VersionLabel);

    public static GhgSourceDownloadExecutionValidationResult Validate(
        GhgSourceDownloadExecutionRequest? request)
    {
        var issues = new List<GhgSourceDownloadExecutionIssue>();

        if (request is null)
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(
                "GHG_SOURCE_DOWNLOAD_MISSING_REQUEST",
                "request is required.",
                "request"));
            return new GhgSourceDownloadExecutionValidationResult(issues);
        }

        if (!Enum.IsDefined(request.SourceFamily))
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(
                "GHG_SOURCE_DOWNLOAD_INVALID_SOURCE_FAMILY",
                "source_family must be a defined source family.",
                "source_family"));
        }

        ValidateRequiredText(
            request.SourceKey,
            "source_key",
            "GHG_SOURCE_DOWNLOAD_MISSING_SOURCE_KEY",
            "source_key must be a non-empty string.",
            issues);
        ValidateRequiredText(
            request.CandidateId,
            "candidate_id",
            "GHG_SOURCE_DOWNLOAD_MISSING_CANDIDATE_ID",
            "candidate_id must be a non-empty string.",
            issues);
        ValidateRequiredText(
            request.CandidateTitle,
            "candidate_title",
            "GHG_SOURCE_DOWNLOAD_MISSING_CANDIDATE_TITLE",
            "candidate_title must be a non-empty string.",
            issues);
        ValidateRequiredText(
            request.SourceReferenceUri,
            "source_reference_uri",
            "GHG_SOURCE_DOWNLOAD_MISSING_SOURCE_REFERENCE_URI",
            "source_reference_uri must be a non-empty string.",
            issues);
        ValidateRequiredText(
            request.ArtifactKind,
            "artifact_kind",
            "GHG_SOURCE_DOWNLOAD_MISSING_ARTIFACT_KIND",
            "artifact_kind must be a non-empty string.",
            issues);
        ValidateRequiredText(
            request.TargetRoot,
            "target_root",
            "GHG_SOURCE_DOWNLOAD_MISSING_TARGET_ROOT",
            "target_root must be a non-empty string.",
            issues);
        ValidateRequiredText(
            request.TargetRelativePath,
            "target_relative_path",
            "GHG_SOURCE_DOWNLOAD_MISSING_TARGET_RELATIVE_PATH",
            "target_relative_path must be a non-empty string.",
            issues);
        ValidateOptionalText(
            request.ContentType,
            "content_type",
            "GHG_SOURCE_DOWNLOAD_BLANK_CONTENT_TYPE",
            "content_type must be non-empty when provided.",
            issues);
        ValidateOptionalText(
            request.Extension,
            "extension",
            "GHG_SOURCE_DOWNLOAD_BLANK_EXTENSION",
            "extension must be non-empty when provided.",
            issues);
        ValidateOptionalText(
            request.ExpectedChecksumSha256,
            "expected_checksum_sha256",
            "GHG_SOURCE_DOWNLOAD_BLANK_EXPECTED_CHECKSUM_SHA256",
            "expected_checksum_sha256 must be non-empty when provided.",
            issues);
        ValidateOptionalText(
            request.VersionLabel,
            "version_label",
            "GHG_SOURCE_DOWNLOAD_BLANK_VERSION_LABEL",
            "version_label must be non-empty when provided.",
            issues);
        ValidateOptionalPositiveInt(
            request.DocumentYear,
            "document_year",
            "GHG_SOURCE_DOWNLOAD_INVALID_DOCUMENT_YEAR",
            "document_year must be a positive integer when provided.",
            issues);
        ValidateOptionalPositiveInt(
            request.ReportingYear,
            "reporting_year",
            "GHG_SOURCE_DOWNLOAD_INVALID_REPORTING_YEAR",
            "reporting_year must be a positive integer when provided.",
            issues);

        if (request.SourceFamily != SourceFamily.GhgProtocol)
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(
                "GHG_SOURCE_DOWNLOAD_SOURCE_FAMILY_MISMATCH",
                "source_family must be ghg_protocol.",
                "source_family"));
        }

        if (request.SourceKey != GhgSourceKey)
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(
                "GHG_SOURCE_DOWNLOAD_SOURCE_KEY_MISMATCH",
                "source_key must be ghg_protocol.",
                "source_key"));
        }

        ValidateTrue(
            request.CandidateDownloadAllowed,
            "candidate_download_allowed",
            "GHG_SOURCE_DOWNLOAD_CANDIDATE_NOT_DOWNLOADABLE",
            "candidate metadata must explicitly allow download execution.",
            issues);
        ValidateTrue(
            request.AllowDownloadExecution,
            "allow_download_execution",
            "GHG_SOURCE_DOWNLOAD_EXECUTION_NOT_ALLOWED",
            "allow_download_execution must be true.",
            issues);
        ValidateTrue(
            request.AllowFileWrite,
            "allow_file_write",
            "GHG_SOURCE_DOWNLOAD_FILE_WRITE_NOT_ALLOWED",
            "allow_file_write must be true.",
            issues);
        ValidateFalse(
            request.AllowParse,
            "allow_parse",
            "GHG_SOURCE_DOWNLOAD_PARSE_NOT_ALLOWED",
            "allow_parse must be false for this boundary.",
            issues);
        ValidateFalse(
            request.AllowDatabaseWrites,
            "allow_database_writes",
            "GHG_SOURCE_DOWNLOAD_DATABASE_WRITES_NOT_ALLOWED",
            "allow_database_writes must be false for this boundary.",
            issues);
        ValidateFalse(
            request.AllowScheduler,
            "allow_scheduler",
            "GHG_SOURCE_DOWNLOAD_SCHEDULER_NOT_ALLOWED",
            "allow_scheduler must be false for this boundary.",
            issues);

        ValidateSourceReferenceUri(request, issues);
        ValidateTargetPaths(request, issues);

        return new GhgSourceDownloadExecutionValidationResult(issues);
    }

    public static GhgSourceDownloadExecutionResult Execute(
        GhgSourceDownloadExecutionRequest request,
        Func<string, GhgSourceDownloadTransportResponse> transport)
    {
        var validation = Validate(request);
        if (!validation.IsValid)
        {
            return new GhgSourceDownloadExecutionResult(
                GhgSourceDownloadExecutionStatus.Blocked,
                request,
                issues: validation.Issues);
        }

        var safeTarget = PrepareSafeTargetPath(request);
        if (!safeTarget.Validation.IsValid)
        {
            return new GhgSourceDownloadExecutionResult(
                GhgSourceDownloadExecutionStatus.Blocked,
                request,
                issues: safeTarget.Validation.Issues);
        }

        GhgSourceDownloadTransportResponse response;
        try
        {
            response = transport(request.SourceReferenceUri);
        }
        catch (Exception error)
        {
            return new GhgSourceDownloadExecutionResult(
                GhgSourceDownloadExecutionStatus.Failed,
                request,
                issues:
                [
                    new GhgSourceDownloadExecutionIssue(
                        "GHG_SOURCE_DOWNLOAD_TRANSPORT_FAILED",
                        $"transport failed: {error.Message}",
                        "source_reference_uri"),
                ]);
        }

        var responseValidation = ValidateTransportResponse(response);
        if (!responseValidation.IsValid)
        {
            return new GhgSourceDownloadExecutionResult(
                GhgSourceDownloadExecutionStatus.Failed,
                request,
                issues: responseValidation.Issues);
        }

        var checksum = Convert.ToHexString(SHA256.HashData(response.Content)).ToLowerInvariant();
        if (request.ExpectedChecksumSha256 is not null
            && !string.Equals(checksum, request.ExpectedChecksumSha256, StringComparison.OrdinalIgnoreCase))
        {
            return new GhgSourceDownloadExecutionResult(
                GhgSourceDownloadExecutionStatus.Failed,
                request,
                issues:
                [
                    new GhgSourceDownloadExecutionIssue(
                        "GHG_SOURCE_DOWNLOAD_CHECKSUM_MISMATCH",
                        "downloaded content checksum did not match expected value.",
                        "expected_checksum_sha256"),
                ]);
        }

        safeTarget = PrepareSafeTargetPath(request);
        if (!safeTarget.Validation.IsValid)
        {
            return new GhgSourceDownloadExecutionResult(
                GhgSourceDownloadExecutionStatus.Blocked,
                request,
                issues: safeTarget.Validation.Issues);
        }

        try
        {
            WriteContentToSafeTarget(safeTarget.TargetPath, response.Content, request.AllowOverwrite);
        }
        catch (IOException error) when (File.Exists(safeTarget.TargetPath) && !request.AllowOverwrite)
        {
            return WriteFailed(request, "GHG_SOURCE_DOWNLOAD_TARGET_EXISTS", error);
        }
        catch (Exception error)
        {
            return WriteFailed(request, "GHG_SOURCE_DOWNLOAD_WRITE_FAILED", error);
        }

        var artifact = new GhgSourceDownloadedArtifact(
            request.SourceFamily,
            request.SourceKey,
            request.CandidateId,
            $"ghg_source_download_artifact_{request.CandidateId}",
            request.ArtifactKind,
            request.SourceReferenceUri,
            safeTarget.TargetPath,
            Path.GetFileName(safeTarget.TargetPath),
            checksum,
            response.Content.LongLength,
            response.ContentType ?? request.ContentType,
            request.Extension,
            response.FinalUri,
            request.DocumentYear,
            request.ReportingYear,
            request.VersionLabel);

        return new GhgSourceDownloadExecutionResult(
            GhgSourceDownloadExecutionStatus.Downloaded,
            request,
            artifact);
    }

    public static GhgSourceDownloadExecutionValidationResult Validate(
        GhgSourceDownloadExecutionResult? result)
    {
        var issues = new List<GhgSourceDownloadExecutionIssue>();

        if (result is null)
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(
                "GHG_SOURCE_DOWNLOAD_RESULT_MISSING",
                "result is required.",
                "result"));
            return new GhgSourceDownloadExecutionValidationResult(issues);
        }

        issues.AddRange(Validate(result.Request).Issues);

        if (!Enum.IsDefined(result.Status))
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(
                "GHG_SOURCE_DOWNLOAD_RESULT_INVALID_STATUS",
                "status must be a defined GHG source download execution status.",
                "status"));
        }

        foreach (var (fieldName, value) in new[]
        {
            ("no_parse", result.NoParse),
            ("no_database_writes", result.NoDatabaseWrites),
            ("no_sql", result.NoSql),
            ("no_scheduler", result.NoScheduler),
        })
        {
            if (!value)
            {
                issues.Add(new GhgSourceDownloadExecutionIssue(
                    "GHG_SOURCE_DOWNLOAD_RESULT_SIDE_EFFECT_FLAG_ENABLED",
                    $"{fieldName} must remain true.",
                    fieldName));
            }
        }

        if (result.Status == GhgSourceDownloadExecutionStatus.Downloaded && result.Artifact is null)
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(
                "GHG_SOURCE_DOWNLOAD_RESULT_MISSING_ARTIFACT",
                "downloaded results require artifact metadata.",
                "artifact"));
        }
        else if (result.Status != GhgSourceDownloadExecutionStatus.Downloaded && result.Artifact is not null)
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(
                "GHG_SOURCE_DOWNLOAD_RESULT_UNEXPECTED_ARTIFACT",
                "non-downloaded results must not include artifact metadata.",
                "artifact"));
        }

        return new GhgSourceDownloadExecutionValidationResult(issues);
    }

    private static GhgSourceDownloadExecutionResult WriteFailed(
        GhgSourceDownloadExecutionRequest request,
        string code,
        Exception error) =>
        new(
            GhgSourceDownloadExecutionStatus.Failed,
            request,
            issues:
            [
                new GhgSourceDownloadExecutionIssue(
                    code,
                    $"target write failed: {error.Message}",
                    "target_relative_path"),
            ]);

    private static GhgSourceDownloadExecutionValidationResult ValidateTransportResponse(
        GhgSourceDownloadTransportResponse? response)
    {
        var issues = new List<GhgSourceDownloadExecutionIssue>();

        if (response is null)
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(
                "GHG_SOURCE_DOWNLOAD_RESPONSE_MISSING",
                "transport response is required.",
                "transport"));
            return new GhgSourceDownloadExecutionValidationResult(issues);
        }

        if (response.Content is null)
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(
                "GHG_SOURCE_DOWNLOAD_RESPONSE_MISSING_CONTENT",
                "transport response content is required.",
                "content"));
        }
        else if (response.Content.Length == 0)
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(
                "GHG_SOURCE_DOWNLOAD_RESPONSE_EMPTY_CONTENT",
                "transport response content must not be empty.",
                "content"));
        }

        ValidateOptionalText(
            response.ContentType,
            "content_type",
            "GHG_SOURCE_DOWNLOAD_RESPONSE_BLANK_CONTENT_TYPE",
            "response content_type must be non-empty when provided.",
            issues);
        ValidateOptionalText(
            response.FinalUri,
            "final_uri",
            "GHG_SOURCE_DOWNLOAD_RESPONSE_BLANK_FINAL_URI",
            "response final_uri must be non-empty when provided.",
            issues);

        return new GhgSourceDownloadExecutionValidationResult(issues);
    }

    private static (string TargetPath, GhgSourceDownloadExecutionValidationResult Validation) PrepareSafeTargetPath(
        GhgSourceDownloadExecutionRequest request)
    {
        var issues = new List<GhgSourceDownloadExecutionIssue>();

        string root;
        string targetPath;
        try
        {
            root = Path.GetFullPath(request.TargetRoot);
            targetPath = Path.GetFullPath(Path.Combine(root, request.TargetRelativePath));
        }
        catch (Exception error) when (error is ArgumentException or NotSupportedException or PathTooLongException)
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(
                "GHG_SOURCE_DOWNLOAD_TARGET_PATH_UNRESOLVED",
                "target path could not be resolved safely.",
                "target_relative_path"));
            return (string.Empty, new GhgSourceDownloadExecutionValidationResult(issues));
        }

        if (!IsPathInsideRoot(root, targetPath))
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(
                "GHG_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_UNSAFE",
                "target_relative_path must stay within target_root.",
                "target_relative_path"));
        }

        if (ContainsExistingSymlink(root, targetPath))
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(
                "GHG_SOURCE_DOWNLOAD_TARGET_SYMLINK_UNSAFE",
                "target path must not traverse an existing symbolic link.",
                "target_relative_path"));
        }

        if (File.Exists(targetPath) && !request.AllowOverwrite)
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(
                "GHG_SOURCE_DOWNLOAD_TARGET_EXISTS",
                "target path already exists and allow_overwrite is false.",
                "target_relative_path"));
        }

        return (targetPath, new GhgSourceDownloadExecutionValidationResult(issues));
    }

    private static void WriteContentToSafeTarget(string targetPath, byte[] content, bool allowOverwrite)
    {
        var parent = Path.GetDirectoryName(targetPath);
        if (!string.IsNullOrWhiteSpace(parent))
        {
            Directory.CreateDirectory(parent);
        }

        if (IsSymlink(targetPath))
        {
            throw new IOException("target path is a symbolic link.");
        }

        var mode = allowOverwrite ? FileMode.Create : FileMode.CreateNew;
        using var stream = new FileStream(targetPath, mode, FileAccess.Write, FileShare.None);
        stream.Write(content, 0, content.Length);
    }

    private static bool IsPathInsideRoot(string root, string targetPath)
    {
        var rootWithSeparator = Path.EndsInDirectorySeparator(root)
            ? root
            : root + Path.DirectorySeparatorChar;

        return targetPath.StartsWith(rootWithSeparator, StringComparison.Ordinal)
            || string.Equals(root, targetPath, StringComparison.Ordinal);
    }

    private static bool ContainsExistingSymlink(string root, string targetPath)
    {
        var relative = Path.GetRelativePath(root, targetPath);
        if (relative.StartsWith("..", StringComparison.Ordinal) || Path.IsPathRooted(relative))
        {
            return false;
        }

        if (IsSymlink(root))
        {
            return true;
        }

        var current = root;
        foreach (var segment in relative.Split(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar))
        {
            if (string.IsNullOrWhiteSpace(segment))
            {
                continue;
            }

            current = Path.Combine(current, segment);
            if ((Directory.Exists(current) || File.Exists(current)) && IsSymlink(current))
            {
                return true;
            }
        }

        return false;
    }

    private static bool IsSymlink(string path)
    {
        try
        {
            return (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0;
        }
        catch (FileNotFoundException)
        {
            return false;
        }
        catch (DirectoryNotFoundException)
        {
            return false;
        }
    }

    private static void ValidateSourceReferenceUri(
        GhgSourceDownloadExecutionRequest request,
        ICollection<GhgSourceDownloadExecutionIssue> issues)
    {
        if (string.IsNullOrWhiteSpace(request.SourceReferenceUri))
        {
            return;
        }

        if (!Uri.TryCreate(request.SourceReferenceUri, UriKind.Absolute, out var uri))
        {
            return;
        }

        if (uri.Scheme == Uri.UriSchemeHttps && !request.AllowNetwork)
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(
                "GHG_SOURCE_DOWNLOAD_NETWORK_NOT_ALLOWED",
                "allow_network must be true for https source references.",
                "source_reference_uri"));
        }
        else if (uri.Scheme == Uri.UriSchemeHttp)
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(
                "GHG_SOURCE_DOWNLOAD_INSECURE_HTTP_NOT_ALLOWED",
                "http source references are not allowed.",
                "source_reference_uri"));
        }
        else if (uri.Scheme is not "mock" and not "memory")
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(
                "GHG_SOURCE_DOWNLOAD_UNSAFE_SOURCE_REFERENCE_URI",
                "source_reference_uri must use an allowed execution scheme.",
                "source_reference_uri"));
        }
    }

    private static void ValidateTargetPaths(
        GhgSourceDownloadExecutionRequest request,
        ICollection<GhgSourceDownloadExecutionIssue> issues)
    {
        if (!string.IsNullOrWhiteSpace(request.TargetRoot) && !Path.IsPathFullyQualified(request.TargetRoot))
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(
                "GHG_SOURCE_DOWNLOAD_TARGET_ROOT_NOT_ABSOLUTE",
                "target_root must be an absolute path.",
                "target_root"));
        }

        if (string.IsNullOrWhiteSpace(request.TargetRelativePath))
        {
            return;
        }

        if (Path.IsPathFullyQualified(request.TargetRelativePath))
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(
                "GHG_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_ABSOLUTE",
                "target_relative_path must be relative.",
                "target_relative_path"));
        }

        if (Uri.TryCreate(request.TargetRelativePath, UriKind.Absolute, out var targetUri)
            && !string.IsNullOrWhiteSpace(targetUri.Scheme))
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(
                "GHG_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_URI",
                "target_relative_path must not be a URI.",
                "target_relative_path"));
        }

        var segments = request.TargetRelativePath.Split(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar);
        if (segments.Any(segment => segment == ".."))
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(
                "GHG_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_UNSAFE",
                "target_relative_path must not contain parent traversal.",
                "target_relative_path"));
        }
    }

    private static void ValidateRequiredText(
        string? value,
        string fieldName,
        string code,
        string message,
        ICollection<GhgSourceDownloadExecutionIssue> issues)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(code, message, fieldName));
        }
    }

    private static void ValidateOptionalText(
        string? value,
        string fieldName,
        string code,
        string message,
        ICollection<GhgSourceDownloadExecutionIssue> issues)
    {
        if (value is not null && string.IsNullOrWhiteSpace(value))
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(code, message, fieldName));
        }
    }

    private static void ValidateOptionalPositiveInt(
        int? value,
        string fieldName,
        string code,
        string message,
        ICollection<GhgSourceDownloadExecutionIssue> issues)
    {
        if (value is <= 0)
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(code, message, fieldName));
        }
    }

    private static void ValidateTrue(
        bool value,
        string fieldName,
        string code,
        string message,
        ICollection<GhgSourceDownloadExecutionIssue> issues)
    {
        if (!value)
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(code, message, fieldName));
        }
    }

    private static void ValidateFalse(
        bool value,
        string fieldName,
        string code,
        string message,
        ICollection<GhgSourceDownloadExecutionIssue> issues)
    {
        if (value)
        {
            issues.Add(new GhgSourceDownloadExecutionIssue(code, message, fieldName));
        }
    }
}
