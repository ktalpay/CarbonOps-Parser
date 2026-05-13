using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class ProductionConfigBoundaryTests
{
    [Fact]
    public void BoundaryDocumentsAlignedRequiredEnvironmentVariables()
    {
        var description = ProductionConfigBoundary.Describe();

        Assert.Equal(
            [
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
            ],
            description.RequiredEnvironmentVariables);
        Assert.Equal(["CARBONOPS_PARSER_POSTGRES_PASSWORD"], description.SecretEnvironmentVariables);
        Assert.Equal("postgres", description.Provider);
        Assert.False(description.LoadsEnvironment);
        Assert.False(description.LoadsConfigFiles);
        Assert.False(description.LoadsCredentials);
        Assert.False(description.LogsSecretValues);
    }

    [Fact]
    public void ValidProductionConfigMappingPassesWithoutReturningSecret()
    {
        var result = ProductionConfigBoundary.Validate(ValidConfig());

        Assert.True(result.IsValid);
        Assert.Empty(result.Issues);
    }

    [Fact]
    public void MissingRequiredProductionKeysFailClosedWithSafeMessages()
    {
        var values = ValidConfig();
        values["CARBONOPS_PARSER_POSTGRES_PASSWORD"] = " ";
        values["CARBONOPS_PARSER_RAW_ARCHIVE_PATH"] = null;

        var result = ProductionConfigBoundary.Validate(values);

        Assert.False(result.IsValid);
        Assert.Equal(
            ["CARBONOPS_PARSER_POSTGRES_PASSWORD", "CARBONOPS_PARSER_RAW_ARCHIVE_PATH"],
            result.Issues.Select(issue => issue.FieldName));
        Assert.DoesNotContain("runtime-secret-not-returned", result.ToString(), StringComparison.Ordinal);
        Assert.DoesNotContain("Password" + "=", result.ToString(), StringComparison.Ordinal);
    }

    [Fact]
    public void InvalidValuesFailWithActionableKeyOnlyMessages()
    {
        var values = ValidConfig();
        values["CARBONOPS_PARSER_DATABASE_PROVIDER"] = "mysql";
        values["CARBONOPS_PARSER_POSTGRES_PORT"] = "not-a-port";
        values["CARBONOPS_PARSER_LOG_LEVEL"] = "verbose";
        values["CARBONOPS_PARSER_POSTGRES_CONNECTION_STRING"] = "Host=db;Username=svc;" + "Password" + "=raw-secret";

        var result = ProductionConfigBoundary.Validate(values);

        Assert.Equal(
            [
                "PRODUCTION_CONFIG_UNSUPPORTED_DATABASE_PROVIDER",
                "PRODUCTION_CONFIG_INVALID_POSTGRES_PORT",
                "PRODUCTION_CONFIG_INVALID_LOG_LEVEL",
                "PRODUCTION_CONFIG_RAW_CONNECTION_STRING_NOT_ALLOWED",
            ],
            result.Issues.Select(issue => issue.Code));
        var rendered = string.Join(" ", result.Issues.Select(issue => issue.ToString()));
        Assert.DoesNotContain("mysql", rendered, StringComparison.Ordinal);
        Assert.DoesNotContain("not-a-port", rendered, StringComparison.Ordinal);
        Assert.DoesNotContain("verbose", rendered, StringComparison.Ordinal);
        Assert.DoesNotContain("raw-secret", rendered, StringComparison.Ordinal);
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
}
