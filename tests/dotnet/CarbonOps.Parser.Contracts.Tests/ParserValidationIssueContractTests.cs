using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class ParserValidationIssueContractTests
{
    [Fact]
    public void ValidValidationIssuesCanBeConstructedForPhaseOneParserAdapters()
    {
        var batch = ParserValidationIssueRegistry.CreateDefaultDryRunBatch();

        Assert.Equal(3, batch.IssueCount);
        Assert.Equal(
            [
                SourceFamily.GhgProtocol,
                SourceFamily.DefraDesnz,
                SourceFamily.IpccEfdb,
            ],
            batch.Issues.Select(issue => issue.SourceFamily));
        Assert.All(batch.Issues, issue => Assert.True(issue.Validate().IsValid));
    }

    [Fact]
    public void ValidationIssueSourceAndParserKeysAlignWithDescriptorRegistry()
    {
        var issues = ParserValidationIssueRegistry.CreateDefaultDryRunBatch().Issues;

        foreach (var issue in issues)
        {
            Assert.True(ParserAdapterDescriptorRegistry.TryGetBySourceKey(issue.SourceKey, out var descriptor));
            Assert.NotNull(descriptor);
            Assert.Equal(descriptor!.SourceFamily, issue.SourceFamily);
            Assert.Equal(descriptor.ParserKey, issue.ParserKey);
        }
    }

    [Fact]
    public void ValidationIssuesCarryExistingNormalizedRowMetadata()
    {
        var rows = ParserNormalizedOutputRegistry.CreateDefaultDryRunBatch().Rows;
        var issues = ParserValidationIssueRegistry.CreateDefaultDryRunBatch().Issues;

        foreach (var pair in rows.Zip(issues))
        {
            var row = pair.First;
            var issue = pair.Second;

            Assert.Equal(row.SourceFamily, issue.SourceFamily);
            Assert.Equal(row.SourceKey, issue.SourceKey);
            Assert.Equal(row.ParserKey, issue.ParserKey);
            Assert.Equal(row.ArtifactReference, issue.ArtifactReference);
            Assert.Equal(row.RowIdentifier, issue.RowIdentifier);
            Assert.Equal(row.SourceRowNumber, issue.SourceRowNumber);
        }
    }

    [Fact]
    public void SeverityValuesAreConstrainedToDeterministicAllowedSet()
    {
        Assert.Equal(
            [
                ParserValidationIssueSeverity.Info,
                ParserValidationIssueSeverity.Warning,
                ParserValidationIssueSeverity.Error,
            ],
            Enum.GetValues<ParserValidationIssueSeverity>());
        Assert.Equal("info", ParserValidationIssueSeverity.Info.ToWireName());
        Assert.Equal("warning", ParserValidationIssueSeverity.Warning.ToWireName());
        Assert.Equal("error", ParserValidationIssueSeverity.Error.ToWireName());
        Assert.True(ContractWireNames.TryParseParserValidationIssueSeverityWireName("info", out var info));
        Assert.True(ContractWireNames.TryParseParserValidationIssueSeverityWireName("warning", out var warning));
        Assert.True(ContractWireNames.TryParseParserValidationIssueSeverityWireName("error", out var error));
        Assert.False(ContractWireNames.TryParseParserValidationIssueSeverityWireName("critical", out _));

        Assert.Equal(ParserValidationIssueSeverity.Info, info);
        Assert.Equal(ParserValidationIssueSeverity.Warning, warning);
        Assert.Equal(ParserValidationIssueSeverity.Error, error);
        Assert.Throws<ArgumentOutOfRangeException>(() => ((ParserValidationIssueSeverity)999).ToWireName());
    }

    [Fact]
    public void RequiredValidationIssueMetadataFieldsRejectEmptyStrings()
    {
        var issue = new ParserValidationIssue(
            SourceFamily.GhgProtocol,
            "",
            new ParserKey(""),
            (ParserValidationIssueSeverity)999,
            "",
            " ",
            artifactReference: " ",
            rowIdentifier: "",
            sourceRowNumber: 0,
            fieldKey: " ");

        var result = issue.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            [
                "SourceKey is required.",
                "ParserKey is required.",
                "ParserValidationIssueSeverity must be a defined parser validation issue severity.",
                "Code is required.",
                "Message is required.",
                "ArtifactReference must not be whitespace when provided.",
                "RowIdentifier must not be whitespace when provided.",
                "SourceRowNumber must be positive when provided.",
                "FieldKey must not be whitespace when provided.",
                "ParserKey must match the registered parser adapter descriptor.",
            ],
            result.Errors);
    }

    [Fact]
    public void ContextKeysRejectEmptyStrings()
    {
        var descriptor = ParserAdapterDescriptorRegistry.Descriptors[0];
        var issue = CreateIssue(
            descriptor,
            [
                new ParserValidationIssueContext("", "value"),
                new ParserValidationIssueContext(" ", null),
            ]);

        var result = issue.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            [
                "Context[0].Key is required.",
                "Context[1].Key is required.",
            ],
            result.Errors);
    }

    [Fact]
    public void IssueCollectionOrderingIsDeterministic()
    {
        var first = ParserValidationIssueRegistry.CreateDefaultDryRunBatch();
        var second = ParserValidationIssueRegistry.CreateDefaultDryRunBatch();

        Assert.NotSame(first, second);
        Assert.NotSame(first.Issues, second.Issues);
        Assert.Equal(
            first.Issues.Select(issue => issue.SourceKey),
            second.Issues.Select(issue => issue.SourceKey));
        Assert.Equal(
            first.Issues.Select(issue => issue.Code),
            second.Issues.Select(issue => issue.Code));
        Assert.Equal(
            ParserAdapterDescriptorRegistry.Descriptors.Select(descriptor => descriptor.SourceFamily),
            first.Issues.Select(issue => issue.SourceFamily));
        Assert.Equal(
            ParserAdapterDescriptorRegistry.Descriptors.Select(descriptor => descriptor.ParserKey),
            first.Issues.Select(issue => issue.ParserKey));
    }

    [Fact]
    public void ValidationIssueBatchSnapshotsIssues()
    {
        var issues = new List<ParserValidationIssue>
        {
            ParserValidationIssueRegistry.CreateDefaultDryRunBatch().Issues[0],
        };

        var batch = new ParserValidationIssueBatch(issues);
        issues.Clear();

        Assert.Equal(1, batch.IssueCount);
        Assert.Single(batch.Issues);
        Assert.Equal(SourceFamily.GhgProtocol, batch.Issues[0].SourceFamily);
    }

    [Fact]
    public void ValidationIssueSnapshotsContext()
    {
        var descriptor = ParserAdapterDescriptorRegistry.Descriptors[1];
        var context = new List<ParserValidationIssueContext>
        {
            new("artifact_reference", "defra_desnz_discovery_reference"),
        };

        var issue = CreateIssue(descriptor, context);
        context.Clear();

        Assert.Equal(
            [new ParserValidationIssueContext("artifact_reference", "defra_desnz_discovery_reference")],
            issue.Context);
    }

    [Fact]
    public void ValidationDoesNotReadFilesInspectContentAccessDbOrCallNetwork()
    {
        var descriptor = ParserAdapterDescriptorRegistry.Descriptors[1];
        var issue = new ParserValidationIssue(
            descriptor.SourceFamily,
            descriptor.SourceFamily.ToWireName(),
            descriptor.ParserKey,
            ParserValidationIssueSeverity.Warning,
            "PARSER_VALIDATION_METADATA_ONLY",
            "Diagnostic metadata only.",
            artifactReference: "/definitely/not-present/defra-desnz-input.csv",
            rowIdentifier: "row-1",
            sourceRowNumber: 1,
            fieldKey: "raw_json_text",
            context:
            [
                new ParserValidationIssueContext("source_payload_reference", "{not inspected json text}"),
                new ParserValidationIssueContext("factor_value", "not calculated"),
            ]);

        var result = issue.Validate();

        Assert.True(result.IsValid);
        Assert.Empty(result.Errors);
    }

    [Fact]
    public void UnknownSourceMetadataFailsClearly()
    {
        var descriptor = ParserAdapterDescriptorRegistry.Descriptors[0];
        var issue = new ParserValidationIssue(
            descriptor.SourceFamily,
            "unknown_source_family",
            descriptor.ParserKey,
            ParserValidationIssueSeverity.Error,
            "UNKNOWN_SOURCE",
            "Unknown source metadata.",
            artifactReference: "artifact-reference");

        var result = issue.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            ["SourceKey must match a registered parser adapter descriptor."],
            result.Errors);
    }

    [Fact]
    public void DivergentParserMetadataFailsClearly()
    {
        var descriptor = ParserAdapterDescriptorRegistry.Descriptors[2];
        var issue = new ParserValidationIssue(
            descriptor.SourceFamily,
            descriptor.SourceFamily.ToWireName(),
            ParserSelectionRegistry.GetParserKey(SourceFamily.GhgProtocol),
            ParserValidationIssueSeverity.Error,
            "DIVERGENT_PARSER",
            "Parser key does not match source metadata.",
            artifactReference: "artifact-reference");

        var result = issue.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            ["ParserKey must match the registered parser adapter descriptor."],
            result.Errors);
    }

    [Fact]
    public void ConstructionRemainsRuntimePassive()
    {
        var issueMethods = typeof(ParserValidationIssue)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();
        var batchMethods = typeof(ParserValidationIssueBatch)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();
        var registryMethods = typeof(ParserValidationIssueRegistry)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();

        Assert.DoesNotContain("Parse", issueMethods);
        Assert.DoesNotContain("Execute", issueMethods);
        Assert.DoesNotContain("Parse", batchMethods);
        Assert.DoesNotContain("Execute", batchMethods);
        Assert.DoesNotContain("Parse", registryMethods);
        Assert.DoesNotContain("Execute", registryMethods);
    }

    [Fact]
    public void ContractDoesNotIntroduceDbHttpFileIoParserExecutionOrPersistenceMappingSurface()
    {
        var publicMembers = typeof(ParserValidationIssueSeverity)
            .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Concat(typeof(ParserValidationIssueContext)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Concat(typeof(ParserValidationIssue)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Concat(typeof(ParserValidationIssueBatch)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Concat(typeof(ParserValidationIssueRegistry)
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

    private static ParserValidationIssue CreateIssue(
        IParserAdapterDescriptor descriptor,
        IEnumerable<ParserValidationIssueContext> context) =>
        new(
            descriptor.SourceFamily,
            descriptor.SourceFamily.ToWireName(),
            descriptor.ParserKey,
            ParserValidationIssueSeverity.Warning,
            "PARSER_VALIDATION_METADATA_ONLY",
            "Diagnostic metadata only.",
            artifactReference: "artifact-reference",
            rowIdentifier: "row-1",
            sourceRowNumber: 1,
            fieldKey: "activity",
            context: context);
}
