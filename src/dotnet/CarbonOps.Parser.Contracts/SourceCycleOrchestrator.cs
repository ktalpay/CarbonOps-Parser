using System.Globalization;
using System.Security.Cryptography;
using System.Text.Json;

namespace CarbonOps.Parser.Contracts;

public enum SourceCycleRunStatus
{
    Ready = 0,
    Blocked = 1,
    NoAvailableSourceYear = 2,
    ParserNotAvailable = 3,
    Parsed = 4,
    PersistenceNotImplemented = 5,
    NotImplemented = 6,
}

public sealed record SourceCycleArtifact(
    SourceFamily SourceFamily,
    int ReportingYear,
    string ArtifactReference,
    string ContentType,
    string? Extension = null,
    string? VersionLabel = null);

public sealed record SourceCycleRunSummary(
    SourceFamily SourceFamily,
    int? LatestSuccessfulYear,
    int TargetYear,
    SourceCycleRunStatus Status,
    SourceCycleRunStatus ParserStatus,
    SourceCycleRunStatus PersistenceStatus,
    string StatusReason,
    string? ArtifactReference,
    int ArtifactCount,
    int ParsedRowCount,
    int ParserIssueCount,
    ParserRunStatus? ParserRunStatus);

public sealed record SourceCyclePreviewResult(
    IReadOnlyList<SourceCycleRunSummary> Runs,
    bool PostgreSQLConnectionOpened,
    bool PostgreSQLSqlExecuted,
    bool RecordsInserted,
    bool YearStateAdvanced,
    bool NetworkAccessAttempted,
    bool SecretValuesPrinted)
{
    public int RunCount => Runs.Count;
}

public sealed class SourceCycleOrchestrator
{
    private readonly PostgreSQLSourceFamilyYearStateRepository _yearStateRepository;
    private readonly IReadOnlyList<SourceFamily> _enabledSourceFamilies;
    private readonly IReadOnlyDictionary<(SourceFamily SourceFamily, int ReportingYear), SourceCycleArtifact> _artifacts;
    private readonly Func<SourceCycleArtifact, string?> _loadLocalArtifactContent;

    public SourceCycleOrchestrator(
        PostgreSQLSourceFamilyYearStateRepository yearStateRepository,
        IEnumerable<SourceFamily>? enabledSourceFamilies = null,
        IEnumerable<SourceCycleArtifact>? artifacts = null,
        Func<SourceCycleArtifact, string?>? loadLocalArtifactContent = null)
    {
        _yearStateRepository = yearStateRepository;
        _enabledSourceFamilies = Array.AsReadOnly((enabledSourceFamilies ?? SourceFamilyRegistry.SupportedFamilies)
            .Distinct()
            .OrderBy(family => family.ToWireName(), StringComparer.Ordinal)
            .ToArray());
        _artifacts = (artifacts ?? [])
            .GroupBy(artifact => (artifact.SourceFamily, artifact.ReportingYear))
            .ToDictionary(group => group.Key, group => group.OrderBy(item => item.ArtifactReference, StringComparer.Ordinal).First());
        _loadLocalArtifactContent = loadLocalArtifactContent ?? LoadLocalArtifactContent;
    }

    public async Task<SourceCyclePreviewResult> PreviewAsync(CancellationToken cancellationToken = default)
    {
        var runs = new List<SourceCycleRunSummary>();

        foreach (var sourceFamily in _enabledSourceFamilies)
        {
            var yearState = await _yearStateRepository.GetYearStateAsync(sourceFamily, cancellationToken).ConfigureAwait(false);
            runs.Add(RunSourceFamily(yearState));
        }

        return new SourceCyclePreviewResult(
            Array.AsReadOnly(runs.ToArray()),
            PostgreSQLConnectionOpened: false,
            PostgreSQLSqlExecuted: false,
            RecordsInserted: false,
            YearStateAdvanced: false,
            NetworkAccessAttempted: false,
            SecretValuesPrinted: false);
    }

    private SourceCycleRunSummary RunSourceFamily(SourceFamilyYearState yearState)
    {
        if (!_artifacts.TryGetValue((yearState.SourceFamily, yearState.NextYear), out var artifact))
        {
            return Summary(
                yearState,
                SourceCycleRunStatus.NoAvailableSourceYear,
                SourceCycleRunStatus.NoAvailableSourceYear,
                "no configured local artifact exists for the target source-family year",
                artifactReference: null,
                artifactCount: 0,
                parsedRowCount: 0,
                parserIssueCount: 0,
                parserRunStatus: null);
        }

        if (!IsLocalTextArtifact(artifact))
        {
            return Summary(
                yearState,
                SourceCycleRunStatus.ParserNotAvailable,
                SourceCycleRunStatus.ParserNotAvailable,
                "parser handoff is available only for configured local CSV/text artifacts",
                artifact.ArtifactReference,
                artifactCount: 1,
                parsedRowCount: 0,
                parserIssueCount: 0,
                parserRunStatus: null);
        }

        var content = _loadLocalArtifactContent(artifact);
        if (content is null)
        {
            return Summary(
                yearState,
                SourceCycleRunStatus.NoAvailableSourceYear,
                SourceCycleRunStatus.NoAvailableSourceYear,
                "configured artifact is missing or unavailable",
                artifact.ArtifactReference,
                artifactCount: 0,
                parsedRowCount: 0,
                parserIssueCount: 0,
                parserRunStatus: null);
        }

        var parserResult = ParseArtifact(artifact, content);
        var parserStatus = parserResult.Status == ParserRunStatus.Completed
            ? SourceCycleRunStatus.Parsed
            : SourceCycleRunStatus.ParserNotAvailable;
        var status = parserResult.Status == ParserRunStatus.Completed
            ? SourceCycleRunStatus.PersistenceNotImplemented
            : SourceCycleRunStatus.ParserNotAvailable;

        return Summary(
            yearState,
            status,
            parserStatus,
            parserResult.Status == ParserRunStatus.Completed
                ? "parser completed; source-specific master/detail persistence is not implemented"
                : "parser failed closed for the configured artifact",
            artifact.ArtifactReference,
            artifactCount: 1,
            parserResult.RowCount,
            parserResult.IssueCount,
            parserResult.Status);
    }

