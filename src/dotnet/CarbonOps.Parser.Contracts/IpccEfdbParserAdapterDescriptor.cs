namespace CarbonOps.Parser.Contracts;

public sealed record IpccEfdbParserAdapterDescriptor
{
    public string AdapterName { get; }

    public SourceFamily SourceFamily { get; }

    public ParserKey ParserKey { get; }

    public ParserAdapterCapability Capability { get; }

    public ParserAdapterReadiness Readiness { get; }

    public bool IsExecutionImplemented { get; }

    public IReadOnlyList<string> ReadinessNotes { get; }

    public IpccEfdbParserAdapterDescriptor(
        string adapterName,
        SourceFamily sourceFamily,
        ParserKey parserKey,
        ParserAdapterCapability capability,
        ParserAdapterReadiness readiness,
        bool isExecutionImplemented,
        IEnumerable<string> readinessNotes)
    {
        AdapterName = adapterName;
        SourceFamily = sourceFamily;
        ParserKey = parserKey;
        Capability = capability;
        Readiness = readiness;
        IsExecutionImplemented = isExecutionImplemented;
        ReadinessNotes = Array.AsReadOnly(readinessNotes.ToArray());
    }

    public static IpccEfdbParserAdapterDescriptor CreateDefault() =>
        new(
            "ipcc_efdb_parser_adapter",
            SourceFamily.IpccEfdb,
            ParserSelectionRegistry.GetParserKey(SourceFamily.IpccEfdb),
            new ParserAdapterCapability(
                [SourceFamily.IpccEfdb],
                [ParserSourceFormat.DiscoveryReference],
                ["application/x-carbonops-discovery-reference"],
                ["discovery"]),
            ParserAdapterReadiness.ExecutionNotImplemented,
            isExecutionImplemented: false,
            ["IPCC EFDB parser adapter skeleton: parser execution is not implemented yet."]);
}
