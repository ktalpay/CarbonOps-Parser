namespace CarbonOps.Parser.Contracts;

public static class ContractWireNames
{
    public static string ToWireName(this SourceFamily value) =>
        value switch
        {
            SourceFamily.GhgProtocol => "ghg_protocol",
            SourceFamily.DefraDesnz => "defra_desnz",
            SourceFamily.IpccEfdb => "ipcc_efdb",
            _ => throw new ArgumentOutOfRangeException(nameof(value), value, "Unknown source family."),
        };

    public static string ToWireName(this IngestionRunStatus value) =>
        value switch
        {
            IngestionRunStatus.Pending => "pending",
            IngestionRunStatus.Running => "running",
            IngestionRunStatus.Completed => "completed",
            IngestionRunStatus.Failed => "failed",
            IngestionRunStatus.Cancelled => "cancelled",
            _ => throw new ArgumentOutOfRangeException(nameof(value), value, "Unknown ingestion run status."),
        };

    public static string ToWireName(this SourceDocumentStatus value) =>
        value switch
        {
            SourceDocumentStatus.Discovered => "discovered",
            SourceDocumentStatus.Downloaded => "downloaded",
            SourceDocumentStatus.Failed => "failed",
            SourceDocumentStatus.Skipped => "skipped",
            _ => throw new ArgumentOutOfRangeException(nameof(value), value, "Unknown source document status."),
        };

    public static string ToWireName(this ParserRunStatus value) =>
        value switch
        {
            ParserRunStatus.Pending => "pending",
            ParserRunStatus.Running => "running",
            ParserRunStatus.Completed => "completed",
            ParserRunStatus.Failed => "failed",
            _ => throw new ArgumentOutOfRangeException(nameof(value), value, "Unknown parser run status."),
        };

    public static string ToWireName(this SourceDiscoveryStatus value) =>
        value switch
        {
            SourceDiscoveryStatus.Declared => "declared",
            _ => throw new ArgumentOutOfRangeException(nameof(value), value, "Unknown source discovery status."),
        };

    public static string ToWireName(this GhgSourceDiscoveryMode value) =>
        value switch
        {
            GhgSourceDiscoveryMode.RuntimePassive => "runtime_passive",
            _ => throw new ArgumentOutOfRangeException(nameof(value), value, "Unknown GHG source discovery mode."),
        };

    public static string ToWireName(this GhgSourceDiscoveryStatus value) =>
        value switch
        {
            GhgSourceDiscoveryStatus.Declared => "declared",
            GhgSourceDiscoveryStatus.Invalid => "invalid",
            _ => throw new ArgumentOutOfRangeException(nameof(value), value, "Unknown GHG source discovery status."),
        };

    public static string ToWireName(this GhgSourceDownloadExecutionStatus value) =>
        value switch
        {
            GhgSourceDownloadExecutionStatus.Blocked => "blocked",
            GhgSourceDownloadExecutionStatus.Downloaded => "downloaded",
            GhgSourceDownloadExecutionStatus.Failed => "failed",
            _ => throw new ArgumentOutOfRangeException(
                nameof(value),
                value,
                "Unknown GHG source download execution status."),
        };

    public static string ToWireName(this ParserSourceFormat value) =>
        value switch
        {
            ParserSourceFormat.DiscoveryReference => "discovery_reference",
            _ => throw new ArgumentOutOfRangeException(nameof(value), value, "Unknown parser source format."),
        };

    public static string ToWireName(this ParserAdapterReadiness value) =>
        value switch
        {
            ParserAdapterReadiness.ExecutionNotImplemented => "execution_not_implemented",
            _ => throw new ArgumentOutOfRangeException(nameof(value), value, "Unknown parser adapter readiness."),
        };

    public static string ToWireName(this ParserValidationIssueSeverity value) =>
        value switch
        {
            ParserValidationIssueSeverity.Info => "info",
            ParserValidationIssueSeverity.Warning => "warning",
            ParserValidationIssueSeverity.Error => "error",
            _ => throw new ArgumentOutOfRangeException(nameof(value), value, "Unknown parser validation issue severity."),
        };

    public static string ToWireName(this ParserDryRunStatus value) =>
        value switch
        {
            ParserDryRunStatus.Planned => "planned",
            ParserDryRunStatus.InvalidRequest => "invalid_request",
            ParserDryRunStatus.ExecutionNotImplemented => "execution_not_implemented",
            _ => throw new ArgumentOutOfRangeException(nameof(value), value, "Unknown parser dry-run status."),
        };

    public static string ToWireName(this PostgreSQLRuntimeConfigGateStatus value) =>
        value switch
        {
            PostgreSQLRuntimeConfigGateStatus.Disabled => "disabled",
            PostgreSQLRuntimeConfigGateStatus.Blocked => "blocked",
            PostgreSQLRuntimeConfigGateStatus.NotEnabled => "not_enabled",
            _ => throw new ArgumentOutOfRangeException(
                nameof(value),
                value,
                "Unknown PostgreSQL runtime config gate status."),
        };

