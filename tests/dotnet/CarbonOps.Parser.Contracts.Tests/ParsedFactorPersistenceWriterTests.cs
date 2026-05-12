using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class ParsedFactorPersistenceWriterTests
{
    [Theory]
    [InlineData(SourceFamily.GhgProtocol, "ghg", "GHG-001", "kgco2e", "CO2e")]
    [InlineData(SourceFamily.DefraDesnz, "defra", "DEFRA-001", "kWh", "CO2e")]
    [InlineData(SourceFamily.IpccEfdb, "ipcc", "IPCC-001", "kg", "CH4")]
    public void WriterMapsNormalizedOutputIntoSourceFamilyRecords(
        SourceFamily sourceFamily,
        string expectedPrefix,
        string factorId,
        string unit,
        string gas)
    {
        var row = CreateRow(sourceFamily, factorId, unit, gas);

        var command = ParsedFactorPersistenceWriter.BuildCommand(
            new ParserNormalizedOutputBatch([row]),
            sourceDocumentId: "source-document-001");

        Assert.Empty(command.Issues);
        Assert.Single(command.MasterRecords);
        Assert.Single(command.DetailRecords);
        Assert.Equal(sourceFamily, command.MasterRecords[0].SourceFamily);
        Assert.Equal(sourceFamily, command.DetailRecords[0].SourceFamily);
        Assert.Equal("source-document-001", command.MasterRecords[0].SourceDocumentId);
        Assert.Equal($"{expectedPrefix}_master_2024_fixture-v1_{factorId}", command.MasterRecords[0].SourceFamilyMasterId);
        Assert.Equal($"2024:fixture-v1:{factorId}", command.MasterRecords[0].MasterExternalKey);
        Assert.Equal($"{expectedPrefix}_detail_2024_fixture-v1_{factorId}", command.DetailRecords[0].SourceFamilyDetailId);
        Assert.Equal(command.MasterRecords[0].SourceFamilyMasterId, command.DetailRecords[0].SourceFamilyMasterId);
        Assert.Equal($"{factorId}:{unit}:{gas}", command.DetailRecords[0].DetailExternalKey);
        Assert.Equal("1.25", command.DetailRecords[0].FactorValue);
        Assert.Equal(unit, command.DetailRecords[0].FactorUnit);
    }

    [Fact]
    public void WriterPersistsMappedCommandThroughRepository()
    {
        var repository = new FakeSourceFamilyRepository();
        var batch = new ParserNormalizedOutputBatch(
            [
                CreateRow(SourceFamily.GhgProtocol, "GHG-001", "kgco2e", "CO2e"),
                CreateRow(SourceFamily.DefraDesnz, "DEFRA-001", "kWh", "CO2e"),
                CreateRow(SourceFamily.IpccEfdb, "IPCC-001", "kg", "CH4"),
            ]);

        var result = ParsedFactorPersistenceWriter.Persist(
            batch,
            repository,
            sourceDocumentId: "source-document-001");

        Assert.Equal(ParsedFactorPersistenceStatus.Declared, result.Status);
        Assert.Equal("fake_source_family", result.ProviderName);
        Assert.Equal(3, result.AttemptedMasterCount);
        Assert.Equal(3, result.AttemptedDetailCount);
        Assert.Equal(3, result.PersistedMasterCount);
        Assert.Equal(3, result.PersistedDetailCount);
        Assert.Empty(result.Issues);
        Assert.NotNull(result.Command);
        Assert.Single(repository.Calls);
    }

    [Fact]
    public void WriterDeduplicatesIdenticalFactorIdentityDeterministically()
    {
        var row = CreateRow(SourceFamily.DefraDesnz, "DEFRA-001", "kWh", "CO2e");

        var command = ParsedFactorPersistenceWriter.BuildCommand(
            new ParserNormalizedOutputBatch([row, row]),
            sourceDocumentId: "source-document-001");

        Assert.Empty(command.Issues);
        Assert.Equal(2, command.SkippedDuplicateCount);
        Assert.Single(command.MasterRecords);
        Assert.Single(command.DetailRecords);
    }

    [Fact]
    public void WriterResolvesDuplicateSourceDocumentIdentityDeterministically()
    {
        var row = CreateRow(SourceFamily.GhgProtocol, "GHG-001", "kgco2e", "CO2e");

        var first = ParsedFactorPersistenceWriter.BuildCommand(new ParserNormalizedOutputBatch([row]));
        var second = ParsedFactorPersistenceWriter.BuildCommand(new ParserNormalizedOutputBatch([row]));

        Assert.Empty(first.Issues);
        Assert.Empty(second.Issues);
        Assert.StartsWith("source_document_", first.MasterRecords[0].SourceDocumentId);
        Assert.Equal(first.MasterRecords[0].SourceDocumentId, second.MasterRecords[0].SourceDocumentId);
    }

    [Fact]
    public void WriterRejectsDuplicateFactorIdentityWithDifferentContent()
    {
        var first = CreateRow(SourceFamily.DefraDesnz, "DEFRA-001", "kWh", "CO2e");
        var conflicting = CreateRow(SourceFamily.DefraDesnz, "DEFRA-001", "kWh", "CO2e", factorValue: "9.99");

        var command = ParsedFactorPersistenceWriter.BuildCommand(
            new ParserNormalizedOutputBatch([first, conflicting]),
            sourceDocumentId: "source-document-001");

        Assert.Contains(command.Issues, issue => issue.Code == "PARSED_FACTOR_PERSISTENCE_DUPLICATE_DETAIL_CONFLICT");
    }

    [Fact]
    public void WriterRejectsMalformedPersistenceInputBeforeRepositoryCall()
    {
        var repository = new FakeSourceFamilyRepository();
        var malformed = CreateRow(
            SourceFamily.DefraDesnz,
            "DEFRA-001",
            unit: "",
            gas: "CO2e");

        var result = ParsedFactorPersistenceWriter.Persist(
            new ParserNormalizedOutputBatch([malformed]),
            repository,
            sourceDocumentId: "source-document-001");

        Assert.Equal(ParsedFactorPersistenceStatus.FailedValidation, result.Status);
        Assert.Empty(repository.Calls);
        Assert.Contains(result.Issues, issue =>
            issue.Code == "PARSED_FACTOR_PERSISTENCE_MISSING_REQUIRED_FIELD" &&
            issue.FieldName == "Rows[0].factor_unit");
    }

    [Fact]
    public void WriterReportsNoRecordsWithoutCallingRepository()
    {
        var repository = new FakeSourceFamilyRepository();

        var result = ParsedFactorPersistenceWriter.Persist(
            new ParserNormalizedOutputBatch([]),
            repository);

        Assert.Equal(ParsedFactorPersistenceStatus.NoRecords, result.Status);
        Assert.Empty(repository.Calls);
        Assert.Equal("PARSED_FACTOR_PERSISTENCE_NO_RECORDS", result.Issues[0].Code);
    }

    private static ParserNormalizedOutputRow CreateRow(
        SourceFamily sourceFamily,
        string factorId,
        string unit,
        string gas,
        string factorValue = "1.25")
    {
        var parserKey = ParserSelectionRegistry.GetParserKey(sourceFamily);
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
            parserKey,
            $"artifact://{sourceKey}/factors.csv",
            $"{sourceKey}_{factorId}_row_1",
            sourceRowNumber: 1,
            [
                new ParserNormalizedField("source_family", sourceKey),
                new ParserNormalizedField("source_year", "2024"),
                new ParserNormalizedField("source_version", "fixture-v1"),
                new ParserNormalizedField("factor_id", factorId),
                new ParserNormalizedField("factor_value", factorValue),
                new ParserNormalizedField("unit", unit),
                new ParserNormalizedField("gas", gas),
                new ParserNormalizedField("provenance_artifact_reference", $"artifact://{sourceKey}/factors.csv"),
                new ParserNormalizedField("provenance_checksum_value", "c".PadLeft(64, 'c')),
                new ParserNormalizedField("source_family_master_id", $"{prefix}_master_2024_fixture-v1_{factorId}"),
                new ParserNormalizedField("source_family_detail_id", $"{prefix}_detail_2024_fixture-v1_{factorId}"),
                new ParserNormalizedField("master_external_key", $"2024:fixture-v1:{factorId}"),
                new ParserNormalizedField("detail_external_key", $"{factorId}:{unit}:{gas}"),
            ],
            reportingYear: 2024);
    }

    private sealed class FakeSourceFamilyRepository : ISourceFamilyRepository
    {
        public List<(IReadOnlyList<SourceFamilyMasterRecord> Masters, IReadOnlyList<SourceFamilyDetailRecord> Details)> Calls { get; } = [];

        public string ProviderName => "fake_source_family";

        public SourceFamilyRepositoryPersistResult PersistSourceFamilyRecords(
            IEnumerable<SourceFamilyMasterRecord> masterRecords,
            IEnumerable<SourceFamilyDetailRecord> detailRecords)
        {
            var masterSnapshot = masterRecords.ToArray();
            var detailSnapshot = detailRecords.ToArray();
            Calls.Add((masterSnapshot, detailSnapshot));

            return SourceFamilyRepositoryRegistry.CreatePersistResult(
                ProviderName,
                masterSnapshot,
                detailSnapshot);
        }
    }
}
