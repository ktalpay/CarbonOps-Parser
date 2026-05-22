namespace CarbonOps.Parser.Contracts;

public enum PostgreSQLSchemaBootstrapMode
{
    CheckOnly = 0,
    CreateMissing = 1,
}

public enum PostgreSQLSchemaBootstrapTableStatus
{
    Required = 0,
    Present = 1,
    Missing = 2,
    Created = 3,
    Skipped = 4,
}

public sealed record PostgreSQLSchemaBootstrapRequest
{
    public PostgreSQLSchemaBootstrapMode Mode { get; }

    public IReadOnlyList<string> RequiredTableNames { get; }

    public bool FailOnMissing { get; }

    public PostgreSQLSchemaBootstrapRequest(
        PostgreSQLSchemaBootstrapMode mode,
        IEnumerable<string> requiredTableNames,
        bool failOnMissing = true)
    {
        Mode = mode;
        RequiredTableNames = Array.AsReadOnly(requiredTableNames.ToArray());
        FailOnMissing = failOnMissing;
    }
}

public sealed record PostgreSQLSchemaBootstrapTableResult(
    string TableName,
    PostgreSQLSchemaBootstrapTableStatus Status,
    string Reason = "");

public sealed record PostgreSQLSchemaBootstrapReport
{
    public PostgreSQLSchemaBootstrapMode Mode { get; }

    public IReadOnlyList<string> RequiredTableNames { get; }

    public IReadOnlyList<PostgreSQLSchemaBootstrapTableResult> TableResults { get; }

    public bool FailOnMissing { get; }

    public bool NoExecution { get; }

    public bool OpensConnection { get; }

    public bool RunsSql { get; }

    public bool CreatesTablesNow { get; }

    public bool RunsMigrations { get; }

    public bool ReadsEnvironment { get; }

    public bool WritesFiles { get; }

    public bool PerformsNetworkCalls { get; }

    public IReadOnlyList<string> MissingTableNames => Array.AsReadOnly(
        TableResults
            .Where(result => result.Status == PostgreSQLSchemaBootstrapTableStatus.Missing)
            .Select(result => result.TableName)
            .ToArray());

    public IReadOnlyList<string> PresentTableNames => Array.AsReadOnly(
        TableResults
            .Where(result => result.Status == PostgreSQLSchemaBootstrapTableStatus.Present)
            .Select(result => result.TableName)
            .ToArray());

    public IReadOnlyList<string> CreatedTableNames => Array.AsReadOnly(
        TableResults
            .Where(result => result.Status == PostgreSQLSchemaBootstrapTableStatus.Created)
            .Select(result => result.TableName)
            .ToArray());

    public IReadOnlyList<string> SkippedTableNames => Array.AsReadOnly(
        TableResults
            .Where(result => result.Status == PostgreSQLSchemaBootstrapTableStatus.Skipped)
            .Select(result => result.TableName)
            .ToArray());

    public PostgreSQLSchemaBootstrapReport(
        PostgreSQLSchemaBootstrapMode mode,
        IEnumerable<string> requiredTableNames,
        IEnumerable<PostgreSQLSchemaBootstrapTableResult> tableResults,
        bool failOnMissing,
        bool noExecution,
        bool opensConnection,
        bool runsSql,
        bool createsTablesNow,
        bool runsMigrations,
        bool readsEnvironment,
        bool writesFiles,
        bool performsNetworkCalls)
    {
        Mode = mode;
        RequiredTableNames = Array.AsReadOnly(requiredTableNames.ToArray());
        TableResults = Array.AsReadOnly(tableResults.ToArray());
        FailOnMissing = failOnMissing;
        NoExecution = noExecution;
        OpensConnection = opensConnection;
        RunsSql = runsSql;
        CreatesTablesNow = createsTablesNow;
        RunsMigrations = runsMigrations;
        ReadsEnvironment = readsEnvironment;
        WritesFiles = writesFiles;
        PerformsNetworkCalls = performsNetworkCalls;
    }
}

public static class PostgreSQLSchemaBootstrapBoundary
{
    public static IReadOnlyList<string> RequiredPhase1TableNames { get; } = Array.AsReadOnly(
        PostgreSQLRuntimeSchemaCatalog.RequiredTableNames.ToArray());

    public static PostgreSQLSchemaBootstrapRequest CreateRequest(
        PostgreSQLSchemaBootstrapMode mode = PostgreSQLSchemaBootstrapMode.CheckOnly,
        bool failOnMissing = true) =>
        new(mode, RequiredPhase1TableNames, failOnMissing);

    public static PostgreSQLSchemaBootstrapReport BuildReport(
        PostgreSQLSchemaBootstrapMode mode = PostgreSQLSchemaBootstrapMode.CheckOnly,
        IEnumerable<string>? presentTableNames = null,
        IEnumerable<string>? createdTableNames = null,
        IEnumerable<string>? skippedTableNames = null,
        bool failOnMissing = true)
    {
        var request = CreateRequest(mode, failOnMissing);
        var presentTables = (presentTableNames ?? []).ToHashSet(StringComparer.Ordinal);
        var createdTables = (createdTableNames ?? []).ToHashSet(StringComparer.Ordinal);
        var skippedTables = (skippedTableNames ?? []).ToHashSet(StringComparer.Ordinal);

        var tableResults = request.RequiredTableNames.Select(tableName => new PostgreSQLSchemaBootstrapTableResult(
            tableName,
            ResolveTableStatus(tableName, request.Mode, presentTables, createdTables, skippedTables),
            ResolveTableReason(tableName, request.Mode, presentTables, createdTables, skippedTables)));

        return new PostgreSQLSchemaBootstrapReport(
            request.Mode,
            request.RequiredTableNames,
            tableResults,
            request.FailOnMissing,
            noExecution: true,
            opensConnection: false,
            runsSql: false,
            createsTablesNow: false,
            runsMigrations: false,
            readsEnvironment: false,
            writesFiles: false,
            performsNetworkCalls: false);
    }

    private static PostgreSQLSchemaBootstrapTableStatus ResolveTableStatus(
        string tableName,
        PostgreSQLSchemaBootstrapMode mode,
        ISet<string> presentTableNames,
        ISet<string> createdTableNames,
        ISet<string> skippedTableNames)
    {
        if (presentTableNames.Contains(tableName))
        {
            return PostgreSQLSchemaBootstrapTableStatus.Present;
        }

        if (mode == PostgreSQLSchemaBootstrapMode.CreateMissing &&
            createdTableNames.Contains(tableName))
        {
            return PostgreSQLSchemaBootstrapTableStatus.Created;
        }

        if (skippedTableNames.Contains(tableName))
        {
            return PostgreSQLSchemaBootstrapTableStatus.Skipped;
        }

        return PostgreSQLSchemaBootstrapTableStatus.Missing;
    }

    private static string ResolveTableReason(
        string tableName,
        PostgreSQLSchemaBootstrapMode mode,
        ISet<string> presentTableNames,
        ISet<string> createdTableNames,
        ISet<string> skippedTableNames)
    {
        if (presentTableNames.Contains(tableName))
        {
            return "Required table was reported present by caller metadata.";
        }

        if (mode == PostgreSQLSchemaBootstrapMode.CreateMissing &&
            createdTableNames.Contains(tableName))
        {
            return "Required table was reported created by caller metadata.";
        }

        if (skippedTableNames.Contains(tableName))
        {
            return "Required table was reported skipped by caller metadata.";
        }

        return "Required table was not reported present or created.";
    }
}
