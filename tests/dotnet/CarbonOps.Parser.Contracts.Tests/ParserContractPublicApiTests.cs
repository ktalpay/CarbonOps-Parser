using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class ParserContractPublicApiTests
{
    [Fact]
    public void RuntimePassiveParserContractTypesArePublic()
    {
        var publicContractTypes = new[]
        {
            typeof(IParserAdapterDescriptor),
            typeof(GhgProtocolParserAdapterDescriptor),
            typeof(DefraDesnzParserAdapterDescriptor),
            typeof(IpccEfdbParserAdapterDescriptor),
            typeof(ParserAdapterCapability),
            typeof(ParserAdapterReadiness),
            typeof(ParserAdapterDescriptorRegistry),
            typeof(ParserAdapterReadinessReport),
            typeof(ParserAdapterReadinessReportEntry),
            typeof(ParserInputArtifact),
            typeof(ParserInputArtifactBatch),
            typeof(ParserInputArtifactRegistry),
            typeof(ParserNormalizedField),
            typeof(ParserNormalizedOutputRow),
            typeof(ParserNormalizedOutputBatch),
            typeof(ParserNormalizedOutputRegistry),
            typeof(ParserValidationIssueSeverity),
            typeof(ParserValidationIssueContext),
            typeof(ParserValidationIssue),
            typeof(ParserValidationIssueBatch),
            typeof(ParserValidationIssueRegistry),
            typeof(ParserAdapterRunRequest),
            typeof(ParserAdapterRunRequestBatch),
            typeof(ParserAdapterRunResult),
            typeof(ParserAdapterRunResultBatch),
            typeof(ParserAdapterRunRegistry),
            typeof(ParserDryRunStatus),
            typeof(ParserDryRunBoundaryPlan),
            typeof(ParserDryRunBoundaryPlanBatch),
            typeof(ParserDryRunBoundaryResult),
            typeof(ParserDryRunBoundaryResultBatch),
            typeof(ParserDryRunBoundaryPlanner),
        };

        Assert.Equal(
            [
                "IParserAdapterDescriptor",
                "GhgProtocolParserAdapterDescriptor",
                "DefraDesnzParserAdapterDescriptor",
                "IpccEfdbParserAdapterDescriptor",
                "ParserAdapterCapability",
                "ParserAdapterReadiness",
                "ParserAdapterDescriptorRegistry",
                "ParserAdapterReadinessReport",
                "ParserAdapterReadinessReportEntry",
                "ParserInputArtifact",
                "ParserInputArtifactBatch",
                "ParserInputArtifactRegistry",
                "ParserNormalizedField",
                "ParserNormalizedOutputRow",
                "ParserNormalizedOutputBatch",
                "ParserNormalizedOutputRegistry",
                "ParserValidationIssueSeverity",
                "ParserValidationIssueContext",
                "ParserValidationIssue",
                "ParserValidationIssueBatch",
                "ParserValidationIssueRegistry",
                "ParserAdapterRunRequest",
                "ParserAdapterRunRequestBatch",
                "ParserAdapterRunResult",
                "ParserAdapterRunResultBatch",
                "ParserAdapterRunRegistry",
                "ParserDryRunStatus",
                "ParserDryRunBoundaryPlan",
                "ParserDryRunBoundaryPlanBatch",
                "ParserDryRunBoundaryResult",
                "ParserDryRunBoundaryResultBatch",
                "ParserDryRunBoundaryPlanner",
            ],
            publicContractTypes.Select(type => type.Name));
        Assert.All(publicContractTypes, type => Assert.True(type.IsPublic, $"{type.Name} must be public."));
    }

    [Fact]
    public void ParserContractTypesCanBeConstructedThroughPublicApi()
    {
        var descriptor = ParserAdapterDescriptorRegistry.Descriptors[0];
        var capability = new ParserAdapterCapability(
            [descriptor.SourceFamily],
            [ParserSourceFormat.DiscoveryReference],
            ["application/x-carbonops-discovery-reference"],
            ["discovery"]);
        var readinessReport = ParserAdapterReadinessReport.CreateDefault();
        var artifact = new ParserInputArtifact(
            descriptor.SourceFamily,
            descriptor.SourceFamily.ToWireName(),
            descriptor.ParserKey,
            ParserSourceFormat.DiscoveryReference,
            "ghg_protocol_discovery_reference",
            "ghg_protocol_discovery_reference",
            "dry_run_sha256",
            "ghg_protocol_dry_run_checksum",
            isDryRunChecksum: true,
            "application/x-carbonops-discovery-reference",
            extension: null,
            reportingYear: null);
        var artifactBatch = new ParserInputArtifactBatch([artifact]);
        var normalizedField = new ParserNormalizedField("source_key", artifact.SourceKey);
        var normalizedRow = new ParserNormalizedOutputRow(
            artifact.SourceFamily,
            artifact.SourceKey,
            artifact.ParserKey,
            artifact.ArtifactReference,
            "ghg_protocol_normalized_row_1",
            sourceRowNumber: 1,
            [normalizedField]);
        var normalizedBatch = new ParserNormalizedOutputBatch([normalizedRow]);
        var validationIssue = new ParserValidationIssue(
            artifact.SourceFamily,
            artifact.SourceKey,
            artifact.ParserKey,
            ParserValidationIssueSeverity.Info,
            "PARSER_PUBLIC_API",
            "Parser contract public API construction.",
            artifact.ArtifactReference,
            normalizedRow.RowIdentifier,
            normalizedRow.SourceRowNumber,
            context:
            [
                new ParserValidationIssueContext("source_key", artifact.SourceKey),
            ]);
        var validationIssueBatch = new ParserValidationIssueBatch([validationIssue]);
        var runRequest = new ParserAdapterRunRequest(
            artifact.SourceFamily,
            artifact.SourceKey,
            artifact.ParserKey,
            [artifact]);
        var runRequestBatch = new ParserAdapterRunRequestBatch([runRequest]);
        var runResult = new ParserAdapterRunResult(
            artifact.SourceFamily,
            artifact.SourceKey,
            artifact.ParserKey,
            ParserRunStatus.Pending,
            [artifact.ArtifactReference],
            [normalizedRow],
            [validationIssue]);
        var runResultBatch = new ParserAdapterRunResultBatch([runResult]);
        var dryRunPlan = ParserDryRunBoundaryPlanner.CreatePlan(runRequest);
        var dryRunPlanBatch = new ParserDryRunBoundaryPlanBatch([dryRunPlan]);
        var dryRunResult = ParserDryRunBoundaryPlanner.CreateResult(dryRunPlan);
        var dryRunResultBatch = new ParserDryRunBoundaryResultBatch([dryRunResult]);

        Assert.Equal(descriptor.SourceFamily, capability.SupportedSourceFamilies[0]);
        Assert.Equal(3, readinessReport.AdapterCount);
        Assert.Equal(1, artifactBatch.ArtifactCount);
        Assert.Equal(1, normalizedBatch.RowCount);
        Assert.Equal(1, validationIssueBatch.IssueCount);
        Assert.Equal(1, runRequestBatch.RequestCount);
        Assert.Equal(1, runResultBatch.ResultCount);
        Assert.Equal(1, dryRunPlanBatch.PlanCount);
        Assert.Equal(1, dryRunResultBatch.ResultCount);
        Assert.True(artifact.Validate().IsValid);
        Assert.True(normalizedRow.Validate().IsValid);
        Assert.True(validationIssue.Validate().IsValid);
        Assert.True(runRequest.Validate().IsValid);
        Assert.True(runResult.Validate().IsValid);
        Assert.True(dryRunPlan.Validate().IsValid);
        Assert.True(dryRunResult.Validate().IsValid);
    }

    [Fact]
    public void ParserContractWireNamesArePublicAndDeterministic()
    {
        Assert.Equal("execution_not_implemented", ParserAdapterReadiness.ExecutionNotImplemented.ToWireName());
        Assert.True(
            ContractWireNames.TryParseParserAdapterReadinessWireName(
                "execution_not_implemented",
                out var readiness));
        Assert.Equal(ParserAdapterReadiness.ExecutionNotImplemented, readiness);

        Assert.Equal("info", ParserValidationIssueSeverity.Info.ToWireName());
        Assert.Equal("warning", ParserValidationIssueSeverity.Warning.ToWireName());
        Assert.Equal("error", ParserValidationIssueSeverity.Error.ToWireName());
        Assert.True(ContractWireNames.TryParseParserValidationIssueSeverityWireName("info", out var severity));
        Assert.Equal(ParserValidationIssueSeverity.Info, severity);

        Assert.Equal("planned", ParserDryRunStatus.Planned.ToWireName());
        Assert.Equal("invalid_request", ParserDryRunStatus.InvalidRequest.ToWireName());
        Assert.Equal("execution_not_implemented", ParserDryRunStatus.ExecutionNotImplemented.ToWireName());
        Assert.True(ContractWireNames.TryParseParserDryRunStatusWireName("planned", out var dryRunStatus));
        Assert.Equal(ParserDryRunStatus.Planned, dryRunStatus);
    }

    [Fact]
    public void ParserContractPublicApiConstructionRemainsRuntimePassive()
    {
        var parserContractTypes = new[]
        {
            typeof(ParserAdapterDescriptorRegistry),
            typeof(ParserAdapterReadinessReport),
            typeof(ParserInputArtifactRegistry),
            typeof(ParserNormalizedOutputRegistry),
            typeof(ParserValidationIssueRegistry),
            typeof(ParserAdapterRunRegistry),
            typeof(ParserDryRunBoundaryPlanner),
        };
        var publicMethodNames = parserContractTypes
            .SelectMany(type => type.GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Where(method => !method.Name.StartsWith("get_", StringComparison.Ordinal))
            .Select(method => method.Name)
            .ToArray();

        Assert.DoesNotContain("Parse", publicMethodNames);
        Assert.DoesNotContain("Execute", publicMethodNames);
        Assert.DoesNotContain("Instantiate", publicMethodNames);
    }

    [Fact]
    public void ParserContractPublicApiDoesNotExposeDbHttpFileIoOrRuntimeExecutionSurface()
    {
        var parserContractTypes = new[]
        {
            typeof(ParserInputArtifact),
            typeof(ParserNormalizedOutputRow),
            typeof(ParserValidationIssue),
            typeof(ParserAdapterRunRequest),
            typeof(ParserAdapterRunResult),
            typeof(ParserDryRunBoundaryPlan),
            typeof(ParserDryRunBoundaryResult),
            typeof(ParserDryRunBoundaryPlanner),
        };
        var publicMembers = parserContractTypes
            .SelectMany(type => type.GetMembers(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Select(member => member.Name)
            .ToArray();
        var blockedTerms = new[]
        {
            "Db",
            "Sql",
            "Postgres",
            "Http",
            "Open",
            "Write",
            "Exists",
            "Calculate",
            "Factor",
            "Persist",
        };

        foreach (var term in blockedTerms)
        {
            Assert.DoesNotContain(publicMembers, member => member.Contains(term, StringComparison.OrdinalIgnoreCase));
        }

        Assert.DoesNotContain("Parse", publicMembers);
    }
}
