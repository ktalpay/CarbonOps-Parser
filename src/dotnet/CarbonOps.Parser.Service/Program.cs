using System.Collections;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Service;

public static class Program
{
    public static int Main(string[] args) =>
        CarbonOpsParserServiceCommand.Run(
            args,
            Console.Out,
            Console.Error,
            CarbonOpsParserServiceCommand.ReadProcessEnvironment());
}

public static class CarbonOpsParserServiceCommand
{
    public const int SuccessExitCode = 0;
    public const int ValidationFailedExitCode = 2;
    public const int NotImplementedExitCode = 3;
    public const string NotImplementedStatus = "not_implemented";

    public static int Run(
        string[] args,
        TextWriter output,
        TextWriter error,
        IReadOnlyDictionary<string, string?> environment)
    {
        var command = args.Length == 0 ? "help" : args[0].Trim();

        if (IsHelp(command))
        {
            WriteHelp(output);
            return SuccessExitCode;
        }

        if (string.Equals(command, "validate-config", StringComparison.OrdinalIgnoreCase))
        {
            return ValidateConfig(args.Skip(1).ToArray(), output, environment);
        }

        if (string.Equals(command, "validate-postgresql-runtime", StringComparison.OrdinalIgnoreCase))
        {
            return ValidatePostgreSQLRuntime(args.Skip(1).ToArray(), output, environment);
        }

        if (string.Equals(command, "run-once", StringComparison.OrdinalIgnoreCase))
        {
            return RunOnce(args.Skip(1).ToArray(), output, environment);
        }

        error.WriteLine($"Unknown command: {command}");
        WriteHelp(error);
        return ValidationFailedExitCode;
    }

    private static int ValidateConfig(
        string[] args,
        TextWriter output,
        IReadOnlyDictionary<string, string?> environment)
    {
        var commandOptions = ParseCommandOptions(args);
        var result = LoadAndValidate(commandOptions.ConfigPath, environment, commandOptions.Issues);

        output.WriteLine(result.Validation.IsValid ? "status=ready" : "status=blocked");
        output.WriteLine($"config_file_loaded={result.Load.ConfigFileLoaded}");
        output.WriteLine($"environment_loaded={result.Load.EnvironmentLoaded}");
        output.WriteLine("postgresql_connection_opened=False");
        output.WriteLine("secret_values_printed=False");

        foreach (var required in ProductionConfigBoundary.RequiredEnvironmentVariables)
        {
            if (ProductionConfigBoundary.SecretEnvironmentVariables.Contains(required, StringComparer.Ordinal))
            {
                output.WriteLine($"{required}_present={HasText(result.Load.Values[required])}");
                output.WriteLine("postgresql_password_configured=" + HasText(result.Load.Values[required]));
            }
            else
            {
                output.WriteLine($"{required}_present={HasText(result.Load.Values[required])}");
            }
        }

        WriteIssues(output, result.Validation.Issues);

        return result.Validation.IsValid ? SuccessExitCode : ValidationFailedExitCode;
    }

    private static int ValidatePostgreSQLRuntime(
        string[] args,
        TextWriter output,
        IReadOnlyDictionary<string, string?> environment)
    {
        var commandOptions = ParseCommandOptions(args);
        var result = LoadAndValidate(commandOptions.ConfigPath, environment, commandOptions.Issues);

        output.WriteLine(result.Validation.IsValid ? "status=ready" : "status=blocked");
        output.WriteLine(".net_runtime_production_ready=False");
        output.WriteLine("project_level_production_ready=False");
        output.WriteLine("postgresql_connection_opened=False");
        output.WriteLine("postgresql_sql_executed=False");
        output.WriteLine("schema_bootstrap_available=True");
        output.WriteLine("year_state_available=True");
        output.WriteLine("source_download_implemented=False");
        output.WriteLine("parser_orchestration_implemented=False");
        output.WriteLine("master_detail_inserts_implemented=False");

        if (result.Validation.IsValid &&
            PostgreSQLRuntimeConnectionBoundary.TryCreateFromProductionConfig(
                result.Load.Values,
                out var settings,
                out var runtimeIssues) &&
            settings is not null)
        {
            foreach (var diagnostic in PostgreSQLRuntimeConnectionBoundary.BuildSafeDiagnostics(settings))
            {
                output.WriteLine($"{diagnostic.Key}={diagnostic.Value}");
            }

            output.WriteLine($"required_table_count={PostgreSQLRuntimeSchemaCatalog.RequiredTableNames.Count}");
            output.WriteLine("required_tables=" + string.Join(",", PostgreSQLRuntimeSchemaCatalog.RequiredTableNames));
        }
        else
        {
            if (result.Validation.IsValid)
            {
                PostgreSQLRuntimeConnectionBoundary.TryCreateFromProductionConfig(
                    result.Load.Values,
                    out _,
                    out var runtimeValidationIssues);
                foreach (var issue in runtimeValidationIssues)
                {
                    var safeMessage = Phase1OperationalDiagnostics.RedactDiagnosticValue("message", issue.Message);
                    output.WriteLine(
                        $"issue={issue.Code} field={issue.FieldName} severity={issue.Severity} message={safeMessage}");
                }
            }
        }

        WriteIssues(output, result.Validation.Issues);

        return result.Validation.IsValid ? SuccessExitCode : ValidationFailedExitCode;
    }

