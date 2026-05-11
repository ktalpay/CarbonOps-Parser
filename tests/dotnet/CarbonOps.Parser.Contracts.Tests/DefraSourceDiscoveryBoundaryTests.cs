using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class DefraSourceDiscoveryBoundaryTests
{
    [Fact]
    public void RequestIsDeterministicAndRuntimePassive()
    {
        var first = DefraSourceDiscoveryBoundary.CreateRequest();
        var second = DefraSourceDiscoveryBoundary.CreateRequest();

        Assert.Equal(first, second);
        Assert.Equal(SourceFamily.DefraDesnz, first.SourceFamily);
        Assert.Equal("defra_desnz", first.SourceKey);
        Assert.Equal("discovery://defra_desnz/homepage", first.DiscoveryReferenceUri);
        Assert.Equal(DefraSourceDiscoveryMode.RuntimePassive, first.Mode);
        Assert.False(first.AllowNetwork);
        Assert.False(first.AllowDownload);
        Assert.False(first.AllowParse);
        Assert.False(first.AllowDatabaseWrites);
        Assert.False(first.AllowScheduler);
        Assert.True(DefraSourceDiscoveryBoundary.Validate(first).IsValid);
    }

    [Fact]
    public void ResultDeclaresDefraCandidateWithoutRuntimeWork()
    {
        var result = DefraSourceDiscoveryBoundary.CreateResult();

        Assert.Equal(DefraSourceDiscoveryStatus.Declared, result.Status);
        Assert.Equal(1, result.CandidateCount);
        Assert.Equal(["defra_source_discovery_candidate_001_defra_desnz"], result.CandidateIds);
        Assert.True(result.NoNetwork);
        Assert.True(result.NoDownload);
        Assert.True(result.NoParse);
        Assert.True(result.NoDatabaseWrites);
        Assert.True(result.NoSql);
        Assert.True(result.NoScheduler);
        Assert.True(DefraSourceDiscoveryBoundary.Validate(result).IsValid);

        var candidate = result.Candidates[0];
        Assert.Equal(SourceFamily.DefraDesnz, candidate.SourceFamily);
        Assert.Equal("defra_desnz", candidate.SourceKey);
        Assert.Equal("DEFRA/DESNZ", candidate.Title);
        Assert.Equal("discovery://defra_desnz/homepage", candidate.ReferenceUri);
        Assert.Equal("discovery", candidate.ArtifactKind);
        Assert.Equal(DefraSourceDiscoveryStatus.Declared, candidate.Status);
        Assert.Equal("dn047_defra_discovery_boundary", candidate.VersionLabel);
        Assert.Equal("runtime_passive_discovery_unavailable", candidate.DiscoveredAtLabel);
        Assert.False(candidate.DownloadAllowed);
    }

    [Fact]
    public void BoundaryIsDefraOnly()
    {
        var result = DefraSourceDiscoveryBoundary.CreateResult();

        Assert.Equal([SourceFamily.DefraDesnz], result.Candidates.Select(candidate => candidate.SourceFamily));
        Assert.Equal(["defra_desnz"], result.Candidates.Select(candidate => candidate.SourceKey));
        Assert.DoesNotContain("ghg_protocol", result.CandidateIds);
        Assert.DoesNotContain("ipcc_efdb", result.CandidateIds);
    }

    [Fact]
    public void InvalidRequestFailsClosedWithNoCandidates()
    {
        var request = new DefraSourceDiscoveryRequest(
            SourceFamily.DefraDesnz,
            "ghg_protocol",
            "discovery://defra_desnz/homepage",
            allowNetwork: true,
            allowDownload: true,
            allowParse: true,
            allowDatabaseWrites: true,
            allowScheduler: true);

        var result = DefraSourceDiscoveryBoundary.CreateResult(request);

        Assert.Equal(DefraSourceDiscoveryStatus.Invalid, result.Status);
        Assert.Empty(result.Candidates);
        Assert.True(result.NoNetwork);
        Assert.True(result.NoDownload);
        Assert.True(result.NoParse);
        Assert.True(result.NoDatabaseWrites);
        Assert.Equal(
            [
                "DEFRA_SOURCE_DISCOVERY_SOURCE_KEY_MISMATCH",
                "DEFRA_SOURCE_DISCOVERY_NETWORK_NOT_ALLOWED",
                "DEFRA_SOURCE_DISCOVERY_DOWNLOAD_NOT_ALLOWED",
                "DEFRA_SOURCE_DISCOVERY_PARSE_NOT_ALLOWED",
                "DEFRA_SOURCE_DISCOVERY_DATABASE_WRITES_NOT_ALLOWED",
                "DEFRA_SOURCE_DISCOVERY_SCHEDULER_NOT_ALLOWED",
            ],
            result.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void CandidateInvalidInputsFailClosed()
    {
        var candidate = new DefraSourceDocumentCandidate(
            SourceFamily.GhgProtocol,
            "ghg_protocol",
            "candidate-1",
            "",
            "discovery://defra_desnz/homepage",
            "xlsx",
            DefraSourceDiscoveryStatus.Invalid,
            documentYear: 0,
            reportingYear: -1,
            downloadAllowed: true);

        var result = DefraSourceDiscoveryBoundary.Validate(candidate);

        Assert.False(result.IsValid);
        Assert.Equal(
            [
                "DEFRA_SOURCE_DISCOVERY_CANDIDATE_MISSING_TITLE",
                "DEFRA_SOURCE_DISCOVERY_CANDIDATE_INVALID_DOCUMENT_YEAR",
                "DEFRA_SOURCE_DISCOVERY_CANDIDATE_INVALID_REPORTING_YEAR",
                "DEFRA_SOURCE_DISCOVERY_CANDIDATE_SOURCE_FAMILY_MISMATCH",
                "DEFRA_SOURCE_DISCOVERY_CANDIDATE_SOURCE_KEY_MISMATCH",
                "DEFRA_SOURCE_DISCOVERY_CANDIDATE_ARTIFACT_KIND_MISMATCH",
                "DEFRA_SOURCE_DISCOVERY_CANDIDATE_UNSUPPORTED_STATUS",
                "DEFRA_SOURCE_DISCOVERY_CANDIDATE_DOWNLOAD_NOT_ALLOWED",
            ],
            result.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void CandidateReferenceIsMetadataOnly()
    {
        var candidate = new DefraSourceDocumentCandidate(
            SourceFamily.DefraDesnz,
            "defra_desnz",
            "defra-source-remote-candidate",
            "DEFRA/DESNZ remote metadata",
            "https://example.invalid/not-fetched.xlsx",
            "discovery");

        var result = DefraSourceDiscoveryBoundary.Validate(candidate);

        Assert.True(result.IsValid);
        Assert.Empty(result.Issues);
    }

    [Fact]
    public void ValidationDoesNotRequireNetworkFileDatabaseParserDownloaderOrSchedulerRuntime()
    {
        var candidate = new DefraSourceDocumentCandidate(
            SourceFamily.DefraDesnz,
            "defra_desnz",
            "defra-source-local-reference-candidate",
            "DEFRA/DESNZ local metadata",
            "/definitely/not-present/defra-desnz-factors.xlsx",
            "discovery");
        var result = new DefraSourceDiscoveryResult(
            DefraSourceDiscoveryStatus.Declared,
            DefraSourceDiscoveryBoundary.CreateRequest(),
            [candidate]);

        Assert.True(DefraSourceDiscoveryBoundary.Validate(candidate).IsValid);
        Assert.True(DefraSourceDiscoveryBoundary.Validate(result).IsValid);
        Assert.True(result.NoNetwork);
        Assert.True(result.NoDownload);
        Assert.True(result.NoParse);
        Assert.True(result.NoDatabaseWrites);
        Assert.True(result.NoSql);
        Assert.True(result.NoScheduler);
    }

    [Fact]
    public void ResultValidationRejectsSideEffectFlags()
    {
        var valid = DefraSourceDiscoveryBoundary.CreateResult();
        var result = new DefraSourceDiscoveryResult(
            valid.Status,
            valid.Request,
            valid.Candidates,
            valid.Issues,
            noNetwork: false,
            noSql: false);

        var validation = DefraSourceDiscoveryBoundary.Validate(result);

        Assert.False(validation.IsValid);
        Assert.Equal(
            [
                "DEFRA_SOURCE_DISCOVERY_RESULT_SIDE_EFFECT_FLAG_ENABLED",
                "DEFRA_SOURCE_DISCOVERY_RESULT_SIDE_EFFECT_FLAG_ENABLED",
                "DEFRA_SOURCE_DISCOVERY_RESULT_STATUS_MISMATCH",
            ],
            validation.Issues.Select(issue => issue.Code));
        Assert.Equal(["no_network", "no_sql"], validation.Issues.Take(2).Select(issue => issue.FieldName));
    }

    [Fact]
    public void ResultValidationRejectsDeclaredResultsWithIssueMetadata()
    {
        var valid = DefraSourceDiscoveryBoundary.CreateResult();
        var result = new DefraSourceDiscoveryResult(
            DefraSourceDiscoveryStatus.Declared,
            valid.Request,
            valid.Candidates,
            [
                new DefraSourceDiscoveryIssue(
                    "DEFRA_SOURCE_DISCOVERY_TEST_ISSUE",
                    "test issue",
                    "test"),
            ]);

        var validation = DefraSourceDiscoveryBoundary.Validate(result);

        Assert.False(validation.IsValid);
        Assert.Equal(
            [
                "DEFRA_SOURCE_DISCOVERY_RESULT_DECLARED_WITH_ISSUES",
                "DEFRA_SOURCE_DISCOVERY_RESULT_STATUS_MISMATCH",
            ],
            validation.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void ResultValidationRejectsUndefinedStatus()
    {
        var valid = DefraSourceDiscoveryBoundary.CreateResult();
        var result = new DefraSourceDiscoveryResult(
            (DefraSourceDiscoveryStatus)999,
            valid.Request,
            valid.Candidates,
            [
                new DefraSourceDiscoveryIssue(
                    "DEFRA_SOURCE_DISCOVERY_TEST_ISSUE",
                    "test issue",
                    "test"),
            ]);

        var validation = DefraSourceDiscoveryBoundary.Validate(result);

        Assert.False(validation.IsValid);
        Assert.Equal(
            ["DEFRA_SOURCE_DISCOVERY_RESULT_INVALID_STATUS"],
            validation.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void BoundaryPublicSurfaceDoesNotExposeRuntimeExecutionMethods()
    {
        var publicMethodNames = typeof(DefraSourceDiscoveryBoundary)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();

        Assert.Contains("CreateRequest", publicMethodNames);
        Assert.Contains("CreateResult", publicMethodNames);
        Assert.Equal(3, publicMethodNames.Count(methodName => methodName == "Validate"));
        Assert.DoesNotContain("Discover", publicMethodNames);
        Assert.DoesNotContain("Fetch", publicMethodNames);
        Assert.DoesNotContain("Parse", publicMethodNames);
        Assert.DoesNotContain("Execute", publicMethodNames);
    }

    [Fact]
    public void BoundaryTypesDoNotExposeRuntimeExecutionMethods()
    {
        var publicMethodNames = new[]
        {
            typeof(DefraSourceDiscoveryRequest),
            typeof(DefraSourceDocumentCandidate),
            typeof(DefraSourceDiscoveryResult),
            typeof(DefraSourceDiscoveryIssue),
            typeof(DefraSourceDiscoveryValidationResult),
        }
            .SelectMany(type => type.GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance | BindingFlags.DeclaredOnly))
            .Where(method => !method.Name.StartsWith("get_", StringComparison.Ordinal))
            .Select(method => method.Name)
            .ToArray();

        Assert.DoesNotContain("Discover", publicMethodNames);
        Assert.DoesNotContain("Fetch", publicMethodNames);
        Assert.DoesNotContain("Parse", publicMethodNames);
        Assert.DoesNotContain("Execute", publicMethodNames);
        Assert.DoesNotContain("Schedule", publicMethodNames);
        Assert.DoesNotContain("Persist", publicMethodNames);
        Assert.DoesNotContain("Open", publicMethodNames);
        Assert.DoesNotContain("Read", publicMethodNames);
        Assert.DoesNotContain("Write", publicMethodNames);
    }

    [Fact]
    public void DefraDiscoveryWireNamesArePythonAligned()
    {
        Assert.Equal("runtime_passive", DefraSourceDiscoveryMode.RuntimePassive.ToWireName());
        Assert.Equal("declared", DefraSourceDiscoveryStatus.Declared.ToWireName());
        Assert.Equal("invalid", DefraSourceDiscoveryStatus.Invalid.ToWireName());
        Assert.True(ContractWireNames.TryParseDefraSourceDiscoveryModeWireName("runtime_passive", out var parsedMode));
        Assert.Equal(DefraSourceDiscoveryMode.RuntimePassive, parsedMode);
        Assert.True(ContractWireNames.TryParseDefraSourceDiscoveryStatusWireName("declared", out var parsedStatus));
        Assert.Equal(DefraSourceDiscoveryStatus.Declared, parsedStatus);
        Assert.False(ContractWireNames.TryParseDefraSourceDiscoveryStatusWireName("unknown", out _));
        Assert.Throws<ArgumentOutOfRangeException>(() => ((DefraSourceDiscoveryMode)999).ToWireName());
        Assert.Throws<ArgumentOutOfRangeException>(() => ((DefraSourceDiscoveryStatus)999).ToWireName());
    }
}
