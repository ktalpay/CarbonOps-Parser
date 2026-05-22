using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class PostgreSQLRuntimeSchemaAndYearStateTests
{
    [Fact]
    public void BootstrapDdlIsAdditiveOnlyAndIncludesRequiredTables()
    {
        var statements = PostgreSQLRuntimeSchemaDdl.RenderIdempotentSchemaStatements();
        var rendered = string.Join("\n", statements);

        Assert.All(
            PostgreSQLRuntimeSchemaCatalog.RequiredTableNames,
            tableName => Assert.Contains($"CREATE TABLE IF NOT EXISTS {tableName}", rendered, StringComparison.Ordinal));
        Assert.Contains("CREATE INDEX IF NOT EXISTS idx_source_family_year_states_family_year", rendered, StringComparison.Ordinal);
        Assert.Contains("source_family_year_states", PostgreSQLSchemaBootstrapBoundary.RequiredPhase1TableNames);
        Assert.Equal(
            PostgreSQLRuntimeSchemaCatalog.RequiredTableNames,
            PostgreSQLSchemaBootstrapBoundary.RequiredPhase1TableNames);
    }

    [Fact]
    public void BootstrapDdlContainsNoDestructiveSqlTokens()
    {
        var statements = PostgreSQLRuntimeSchemaDdl.RenderIdempotentSchemaStatements();

        Assert.All(statements, statement =>
        {
            Assert.False(PostgreSQLRuntimeSchemaDdl.ContainsDestructiveSql(statement), statement);
            Assert.DoesNotContain("DROP", statement, StringComparison.OrdinalIgnoreCase);
            Assert.DoesNotContain("TRUNCATE", statement, StringComparison.OrdinalIgnoreCase);
            Assert.DoesNotContain("DELETE", statement, StringComparison.OrdinalIgnoreCase);
            Assert.DoesNotContain("ALTER TABLE", statement, StringComparison.OrdinalIgnoreCase);
            Assert.DoesNotContain("RENAME", statement, StringComparison.OrdinalIgnoreCase);
        });
    }

    [Fact]
    public void RuntimeSettingsFailClosedForMissingOrInvalidDatabaseConfig()
    {
        var values = ValidConfig();
        values["CARBONOPS_PARSER_POSTGRES_PASSWORD"] = string.Empty;
        values["CARBONOPS_PARSER_POSTGRES_SCHEMA"] = "Invalid-Schema";

        var created = PostgreSQLRuntimeConnectionBoundary.TryCreateFromProductionConfig(
            values,
            out var settings,
            out var issues);

        Assert.False(created);
        Assert.NotNull(settings);
        Assert.Contains(issues, issue => issue.Code == "POSTGRESQL_RUNTIME_MISSING_PASSWORD");
        Assert.Contains(issues, issue => issue.Code == "POSTGRESQL_RUNTIME_INVALID_IDENTIFIER");
    }

    [Fact]
    public void RuntimeDiagnosticsRedactSecretValues()
    {
        Assert.True(PostgreSQLRuntimeConnectionBoundary.TryCreateFromProductionConfig(
            ValidConfig(),
            out var settings,
            out var issues));
        Assert.Empty(issues);

        var diagnostics = PostgreSQLRuntimeConnectionBoundary.BuildSafeDiagnostics(settings!);
        var rendered = string.Join("\n", diagnostics.Select(item => $"{item.Key}={item.Value}"));

        Assert.Contains("postgresql_password=[redacted]", rendered, StringComparison.Ordinal);
        Assert.Contains("postgresql_connection_string=[redacted]", rendered, StringComparison.Ordinal);
        Assert.DoesNotContain("runtime-secret-not-returned", rendered, StringComparison.Ordinal);
    }

    [Fact]
    public async Task YearStateReturnsInitialYearWhenNoDataExists()
    {
        var session = new InMemoryYearStateSession();
        var repository = new PostgreSQLSourceFamilyYearStateRepository(session);

        var state = await repository.GetYearStateAsync(SourceFamily.GhgProtocol);

        Assert.Equal(SourceFamily.GhgProtocol, state.SourceFamily);
        Assert.Null(state.LatestYear);
        Assert.Equal(2024, state.InitialYear);
        Assert.Equal(2024, state.NextYear);
    }

    [Fact]
    public async Task YearStateReturnsNextYearWhenSuccessfulYearExists()
    {
        var session = new InMemoryYearStateSession();
        var repository = new PostgreSQLSourceFamilyYearStateRepository(session);

        await repository.RecordSuccessfulYearAsync(SourceFamily.DefraDesnz, 2025);
        var state = await repository.GetYearStateAsync(SourceFamily.DefraDesnz);

        Assert.Equal(2025, state.LatestYear);
        Assert.Equal(2026, state.NextYear);
    }

    [Fact]
    public async Task RecordSuccessfulYearIsIdempotent()
    {
        var session = new InMemoryYearStateSession();
        var repository = new PostgreSQLSourceFamilyYearStateRepository(session);

        await repository.RecordSuccessfulYearAsync(SourceFamily.IpccEfdb, 2024);
        await repository.RecordSuccessfulYearAsync(SourceFamily.IpccEfdb, 2024);

        Assert.Equal(1, session.RecordCount(SourceFamily.IpccEfdb));
        Assert.Equal(2025, await repository.NextTargetYearAsync(SourceFamily.IpccEfdb));
    }

    [Fact]
    public void SourceFamilyRuntimeValuesAlignWithPythonPostgreSqlContract()
    {
        Assert.Equal("ghg_protocol", SourceFamily.GhgProtocol.ToPostgreSQLRuntimeValue());
        Assert.Equal("defra_desnz", SourceFamily.DefraDesnz.ToPostgreSQLRuntimeValue());
        Assert.Equal("ipcc_efdb", SourceFamily.IpccEfdb.ToPostgreSQLRuntimeValue());
    }

    private static Dictionary<string, string?> ValidConfig() => new()
    {
        ["CARBONOPS_PARSER_ENV"] = "production",
        ["CARBONOPS_PARSER_DATABASE_PROVIDER"] = "postgres",
        ["CARBONOPS_PARSER_POSTGRES_HOST"] = "db.internal.example",
        ["CARBONOPS_PARSER_POSTGRES_PORT"] = "5432",
        ["CARBONOPS_PARSER_POSTGRES_DATABASE"] = "carbonops_parser",
        ["CARBONOPS_PARSER_POSTGRES_USERNAME"] = "carbonops_runtime",
        ["CARBONOPS_PARSER_POSTGRES_PASSWORD"] = "runtime-secret-not-returned",
        ["CARBONOPS_PARSER_POSTGRES_SCHEMA"] = "carbonops",
        ["CARBONOPS_PARSER_RAW_ARCHIVE_PATH"] = "/var/lib/carbonops/raw",
        ["CARBONOPS_PARSER_LOG_LEVEL"] = "info",
    };

    private sealed class InMemoryYearStateSession : IPostgreSQLSourceFamilyYearStateSession
    {
        private readonly HashSet<(SourceFamily SourceFamily, int Year)> _records = [];

        public Task<int?> LatestSuccessfulYearAsync(
            SourceFamily sourceFamily,
            CancellationToken cancellationToken = default)
        {
            var years = _records
                .Where(record => record.SourceFamily == sourceFamily)
                .Select(record => record.Year)
                .ToArray();
            return Task.FromResult(years.Length == 0 ? null : (int?)years.Max());
        }

        public Task RecordSuccessfulYearAsync(
            SourceFamily sourceFamily,
            int ingestedYear,
            CancellationToken cancellationToken = default)
        {
            _records.Add((sourceFamily, ingestedYear));
            return Task.CompletedTask;
        }

        public int RecordCount(SourceFamily sourceFamily) =>
            _records.Count(record => record.SourceFamily == sourceFamily);
    }
}