    private static int RunOnce(
        string[] args,
        TextWriter output,
        IReadOnlyDictionary<string, string?> environment)
    {
        var commandOptions = ParseCommandOptions(args);
        var result = LoadAndValidate(commandOptions.ConfigPath, environment, commandOptions.Issues);

        output.WriteLine("status=blocked");
        output.WriteLine($"ingestion_status={NotImplementedStatus}");
        output.WriteLine("postgresql_connection_opened=False");
        output.WriteLine("records_inserted=0");
        output.WriteLine("message=.NET ingestion execution is not implemented in PROD-004.");

        if (!result.Validation.IsValid)
        {
            output.WriteLine("config_status=blocked");
            WriteIssues(output, result.Validation.Issues);
        }
        else
        {
            output.WriteLine("config_status=ready");
        }

        return NotImplementedExitCode;
    }

    private static ProductionConfigCommandValidation LoadAndValidate(
        string? configPath,
        IReadOnlyDictionary<string, string?> environment,
        IReadOnlyList<ProductionConfigValidationIssue> commandIssues)
    {
        var load = ProductionConfigLoader.Load(configPath, environment);
        var issues = new List<ProductionConfigValidationIssue>();
        issues.AddRange(commandIssues);
        issues.AddRange(load.Issues);
        issues.AddRange(ProductionConfigBoundary.Validate(load.Values).Issues);

        return new ProductionConfigCommandValidation(
            load,
            new ProductionConfigValidationResult(issues));
    }

    private static ProductionConfigCommandOptions ParseCommandOptions(string[] args)
    {
        var issues = new List<ProductionConfigValidationIssue>();
        string? configPath = null;

        for (var index = 0; index < args.Length; index++)
        {
            var arg = args[index];
            if (string.Equals(arg, "--config", StringComparison.OrdinalIgnoreCase))
            {
                if (index + 1 >= args.Length || string.IsNullOrWhiteSpace(args[index + 1]))
                {
                    issues.Add(new ProductionConfigValidationIssue(
                        "PRODUCTION_CONFIG_COMMAND_MISSING_CONFIG_PATH",
                        "--config requires a file path.",
                        "config"));
                    continue;
                }

                configPath = args[++index];
                continue;
            }

            issues.Add(new ProductionConfigValidationIssue(
                "PRODUCTION_CONFIG_COMMAND_UNKNOWN_ARGUMENT",
                "Unknown command argument.",
                "argument"));
        }

        return new ProductionConfigCommandOptions(
            configPath,
            Array.AsReadOnly(issues.ToArray()));
    }

    public static IReadOnlyDictionary<string, string?> ReadProcessEnvironment()
    {
        var values = new Dictionary<string, string?>(StringComparer.Ordinal);

        foreach (DictionaryEntry entry in Environment.GetEnvironmentVariables())
        {
            if (entry.Key is string key)
            {
                values[key] = entry.Value?.ToString();
            }
        }

        return values;
    }

    private static void WriteIssues(
        TextWriter output,
        IReadOnlyList<ProductionConfigValidationIssue> issues)
    {
        foreach (var issue in issues)
        {
            var safeMessage = Phase1OperationalDiagnostics.RedactDiagnosticValue("message", issue.Message);
            output.WriteLine(
                $"issue={issue.Code} field={issue.FieldName} severity={issue.Severity} message={safeMessage}");
        }
    }

    private static bool IsHelp(string command) =>
        string.Equals(command, "help", StringComparison.OrdinalIgnoreCase) ||
        string.Equals(command, "--help", StringComparison.OrdinalIgnoreCase) ||
        string.Equals(command, "-h", StringComparison.OrdinalIgnoreCase);

    private static bool HasText(string? value) => !string.IsNullOrWhiteSpace(value);

    private static void WriteHelp(TextWriter writer)
    {
        writer.WriteLine("CarbonOps.Parser.Service");
        writer.WriteLine();
        writer.WriteLine("Usage:");
        writer.WriteLine("  dotnet run --project src/dotnet/CarbonOps.Parser.Service -- <command> [--config <path>]");
        writer.WriteLine();
        writer.WriteLine("Commands:");
        writer.WriteLine("  help                         Show this command surface.");
        writer.WriteLine("  validate-config              Validate required .NET runtime configuration shape without opening PostgreSQL.");
        writer.WriteLine("  validate-postgresql-runtime  Report .NET PostgreSQL schema/year-state readiness without opening PostgreSQL.");
        writer.WriteLine("  run-once                     Run one scheduled-worker cycle placeholder; fails closed until .NET ingestion is implemented.");
    }

    private sealed record ProductionConfigCommandOptions(
        string? ConfigPath,
        IReadOnlyList<ProductionConfigValidationIssue> Issues);

    private sealed record ProductionConfigCommandValidation(
        ProductionConfigLoadResult Load,
        ProductionConfigValidationResult Validation);
}
