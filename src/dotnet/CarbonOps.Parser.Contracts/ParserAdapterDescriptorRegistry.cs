namespace CarbonOps.Parser.Contracts;

public static class ParserAdapterDescriptorRegistry
{
    public static IReadOnlyList<IParserAdapterDescriptor> Descriptors { get; } = Array.AsReadOnly(
        new IParserAdapterDescriptor[]
        {
            GhgProtocolParserAdapterDescriptor.CreateDefault(),
            DefraDesnzParserAdapterDescriptor.CreateDefault(),
            IpccEfdbParserAdapterDescriptor.CreateDefault(),
        });

    public static bool TryGetBySourceFamily(
        SourceFamily sourceFamily,
        out IParserAdapterDescriptor? descriptor)
    {
        descriptor = Descriptors.SingleOrDefault(candidate => candidate.SourceFamily == sourceFamily);

        return descriptor is not null;
    }

    public static bool TryGetBySourceKey(
        string? sourceKey,
        out IParserAdapterDescriptor? descriptor)
    {
        if (!ContractWireNames.TryParseSourceFamilyWireName(sourceKey, out var sourceFamily))
        {
            descriptor = null;

            return false;
        }

        return TryGetBySourceFamily(sourceFamily, out descriptor);
    }

    public static bool TryGetByParserKey(
        ParserKey parserKey,
        out IParserAdapterDescriptor? descriptor)
    {
        descriptor = Descriptors.SingleOrDefault(candidate => candidate.ParserKey == parserKey);

        return descriptor is not null;
    }
}
