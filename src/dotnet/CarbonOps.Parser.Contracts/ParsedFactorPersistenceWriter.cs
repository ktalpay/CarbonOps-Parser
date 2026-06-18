using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace CarbonOps.Parser.Contracts;

public static class ParsedFactorPersistenceWriter
{
    public const string DefaultTimestampLabel = "dry_run_timestamp_unavailable";

    public static ParsedFactorPersistenceCommand BuildCommand(
        ParserNormalizedOutputBatch parsedOutput,
        string? sourceDocumentId = null,
        string lifecycleStatus = "active",
        string timestampLabel = DefaultTimestampLabel)
    {
        if (parsedOutput is null)
        {
            return new ParsedFactorPersistenceCommand(
                [],
                [],
                issues:
                [
                    new ParsedFactorPersistenceIssue(
                        "PARSED_FACTOR_PERSISTENCE_INVALID_OUTPUT",
                        "parsed output must be a ParserNormalizedOutputBatch.",
                        "parsedOutput"),
                ]);
        }

        if (parsedOutput.RowCount == 0)
        {
            return new ParsedFactorPersistenceCommand(
                [],
                [],
                issues:
                [
                    new ParsedFactorPersistenceIssue(
                        "PARSED_FACTOR_PERSISTENCE_NO_RECORDS",
                        "parsed output must include records before persistence.",
                        "Rows",
                        "warning"),
                ]);
        }

        var issues = new List<ParsedFactorPersistenceIssue>();
        var masters = new Dictionary<(SourceFamily SourceFamily, string MasterId), SourceFamilyMasterRecord>();
        var details = new Dictionary<(SourceFamily SourceFamily, string MasterId, string DetailExternalKey), SourceFamilyDetailRecord>();
        var skippedDuplicateCount = 0;

        for (var index = 0; index < parsedOutput.Rows.Count; index++)
        {
            var row = parsedOutput.Rows[index];
            if (row is null)
            {
                issues.Add(new ParsedFactorPersistenceIssue(
                    "PARSED_FACTOR_PERSISTENCE_INVALID_NORMALIZED_ROW",
                    "ParserNormalizedOutputRow is required.",
                    $"Rows[{index}]"));
                continue;
            }

            AppendRowValidationIssues(row, index, issues);

            var mapped = MapRow(
                row,
                index,
                sourceDocumentId,
                lifecycleStatus,
                timestampLabel);
            issues.AddRange(mapped.Issues);

            if (mapped.MasterRecord is null || mapped.DetailRecord is null)
            {
                continue;
            }

            var masterKey = (mapped.MasterRecord.SourceFamily, mapped.MasterRecord.SourceFamilyMasterId);
            if (!masters.TryGetValue(masterKey, out var existingMaster))
            {
                masters.Add(masterKey, mapped.MasterRecord);
            }
            else if (existingMaster == mapped.MasterRecord)
            {
                skippedDuplicateCount++;
            }
            else
            {
                issues.Add(new ParsedFactorPersistenceIssue(
                    "PARSED_FACTOR_PERSISTENCE_DUPLICATE_MASTER_CONFLICT",
                    "duplicate source-family master identity maps to different record content.",
                    $"Rows[{index}].source_family_master_id"));
            }

            var detailKey = (
                mapped.DetailRecord.SourceFamily,
                mapped.DetailRecord.SourceFamilyMasterId,
                mapped.DetailRecord.DetailExternalKey);
            if (!details.TryGetValue(detailKey, out var existingDetail))
            {
                details.Add(detailKey, mapped.DetailRecord);
            }
            else if (existingDetail == mapped.DetailRecord)
            {
                skippedDuplicateCount++;
            }
            else
            {
                issues.Add(new ParsedFactorPersistenceIssue(
                    "PARSED_FACTOR_PERSISTENCE_DUPLICATE_DETAIL_CONFLICT",
                    "duplicate factor identity maps to different detail record content.",
                    $"Rows[{index}].detail_external_key"));
            }
        }

        var command = new ParsedFactorPersistenceCommand(
            masters.Values,
            details.Values,
            skippedDuplicateCount,
            issues);
        var repositoryValidation = SourceFamilyRepositoryRegistry.ValidateInputs(
            "parsed_factor_persistence_command",
            command.MasterRecords,
            command.DetailRecords);

        if (repositoryValidation.Issues.Count == 0)
        {
            return command;
        }

        return new ParsedFactorPersistenceCommand(
            command.MasterRecords,
            command.DetailRecords,
            command.SkippedDuplicateCount,
            command.Issues.Concat(repositoryValidation.Issues.Select(FromRepositoryIssue)));
    }

