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
        Assert.True(description.LoadsEnvironment);
        Assert.True(description.LoadsConfigFiles);
        Assert.True(description.LoadsCredentials);
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

    [Fact]
    public void LoaderAcceptsValidConfigFileOnlyShape()
    {
        var configPath = WriteConfigFile(ValidConfig());

        var load = ProductionConfigLoader.Load(configPath, new Dictionary<string, string?>());
        var result = ProductionConfigBoundary.Validate(load.Values);

        Assert.True(load.ConfigFileLoaded);
        Assert.True(load.EnvironmentLoaded);
        Assert.Empty(load.Issues);
        Assert.True(result.IsValid);
        Assert.Equal("db.internal.example", load.Values["CARBONOPS_PARSER_POSTGRES_HOST"]);
    }

    [Fact]
    public void LoaderAcceptsValidEnvironmentOnlyShape()
    {
        var load = ProductionConfigLoader.Load(null, ValidConfig());
        var result = ProductionConfigBoundary.Validate(load.Values);

        Assert.False(load.ConfigFileLoaded);
        Assert.True(load.EnvironmentLoaded);
        Assert.Empty(load.Issues);
        Assert.True(result.IsValid);
    }

    [Fact]
    public void LoaderEnvironmentValuesOverrideConfigFileValues()
    {
        var fileValues = ValidConfig();
        fileValues["CARBONOPS_PARSER_POSTGRES_HOST"] = "file-db.internal.example";
        fileValues["CARBONOPS_PARSER_POSTGRES_PORT"] = "1111";
        var configPath = WriteConfigFile(fileValues);
        var environment = new Dictionary<string, string?>(StringComparer.Ordinal)
        {
            ["CARBONOPS_PARSER_POSTGRES_HOST"] = "env-db.internal.example",
            ["CARBONOPS_PARSER_POSTGRES_PORT"] = "5433",
        };

        var load = ProductionConfigLoader.Load(configPath, environment);

        Assert.Equal("env-db.internal.example", load.Values["CARBONOPS_PARSER_POSTGRES_HOST"]);
        Assert.Equal("5433", load.Values["CARBONOPS_PARSER_POSTGRES_PORT"]);
    }

    [Fact]
    public void LoaderMissingRequiredValuesFailClosed()
    {
        var values = ValidConfig();
        values.Remove("CARBONOPS_PARSER_POSTGRES_HOST");
        var configPath = WriteConfigFile(values);

        var load = ProductionConfigLoader.Load(configPath, new Dictionary<string, string?>());
        var result = ProductionConfigBoundary.Validate(load.Values);

        Assert.False(result.IsValid);
        Assert.Contains(result.Issues, issue =>
            issue.Code == "PRODUCTION_CONFIG_MISSING_REQUIRED_ENV_VAR" &&
            issue.FieldName == "CARBONOPS_PARSER_POSTGRES_HOST");
    }

    [Fact]
    public void LoaderInvalidPortFailsClosed()
    {
        var values = ValidConfig();
        values["CARBONOPS_PARSER_POSTGRES_PORT"] = "70000";
        var configPath = WriteConfigFile(values);

        var load = ProductionConfigLoader.Load(configPath, new Dictionary<string, string?>());
        var result = ProductionConfigBoundary.Validate(load.Values);

        Assert.False(result.IsValid);
        Assert.Contains(result.Issues, issue => issue.Code == "PRODUCTION_CONFIG_INVALID_POSTGRES_PORT");
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

    private static string WriteConfigFile(IReadOnlyDictionary<string, string?> values)
    {
        var path = Path.Combine(Path.GetTempPath(), $"carbonops-production-config-{Guid.NewGuid():N}.json");
        var json = System.Text.Json.JsonSerializer.Serialize(values);
        File.WriteAllText(path, json);
        return path;
    }
}
