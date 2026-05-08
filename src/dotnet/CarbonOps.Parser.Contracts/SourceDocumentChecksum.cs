namespace CarbonOps.Parser.Contracts;

public sealed record SourceDocumentChecksum(
    string Algorithm,
    string Value,
    bool IsDryRunPlaceholder);
