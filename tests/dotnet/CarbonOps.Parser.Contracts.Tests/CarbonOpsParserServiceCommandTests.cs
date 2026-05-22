using CarbonOps.Parser.Service;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class CarbonOpsParserServiceCommandTests
{
    [Fact]
    public void HelpDocumentsScheduledWorkerCommandSurface()
    {
        var output = new StringWriter();
        var error = new StringWriter();

        var exitCode = CarbonOpsParserServiceCommand.Run(["help"], output, error, ValidEnvironment());

        Assert.Equal(0, exitCode);
        var rendered = output.ToString();
        Assert.Contains("validate-config", rendered, StringComparison.Ordinal);
        Assert.Contains("validate-postgresql-runtime", rendered, StringComparison.Ordinal);
        Assert.Contains("run-once", rendered, StringComparison.Ordinal);
        Assert.Contains("scheduled-worker", rendered, StringComparison.Ordinal);
        Assert.Equal(string.Empty, error.ToString());
    }

    [Fact]
    public void ValidateConfigReportsPresenceWithoutOpeningPostgreSqlOrPrintingSecrets()
    {
        var output = new StringWriter();
        var environment = ValidEnvironment();

        var exitCode = CarbonOpsParserServiceCommand.Run(
            ["validate-config"],
            output,
            TextWriter.Null,
            environment);

        Assert.Equal(0, exitCode);
        var rendered = output.ToString();
        Assert.Contains("status=ready", rendered, StringComparison.Ordinal);
        Assert.Contains("postgresql_connection_opened=False", rendered, StringComparison.Ordinal);
        Assert.Contains("CARBONOPS_PARSER_POSTGRES_PASSWORD_present=True", rendered, StringComparison.Ordinal);
        Assert.DoesNotContain("runtime-secret-not-returned", rendered, StringComparison.Ordinal);
        Assert.DoesNotContain("Password=raw-secret", rendered, StringComparison.Ordinal);
    }

    [Fact]
    public void ValidateConfigAcceptsConfigFileOnlyValidShape()
    {
        var output = new StringWriter();
        var configPath = WriteConfigFile(ValidEnvironment());

        var exitCode = CarbonOpsParserServiceCommand.Run(
            ["validate-config", "--config", configPath],
            output,
            TextWriter.Null,
            new Dictionary<string, string?>());

        Assert.Equal(0, exitCode);
        var rendered = output.ToString();
        Assert.Contains("status=ready", rendered, StringComparison.Ordinal);
        Assert.Contains("config_file_loaded=True", rendered, StringComparison.Ordinal);
        Assert.Contains("environment_loaded=True", rendered, StringComparison.Ordinal);
        Assert.Contains("postgresql_connection_opened=False", rendered, StringComparison.Ordinal);
        Assert.DoesNotContain("runtime-secret-not-returned", rendered, StringComparison.Ordinal);
    }

    [Fact]
    public void ValidatePostgreSqlRuntimeReportsReadinessWithoutClaimingProductionReady()
    {
        var output = new StringWriter();

        var exitCode = CarbonOpsParserServiceCommand.Run(
            ["validate-postgresql-runtime"],
            output,
            TextWriter.Null,
            ValidEnvironment());

        Assert.Equal(0, exitCode);
        var rendered = output.ToString();
        Assert.Contains("status=ready", rendered, StringComparison.Ordinal);
        Assert.Contains(".net_runtime_production_ready=False", rendered, StringComparison.Ordinal);
        Assert.Contains("project_level_production_ready=False", rendered, StringComparison.Ordinal);
        Assert.Contains("postgresql_connection_opened=False", rendered, StringComparison.Ordinal);
        Assert.Contains("schema_bootstrap_available=True", rendered, StringComparison.Ordinal);
        Assert.Contains("year_state_available=True", rendered, StringComparison.Ordinal);
        Assert.Contains("source_download_implemented=False", rendered, StringComparison.Ordinal);
        Assert.Contains("parser_orchestration_implemented=False", rendered, StringComparison.Ordinal);
        Assert.Contains("master_detail_inserts_implemented=False", rendered, StringComparison.Ordinal);
        Assert.Contains("source_family_year_states", rendered, StringComparison.Ordinal);
        Assert.DoesNotContain("runtime-secret-not-returned", rendered, StringComparison.Ordinal);
    }

    [Fact]
    public void ValidatePostgreSqlRuntimeFailsClosedWhenConfigIsMissing()
    {
        var output = new StringWriter();

        var exitCode = CarbonOpsParserServiceCommand.Run(
            ["validate-postgresql-runtime"],
            output,
            TextWriter.Null,
            new Dictionary<string, string?>());

        Assert.Equal(2, exitCode);
        var rendered = output.ToString();
        Assert.Contains("status=blocked", rendered, StringComparison.Ordinal);
        Assert.Contains(".net_runtime_production_ready=False", rendered, StringComparison.Ordinal);
        Assert.Contains("postgresql_connection_opened=False", rendered, StringComparison.Ordinal);
        Assert.Contains("PRODUCTION_CONFIG_MISSING_REQUIRED_ENV_VAR", rendered, StringComparison.Ordinal);
    }

    [Fact]
    public void ValidateConfigEnvironmentOverridesConfigFile()
    {
        var output = new StringWriter();
        var fileValues = ValidEnvironment();
        fileValues["CARBONOPS_PARSER_POSTGRES_PORT"] = "70000";
        var configPath = WriteConfigFile(fileValues);
        var environment = new Dictionary<string, string?>(StringComparer.Ordinal)
        {
            ["CARBONOPS_PARSER_POSTGRES_PORT"] = "5432",
        };

        var exitCode = CarbonOpsParserServiceCommand.Run(
            ["validate-config", "--config", configPath],
            output,
            TextWriter.Null,
            environment);

        Assert.Equal(0, exitCode);
        var rendered = output.ToString();
        Assert.Contains("status=ready", rendered, StringComparison.Ordinal);
        Assert.DoesNotContain("PRODUCTION_CONFIG_INVALID_POSTGRES_PORT", rendered, StringComparison.Ordinal);
    }

    [Fact]
    public void ValidateConfigFailsClosedForMissingValuesWithoutPrintingSecrets()
    {
        var output = new StringWriter();
        var environment = ValidEnvironment();
        environment["CARBONOPS_PARSER_POSTGRES_PASSWORD"] = "";

        var exitCode = CarbonOpsParserServiceCommand.Run(
            ["validate-config"],
            output,
            TextWriter.Null,
            environment);

        Assert.Equal(2, exitCode);
        var rendered = output.ToString();
        Assert.Contains("status=blocked", rendered, StringComparison.Ordinal);
        Assert.Contains("PRODUCTION_CONFIG_MISSING_REQUIRED_ENV_VAR", rendered, StringComparison.Ordinal);
        Assert.DoesNotContain("runtime-secret-not-returned", rendered, StringComparison.Ordinal);
    }

    [Fact]
    public void ValidateConfigFailsClosedForInvalidPort()
    {
        var output = new StringWriter();
        var environment = ValidEnvironment();
        environment["CARBONOPS_PARSER_POSTGRES_PORT"] = "not-a-port";

        var exitCode = CarbonOpsParserServiceCommand.Run(
            ["validate-config"],
            output,
            TextWriter.Null,
            environment);

        Assert.Equal(2, exitCode);
        var rendered = output.ToString();
        Assert.Contains("status=blocked", rendered, StringComparison.Ordinal);
        Assert.Contains("issue=PRODUCTION_CONFIG_INVALID_POSTGRES_PORT", rendered, StringComparison.Ordinal);
        Assert.Contains("field=CARBONOPS_PARSER_POSTGRES_PORT", rendered, StringComparison.Ordinal);
        Assert.Contains("severity=error", rendered, StringComparison.Ordinal);
    }

    [Fact]
    public void ValidateConfigRedactsRawConnectionStringWithCredentials()
    {
        var output = new StringWriter();
        var environment = ValidEnvironment();
        environment["CARBONOPS_PARSER_POSTGRES_CONNECTION_STRING"] =
            "postgresql://carbonops_runtime:raw-secret@db.internal.example/carbonops_parser";

        var exitCode = CarbonOpsParserServiceCommand.Run(
            ["validate-config"],
            output,
            TextWriter.Null,
            environment);

        Assert.Equal(2, exitCode);
        var rendered = output.ToString();
        Assert.Contains("PRODUCTION_CONFIG_RAW_CONNECTION_STRING_NOT_ALLOWED", rendered, StringComparison.Ordinal);
        Assert.DoesNotContain("raw-secret", rendered, StringComparison.Ordinal);
        Assert.DoesNotContain("carbonops_runtime:raw-secret", rendered, StringComparison.Ordinal);
    }

    [Fact]
    public void RunOnceFailsClosedUntilDotNetIngestionIsImplemented()
    {
        var output = new StringWriter();

        var exitCode = CarbonOpsParserServiceCommand.Run(
            ["run-once"],
            output,
            TextWriter.Null,
            ValidEnvironment());

        Assert.Equal(3, exitCode);
        var rendered = output.ToString();
        Assert.Contains("status=blocked", rendered, StringComparison.Ordinal);
        Assert.Contains("ingestion_status=not_implemented", rendered, StringComparison.Ordinal);
        Assert.Contains("postgresql_connection_opened=False", rendered, StringComparison.Ordinal);
        Assert.Contains("records_inserted=0", rendered, StringComparison.Ordinal);
        Assert.DoesNotContain("runtime-secret-not-returned", rendered, StringComparison.Ordinal);
    }

    [Fact]
    public void RunOnceAcceptsConfigOptionButRemainsNotImplementedAndNonZero()
    {
        var output = new StringWriter();
        var configPath = WriteConfigFile(ValidEnvironment());

        var exitCode = CarbonOpsParserServiceCommand.Run(
            ["run-once", "--config", configPath],
            output,
            TextWriter.Null,
            new Dictionary<string, string?>());

        Assert.Equal(3, exitCode);
        var rendered = output.ToString();
        Assert.Contains("status=blocked", rendered, StringComparison.Ordinal);
        Assert.Contains("ingestion_status=not_implemented", rendered, StringComparison.Ordinal);
        Assert.Contains("config_status=ready", rendered, StringComparison.Ordinal);
        Assert.Contains("postgresql_connection_opened=False", rendered, StringComparison.Ordinal);
        Assert.DoesNotContain("runtime-secret-not-returned", rendered, StringComparison.Ordinal);
    }

    private static Dictionary<string, string?> ValidEnvironment() => new()
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

    private static string WriteConfigFile(IReadOnlyDictionary<string, string?> values)
    {
        var path = Path.Combine(Path.GetTempPath(), $"carbonops-service-config-{Guid.NewGuid():N}.json");
        var json = System.Text.Json.JsonSerializer.Serialize(values);
        File.WriteAllText(path, json);
        return path;
    }
}
