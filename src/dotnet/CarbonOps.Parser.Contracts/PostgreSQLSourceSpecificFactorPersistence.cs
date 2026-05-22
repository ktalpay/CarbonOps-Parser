using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Npgsql;

namespace CarbonOps.Parser.Contracts;

public enum PostgreSQLSourceSpecificFactorPersistenceStatus
{
    Inserted = 0,
    NoRecords = 1,
    FailedValidation = 2,
    FailedDatabase = 3,
}

public sealed record PostgreSQLSourceSpecificFactorPersistenceIssue(
    string Code,
    string Message,
    string FieldName,
    string Severity = "error");

public sealed record PostgreSQLSourceSpecificFactorPersistenceCounts(
    int MasterInserted,
    int MasterSkippedDuplicate,
    int DetailInserted,
    int DetailSkippedDuplicate,
    int ValidationFailed);

public sealed record PostgreSQLSourceSpecificFactorPersistenceResult(
    string ProviderName,
    PostgreSQLSourceSpecificFactorPersistenceStatus Status,
    PostgreSQLSourceSpecificFactorPersistenceCounts Counts,
    IReadOnlyList<PostgreSQLSourceSpecificFactorPersistenceIssue> Issues)
{
    public int MasterInserted => Counts.MasterInserted;

    public int MasterSkippedDuplicate => Counts.MasterSkippedDuplicate;

    public int DetailInserted => Counts.DetailInserted;

    public int DetailSkippedDuplicate => Counts.DetailSkippedDuplicate;

    public int ValidationFailed => Counts.ValidationFailed;
}

public sealed record PostgreSQLSourceSpecificMasterRecord(
    SourceFamily SourceFamily,
    Guid SourceFamilyMasterId,
    int SourceYear,
    string SourceVersion,
    string? SourceRelease,
    Guid SourceDocumentId,
    Guid? IngestionRunId,
    string? RunId,
    string MasterExternalKey,
    string Status,
    string? ArtifactReference,
    string? ArtifactChecksumSha256,
    string? ArchiveReference,
    string? ArchiveChecksumSha256,
    string? EffectiveFrom,
    string? EffectiveTo,
    string RecordChecksumSha256,
    IReadOnlyDictionary<string, object?> Metadata);

public sealed record PostgreSQLSourceSpecificDetailRecord(
    SourceFamily SourceFamily,
    Guid SourceFamilyDetailId,
    Guid SourceFamilyMasterId,
    string DetailExternalKey,
    int? SourceRowNumber,
    string? FactorId,
    string? FactorName,
    decimal FactorValue,
    string FactorUnit,
    string Status,
    string RecordChecksumSha256,
    IReadOnlyDictionary<string, object?> RawFields,
    IReadOnlyDictionary<string, object?> NormalizedFields);

public sealed record PostgreSQLSourceSpecificFactorPersistenceBatch(
    SourceFamily SourceFamily,
    int SourceYear,
    IReadOnlyList<PostgreSQLSourceSpecificMasterRecord> MasterRecords,
    IReadOnlyList<PostgreSQLSourceSpecificDetailRecord> DetailRecords);

public interface IPostgreSQLSourceSpecificFactorPersistenceSession
{
    string ProviderName { get; }

    Task<PostgreSQLSourceSpecificFactorPersistenceCounts> PersistSourceFamilyYearAsync(
        PostgreSQLSourceSpecificFactorPersistenceBatch batch,
        CancellationToken cancellationToken = default);
}

public sealed class PostgreSQLSourceSpecificFactorPersistenceRepository
{
    private readonly IPostgreSQLSourceSpecificFactorPersistenceSession _session;

    public PostgreSQLSourceSpecificFactorPersistenceRepository(
        IPostgreSQLSourceSpecificFactorPersistenceSession session)
    {
        _session = session ?? throw new ArgumentNullException(nameof(session));
    }

