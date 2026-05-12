using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class DefraDesnzNormalizedContentParserTests
{
    [Fact]
    public void DefraDesnzHeaderIsDeterministic()
    {
        Assert.Equal(
            [
                "source_year",
                "source_version",
                "category",
                "subcategory",
                "activity",
                "factor_id",
                "factor_name",
                "factor_value",
                "unit",
                "greenhouse_gas",
                "provenance",
            ],
            DefraDesnzNormalizedContentParser.Header);
    }

    [Fact]
    public void ValidDefraDesnzContentReturnsNormalizedRows()
    {
        var request = CreateRequest();
        var result = DefraDesnzNormalizedContentParser.Parse(
            request,
            CreateContentMap("defra_desnz_normalized_factors.csv"));

        Assert.Equal(ParserRunStatus.Completed, result.Status);
        Assert.Equal(2, result.RowCount);
        Assert.Empty(result.ValidationIssues);
        Assert.True(result.Validate().IsValid);
        Assert.All(result.Rows, row => Assert.True(row.Validate().IsValid));

        var first = result.Rows[0];
        Assert.Equal(SourceFamily.DefraDesnz, first.SourceFamily);
        Assert.Equal("defra_desnz", first.SourceKey);
        Assert.Equal("defra_desnz_2024_conversion-factors-2024_DEFRA-2024-ELEC_row_2", first.RowIdentifier);
        Assert.Equal(2, first.SourceRowNumber);
        Assert.Equal(2024, first.ReportingYear);
        Assert.Equal(
            [
                new ParserNormalizedField("source_family", "defra_desnz"),
                new ParserNormalizedField("source_year", "2024"),
                new ParserNormalizedField("source_version", "conversion-factors-2024"),
                new ParserNormalizedField("factor_id", "DEFRA-2024-ELEC"),
                new ParserNormalizedField("factor_name", "Electricity generated"),
                new ParserNormalizedField("factor_value", "0.20705"),
                new ParserNormalizedField("unit", "kWh"),
                new ParserNormalizedField("category", "Energy"),
                new ParserNormalizedField("subcategory", "Electricity"),
                new ParserNormalizedField("activity", "Generated"),
                new ParserNormalizedField("greenhouse_gas", "CO2e"),
                new ParserNormalizedField("provenance_artifact_reference", ArtifactReference),
                new ParserNormalizedField("provenance_checksum_algorithm", "sha256"),
                new ParserNormalizedField("provenance_checksum_value", ChecksumValue),
                new ParserNormalizedField("provenance_row_number", "2"),
                new ParserNormalizedField("provenance", "worksheet:UK electricity row 10"),
                new ParserNormalizedField("source_family_master_id", "defra_master_2024_conversion-factors-2024_DEFRA-2024-ELEC"),
                new ParserNormalizedField("source_family_detail_id", "defra_detail_2024_conversion-factors-2024_DEFRA-2024-ELEC"),
                new ParserNormalizedField("master_external_key", "2024:conversion-factors-2024:DEFRA-2024-ELEC"),
                new ParserNormalizedField("detail_external_key", "DEFRA-2024-ELEC:kWh:CO2e"),
            ],
            first.Fields);
    }

    [Fact]
    public void DefraDesnzParserIsDeterministicForFixtureInput()
    {
        var request = CreateRequest();
        var content = CreateContentMap("defra_desnz_normalized_factors.csv");

        var first = DefraDesnzNormalizedContentParser.Parse(request, content);
        var second = DefraDesnzNormalizedContentParser.Parse(request, content);

        Assert.Equal(first, second);
        Assert.Equal(2, first.RowCount);
    }

    [Fact]
    public void MalformedDefraDesnzRowsReturnStructuredErrors()
    {
        var result = DefraDesnzNormalizedContentParser.Parse(
            CreateRequest(),
            CreateContentMap("defra_desnz_malformed_factors.csv"));

        Assert.Equal(ParserRunStatus.Failed, result.Status);
        Assert.Equal(0, result.RowCount);
        Assert.Equal(
            [
                "DEFRA_DESNZ_CONTENT_INVALID_FACTOR_VALUE",
                "DEFRA_DESNZ_CONTENT_MISSING_REQUIRED_FIELD",
            ],
            result.ValidationIssues.Select(issue => issue.Code));
        Assert.Equal(
            [
                "factor_value",
                "unit",
            ],
            result.ValidationIssues.Select(issue => issue.FieldKey));
        Assert.Equal(
            new int?[]
            {
                2,
                3,
            },
            result.ValidationIssues.Select(issue => issue.SourceRowNumber));
        Assert.Equal("not-a-number", result.ValidationIssues[0].Context.Single(context => context.Key == "raw_value").Value);
    }

    [Fact]
    public void InvalidDefraDesnzHeaderReturnsFailedIssue()
    {
        var result = DefraDesnzNormalizedContentParser.Parse(
            CreateRequest(),
            new Dictionary<string, string> { [ArtifactReference] = "source_year,wrong\n2024,value\n" });

        Assert.Equal(ParserRunStatus.Failed, result.Status);
        Assert.Equal("DEFRA_DESNZ_CONTENT_INVALID_HEADER", result.ValidationIssues[0].Code);
        Assert.Equal("header", result.ValidationIssues[0].FieldKey);
    }

    [Fact]
    public void NonDefraSourceFamilyReturnsFailedIssue()
    {
        var parserKey = ParserSelectionRegistry.GetParserKey(SourceFamily.GhgProtocol);
        var artifact = new ParserInputArtifact(
            SourceFamily.GhgProtocol,
            SourceFamily.GhgProtocol.ToWireName(),
            parserKey,
            ParserSourceFormat.DiscoveryReference,
            ArtifactReference,
            "defra_desnz_normalized_factors.csv",
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

        var result = DefraDesnzNormalizedContentParser.Parse(
            request,
            CreateContentMap("defra_desnz_normalized_factors.csv"));

        Assert.Equal(ParserRunStatus.Failed, result.Status);
        Assert.Equal("DEFRA_DESNZ_CONTENT_SOURCE_FAMILY_MISMATCH", result.ValidationIssues[0].Code);
        Assert.Equal("source_family", result.ValidationIssues[0].FieldKey);
    }

    private const string ArtifactReference = "tests/fixtures/source_documents/defra_desnz/defra_desnz_normalized_factors.csv";
    private const string ChecksumValue = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";

    private static ParserAdapterRunRequest CreateRequest()
    {
        var parserKey = ParserSelectionRegistry.GetParserKey(SourceFamily.DefraDesnz);
        var artifact = new ParserInputArtifact(
            SourceFamily.DefraDesnz,
            SourceFamily.DefraDesnz.ToWireName(),
            parserKey,
            ParserSourceFormat.DiscoveryReference,
            ArtifactReference,
            "defra_desnz_normalized_factors.csv",
            "sha256",
            ChecksumValue,
            isDryRunChecksum: false,
            "text/csv",
            ".csv",
            2024);

        return new ParserAdapterRunRequest(
            SourceFamily.DefraDesnz,
            SourceFamily.DefraDesnz.ToWireName(),
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
                "defra_desnz");
            if (Directory.Exists(fixtureDirectory))
            {
                return fixtureDirectory;
            }

            directory = directory.Parent;
        }

        throw new DirectoryNotFoundException("Could not locate DEFRA/DESNZ fixture directory.");
    }
}
