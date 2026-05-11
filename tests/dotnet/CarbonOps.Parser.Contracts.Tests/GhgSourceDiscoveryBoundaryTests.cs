using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class GhgSourceDiscoveryBoundaryTests
{
    [Fact]
    public void RequestIsDeterministicAndRuntimePassive()
    {
        var first = GhgSourceDiscoveryBoundary.CreateRequest();
        var second = GhgSourceDiscoveryBoundary.CreateRequest();

        Assert.Equal(first, second);
        Assert.Equal(SourceFamily.GhgProtocol, first.SourceFamily);
        Assert.Equal("ghg_protocol", first.SourceKey);
        Assert.Equal("discovery://ghg_protocol/acquisition", first.DiscoveryReferenceUri);
        Assert.Equal(GhgSourceDiscoveryMode.RuntimePassive, first.Mode);
        Assert.False(first.AllowNetwork);
        Assert.False(first.AllowDownload);
        Assert.False(first.AllowParse);
        Assert.False(first.AllowDatabaseWrites);
        Assert.False(first.AllowScheduler);
        Assert.True(GhgSourceDiscoveryBoundary.Validate(first).IsValid);
    }

    [Fact]
    public void ResultDeclaresGhgCandidateWithoutRuntimeWork()
    {
        var result = GhgSourceDiscoveryBoundary.CreateResult();

        Assert.Equal(GhgSourceDiscoveryStatus.Declared, result.Status);
        Assert.Equal(1, result.CandidateCount);
        Assert.Equal(["ghg_source_discovery_candidate_001_ghg_protocol"], result.CandidateIds);
        Assert.True(result.NoNetwork);
        Assert.True(result.NoDownload);
        Assert.True(result.NoParse);
        Assert.True(result.NoDatabaseWrites);
        Assert.True(result.NoSql);
        Assert.True(result.NoScheduler);
        Assert.True(GhgSourceDiscoveryBoundary.Validate(result).IsValid);

        var candidate = result.Candidates[0];
        Assert.Equal(SourceFamily.GhgProtocol, candidate.SourceFamily);
        Assert.Equal("ghg_protocol", candidate.SourceKey);
        Assert.Equal("GHG Protocol", candidate.Title);
        Assert.Equal("discovery://ghg_protocol/acquisition", candidate.ReferenceUri);
        Assert.Equal("discovery", candidate.ArtifactKind);
        Assert.Equal(GhgSourceDiscoveryStatus.Declared, candidate.Status);
        Assert.Equal("dn045_ghg_discovery_boundary", candidate.VersionLabel);
        Assert.Equal("runtime_passive_discovery_unavailable", candidate.DiscoveredAtLabel);
        Assert.False(candidate.DownloadAllowed);
    }

    [Fact]
    public void BoundaryIsGhgOnly()
    {
        var result = GhgSourceDiscoveryBoundary.CreateResult();

        Assert.Equal([SourceFamily.GhgProtocol], result.Candidates.Select(candidate => candidate.SourceFamily));
        Assert.Equal(["ghg_protocol"], result.Candidates.Select(candidate => candidate.SourceKey));
        Assert.DoesNotContain("defra_desnz", result.CandidateIds);
        Assert.DoesNotContain("ipcc_efdb", result.CandidateIds);
    }

    [Fact]
    public void InvalidRequestFailsClosedWithNoCandidates()
    {
        var request = new GhgSourceDiscoveryRequest(
            SourceFamily.GhgProtocol,
            "defra_desnz",
            "discovery://ghg_protocol/acquisition",
            allowNetwork: true,
            allowDownload: true,
            allowParse: true,
            allowDatabaseWrites: true,
            allowScheduler: true);

        var result = GhgSourceDiscoveryBoundary.CreateResult(request);

        Assert.Equal(GhgSourceDiscoveryStatus.Invalid, result.Status);
        Assert.Empty(result.Candidates);
        Assert.True(result.NoNetwork);
        Assert.True(result.NoDownload);
        Assert.True(result.NoParse);
        Assert.True(result.NoDatabaseWrites);
        Assert.Equal(
            [
                "GHG_SOURCE_DISCOVERY_SOURCE_KEY_MISMATCH",
                "GHG_SOURCE_DISCOVERY_NETWORK_NOT_ALLOWED",
                "GHG_SOURCE_DISCOVERY_DOWNLOAD_NOT_ALLOWED",
                "GHG_SOURCE_DISCOVERY_PARSE_NOT_ALLOWED",
                "GHG_SOURCE_DISCOVERY_DATABASE_WRITES_NOT_ALLOWED",
                "GHG_SOURCE_DISCOVERY_SCHEDULER_NOT_ALLOWED",
            ],
            result.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void CandidateInvalidInputsFailClosed()
    {
        var candidate = new GhgSourceDocumentCandidate(
            SourceFamily.DefraDesnz,
            "defra_desnz",
            "candidate-1",
            "",
            "discovery://ghg_protocol/acquisition",
            "xlsx",
            GhgSourceDiscoveryStatus.Invalid,
            documentYear: 0,
            reportingYear: -1,
            downloadAllowed: true);

        var result = GhgSourceDiscoveryBoundary.Validate(candidate);

        Assert.False(result.IsValid);
        Assert.Equal(
            [
                "GHG_SOURCE_DISCOVERY_CANDIDATE_MISSING_TITLE",
                "GHG_SOURCE_DISCOVERY_CANDIDATE_INVALID_DOCUMENT_YEAR",
                "GHG_SOURCE_DISCOVERY_CANDIDATE_INVALID_REPORTING_YEAR",
                "GHG_SOURCE_DISCOVERY_CANDIDATE_SOURCE_FAMILY_MISMATCH",
                "GHG_SOURCE_DISCOVERY_CANDIDATE_SOURCE_KEY_MISMATCH",
                "GHG_SOURCE_DISCOVERY_CANDIDATE_ARTIFACT_KIND_MISMATCH",
                "GHG_SOURCE_DISCOVERY_CANDIDATE_UNSUPPORTED_STATUS",
                "GHG_SOURCE_DISCOVERY_CANDIDATE_DOWNLOAD_NOT_ALLOWED",
            ],
            result.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void CandidateReferenceIsMetadataOnly()
    {
        var candidate = new GhgSourceDocumentCandidate(
            SourceFamily.GhgProtocol,
            "ghg_protocol",
            "ghg-source-remote-candidate",
            "GHG Protocol remote metadata",
            "https://example.invalid/not-fetched.csv",
            "discovery");

        var result = GhgSourceDiscoveryBoundary.Validate(candidate);

        Assert.True(result.IsValid);
        Assert.Empty(result.Issues);
    }

    [Fact]
    public void ValidationDoesNotRequireNetworkFileDatabaseParserDownloaderOrSchedulerRuntime()
    {
        var candidate = new GhgSourceDocumentCandidate(
            SourceFamily.GhgProtocol,
            "ghg_protocol",
            "ghg-source-local-reference-candidate",
            "GHG Protocol local metadata",
            "/definitely/not-present/ghg-protocol-factors.csv",
            "discovery");
        var result = new GhgSourceDiscoveryResult(
            GhgSourceDiscoveryStatus.Declared,
            GhgSourceDiscoveryBoundary.CreateRequest(),
            [candidate]);

        Assert.True(GhgSourceDiscoveryBoundary.Validate(candidate).IsValid);
        Assert.True(GhgSourceDiscoveryBoundary.Validate(result).IsValid);
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
        var valid = GhgSourceDiscoveryBoundary.CreateResult();
        var result = new GhgSourceDiscoveryResult(
            valid.Status,
            valid.Request,
            valid.Candidates,
            valid.Issues,
            noNetwork: false,
            noSql: false);

        var validation = GhgSourceDiscoveryBoundary.Validate(result);

        Assert.False(validation.IsValid);
        Assert.Equal(
            [
                "GHG_SOURCE_DISCOVERY_RESULT_SIDE_EFFECT_FLAG_ENABLED",
                "GHG_SOURCE_DISCOVERY_RESULT_SIDE_EFFECT_FLAG_ENABLED",
                "GHG_SOURCE_DISCOVERY_RESULT_STATUS_MISMATCH",
            ],
            validation.Issues.Select(issue => issue.Code));
        Assert.Equal(["no_network", "no_sql"], validation.Issues.Take(2).Select(issue => issue.FieldName));
    }

    [Fact]
    public void ResultValidationRejectsDeclaredResultsWithIssueMetadata()
    {
        var valid = GhgSourceDiscoveryBoundary.CreateResult();
        var result = new GhgSourceDiscoveryResult(
            GhgSourceDiscoveryStatus.Declared,
            valid.Request,
            valid.Candidates,
            [
                new GhgSourceDiscoveryIssue(
                    "GHG_SOURCE_DISCOVERY_TEST_ISSUE",
                    "test issue",
                    "test"),
            ]);

        var validation = GhgSourceDiscoveryBoundary.Validate(result);

        Assert.False(validation.IsValid);
        Assert.Equal(
            [
                "GHG_SOURCE_DISCOVERY_RESULT_DECLARED_WITH_ISSUES",
                "GHG_SOURCE_DISCOVERY_RESULT_STATUS_MISMATCH",
            ],
            validation.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void ResultValidationRejectsUndefinedStatus()
    {
        var valid = GhgSourceDiscoveryBoundary.CreateResult();
        var result = new GhgSourceDiscoveryResult(
            (GhgSourceDiscoveryStatus)999,
            valid.Request,
            valid.Candidates,
            [
                new GhgSourceDiscoveryIssue(
                    "GHG_SOURCE_DISCOVERY_TEST_ISSUE",
                    "test issue",
                    "test"),
            ]);

        var validation = GhgSourceDiscoveryBoundary.Validate(result);

        Assert.False(validation.IsValid);
        Assert.Equal(
            ["GHG_SOURCE_DISCOVERY_RESULT_INVALID_STATUS"],
            validation.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void BoundaryPublicSurfaceDoesNotExposeRuntimeExecutionMethods()
    {
        var publicMethodNames = typeof(GhgSourceDiscoveryBoundary)
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
            typeof(GhgSourceDiscoveryRequest),
            typeof(GhgSourceDocumentCandidate),
            typeof(GhgSourceDiscoveryResult),
            typeof(GhgSourceDiscoveryIssue),
            typeof(GhgSourceDiscoveryValidationResult),
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
    public void GhgDiscoveryWireNamesArePythonAligned()
    {
        Assert.Equal("runtime_passive", GhgSourceDiscoveryMode.RuntimePassive.ToWireName());
        Assert.Equal("declared", GhgSourceDiscoveryStatus.Declared.ToWireName());
        Assert.Equal("invalid", GhgSourceDiscoveryStatus.Invalid.ToWireName());
        Assert.True(ContractWireNames.TryParseGhgSourceDiscoveryModeWireName("runtime_passive", out var parsedMode));
        Assert.Equal(GhgSourceDiscoveryMode.RuntimePassive, parsedMode);
        Assert.True(ContractWireNames.TryParseGhgSourceDiscoveryStatusWireName("declared", out var parsedStatus));
        Assert.Equal(GhgSourceDiscoveryStatus.Declared, parsedStatus);
        Assert.False(ContractWireNames.TryParseGhgSourceDiscoveryStatusWireName("unknown", out _));
        Assert.Throws<ArgumentOutOfRangeException>(() => ((GhgSourceDiscoveryMode)999).ToWireName());
        Assert.Throws<ArgumentOutOfRangeException>(() => ((GhgSourceDiscoveryStatus)999).ToWireName());
    }
}