    public static ParsedFactorPersistenceWriterResult Persist(
        ParserNormalizedOutputBatch parsedOutput,
        ISourceFamilyRepository repository,
        string? sourceDocumentId = null,
        string lifecycleStatus = "active",
        string timestampLabel = DefaultTimestampLabel)
    {
        var command = BuildCommand(parsedOutput, sourceDocumentId, lifecycleStatus, timestampLabel);
        if (command.Issues.Count > 0)
        {
            var status = IsOnlyNoRecords(command.Issues)
                ? ParsedFactorPersistenceStatus.NoRecords
                : ParsedFactorPersistenceStatus.FailedValidation;

            return new ParsedFactorPersistenceWriterResult(
                repository.ProviderName,
                status,
                command.MasterRecords.Count,
                command.DetailRecords.Count,
                0,
                0,
                command.SkippedDuplicateCount,
                command.Issues,
                command);
        }

        var repositoryResult = repository.PersistSourceFamilyRecords(
            command.MasterRecords,
            command.DetailRecords);
        var repositoryIssues = repositoryResult.Issues.Select(FromRepositoryIssue).ToArray();
        var resultStatus = repositoryResult.Status == SourceFamilyRepositoryPersistStatus.Declared
            ? ParsedFactorPersistenceStatus.Declared
            : ParsedFactorPersistenceStatus.FailedValidation;

        return new ParsedFactorPersistenceWriterResult(
            repositoryResult.ProviderName,
            resultStatus,
            command.MasterRecords.Count,
            command.DetailRecords.Count,
            repositoryResult.PersistedMasterCount,
            repositoryResult.PersistedDetailCount,
            command.SkippedDuplicateCount,
            repositoryIssues,
            command);
    }

    private static MappedRow MapRow(
        ParserNormalizedOutputRow row,
        int index,
        string? explicitSourceDocumentId,
        string lifecycleStatus,
        string timestampLabel)
    {
        if (!Enum.IsDefined(row.SourceFamily))
        {
            return new MappedRow(
                null,
                null,
                [
                    new ParsedFactorPersistenceIssue(
                        "PARSED_FACTOR_PERSISTENCE_UNSUPPORTED_SOURCE_FAMILY",
                        "source family must be GHG Protocol, DEFRA/DESNZ, or IPCC EFDB.",
                        $"Rows[{index}].SourceFamily"),
                ]);
        }

        var fields = row.Fields
            .GroupBy(field => field.Key, StringComparer.Ordinal)
            .ToDictionary(group => group.Key, group => group.First().Value, StringComparer.Ordinal);
        var issues = new List<ParsedFactorPersistenceIssue>();
        var resolvedSourceDocumentId = ResolveSourceDocumentId(row, fields, explicitSourceDocumentId);
        var factorValue = TextOrNull(Field(fields, "factor_value", "value"));
        var factorUnit = TextOrNull(Field(fields, "factor_unit", "unit"));

        var requiredValues = new Dictionary<string, string?>
        {
            ["source_document_id"] = resolvedSourceDocumentId,
            ["factor_value"] = factorValue,
            ["factor_unit"] = factorUnit,
        };
        foreach (var pair in requiredValues)
        {
            if (pair.Value is null)
            {
                issues.Add(new ParsedFactorPersistenceIssue(
                    "PARSED_FACTOR_PERSISTENCE_MISSING_REQUIRED_FIELD",
                    "parsed factor persistence requires a non-empty value.",
                    $"Rows[{index}].{pair.Key}"));
            }
        }

        if (issues.Count > 0)
        {
            return new MappedRow(null, null, issues);
        }

        var masterExternalKey = TextOrNull(Field(fields, "master_external_key")) ?? DefaultMasterExternalKey(row, fields);
        var detailExternalKey = TextOrNull(Field(fields, "detail_external_key")) ?? DefaultDetailExternalKey(row, fields);
        var familyPrefix = row.SourceFamily switch
        {
            SourceFamily.GhgProtocol => "ghg",
            SourceFamily.DefraDesnz => "defra",
            SourceFamily.IpccEfdb => "ipcc",
            _ => row.SourceFamily.ToWireName(),
        };
        var masterId = TextOrNull(Field(fields, "source_family_master_id"))
            ?? $"{familyPrefix}_master_{StableDigest(familyPrefix, masterExternalKey)[..16]}";
        var detailId = TextOrNull(Field(fields, "source_family_detail_id"))
            ?? $"{familyPrefix}_detail_{StableDigest(familyPrefix, masterId, detailExternalKey)[..16]}";

        var masterRecord = new SourceFamilyMasterRecord(
            row.SourceFamily,
            masterId,
            resolvedSourceDocumentId!,
            masterExternalKey,
            lifecycleStatus,
            TextOrNull(Field(fields, "effective_from")),
            TextOrNull(Field(fields, "effective_to")),
            StableDigest("master", familyPrefix, resolvedSourceDocumentId!, masterExternalKey, lifecycleStatus),
            timestampLabel,
            timestampLabel);
        var detailRecord = new SourceFamilyDetailRecord(
            row.SourceFamily,
            detailId,
            masterId,
            detailExternalKey,
            factorValue!,
            factorUnit!,
            lifecycleStatus,
            StableDigest("detail", familyPrefix, masterId, detailExternalKey, factorValue!, factorUnit!),
            timestampLabel,
            timestampLabel);

        return new MappedRow(masterRecord, detailRecord, issues);
    }

