using System.Text.Json;

namespace CarbonOps.Parser.Contracts;

public sealed record ProductionConfigValidationIssue(
    string Code,
    string Message,
    string FieldName,
    string Severity = "error");

public sealed record ProductionConfigValidationResult
{
    public IReadOnlyList<ProductionConfigValidationIssue> Issues { get; }

    public bool IsValid => Issues.Count == 0;

    public ProductionConfigValidationResult(
        IEnumerable<ProductionConfigValidationIssue>? issues = null)
    {
        Issues = Array.AsReadOnly((issues ?? []).ToArray());
    }
}

public sealed record ProductionConfigBoundaryDescription(
    IReadOnlyList<string> RequiredEnvironmentVariables,
    IReadOnlyList<string> SecretEnvironmentVariables,
    string Provider,
    bool LoadsEnvironment,
    bool LoadsConfigFiles,
    bool LoadsCredentials,
    bool LogsSecretValues,
    IReadOnlyList<string> Notes);

public static class ProductionConfigBoundary
{
    public const string RawPostgreSQLConnectionStringKey = "CARBONOPS_PARSER_POSTGRES_CONNECTION_STRING";

    public static readonly IReadOnlyList<string> RequiredEnvironmentVariables = Array.AsReadOnly(new[]
    {
        "CARBONOPS_PARSER_ENV",
        "CARBONOPS_PARSER_DATABASE_PROVIDER",
        "CARBONOPS_PARSER_POSTGRES_HOST",
        "CARBONOPS_PARSER_POSTGRES_PORT",
        "CARBONOPS_PARSER_POSTGRES_DATABASE",
        "CARBONOPS_PARSER_POSTGRES_USERNAME",
        "CARBONOPS_PARSER_POSTGRES_PASSWORD",
        "CARBONOPS_PARSER_POSTGRES_SCHEMA",
        "CARBONOPS_PARSER_RAW_ARCHIVE_PATH",
        "CARBONOPS_PARSER_LOG_LEVEL",
    });

    public static readonly IReadOnlyList<string> SecretEnvironmentVariables = Array.AsReadOnly(new[]
    {
        "CARBONOPS_PARSER_POSTGRES_PASSWORD",
    });

    public static readonly IReadOnlyList<string> KnownConfigurationKeys = Array.AsReadOnly(
        RequiredEnvironmentVariables
            .Append(RawPostgreSQLConnectionStringKey)
            .ToArray());

    private static readonly HashSet<string> ValidLogLevels = new(StringComparer.OrdinalIgnoreCase)
    {
        "debug",
        "info",
        "warning",
        "error",
        "critical",
    };

    public static ProductionConfigBoundaryDescription Describe() =>
        new(
            RequiredEnvironmentVariables,
            SecretEnvironmentVariables,
            "postgres",
            LoadsEnvironment: true,
            LoadsConfigFiles: true,
            LoadsCredentials: true,
            LogsSecretValues: false,
            [
                "The .NET service entrypoint loads an optional explicit JSON config file and process environment.",
                "Environment values override config file values for known production keys.",
                "CARBONOPS_PARSER_POSTGRES_PASSWORD is required but never returned.",
                "Connection strings are not accepted as production config values.",
                "Validation messages name keys only and do not echo configured values.",
            ]);

    public static ProductionConfigValidationResult Validate(
        IReadOnlyDictionary<string, string?> values)
    {
        var issues = new List<ProductionConfigValidationIssue>();

        foreach (var envVar in RequiredEnvironmentVariables)
        {
            if (!HasText(Get(values, envVar)))
            {
                issues.Add(new ProductionConfigValidationIssue(
                    "PRODUCTION_CONFIG_MISSING_REQUIRED_ENV_VAR",
                    $"{envVar} must be set for production startup.",
                    envVar));
            }
        }

        var provider = Get(values, "CARBONOPS_PARSER_DATABASE_PROVIDER");
        if (provider is not null &&
            HasText(provider) &&
            !string.Equals(provider.Trim(), "postgres", StringComparison.OrdinalIgnoreCase))
        {
            issues.Add(new ProductionConfigValidationIssue(
                "PRODUCTION_CONFIG_UNSUPPORTED_DATABASE_PROVIDER",
                "Unsupported database provider. Phase 1 supports postgres only.",
                "CARBONOPS_PARSER_DATABASE_PROVIDER"));
        }

        ValidatePort(Get(values, "CARBONOPS_PARSER_POSTGRES_PORT"), issues);
        ValidateLogLevel(Get(values, "CARBONOPS_PARSER_LOG_LEVEL"), issues);

        if (HasText(Get(values, RawPostgreSQLConnectionStringKey)))
        {
            issues.Add(new ProductionConfigValidationIssue(
                "PRODUCTION_CONFIG_RAW_CONNECTION_STRING_NOT_ALLOWED",
                "Raw PostgreSQL connection strings are not accepted; use split non-secret fields and CARBONOPS_PARSER_POSTGRES_PASSWORD.",
                RawPostgreSQLConnectionStringKey));
        }

        return new ProductionConfigValidationResult(issues);
    }

