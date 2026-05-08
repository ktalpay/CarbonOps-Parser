namespace CarbonOps.Parser.Contracts;

public sealed record ParserAdapterCapability
{
    public IReadOnlyList<SourceFamily> SupportedSourceFamilies { get; }

    public IReadOnlyList<ParserSourceFormat> SupportedSourceFormats { get; }

    public IReadOnlyList<string> SupportedContentTypes { get; }

    public IReadOnlyList<string> SupportedFormatHints { get; }

    public ParserAdapterCapability(
        IEnumerable<SourceFamily> supportedSourceFamilies,
        IEnumerable<ParserSourceFormat> supportedSourceFormats,
        IEnumerable<string> supportedContentTypes,
        IEnumerable<string> supportedFormatHints)
    {
        SupportedSourceFamilies = Array.AsReadOnly(supportedSourceFamilies.ToArray());
        SupportedSourceFormats = Array.AsReadOnly(supportedSourceFormats.ToArray());
        SupportedContentTypes = Array.AsReadOnly(supportedContentTypes.ToArray());
        SupportedFormatHints = Array.AsReadOnly(supportedFormatHints.ToArray());
    }
}
