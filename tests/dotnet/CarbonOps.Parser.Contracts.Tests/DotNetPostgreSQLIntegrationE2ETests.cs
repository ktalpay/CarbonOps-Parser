using System.Security.Cryptography;
using Npgsql;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class DotNetPostgreSQLIntegrationE2ETests
{
    private const string OptInEnvironmentVariable = "CARBONOPS_RUN_DOTNET_POSTGRESQL_INTEGRATION";
    private const string DotNetTestDsnEnvironmentVariable = "CARBONOPS_DOTNET_POSTGRESQL_TEST_DSN";
    private const string SharedTestDsnEnvironmentVariable = "CARBONOPS_POSTGRESQL_TEST_DSN";

    [Fact]
    public void DefaultIntegrationGuardDoesNotConnectWithoutOptIn()
    {
        var gate = ResolveIntegrationSettings(
            new Dictionary<string, string?>(StringComparer.Ordinal),
            allowGeneratedSchema: true);

        Assert.False(gate.Enabled);
        Assert.False(gate.ConnectionAttempted);
        Assert.Contains(OptInEnvironmentVariable, gate.Reason, StringComparison.Ordinal);
    }

    [Fact]
    public void MissingPostgreSQLConfigFailsClosedWhenOptedIn()
    {
        var gate = ResolveIntegrationSettings(
            new Dictionary<string, string?>(StringComparer.Ordinal)
            {
                [OptInEnvironmentVariable] = "1",
            },
            allowGeneratedSchema: true);

        Assert.True(gate.Enabled);
        Assert.False(gate.ConnectionAttempted);
        Assert.False(gate.HasSettings);
        Assert.Contains("POSTGRESQL_RUNTIME_MISSING_PASSWORD", gate.Reason, StringComparison.Ordinal);
        Assert.DoesNotContain("Password=", gate.Reason, StringComparison.OrdinalIgnoreCase);
        Assert.DoesNotContain("postgresql://", gate.Reason, StringComparison.OrdinalIgnoreCase);
    }

    [Fact]
    public async Task DockerPostgreSQLBootstrapIsIdempotentWhenEnabled()
    {
        var gate = ResolveIntegrationSettingsFromEnvironment();
        if (!gate.Enabled)
        {
            return;
        }

        Assert.True(gate.HasSettings, gate.Reason);
        var bootstrapper = new PostgreSQLRuntimeSchemaBootstrapper();

        var first = await bootstrapper.BootstrapAsync(gate.Settings!);
        var second = await bootstrapper.BootstrapAsync(gate.Settings!);

        Assert.Empty(first.MissingTableNames);
        Assert.Empty(second.MissingTableNames);
        Assert.Equal(PostgreSQLRuntimeSchemaCatalog.RequiredTableNames, first.PresentTableNames);
        Assert.Equal(PostgreSQLRuntimeSchemaCatalog.RequiredTableNames, second.PresentTableNames);
        Assert.Empty(second.CreatedTableNames);
    }

    [Theory]
    [MemberData(nameof(SourceFamilyFixtureCases))]
    public async Task SourceFamilyFixtureInsertRerunAndYearStateAreIdempotentWhenEnabled(
        SourceFamily sourceFamily)
    {
        var gate = ResolveIntegrationSettingsFromEnvironment();
        if (!gate.Enabled)
        {
            return;
        }

        Assert.True(gate.HasSettings, gate.Reason);
        var settings = gate.Settings!;
        var bootstrapper = new PostgreSQLRuntimeSchemaBootstrapper();
        var firstBootstrap = await bootstrapper.BootstrapAsync(settings);
        var secondBootstrap = await bootstrapper.BootstrapAsync(settings);
        Assert.Empty(firstBootstrap.MissingTableNames);
        Assert.Empty(secondBootstrap.MissingTableNames);
        Assert.Empty(secondBootstrap.CreatedTableNames);

        await using var dataSource = NpgsqlDataSource.Create(
            PostgreSQLRuntimeConnectionBoundary.BuildConnectionString(settings));

        var parsed = ParseFixture(sourceFamily, settings.Schema, targetYear: 2024);
        var repository = new PostgreSQLSourceSpecificFactorPersistenceRepository(
            new NpgsqlSourceSpecificFactorPersistenceSession(dataSource));
        var yearState = new PostgreSQLSourceFamilyYearStateRepository(
            new NpgsqlSourceFamilyYearStateSession(dataSource));

        var first = await repository.PersistAsync(parsed);
        var second = await repository.PersistAsync(parsed);
        var state = await yearState.GetYearStateAsync(sourceFamily);
        var counts = await CountSourceFamilyRowsAsync(dataSource, sourceFamily, "prod009-" + settings.Schema);

        Assert.Equal(PostgreSQLSourceSpecificFactorPersistenceStatus.Inserted, first.Status);
        Assert.True(first.MasterInserted > 0);
        Assert.True(first.DetailInserted > 0);
        Assert.Equal(0, first.MasterSkippedDuplicate);
        Assert.Equal(0, first.DetailSkippedDuplicate);

        Assert.Equal(PostgreSQLSourceSpecificFactorPersistenceStatus.Inserted, second.Status);
        Assert.Equal(0, second.MasterInserted);
        Assert.Equal(0, second.DetailInserted);
        Assert.True(second.MasterSkippedDuplicate > 0);
        Assert.True(second.DetailSkippedDuplicate > 0);

        Assert.Equal(first.MasterInserted, counts.MasterRows);
        Assert.Equal(first.DetailInserted, counts.DetailRows);
        Assert.Equal(2024, state.LatestYear);
        Assert.Equal(2025, state.NextYear);
        Assert.Equal(1, await CountYearStateRowsAsync(dataSource, sourceFamily, 2024));
    }

    [Fact]
    public async Task PersistedParityFixtureBaselineWhenEnabled()
    {
        var gate = ResolveIntegrationSettingsFromEnvironment();
        if (!gate.Enabled)
        {
            return;
        }

        Assert.True(gate.HasSettings, gate.Reason);
        var settings = gate.Settings!;
        await new PostgreSQLRuntimeSchemaBootstrapper().BootstrapAsync(settings);
        await using var dataSource = NpgsqlDataSource.Create(
            PostgreSQLRuntimeConnectionBoundary.BuildConnectionString(settings));
        var repository = new PostgreSQLSourceSpecificFactorPersistenceRepository(
            new NpgsqlSourceSpecificFactorPersistenceSession(dataSource));

        foreach (var sourceFamily in SourceFamilyFixtureCases().Select(item => (SourceFamily)item[0]))
        {
            var parsed = ParseFixture(sourceFamily, "prod010-parity", targetYear: 2024);
            var first = await repository.PersistAsync(parsed);
            var second = await repository.PersistAsync(parsed);

            Assert.Equal(PostgreSQLSourceSpecificFactorPersistenceStatus.Inserted, first.Status);
            Assert.True(first.MasterInserted > 0);
            Assert.True(first.DetailInserted > 0);
            Assert.Equal(PostgreSQLSourceSpecificFactorPersistenceStatus.Inserted, second.Status);
            Assert.Equal(0, second.MasterInserted);
            Assert.Equal(0, second.DetailInserted);
            Assert.True(second.MasterSkippedDuplicate > 0);
            Assert.True(second.DetailSkippedDuplicate > 0);
            Assert.Equal(1, await CountYearStateRowsAsync(dataSource, sourceFamily, 2024));
        }
    }

    [Theory]
    [MemberData(nameof(SourceFamilyFixtureCases))]
    public async Task NoAvailableSourceYearDoesNotAdvanceYearStateWhenEnabled(
        SourceFamily sourceFamily)
    {
        var gate = ResolveIntegrationSettingsFromEnvironment();
        if (!gate.Enabled)
        {
            return;
        }

        Assert.True(gate.HasSettings, gate.Reason);
        await new PostgreSQLRuntimeSchemaBootstrapper().BootstrapAsync(gate.Settings!);
        await using var dataSource = NpgsqlDataSource.Create(
            PostgreSQLRuntimeConnectionBoundary.BuildConnectionString(gate.Settings!));
        var yearState = new PostgreSQLSourceFamilyYearStateRepository(
            new NpgsqlSourceFamilyYearStateSession(dataSource));
        await yearState.RecordSuccessfulYearAsync(sourceFamily, 2024);
        var orchestrator = new SourceCycleOrchestrator(
            yearState,
            [sourceFamily],
            artifacts: []);

        var result = await orchestrator.PreviewAsync();
        var run = Assert.Single(result.Runs);
        var after = await yearState.GetYearStateAsync(sourceFamily);

        Assert.Equal(SourceCycleRunStatus.NoAvailableSourceYear, run.Status);
        Assert.Equal(2024, run.LatestSuccessfulYear);
        Assert.Equal(2025, run.TargetYear);
        Assert.Equal(2024, after.LatestYear);
        Assert.Equal(2025, after.NextYear);
        Assert.Equal(1, await CountYearStateRowsAsync(dataSource, sourceFamily, 2024));
    }

    [Fact]
    public async Task FailedPersistenceRollsBackAndDoesNotAdvanceYearStateWhenEnabled()
    {
        var gate = ResolveIntegrationSettingsFromEnvironment();
        if (!gate.Enabled)
        {
            return;
        }

        Assert.True(gate.HasSettings, gate.Reason);
        var settings = gate.Settings!;
        await new PostgreSQLRuntimeSchemaBootstrapper().BootstrapAsync(settings);
        await using var dataSource = NpgsqlDataSource.Create(
            PostgreSQLRuntimeConnectionBoundary.BuildConnectionString(settings));
        var parsed = ParseFixture(SourceFamily.DefraDesnz, settings.Schema, targetYear: 2024);
        var mapped = PostgreSQLSourceSpecificFactorPersistenceMapper.Map(parsed);
        var validBatch = Assert.Single(mapped.Batches);
        var invalidDetail = validBatch.DetailRecords[0] with
        {
            SourceFamilyMasterId = Guid.NewGuid(),
            DetailExternalKey = "invalid-master-reference-" + settings.Schema,
        };
        var invalidBatch = validBatch with
        {
            DetailRecords = [invalidDetail],
        };
        var session = new NpgsqlSourceSpecificFactorPersistenceSession(dataSource);

        await Assert.ThrowsAnyAsync<PostgresException>(
            () => session.PersistSourceFamilyYearAsync(invalidBatch));

        Assert.Equal(0, await CountYearStateRowsAsync(dataSource, SourceFamily.DefraDesnz, 2024));
    }

    [Fact]
    public void IntegrationDiagnosticsRedactSecrets()
    {
        var secret = "secret-not-returned";
        var gate = ResolveIntegrationSettings(
            new Dictionary<string, string?>(StringComparer.Ordinal)
            {
                [OptInEnvironmentVariable] = "1",
                ["CARBONOPS_PARSER_ENV"] = "production",
                ["CARBONOPS_PARSER_DATABASE_PROVIDER"] = "postgres",
                ["CARBONOPS_PARSER_POSTGRES_HOST"] = "localhost",
                ["CARBONOPS_PARSER_POSTGRES_PORT"] = "5432",
                ["CARBONOPS_PARSER_POSTGRES_DATABASE"] = "carbonops_parser",
                ["CARBONOPS_PARSER_POSTGRES_USERNAME"] = "carbonops_runtime",
                ["CARBONOPS_PARSER_POSTGRES_PASSWORD"] = secret,
                ["CARBONOPS_PARSER_POSTGRES_SCHEMA"] = "carbonops_prod009_redaction",
                ["CARBONOPS_PARSER_RAW_ARCHIVE_PATH"] = "/tmp/carbonops-parser",
                ["CARBONOPS_PARSER_LOG_LEVEL"] = "info",
            },
            allowGeneratedSchema: false);

        Assert.True(gate.HasSettings, gate.Reason);
        var rendered = string.Join(
            "\n",
            PostgreSQLRuntimeConnectionBoundary.BuildSafeDiagnostics(gate.Settings!)
                .Select(item => $"{item.Key}={item.Value}"));

        Assert.Contains("postgresql_password=[redacted]", rendered, StringComparison.Ordinal);
        Assert.Contains("postgresql_connection_string=[redacted]", rendered, StringComparison.Ordinal);
        Assert.DoesNotContain(secret, rendered, StringComparison.Ordinal);
    }

    private static IntegrationGate ResolveIntegrationSettingsFromEnvironment() =>
        ResolveIntegrationSettings(
            Environment.GetEnvironmentVariables()
                .Cast<System.Collections.DictionaryEntry>()
                .ToDictionary(
                    entry => (string)entry.Key,
                    entry => entry.Value?.ToString(),
                    StringComparer.Ordinal),
            allowGeneratedSchema: true);

    private static IntegrationGate ResolveIntegrationSettings(
        IReadOnlyDictionary<string, string?> environment,
        bool allowGeneratedSchema)
    {
        if (!string.Equals(Get(environment, OptInEnvironmentVariable), "1", StringComparison.Ordinal))
        {
            return new IntegrationGate(
                Enabled: false,
                ConnectionAttempted: false,
                HasSettings: false,
                Settings: null,
                Reason: $"{OptInEnvironmentVariable}=1 is required for .NET PostgreSQL integration tests.");
        }

        var schema = Get(environment, "CARBONOPS_DOTNET_POSTGRESQL_TEST_SCHEMA");
        if (string.IsNullOrWhiteSpace(schema) && allowGeneratedSchema)
        {
            schema = "carbonops_prod009_" + Guid.NewGuid().ToString("N");
        }

        var dsn = Get(environment, DotNetTestDsnEnvironmentVariable) ?? Get(environment, SharedTestDsnEnvironmentVariable);
        if (!string.IsNullOrWhiteSpace(dsn))
        {
            return ResolveFromDsn(dsn, schema);
        }

        var values = ProductionConfigBoundary.KnownConfigurationKeys.ToDictionary(
            key => key,
            key => Get(environment, key),
            StringComparer.Ordinal);
        if (!string.IsNullOrWhiteSpace(schema))
        {
            values["CARBONOPS_PARSER_POSTGRES_SCHEMA"] = schema;
        }

        var created = PostgreSQLRuntimeConnectionBoundary.TryCreateFromProductionConfig(
            values,
            out var settings,
            out var issues);
        return created && settings is not null
            ? new IntegrationGate(true, false, true, settings, "ready")
            : new IntegrationGate(true, false, false, null, string.Join(",", issues.Select(issue => issue.Code)));
    }

    private static IntegrationGate ResolveFromDsn(string dsn, string? schema)
    {
        try
        {
            if (Uri.TryCreate(dsn, UriKind.Absolute, out var uri) &&
                (string.Equals(uri.Scheme, "postgresql", StringComparison.OrdinalIgnoreCase) ||
                    string.Equals(uri.Scheme, "postgres", StringComparison.OrdinalIgnoreCase)))
            {
                return ResolveFromPostgreSQLUri(uri, schema);
            }

            var builder = new NpgsqlConnectionStringBuilder(dsn);
            var resolvedSchema = string.IsNullOrWhiteSpace(schema)
                ? FirstSearchPathSchema(builder.SearchPath)
                : schema;
            var settings = new PostgreSQLRuntimeConnectionSettings(
                builder.Host ?? string.Empty,
                builder.Port,
                builder.Database ?? string.Empty,
                builder.Username ?? string.Empty,
                builder.Password ?? string.Empty,
                resolvedSchema ?? string.Empty,
                string.IsNullOrWhiteSpace(builder.ApplicationName)
                    ? "carbonops-parser-dotnet-prod009-tests"
                    : builder.ApplicationName,
                builder.Timeout <= 0 ? 15 : builder.Timeout);
            var validation = PostgreSQLRuntimeConnectionBoundary.Validate(settings);
            return validation.IsValid
                ? new IntegrationGate(true, false, true, settings, "ready")
                : new IntegrationGate(
                    true,
                    false,
                    false,
                    null,
                    string.Join(",", validation.Issues.Select(issue => issue.Code)));
        }
        catch (ArgumentException ex)
        {
            return new IntegrationGate(true, false, false, null, ex.GetType().Name);
        }
    }

    private static IntegrationGate ResolveFromPostgreSQLUri(Uri uri, string? schema)
    {
        var userInfo = uri.UserInfo.Split(':', 2);
        var settings = new PostgreSQLRuntimeConnectionSettings(
            uri.Host,
            uri.Port > 0 ? uri.Port : 5432,
            Uri.UnescapeDataString(uri.AbsolutePath.TrimStart('/')),
            userInfo.Length > 0 ? Uri.UnescapeDataString(userInfo[0]) : string.Empty,
            userInfo.Length > 1 ? Uri.UnescapeDataString(userInfo[1]) : string.Empty,
            schema ?? string.Empty,
            "carbonops-parser-dotnet-prod009-tests");
        var validation = PostgreSQLRuntimeConnectionBoundary.Validate(settings);
        return validation.IsValid
            ? new IntegrationGate(true, false, true, settings, "ready")
            : new IntegrationGate(
                true,
                false,
                false,
                null,
                string.Join(",", validation.Issues.Select(issue => issue.Code)));
    }

    public static IEnumerable<object[]> SourceFamilyFixtureCases()
    {
        yield return [SourceFamily.GhgProtocol];
        yield return [SourceFamily.DefraDesnz];
        yield return [SourceFamily.IpccEfdb];
    }

    private static ParserNormalizedOutputBatch ParseFixture(
        SourceFamily sourceFamily,
        string uniqueLabel,
        int targetYear)
    {
        var fixture = Fixture(sourceFamily);
        var artifactPath = FixturePath(fixture.FamilyDirectory, fixture.FileName);
        var content = File.ReadAllText(artifactPath);
        var artifactChecksum = Sha256Hex(content);
        var parserKey = ParserSelectionRegistry.GetParserKey(sourceFamily);
        var artifact = new ParserInputArtifact(
            sourceFamily,
            sourceFamily.ToWireName(),
            parserKey,
            ParserSourceFormat.DiscoveryReference,
            artifactPath,
            Path.GetFileName(artifactPath),
            "sha256",
            artifactChecksum,
            isDryRunChecksum: false,
            "text/csv",
            ".csv",
            reportingYear: targetYear);
        var request = new ParserAdapterRunRequest(
            sourceFamily,
            sourceFamily.ToWireName(),
            parserKey,
            [artifact],
            runId: "prod009-" + uniqueLabel,
            requestedReportingYear: targetYear);
        var contentByArtifactReference = new Dictionary<string, string>(StringComparer.Ordinal)
        {
            [artifactPath] = content,
        };
        var parsed = sourceFamily switch
        {
            SourceFamily.GhgProtocol => GhgProtocolNormalizedContentParser.Parse(request, contentByArtifactReference),
            SourceFamily.DefraDesnz => DefraDesnzNormalizedContentParser.Parse(request, contentByArtifactReference),
            SourceFamily.IpccEfdb => IpccEfdbNormalizedContentParser.Parse(request, contentByArtifactReference),
            _ => throw new ArgumentOutOfRangeException(nameof(sourceFamily), sourceFamily, "Unknown source family."),
        };

        Assert.Equal(ParserRunStatus.Completed, parsed.Status);
        Assert.True(parsed.RowCount > 0);

        return new ParserNormalizedOutputBatch(
            parsed.Rows.Select(row => RewriteForIsolatedE2E(row, uniqueLabel, artifactChecksum, targetYear)));
    }

    private static ParserNormalizedOutputRow RewriteForIsolatedE2E(
        ParserNormalizedOutputRow row,
        string uniqueLabel,
        string artifactChecksum,
        int targetYear)
    {
        var sourceVersion = "prod009-" + uniqueLabel;
        var factorId = row.Fields
            .Where(field => field.Key == "factor_id")
            .Select(field => field.Value)
            .FirstOrDefault() ?? row.RowIdentifier;
        var replacementFields = row.Fields
            .Where(field => field.Key is not (
                "source_year" or
                "source_version" or
                "run_id" or
                "provenance_checksum_value" or
                "master_external_key" or
                "source_family_master_id" or
                "source_family_detail_id"))
            .Concat(
            [
                new ParserNormalizedField("source_year", targetYear.ToString(System.Globalization.CultureInfo.InvariantCulture)),
                new ParserNormalizedField("source_version", sourceVersion),
                new ParserNormalizedField("run_id", "prod009-" + uniqueLabel),
                new ParserNormalizedField("provenance_checksum_value", artifactChecksum),
                new ParserNormalizedField("master_external_key", $"{targetYear}:{sourceVersion}:{factorId}"),
            ]);

        return new ParserNormalizedOutputRow(
            row.SourceFamily,
            row.SourceKey,
            row.ParserKey,
            row.ArtifactReference,
            row.RowIdentifier,
            row.SourceRowNumber,
            replacementFields,
            row.Issues,
            targetYear);
    }

    private static async Task<(int MasterRows, int DetailRows)> CountSourceFamilyRowsAsync(
        NpgsqlDataSource dataSource,
        SourceFamily sourceFamily,
        string sourceVersion)
    {
        var names = SourceFamilyRepositoryRegistry.GetTableNames(sourceFamily);
        var masterIdColumn = SourceFamilyMasterIdColumn(sourceFamily);
        await using var command = dataSource.CreateCommand($$"""
            SELECT
              (SELECT count(*) FROM {{names.MasterTableName}} WHERE source_version = $1),
              (SELECT count(*) FROM {{names.DetailTableName}} d
               JOIN {{names.MasterTableName}} m
                 ON m.{{masterIdColumn}} = d.{{masterIdColumn}}
               WHERE m.source_version = $1)
            """);
        command.Parameters.AddWithValue(sourceVersion);

        await using var reader = await command.ExecuteReaderAsync();
        Assert.True(await reader.ReadAsync());
        return (Convert.ToInt32(reader.GetInt64(0)), Convert.ToInt32(reader.GetInt64(1)));
    }

    private static (string FamilyDirectory, string FileName) Fixture(SourceFamily sourceFamily) =>
        sourceFamily switch
        {
            SourceFamily.GhgProtocol => ("ghg_protocol", "ghg_protocol_sample_factors.csv"),
            SourceFamily.DefraDesnz => ("defra_desnz", "defra_desnz_normalized_factors.csv"),
            SourceFamily.IpccEfdb => ("ipcc_efdb", "ipcc_efdb_sample_factors.csv"),
            _ => throw new ArgumentOutOfRangeException(nameof(sourceFamily), sourceFamily, "Unknown source family."),
        };

    private static string SourceFamilyMasterIdColumn(SourceFamily sourceFamily) =>
        sourceFamily switch
        {
            SourceFamily.GhgProtocol => "ghg_emission_factor_master_id",
            SourceFamily.DefraDesnz => "defra_emission_factor_master_id",
            SourceFamily.IpccEfdb => "ipcc_emission_factor_master_id",
            _ => throw new ArgumentOutOfRangeException(nameof(sourceFamily), sourceFamily, "Unknown source family."),
        };

    private static async Task<int> CountYearStateRowsAsync(
        NpgsqlDataSource dataSource,
        SourceFamily sourceFamily,
        int year)
    {
        await using var command = dataSource.CreateCommand("""
            SELECT count(*)
            FROM source_family_year_states
            WHERE source_family = $1
              AND ingested_year = $2
            """);
        command.Parameters.AddWithValue(sourceFamily.ToPostgreSQLRuntimeValue());
        command.Parameters.AddWithValue(year);
        var count = await command.ExecuteScalarAsync();
        return Convert.ToInt32(count, System.Globalization.CultureInfo.InvariantCulture);
    }

    private static string FixturePath(string familyDirectory, string fileName)
    {
        var directory = new DirectoryInfo(AppContext.BaseDirectory);
        while (directory is not null)
        {
            var fixtureDirectory = Path.Combine(
                directory.FullName,
                "tests",
                "fixtures",
                "source_documents",
                familyDirectory);
            if (Directory.Exists(fixtureDirectory))
            {
                return Path.Combine(fixtureDirectory, fileName);
            }

            directory = directory.Parent;
        }

        throw new DirectoryNotFoundException("Could not locate source document fixture directory.");
    }

    private static string Sha256Hex(string content) =>
        Convert.ToHexString(SHA256.HashData(System.Text.Encoding.UTF8.GetBytes(content))).ToLowerInvariant();

    private static string? FirstSearchPathSchema(string? searchPath) =>
        searchPath?
            .Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries)
            .FirstOrDefault();

    private static string? Get(IReadOnlyDictionary<string, string?> values, string key) =>
        values.TryGetValue(key, out var value) ? value : null;

    private sealed record IntegrationGate(
        bool Enabled,
        bool ConnectionAttempted,
        bool HasSettings,
        PostgreSQLRuntimeConnectionSettings? Settings,
        string Reason);
}
