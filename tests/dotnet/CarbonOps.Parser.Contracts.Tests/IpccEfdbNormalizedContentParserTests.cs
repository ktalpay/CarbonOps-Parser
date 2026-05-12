using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class IpccEfdbNormalizedContentParserTests
{
    [Fact]
    public void IpccEfdbHeaderIsDeterministic()
    {
        Assert.Equal(
            [
                "record_type",
                "source_year",
                "source_version",
                "factor_id",
                "factor_name",
                "factor_value",
                "unit",
                "category",
                "subcategory",
                "ipcc_sector",
                "gas",
                "region",
                "technology",
                "provenance",
            ],
            IpccEfdbNormalizedContentParser.Header);
    }

    [Fact]
    public void ValidIpccEfdbContentReturnsNormalizedRows()
    {
        var request = CreateRequest();
        var result = IpccEfdbNormalizedContentParser.Parse(
            request,
            CreateContentMap("ipcc_efdb_sample_factors.csv"));

        Assert.Equal(ParserRunStatus.Completed, result.Status);
        Assert.Equal(2, result.RowCount);
        Assert.Single(result.ValidationIssues);
        Assert.True(result.Validate().IsValid);
        Assert.All(result.Rows, row => Assert.True(row.Validate().IsValid));
        Assert.Equal("IPCC_EFDB_CONTENT_UNSUPPORTED_ROW_SKIPPED", result.ValidationIssues[0].Code);
        Assert.Equal(ParserValidationIssueSeverity.Warning, result.ValidationIssues[0].Severity);

        var first = result.Rows[0];
        Assert.Equal(SourceFamily.IpccEfdb, first.SourceFamily);
        Assert.Equal("ipcc_efdb", first.SourceKey);
        Assert.Equal("ipcc_efdb_2006_efdb-v2024_IPCC-ENERGY-CO2_row_2", first.RowIdentifier);
        Assert.Equal(2, first.SourceRowNumber);
        Assert.Equal(2006, first.ReportingYear);
        Assert.Equal(
            [
                new ParserNormalizedField("source_family", "ipcc_efdb"),
                new ParserNormalizedField("source_year", "2006"),
                new ParserNormalizedField("source_version", "efdb-v2024"),
                new ParserNormalizedField("factor_id", "IPCC-ENERGY-CO2"),
                new ParserNormalizedField("factor_name", "Stationary combustion CO2"),
                new ParserNormalizedField("factor_value", "56.1"),
                new ParserNormalizedField("unit", "t CO2/TJ"),
                new ParserNormalizedField("category", "Energy"),
                new ParserNormalizedField("subcategory", "Stationary combustion"),
                new ParserNormalizedField("ipcc_sector", "1A"),
                new ParserNormalizedField("gas", "CO2"),
                new ParserNormalizedField("region", "Global"),
                new ParserNormalizedField("technology", "Default"),
                new ParserNormalizedField("provenance_artifact_reference", ArtifactReference),
                new ParserNormalizedField("provenance_checksum_algorithm", "sha256"),
                new ParserNormalizedField("provenance_checksum_value", ChecksumValue),
                new ParserNormalizedField("provenance_row_number", "2"),
                new ParserNormalizedField("provenance", "worksheet:EFDB row 12"),
                new ParserNormalizedField("source_family_master_id", "ipcc_master_2006_efdb-v2024_IPCC-ENERGY-CO2"),
                new ParserNormalizedField("source_family_detail_id", "ipcc_detail_2006_efdb-v2024_IPCC-ENERGY-CO2"),
                new ParserNormalizedField("master_external_key", "2006:efdb-v2024:IPCC-ENERGY-CO2"),
                new ParserNormalizedField("detail_external_key", "IPCC-ENERGY-CO2:t CO2/TJ:CO2:1A"),
            ],
            first.Fields);

        var second = result.Rows[1];
        Assert.Equal("ipcc_efdb_2019_efdb-v2024_IPCC-WASTE-CH4_row_4", second.RowIdentifier);
        Assert.Equal(2019, second.ReportingYear);
        Assert.Contains(new ParserNormalizedField("category", "Waste"), second.Fields);
        Assert.Contains(new ParserNormalizedField("ipcc_sector", "4D"), second.Fields);
    }

    [Fact]
    public void IpccEfdbParserIsDeterministicForFixtureInput()
    {
        var request = CreateRequest();
        var content = CreateContentMap("ipcc_efdb_sample_factors.csv");

        var first = IpccEfdbNormalizedContentParser.Parse(request, content);
        var second = IpccEfdbNormalizedContentParser.Parse(request, content);

        Assert.Equal(first, second);
        Assert.Equal(2, first.RowCount);
    }

    [Fact]
    public void MalformedIpccEfdbRowsReturnStructuredErrors()
    {
        var result = IpccEfdbNormalizedContentParser.Parse(
            CreateRequest(),
            CreateContentMap("ipcc_efdb_malformed_factors.csv"));

        Assert.Equal(ParserRunStatus.Failed, result.Status);
        Assert.Equal(0, result.RowCount);
        Assert.Equal(
            [
                "IPCC_EFDB_CONTENT_INVALID_SOURCE_YEAR",
                "IPCC_EFDB_CONTENT_INVALID_FACTOR_VALUE",
                "IPCC_EFDB_CONTENT_MISSING_REQUIRED_FIELD",
            ],
            result.ValidationIssues.Select(issue => issue.Code));
        Assert.Equal(
            [
                "source_year",
                "factor_value",
                "factor_id",
            ],
            result.ValidationIssues.Select(issue => issue.FieldKey));
        Assert.Equal(
            [
                (int?)2,
                (int?)3,
                (int?)4,
            ],
            result.ValidationIssues.Select(issue => issue.SourceRowNumber));
        Assert.Equal("year", result.ValidationIssues[0].Context.Single(context => context.Key == "raw_value").Value);
        Assert.Equal("not-a-number", result.ValidationIssues[1].Context.Single(context => context.Key == "raw_value").Value);
    }

    [Fact]
    public void UnsupportedIpccEfdbRowsAreSkippedWithWarnings()
    {
        var content = string.Join(
            "\n",
            [
                string.Join(",", IpccEfdbNormalizedContentParser.Header),
                "metadata,2006,efdb-v2024,IPCC-NOTE-001,Workbook note,0,none,Notes,,metadata,CO2,,,skip",
            ]);

        var result = IpccEfdbNormalizedContentParser.Parse(
            CreateRequest(),
            new Dictionary<string, string> { [ArtifactReference] = content });

        Assert.Equal(ParserRunStatus.Completed, result.Status);
        Assert.Equal(0, result.RowCount);
        Assert.Equal(
            [
                "IPCC_EFDB_CONTENT_UNSUPPORTED_ROW_SKIPPED",
                "IPCC_EFDB_CONTENT_NO_RECORDS",
            ],
            result.ValidationIssues.Select(issue => issue.Code));
        Assert.Equal(ParserValidationIssueSeverity.Warning, result.ValidationIssues[0].Severity);
        Assert.Equal("record_type", result.ValidationIssues[0].FieldKey);
    }

    [Fact]
    public void InvalidIpccEfdbHeaderReturnsFailedIssue()
    {
        var result = IpccEfdbNormalizedContentParser.Parse(
            CreateRequest(),
            new Dictionary<string, string> { [ArtifactReference] = "record_type,source_year\nemission_factor,2006\n" });

        Assert.Equal(ParserRunStatus.Failed, result.Status);
        Assert.Equal("IPCC_EFDB_CONTENT_INVALID_HEADER", result.ValidationIssues[0].Code);
        Assert.Equal("header", result.ValidationIssues[0].FieldKey);
    }

    [Fact]
    public void NonIpccSourceFamilyReturnsFailedIssue()
    {
        var parserKey = ParserSelectionRegistry.GetParserKey(SourceFamily.GhgProtocol);
        var artifact = new ParserInputArtifact(
            SourceFamily.GhgProtocol,
            SourceFamily.GhgProtocol.ToWireName(),
            parserKey,
            ParserSourceFormat.DiscoveryReference,
            ArtifactReference,
            "ipcc_efdb_sample_factors.csv",
            "sha256",
            ChecksumValue,
            isDryRunChecksum: false,
            "text/csv",
            ".csv",
            2024);
        var request = new ParserAdapterRunRequest(
            SourceFamily.GhgProtocol,
            SourceFamily.GhgProtocol.ToWireName(),
            parserKey,
            [artifact],
            requestedReportingYear: 2024);

        var result = IpccEfdbNormalizedContentParser.Parse(
            request,
            CreateContentMap("ipcc_efdb_sample_factors.csv"));

        Assert.Equal(ParserRunStatus.Failed, result.Status);
        Assert.Equal("IPCC_EFDB_CONTENT_SOURCE_FAMILY_MISMATCH", result.ValidationIssues[0].Code);
        Assert.Equal("source_family", result.ValidationIssues[0].FieldKey);
    }

    private const string ArtifactReference = "tests/fixtures/source_documents/ipcc_efdb/ipcc_efdb_sample_factors.csv";
    private const string ChecksumValue = "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd";

    private static ParserAdapterRunRequest CreateRequest()
    {
        var parserKey = ParserSelectionRegistry.GetParserKey(SourceFamily.IpccEfdb);
        var artifact = new ParserInputArtifact(
            SourceFamily.IpccEfdb,
            SourceFamily.IpccEfdb.ToWireName(),
            parserKey,
            ParserSourceFormat.DiscoveryReference,
            ArtifactReference,
            "ipcc_efdb_sample_factors.csv",
            "sha256",
            ChecksumValue,
            isDryRunChecksum: false,
            "text/csv",
            ".csv",
            2024);

        return new ParserAdapterRunRequest(
            SourceFamily.IpccEfdb,
            SourceFamily.IpccEfdb.ToWireName(),
            parserKey,
            [artifact],
            requestedReportingYear: 2024);
    }

    private static IReadOnlyDictionary<string, string> CreateContentMap(string fixtureName) =>
        new Dictionary<string, string>
        {
            [ArtifactReference] = File.ReadAllText(Path.Combine(FixtureDirectory(), fixtureName)),
        };

    private static string FixtureDirectory()
    {
        var directory = new DirectoryInfo(AppContext.BaseDirectory);
        while (directory is not null)
        {
            var fixtureDirectory = Path.Combine(
                directory.FullName,
                "tests",
                "fixtures",
                "source_documents",
                "ipcc_efdb");
            if (Directory.Exists(fixtureDirectory))
            {
                return fixtureDirectory;
            }

            directory = directory.Parent;
        }

        throw new DirectoryNotFoundException("Could not locate IPCC EFDB fixture directory.");
    }
}