    public async Task<PostgreSQLSourceSpecificFactorPersistenceResult> PersistAsync(
        ParserNormalizedOutputBatch parsedOutput,
        CancellationToken cancellationToken = default)
    {
        var mapped = PostgreSQLSourceSpecificFactorPersistenceMapper.Map(parsedOutput);
        if (mapped.Issues.Count > 0)
        {
            var noRecords = mapped.Issues.Count == 1 &&
                mapped.Issues[0].Code == "POSTGRESQL_SOURCE_SPECIFIC_NO_RECORDS";
            return new PostgreSQLSourceSpecificFactorPersistenceResult(
                _session.ProviderName,
                noRecords
                    ? PostgreSQLSourceSpecificFactorPersistenceStatus.NoRecords
                    : PostgreSQLSourceSpecificFactorPersistenceStatus.FailedValidation,
                new PostgreSQLSourceSpecificFactorPersistenceCounts(0, 0, 0, 0, mapped.Issues.Count),
                mapped.Issues);
        }

        var total = new PostgreSQLSourceSpecificFactorPersistenceCounts(0, 0, 0, 0, 0);
        foreach (var batch in mapped.Batches)
        {
            try
            {
                var counts = await _session.PersistSourceFamilyYearAsync(batch, cancellationToken)
                    .ConfigureAwait(false);
                total = total with
                {
                    MasterInserted = total.MasterInserted + counts.MasterInserted,
                    MasterSkippedDuplicate = total.MasterSkippedDuplicate + counts.MasterSkippedDuplicate,
                    DetailInserted = total.DetailInserted + counts.DetailInserted,
                    DetailSkippedDuplicate = total.DetailSkippedDuplicate + counts.DetailSkippedDuplicate,
                    ValidationFailed = total.ValidationFailed + counts.ValidationFailed,
                };
            }
            catch (Exception ex) when (ex is not OperationCanceledException)
            {
                return new PostgreSQLSourceSpecificFactorPersistenceResult(
                    _session.ProviderName,
                    PostgreSQLSourceSpecificFactorPersistenceStatus.FailedDatabase,
                    total,
                    [
                        new(
                            "POSTGRESQL_SOURCE_SPECIFIC_DATABASE_ERROR",
                            RedactSensitiveText(ex.Message),
                            "database"),
                    ]);
            }
        }

        return new PostgreSQLSourceSpecificFactorPersistenceResult(
            _session.ProviderName,
            PostgreSQLSourceSpecificFactorPersistenceStatus.Inserted,
            total,
            []);
    }
    private static string RedactSensitiveText(string value)
    {
        var withoutUriSecret = System.Text.RegularExpressions.Regex.Replace(
            value,
            @"postgresql://[^@\s]+@",
            "postgresql://***@",
            System.Text.RegularExpressions.RegexOptions.IgnoreCase);
        return System.Text.RegularExpressions.Regex.Replace(
            withoutUriSecret,
            @"password=([^;\s]+)",
            "password=***",
            System.Text.RegularExpressions.RegexOptions.IgnoreCase);
    }
}

