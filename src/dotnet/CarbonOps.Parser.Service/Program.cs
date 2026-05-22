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
            return ValidateConfig(output, environment);
        }

        if (string.Equals(command, "run-once", StringComparison.OrdinalIgnoreCase))
        {
            return RunOnce(output, environment);
        }

        error.WriteLine($"Unknown command: {command}");
        WriteHelp(error);
        return ValidationFailedExitCode;
    }

    private static int ValidateConfig(
        TextWriter output,
        IReadOnlyDictionary<string, string?> environment)
    {
        var values = ReadKnownEnvironment(environment);
        var result = ProductionConfigBoundary.Validate(values);

        output.WriteLine(result.IsValid ? "status=ready" : "status=blocked");
        output.WriteLine("postgresql_connection_opened=False");
        output.WriteLine("secret_values_printed=False");

        foreach (var required in ProductionConfigBoundary.RequiredEnvironmentVariables)
        {
            output.WriteLine($"{required}_present={HasText(values[required])}");
        }

        foreach (var issue in result.Issues)
        {
            output.WriteLine($"issue={issue.Code} field={issue.FieldName} severity={issue.Severity}");
        }

        return result.IsValid ? SuccessExitCode : ValidationFailedExitCode;
    }

    private static int RunOnce(
        TextWriter output,
        IReadOnlyDictionary<string, string?> environment)
    {
        var values = ReadKnownEnvironment(environment);
        var result = ProductionConfigBoundary.Validate(values);

        output.WriteLine("status=blocked");
        output.WriteLine($"ingestion_status={NotImplementedStatus}");
        output.WriteLine("postgresql_connection_opened=False");
        output.WriteLine("records_inserted=0");
        output.WriteLine("message=.NET ingestion execution is not implemented in PROD-003.");

        if (!result.IsValid)
        {
            output.WriteLine("config_status=blocked");
            foreach (var issue in result.Issues)
            {
                output.WriteLine($"issue={issue.Code} field={issue.FieldName} severity={issue.Severity}");
            }
        }
        else
        {
            output.WriteLine("config_status=ready");
        }

        return NotImplementedExitCode;
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

    private static IReadOnlyDictionary<string, string?> ReadKnownEnvironment(
        IReadOnlyDictionary<string, string?> environment)
    {
        var values = new Dictionary<string, string?>(StringComparer.Ordinal);

        foreach (var required in ProductionConfigBoundary.RequiredEnvironmentVariables)
        {
            values[required] = environment.TryGetValue(required, out var value) ? value : null;
        }

        values["CARBONOPS_PARSER_POSTGRES_CONNECTION_STRING"] =
            environment.TryGetValue("CARBONOPS_PARSER_POSTGRES_CONNECTION_STRING", out var connectionString)
                ? connectionString
                : null;

        return values;
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
        writer.WriteLine("  dotnet run --project src/dotnet/CarbonOps.Parser.Service -- <command>");
        writer.WriteLine();
        writer.WriteLine("Commands:");
        writer.WriteLine("  help             Show this command surface.");
        writer.WriteLine("  validate-config  Validate required .NET runtime configuration shape without opening PostgreSQL.");
        writer.WriteLine("  run-once         Run one scheduled-worker cycle placeholder; fails closed until .NET ingestion is implemented.");
    }
}
