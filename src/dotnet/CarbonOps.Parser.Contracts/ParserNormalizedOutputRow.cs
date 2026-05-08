namespace CarbonOps.Parser.Contracts;

public sealed record ParserNormalizedOutputRow
{
    public SourceFamily SourceFamily { get; }

    public string SourceKey { get; }

    public ParserKey ParserKey { get; }

    public string ArtifactReference { get; }

    public string RowIdentifier { get; }

    public int? SourceRowNumber { get; }

    public IReadOnlyList<ParserNormalizedField> Fields { get; }

    public IReadOnlyList<ParserRunIssue> Issues { get; }

    public int? ReportingYear { get; }

    public ParserNormalizedOutputRow(
        SourceFamily sourceFamily,
        string sourceKey,
        ParserKey parserKey,
        string artifactReference,
        string rowIdentifier,
        int? sourceRowNumber,
        IEnumerable<ParserNormalizedField> fields,
        IEnumerable<ParserRunIssue>? issues = null,
        int? reportingYear = null)
    {
        SourceFamily = sourceFamily;
        SourceKey = sourceKey;
        ParserKey = parserKey;
        ArtifactReference = artifactReference;
        RowIdentifier = rowIdentifier;
        SourceRowNumber = sourceRowNumber;
        Fields = Array.AsReadOnly(fields.ToArray());
        Issues = Array.AsReadOnly((issues ?? []).ToArray());
        ReportingYear = reportingYear;
    }

    internal static ParserNormalizedOutputRow FromArtifact(ParserInputArtifact artifact) =>
        new(
            artifact.SourceFamily,
            artifact.SourceKey,
            artifact.ParserKey,
            artifact.ArtifactReference,
            $"{artifact.SourceKey}_normalized_row_1",
            sourceRowNumber: 1,
            [
                new ParserNormalizedField("source_key", artifact.SourceKey),
                new ParserNormalizedField("artifact_reference", artifact.ArtifactReference),
                new ParserNormalizedField("parser_key", artifact.ParserKey.Value),
            ],
            reportingYear: artifact.ReportingYear);
}
