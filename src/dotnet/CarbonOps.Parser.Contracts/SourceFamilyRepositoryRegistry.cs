namespace CarbonOps.Parser.Contracts;

public static class SourceFamilyRepositoryRegistry
{
    public static SourceFamilyRepositoryPersistResult CreatePersistResult(
        string providerName,
        IEnumerable<SourceFamilyMasterRecord?> masterRecords,
        IEnumerable<SourceFamilyDetailRecord?> detailRecords,
        IEnumerable<SourceFamilyRepositoryIssue>? issues = null)
    {
        var masterSnapshot = masterRecords.ToArray();
        var detailSnapshot = detailRecords.ToArray();
        var collectedIssues = ValidateInputs(providerName, masterSnapshot, detailSnapshot).Issues
            .Select(issue => new SourceFamilyRepositoryIssue(
                issue.Code,
                issue.Message,
                issue.FieldName,
                issue.Severity))
            .ToList();
        collectedIssues.AddRange(issues ?? []);

        var status = collectedIssues.Count == 0
            ? SourceFamilyRepositoryPersistStatus.Declared
            : SourceFamilyRepositoryPersistStatus.FailedValidation;

        return new SourceFamilyRepositoryPersistResult(
            providerName,
            status,
            status == SourceFamilyRepositoryPersistStatus.Declared ? masterSnapshot.Length : 0,
            status == SourceFamilyRepositoryPersistStatus.Declared ? detailSnapshot.Length : 0,
            collectedIssues);
    }

    public static SourceFamilyRepositoryValidationResult ValidateInputs(
        string providerName,
        IEnumerable<SourceFamilyMasterRecord?> masterRecords,
        IEnumerable<SourceFamilyDetailRecord?> detailRecords)
    {
        var errors = new List<SourceFamilyRepositoryIssue>();

        if (string.IsNullOrWhiteSpace(providerName))
        {
            errors.Add(new SourceFamilyRepositoryIssue(
                "SOURCE_FAMILY_REPOSITORY_MISSING_PROVIDER_NAME",
                "ProviderName must be a non-empty string.",
                "ProviderName"));
        }

        var masterSnapshot = masterRecords.ToArray();
        var detailSnapshot = detailRecords.ToArray();
        var masterKeys = new HashSet<(SourceFamily SourceFamily, string SourceFamilyMasterId)>();

        for (var index = 0; index < masterSnapshot.Length; index++)
        {
            var record = masterSnapshot[index];
            if (record is null)
            {
                errors.Add(new SourceFamilyRepositoryIssue(
                    "SOURCE_FAMILY_REPOSITORY_INVALID_MASTER_RECORD",
                    "MasterRecords must contain SourceFamilyMasterRecord instances.",
                    $"MasterRecords[{index}]"));
                continue;
            }

            ValidateSourceFamily(record.SourceFamily, $"MasterRecords[{index}].SourceFamily", errors);
            ValidateMasterRecord(record, index, errors);
            if (!string.IsNullOrWhiteSpace(record.SourceFamilyMasterId))
            {
                masterKeys.Add((record.SourceFamily, record.SourceFamilyMasterId));
            }
        }

        for (var index = 0; index < detailSnapshot.Length; index++)
        {
            var record = detailSnapshot[index];
            if (record is null)
            {
                errors.Add(new SourceFamilyRepositoryIssue(
                    "SOURCE_FAMILY_REPOSITORY_INVALID_DETAIL_RECORD",
                    "DetailRecords must contain SourceFamilyDetailRecord instances.",
                    $"DetailRecords[{index}]"));
                continue;
            }

            ValidateSourceFamily(record.SourceFamily, $"DetailRecords[{index}].SourceFamily", errors);
            ValidateDetailRecord(record, index, masterKeys, errors);
        }

        return new SourceFamilyRepositoryValidationResult(errors);
    }

    public static SourceFamilyRepositoryTableNames GetTableNames(SourceFamily sourceFamily)
    {
        ValidateSourceFamily(sourceFamily, nameof(sourceFamily), []);

        var familyPrefix = sourceFamily switch
        {
            SourceFamily.GhgProtocol => "ghg",
            SourceFamily.DefraDesnz => "defra",
            SourceFamily.IpccEfdb => "ipcc",
            _ => throw new ArgumentOutOfRangeException(
                nameof(sourceFamily),
                sourceFamily,
                "Unknown source family."),
        };

        return new SourceFamilyRepositoryTableNames(
            $"{familyPrefix}_emission_factor_masters",
            $"{familyPrefix}_emission_factor_details");
    }

