namespace CarbonOps.Parser.Contracts;

public sealed record SourceFamilyDetailRecord(
    SourceFamily SourceFamily,
    string SourceFamilyDetailId,
    string SourceFamilyMasterId,
    string DetailExternalKey,
    string FactorValue,
    string FactorUnit,
    string LifecycleStatus,
    string RecordChecksumSha256,
    string CreatedAt,
    string UpdatedAt);
