using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using Npgsql;
using NpgsqlTypes;

namespace CarbonOps.Parser.Contracts;

public sealed record PostgreSQLSourceFamilyMasterDetailPersistSummary(
    string ProviderName,
    SourceFamilyRepositoryPersistStatus Status,
    int AttemptedMasterCount,
    int AttemptedDetailCount,
    int PersistedMasterCount,
    int PersistedDetailCount,
    int RecordedYearStateCount,
    IReadOnlyList<SourceFamilyRepositoryIssue> Issues);

public sealed class PostgreSQLSourceFamilyMasterDetailRuntime
{
    private readonly ISourceFamilyRepository _repository;
    private readonly PostgreSQLSourceFamilyYearStateRepository _yearStateRepository;

    public PostgreSQLSourceFamilyMasterDetailRuntime(
        ISourceFamilyRepository repository,
        PostgreSQLSourceFamilyYearStateRepository yearStateRepository)
    {
        _repository = repository;
        _yearStateRepository = yearStateRepository;
    }

    public async Task<PostgreSQLSourceFamilyMasterDetailPersistSummary> PersistParsedOutputAsync(
        ParserNormalizedOutputBatch parsedOutput,
        string? sourceDocumentId = null,
        CancellationToken cancellationToken = default)
    {
        var command = ParsedFactorPersistenceWriter.BuildCommand(parsedOutput, sourceDocumentId);
        if (command.Issues.Count > 0)
        {
            return new PostgreSQLSourceFamilyMasterDetailPersistSummary(
                _repository.ProviderName,
                SourceFamilyRepositoryPersistStatus.FailedValidation,
                command.MasterRecords.Count,
                command.DetailRecords.Count,
                0,
                0,
                0,
                command.Issues.Select(issue => new SourceFamilyRepositoryIssue(
                    issue.Code,
                    issue.Message,
                    issue.FieldName,
                    issue.Severity)).ToArray());
        }

        var result = _repository.PersistSourceFamilyRecords(command.MasterRecords, command.DetailRecords);
        if (result.Status != SourceFamilyRepositoryPersistStatus.Declared)
        {
            return new PostgreSQLSourceFamilyMasterDetailPersistSummary(
                result.ProviderName,
                result.Status,
                command.MasterRecords.Count,
                command.DetailRecords.Count,
                result.PersistedMasterCount,
                result.PersistedDetailCount,
                0,
                result.Issues);
        }

        var years = command.MasterRecords
            .Select(record => (record.SourceFamily, SourceYear: PostgreSQLSourceFamilyRecordMapper.ResolveSourceYear(record)))
            .Distinct()
            .OrderBy(item => item.SourceFamily.ToWireName(), StringComparer.Ordinal)
            .ThenBy(item => item.SourceYear)
            .ToArray();

        foreach (var year in years)
        {
            await _yearStateRepository.RecordSuccessfulYearAsync(
                year.SourceFamily,
                year.SourceYear,
                cancellationToken).ConfigureAwait(false);
        }

        return new PostgreSQLSourceFamilyMasterDetailPersistSummary(
            result.ProviderName,
            result.Status,
            command.MasterRecords.Count,
            command.DetailRecords.Count,
            result.PersistedMasterCount,
            result.PersistedDetailCount,
            years.Length,
            result.Issues);
    }
}

public sealed class PostgreSQLSourceFamilyMasterDetailRepository : ISourceFamilyRepository
{
    private readonly NpgsqlDataSource _dataSource;

    public PostgreSQLSourceFamilyMasterDetailRepository(NpgsqlDataSource dataSource)
    {
        _dataSource = dataSource;
    }

    public string ProviderName => "postgresql";

    public SourceFamilyRepositoryPersistResult PersistSourceFamilyRecords(
        IEnumerable<SourceFamilyMasterRecord> masterRecords,
        IEnumerable<SourceFamilyDetailRecord> detailRecords) =>
        PersistSourceFamilyRecordsAsync(masterRecords, detailRecords).GetAwaiter().GetResult();