public static class PostgreSQLSourceSpecificFactorPersistenceMapper
{
    public static PostgreSQLSourceSpecificFactorPersistenceMapResult Map(ParserNormalizedOutputBatch? parsedOutput)
    {
        if (parsedOutput is null)
        {
            return new PostgreSQLSourceSpecificFactorPersistenceMapResult(
                [],
                [
                    new(
                        "POSTGRESQL_SOURCE_SPECIFIC_INVALID_OUTPUT",
                        "parsed output must be a ParserNormalizedOutputBatch.",
                        "parsedOutput"),
                ]);
        }

        if (parsedOutput.RowCount == 0)
        {
            return new PostgreSQLSourceSpecificFactorPersistenceMapResult(
                [],
                [
                    new(
                        "POSTGRESQL_SOURCE_SPECIFIC_NO_RECORDS",
                        "parsed output must include records before source-specific persistence.",
                        "Rows",
                        "warning"),
                ]);
        }

        var issues = new List<PostgreSQLSourceSpecificFactorPersistenceIssue>();
        var masters = new Dictionary<(SourceFamily SourceFamily, int SourceYear, string SourceVersion, string MasterKey),
            PostgreSQLSourceSpecificMasterRecord>();
        var details = new Dictionary<(SourceFamily SourceFamily, Guid MasterId, string DetailKey),
            PostgreSQLSourceSpecificDetailRecord>();

        for (var index = 0; index < parsedOutput.Rows.Count; index++)
        {
            var mapped = MapRow(parsedOutput.Rows[index], index);
            issues.AddRange(mapped.Issues);
            if (mapped.MasterRecord is null || mapped.DetailRecord is null)
            {
                continue;
            }

            var masterKey = (
                mapped.MasterRecord.SourceFamily,
                mapped.MasterRecord.SourceYear,
                mapped.MasterRecord.SourceVersion,
                mapped.MasterRecord.MasterExternalKey);
            if (!masters.TryAdd(masterKey, mapped.MasterRecord) &&
                masters[masterKey] != mapped.MasterRecord)
            {
                issues.Add(new(
                    "POSTGRESQL_SOURCE_SPECIFIC_DUPLICATE_MASTER_CONFLICT",
                    "duplicate source-specific master identity maps to different record content.",
                    $"Rows[{index}].master_external_key"));
            }

            var detailKey = (
                mapped.DetailRecord.SourceFamily,
                mapped.DetailRecord.SourceFamilyMasterId,
                mapped.DetailRecord.DetailExternalKey);
            if (!details.TryAdd(detailKey, mapped.DetailRecord) &&
                details[detailKey] != mapped.DetailRecord)
            {
                issues.Add(new(
                    "POSTGRESQL_SOURCE_SPECIFIC_DUPLICATE_DETAIL_CONFLICT",
                    "duplicate source-specific detail identity maps to different record content.",
                    $"Rows[{index}].detail_external_key"));
            }
        }

        if (issues.Count > 0)
        {
            return new PostgreSQLSourceSpecificFactorPersistenceMapResult([], issues);
        }

        var batches = masters.Values
            .GroupBy(master => (master.SourceFamily, master.SourceYear))
            .Select(group =>
            {
                var masterIds = group.Select(master => master.SourceFamilyMasterId).ToHashSet();
                var batchDetails = details.Values
                    .Where(detail => detail.SourceFamily == group.Key.SourceFamily &&
                        masterIds.Contains(detail.SourceFamilyMasterId))
                    .OrderBy(detail => detail.DetailExternalKey, StringComparer.Ordinal)
                    .ToArray();
                return new PostgreSQLSourceSpecificFactorPersistenceBatch(
                    group.Key.SourceFamily,
                    group.Key.SourceYear,
                    Array.AsReadOnly(group.OrderBy(master => master.MasterExternalKey, StringComparer.Ordinal).ToArray()),
                    Array.AsReadOnly(batchDetails));
            })
            .OrderBy(batch => batch.SourceFamily.ToWireName(), StringComparer.Ordinal)
            .ThenBy(batch => batch.SourceYear)
            .ToArray();

        return new PostgreSQLSourceSpecificFactorPersistenceMapResult(Array.AsReadOnly(batches), []);
    }

