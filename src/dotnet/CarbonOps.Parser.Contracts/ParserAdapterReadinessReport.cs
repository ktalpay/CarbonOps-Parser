namespace CarbonOps.Parser.Contracts;

public sealed record ParserAdapterReadinessReport
{
    public IReadOnlyList<ParserAdapterReadinessReportEntry> Adapters { get; }

    public int AdapterCount => Adapters.Count;

    public ParserAdapterReadinessReport(IEnumerable<ParserAdapterReadinessReportEntry> adapters)
    {
        Adapters = Array.AsReadOnly(adapters.ToArray());
    }

    public static ParserAdapterReadinessReport CreateDefault() =>
        FromDescriptors(ParserAdapterDescriptorRegistry.Descriptors);

    private static ParserAdapterReadinessReport FromDescriptors(IEnumerable<IParserAdapterDescriptor> descriptors) =>
        new(descriptors.Select(ParserAdapterReadinessReportEntry.FromDescriptor));
}
