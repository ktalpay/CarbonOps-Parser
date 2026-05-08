namespace CarbonOps.Parser.Contracts;

public sealed record ParserAdapterReadinessReportEntry
{
    public string SourceKey { get; }

    public SourceFamily SourceFamily { get; }

    public ParserKey ParserKey { get; }

    public string AdapterName { get; }

    public ParserAdapterReadiness Readiness { get; }

    public bool IsExecutionImplemented { get; }

    public ParserAdapterCapability Capability { get; }

    public IReadOnlyList<string> ReadinessNotes { get; }

    public ParserAdapterReadinessReportEntry(
        string sourceKey,
        SourceFamily sourceFamily,
        ParserKey parserKey,
        string adapterName,
        ParserAdapterReadiness readiness,
        bool isExecutionImplemented,
        ParserAdapterCapability capability,
        IEnumerable<string> readinessNotes)
    {
        SourceKey = sourceKey;
        SourceFamily = sourceFamily;
        ParserKey = parserKey;
        AdapterName = adapterName;
        Readiness = readiness;
        IsExecutionImplemented = isExecutionImplemented;
        Capability = capability;
        ReadinessNotes = Array.AsReadOnly(readinessNotes.ToArray());
    }

    internal static ParserAdapterReadinessReportEntry FromDescriptor(IParserAdapterDescriptor descriptor) =>
        new(
            descriptor.SourceFamily.ToWireName(),
            descriptor.SourceFamily,
            descriptor.ParserKey,
            descriptor.AdapterName,
            descriptor.Readiness,
            descriptor.IsExecutionImplemented,
            descriptor.Capability,
            descriptor.ReadinessNotes);
}
