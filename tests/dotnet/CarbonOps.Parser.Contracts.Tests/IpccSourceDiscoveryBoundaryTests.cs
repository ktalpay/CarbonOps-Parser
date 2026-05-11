using System.Reflection;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class IpccSourceDiscoveryBoundaryTests
{
    [Fact]
    public void RequestIsDeterministicAndRuntimePassive()
    {
        var first = IpccSourceDiscoveryBoundary.CreateRequest();
        var second = IpccSourceDiscoveryBoundary.CreateRequest();

        Assert.Equal(first, second);
        Assert.Equal(SourceFamily.IpccEfdb, first.SourceFamily);
        Assert.Equal("ipcc_efdb", first.SourceKey);
        Assert.Equal("discovery://ipcc_efdb/homepage", first.DiscoveryReferenceUri);
        Assert.Equal(IpccSourceDiscoveryMode.RuntimePassive, first.Mode);
        Assert.False(first.AllowNetwork);
        Assert.False(first.AllowDownload);
        Assert.False(first.AllowParse);
        Assert.False(first.AllowDatabaseWrites);
        Assert.False(first.AllowScheduler);
        Assert.True(IpccSourceDiscoveryBoundary.Validate(first).IsValid);
    }

    [Fact]
    public void ResultDeclaresIpccCandidateWithoutRuntimeWork()
    {
        var result = IpccSourceDiscoveryBoundary.CreateResult();

        Assert.Equal(IpccSourceDiscoveryStatus.Declared, result.Status);
        Assert.Equal(1, result.CandidateCount);
        Assert.Equal(["ipcc_source_discovery_candidate_001_ipcc_efdb"], result.CandidateIds);
        Assert.True(result.NoNetwork);
        Assert.True(result.NoDownload);
        Assert.True(result.NoParse);
        Assert.True(result.NoDatabaseWrites);
        Assert.True(result.NoSql);
        Assert.True(result.NoScheduler);
        Assert.True(IpccSourceDiscoveryBoundary.Validate(result).IsValid);

        var candidate = result.Candidates[0];
        Assert.Equal(SourceFamily.IpccEfdb, candidate.SourceFamily);
        Assert.Equal("ipcc_efdb", candidate.SourceKey);
        Assert.Equal("IPCC EFDB", candidate.Title);
        Assert.Equal("discovery://ipcc_efdb/homepage", candidate.ReferenceUri);
        Assert.Equal("discovery", candidate.ArtifactKind);
        Assert.Equal(IpccSourceDiscoveryStatus.Declared, candidate.Status);
        Assert.Equal("dn049_ipcc_discovery_boundary", candidate.VersionLabel);
        Assert.Equal("runtime_passive_discovery_unavailable", candidate.DiscoveredAtLabel);
        Assert.False(candidate.DownloadAllowed);
    }

    [Fact]
    public void BoundaryIsIpccOnly()
    {
        var result = IpccSourceDiscoveryBoundary.CreateResult();

        Assert.Equal([SourceFamily.IpccEfdb], result.Candidates.Select(candidate => candidate.SourceFamily));
        Assert.Equal(["ipcc_efdb"], result.Candidates.Select(candidate => candidate.SourceKey));
        Assert.DoesNotContain("ghg_protocol", result.CandidateIds);
        Assert.DoesNotContain("defra_desnz", result.CandidateIds);
    }

    [Fact]
    public void InvalidRequestFailsClosedWithNoCandidates()
    {
        var request = new IpccSourceDiscoveryRequest(
            SourceFamily.IpccEfdb,
            "ghg_protocol",
            "discovery://ipcc_efdb/homepage",
            allowNetwork: true,
            allowDownload: true,
            allowParse: true,
            allowDatabaseWrites: true,
            allowScheduler: true);

        var result = IpccSourceDiscoveryBoundary.CreateResult(request);

        Assert.Equal(IpccSourceDiscoveryStatus.Invalid, result.Status);
        Assert.Empty(result.Candidates);
        Assert.True(result.NoNetwork);
        Assert.True(result.NoDownload);
        Assert.True(result.NoParse);
        Assert.True(result.NoDatabaseWrites);
        Assert.Equal(
            [
                "IPCC_SOURCE_DISCOVERY_SOURCE_KEY_MISMATCH",
                "IPCC_SOURCE_DISCOVERY_NETWORK_NOT_ALLOWED",
                "IPCC_SOURCE_DISCOVERY_DOWNLOAD_NOT_ALLOWED",
                "IPCC_SOURCE_DISCOVERY_PARSE_NOT_ALLOWED",
                "IPCC_SOURCE_DISCOVERY_DATABASE_WRITES_NOT_ALLOWED",
                "IPCC_SOURCE_DISCOVERY_SCHEDULER_NOT_ALLOWED",
            ],
            result.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void CandidateInvalidInputsFailClosed()
    {
        var candidate = new IpccSourceDocumentCandidate(
            SourceFamily.GhgProtocol,
            "ghg_protocol",
            "candidate-1",
            "",
            "discovery://ipcc_efdb/homepage",
            "xlsx",
            IpccSourceDiscoveryStatus.Invalid,
            documentYear: 0,
            reportingYear: -1,
            downloadAllowed: true);

        var result = IpccSourceDiscoveryBoundary.Validate(candidate);

        Assert.False(result.IsValid);
        Assert.Equal(
            [
                "IPCC_SOURCE_DISCOVERY_CANDIDATE_MISSING_TITLE",
                "IPCC_SOURCE_DISCOVERY_CANDIDATE_INVALID_DOCUMENT_YEAR",
                "IPCC_SOURCE_DISCOVERY_CANDIDATE_INVALID_REPORTING_YEAR",
                "IPCC_SOURCE_DISCOVERY_CANDIDATE_SOURCE_FAMILY_MISMATCH",
                "IPCC_SOURCE_DISCOVERY_CANDIDATE_SOURCE_KEY_MISMATCH",
                "IPCC_SOURCE_DISCOVERY_CANDIDATE_ARTIFACT_KIND_MISMATCH",
                "IPCC_SOURCE_DISCOVERY_CANDIDATE_UNSUPPORTED_STATUS",
                "IPCC_SOURCE_DISCOVERY_CANDIDATE_DOWNLOAD_NOT_ALLOWED",
            ],
            result.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void CandidateReferenceIsMetadataOnly()
    {
        var candidate = new IpccSourceDocumentCandidate(
            SourceFamily.IpccEfdb,
            "ipcc_efdb",
            "ipcc-source-remote-candidate",
            "IPCC EFDB remote metadata",
            "https://example.invalid/not-fetched.xlsx",
            "discovery");

        var result = IpccSourceDiscoveryBoundary.Validate(candidate);

        Assert.True(result.IsValid);
        Assert.Empty(result.Issues);
    }

    [Fact]
    public void ValidationDoesNotRequireNetworkFileDatabaseParserDownloaderOrSchedulerRuntime()
    {
        var candidate = new IpccSourceDocumentCandidate(
            SourceFamily.IpccEfdb,
            "ipcc_efdb",
            "ipcc-source-local-reference-candidate",
            "IPCC EFDB local metadata",
            "/definitely/not-present/ipcc-efdb-factors.xlsx",
            "discovery");
        var result = new IpccSourceDiscoveryResult(
            IpccSourceDiscoveryStatus.Declared,
            IpccSourceDiscoveryBoundary.CreateRequest(),
            [candidate]);

        Assert.True(IpccSourceDiscoveryBoundary.Validate(candidate).IsValid);
        Assert.True(IpccSourceDiscoveryBoundary.Validate(result).IsValid);
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
        var valid = IpccSourceDiscoveryBoundary.CreateResult();
        var result = new IpccSourceDiscoveryResult(
            valid.Status,
            valid.Request,
            valid.Candidates,
            valid.Issues,
            noNetwork: false,
            noSql: false);

        var validation = IpccSourceDiscoveryBoundary.Validate(result);

        Assert.False(validation.IsValid);
        Assert.Equal(
            [
                "IPCC_SOURCE_DISCOVERY_RESULT_SIDE_EFFECT_FLAG_ENABLED",
                "IPCC_SOURCE_DISCOVERY_RESULT_SIDE_EFFECT_FLAG_ENABLED",
                "IPCC_SOURCE_DISCOVERY_RESULT_STATUS_MISMATCH",
            ],
            validation.Issues.Select(issue => issue.Code));
        Assert.Equal(["no_network", "no_sql"], validation.Issues.Take(2).Select(issue => issue.FieldName));
    }

    [Fact]
    public void ResultValidationRejectsDeclaredResultsWithIssueMetadata()
    {
        var valid = IpccSourceDiscoveryBoundary.CreateResult();
        var result = new IpccSourceDiscoveryResult(
            IpccSourceDiscoveryStatus.Declared,
            valid.Request,
            valid.Candidates,
            [
                new IpccSourceDiscoveryIssue(
                    "IPCC_SOURCE_DISCOVERY_TEST_ISSUE",
                    "test issue",
                    "test"),
            ]);

        var validation = IpccSourceDiscoveryBoundary.Validate(result);

        Assert.False(validation.IsValid);
        Assert.Equal(
            [
                "IPCC_SOURCE_DISCOVERY_RESULT_DECLARED_WITH_ISSUES",
                "IPCC_SOURCE_DISCOVERY_RESULT_STATUS_MISMATCH",
            ],
            validation.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void ResultValidationRejectsUndefinedStatus()
    {
        var valid = IpccSourceDiscoveryBoundary.CreateResult();
        var result = new IpccSourceDiscoveryResult(
            (IpccSourceDiscoveryStatus)999,
            valid.Request,
            valid.Candidates,
            [
                new IpccSourceDiscoveryIssue(
                    "IPCC_SOURCE_DISCOVERY_TEST_ISSUE",
                    "test issue",
                    "test"),
            ]);

        var validation = IpccSourceDiscoveryBoundary.Validate(result);

        Assert.False(validation.IsValid);
        Assert.Equal(
            ["IPCC_SOURCE_DISCOVERY_RESULT_INVALID_STATUS"],
            validation.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void BoundaryPublicSurfaceDoesNotExposeRuntimeExecutionMethods()
    {
        var publicMethodNames = typeof(IpccSourceDiscoveryBoundary)
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
            typeof(IpccSourceDiscoveryRequest),
            typeof(IpccSourceDocumentCandidate),
            typeof(IpccSourceDiscoveryResult),
            typeof(IpccSourceDiscoveryIssue),
            typeof(IpccSourceDiscoveryValidationResult),
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
    public void IpccDiscoveryWireNamesArePythonAligned()
    {
        Assert.Equal("runtime_passive", IpccSourceDiscoveryMode.RuntimePassive.ToWireName());
        Assert.Equal("declared", IpccSourceDiscoveryStatus.Declared.ToWireName());
        Assert.Equal("invalid", IpccSourceDiscoveryStatus.Invalid.ToWireName());
        Assert.True(ContractWireNames.TryParseIpccSourceDiscoveryModeWireName("runtime_passive", out var parsedMode));
        Assert.Equal(IpccSourceDiscoveryMode.RuntimePassive, parsedMode);
        Assert.True(ContractWireNames.TryParseIpccSourceDiscoveryStatusWireName("declared", out var parsedStatus));
        Assert.Equal(IpccSourceDiscoveryStatus.Declared, parsedStatus);
        Assert.False(ContractWireNames.TryParseIpccSourceDiscoveryStatusWireName("unknown", out _));
        Assert.Throws<ArgumentOutOfRangeException>(() => ((IpccSourceDiscoveryMode)999).ToWireName());
        Assert.Throws<ArgumentOutOfRangeException>(() => ((IpccSourceDiscoveryStatus)999).ToWireName());
    }
}
