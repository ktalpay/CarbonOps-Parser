using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class PostgreSQLSourceFamilyMasterDetailRuntimeTests
{
    [Theory]
    [InlineData(SourceFamily.GhgProtocol, "ghg_emission_factor_masters", "ghg_emission_factor_details")]
    [InlineData(SourceFamily.DefraDesnz, "defra_emission_factor_masters", "defra_emission_factor_details")]
    [InlineData(SourceFamily.IpccEfdb, "ipcc_emission_factor_masters", "ipcc_emission_factor_details")]
    public void RuntimeMappingTargetsAllSourceFamilyTables(
        SourceFamily sourceFamily,
        string expectedMasterTable,
        string expectedDetailTable)
    {
        var tableNames = SourceFamilyRepositoryRegistry.GetTableNames(sourceFamily);
        var columns = PostgreSQLSourceFamilyRecordMapper.GetColumnNames(sourceFamily);
        var master = CreateMasterRecord(sourceFamily);
        var detail = CreateDetailRecord(sourceFamily);

        Assert.Equal(expectedMasterTable, tableNames.MasterTableName);
        Assert.Equal(expectedDetailTable, tableNames.DetailTableName);
        Assert.EndsWith("_emission_factor_master_id", columns.MasterIdColumnName, StringComparison.Ordinal);
        Assert.EndsWith("_emission_factor_detail_id", columns.DetailIdColumnName, StringComparison.Ordinal);
        Assert.Equal(2024, PostgreSQLSourceFamilyRecordMapper.ResolveSourceYear(master));
        Assert.Equal("fixture-v1", PostgreSQLSourceFamilyRecordMapper.ResolveSourceVersion(master));
        Assert.Equal("factor-001", PostgreSQLSourceFamilyRecordMapper.ResolveFactorId(detail));
        Assert.Equal(
            PostgreSQLSourceFamilyRecordMapper.StableUuid(master.SourceFamilyMasterId),
            PostgreSQLSourceFamilyRecordMapper.StableUuid(master.SourceFamilyMasterId));
    }

    [Fact]
    public async Task RuntimePersistsMasterDetailAndRecordsYearStateAfterSuccessfulInsert()
    {
        var repository = new IdempotentSourceFamilyRepository();
        var yearState = new RecordingYearStateSession();
        var runtime = new PostgreSQLSourceFamilyMasterDetailRuntime(
            repository,
            new PostgreSQLSourceFamilyYearStateRepository(yearState));
        var batch = new ParserNormalizedOutputBatch(
            [
                CreateRow(SourceFamily.GhgProtocol, "GHG-001"),
                CreateRow(SourceFamily.DefraDesnz, "DEFRA-001"),
                CreateRow(SourceFamily.IpccEfdb, "IPCC-001"),
            ]);

        var result = await runtime.PersistParsedOutputAsync(batch, sourceDocumentId: "source-document-001");

        Assert.Equal(SourceFamilyRepositoryPersistStatus.Declared, result.Status);
        Assert.Equal(3, result.AttemptedMasterCount);
        Assert.Equal(3, result.AttemptedDetailCount);
        Assert.Equal(3, result.PersistedMasterCount);
        Assert.Equal(3, result.PersistedDetailCount);
        Assert.Equal(3, result.RecordedYearStateCount);
        Assert.Equal(
            new[] { SourceFamily.DefraDesnz, SourceFamily.GhgProtocol, SourceFamily.IpccEfdb },
            yearState.Records.Select(record => record.SourceFamily));
        Assert.All(yearState.Records, record => Assert.Equal(2024, record.Year));
    }

    [Fact]
    public async Task DuplicateSourceYearArtifactRerunsDoNotDuplicateRows()
    {
        var repository = new IdempotentSourceFamilyRepository();
        var yearState = new RecordingYearStateSession();
        var runtime = new PostgreSQLSourceFamilyMasterDetailRuntime(
            repository,
            new PostgreSQLSourceFamilyYearStateRepository(yearState));
        var batch = new ParserNormalizedOutputBatch([CreateRow(SourceFamily.GhgProtocol, "GHG-001")]);

        var first = await runtime.PersistParsedOutputAsync(batch, sourceDocumentId: "source-document-001");
        var second = await runtime.PersistParsedOutputAsync(batch, sourceDocumentId: "source-document-001");

        Assert.Equal(1, first.PersistedMasterCount);
        Assert.Equal(1, first.PersistedDetailCount);
        Assert.Equal(0, second.PersistedMasterCount);
        Assert.Equal(0, second.PersistedDetailCount);
        Assert.Single(repository.MasterKeys);
        Assert.Single(repository.DetailKeys);
        Assert.Single(yearState.Records);
    }

    [Fact]
    public async Task RuntimeDoesNotUpdateYearStateAfterFailedInsert()
    {
        var repository = new FailingSourceFamilyRepository();
        var yearState = new RecordingYearStateSession();
        var runtime = new PostgreSQLSourceFamilyMasterDetailRuntime(
            repository,
            new PostgreSQLSourceFamilyYearStateRepository(yearState));

        var result = await runtime.PersistParsedOutputAsync(
            new ParserNormalizedOutputBatch([CreateRow(SourceFamily.DefraDesnz, "DEFRA-001")]),
            sourceDocumentId: "source-document-001");

        Assert.Equal(SourceFamilyRepositoryPersistStatus.FailedValidation, result.Status);
        Assert.Equal(0, result.RecordedYearStateCount);
        Assert.Empty(yearState.Records);
    }

    [Fact]
    public void RuntimeDiagnosticsRedactSensitiveExceptionText()
    {
        var diagnostic = PostgreSQLSourceFamilyRecordMapper.SafeDiagnosticMessage(
            new InvalidOperationException(
                "failed dsn=postgresql://svc:raw-secret@db.internal/carbonops token=abc123"));

        Assert.Contains(Phase1OperationalDiagnostics.Redacted, diagnostic, StringComparison.Ordinal);
        Assert.DoesNotContain("raw-secret", diagnostic, StringComparison.Ordinal);
        Assert.DoesNotContain("abc123", diagnostic, StringComparison.Ordinal);
    }

    private static ParserNormalizedOutputRow CreateRow(SourceFamily sourceFamily, string factorId)
    {
        var sourceKey = sourceFamily.ToWireName();
        var prefix = sourceFamily switch
        {
            SourceFamily.GhgProtocol => "ghg",
            SourceFamily.DefraDesnz => "defra",
            SourceFamily.IpccEfdb => "ipcc",
            _ => throw new ArgumentOutOfRangeException(nameof(sourceFamily), sourceFamily, "Unknown source family."),
        };

        return new ParserNormalizedOutputRow(
            sourceFamily,
            sourceKey,
            ParserSelectionRegistry.GetParserKey(sourceFamily),
            $"artifact://{sourceKey}/2024.csv",
            $"{sourceKey}_{factorId}_row_1",
            1,
            [
                new ParserNormalizedField("source_family", sourceKey),
                new ParserNormalizedField("source_year", "2024"),
                new ParserNormalizedField("source_version", "fixture-v1"),
                new ParserNormalizedField("factor_id", factorId),
                new ParserNormalizedField("factor_value", "1.25"),
                new ParserNormalizedField("unit", "kgco2e"),
                new ParserNormalizedField("gas", "CO2e"),
                new ParserNormalizedField("provenance_artifact_reference", $"artifact://{sourceKey}/2024.csv"),
                new ParserNormalizedField("provenance_checksum_value", "c".PadLeft(64, 'c')),
                new ParserNormalizedField("source_family_master_id", $"{prefix}_master_2024_fixture-v1_{factorId}"),
                new ParserNormalizedField("source_family_detail_id", $"{prefix}_detail_2024_fixture-v1_{factorId}"),
                new ParserNormalizedField("master_external_key", $"2024:fixture-v1:{factorId}"),
                new ParserNormalizedField("detail_external_key", $"{factorId}:kgco2e:CO2e"),
            ],
            reportingYear: 2024);
    }

    private static SourceFamilyMasterRecord CreateMasterRecord(SourceFamily sourceFamily) =>
        new(
            sourceFamily,
            $"{sourceFamily.ToWireName()}_master",
            "source-document-001",
            "2024:fixture-v1:factor-001",
            "active",
            null,
            null,
            "checksum-master",
            ParsedFactorPersistenceWriter.DefaultTimestampLabel,
            ParsedFactorPersistenceWriter.DefaultTimestampLabel);

    private static SourceFamilyDetailRecord CreateDetailRecord(SourceFamily sourceFamily) =>
        new(
            sourceFamily,
            $"{sourceFamily.ToWireName()}_detail",
            $"{sourceFamily.ToWireName()}_master",
            "factor-001:kgco2e",
            "1.25",
            "kgco2e",
            "active",
            "checksum-detail",
            ParsedFactorPersistenceWriter.DefaultTimestampLabel,
            ParsedFactorPersistenceWriter.DefaultTimestampLabel);

    private sealed class IdempotentSourceFamilyRepository : ISourceFamilyRepository
    {
        public HashSet<(SourceFamily SourceFamily, string MasterKey)> MasterKeys { get; } = [];

        public HashSet<(SourceFamily SourceFamily, string MasterKey, string DetailKey)> DetailKeys { get; } = [];

        public string ProviderName => "idempotent_test";

        public SourceFamilyRepositoryPersistResult PersistSourceFamilyRecords(
            IEnumerable<SourceFamilyMasterRecord> masterRecords,
            IEnumerable<SourceFamilyDetailRecord> detailRecords)
        {
            var masters = masterRecords.ToArray();
            var details = detailRecords.ToArray();
            var validation = SourceFamilyRepositoryRegistry.ValidateInputs(ProviderName, masters, details);
            if (!validation.IsValid)
            {
                return new SourceFamilyRepositoryPersistResult(
                    ProviderName,
                    SourceFamilyRepositoryPersistStatus.FailedValidation,
                    0,
                    0,
                    validation.Issues);
            }

            var insertedMasters = masters.Count(master => MasterKeys.Add((master.SourceFamily, master.MasterExternalKey)));
            var insertedDetails = details.Count(detail => DetailKeys.Add((detail.SourceFamily, detail.SourceFamilyMasterId, detail.DetailExternalKey)));
            return new SourceFamilyRepositoryPersistResult(
                ProviderName,
                SourceFamilyRepositoryPersistStatus.Declared,
                insertedMasters,
                insertedDetails);
        }
    }

    private sealed class FailingSourceFamilyRepository : ISourceFamilyRepository
    {
        public string ProviderName => "failing_test";

        public SourceFamilyRepositoryPersistResult PersistSourceFamilyRecords(
            IEnumerable<SourceFamilyMasterRecord> masterRecords,
            IEnumerable<SourceFamilyDetailRecord> detailRecords) =>
            new(
                ProviderName,
                SourceFamilyRepositoryPersistStatus.FailedValidation,
                0,
                0,
                [new SourceFamilyRepositoryIssue("TEST_INSERT_FAILED", "insert failed", "repository")]);
    }

    private sealed class RecordingYearStateSession : IPostgreSQLSourceFamilyYearStateSession
    {
        private readonly HashSet<(SourceFamily SourceFamily, int Year)> _records = [];

        public IReadOnlyList<(SourceFamily SourceFamily, int Year)> Records =>
            _records.OrderBy(record => record.SourceFamily.ToWireName(), StringComparer.Ordinal).ToArray();

        public Task<int?> LatestSuccessfulYearAsync(
            SourceFamily sourceFamily,
            CancellationToken cancellationToken = default)
        {
            var years = _records
                .Where(record => record.SourceFamily == sourceFamily)
                .Select(record => record.Year)
                .ToArray();
            return Task.FromResult(years.Length == 0 ? null : (int?)years.Max());
        }

        public Task RecordSuccessfulYearAsync(
            SourceFamily sourceFamily,
            int ingestedYear,
            CancellationToken cancellationToken = default)
        {
            _records.Add((sourceFamily, ingestedYear));
            return Task.CompletedTask;
        }
    }
}
