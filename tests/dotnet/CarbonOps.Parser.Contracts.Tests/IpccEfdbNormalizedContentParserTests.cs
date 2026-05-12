using System.Text.Json;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class IpccEfdbNormalizedContentParserTests
{
    [Fact]
    public void IpccEfdbHeaderIsDeterministic()
    {
        using var expectations = LoadParityExpectations();

        Assert.Equal(
            JsonStringArray(expectations.RootElement.GetProperty("header")),
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
    public void ValidIpccEfdbContentMatchesSharedParityExpectations()
    {
        using var expectations = LoadParityExpectations();
        var root = expectations.RootElement;
        var request = CreateRequest();
        var result = IpccEfdbNormalizedContentParser.Parse(
            request,
            CreateContentMap("ipcc_efdb_sample_factors.csv"));
        var expectedRows = root.GetProperty("sample_rows").EnumerateArray().ToArray();

        Assert.Equal(
            root.GetProperty("sample_status").GetProperty("dotnet").GetString(),
            result.Status.ToString());
        Assert.Equal(
            JsonStringArray(root.GetProperty("sample_issue_codes")),
            result.ValidationIssues.Select(issue => issue.Code));
        Assert.Equal(expectedRows.Length, result.RowCount);

        for (var index = 0; index < expectedRows.Length; index++)
        {
            var expected = expectedRows[index];
            var actual = result.Rows[index];

            Assert.Equal(expected.GetProperty("row_identifier").GetString(), actual.RowIdentifier);
            Assert.Equal(expected.GetProperty("source_row_number").GetInt32(), actual.SourceRowNumber);
            Assert.Equal(expected.GetProperty("reporting_year").GetInt32(), actual.ReportingYear);
            Assert.Equal(JsonFieldArray(expected.GetProperty("fields")), actual.Fields);
        }
    }

    [Fact]
    public void MalformedIpccEfdbRowsReturnStructuredErrors()
    {
        using var expectations = LoadParityExpectations();
        var root = expectations.RootElement;
        var result = IpccEfdbNormalizedContentParser.Parse(
            CreateRequest(),
            CreateContentMap("ipcc_efdb_malformed_factors.csv"));

        Assert.Equal(
            root.GetProperty("malformed_status").GetProperty("dotnet").GetString(),
            result.Status.ToString());
        Assert.Equal(0, result.RowCount);
        Assert.Equal(
            root.GetProperty("malformed_issues")
                .EnumerateArray()
                .Select(issue => issue.GetProperty("code").GetString()),
            result.ValidationIssues.Select(issue => issue.Code));
        Assert.Equal(
            root.GetProperty("malformed_issues")
                .EnumerateArray()
                .Select(issue => issue.GetProperty("field_key").GetString()),
            result.ValidationIssues.Select(issue => issue.FieldKey));
        Assert.Equal(
            root.GetProperty("malformed_issues")
                .EnumerateArray()
                .Select(issue => (int?)issue.GetProperty("source_row_number").GetInt32()),
            result.ValidationIssues.Select(issue => issue.SourceRowNumber));
        Assert.Equal("year", result.ValidationIssues[0].Context.Single(context => context.Key == "raw_value").Value);
        Assert.Equal("not-a-number", result.ValidationIssues[1].Context.Single(context => context.Key == "raw_value").Value);
    }

    [Fact]
    public void UnsupportedIpccEfdbRowsAreSkippedWithWarnings()
    {
        using var expectations = LoadParityExpectations();
        var root = expectations.RootElement;
        var content = string.Join(
            "\n",
            [
                string.Join(",", IpccEfdbNormalizedContentParser.Header),
                "metadata,2006,efdb-v2024,IPCC-NOTE-001,Workbook note,0,none,Notes,,metadata,CO2,,,skip",
            ]);

        var result = IpccEfdbNormalizedContentParser.Parse(
            CreateRequest(),
            new Dictionary<string, string> { [ArtifactReference] = content });

        Assert.Equal(
            root.GetProperty("unsupported_only_status").GetProperty("dotnet").GetString(),
            result.Status.ToString());
        Assert.Equal(0, result.RowCount);
        Assert.Equal(
            JsonStringArray(root.GetProperty("unsupported_only_issue_codes")),
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

    private static JsonDocument LoadParityExpectations() =>
        JsonDocument.Parse(File.ReadAllText(Path.Combine(
            ParityFixtureDirectory(),
            "ipcc_efdb_normalized_output_expectations.json")));

    private static IReadOnlyList<string> JsonStringArray(JsonElement array) =>
        array.EnumerateArray().Select(item => item.GetString() ?? string.Empty).ToArray();

    private static IReadOnlyList<ParserNormalizedField> JsonFieldArray(JsonElement array) =>
        array
            .EnumerateArray()
            .Select(field =>
            {
                var values = field.EnumerateArray().ToArray();
                return new ParserNormalizedField(values[0].GetString() ?? string.Empty, values[1].GetString());
            })
            .ToArray();

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

    private static string ParityFixtureDirectory()
    {
        var directory = new DirectoryInfo(AppContext.BaseDirectory);
        while (directory is not null)
        {
            var fixtureDirectory = Path.Combine(directory.FullName, "tests", "fixtures", "parity");
            if (Directory.Exists(fixtureDirectory))
            {
                return fixtureDirectory;
            }

            directory = directory.Parent;
        }

        throw new DirectoryNotFoundException("Could not locate parity fixture directory.");
    }
}