    public async Task<SourceFamilyRepositoryPersistResult> PersistSourceFamilyRecordsAsync(
        IEnumerable<SourceFamilyMasterRecord> masterRecords,
        IEnumerable<SourceFamilyDetailRecord> detailRecords,
        CancellationToken cancellationToken = default)
    {
        var masterSnapshot = masterRecords.ToArray();
        var detailSnapshot = detailRecords.ToArray();
        var validation = SourceFamilyRepositoryRegistry.ValidateInputs(
            ProviderName,
            masterSnapshot,
            detailSnapshot);
        if (!validation.IsValid)
        {
            return new SourceFamilyRepositoryPersistResult(
                ProviderName,
                SourceFamilyRepositoryPersistStatus.FailedValidation,
                0,
                0,
                validation.Issues);
        }

        try
        {
            await using var connection = await _dataSource.OpenConnectionAsync(cancellationToken).ConfigureAwait(false);
            await using var transaction = await connection.BeginTransactionAsync(cancellationToken).ConfigureAwait(false);

            var persistedMasters = 0;
            foreach (var master in masterSnapshot)
            {
                persistedMasters += await InsertMasterAsync(
                    connection,
                    transaction,
                    master,
                    cancellationToken).ConfigureAwait(false);
            }

            var persistedDetails = 0;
            foreach (var detail in detailSnapshot)
            {
                persistedDetails += await InsertDetailAsync(
                    connection,
                    transaction,
                    detail,
                    cancellationToken).ConfigureAwait(false);
            }

            await transaction.CommitAsync(cancellationToken).ConfigureAwait(false);
            return new SourceFamilyRepositoryPersistResult(
                ProviderName,
                SourceFamilyRepositoryPersistStatus.Declared,
                persistedMasters,
                persistedDetails);
        }
        catch (NpgsqlException exception)
        {
            return Failed("POSTGRESQL_SOURCE_FAMILY_INSERT_FAILED", exception);
        }
        catch (InvalidOperationException exception)
        {
            return Failed("POSTGRESQL_SOURCE_FAMILY_INSERT_INVALID_RECORD", exception);
        }
        catch (FormatException exception)
        {
            return Failed("POSTGRESQL_SOURCE_FAMILY_INSERT_INVALID_RECORD", exception);
        }
    }

    private static async Task<int> InsertMasterAsync(
        NpgsqlConnection connection,
        NpgsqlTransaction transaction,
        SourceFamilyMasterRecord record,
        CancellationToken cancellationToken)
    {
        var tableNames = SourceFamilyRepositoryRegistry.GetTableNames(record.SourceFamily);
        var columnNames = PostgreSQLSourceFamilyRecordMapper.GetColumnNames(record.SourceFamily);
        await using var command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText = $"""
            INSERT INTO {tableNames.MasterTableName} (
                {columnNames.MasterIdColumnName},
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
                $1, $2, $3, $4, NULL, $5, NULL, NULL, $6, $7,
                NULL, NULL, NULL, NULL, $8, $9, $10, $11::jsonb, NOW(), NOW()
            )
            ON CONFLICT (source_family, source_year, source_version, master_external_key)
            DO NOTHING
            """;

        command.Parameters.AddWithValue(PostgreSQLSourceFamilyRecordMapper.StableUuid(record.SourceFamilyMasterId));
        command.Parameters.AddWithValue(record.SourceFamily.ToPostgreSQLRuntimeValue());
        command.Parameters.AddWithValue(PostgreSQLSourceFamilyRecordMapper.ResolveSourceYear(record));
        command.Parameters.AddWithValue(PostgreSQLSourceFamilyRecordMapper.ResolveSourceVersion(record));
        command.Parameters.AddWithValue(PostgreSQLSourceFamilyRecordMapper.StableUuid(record.SourceDocumentId));
        command.Parameters.AddWithValue(record.MasterExternalKey);
        command.Parameters.AddWithValue(record.LifecycleStatus);
        command.Parameters.AddWithValue(ToNullableTimestamp(record.EffectiveFrom));
        command.Parameters.AddWithValue(ToNullableTimestamp(record.EffectiveTo));
        command.Parameters.AddWithValue(record.RecordChecksumSha256);
        command.Parameters.AddWithValue(NpgsqlDbType.Jsonb, PostgreSQLSourceFamilyRecordMapper.MasterMetadataJson(record));

        return await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    private static async Task<int> InsertDetailAsync(
        NpgsqlConnection connection,
        NpgsqlTransaction transaction,
        SourceFamilyDetailRecord record,
        CancellationToken cancellationToken)
    {
        var tableNames = SourceFamilyRepositoryRegistry.GetTableNames(record.SourceFamily);
        var columnNames = PostgreSQLSourceFamilyRecordMapper.GetColumnNames(record.SourceFamily);
        await using var command = connection.CreateCommand();
        command.Transaction = transaction;
        command.CommandText = $"""
            INSERT INTO {tableNames.DetailTableName} (
                {columnNames.DetailIdColumnName},
                {columnNames.MasterIdColumnName},
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
                $1, $2, $3, NULL, $4, NULL, $5, $6, $7, $8, $9::jsonb, $10::jsonb, NOW(), NOW()
            )
            ON CONFLICT ({columnNames.MasterIdColumnName}, detail_external_key)
            DO NOTHING
            """;

        command.Parameters.AddWithValue(PostgreSQLSourceFamilyRecordMapper.StableUuid(record.SourceFamilyDetailId));
        command.Parameters.AddWithValue(PostgreSQLSourceFamilyRecordMapper.StableUuid(record.SourceFamilyMasterId));
        command.Parameters.AddWithValue(record.DetailExternalKey);
        command.Parameters.AddWithValue(PostgreSQLSourceFamilyRecordMapper.ResolveFactorId(record));
        command.Parameters.AddWithValue(decimal.Parse(record.FactorValue, CultureInfo.InvariantCulture));
        command.Parameters.AddWithValue(record.FactorUnit);
        command.Parameters.AddWithValue(record.LifecycleStatus);
        command.Parameters.AddWithValue(record.RecordChecksumSha256);
        command.Parameters.AddWithValue(NpgsqlDbType.Jsonb, "{}");
        command.Parameters.AddWithValue(NpgsqlDbType.Jsonb, PostgreSQLSourceFamilyRecordMapper.DetailMetadataJson(record));

        return await command.ExecuteNonQueryAsync(cancellationToken).ConfigureAwait(false);
    }

    private static object ToNullableTimestamp(string? value) =>
        DateTimeOffset.TryParse(value, CultureInfo.InvariantCulture, DateTimeStyles.AssumeUniversal, out var parsed)
            ? parsed
            : DBNull.Value;

    private SourceFamilyRepositoryPersistResult Failed(string code, Exception exception) =>
        new(
            ProviderName,
            SourceFamilyRepositoryPersistStatus.FailedValidation,
            0,
            0,
            [
                new SourceFamilyRepositoryIssue(
                    code,
                    PostgreSQLSourceFamilyRecordMapper.SafeDiagnosticMessage(exception),
                    "PostgreSQLSourceFamilyMasterDetailRepository"),
            ]);
}

public sealed record PostgreSQLSourceFamilyColumnNames(
    string MasterIdColumnName,
    string DetailIdColumnName);

public static class PostgreSQLSourceFamilyRecordMapper
{
    public static PostgreSQLSourceFamilyColumnNames GetColumnNames(SourceFamily sourceFamily)
    {
        var prefix = sourceFamily switch
        {
            SourceFamily.GhgProtocol => "ghg",
            SourceFamily.DefraDesnz => "defra",
            SourceFamily.IpccEfdb => "ipcc",
            _ => throw new ArgumentOutOfRangeException(nameof(sourceFamily), sourceFamily, "Unknown source family."),
        };

        return new PostgreSQLSourceFamilyColumnNames(
            $"{prefix}_emission_factor_master_id",
            $"{prefix}_emission_factor_detail_id");
    }

