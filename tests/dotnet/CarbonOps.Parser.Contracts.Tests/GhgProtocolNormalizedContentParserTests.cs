using System.Text.Json;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class GhgProtocolNormalizedContentParserTests
{
    [Fact]
    public void GhgProtocolHeaderIsDeterministic()
    {
        using var expectations = LoadParityExpectations();

        Assert.Equal(
            JsonStringArray(expectations.RootElement.GetProperty("header")),
            GhgProtocolNormalizedContentParser.Header);
    }

    [Fact]
    public void ValidGhgProtocolContentReturnsNormalizedRows()
    {
        var request = CreateRequest();
        var result = GhgProtocolNormalizedContentParser.Parse(
            request,
            CreateContentMap("ghg_protocol_sample_factors.csv"));

        Assert.Equal(ParserRunStatus.Completed, result.Status);
        Assert.Equal(2, result.RowCount);
        Assert.Single(result.ValidationIssues);
        Assert.True(result.Validate().IsValid);
        Assert.All(result.Rows, row => Assert.True(row.Validate().IsValid));
        Assert.Equal("GHG_PROTOCOL_CONTENT_UNSUPPORTED_ROW_SKIPPED", result.ValidationIssues[0].Code);
        Assert.Equal(ParserValidationIssueSeverity.Warning, result.ValidationIssues[0].Severity);

        var first = result.Rows[0];
        Assert.Equal(SourceFamily.GhgProtocol, first.SourceFamily);
        Assert.Equal("ghg_protocol", first.SourceKey);
        Assert.Equal("ghg_protocol_2024_v1_GHG-ELEC-001_row_2", first.RowIdentifier);
        Assert.Equal(2, first.SourceRowNumber);
        Assert.Equal(2024, first.ReportingYear);
        Assert.Equal(
            [
                new ParserNormalizedField("source_family", "ghg_protocol"),
                new ParserNormalizedField("source_year", "2024"),
                new ParserNormalizedField("source_version", "v1"),
                new ParserNormalizedField("factor_id", "GHG-ELEC-001"),
                new ParserNormalizedField("factor_name", "Grid electricity"),
                new ParserNormalizedField("factor_value", "0.233"),
                new ParserNormalizedField("unit", "kg CO2e/kWh"),
                new ParserNormalizedField("category", "Stationary combustion"),
                new ParserNormalizedField("subcategory", "Electricity"),
                new ParserNormalizedField("scope", "Scope 2"),
                new ParserNormalizedField("gas", "CO2e"),
                new ParserNormalizedField("provenance_artifact_reference", ArtifactReference),
                new ParserNormalizedField("provenance_checksum_algorithm", "sha256"),
                new ParserNormalizedField("provenance_checksum_value", ChecksumValue),
                new ParserNormalizedField("provenance_row_number", "2"),
                new ParserNormalizedField("provenance_note", "fixture row 1"),
                new ParserNormalizedField("source_family_master_id", "ghg_master_2024_v1_GHG-ELEC-001"),
                new ParserNormalizedField("source_family_detail_id", "ghg_detail_2024_v1_GHG-ELEC-001"),
                new ParserNormalizedField("master_external_key", "2024:v1:GHG-ELEC-001"),
                new ParserNormalizedField("detail_external_key", "GHG-ELEC-001:kg CO2e/kWh"),
            ],
            first.Fields);
    }

    [Fact]
    public void ValidGhgProtocolContentMatchesSharedParityExpectations()
    {
        using var expectations = LoadParityExpectations();
        var root = expectations.RootElement;
        var request = CreateRequest();
        var result = GhgProtocolNormalizedContentParser.Parse(
            request,
            CreateContentMap("ghg_protocol_sample_factors.csv"));
        var expectedRows = root.GetProperty("sample_rows").EnumerateArray().ToArray();

        Assert.Equal(root.GetProperty("sample_status").GetProperty("dotnet").GetString(), result.Status.ToString());
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
    public void GhgProtocolParserIsDeterministicForFixtureInput()
    {
        var request = CreateRequest();
        var content = CreateContentMap("ghg_protocol_sample_factors.csv");

        var first = GhgProtocolNormalizedContentParser.Parse(request, content);
        var second = GhgProtocolNormalizedContentParser.Parse(request, content);

        Assert.Equal(first, second);
        Assert.Equal(2, first.RowCount);
    }

    [Fact]
    public void MalformedGhgProtocolRowsReturnStructuredErrors()
    {
        using var expectations = LoadParityExpectations();
        var root = expectations.RootElement;
        var result = GhgProtocolNormalizedContentParser.Parse(
            CreateRequest(),
            CreateContentMap("ghg_protocol_malformed_factors.csv"));

        Assert.Equal(root.GetProperty("malformed_status").GetProperty("dotnet").GetString(), result.Status.ToString());
        Assert.Equal(0, result.RowCount);
        Assert.Equal(
            root.GetProperty("malformed_issues").EnumerateArray().Select(issue => issue.GetProperty("code").GetString()),
            result.ValidationIssues.Select(issue => issue.Code));
        Assert.Equal(
            root.GetProperty("malformed_issues").EnumerateArray().Select(issue => issue.GetProperty("field_key").GetString()),
            result.ValidationIssues.Select(issue => issue.FieldKey));
        Assert.Equal(
            root.GetProperty("malformed_issues").EnumerateArray().Select(issue => (int?)issue.GetProperty("source_row_number").GetInt32()),
            result.ValidationIssues.Select(issue => issue.SourceRowNumber));
    }

    [Fact]
    public void UnsupportedGhgProtocolRowsAreSkippedWithWarnings()
    {
        using var expectations = LoadParityExpectations();
        var root = expectations.RootElement;
        var content = string.Join(
            "\n",
            [
                string.Join(",", GhgProtocolNormalizedContentParser.Header),
                "metadata,2024,v1,NOTE-001,Workbook note,0,none,Notes,,,,skip",
            ]);

        var result = GhgProtocolNormalizedContentParser.Parse(
            CreateRequest(),
            new Dictionary<string, string> { [ArtifactReference] = content });

        Assert.Equal(root.GetProperty("unsupported_only_status").GetProperty("dotnet").GetString(), result.Status.ToString());
        Assert.Equal(0, result.RowCount);
        Assert.Equal(
            JsonStringArray(root.GetProperty("unsupported_only_issue_codes")),
            result.ValidationIssues.Select(issue => issue.Code));
        Assert.Equal(ParserValidationIssueSeverity.Warning, result.ValidationIssues[0].Severity);
        Assert.Equal("record_type", result.ValidationIssues[0].FieldKey);
    }

    [Fact]
    public void InvalidGhgProtocolHeaderReturnsFailedIssue()
    {
        var result = GhgProtocolNormalizedContentParser.Parse(
            CreateRequest(),
            new Dictionary<string, string> { [ArtifactReference] = "record_type,source_year\nemission_factor,2024\n" });

        Assert.Equal(ParserRunStatus.Failed, result.Status);
        Assert.Equal("GHG_PROTOCOL_CONTENT_INVALID_HEADER", result.ValidationIssues[0].Code);
        Assert.Equal("header", result.ValidationIssues[0].FieldKey);
    }

    private const string ArtifactReference = "tests/fixtures/source_documents/ghg_protocol/ghg_protocol_sample_factors.csv";
    private const string ChecksumValue = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";

    private static ParserAdapterRunRequest CreateRequest()
    {
        var parserKey = ParserSelectionRegistry.GetParserKey(SourceFamily.GhgProtocol);
        var artifact = new ParserInputArtifact(
            SourceFamily.GhgProtocol,
            SourceFamily.GhgProtocol.ToWireName(),
            parserKey,
            ParserSourceFormat.DiscoveryReference,
            ArtifactReference,
            "ghg_protocol_sample_factors.csv",
            "sha256",
            ChecksumValue,
            isDryRunChecksum: false,
            "text/csv",
            ".csv",
            2024);

        return new ParserAdapterRunRequest(
            SourceFamily.GhgProtocol,
            SourceFamily.GhgProtocol.ToWireName(),
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
        JsonDocument.Parse(File.ReadAllText(Path.Combine(ParityFixtureDirectory(), "ghg_protocol_normalized_output_expectations.json")));

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
                "ghg_protocol");
            if (Directory.Exists(fixtureDirectory))
            {
                return fixtureDirectory;
            }

            directory = directory.Parent;
        }

        throw new DirectoryNotFoundException("Could not locate GHG Protocol fixture directory.");
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
