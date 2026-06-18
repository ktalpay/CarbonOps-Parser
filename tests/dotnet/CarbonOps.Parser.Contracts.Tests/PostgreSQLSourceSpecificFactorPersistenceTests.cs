using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class PostgreSQLSourceSpecificFactorPersistenceTests
{
    [Theory]
    [InlineData(SourceFamily.GhgProtocol, "ghg_emission_factor_masters", "ghg_emission_factor_details")]
    [InlineData(SourceFamily.DefraDesnz, "defra_emission_factor_masters", "defra_emission_factor_details")]
    [InlineData(SourceFamily.IpccEfdb, "ipcc_emission_factor_masters", "ipcc_emission_factor_details")]
    public void MapperBuildsSourceSpecificMasterAndDetailRecordsForEachFamily(
        SourceFamily sourceFamily,
        string masterTable,
        string detailTable)
    {
        var mapped = PostgreSQLSourceSpecificFactorPersistenceMapper.Map(
            new ParserNormalizedOutputBatch([CreateRow(sourceFamily)]));

        Assert.Empty(mapped.Issues);
        var batch = Assert.Single(mapped.Batches);
        Assert.Equal(sourceFamily, batch.SourceFamily);
        Assert.Equal(2024, batch.SourceYear);
        var master = Assert.Single(batch.MasterRecords);
        var detail = Assert.Single(batch.DetailRecords);
        Assert.Equal(sourceFamily, master.SourceFamily);
        Assert.Equal(sourceFamily, detail.SourceFamily);
        Assert.Equal(2024, master.SourceYear);
        Assert.Equal("fixture-v1", master.SourceVersion);
        Assert.Equal("release-a", master.SourceRelease);
        Assert.Equal("run-001", master.RunId);
        Assert.Equal("artifact://fixture/factors.csv", master.ArtifactReference);
        Assert.Equal("a".PadLeft(64, 'a'), master.ArtifactChecksumSha256);
        Assert.Equal("2024:fixture-v1:FACTOR-001", master.MasterExternalKey);
        Assert.Equal(master.SourceFamilyMasterId, detail.SourceFamilyMasterId);
        Assert.Equal("FACTOR-001:kgco2e:CO2e", detail.DetailExternalKey);
        Assert.Equal(7, detail.SourceRowNumber);
        Assert.Equal("FACTOR-001", detail.FactorId);
        Assert.Equal("Fixture factor", detail.FactorName);
        Assert.Equal(1.25m, detail.FactorValue);
        Assert.Equal("kgco2e", detail.FactorUnit);
        Assert.Equal("active", detail.Status);

        Assert.Contains(masterTable, NpgsqlSourceSpecificFactorPersistenceSession.RenderMasterInsertSql(sourceFamily), StringComparison.Ordinal);
        Assert.Contains(detailTable, NpgsqlSourceSpecificFactorPersistenceSession.RenderDetailInsertSql(sourceFamily), StringComparison.Ordinal);
    }

    [Theory]
    [InlineData(SourceFamily.GhgProtocol)]
    [InlineData(SourceFamily.DefraDesnz)]
    [InlineData(SourceFamily.IpccEfdb)]
    public async Task RepositoryInsertsOneMasterAndMatchingDetailForEachFamily(SourceFamily sourceFamily)
    {
        var session = new InMemorySourceSpecificSession();
        var repository = new PostgreSQLSourceSpecificFactorPersistenceRepository(session);

        var result = await repository.PersistAsync(new ParserNormalizedOutputBatch([CreateRow(sourceFamily)]));

        Assert.Equal(PostgreSQLSourceSpecificFactorPersistenceStatus.Inserted, result.Status);
        Assert.Equal(1, result.MasterInserted);
        Assert.Equal(0, result.MasterSkippedDuplicate);
        Assert.Equal(1, result.DetailInserted);
        Assert.Equal(0, result.DetailSkippedDuplicate);
        Assert.Equal(0, result.ValidationFailed);
        Assert.Contains((sourceFamily, 2024), session.RecordedYears);
    }

    [Fact]
    public async Task RepositoryRerunSkipsDuplicatesExplicitly()
    {
        var session = new InMemorySourceSpecificSession();
        var repository = new PostgreSQLSourceSpecificFactorPersistenceRepository(session);
        var batch = new ParserNormalizedOutputBatch([CreateRow(SourceFamily.DefraDesnz)]);

        var first = await repository.PersistAsync(batch);
        var second = await repository.PersistAsync(batch);

        Assert.Equal(1, first.MasterInserted);
        Assert.Equal(1, first.DetailInserted);
        Assert.Equal(0, first.MasterSkippedDuplicate);
        Assert.Equal(0, first.DetailSkippedDuplicate);
        Assert.Equal(0, second.MasterInserted);
        Assert.Equal(0, second.DetailInserted);
        Assert.Equal(1, second.MasterSkippedDuplicate);
        Assert.Equal(1, second.DetailSkippedDuplicate);
        Assert.Equal(1, session.RecordedYears.Count(record => record == (SourceFamily.DefraDesnz, 2024)));
    }

    [Fact]
    public async Task RepositoryDoesNotAdvanceYearStateWhenValidationFails()
    {
        var session = new InMemorySourceSpecificSession();
        var repository = new PostgreSQLSourceSpecificFactorPersistenceRepository(session);
        var malformed = CreateRow(SourceFamily.GhgProtocol, factorValue: "not-a-number");

        var result = await repository.PersistAsync(new ParserNormalizedOutputBatch([malformed]));

        Assert.Equal(PostgreSQLSourceSpecificFactorPersistenceStatus.FailedValidation, result.Status);
        Assert.Equal(0, result.MasterInserted);
        Assert.Equal(0, result.DetailInserted);
        Assert.True(result.ValidationFailed > 0);
        Assert.Empty(session.RecordedYears);
    }

    [Fact]
    public async Task RepositoryDoesNotAdvanceYearStateWhenInsertFails()
    {
        var session = new InMemorySourceSpecificSession { FailBeforeYearState = true };
        var repository = new PostgreSQLSourceSpecificFactorPersistenceRepository(session);

        var result = await repository.PersistAsync(new ParserNormalizedOutputBatch([CreateRow(SourceFamily.IpccEfdb)]));

        Assert.Equal(PostgreSQLSourceSpecificFactorPersistenceStatus.FailedDatabase, result.Status);
        Assert.Equal(0, result.MasterInserted);
        Assert.Equal(0, result.DetailInserted);
        Assert.Empty(session.RecordedYears);
    }

    [Fact]
    public async Task RepositoryDiagnosticsRedactSecrets()
    {
        var session = new InMemorySourceSpecificSession
        {
            FailureMessage = "postgresql://user:secret@example/db password=secret-token",
        };
        var repository = new PostgreSQLSourceSpecificFactorPersistenceRepository(session);

        var result = await repository.PersistAsync(new ParserNormalizedOutputBatch([CreateRow(SourceFamily.GhgProtocol)]));

        var issue = Assert.Single(result.Issues);
        Assert.Equal("POSTGRESQL_SOURCE_SPECIFIC_DATABASE_ERROR", issue.Code);
        Assert.Contains("postgresql://***@example/db", issue.Message, StringComparison.Ordinal);
        Assert.Contains("password=***", issue.Message, StringComparison.Ordinal);
        Assert.DoesNotContain("secret-token", issue.Message, StringComparison.Ordinal);
    }

    [Fact]
    public void SourceSpecificInsertSqlIsAdditiveAndUsesConflictSkips()
    {
        var statements = SourceFamilyRegistry.SupportedFamilies
            .SelectMany(family => new[]
            {
                NpgsqlSourceSpecificFactorPersistenceSession.RenderMasterInsertSql(family),
                NpgsqlSourceSpecificFactorPersistenceSession.RenderDetailInsertSql(family),
            })
            .ToArray();

        Assert.All(statements, statement =>
        {
            Assert.Contains("INSERT INTO", statement, StringComparison.Ordinal);
            Assert.Contains("ON CONFLICT", statement, StringComparison.Ordinal);
            Assert.Contains("DO NOTHING", statement, StringComparison.Ordinal);
            Assert.DoesNotContain("DROP", statement, StringComparison.OrdinalIgnoreCase);
            Assert.DoesNotContain("TRUNCATE", statement, StringComparison.OrdinalIgnoreCase);
            Assert.DoesNotContain("DELETE", statement, StringComparison.OrdinalIgnoreCase);
            Assert.DoesNotContain("ALTER TABLE", statement, StringComparison.OrdinalIgnoreCase);
            Assert.DoesNotContain("RENAME", statement, StringComparison.OrdinalIgnoreCase);
        });
    }

    [Fact]
    public void YearStateInsertSqlIsExplicitAndIdempotent()
    {
        var statement = NpgsqlSourceSpecificFactorPersistenceSession.RenderYearStateInsertSql();

        Assert.Contains("INSERT INTO source_family_year_states", statement, StringComparison.Ordinal);
        Assert.Contains("source_family_year_state_id", statement, StringComparison.Ordinal);
        Assert.Contains("source_family", statement, StringComparison.Ordinal);
        Assert.Contains("ingested_year", statement, StringComparison.Ordinal);
        Assert.Contains("ON CONFLICT (source_family, ingested_year)", statement, StringComparison.Ordinal);
        Assert.Contains("DO UPDATE SET updated_at = EXCLUDED.updated_at", statement, StringComparison.Ordinal);
        Assert.DoesNotContain("DROP", statement, StringComparison.OrdinalIgnoreCase);
        Assert.DoesNotContain("TRUNCATE", statement, StringComparison.OrdinalIgnoreCase);
        Assert.DoesNotContain("DELETE", statement, StringComparison.OrdinalIgnoreCase);
        Assert.DoesNotContain("ALTER TABLE", statement, StringComparison.OrdinalIgnoreCase);
    }

    [Theory]
    [InlineData(SourceFamily.GhgProtocol)]
    [InlineData(SourceFamily.DefraDesnz)]
    [InlineData(SourceFamily.IpccEfdb)]
    public void MasterAndDetailInsertSqlDoNotWriteYearState(SourceFamily sourceFamily)
    {
        var master = NpgsqlSourceSpecificFactorPersistenceSession.RenderMasterInsertSql(sourceFamily);
        var detail = NpgsqlSourceSpecificFactorPersistenceSession.RenderDetailInsertSql(sourceFamily);

        Assert.DoesNotContain("source_family_year_states", master, StringComparison.Ordinal);
        Assert.DoesNotContain("source_family_year_states", detail, StringComparison.Ordinal);
        Assert.DoesNotContain("DO UPDATE SET", master, StringComparison.Ordinal);
        Assert.DoesNotContain("DO UPDATE SET", detail, StringComparison.Ordinal);
    }

    [Fact]
    public void NpgsqlPersistenceSessionDeclaresTransactionRollbackBoundary()
    {
        var boundary = NpgsqlSourceSpecificFactorPersistenceSession.DescribeTransactionBoundary();

        Assert.True(boundary.OpensTransaction);
        Assert.True(boundary.CommitsTransaction);
        Assert.True(boundary.RollsBackOnFailure);
    }

    [Theory]
    [InlineData(SourceFamily.GhgProtocol)]
    [InlineData(SourceFamily.DefraDesnz)]
    [InlineData(SourceFamily.IpccEfdb)]
    public void YearStateRecordingRemainsAfterMasterAndDetailInsertSqlInFlow(SourceFamily sourceFamily)
    {
        var flow = NpgsqlSourceSpecificFactorPersistenceSession.RenderSourceFamilyYearPersistenceSqlFlow(sourceFamily);

        Assert.Equal(["master_insert", "detail_insert", "year_state_insert"], flow.Select(step => step.Name));
        Assert.Contains("source_family_year_states", flow[2].CommandText, StringComparison.Ordinal);
        Assert.DoesNotContain("source_family_year_states", flow[0].CommandText, StringComparison.Ordinal);
        Assert.DoesNotContain("source_family_year_states", flow[1].CommandText, StringComparison.Ordinal);
    }

    private static ParserNormalizedOutputRow CreateRow(
        SourceFamily sourceFamily,
        string factorValue = "1.25")
    {
        var sourceKey = sourceFamily.ToWireName();
        return new ParserNormalizedOutputRow(
            sourceFamily,
            sourceKey,
            ParserSelectionRegistry.GetParserKey(sourceFamily),
            "artifact://fixture/factors.csv",
            $"{sourceKey}_row_7",
            sourceRowNumber: 7,
            [
                new ParserNormalizedField("source_family", sourceKey),
                new ParserNormalizedField("source_year", "2024"),
                new ParserNormalizedField("source_version", "fixture-v1"),
                new ParserNormalizedField("source_release", "release-a"),
                new ParserNormalizedField("run_id", "run-001"),
                new ParserNormalizedField("factor_id", "FACTOR-001"),
                new ParserNormalizedField("factor_name", "Fixture factor"),
                new ParserNormalizedField("factor_value", factorValue),
                new ParserNormalizedField("unit", "kgco2e"),
                new ParserNormalizedField("gas", "CO2e"),
                new ParserNormalizedField("provenance_artifact_reference", "artifact://fixture/factors.csv"),
                new ParserNormalizedField("provenance_checksum_value", "a".PadLeft(64, 'a')),
                new ParserNormalizedField("provenance_row_number", "7"),
                new ParserNormalizedField("master_external_key", "2024:fixture-v1:FACTOR-001"),
                new ParserNormalizedField("detail_external_key", "FACTOR-001:kgco2e:CO2e"),
            ],
            reportingYear: 2024);
    }

    private sealed class InMemorySourceSpecificSession : IPostgreSQLSourceSpecificFactorPersistenceSession
    {
        private readonly HashSet<(SourceFamily SourceFamily, int SourceYear, string SourceVersion, string MasterKey)> _masters = [];
        private readonly HashSet<(SourceFamily SourceFamily, Guid MasterId, string DetailKey)> _details = [];

        public string ProviderName => "fake_postgresql";

        public bool FailBeforeYearState { get; init; }

        public string? FailureMessage { get; init; }

        public List<(SourceFamily SourceFamily, int SourceYear)> RecordedYears { get; } = [];

        public Task<PostgreSQLSourceSpecificFactorPersistenceCounts> PersistSourceFamilyYearAsync(
            PostgreSQLSourceSpecificFactorPersistenceBatch batch,
            CancellationToken cancellationToken = default)
        {
            if (FailureMessage is not null)
            {
                throw new InvalidOperationException(FailureMessage);
            }

            var masterInserted = 0;
            var detailInserted = 0;
            foreach (var master in batch.MasterRecords)
            {
                if (_masters.Add((master.SourceFamily, master.SourceYear, master.SourceVersion, master.MasterExternalKey)))
                {
                    masterInserted++;
                }
            }

            foreach (var detail in batch.DetailRecords)
            {
                if (_details.Add((detail.SourceFamily, detail.SourceFamilyMasterId, detail.DetailExternalKey)))
                {
                    detailInserted++;
                }
            }

            if (FailBeforeYearState)
            {
                throw new InvalidOperationException("detail insert failed before year-state update");
            }

            if (!RecordedYears.Contains((batch.SourceFamily, batch.SourceYear)))
            {
                RecordedYears.Add((batch.SourceFamily, batch.SourceYear));
            }

            return Task.FromResult(new PostgreSQLSourceSpecificFactorPersistenceCounts(
                masterInserted,
                batch.MasterRecords.Count - masterInserted,
                detailInserted,
                batch.DetailRecords.Count - detailInserted,
                0));
        }
    }
}