    private static SourceCycleRunSummary Summary(
        SourceFamilyYearState yearState,
        SourceCycleRunStatus status,
        SourceCycleRunStatus parserStatus,
        string statusReason,
        string? artifactReference,
        int artifactCount,
        int parsedRowCount,
        int parserIssueCount,
        ParserRunStatus? parserRunStatus) =>
        new(
            yearState.SourceFamily,
            yearState.LatestYear,
            yearState.NextYear,
            status,
            parserStatus,
            SourceCycleRunStatus.PersistenceNotImplemented,
            statusReason,
            artifactReference,
            artifactCount,
            parsedRowCount,
            parserIssueCount,
            parserRunStatus);

    private static ParserAdapterRunResult ParseArtifact(SourceCycleArtifact artifact, string content)
    {
        var parserKey = ParserSelectionRegistry.GetParserKey(artifact.SourceFamily);
        var parserArtifact = new ParserInputArtifact(
            artifact.SourceFamily,
            artifact.SourceFamily.ToWireName(),
            parserKey,
            ParserSourceFormat.DiscoveryReference,
            artifact.ArtifactReference,
            Path.GetFileName(artifact.ArtifactReference),
            "sha256",
            Sha256Hex(content),
            isDryRunChecksum: false,
            artifact.ContentType,
            artifact.Extension,
            artifact.ReportingYear);
        var request = new ParserAdapterRunRequest(
            artifact.SourceFamily,
            artifact.SourceFamily.ToWireName(),
            parserKey,
            [parserArtifact],
            requestedReportingYear: artifact.ReportingYear);
        var contentByArtifactReference = new Dictionary<string, string>(StringComparer.Ordinal)
        {
            [artifact.ArtifactReference] = content,
        };

        return artifact.SourceFamily switch
        {
            SourceFamily.GhgProtocol => GhgProtocolNormalizedContentParser.Parse(request, contentByArtifactReference),
            SourceFamily.DefraDesnz => DefraDesnzNormalizedContentParser.Parse(request, contentByArtifactReference),
            SourceFamily.IpccEfdb => IpccEfdbNormalizedContentParser.Parse(request, contentByArtifactReference),
            _ => throw new ArgumentOutOfRangeException(nameof(artifact), artifact.SourceFamily, "Unknown source family."),
        };
    }

    private static string? LoadLocalArtifactContent(SourceCycleArtifact artifact)
    {
        if (!TryGetLocalPath(artifact.ArtifactReference, out var localPath) || !File.Exists(localPath))
        {
            return null;
        }

        return File.ReadAllText(localPath);
    }

    private static bool IsLocalTextArtifact(SourceCycleArtifact artifact) =>
        IsLocalPath(artifact.ArtifactReference) &&
        (string.Equals(artifact.Extension, ".csv", StringComparison.OrdinalIgnoreCase) ||
            string.Equals(artifact.ContentType, "text/csv", StringComparison.OrdinalIgnoreCase) ||
            string.Equals(artifact.ContentType, "text/plain", StringComparison.OrdinalIgnoreCase));

    private static bool IsLocalPath(string reference) =>
        !Uri.TryCreate(reference, UriKind.Absolute, out var uri) || uri.IsFile;

    private static bool TryGetLocalPath(string reference, out string localPath)
    {
        if (Uri.TryCreate(reference, UriKind.Absolute, out var uri))
        {
            if (!uri.IsFile)
            {
                localPath = string.Empty;
                return false;
            }

            localPath = uri.LocalPath;
            return true;
        }

        localPath = reference;
        return true;
    }

    private static string Sha256Hex(string content)
    {
        var hash = SHA256.HashData(System.Text.Encoding.UTF8.GetBytes(content));
        return Convert.ToHexString(hash).ToLowerInvariant();
    }
}

