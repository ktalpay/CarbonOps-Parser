namespace CarbonOps.Parser.Contracts;

public sealed record SourceFamilyMasterRecord(
    SourceFamily SourceFamily,
    string SourceFamilyMasterId,
    string SourceDocumentId,
    string MasterExternalKey,
    string LifecycleStatus,
    string? EffectiveFrom,
    string? EffectiveTo,
    string RecordChecksumSha256,
    string CreatedAt,
    string UpdatedAt);
