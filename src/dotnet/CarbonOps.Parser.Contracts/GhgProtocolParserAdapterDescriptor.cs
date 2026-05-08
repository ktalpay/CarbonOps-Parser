namespace CarbonOps.Parser.Contracts;

public sealed record GhgProtocolParserAdapterDescriptor : IParserAdapterDescriptor
{
    public string AdapterName { get; }

    public SourceFamily SourceFamily { get; }

    public ParserKey ParserKey { get; }

    public ParserAdapterCapability Capability { get; }

    public ParserAdapterReadiness Readiness { get; }

    public bool IsExecutionImplemented { get; }

    public IReadOnlyList<string> ReadinessNotes { get; }

    public GhgProtocolParserAdapterDescriptor(
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

    public static GhgProtocolParserAdapterDescriptor CreateDefault() =>
        new(
            "ghg_protocol_parser_adapter",
            SourceFamily.GhgProtocol,
            ParserSelectionRegistry.GetParserKey(SourceFamily.GhgProtocol),
            new ParserAdapterCapability(
                [SourceFamily.GhgProtocol],
                [ParserSourceFormat.DiscoveryReference],
                ["application/x-carbonops-discovery-reference"],
                ["discovery"]),
            ParserAdapterReadiness.ExecutionNotImplemented,
            isExecutionImplemented: false,
            ["GHG Protocol parser adapter skeleton: parser execution is not implemented yet."]);
}