    private static void AppendRowValidationIssues(
        ParserNormalizedOutputRow row,
        int index,
        ICollection<ParsedFactorPersistenceIssue> issues)
    {
        foreach (var error in row.Validate().Errors)
        {
            issues.Add(new ParsedFactorPersistenceIssue(
                "PARSED_FACTOR_PERSISTENCE_INVALID_NORMALIZED_ROW",
                error,
                $"Rows[{index}]"));
        }
    }

    private static string? ResolveSourceDocumentId(
        ParserNormalizedOutputRow row,
        IReadOnlyDictionary<string, string?> fields,
        string? explicitSourceDocumentId)
    {
        var explicitValue = TextOrNull(explicitSourceDocumentId);
        if (explicitValue is not null)
        {
            return explicitValue;
        }

        var fieldValue = TextOrNull(Field(fields, "source_document_id"));
        if (fieldValue is not null)
        {
            return fieldValue;
        }

        var artifactReference = TextOrNull(Field(fields, "provenance_artifact_reference", "artifact_reference"))
            ?? TextOrNull(row.ArtifactReference);
        var checksum = TextOrNull(Field(fields, "provenance_checksum_value", "source_checksum_sha256"));
        if (artifactReference is null && checksum is null)
        {
            return null;
        }

        return $"source_document_{StableDigest(row.SourceFamily.ToWireName(), row.SourceKey, artifactReference, checksum)[..24]}";
    }

    private static string DefaultMasterExternalKey(
        ParserNormalizedOutputRow row,
        IReadOnlyDictionary<string, string?> fields)
    {
        var sourceYear = TextOrNull(Field(fields, "source_year")) ?? "unknown-year";
        var sourceVersion = TextOrNull(Field(fields, "source_version")) ?? "unknown-version";
        var factorId = TextOrNull(Field(fields, "factor_id")) ?? row.RowIdentifier;

        return $"{sourceYear}:{sourceVersion}:{factorId}";
    }

    private static string DefaultDetailExternalKey(
        ParserNormalizedOutputRow row,
        IReadOnlyDictionary<string, string?> fields)
    {
        var factorId = TextOrNull(Field(fields, "factor_id")) ?? row.RowIdentifier;
        var factorUnit = TextOrNull(Field(fields, "factor_unit", "unit")) ?? "unknown-unit";
        var gas = TextOrNull(Field(fields, "greenhouse_gas", "gas"));

        return gas is null
            ? $"{factorId}:{factorUnit}"
            : $"{factorId}:{factorUnit}:{gas}";
    }

    private static string? Field(IReadOnlyDictionary<string, string?> fields, params string[] names)
    {
        foreach (var name in names)
        {
            if (fields.TryGetValue(name, out var value))
            {
                return value;
            }
        }

        return null;
    }

    private static string? TextOrNull(string? value)
    {
        var text = value?.Trim();

        return string.IsNullOrEmpty(text) ? null : text;
    }

    private static string StableDigest(params string?[] values)
    {
        var payload = JsonSerializer.Serialize(values);

        return Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(payload))).ToLowerInvariant();
    }

    private static ParsedFactorPersistenceIssue FromRepositoryIssue(SourceFamilyRepositoryIssue issue) =>
        new(issue.Code, issue.Message, issue.FieldName, issue.Severity);

    private static bool IsOnlyNoRecords(IReadOnlyList<ParsedFactorPersistenceIssue> issues) =>
        issues.Count == 1 && issues[0].Code == "PARSED_FACTOR_PERSISTENCE_NO_RECORDS";

    private sealed record MappedRow(
        SourceFamilyMasterRecord? MasterRecord,
        SourceFamilyDetailRecord? DetailRecord,
        IEnumerable<ParsedFactorPersistenceIssue> Issues);
}
