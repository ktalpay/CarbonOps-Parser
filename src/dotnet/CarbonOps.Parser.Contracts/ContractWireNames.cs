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
}
