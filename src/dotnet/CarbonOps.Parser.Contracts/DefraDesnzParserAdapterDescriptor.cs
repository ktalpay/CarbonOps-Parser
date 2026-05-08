namespace CarbonOps.Parser.Contracts;

public sealed record DefraDesnzParserAdapterDescriptor : IParserAdapterDescriptor
{
    public string AdapterName { get; }

    public SourceFamily SourceFamily { get; }

    public ParserKey ParserKey { get; }

    public ParserAdapterCapability Capability { get; }

    public ParserAdapterReadiness Readiness { get; }

    public bool IsExecutionImplemented { get; }

    public IReadOnlyList<string> ReadinessNotes { get; }

    public DefraDesnzParserAdapterDescriptor(
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

    public static DefraDesnzParserAdapterDescriptor CreateDefault() =>
        new(
            "defra_desnz_parser_adapter",
            SourceFamily.DefraDesnz,
            ParserSelectionRegistry.GetParserKey(SourceFamily.DefraDesnz),
            new ParserAdapterCapability(
                [SourceFamily.DefraDesnz],
                [ParserSourceFormat.DiscoveryReference],
                ["application/x-carbonops-discovery-reference"],
                ["discovery"]),
            ParserAdapterReadiness.ExecutionNotImplemented,
            isExecutionImplemented: false,
            ["DEFRA/DESNZ parser adapter skeleton: parser execution is not implemented yet."]);
}