    private static MappedRow MapRow(ParserNormalizedOutputRow? row, int index)
    {
        if (row is null)
        {
            return new MappedRow(
                null,
                null,
                [new("POSTGRESQL_SOURCE_SPECIFIC_INVALID_ROW", "ParserNormalizedOutputRow is required.", $"Rows[{index}]")]);
        }

        var fields = row.Fields
            .GroupBy(field => field.Key, StringComparer.Ordinal)
            .ToDictionary(group => group.Key, group => group.First().Value, StringComparer.Ordinal);
        var issues = new List<PostgreSQLSourceSpecificFactorPersistenceIssue>();
        foreach (var error in row.Validate().Errors)
        {
            issues.Add(new(
                "POSTGRESQL_SOURCE_SPECIFIC_INVALID_ROW",
                error,
                $"Rows[{index}]"));
        }

        var sourceYear = TryParsePositiveInt(TextOrNull(Field(fields, "source_year")) ?? row.ReportingYear?.ToString(CultureInfo.InvariantCulture));
        var sourceVersion = TextOrNull(Field(fields, "source_version")) ?? "version-unavailable";
        var factorValueText = TextOrNull(Field(fields, "factor_value", "value"));
        var factorUnit = TextOrNull(Field(fields, "factor_unit", "unit"));
        var factorValue = TryParseDecimal(factorValueText);

        if (sourceYear is null)
        {
            issues.Add(new("POSTGRESQL_SOURCE_SPECIFIC_MISSING_SOURCE_YEAR", "source_year must be a positive integer.", $"Rows[{index}].source_year"));
        }

        if (factorValue is null)
        {
            issues.Add(new("POSTGRESQL_SOURCE_SPECIFIC_INVALID_FACTOR_VALUE", "factor_value must be a decimal value.", $"Rows[{index}].factor_value"));
        }

        if (factorUnit is null)
        {
            issues.Add(new("POSTGRESQL_SOURCE_SPECIFIC_MISSING_FACTOR_UNIT", "factor_unit must be a non-empty value.", $"Rows[{index}].factor_unit"));
        }

        if (issues.Count > 0)
        {
            return new MappedRow(null, null, issues);
        }

        var resolvedSourceYear = sourceYear.GetValueOrDefault();
        var resolvedFactorValue = factorValue.GetValueOrDefault();
        var masterExternalKey = TextOrNull(Field(fields, "master_external_key")) ??
            $"{resolvedSourceYear}:{sourceVersion}:{TextOrNull(Field(fields, "factor_id")) ?? row.RowIdentifier}";
        var detailExternalKey = TextOrNull(Field(fields, "detail_external_key")) ??
            $"{TextOrNull(Field(fields, "factor_id")) ?? row.RowIdentifier}:{factorUnit}";
        var sourceDocumentKey = TextOrNull(Field(fields, "source_document_id")) ??
            StableDigest("source_document", row.SourceFamily.ToWireName(), row.SourceKey, row.ArtifactReference, Field(fields, "provenance_checksum_value"));
        var runId = TextOrNull(Field(fields, "run_id"));
        var artifactReference = TextOrNull(Field(fields, "provenance_artifact_reference", "artifact_reference")) ??
            TextOrNull(row.ArtifactReference);
        var artifactChecksum = TextOrNull(Field(fields, "provenance_checksum_value", "source_checksum_sha256"));
        var normalizedFields = NormalizeFields(fields);
        var masterMetadata = new Dictionary<string, object?>(StringComparer.Ordinal)
        {
            ["source_key"] = row.SourceKey,
            ["parser_key"] = row.ParserKey.Value,
            ["row_identifier"] = row.RowIdentifier,
            ["source_release"] = TextOrNull(Field(fields, "source_release")),
            ["fields"] = normalizedFields,
        };

        var sourceFamilyMasterId = StableUuid(
            "master",
            row.SourceFamily.ToWireName(),
            resolvedSourceYear.ToString(CultureInfo.InvariantCulture),
            sourceVersion,
            masterExternalKey);
        var sourceFamilyDetailId = StableUuid(
            "detail",
            row.SourceFamily.ToWireName(),
            sourceFamilyMasterId.ToString("D"),
            detailExternalKey);
        var master = new PostgreSQLSourceSpecificMasterRecord(
            row.SourceFamily,
            sourceFamilyMasterId,
            resolvedSourceYear,
            sourceVersion,
            TextOrNull(Field(fields, "source_release")),
            StableUuid("source_document", row.SourceFamily.ToWireName(), sourceDocumentKey),
            StableUuid("ingestion_run", row.SourceFamily.ToWireName(), runId ?? $"{resolvedSourceYear}:{sourceVersion}"),
            runId,
            masterExternalKey,
            TextOrNull(Field(fields, "status", "validation_status")) ?? "active",
            artifactReference,
            artifactChecksum,
            TextOrNull(Field(fields, "archive_reference")),
            TextOrNull(Field(fields, "archive_checksum_sha256")),
            TextOrNull(Field(fields, "effective_from")),
            TextOrNull(Field(fields, "effective_to")),
            StableDigest("master", row.SourceFamily.ToWireName(), resolvedSourceYear.ToString(CultureInfo.InvariantCulture), sourceVersion, masterExternalKey),
            masterMetadata);
        var detail = new PostgreSQLSourceSpecificDetailRecord(
            row.SourceFamily,
            sourceFamilyDetailId,
            sourceFamilyMasterId,
            detailExternalKey,
            row.SourceRowNumber ?? TryParsePositiveInt(TextOrNull(Field(fields, "provenance_row_number"))),
            TextOrNull(Field(fields, "factor_id")),
            TextOrNull(Field(fields, "factor_name")),
            resolvedFactorValue,
            factorUnit!,
            TextOrNull(Field(fields, "status", "validation_status")) ?? "active",
            StableDigest("detail", row.SourceFamily.ToWireName(), sourceFamilyMasterId.ToString("D"), detailExternalKey, factorValueText, factorUnit),
            normalizedFields,
            normalizedFields);

        return new MappedRow(master, detail, []);
    }

    private static IReadOnlyDictionary<string, object?> NormalizeFields(IReadOnlyDictionary<string, string?> fields) =>
        fields
            .OrderBy(pair => pair.Key, StringComparer.Ordinal)
            .ToDictionary(pair => pair.Key, pair => (object?)pair.Value, StringComparer.Ordinal);

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

