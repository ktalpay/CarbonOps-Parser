using System.Collections;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace CarbonOps.Parser.Contracts;

public delegate void Phase1OperationalEventSink(string jsonEvent);

public static partial class Phase1OperationalDiagnostics
{
    public const string OperationalLoggerName = "CarbonOps.Parser.Phase1";
    public const string Redacted = "<redacted>";

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping,
        WriteIndented = false,
    };

    private static readonly HashSet<string> SensitiveRuntimeOptionFields = new(StringComparer.OrdinalIgnoreCase)
    {
        "host",
        "database",
        "username",
        "application_name",
        "dsn",
        "connection_string",
        "connectionstring",
        "connection_uri",
        "connectionuri",
        "database_url",
        "databaseurl",
        "api_key",
        "apikey",
        "access_key",
        "accesskey",
        "private_key",
        "privatekey",
    };

    private static readonly string[] SensitiveKeyParts =
    [
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
        "credential",
        "dsn",
        "connection_string",
        "connection_uri",
        "database_url",
    ];

    public static IReadOnlyDictionary<string, object?> BuildOperationalEvent(
        string eventName,
        IReadOnlyDictionary<string, object?> payload)
    {
        var redactedPayload = RedactDiagnosticValue("payload", payload);
        var eventPayload = redactedPayload as IReadOnlyDictionary<string, object?> ??
            new SortedDictionary<string, object?>(StringComparer.Ordinal);
        var result = new SortedDictionary<string, object?>(StringComparer.Ordinal)
        {
            ["event"] = eventName,
        };

        foreach (var item in eventPayload)
        {
            result[item.Key] = NormalizeDiagnosticValue(item.Value);
        }

        return result;
    }

    public static string SerializeOperationalEvent(
        string eventName,
        IReadOnlyDictionary<string, object?> payload) =>
        JsonSerializer.Serialize(BuildOperationalEvent(eventName, payload), JsonOptions);

    public static object? RedactDiagnosticValue(string fieldName, object? value)
    {
        if (IsSensitiveField(fieldName))
        {
            return value is null ? null : Redacted;
        }

        return value switch
        {
            null => null,
            string text => SafeText(text),
            IReadOnlyDictionary<string, object?> mapping => StableMapping(mapping),
            IDictionary dictionary => StableDictionary(dictionary),
            IEnumerable enumerable when value is not string => StableEnumerable(fieldName, enumerable),
            Enum enumValue => enumValue.ToString(),
            _ => value,
        };
    }

    public static IReadOnlyDictionary<string, object?> SummarizePostgreSQLOptionsForDiagnostics(
        PostgreSQLPersistenceOptions options) =>
        new SortedDictionary<string, object?>(StringComparer.Ordinal)
        {
            ["application_name"] = options.ApplicationName is null ? null : Redacted,
            ["connect_timeout_seconds"] = options.ConnectTimeoutSeconds,
            ["database"] = Redacted,
            ["host"] = Redacted,
            ["password_set"] = options.PasswordSet,
            ["port"] = options.Port,
            ["ssl_mode"] = options.SslMode,
            ["username"] = Redacted,
        };

    public static IReadOnlyDictionary<string, object?> SummarizeOrchestratorRequest(
        Phase1IngestionOrchestratorRequest request) =>
        new SortedDictionary<string, object?>(StringComparer.Ordinal)
        {
            ["correlation_id"] = SafeText(request.CorrelationId),
            ["execution_mode"] = Phase1ExecutionModeWireName(request.ExecutionMode),
            ["max_degree_of_parallelism"] = request.MaxDegreeOfParallelism,
            ["run_id"] = SafeText(request.RunId),
            ["source_families"] = request.SourceFamilies.Select(sourceFamily => sourceFamily.ToWireName()).ToArray(),
        };

    public static IReadOnlyDictionary<string, object?> SummarizeFamilyResultForDiagnostics(
        Phase1IngestionFamilyResult familyResult,
        string? runId = null,
        string? correlationId = null) =>
        new SortedDictionary<string, object?>(StringComparer.Ordinal)
        {
            ["correlation_id"] = SafeText(correlationId),
            ["documents"] = DocumentSummaries(familyResult.AcquisitionRun?.Artifacts ?? []),
            ["failures"] = FailureSummaries(familyResult.Failures),
            ["parser"] = new SortedDictionary<string, object?>(StringComparer.Ordinal)
            {
                ["accepted_row_count"] = familyResult.ParserAcceptedRowCount,
                ["failure_count"] = familyResult.ParserFailureCount,
                ["result_status"] = familyResult.ParserRun?.Status.ToWireName(),
                ["run_id"] = SafeText(familyResult.ParserRun?.RunId),
                ["validation_issue_count"] = familyResult.ParserRun?.IssueCount ?? 0,
            },
            ["persistence"] = new SortedDictionary<string, object?>(StringComparer.Ordinal)
            {
                ["parsed_factor_detail_count"] = familyResult.PersistedDetailCount,
                ["parsed_factor_master_count"] = familyResult.PersistedMasterCount,
                ["parser_run_count"] = familyResult.ParserRunPersistResult?.PersistedCount ?? 0,
                ["source_document_count"] = familyResult.SourceDocumentPersistResult?.PersistedCount ?? 0,
                ["source_run_count"] = familyResult.AcquisitionRunPersistResult?.PersistedCount ?? 0,
            },
            ["run_id"] = SafeText(runId ?? familyResult.AcquisitionRun?.RunId),
            ["source_family"] = familyResult.SourceFamily.ToWireName(),
            ["source_key"] = familyResult.SourceKey,
            ["status"] = Phase1FamilyRunStatusWireName(familyResult.Status),
        };

    public static IReadOnlyDictionary<string, object?> SummarizeOrchestratorResultForDiagnostics(
        Phase1IngestionOrchestratorResult result) =>
        new SortedDictionary<string, object?>(StringComparer.Ordinal)
        {
            ["correlation_id"] = SafeText(result.Request.CorrelationId),
            ["failures"] = FailureSummaries(result.Failures),
            ["run_id"] = SafeText(result.Request.RunId),
            ["selected_source_families"] = result.SelectedSourceFamilies
                .Select(sourceFamily => sourceFamily.ToWireName())
                .ToArray(),
            ["source_family_statuses"] = result.FamilyResults
                .Select(familyResult => new SortedDictionary<string, object?>(StringComparer.Ordinal)
                {
                    ["source_family"] = familyResult.SourceFamily.ToWireName(),
                    ["status"] = Phase1FamilyRunStatusWireName(familyResult.Status),
                })
                .ToArray(),
            ["status"] = Phase1RunStatusWireName(result.Status),
            ["summary"] = new SortedDictionary<string, object?>(StringComparer.Ordinal)
            {
                ["completed_family_count"] = result.CompletedSourceFamilyCount,
                ["failed_family_count"] = result.FailedSourceFamilyCount,
                ["failure_count"] = result.FailureCount,
                ["parsed_factor_row_count"] = result.TotalParserAcceptedRowCount,
                ["parser_run_count"] = result.FamilyResults.Count(familyResult => familyResult.ParserRun is not null),
                ["persisted_detail_count"] = result.TotalPersistedDetailCount,
                ["persisted_master_count"] = result.TotalPersistedMasterCount,
                ["persisted_parser_run_count"] = result.FamilyResults.Sum(familyResult =>
                    familyResult.ParserRunPersistResult?.PersistedCount ?? 0),
                ["persisted_source_document_count"] = result.FamilyResults.Sum(familyResult =>
                    familyResult.SourceDocumentPersistResult?.PersistedCount ?? 0),
                ["persisted_source_run_count"] = result.FamilyResults.Sum(familyResult =>
                    familyResult.AcquisitionRunPersistResult?.PersistedCount ?? 0),
                ["requested_family_count"] = result.Request.SourceFamilies.Count,
                ["source_artifact_count"] = result.TotalSourceDocumentMetadataCount,
                ["source_candidate_count"] = result.FamilyResults.Sum(familyResult => familyResult.SourceCandidateCount),
            },
        };

    internal static void Emit(
        Phase1OperationalEventSink? sink,
        string eventName,
        IReadOnlyDictionary<string, object?> payload)
    {
        sink?.Invoke(SerializeOperationalEvent(eventName, payload));
    }

    private static IReadOnlyDictionary<string, object?>[] DocumentSummaries(
        IEnumerable<SourceDownloadArtifact> artifacts) =>
        artifacts
            .Select(artifact => new SortedDictionary<string, object?>(StringComparer.Ordinal)
            {
                ["checksum_sha256"] = SafeChecksum(artifact.Checksum?.Value),
                ["document_id"] = SafeText(artifact.ArtifactId),
                ["source_family"] = artifact.SourceFamily.ToWireName(),
                ["source_key"] = artifact.SourceKey,
            })
            .ToArray();

    private static IReadOnlyDictionary<string, object?>[] FailureSummaries(
        IEnumerable<Phase1IngestionFailure> failures) =>
        failures
            .Select(failure => new SortedDictionary<string, object?>(StringComparer.Ordinal)
            {
                ["code"] = failure.Code,
                ["field_name"] = failure.FieldName,
                ["message"] = SafeText(failure.Message),
                ["severity"] = failure.Severity,
                ["source_family"] = failure.SourceFamily.ToWireName(),
                ["source_key"] = failure.SourceKey,
                ["stage"] = failure.Stage,
            })
            .ToArray();

    private static IReadOnlyDictionary<string, object?> StableMapping(
        IReadOnlyDictionary<string, object?> mapping)
    {
        var result = new SortedDictionary<string, object?>(StringComparer.Ordinal);
        foreach (var item in mapping)
        {
            result[item.Key] = RedactDiagnosticValue(item.Key, item.Value);
        }

        return result;
    }

    private static IReadOnlyDictionary<string, object?> StableDictionary(IDictionary dictionary)
    {
        var result = new SortedDictionary<string, object?>(StringComparer.Ordinal);
        foreach (DictionaryEntry item in dictionary)
        {
            var key = Convert.ToString(item.Key) ?? string.Empty;
            result[key] = RedactDiagnosticValue(key, item.Value);
        }

        return result;
    }

    private static object?[] StableEnumerable(string fieldName, IEnumerable enumerable)
    {
        var result = new List<object?>();
        foreach (var item in enumerable)
        {
            result.Add(RedactDiagnosticValue(fieldName, item));
        }

        return result.ToArray();
    }

    private static object? NormalizeDiagnosticValue(object? value) =>
        value switch
        {
            IReadOnlyDictionary<string, object?> mapping => StableMapping(mapping),
            IDictionary dictionary => StableDictionary(dictionary),
            IEnumerable enumerable when value is not string => StableEnumerable("item", enumerable),
            Enum enumValue => enumValue.ToString(),
            _ => value,
        };

    private static string? SafeText(string? value)
    {
        if (value is null)
        {
            return null;
        }

        var withoutUserInfo = UserInfoUriPattern().Replace(value, $"//{Redacted}@");
        return SensitiveAssignmentPattern().Replace(
            withoutUserInfo,
            match => $"{match.Groups[1].Value}={Redacted}");
    }

    private static string? SafeChecksum(string? value)
    {
        if (value is null || !ChecksumPattern().IsMatch(value))
        {
            return null;
        }

        return value.ToLowerInvariant();
    }

    private static bool IsSensitiveField(string fieldName)
    {
        var normalized = fieldName.Trim().ToLowerInvariant();
        var compact = normalized.Replace("_", string.Empty, StringComparison.Ordinal)
            .Replace("-", string.Empty, StringComparison.Ordinal);
        if (normalized == "password_set")
        {
            return false;
        }

        return SensitiveRuntimeOptionFields.Contains(normalized) ||
            SensitiveKeyParts.Any(part =>
                normalized.Contains(part, StringComparison.Ordinal) ||
                compact.Contains(part, StringComparison.Ordinal));
    }

    private static string Phase1ExecutionModeWireName(Phase1IngestionExecutionMode value) =>
        value switch
        {
            Phase1IngestionExecutionMode.Sequential => "sequential",
            Phase1IngestionExecutionMode.BoundedParallel => "bounded_parallel",
            _ => throw new ArgumentOutOfRangeException(nameof(value), value, "Unknown Phase 1 execution mode."),
        };

    private static string Phase1RunStatusWireName(Phase1IngestionRunStatus value) =>
        value switch
        {
            Phase1IngestionRunStatus.Completed => "completed",
            Phase1IngestionRunStatus.CompletedWithFailures => "completed_with_failures",
            Phase1IngestionRunStatus.Failed => "failed",
            Phase1IngestionRunStatus.NotExecutable => "not_executable",
            _ => throw new ArgumentOutOfRangeException(nameof(value), value, "Unknown Phase 1 run status."),
        };

    private static string Phase1FamilyRunStatusWireName(Phase1IngestionFamilyRunStatus value) =>
        value switch
        {
            Phase1IngestionFamilyRunStatus.Completed => "completed",
            Phase1IngestionFamilyRunStatus.Failed => "failed",
            Phase1IngestionFamilyRunStatus.Skipped => "skipped",
            _ => throw new ArgumentOutOfRangeException(nameof(value), value, "Unknown Phase 1 family run status."),
        };

    [GeneratedRegex("^[0-9a-fA-F]{64}$")]
    private static partial Regex ChecksumPattern();

    [GeneratedRegex("//[^/\\s:@]+:[^@\\s/]+@")]
    private static partial Regex UserInfoUriPattern();

    [GeneratedRegex("(?i)\\b(password|passwd|pwd|secret|token|dsn|connection[_-]?string)=([^\\s;,]+)")]
    private static partial Regex SensitiveAssignmentPattern();
}
