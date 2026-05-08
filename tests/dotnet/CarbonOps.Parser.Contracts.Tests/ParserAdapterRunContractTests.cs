using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class ParserAdapterRunContractTests
{
    [Fact]
    public void ValidParserRunRequestsCanBeConstructedForPhaseOneParserAdapters()
    {
        var batch = ParserAdapterRunRegistry.CreateDefaultDryRunRequestBatch();

        Assert.Equal(3, batch.RequestCount);
        Assert.Equal(
            [
                SourceFamily.GhgProtocol,
                SourceFamily.DefraDesnz,
                SourceFamily.IpccEfdb,
            ],
            batch.Requests.Select(request => request.SourceFamily));
        Assert.All(batch.Requests, request => Assert.True(request.Validate().IsValid));
    }

    [Fact]
    public void ValidParserRunResultsCanBeConstructedForPhaseOneParserAdapters()
    {
        var batch = ParserAdapterRunRegistry.CreateDefaultDryRunResultBatch();

        Assert.Equal(3, batch.ResultCount);
        Assert.Equal(
            [
                SourceFamily.GhgProtocol,
                SourceFamily.DefraDesnz,
                SourceFamily.IpccEfdb,
            ],
            batch.Results.Select(result => result.SourceFamily));
        Assert.All(batch.Results, result => Assert.True(result.Validate().IsValid));
    }

    [Fact]
    public void RequestArtifactsAlignWithDescriptorRegistrySourceAndParserKeys()
    {
        var requests = ParserAdapterRunRegistry.CreateDefaultDryRunRequestBatch().Requests;

        foreach (var request in requests)
        {
            Assert.True(ParserAdapterDescriptorRegistry.TryGetBySourceKey(request.SourceKey, out var descriptor));
            Assert.NotNull(descriptor);
            Assert.Equal(descriptor!.SourceFamily, request.SourceFamily);
            Assert.Equal(descriptor.ParserKey, request.ParserKey);
            Assert.All(
                request.Artifacts,
                artifact =>
                {
                    Assert.Equal(request.SourceFamily, artifact.SourceFamily);
                    Assert.Equal(request.SourceKey, artifact.SourceKey);
                    Assert.Equal(request.ParserKey, artifact.ParserKey);
                });
        }
    }

    [Fact]
    public void ResultRowsAndValidationIssuesAlignWithDescriptorRegistrySourceAndParserKeys()
    {
        var results = ParserAdapterRunRegistry.CreateDefaultDryRunResultBatch().Results;

        foreach (var result in results)
        {
            Assert.True(ParserAdapterDescriptorRegistry.TryGetBySourceKey(result.SourceKey, out var descriptor));
            Assert.NotNull(descriptor);
            Assert.Equal(descriptor!.SourceFamily, result.SourceFamily);
            Assert.Equal(descriptor.ParserKey, result.ParserKey);
            Assert.All(
                result.Rows,
                row =>
                {
                    Assert.Equal(result.SourceFamily, row.SourceFamily);
                    Assert.Equal(result.SourceKey, row.SourceKey);
                    Assert.Equal(result.ParserKey, row.ParserKey);
                });
            Assert.All(
                result.ValidationIssues,
                issue =>
                {
                    Assert.Equal(result.SourceFamily, issue.SourceFamily);
                    Assert.Equal(result.SourceKey, issue.SourceKey);
                    Assert.Equal(result.ParserKey, issue.ParserKey);
                });
        }
    }

    [Fact]
    public void RunStatusValuesAreConstrainedToDeterministicAllowedSet()
    {
        Assert.Equal(
            [
                ParserRunStatus.Pending,
                ParserRunStatus.Running,
                ParserRunStatus.Completed,
                ParserRunStatus.Failed,
            ],
            Enum.GetValues<ParserRunStatus>());
        Assert.Equal(
            [
                "pending",
                "running",
                "completed",
                "failed",
            ],
            Enum.GetValues<ParserRunStatus>().Select(status => status.ToWireName()));
        Assert.False(ContractWireNames.TryParseParserRunStatusWireName("cancelled", out _));
        Assert.Throws<ArgumentOutOfRangeException>(() => ((ParserRunStatus)999).ToWireName());
    }

    [Fact]
    public void RequiredRequestMetadataFieldsRejectEmptyStrings()
    {
        var request = new ParserAdapterRunRequest(
            SourceFamily.GhgProtocol,
            "",
            new ParserKey(""),
            [],
            runId: " ",
            correlationId: "",
            requestedReportingYear: 1800);

        var result = request.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            [
                "SourceKey is required.",
                "ParserKey is required.",
                "ParserAdapterRunRequest must include at least one input artifact.",
                "RunId must not be whitespace when provided.",
                "CorrelationId must not be whitespace when provided.",
                "RequestedReportingYear must be between 1990 and 2100 when provided.",
            ],
            result.Errors);
    }

    [Fact]
    public void RequiredResultMetadataFieldsRejectEmptyStrings()
    {
        var result = new ParserAdapterRunResult(
            SourceFamily.GhgProtocol,
            "",
            new ParserKey(""),
            (ParserRunStatus)999,
            [" "],
            [],
            [],
            runId: "",
            correlationId: " ",
            reportingYear: 1800);

        var validation = result.Validate();

        Assert.False(validation.IsValid);
        Assert.Equal(
            [
                "SourceKey is required.",
                "ParserKey is required.",
                "ParserRunStatus must be a defined parser run status.",
                "RunId must not be whitespace when provided.",
                "CorrelationId must not be whitespace when provided.",
                "ReportingYear must be between 1990 and 2100 when provided.",
                "ArtifactReferences[0] is required.",
            ],
            validation.Errors);
    }

    [Fact]
    public void RequestValidationRejectsArtifactsThatDoNotAlignWithRequestMetadata()
    {
        var request = ParserAdapterRunRegistry.CreateDefaultDryRunRequestBatch().Requests[0];
        var mismatchedArtifact = ParserInputArtifactRegistry.CreateDefaultDryRunBatch().Artifacts[1];
        var mismatchedRequest = new ParserAdapterRunRequest(
            request.SourceFamily,
            request.SourceKey,
            request.ParserKey,
            [mismatchedArtifact]);

        var result = mismatchedRequest.Validate();

        Assert.False(result.IsValid);
        Assert.Equal(
            [
                "Artifacts[0].SourceFamily must match request SourceFamily.",
                "Artifacts[0].SourceKey must match request SourceKey.",
                "Artifacts[0].ParserKey must match request ParserKey.",
            ],
            result.Errors);
    }

    [Fact]
    public void ResultValidationRejectsRowsAndIssuesThatDoNotAlignWithResultMetadata()
    {
        var result = ParserAdapterRunRegistry.CreateDefaultDryRunResultBatch().Results[0];
        var mismatchedRow = ParserNormalizedOutputRegistry.CreateDefaultDryRunBatch().Rows[1];
        var mismatchedIssue = ParserValidationIssueRegistry.CreateDefaultDryRunBatch().Issues[1];
        var mismatchedResult = new ParserAdapterRunResult(
            result.SourceFamily,
            result.SourceKey,
            result.ParserKey,
            ParserRunStatus.Pending,
            result.ArtifactReferences,
            [mismatchedRow],
            [mismatchedIssue]);

        var validation = mismatchedResult.Validate();

        Assert.False(validation.IsValid);
        Assert.Equal(
            [
                "Rows[0].SourceFamily must match result SourceFamily.",
                "Rows[0].SourceKey must match result SourceKey.",
                "Rows[0].ParserKey must match result ParserKey.",
                "ValidationIssues[0].SourceFamily must match result SourceFamily.",
                "ValidationIssues[0].SourceKey must match result SourceKey.",
                "ValidationIssues[0].ParserKey must match result ParserKey.",
            ],
            validation.Errors);
    }

    [Fact]
    public void SummaryCountsAreDeterministicMetadata()
    {
        var request = ParserAdapterRunRegistry.CreateDefaultDryRunRequestBatch().Requests[0];
        var result = ParserAdapterRunRegistry.CreateDefaultDryRunResultBatch().Results[0];

        Assert.Equal(request.Artifacts.Count, request.ArtifactCount);
        Assert.Equal(result.ArtifactReferences.Count, result.ArtifactCount);
        Assert.Equal(result.Rows.Count, result.RowCount);
        Assert.Equal(result.ValidationIssues.Count, result.IssueCount);
        Assert.Equal(1, request.ArtifactCount);
        Assert.Equal(1, result.ArtifactCount);
        Assert.Equal(1, result.RowCount);
        Assert.Equal(1, result.IssueCount);
    }

    [Fact]
    public void OrderingOfArtifactsRowsAndIssuesIsDeterministic()
    {
        var firstRequests = ParserAdapterRunRegistry.CreateDefaultDryRunRequestBatch();
        var secondRequests = ParserAdapterRunRegistry.CreateDefaultDryRunRequestBatch();
        var firstResults = ParserAdapterRunRegistry.CreateDefaultDryRunResultBatch();
        var secondResults = ParserAdapterRunRegistry.CreateDefaultDryRunResultBatch();

        Assert.Equal(
            firstRequests.Requests.Select(request => request.SourceKey),
            secondRequests.Requests.Select(request => request.SourceKey));
        Assert.Equal(
            firstResults.Results.Select(result => result.SourceKey),
            secondResults.Results.Select(result => result.SourceKey));
        Assert.Equal(
            ParserAdapterDescriptorRegistry.Descriptors.Select(descriptor => descriptor.SourceFamily),
            firstRequests.Requests.Select(request => request.SourceFamily));
        Assert.Equal(
            ParserAdapterDescriptorRegistry.Descriptors.Select(descriptor => descriptor.SourceFamily),
            firstResults.Results.Select(result => result.SourceFamily));
        Assert.Equal(
            firstResults.Results.Select(result => result.Rows[0].RowIdentifier),
            secondResults.Results.Select(result => result.Rows[0].RowIdentifier));
        Assert.Equal(
            firstResults.Results.Select(result => result.ValidationIssues[0].Code),
            secondResults.Results.Select(result => result.ValidationIssues[0].Code));
    }

    [Fact]
    public void RequestAndResultBatchesSnapshotCollections()
    {
        var requests = new List<ParserAdapterRunRequest>
        {
            ParserAdapterRunRegistry.CreateDefaultDryRunRequestBatch().Requests[0],
        };
        var results = new List<ParserAdapterRunResult>
        {
            ParserAdapterRunRegistry.CreateDefaultDryRunResultBatch().Results[0],
        };

        var requestBatch = new ParserAdapterRunRequestBatch(requests);
        var resultBatch = new ParserAdapterRunResultBatch(results);
        requests.Clear();
        results.Clear();

        Assert.Equal(1, requestBatch.RequestCount);
        Assert.Equal(1, resultBatch.ResultCount);
        Assert.Single(requestBatch.Requests);
        Assert.Single(resultBatch.Results);
    }

    [Fact]
    public void RequestAndResultSnapshotNestedCollections()
    {
        var artifact = ParserInputArtifactRegistry.CreateDefaultDryRunBatch().Artifacts[0];
        var row = ParserNormalizedOutputRegistry.CreateDefaultDryRunBatch().Rows[0];
        var issue = ParserValidationIssueRegistry.CreateDefaultDryRunBatch().Issues[0];
        var artifacts = new List<ParserInputArtifact> { artifact };
        var artifactReferences = new List<string> { artifact.ArtifactReference };
        var rows = new List<ParserNormalizedOutputRow> { row };
        var issues = new List<ParserValidationIssue> { issue };

        var request = new ParserAdapterRunRequest(
            artifact.SourceFamily,
            artifact.SourceKey,
            artifact.ParserKey,
            artifacts);
        var result = new ParserAdapterRunResult(
            artifact.SourceFamily,
            artifact.SourceKey,
            artifact.ParserKey,
            ParserRunStatus.Pending,
            artifactReferences,
            rows,
            issues);
        artifacts.Clear();
        artifactReferences.Clear();
        rows.Clear();
        issues.Clear();

        Assert.Equal(1, request.ArtifactCount);
        Assert.Equal(1, result.ArtifactCount);
        Assert.Equal(1, result.RowCount);
        Assert.Equal(1, result.IssueCount);
    }

    [Fact]
    public void ValidationDoesNotReadFilesInspectContentAccessDbOrCallNetwork()
    {
        var descriptor = ParserAdapterDescriptorRegistry.Descriptors[1];
        var artifact = new ParserInputArtifact(
            descriptor.SourceFamily,
            descriptor.SourceFamily.ToWireName(),
            descriptor.ParserKey,
            ParserSourceFormat.DiscoveryReference,
            "/definitely/not-present/defra-desnz-input.csv",
            "defra-desnz-input.csv",
            "sha256",
            "abc123",
            isDryRunChecksum: false,
            "text/csv",
            ".csv",
            2024);
        var row = new ParserNormalizedOutputRow(
            descriptor.SourceFamily,
            descriptor.SourceFamily.ToWireName(),
            descriptor.ParserKey,
            artifact.ArtifactReference,
            "row-1",
            sourceRowNumber: 1,
            [
                new ParserNormalizedField("source_payload_reference", "{not inspected json text}"),
            ],
            reportingYear: 2024);
        var issue = new ParserValidationIssue(
            descriptor.SourceFamily,
            descriptor.SourceFamily.ToWireName(),
            descriptor.ParserKey,
            ParserValidationIssueSeverity.Warning,
            "PARSER_RUN_METADATA_ONLY",
            "Run boundary metadata only.",
            artifact.ArtifactReference,
            row.RowIdentifier,
            row.SourceRowNumber);

        Assert.True(new ParserAdapterRunRequest(
            descriptor.SourceFamily,
            descriptor.SourceFamily.ToWireName(),
            descriptor.ParserKey,
            [artifact],
            requestedReportingYear: 2024).Validate().IsValid);
        Assert.True(new ParserAdapterRunResult(
            descriptor.SourceFamily,
            descriptor.SourceFamily.ToWireName(),
            descriptor.ParserKey,
            ParserRunStatus.Pending,
            [artifact.ArtifactReference],
            [row],
            [issue],
            reportingYear: 2024).Validate().IsValid);
    }

    [Fact]
    public void UnknownSourceMetadataFailsClearly()
    {
        var descriptor = ParserAdapterDescriptorRegistry.Descriptors[0];
        var request = new ParserAdapterRunRequest(
            descriptor.SourceFamily,
            "unknown_source_family",
            descriptor.ParserKey,
            [
                ParserInputArtifactRegistry.CreateDefaultDryRunBatch().Artifacts[0],
            ]);

        var result = request.Validate();

        Assert.False(result.IsValid);
        Assert.Contains("SourceKey must match a registered parser adapter descriptor.", result.Errors);
    }

    [Fact]
    public void DivergentParserMetadataFailsClearly()
    {
        var descriptor = ParserAdapterDescriptorRegistry.Descriptors[2];
        var result = new ParserAdapterRunResult(
            descriptor.SourceFamily,
            descriptor.SourceFamily.ToWireName(),
            ParserSelectionRegistry.GetParserKey(SourceFamily.GhgProtocol),
            ParserRunStatus.Pending,
            ["artifact-reference"],
            [],
            []);

        var validation = result.Validate();

        Assert.False(validation.IsValid);
        Assert.Equal(
            ["ParserKey must match the registered parser adapter descriptor."],
            validation.Errors);
    }

    [Fact]
    public void ConstructionRemainsRuntimePassive()
    {
        var requestMethods = typeof(ParserAdapterRunRequest)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();
        var resultMethods = typeof(ParserAdapterRunResult)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();
        var registryMethods = typeof(ParserAdapterRunRegistry)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();

        Assert.DoesNotContain("Parse", requestMethods);
        Assert.DoesNotContain("Execute", requestMethods);
        Assert.DoesNotContain("Parse", resultMethods);
        Assert.DoesNotContain("Execute", resultMethods);
        Assert.DoesNotContain("Parse", registryMethods);
        Assert.DoesNotContain("Execute", registryMethods);
    }

    [Fact]
    public void ContractDoesNotIntroduceDbHttpFileIoParserExecutionOrPersistenceMappingSurface()
    {
        var publicMembers = typeof(ParserAdapterRunRequest)
            .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly)
            .Concat(typeof(ParserAdapterRunResult)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Concat(typeof(ParserAdapterRunRequestBatch)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Concat(typeof(ParserAdapterRunResultBatch)
                .GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Concat(typeof(ParserAdapterRunRegistry)
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
}
