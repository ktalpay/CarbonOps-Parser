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
}
