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

    public static string ToWireName(this DefraSourceDiscoveryMode value) =>
        value switch
        {
            DefraSourceDiscoveryMode.RuntimePassive => "runtime_passive",
            _ => throw new ArgumentOutOfRangeException(nameof(value), value, "Unknown DEFRA source discovery mode."),
        };

    public static string ToWireName(this DefraSourceDiscoveryStatus value) =>
        value switch
        {
            DefraSourceDiscoveryStatus.Declared => "declared",
            DefraSourceDiscoveryStatus.Invalid => "invalid",
            _ => throw new ArgumentOutOfRangeException(nameof(value), value, "Unknown DEFRA source discovery status."),
        };

    public static string ToWireName(this IpccSourceDiscoveryMode value) =>
        value switch
        {
            IpccSourceDiscoveryMode.RuntimePassive => "runtime_passive",
            _ => throw new ArgumentOutOfRangeException(nameof(value), value, "Unknown IPCC source discovery mode."),
        };

    public static string ToWireName(this IpccSourceDiscoveryStatus value) =>
        value switch
        {
            IpccSourceDiscoveryStatus.Declared => "declared",
            IpccSourceDiscoveryStatus.Invalid => "invalid",
            _ => throw new ArgumentOutOfRangeException(nameof(value), value, "Unknown IPCC source discovery status."),
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

    public static string ToWireName(this DefraSourceDownloadExecutionStatus value) =>
        value switch
        {
            DefraSourceDownloadExecutionStatus.Blocked => "blocked",
            DefraSourceDownloadExecutionStatus.Downloaded => "downloaded",
            DefraSourceDownloadExecutionStatus.Failed => "failed",
            _ => throw new ArgumentOutOfRangeException(
                nameof(value),
                value,
                "Unknown DEFRA source download execution status."),
        };

    public static string ToWireName(this IpccSourceDownloadExecutionStatus value) =>
        value switch
        {
            IpccSourceDownloadExecutionStatus.Blocked => "blocked",
            IpccSourceDownloadExecutionStatus.Downloaded => "downloaded",
            IpccSourceDownloadExecutionStatus.Failed => "failed",
            IpccSourceDownloadExecutionStatus.AlreadyKnown => "already_known",
            _ => throw new ArgumentOutOfRangeException(
                nameof(value),
                value,
                "Unknown IPCC source download execution status."),
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

    public static string ToWireName(this DataQualityValidationSeverity value) =>
        value switch
        {
            DataQualityValidationSeverity.BlockingError => "blocking_error",
            DataQualityValidationSeverity.Warning => "warning",
            DataQualityValidationSeverity.Info => "info",
            _ => throw new ArgumentOutOfRangeException(
                nameof(value),
                value,
                "Unknown data quality validation severity."),
        };

    public static string ToWireName(this DataQualityValidationCheck value) =>
        value switch
        {
            DataQualityValidationCheck.RequiredField => "required_field",
            DataQualityValidationCheck.NumericValue => "numeric_value",
            DataQualityValidationCheck.Unit => "unit",
            DataQualityValidationCheck.DuplicateFactorIdentity => "duplicate_factor_identity",
            DataQualityValidationCheck.Provenance => "provenance",
            DataQualityValidationCheck.Structure => "structure",
            _ => throw new ArgumentOutOfRangeException(
                nameof(value),
                value,
                "Unknown data quality validation check."),
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

    public static bool TryParseDefraSourceDiscoveryModeWireName(
        string? wireName,
        out DefraSourceDiscoveryMode value)
    {
        value = wireName switch
        {
            "runtime_passive" => DefraSourceDiscoveryMode.RuntimePassive,
            _ => default,
        };

        return wireName is "runtime_passive";
    }

    public static bool TryParseDefraSourceDiscoveryStatusWireName(
        string? wireName,
        out DefraSourceDiscoveryStatus value)
    {
        value = wireName switch
        {
            "declared" => DefraSourceDiscoveryStatus.Declared,
            "invalid" => DefraSourceDiscoveryStatus.Invalid,
            _ => default,
        };

        return wireName is "declared" or "invalid";
    }

    public static bool TryParseIpccSourceDiscoveryModeWireName(
        string? wireName,
        out IpccSourceDiscoveryMode value)
    {
        value = wireName switch
        {
            "runtime_passive" => IpccSourceDiscoveryMode.RuntimePassive,
            _ => default,
        };

        return wireName is "runtime_passive";
    }

    public static bool TryParseIpccSourceDiscoveryStatusWireName(
        string? wireName,
        out IpccSourceDiscoveryStatus value)
    {
        value = wireName switch
        {
            "declared" => IpccSourceDiscoveryStatus.Declared,
            "invalid" => IpccSourceDiscoveryStatus.Invalid,
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

    public static bool TryParseDefraSourceDownloadExecutionStatusWireName(
        string? wireName,
        out DefraSourceDownloadExecutionStatus value)
    {
        value = wireName switch
        {
            "blocked" => DefraSourceDownloadExecutionStatus.Blocked,
            "downloaded" => DefraSourceDownloadExecutionStatus.Downloaded,
            "failed" => DefraSourceDownloadExecutionStatus.Failed,
            _ => default,
        };

        return wireName is "blocked" or "downloaded" or "failed";
    }

    public static bool TryParseIpccSourceDownloadExecutionStatusWireName(
        string? wireName,
        out IpccSourceDownloadExecutionStatus value)
    {
        value = wireName switch
        {
            "blocked" => IpccSourceDownloadExecutionStatus.Blocked,
            "downloaded" => IpccSourceDownloadExecutionStatus.Downloaded,
            "failed" => IpccSourceDownloadExecutionStatus.Failed,
            "already_known" => IpccSourceDownloadExecutionStatus.AlreadyKnown,
            _ => default,
        };

        return wireName is "blocked" or "downloaded" or "failed" or "already_known";
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

    public static bool TryParseDataQualityValidationSeverityWireName(
        string? wireName,
        out DataQualityValidationSeverity value)
    {
        value = wireName switch
        {
            "blocking_error" => DataQualityValidationSeverity.BlockingError,
            "warning" => DataQualityValidationSeverity.Warning,
            "info" => DataQualityValidationSeverity.Info,
            _ => default,
        };

        return wireName is "blocking_error" or "warning" or "info";
    }

    public static bool TryParseDataQualityValidationCheckWireName(
        string? wireName,
        out DataQualityValidationCheck value)
    {
        value = wireName switch
        {
            "required_field" => DataQualityValidationCheck.RequiredField,
            "numeric_value" => DataQualityValidationCheck.NumericValue,
            "unit" => DataQualityValidationCheck.Unit,
            "duplicate_factor_identity" => DataQualityValidationCheck.DuplicateFactorIdentity,
            "provenance" => DataQualityValidationCheck.Provenance,
            "structure" => DataQualityValidationCheck.Structure,
            _ => default,
        };

        return wireName is "required_field"
            or "numeric_value"
            or "unit"
            or "duplicate_factor_identity"
            or "provenance"
            or "structure";
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