    private static int? TryParsePositiveInt(string? value) =>
        int.TryParse(value, NumberStyles.None, CultureInfo.InvariantCulture, out var parsed) && parsed > 0
            ? parsed
            : null;

    private static decimal? TryParseDecimal(string? value) =>
        decimal.TryParse(value, NumberStyles.Number, CultureInfo.InvariantCulture, out var parsed)
            ? parsed
            : null;

    private static Guid StableUuid(params string?[] values)
    {
        var namespaceBytes = Guid.Parse("6ba7b811-9dad-11d1-80b4-00c04fd430c8").ToByteArray();
        SwapGuidByteOrder(namespaceBytes);
        var nameBytes = Encoding.UTF8.GetBytes(JsonSerializer.Serialize(values));
        var payload = namespaceBytes.Concat(nameBytes).ToArray();
        var hash = SHA1.HashData(payload);
        var guidBytes = hash[..16];
        guidBytes[6] = (byte)((guidBytes[6] & 0x0f) | 0x50);
        guidBytes[8] = (byte)((guidBytes[8] & 0x3f) | 0x80);
        SwapGuidByteOrder(guidBytes);
        return new Guid(guidBytes);
    }

    private static void SwapGuidByteOrder(byte[] bytes)
    {
        Array.Reverse(bytes, 0, 4);
        Array.Reverse(bytes, 4, 2);
        Array.Reverse(bytes, 6, 2);
    }

    private static string StableDigest(params string?[] values) =>
        Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(JsonSerializer.Serialize(values)))).ToLowerInvariant();

    private sealed record MappedRow(
        PostgreSQLSourceSpecificMasterRecord? MasterRecord,
        PostgreSQLSourceSpecificDetailRecord? DetailRecord,
        IEnumerable<PostgreSQLSourceSpecificFactorPersistenceIssue> Issues);
}

public sealed record PostgreSQLSourceSpecificFactorPersistenceMapResult(
    IReadOnlyList<PostgreSQLSourceSpecificFactorPersistenceBatch> Batches,
    IReadOnlyList<PostgreSQLSourceSpecificFactorPersistenceIssue> Issues);

public sealed record PostgreSQLSourceSpecificFactorPersistenceSqlStep(
    string Name,
    string CommandText);

public sealed record PostgreSQLSourceSpecificFactorPersistenceTransactionBoundary(
    bool OpensTransaction,
    bool CommitsTransaction,
    bool RollsBackOnFailure);

public sealed class NpgsqlSourceSpecificFactorPersistenceSession : IPostgreSQLSourceSpecificFactorPersistenceSession
{
    private readonly NpgsqlDataSource _dataSource;

    public NpgsqlSourceSpecificFactorPersistenceSession(NpgsqlDataSource dataSource)
    {
        _dataSource = dataSource;
    }

    public string ProviderName => "postgresql";