    private static void ValidateMasterRecord(
        SourceFamilyMasterRecord record,
        int index,
        ICollection<SourceFamilyRepositoryIssue> errors)
    {
        AppendRequiredStringIssue(errors, record.SourceFamilyMasterId, $"MasterRecords[{index}].SourceFamilyMasterId");
        AppendRequiredStringIssue(errors, record.SourceDocumentId, $"MasterRecords[{index}].SourceDocumentId");
        AppendRequiredStringIssue(errors, record.MasterExternalKey, $"MasterRecords[{index}].MasterExternalKey");
        AppendRequiredStringIssue(errors, record.LifecycleStatus, $"MasterRecords[{index}].LifecycleStatus");
        AppendRequiredStringIssue(errors, record.RecordChecksumSha256, $"MasterRecords[{index}].RecordChecksumSha256");
        AppendRequiredStringIssue(errors, record.CreatedAt, $"MasterRecords[{index}].CreatedAt");
        AppendRequiredStringIssue(errors, record.UpdatedAt, $"MasterRecords[{index}].UpdatedAt");
    }

    private static void ValidateDetailRecord(
        SourceFamilyDetailRecord record,
        int index,
        ISet<(SourceFamily SourceFamily, string SourceFamilyMasterId)> masterKeys,
        ICollection<SourceFamilyRepositoryIssue> errors)
    {
        AppendRequiredStringIssue(errors, record.SourceFamilyDetailId, $"DetailRecords[{index}].SourceFamilyDetailId");
        AppendRequiredStringIssue(errors, record.SourceFamilyMasterId, $"DetailRecords[{index}].SourceFamilyMasterId");
        AppendRequiredStringIssue(errors, record.DetailExternalKey, $"DetailRecords[{index}].DetailExternalKey");
        AppendRequiredStringIssue(errors, record.FactorValue, $"DetailRecords[{index}].FactorValue");
        AppendRequiredStringIssue(errors, record.FactorUnit, $"DetailRecords[{index}].FactorUnit");
        AppendRequiredStringIssue(errors, record.LifecycleStatus, $"DetailRecords[{index}].LifecycleStatus");
        AppendRequiredStringIssue(errors, record.RecordChecksumSha256, $"DetailRecords[{index}].RecordChecksumSha256");
        AppendRequiredStringIssue(errors, record.CreatedAt, $"DetailRecords[{index}].CreatedAt");
        AppendRequiredStringIssue(errors, record.UpdatedAt, $"DetailRecords[{index}].UpdatedAt");

        if (!string.IsNullOrWhiteSpace(record.SourceFamilyMasterId) &&
            !masterKeys.Contains((record.SourceFamily, record.SourceFamilyMasterId)))
        {
            errors.Add(new SourceFamilyRepositoryIssue(
                "SOURCE_FAMILY_REPOSITORY_DETAIL_MASTER_NOT_DECLARED",
                "Detail record SourceFamilyMasterId must reference a declared master record for the same source family.",
                $"DetailRecords[{index}].SourceFamilyMasterId"));
        }
    }

    private static void ValidateSourceFamily(
        SourceFamily sourceFamily,
        string fieldName,
        ICollection<SourceFamilyRepositoryIssue> errors)
    {
        if (!Enum.IsDefined(sourceFamily))
        {
            errors.Add(new SourceFamilyRepositoryIssue(
                "SOURCE_FAMILY_REPOSITORY_INVALID_SOURCE_FAMILY",
                "SourceFamily must be a supported Phase 1 source family.",
                fieldName));
        }
    }

    private static void AppendRequiredStringIssue(
        ICollection<SourceFamilyRepositoryIssue> errors,
        string? value,
        string fieldName)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            errors.Add(new SourceFamilyRepositoryIssue(
                "SOURCE_FAMILY_REPOSITORY_MISSING_REQUIRED_FIELD",
                "Required fields must be non-empty strings.",
                fieldName));
        }
    }
}