    private static void ValidatePort(
        string? rawValue,
        ICollection<ProductionConfigValidationIssue> issues)
    {
        if (!HasText(rawValue))
        {
            return;
        }

        if (!int.TryParse(rawValue, out var port) || port is < 1 or > 65535)
        {
            issues.Add(new ProductionConfigValidationIssue(
                "PRODUCTION_CONFIG_INVALID_POSTGRES_PORT",
                "CARBONOPS_PARSER_POSTGRES_PORT must be an integer between 1 and 65535.",
                "CARBONOPS_PARSER_POSTGRES_PORT"));
        }
    }

    private static void ValidateLogLevel(
        string? rawValue,
        ICollection<ProductionConfigValidationIssue> issues)
    {
        if (!HasText(rawValue))
        {
            return;
        }

        if (rawValue is not null && !ValidLogLevels.Contains(rawValue.Trim()))
        {
            issues.Add(new ProductionConfigValidationIssue(
                "PRODUCTION_CONFIG_INVALID_LOG_LEVEL",
                "CARBONOPS_PARSER_LOG_LEVEL must be one of debug, info, warning, error, or critical.",
                "CARBONOPS_PARSER_LOG_LEVEL"));
        }
    }

    private static bool HasText(string? value) => !string.IsNullOrWhiteSpace(value);

    private static string? Get(IReadOnlyDictionary<string, string?> values, string key) =>
        values.TryGetValue(key, out var value) ? value : null;
}

public sealed record ProductionConfigLoadResult(
    IReadOnlyDictionary<string, string?> Values,
    IReadOnlyList<ProductionConfigValidationIssue> Issues,
    bool ConfigFileLoaded,
    bool EnvironmentLoaded);

public static class ProductionConfigLoader
{
    public static ProductionConfigLoadResult Load(
        string? configPath,
        IReadOnlyDictionary<string, string?> environment)
    {
        var values = new Dictionary<string, string?>(StringComparer.Ordinal);
        var issues = new List<ProductionConfigValidationIssue>();
        var configFileLoaded = false;

        foreach (var key in ProductionConfigBoundary.KnownConfigurationKeys)
        {
            values[key] = null;
        }

        if (!string.IsNullOrWhiteSpace(configPath))
        {
            configFileLoaded = LoadFileValues(configPath, values, issues);
        }

        foreach (var key in ProductionConfigBoundary.KnownConfigurationKeys)
        {
            if (environment.TryGetValue(key, out var value))
            {
                values[key] = value;
            }
        }

        return new ProductionConfigLoadResult(
            values,
            Array.AsReadOnly(issues.ToArray()),
            configFileLoaded,
            EnvironmentLoaded: true);
    }

    private static bool LoadFileValues(
        string configPath,
        IDictionary<string, string?> values,
        ICollection<ProductionConfigValidationIssue> issues)
    {
        if (!File.Exists(configPath))
        {
            issues.Add(new ProductionConfigValidationIssue(
                "PRODUCTION_CONFIG_FILE_NOT_FOUND",
                "Config file was not found.",
                "config"));
            return false;
        }

        try
        {
            using var stream = File.OpenRead(configPath);
            using var document = JsonDocument.Parse(stream);

            if (document.RootElement.ValueKind != JsonValueKind.Object)
            {
                issues.Add(new ProductionConfigValidationIssue(
                    "PRODUCTION_CONFIG_FILE_INVALID_SHAPE",
                    "Config file root must be a JSON object.",
                    "config"));
                return false;
            }

            foreach (var property in document.RootElement.EnumerateObject().OrderBy(item => item.Name, StringComparer.Ordinal))
            {
                if (!values.ContainsKey(property.Name))
                {
                    continue;
                }

                if (!TryReadScalar(property.Value, out var value))
                {
                    issues.Add(new ProductionConfigValidationIssue(
                        "PRODUCTION_CONFIG_FILE_INVALID_VALUE",
                        "Config file values must be scalar strings, numbers, booleans, or null.",
                        property.Name));
                    continue;
                }

                values[property.Name] = value;
            }

            return true;
        }
        catch (JsonException)
        {
            issues.Add(new ProductionConfigValidationIssue(
                "PRODUCTION_CONFIG_FILE_INVALID_JSON",
                "Config file must be valid JSON.",
                "config"));
            return false;
        }
        catch (IOException)
        {
            issues.Add(new ProductionConfigValidationIssue(
                "PRODUCTION_CONFIG_FILE_READ_FAILED",
                "Config file could not be read.",
                "config"));
            return false;
        }
        catch (UnauthorizedAccessException)
        {
            issues.Add(new ProductionConfigValidationIssue(
                "PRODUCTION_CONFIG_FILE_READ_FAILED",
                "Config file could not be read.",
                "config"));
            return false;
        }
    }

    private static bool TryReadScalar(JsonElement element, out string? value)
    {
        switch (element.ValueKind)
        {
            case JsonValueKind.String:
                value = element.GetString();
                return true;
            case JsonValueKind.Number:
            case JsonValueKind.True:
            case JsonValueKind.False:
                value = element.GetRawText();
                return true;
            case JsonValueKind.Null:
                value = null;
                return true;
            default:
                value = null;
                return false;
        }
    }
}