    public async Task<PostgreSQLSourceSpecificFactorPersistenceCounts> PersistSourceFamilyYearAsync(
        PostgreSQLSourceSpecificFactorPersistenceBatch batch,
        CancellationToken cancellationToken = default)
    {
        var sqlFlow = RenderSourceFamilyYearPersistenceSqlFlow(batch.SourceFamily);
        var masterInsertSql = sqlFlow.Single(step => step.Name == "master_insert").CommandText;
        var detailInsertSql = sqlFlow.Single(step => step.Name == "detail_insert").CommandText;
        var yearStateInsertSql = sqlFlow.Single(step => step.Name == "year_state_insert").CommandText;

        await using var connection = await _dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
        await using var transaction = await connection.BeginTransactionAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            var masterInserted = 0;
            foreach (var master in batch.MasterRecords)
            {
                await EnsureIngestionRunAsync(connection, transaction, master, cancellationToken).ConfigureAwait(false);
                await EnsureSourceDocumentAsync(connection, transaction, master, cancellationToken).ConfigureAwait(false);
                masterInserted += await ExecuteInsertAsync(
                    connection,
                    transaction,
                    masterInsertSql,
                    MasterParameters(master),
                    cancellationToken).ConfigureAwait(false);
            }

            var detailInserted = 0;
            foreach (var detail in batch.DetailRecords)
            {
                detailInserted += await ExecuteInsertAsync(
                    connection,
                    transaction,
                    detailInsertSql,
                    DetailParameters(detail),
                    cancellationToken).ConfigureAwait(false);
            }

            await RecordSuccessfulYearAsync(
                connection,
                transaction,
                batch,
                yearStateInsertSql,
                cancellationToken).ConfigureAwait(false);
            await transaction.CommitAsync(cancellationToken).ConfigureAwait(false);

            return new PostgreSQLSourceSpecificFactorPersistenceCounts(
                masterInserted,
                batch.MasterRecords.Count - masterInserted,
                detailInserted,
                batch.DetailRecords.Count - detailInserted,
                0);
        }
        catch
        {
            await transaction.RollbackAsync(cancellationToken).ConfigureAwait(false);
            throw;
        }
    }

    public static string RenderMasterInsertSql(SourceFamily sourceFamily)
    {
        var table = SourceFamilyRepositoryRegistry.GetTableNames(sourceFamily).MasterTableName;
        var masterId = MasterIdColumn(sourceFamily);
        return $$"""
            INSERT INTO {{table}} (
                {{masterId}},
                source_family,
                source_year,
                source_version,
                source_release,
                source_document_id,
                ingestion_run_id,
                run_id,
                master_external_key,
                status,
                artifact_reference,
                artifact_checksum_sha256,
                archive_reference,
                archive_checksum_sha256,
                effective_from,
                effective_to,
                record_checksum_sha256,
                metadata,
                created_at,
                updated_at
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                $11, $12, $13, $14, $15, $16, $17, $18::jsonb, NOW(), NOW()
            )
            ON CONFLICT (source_family, source_year, source_version, master_external_key)
            DO NOTHING
            RETURNING {{masterId}}
            """;
    }

    public static string RenderDetailInsertSql(SourceFamily sourceFamily)
    {
        var table = SourceFamilyRepositoryRegistry.GetTableNames(sourceFamily).DetailTableName;
        var masterId = MasterIdColumn(sourceFamily);
        var detailId = DetailIdColumn(sourceFamily);
        return $$"""
            INSERT INTO {{table}} (
                {{detailId}},
                {{masterId}},
                detail_external_key,
                source_row_number,
                factor_id,
                factor_name,
                factor_value,
                factor_unit,
                status,
                record_checksum_sha256,
                raw_fields,
                normalized_fields,
                created_at,
                updated_at
            )
            VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                $11::jsonb, $12::jsonb, NOW(), NOW()
            )
            ON CONFLICT ({{masterId}}, detail_external_key)
            DO NOTHING
            RETURNING {{detailId}}
            """;
    }

    public static string RenderYearStateInsertSql()
    {
        return """
            INSERT INTO source_family_year_states (
                source_family_year_state_id,
                source_family,
                ingested_year,
                created_at,
                updated_at
            )
            VALUES ($1, $2, $3, NOW(), NOW())
            ON CONFLICT (source_family, ingested_year)
            DO UPDATE SET updated_at = EXCLUDED.updated_at
            RETURNING source_family_year_state_id
            """;
    }

    public static IReadOnlyList<PostgreSQLSourceSpecificFactorPersistenceSqlStep> RenderSourceFamilyYearPersistenceSqlFlow(
        SourceFamily sourceFamily) =>
    [
        new("master_insert", RenderMasterInsertSql(sourceFamily)),
        new("detail_insert", RenderDetailInsertSql(sourceFamily)),
        new("year_state_insert", RenderYearStateInsertSql()),
    ];

    public static PostgreSQLSourceSpecificFactorPersistenceTransactionBoundary DescribeTransactionBoundary() =>
        new(
            OpensTransaction: true,
            CommitsTransaction: true,
            RollsBackOnFailure: true);

    private static async Task EnsureIngestionRunAsync(
        NpgsqlConnection connection,
        NpgsqlTransaction transaction,
        PostgreSQLSourceSpecificMasterRecord master,
        CancellationToken cancellationToken)
    {
        if (master.IngestionRunId is null)
        {
            return;
        }

        await ExecuteInsertAsync(
            connection,
            transaction,
            """
            INSERT INTO ingestion_runs (
                ingestion_run_id,
                run_status,
                created_at,
                updated_at
            )
            VALUES ($1, $2, NOW(), NOW())
            ON CONFLICT (ingestion_run_id) DO NOTHING
            RETURNING ingestion_run_id
            """,
            [master.IngestionRunId.Value, "completed"],
            cancellationToken).ConfigureAwait(false);
    }

    private static async Task EnsureSourceDocumentAsync(
        NpgsqlConnection connection,
        NpgsqlTransaction transaction,
        PostgreSQLSourceSpecificMasterRecord master,
        CancellationToken cancellationToken)
    {
        await ExecuteInsertAsync(
            connection,
            transaction,
            """
            INSERT INTO source_documents (
                source_document_id,
                ingestion_run_id,
                source_family,
                source_document_uri,
                source_checksum_sha256,
                acquisition_status,
                acquired_at,
                created_at,
                updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, NOW(), NOW(), NOW())
            ON CONFLICT (source_family, source_document_uri, source_checksum_sha256)
            DO NOTHING
            RETURNING source_document_id
            """,
            [
                master.SourceDocumentId,
                master.IngestionRunId,
                master.SourceFamily.ToPostgreSQLRuntimeValue(),
                master.ArtifactReference ?? master.SourceDocumentId.ToString("D"),
                master.ArtifactChecksumSha256 ?? "checksum-unavailable",
                "downloaded",
            ],
            cancellationToken).ConfigureAwait(false);
    }

    private static async Task RecordSuccessfulYearAsync(
        NpgsqlConnection connection,
        NpgsqlTransaction transaction,
        PostgreSQLSourceSpecificFactorPersistenceBatch batch,
        string commandText,
        CancellationToken cancellationToken)
    {
        await ExecuteInsertAsync(
            connection,
            transaction,
            commandText,
            [Guid.NewGuid(), batch.SourceFamily.ToPostgreSQLRuntimeValue(), batch.SourceYear],
            cancellationToken).ConfigureAwait(false);
    }

    private static async Task<int> ExecuteInsertAsync(
        NpgsqlConnection connection,
        NpgsqlTransaction transaction,
        string commandText,
        IReadOnlyList<object?> parameters,
        CancellationToken cancellationToken)
    {
        await using var command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText = commandText;
        foreach (var parameter in parameters)
        {
            command.Parameters.AddWithValue(parameter ?? DBNull.Value);
        }

        var inserted = await command.ExecuteScalarAsync(cancellationToken).ConfigureAwait(false);
        return inserted is null ? 0 : 1;
    }

    private static IReadOnlyList<object?> MasterParameters(PostgreSQLSourceSpecificMasterRecord record) =>
    [
        record.SourceFamilyMasterId,
        record.SourceFamily.ToPostgreSQLRuntimeValue(),
        record.SourceYear,
        record.SourceVersion,
        record.SourceRelease,
        record.SourceDocumentId,
        record.IngestionRunId,
        record.RunId,
        record.MasterExternalKey,
        record.Status,
        record.ArtifactReference,
        record.ArtifactChecksumSha256,
        record.ArchiveReference,
        record.ArchiveChecksumSha256,
        record.EffectiveFrom,
        record.EffectiveTo,
        record.RecordChecksumSha256,
        JsonSerializer.Serialize(record.Metadata),
    ];

    private static IReadOnlyList<object?> DetailParameters(PostgreSQLSourceSpecificDetailRecord record) =>
    [
        record.SourceFamilyDetailId,
        record.SourceFamilyMasterId,
        record.DetailExternalKey,
        record.SourceRowNumber,
        record.FactorId,
        record.FactorName,
        record.FactorValue,
        record.FactorUnit,
        record.Status,
        record.RecordChecksumSha256,
        JsonSerializer.Serialize(record.RawFields),
        JsonSerializer.Serialize(record.NormalizedFields),
    ];

    private static string MasterIdColumn(SourceFamily sourceFamily)
    {
        var prefix = SourceFamilyPrefix(sourceFamily);
        return $"{prefix}_emission_factor_master_id";
    }

    private static string DetailIdColumn(SourceFamily sourceFamily)
    {
        var prefix = SourceFamilyPrefix(sourceFamily);
        return $"{prefix}_emission_factor_detail_id";
    }

    private static string SourceFamilyPrefix(SourceFamily sourceFamily) =>
        sourceFamily switch
        {
            SourceFamily.GhgProtocol => "ghg",
            SourceFamily.DefraDesnz => "defra",
            SourceFamily.IpccEfdb => "ipcc",
            _ => throw new ArgumentOutOfRangeException(nameof(sourceFamily), sourceFamily, "Unknown source family."),
        };
}