    public static bool TryParseSourceFamilyWireName(string? wireName, out SourceFamily value)
    {
        value = wireName switch
        {
            "ghg_protocol" => SourceFamily.GhgProtocol,
            "defra_desnz" => SourceFamily.DefraDesnz,
            "ipcc_efdb" => SourceFamily.IpccEfdb,
            _ => default,
        };

        return wireName is "ghg_protocol" or "defra_desnz" or "ipcc_efdb";
    }

    public static bool TryParseIngestionRunStatusWireName(string? wireName, out IngestionRunStatus value)
    {
        value = wireName switch
        {
            "pending" => IngestionRunStatus.Pending,
            "running" => IngestionRunStatus.Running,
            "completed" => IngestionRunStatus.Completed,
            "failed" => IngestionRunStatus.Failed,
            "cancelled" => IngestionRunStatus.Cancelled,
            _ => default,
        };

        return wireName is "pending" or "running" or "completed" or "failed" or "cancelled";
    }

    public static bool TryParseSourceDocumentStatusWireName(string? wireName, out SourceDocumentStatus value)
    {
        value = wireName switch
        {
            "discovered" => SourceDocumentStatus.Discovered,
            "downloaded" => SourceDocumentStatus.Downloaded,
            "failed" => SourceDocumentStatus.Failed,
            "skipped" => SourceDocumentStatus.Skipped,
            _ => default,
        };

        return wireName is "discovered" or "downloaded" or "failed" or "skipped";
    }

    public static bool TryParseParserRunStatusWireName(string? wireName, out ParserRunStatus value)
    {
        value = wireName switch
        {
            "pending" => ParserRunStatus.Pending,
            "running" => ParserRunStatus.Running,
            "completed" => ParserRunStatus.Completed,
            "failed" => ParserRunStatus.Failed,
            _ => default,
        };

        return wireName is "pending" or "running" or "completed" or "failed";
    }

    public static bool TryParseSourceDiscoveryStatusWireName(string? wireName, out SourceDiscoveryStatus value)
    {
        value = wireName switch
        {
            "declared" => SourceDiscoveryStatus.Declared,
            _ => default,
        };

        return wireName is "declared";
    }

    public static bool TryParseGhgSourceDiscoveryModeWireName(string? wireName, out GhgSourceDiscoveryMode value)
    {
        value = wireName switch
        {
            "runtime_passive" => GhgSourceDiscoveryMode.RuntimePassive,
            _ => default,
        };

        return wireName is "runtime_passive";
    }

    public static bool TryParseGhgSourceDiscoveryStatusWireName(string? wireName, out GhgSourceDiscoveryStatus value)
    {
        value = wireName switch
        {
            "declared" => GhgSourceDiscoveryStatus.Declared,
            "invalid" => GhgSourceDiscoveryStatus.Invalid,
            _ => default,
        };

        return wireName is "declared" or "invalid";
    }

    public static bool TryParseGhgSourceDownloadExecutionStatusWireName(
        string? wireName,
        out GhgSourceDownloadExecutionStatus value)
    {
        value = wireName switch
        {
            "blocked" => GhgSourceDownloadExecutionStatus.Blocked,
            "downloaded" => GhgSourceDownloadExecutionStatus.Downloaded,
            "failed" => GhgSourceDownloadExecutionStatus.Failed,
            _ => default,
        };

        return wireName is "blocked" or "downloaded" or "failed";
    }

    public static bool TryParseParserSourceFormatWireName(string? wireName, out ParserSourceFormat value)
    {
        value = wireName switch
        {
            "discovery_reference" => ParserSourceFormat.DiscoveryReference,
            _ => default,
        };

        return wireName is "discovery_reference";
    }

    public static bool TryParseParserAdapterReadinessWireName(string? wireName, out ParserAdapterReadiness value)
    {
        value = wireName switch
        {
            "execution_not_implemented" => ParserAdapterReadiness.ExecutionNotImplemented,
            _ => default,
        };

        return wireName is "execution_not_implemented";
    }

    public static bool TryParseParserValidationIssueSeverityWireName(
        string? wireName,
        out ParserValidationIssueSeverity value)
    {
        value = wireName switch
        {
            "info" => ParserValidationIssueSeverity.Info,
            "warning" => ParserValidationIssueSeverity.Warning,
            "error" => ParserValidationIssueSeverity.Error,
            _ => default,
        };

        return wireName is "info" or "warning" or "error";
    }

    public static bool TryParseParserDryRunStatusWireName(string? wireName, out ParserDryRunStatus value)
    {
        value = wireName switch
        {
            "planned" => ParserDryRunStatus.Planned,
            "invalid_request" => ParserDryRunStatus.InvalidRequest,
            "execution_not_implemented" => ParserDryRunStatus.ExecutionNotImplemented,
            _ => default,
        };

        return wireName is "planned" or "invalid_request" or "execution_not_implemented";
    }

    public static bool TryParsePostgreSQLRuntimeConfigGateStatusWireName(
        string? wireName,
        out PostgreSQLRuntimeConfigGateStatus value)
    {
        value = wireName switch
        {
            "disabled" => PostgreSQLRuntimeConfigGateStatus.Disabled,
            "blocked" => PostgreSQLRuntimeConfigGateStatus.Blocked,
            "not_enabled" => PostgreSQLRuntimeConfigGateStatus.NotEnabled,
            _ => default,
        };

        return wireName is "disabled" or "blocked" or "not_enabled";
    }
}