    public static int ResolveSourceYear(SourceFamilyMasterRecord record)
    {
        var parts = record.MasterExternalKey.Split(':', 3);
        if (parts.Length > 0 && int.TryParse(parts[0], NumberStyles.None, CultureInfo.InvariantCulture, out var year) && year > 0)
        {
            return year;
        }

        throw new InvalidOperationException("source-family master external key must start with a positive source year.");
    }

    public static string ResolveSourceVersion(SourceFamilyMasterRecord record)
    {
        var parts = record.MasterExternalKey.Split(':', 3);
        if (parts.Length > 1 && !string.IsNullOrWhiteSpace(parts[1]))
        {
            return parts[1].Trim();
        }

        return "unspecified";
    }

    public static string ResolveFactorId(SourceFamilyDetailRecord record)
    {
        var parts = record.DetailExternalKey.Split(':', 2);
        return string.IsNullOrWhiteSpace(parts[0]) ? record.SourceFamilyDetailId : parts[0].Trim();
    }

    public static Guid StableUuid(string value)
    {
        if (Guid.TryParse(value, out var parsed))
        {
            return parsed;
        }

        var bytes = SHA256.HashData(Encoding.UTF8.GetBytes(value));
        var uuidBytes = bytes.Take(16).ToArray();
        uuidBytes[6] = (byte)((uuidBytes[6] & 0x0F) | 0x50);
        uuidBytes[8] = (byte)((uuidBytes[8] & 0x3F) | 0x80);
        return new Guid(uuidBytes);
    }

    public static string MasterMetadataJson(SourceFamilyMasterRecord record) =>
        JsonSerializer.Serialize(new SortedDictionary<string, string?>
        {
            ["source_family_master_id"] = record.SourceFamilyMasterId,
            ["source_document_id"] = record.SourceDocumentId,
            ["created_at_label"] = record.CreatedAt,
            ["updated_at_label"] = record.UpdatedAt,
        });

    public static string DetailMetadataJson(SourceFamilyDetailRecord record) =>
        JsonSerializer.Serialize(new SortedDictionary<string, string?>
        {
            ["source_family_detail_id"] = record.SourceFamilyDetailId,
            ["source_family_master_id"] = record.SourceFamilyMasterId,
            ["detail_external_key"] = record.DetailExternalKey,
            ["created_at_label"] = record.CreatedAt,
            ["updated_at_label"] = record.UpdatedAt,
        });

    public static string SafeDiagnosticMessage(Exception exception) =>
        Phase1OperationalDiagnostics.RedactDiagnosticValue("message", exception.Message)?.ToString() ??
            "PostgreSQL source-family insert failed.";
}