public static class SourceCycleConfiguration
{
    public static IReadOnlyList<SourceCycleArtifact> LoadArtifacts(string? configPath)
    {
        if (string.IsNullOrWhiteSpace(configPath) || !File.Exists(configPath))
        {
            return Array.Empty<SourceCycleArtifact>();
        }

        using var document = TryLoadJsonDocument(configPath);
        if (document is null)
        {
            return Array.Empty<SourceCycleArtifact>();
        }

        if (document.RootElement.ValueKind != JsonValueKind.Object ||
            !TryGetArtifactRoot(document.RootElement, out var root) ||
            root.ValueKind != JsonValueKind.Object)
        {
            return Array.Empty<SourceCycleArtifact>();
        }

        var artifacts = new List<SourceCycleArtifact>();
        foreach (var familyProperty in root.EnumerateObject().OrderBy(item => item.Name, StringComparer.Ordinal))
        {
            if (!ContractWireNames.TryParseSourceFamilyWireName(familyProperty.Name, out var sourceFamily) ||
                familyProperty.Value.ValueKind != JsonValueKind.Object)
            {
                continue;
            }

            foreach (var yearProperty in familyProperty.Value.EnumerateObject().OrderBy(item => item.Name, StringComparer.Ordinal))
            {
                if (!int.TryParse(yearProperty.Name, NumberStyles.None, CultureInfo.InvariantCulture, out var year) ||
                    year < 1 ||
                    !TryReadArtifactReference(yearProperty.Value, out var reference, out var contentType, out var extension, out var versionLabel))
                {
                    continue;
                }

                artifacts.Add(new SourceCycleArtifact(sourceFamily, year, reference, contentType, extension, versionLabel));
            }
        }

        return Array.AsReadOnly(artifacts.ToArray());
    }

    public static IReadOnlyList<SourceFamily> LoadEnabledSourceFamilies(string? configPath)
    {
        if (string.IsNullOrWhiteSpace(configPath) || !File.Exists(configPath))
        {
            return SourceFamilyRegistry.SupportedFamilies;
        }

        using var document = TryLoadJsonDocument(configPath);
        if (document is null)
        {
            return SourceFamilyRegistry.SupportedFamilies;
        }

        if (document.RootElement.ValueKind != JsonValueKind.Object ||
            !document.RootElement.TryGetProperty("enabled_source_families", out var root) ||
            root.ValueKind != JsonValueKind.Array)
        {
            return SourceFamilyRegistry.SupportedFamilies;
        }

        var families = root
            .EnumerateArray()
            .Select(item => item.ValueKind == JsonValueKind.String ? item.GetString() : null)
            .Where(item => ContractWireNames.TryParseSourceFamilyWireName(item, out _))
            .Select(item =>
            {
                ContractWireNames.TryParseSourceFamilyWireName(item, out var sourceFamily);
                return sourceFamily;
            })
            .Distinct()
            .ToArray();

        return families.Length == 0 ? SourceFamilyRegistry.SupportedFamilies : Array.AsReadOnly(families);
    }

    private static JsonDocument? TryLoadJsonDocument(string configPath)
    {
        try
        {
            using var stream = File.OpenRead(configPath);
            return JsonDocument.Parse(stream);
        }
        catch (IOException)
        {
            return null;
        }
        catch (JsonException)
        {
            return null;
        }
    }

    private static bool TryGetArtifactRoot(JsonElement documentRoot, out JsonElement artifactRoot)
    {
        if (documentRoot.TryGetProperty("source_artifacts", out artifactRoot))
        {
            return true;
        }

        return documentRoot.TryGetProperty("source_years", out artifactRoot);
    }

    private static bool TryReadArtifactReference(
        JsonElement element,
        out string reference,
        out string contentType,
        out string? extension,
        out string? versionLabel)
    {
        reference = string.Empty;
        contentType = "text/csv";
        extension = ".csv";
        versionLabel = null;

        if (element.ValueKind == JsonValueKind.String)
        {
            reference = element.GetString() ?? string.Empty;
            return !string.IsNullOrWhiteSpace(reference);
        }

        if (element.ValueKind != JsonValueKind.Object ||
            !TryReadReferenceProperty(element, out var path))
        {
            return false;
        }

        reference = path;
        if (element.TryGetProperty("content_type", out var contentTypeElement) &&
            contentTypeElement.ValueKind == JsonValueKind.String)
        {
            contentType = contentTypeElement.GetString() ?? contentType;
        }

        if (element.TryGetProperty("extension", out var extensionElement) &&
            extensionElement.ValueKind == JsonValueKind.String)
        {
            extension = extensionElement.GetString();
        }

        if (element.TryGetProperty("version_label", out var versionLabelElement) &&
            versionLabelElement.ValueKind == JsonValueKind.String)
        {
            versionLabel = versionLabelElement.GetString();
        }

        return !string.IsNullOrWhiteSpace(reference);
    }

    private static bool TryReadReferenceProperty(JsonElement element, out string reference)
    {
        foreach (var propertyName in new[] { "path", "uri", "artifact_url" })
        {
            if (element.TryGetProperty(propertyName, out var property) &&
                property.ValueKind == JsonValueKind.String)
            {
                reference = property.GetString() ?? string.Empty;
                return !string.IsNullOrWhiteSpace(reference);
            }
        }

        reference = string.Empty;
        return false;
    }
}
