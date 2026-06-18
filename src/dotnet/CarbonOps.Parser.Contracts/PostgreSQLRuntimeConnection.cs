using Npgsql;

namespace CarbonOps.Parser.Contracts;

public sealed record PostgreSQLRuntimeConnectionSettings(
    string Host,
    int Port,
    string Database,
    string Username,
    string Password,
    string Schema,
    string ApplicationName = "carbonops-parser-dotnet",
    int ConnectTimeoutSeconds = 15)
{
    public PostgreSQLPersistenceOptions ToSafeOptions() =>
        new(
            Host,
            Port,
            Database,
            Username,
            PasswordSet: !string.IsNullOrWhiteSpace(Password),
            ApplicationName: ApplicationName,
            ConnectTimeoutSeconds: ConnectTimeoutSeconds);
}

public sealed record PostgreSQLRuntimeConnectionSettingsValidationIssue(
    string Code,
    string Message,
    string FieldName,
    string Severity = "error");

public sealed record PostgreSQLRuntimeConnectionSettingsValidationResult
{
    public IReadOnlyList<PostgreSQLRuntimeConnectionSettingsValidationIssue> Issues { get; }

    public bool IsValid => Issues.Count == 0;

    public PostgreSQLRuntimeConnectionSettingsValidationResult(
        IEnumerable<PostgreSQLRuntimeConnectionSettingsValidationIssue>? issues = null)
    {
        Issues = Array.AsReadOnly((issues ?? []).ToArray());
    }
}

public static class PostgreSQLRuntimeConnectionBoundary
{
    public static PostgreSQLRuntimeConnectionSettingsValidationResult Validate(
        PostgreSQLRuntimeConnectionSettings settings)
    {
        var issues = new List<PostgreSQLRuntimeConnectionSettingsValidationIssue>();
        var optionsValidation = PostgreSQLPersistenceOptionsValidator.Validate(settings.ToSafeOptions());

        foreach (var issue in optionsValidation.Issues)
        {
            issues.Add(new PostgreSQLRuntimeConnectionSettingsValidationIssue(
                issue.Code,
                issue.Message,
                issue.FieldName,
                issue.Severity));
        }

        if (string.IsNullOrWhiteSpace(settings.Password))
        {
            issues.Add(new PostgreSQLRuntimeConnectionSettingsValidationIssue(
                "POSTGRESQL_RUNTIME_MISSING_PASSWORD",
                "password must be configured for explicit PostgreSQL runtime commands.",
                "password"));
        }

        ValidateIdentifier(settings.Schema, "schema", issues);

        return new PostgreSQLRuntimeConnectionSettingsValidationResult(issues);
    }

    public static bool TryCreateFromProductionConfig(
        IReadOnlyDictionary<string, string?> values,
        out PostgreSQLRuntimeConnectionSettings? settings,
        out IReadOnlyList<PostgreSQLRuntimeConnectionSettingsValidationIssue> issues)
    {
        settings = null;
        var collectedIssues = new List<PostgreSQLRuntimeConnectionSettingsValidationIssue>();

        if (!int.TryParse(Get(values, "CARBONOPS_PARSER_POSTGRES_PORT"), out var port))
        {
            port = 0;
        }

        settings = new PostgreSQLRuntimeConnectionSettings(
            Get(values, "CARBONOPS_PARSER_POSTGRES_HOST") ?? string.Empty,
            port,
            Get(values, "CARBONOPS_PARSER_POSTGRES_DATABASE") ?? string.Empty,
            Get(values, "CARBONOPS_PARSER_POSTGRES_USERNAME") ?? string.Empty,
            Get(values, "CARBONOPS_PARSER_POSTGRES_PASSWORD") ?? string.Empty,
            Get(values, "CARBONOPS_PARSER_POSTGRES_SCHEMA") ?? string.Empty);

        collectedIssues.AddRange(Validate(settings).Issues);
        issues = Array.AsReadOnly(collectedIssues.ToArray());
        return collectedIssues.Count == 0;
    }

    public static IReadOnlyDictionary<string, string> BuildSafeDiagnostics(
        PostgreSQLRuntimeConnectionSettings settings) =>
        new Dictionary<string, string>(StringComparer.Ordinal)
        {
            ["postgresql_host"] = settings.Host,
            ["postgresql_port"] = settings.Port.ToString(System.Globalization.CultureInfo.InvariantCulture),
            ["postgresql_database"] = settings.Database,
            ["postgresql_username"] = settings.Username,
            ["postgresql_schema"] = settings.Schema,
            ["postgresql_password_set"] = (!string.IsNullOrWhiteSpace(settings.Password)).ToString(),
            ["postgresql_password"] = "[redacted]",
            ["postgresql_connection_string"] = "[redacted]",
        };

    public static string BuildConnectionString(PostgreSQLRuntimeConnectionSettings settings)
    {
        var validation = Validate(settings);
        if (!validation.IsValid)
        {
            throw new ArgumentException("PostgreSQL runtime settings are invalid.", nameof(settings));
        }

        var builder = new NpgsqlConnectionStringBuilder
        {
            Host = settings.Host,
            Port = settings.Port,
            Database = settings.Database,
            Username = settings.Username,
            Password = settings.Password,
            SearchPath = settings.Schema,
            ApplicationName = settings.ApplicationName,
            Timeout = settings.ConnectTimeoutSeconds,
            IncludeErrorDetail = false,
        };

        return builder.ConnectionString;
    }

    internal static string RenderIdentifier(string identifier, string fieldName)
    {
        if (!IsValidIdentifier(identifier))
        {
            throw new ArgumentException($"{fieldName} must be a PostgreSQL-safe identifier.", fieldName);
        }

        return identifier;
    }

    private static void ValidateIdentifier(
        string? value,
        string fieldName,
        ICollection<PostgreSQLRuntimeConnectionSettingsValidationIssue> issues)
    {
        if (!IsValidIdentifier(value))
        {
            issues.Add(new PostgreSQLRuntimeConnectionSettingsValidationIssue(
                "POSTGRESQL_RUNTIME_INVALID_IDENTIFIER",
                $"{fieldName} must contain only lowercase letters, digits, and underscores, and must start with a letter.",
                fieldName));
        }
    }

    private static bool IsValidIdentifier(string? value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            return false;
        }

        if (value.Length > 63 || !char.IsAsciiLetterLower(value[0]))
        {
            return false;
        }

        return value.All(character =>
            char.IsAsciiLetterLower(character) ||
            char.IsAsciiDigit(character) ||
            character == '_');
    }

    private static string? Get(IReadOnlyDictionary<string, string?> values, string key) =>
        values.TryGetValue(key, out var value) ? value : null;
}
