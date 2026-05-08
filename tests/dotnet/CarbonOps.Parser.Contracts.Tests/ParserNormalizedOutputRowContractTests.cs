using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class ParserNormalizedOutputRowContractTests
{
    [Fact]
    public void ValidNormalizedRowsCanBeConstructedForPhaseOneParserAdapters()
    {
        var batch = ParserNormalizedOutputRegistry.CreateDefaultDryRunBatch();

        Assert.Equal(3, batch.RowCount);
        Assert.Equal(
            [
                SourceFamily.GhgProtocol,
                SourceFamily.DefraDesnz,
                SourceFamily.IpccEfdb,
            ],
            batch.Rows.Select(row => row.SourceFamily));
        Assert.All(batch.Rows, row => Assert.True(row.Validate().IsValid));
    }

    [Fact]
    public void NormalizedRowSourceAndParserKeysAlignWithDescriptorRegistry()
    {
        var rows = ParserNormalizedOutputRegistry.CreateDefaultDryRunBatch().Rows;

        foreach (var row in rows)
        {
            Assert.True(ParserAdapterDescriptorRegistry.TryGetBySourceKey(row.SourceKey, out var descriptor));
            Assert.NotNull(descriptor);
            Assert.Equal(descriptor!.SourceFamily, row.SourceFamily);
            Assert.Equal(descriptor.ParserKey, row.ParserKey);
        }
    }

    [Fact]
    public void NormalizedRowsCarryExistingInputArtifactMetadata()
    {
        var artifacts = ParserInputArtifactRegistry.CreateDefaultDryRunBatch().Artifacts;
        var rows = ParserNormalizedOutputRegistry.CreateDefaultDryRunBatch().Rows;

        foreach (var pair in artifacts.Zip(rows))
        {
            var artifact = pair.First;
            var row = pair.Second;

            Assert.Equal(artifact.SourceFamily, row.SourceFamily);
            Assert.Equal(artifact.SourceKey, row.SourceKey);
            Assert.Equal(artifact.ParserKey, row.ParserKey);
            Assert.Equal(artifact.ArtifactReference, row.ArtifactReference);
            Assert.Equal($"{artifact.SourceKey}_normalized_row_1", row.RowIdentifier);
            Assert.Equal(1, row.SourceRowNumber);
            Assert.Equal(artifact.ReportingYear, row.ReportingYear);
        }
    }

    [Fact]
    public void NormalizedFieldOrderingIsDeterministic()
    {
        var row = ParserNormalizedOutputRegistry.CreateDefaultDryRunBatch().Rows[0];

        Assert.Equal(
            [
                "source_key",
                "artifact_reference",
                "parser_key",
            ],
            row.Fields.Select(field => field.Key));
        Assert.Equal(
            [
                row.SourceKey,
                row.ArtifactReference,
                row.ParserKey.Value,
            ],
            row.Fields.Select(field => field.Value));
    }

    [Fact]
    public void RequiredNormalizedRowMetadataFieldsRejectEmptyStrings()
    {
        var row = new ParserNormalizedOutputRow(
            SourceFamily.GhgProtocol,
            "",
            new ParserKey(""),
            " ",
            "",
            sourceRowNumber: 0,
            [
                new ParserNormalizedField("activity", "electricity"),
            ],
            reportingYear: 1800);

        var result = row.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            [
                "SourceKey is required.",
                "ParserKey is required.",
                "ArtifactReference is required.",
                "RowIdentifier is required.",
                "SourceRowNumber must be positive when provided.",
                "ReportingYear must be between 1990 and 2100 when provided.",
                "ParserKey must match the registered parser adapter descriptor.",
            ],
            result.Errors);
    }

    [Fact]
    public void NormalizedFieldKeysRejectEmptyStrings()
    {
        var descriptor = ParserAdapterDescriptorRegistry.Descriptors[0];
        var row = CreateRow(
            descriptor,
            "artifact-reference",
            [
                new ParserNormalizedField("", "value"),
                new ParserNormalizedField(" ", null),
            ]);

        var result = row.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            [
                "Fields[0].Key is required.",
                "Fields[1].Key is required.",
            ],
            result.Errors);
    }

    [Fact]
    public void NormalizedRowIssueValidationUsesExistingIssueMetadataRules()
    {
        var descriptor = ParserAdapterDescriptorRegistry.Descriptors[0];
        var row = new ParserNormalizedOutputRow(
            descriptor.SourceFamily,
            descriptor.SourceFamily.ToWireName(),
            descriptor.ParserKey,
            "artifact-reference",
            "row-1",
            sourceRowNumber: 1,
            [
                new ParserNormalizedField("activity", "electricity"),
            ],
            [
                new ParserRunIssue("", " ", (ParserRunIssueSeverity)999, " "),
            ]);

        var result = row.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            [
                "Issues[0].Code is required.",
                "Issues[0].Message is required.",
                "Issues[0].ParserRunIssueSeverity must be a defined parser run issue severity.",
                "Issues[0].Location must not be whitespace when provided.",
            ],
            result.Errors);
    }

    [Fact]
    public void RowAndBatchOrderingIsDeterministic()
    {
        var first = ParserNormalizedOutputRegistry.CreateDefaultDryRunBatch();
        var second = ParserNormalizedOutputRegistry.CreateDefaultDryRunBatch();

        Assert.NotSame(first, second);
        Assert.NotSame(first.Rows, second.Rows);
        Assert.Equal(
            first.Rows.Select(row => row.SourceKey),
            second.Rows.Select(row => row.SourceKey));
        Assert.Equal(
            first.Rows.Select(row => row.RowIdentifier),
            second.Rows.Select(row => row.RowIdentifier));
        Assert.Equal(
            ParserAdapterDescriptorRegistry.Descriptors.Select(descriptor => descriptor.SourceFamily),
            first.Rows.Select(row => row.SourceFamily));
        Assert.Equal(
            ParserAdapterDescriptorRegistry.Descriptors.Select(descriptor => descriptor.ParserKey),
            first.Rows.Select(row => row.ParserKey));
    }

    [Fact]
    public void NormalizedOutputBatchSnapshotsRows()
    {
        var rows = new List<ParserNormalizedOutputRow>
        {
            ParserNormalizedOutputRegistry.CreateDefaultDryRunBatch().Rows[0],
        };

        var batch = new ParserNormalizedOutputBatch(rows);
        rows.Clear();

        Assert.Equal(1, batch.RowCount);
        Assert.Single(batch.Rows);
        Assert.Equal(SourceFamily.GhgProtocol, batch.Rows[0].SourceFamily);
    }

    [Fact]
    public void NormalizedOutputRowSnapshotsFieldsAndIssues()
    {
        var descriptor = ParserAdapterDescriptorRegistry.Descriptors[1];
        var fields = new List<ParserNormalizedField>
        {
            new("activity", "electricity"),
        };
        var issues = new List<ParserRunIssue>
        {
            new("NORMALIZED_ROW_DRY_RUN", "Metadata-only normalized row.", ParserRunIssueSeverity.Warning),
        };

        var row = new ParserNormalizedOutputRow(
            descriptor.SourceFamily,
            descriptor.SourceFamily.ToWireName(),
            descriptor.ParserKey,
            "artifact-reference",
            "row-1",
            sourceRowNumber: 1,
            fields,
            issues);
        fields.Clear();
        issues.Clear();

        Assert.Equal([new ParserNormalizedField("activity", "electricity")], row.Fields);
        Assert.Equal(["NORMALIZED_ROW_DRY_RUN"], row.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void ValidationDoesNotReadFilesInspectContentAccessDbOrCallNetwork()
    {
        var descriptor = ParserAdapterDescriptorRegistry.Descriptors[1];
        var row = CreateRow(
            descriptor,
            "/definitely/not-present/defra-desnz-output.csv",
            [
                new ParserNormalizedField("source_payload_reference", "{not inspected json text}"),
                new ParserNormalizedField("factor_value", "not calculated"),
            ]);

        var result = row.Validate();

        Assert.True(result.IsValid);
        Assert.Empty(result.Errors);
    }

    [Fact]
    public void UnknownSourceMetadataFailsClearly()
    {
        var descriptor = ParserAdapterDescriptorRegistry.Descriptors[0];
        var row = new ParserNormalizedOutputRow(
            descriptor.SourceFamily,
            "unknown_source_family",
            descriptor.ParserKey,
            "artifact-reference",
            "row-1",
            sourceRowNumber: 1,
            [
                new ParserNormalizedField("activity", "electricity"),
            ]);

        var result = row.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            ["SourceKey must match a registered parser adapter descriptor."],
            result.Errors);
    }

    [Fact]
    public void DivergentParserMetadataFailsClearly()
    {
        var descriptor = ParserAdapterDescriptorRegistry.Descriptors[2];
        var row = new ParserNormalizedOutputRow(
            descriptor.SourceFamily,
            descriptor.SourceFamily.ToWireName(),
            ParserSelectionRegistry.GetParserKey(SourceFamily.GhgProtocol),
            "artifact-reference",
            "row-1",
            sourceRowNumber: 1,
            [
                new ParserNormalizedField("activity", "electricity"),
            ]);

        var result = row.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            ["ParserKey must match the registered parser adapter descriptor."],
            result.Errors);
    }

    [Fact]
    public void ConstructionRemainsRuntimePassive()
    {
        var rowMethods = typeof(ParserNormalizedOutputRow)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();
        var batchMethods = typeof(ParserNormalizedOutputBatch)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();
        var registryMethods = typeof(ParserNormalizedOutputRegistry)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();

        Assert.DoesNotContain("Parse", rowMethods);
        Assert.DoesNotContain("Execute", rowMethods);
        Assert.DoesNotContain("Parse", batchMethods);
        Assert.DoesNotContain("Execute", batchMethods);
        Assert.DoesNotContain("Parse", registryMethods);
        Assert.DoesNotContain("Execute", registryMethods);
    }

    [Fact]
    public void ContractDoesNotIntroduceDbHttpFileIoParserExecutionOrPersistenceMappingSurface()
    {
        var publicMembers = typeof(ParserNormalizedField)
            .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Concat(typeof(ParserNormalizedOutputRow)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Concat(typeof(ParserNormalizedOutputBatch)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Concat(typeof(ParserNormalizedOutputRegistry)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly))
            .Select(member => member.Name)
            .ToArray();
        var blockedTerms = new[]
        {
            "Db",
            "Sql",
            "Postgres",
            "Http",
            "Open",
            "Read",
            "Write",
            "Stat",
            "Exists",
            "Calculate",
            "Factor",
            "Persist",
            "Table",
            "Map",
        };

        foreach (var term in blockedTerms)
        {
            Assert.DoesNotContain(publicMembers, member => member.Contains(term, StringComparison.OrdinalIgnoreCase));
        }

        Assert.DoesNotContain("Parse", publicMembers);
        Assert.DoesNotContain("Execute", publicMembers);
    }

    private static ParserNormalizedOutputRow CreateRow(
        IParserAdapterDescriptor descriptor,
        string artifactReference,
        IEnumerable<ParserNormalizedField> fields) =>
        new(
            descriptor.SourceFamily,
            descriptor.SourceFamily.ToWireName(),
            descriptor.ParserKey,
            artifactReference,
            "row-1",
            sourceRowNumber: 1,
            fields);
}
