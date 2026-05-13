namespace CarbonOps.Parser.Contracts;

public sealed record PostgreSQLPersistenceOptions(
    string Host,
    int Port,
    string Database,
    string Username,
    bool PasswordSet = false,
    string? SslMode = null,
    string? ApplicationName = null,
    int? ConnectTimeoutSeconds = null);

public sealed record PostgreSQLPersistenceOptionsValidationIssue(
    string Code,
    string Message,
    string FieldName,
    string Severity = "error");

public sealed record PostgreSQLPersistenceOptionsValidationResult
{
    public IReadOnlyList<PostgreSQLPersistenceOptionsValidationIssue> Issues { get; }

    public bool IsValid => Issues.Count == 0;

    public PostgreSQLPersistenceOptionsValidationResult(
        IEnumerable<PostgreSQLPersistenceOptionsValidationIssue>? issues = null)
    {
        Issues = Array.AsReadOnly((issues ?? []).ToArray());
    }
}

public static class PostgreSQLPersistenceOptionsValidator
{
    public static PostgreSQLPersistenceOptionsValidationResult Validate(
        PostgreSQLPersistenceOptions options)
    {
        var issues = new List<PostgreSQLPersistenceOptionsValidationIssue>();

        ValidateRequiredText(
            options.Host,
            "host",
            "POSTGRESQL_OPTIONS_MISSING_HOST",
            "host must be a non-empty string.",
            issues);
        ValidatePort(options.Port, issues);
        ValidateRequiredText(
            options.Database,
            "database",
            "POSTGRESQL_OPTIONS_MISSING_DATABASE",
            "database must be a non-empty string.",
            issues);
        ValidateRequiredText(
            options.Username,
            "username",
            "POSTGRESQL_OPTIONS_MISSING_USERNAME",
            "username must be a non-empty string.",
            issues);
        ValidateOptionalText(
            options.SslMode,
            "ssl_mode",
            "POSTGRESQL_OPTIONS_BLANK_SSL_MODE",
            "ssl_mode must be non-empty when provided.",
            issues);
        ValidateOptionalText(
            options.ApplicationName,
            "application_name",
            "POSTGRESQL_OPTIONS_BLANK_APPLICATION_NAME",
            "application_name must be non-empty when provided.",
            issues);
        ValidateTimeout(options.ConnectTimeoutSeconds, issues);

        return new PostgreSQLPersistenceOptionsValidationResult(issues);
    }

    private static void ValidateRequiredText(
        string? value,
        string fieldName,
        string code,
        string message,
        ICollection<PostgreSQLPersistenceOptionsValidationIssue> issues)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            issues.Add(new PostgreSQLPersistenceOptionsValidationIssue(code, message, fieldName));
        }
    }

    private static void ValidateOptionalText(
        string? value,
        string fieldName,
        string code,
        string message,
        ICollection<PostgreSQLPersistenceOptionsValidationIssue> issues)
    {
        if (value is not null && string.IsNullOrWhiteSpace(value))
        {
            issues.Add(new PostgreSQLPersistenceOptionsValidationIssue(code, message, fieldName));
        }
    }

    private static void ValidatePort(
        int value,
        ICollection<PostgreSQLPersistenceOptionsValidationIssue> issues)
    {
        if (value is < 1 or > 65535)
        {
            issues.Add(new PostgreSQLPersistenceOptionsValidationIssue(
                "POSTGRESQL_OPTIONS_INVALID_PORT",
                "port must be an integer between 1 and 65535.",
                "port"));
        }
    }

    private static void ValidateTimeout(
        int? value,
        ICollection<PostgreSQLPersistenceOptionsValidationIssue> issues)
    {
        if (value is <= 0)
        {
            issues.Add(new PostgreSQLPersistenceOptionsValidationIssue(
                "POSTGRESQL_OPTIONS_INVALID_CONNECT_TIMEOUT",
                "connect_timeout_seconds must be a positive integer when provided.",
                "connect_timeout_seconds"));
        }
    }
}
