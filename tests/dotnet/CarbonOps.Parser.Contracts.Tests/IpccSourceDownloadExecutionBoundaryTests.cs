using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class IpccSourceDownloadExecutionBoundaryTests
{
    private static readonly DateTimeOffset RetrievedAt =
        new(2026, 5, 12, 10, 30, 0, TimeSpan.FromHours(3));

    [Fact]
    public void RequestFromDiscoveryCandidateIsExplicitOptIn()
    {
        var candidate = DownloadableCandidate();
        using var temp = new TemporaryDirectory();

        var request = IpccSourceDownloadExecutionBoundary.CreateRequest(
            candidate,
            temp.Path,
            "ipcc/efdb.xlsx");

        Assert.Equal(SourceFamily.IpccEfdb, request.SourceFamily);
        Assert.Equal("ipcc_efdb", request.SourceKey);
        Assert.Equal("ipcc_source_discovery_candidate_001_ipcc_efdb", request.CandidateId);
        Assert.Equal("IPCC EFDB", request.CandidateTitle);
        Assert.Equal("mock://ipcc_efdb/efdb.xlsx", request.SourceReferenceUri);
        Assert.Equal("xlsx", request.ArtifactKind);
        Assert.True(request.CandidateDownloadAllowed);
        Assert.False(request.AllowDownloadExecution);
        Assert.False(request.AllowFileWrite);
        Assert.Equal("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", request.ContentType);
        Assert.Equal(".xlsx", request.Extension);
        Assert.Equal(2006, request.DocumentYear);
        Assert.Equal(2024, request.ReportingYear);
        Assert.Equal("efdb-v2024", request.VersionLabel);

        var validation = IpccSourceDownloadExecutionBoundary.Validate(request);

        Assert.False(validation.IsValid);
        Assert.Equal(
            [
                "IPCC_SOURCE_DOWNLOAD_EXECUTION_NOT_ALLOWED",
                "IPCC_SOURCE_DOWNLOAD_FILE_WRITE_NOT_ALLOWED",
            ],
            validation.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void DefaultDiscoveryCandidateIsNotDownloadable()
    {
        using var temp = new TemporaryDirectory();
        var candidate = IpccSourceDiscoveryBoundary.CreateResult().Candidates[0];
        var request = IpccSourceDownloadExecutionBoundary.CreateRequest(
            candidate,
            temp.Path,
            "ipcc/source.discovery",
            allowDownloadExecution: true,
            allowFileWrite: true);

        var result = IpccSourceDownloadExecutionBoundary.Execute(request, UnexpectedTransport);

        Assert.Equal(IpccSourceDownloadExecutionStatus.Blocked, result.Status);
        Assert.False(result.Downloaded);
        Assert.Null(result.Artifact);
        Assert.Equal(
            [
                "IPCC_SOURCE_DOWNLOAD_CANDIDATE_NOT_DOWNLOADABLE",
                "IPCC_SOURCE_DOWNLOAD_DISCOVERY_REFERENCE_NOT_DOWNLOADABLE",
            ],
            result.Issues.Select(issue => issue.Code));
        Assert.False(File.Exists(Path.Combine(temp.Path, "ipcc/source.discovery")));
    }

    [Theory]
    [InlineData(
        "source_reference_uri",
        "https://example.invalid/ipcc.xlsx",
        "IPCC_SOURCE_DOWNLOAD_NETWORK_NOT_ALLOWED")]
    [InlineData(
        "source_reference_uri",
        "http://example.invalid/ipcc.xlsx",
        "IPCC_SOURCE_DOWNLOAD_INSECURE_HTTP_NOT_ALLOWED")]
    [InlineData(
        "source_reference_uri",
        "file:///tmp/ipcc.xlsx",
        "IPCC_SOURCE_DOWNLOAD_UNSAFE_SOURCE_REFERENCE_URI")]
    [InlineData(
        "source_reference_uri",
        "ipcc/efdb.xlsx",
        "IPCC_SOURCE_DOWNLOAD_SOURCE_REFERENCE_URI_MISSING_SCHEME")]
    [InlineData("target_root", "relative/root", "IPCC_SOURCE_DOWNLOAD_TARGET_ROOT_NOT_ABSOLUTE")]
    [InlineData("target_relative_path", "../outside.xlsx", "IPCC_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_UNSAFE")]
    [InlineData("target_relative_path", "/absolute.xlsx", "IPCC_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_ABSOLUTE")]
    public void UnsafeRequestInputsFailClosed(string fieldName, string value, string expectedCode)
    {
        using var temp = new TemporaryDirectory();
        var request = WithField(ValidRequest(temp.Path), fieldName, value);

        var validation = IpccSourceDownloadExecutionBoundary.Validate(request);

        Assert.False(validation.IsValid);
        Assert.Contains(expectedCode, validation.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void SuccessfulDownloadUsesDiscoveryMetadataAndInjectedTransport()
    {
        using var temp = new TemporaryDirectory();
        var payload = "deterministic ipcc source bytes"u8.ToArray();
        var checksum = Convert.ToHexString(SHA256.HashData(payload)).ToLowerInvariant();
        var calls = new List<string>();
        var request = ValidRequest(temp.Path) with { ExpectedChecksumSha256 = checksum };

        var result = IpccSourceDownloadExecutionBoundary.Execute(
            request,
            sourceReferenceUri =>
            {
                calls.Add(sourceReferenceUri);
                return new IpccSourceDownloadTransportResponse(
                    payload,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "mock://ipcc_efdb/final.xlsx");
            },
            () => RetrievedAt);

        var targetPath = Path.Combine(temp.Path, "ipcc/efdb.xlsx");
        Assert.Equal(["mock://ipcc_efdb/efdb.xlsx"], calls);
        Assert.Equal(payload, File.ReadAllBytes(targetPath));
        Assert.Equal(IpccSourceDownloadExecutionStatus.Downloaded, result.Status);
        Assert.True(result.Downloaded);
        Assert.False(result.AlreadyKnown);
        Assert.Equal(
            new IpccSourceDownloadedArtifact(
                SourceFamily.IpccEfdb,
                "ipcc_efdb",
                "ipcc_source_discovery_candidate_001_ipcc_efdb",
                "ipcc_source_download_artifact_ipcc_source_discovery_candidate_001_ipcc_efdb",
                "xlsx",
                "mock://ipcc_efdb/efdb.xlsx",
                targetPath,
                "efdb.xlsx",
                checksum,
                payload.LongLength,
                RetrievedAt.ToUniversalTime(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ".xlsx",
                "mock://ipcc_efdb/final.xlsx",
                DocumentYear: 2006,
                ReportingYear: 2024,
                VersionLabel: "efdb-v2024"),
            result.Artifact);
        Assert.True(IpccSourceDownloadExecutionBoundary.Validate(result).IsValid);
    }

    [Fact]
    public void DownloadExecutionMatchesSharedParityFixture()
    {
        using var document = JsonDocument.Parse(File.ReadAllText(ParityFixturePath()));
        var fixture = document.RootElement;
        using var temp = new TemporaryDirectory();

        var successfulFixture = fixture.GetProperty("successful_download");
        var request = FixtureRequest(temp.Path, fixture) with
        {
            ExpectedChecksumSha256 = RequiredString(successfulFixture, "checksum_sha256"),
        };
        var payload = Encoding.UTF8.GetBytes(RequiredString(successfulFixture, "payload_text"));

        var successful = IpccSourceDownloadExecutionBoundary.Execute(
            request,
            _ => new IpccSourceDownloadTransportResponse(
                payload,
                RequiredString(fixture, "content_type"),
                RequiredString(successfulFixture, "final_uri")),
            () => RetrievedAt);

        Assert.Equal(RequiredString(successfulFixture, "status"), successful.Status.ToWireName());
        Assert.Equal(successfulFixture.GetProperty("downloaded").GetBoolean(), successful.Downloaded);
        Assert.Equal(successfulFixture.GetProperty("already_known").GetBoolean(), successful.AlreadyKnown);
        Assert.NotNull(successful.Artifact);
        Assert.Equal(SourceFamily.IpccEfdb, successful.Artifact.SourceFamily);
        Assert.Equal(RequiredString(fixture, "source_key"), successful.Artifact.SourceKey);
        Assert.Equal(RequiredString(fixture, "candidate_id"), successful.Artifact.CandidateId);
        Assert.Equal(RequiredString(fixture, "artifact_kind"), successful.Artifact.ArtifactKind);
        Assert.Equal(RequiredString(successfulFixture, "checksum_sha256"), successful.Artifact.ChecksumSha256);
        Assert.Equal(successfulFixture.GetProperty("size_bytes").GetInt64(), successful.Artifact.SizeBytes);
        Assert.Equal(RequiredString(fixture, "content_type"), successful.Artifact.ContentType);
        Assert.Equal(RequiredString(fixture, "extension"), successful.Artifact.Extension);
        Assert.Equal(RequiredString(successfulFixture, "final_uri"), successful.Artifact.FinalUri);
        Assert.Equal(fixture.GetProperty("document_year").GetInt32(), successful.Artifact.DocumentYear);
        Assert.Equal(fixture.GetProperty("reporting_year").GetInt32(), successful.Artifact.ReportingYear);
        Assert.Equal(RequiredString(fixture, "version_label"), successful.Artifact.VersionLabel);
        AssertIssueCodes(successful.Issues, successfulFixture);

        var existingFixture = fixture.GetProperty("existing_known_document");
        using var existingTemp = new TemporaryDirectory();
        var existingRequest = FixtureRequest(existingTemp.Path, fixture) with
        {
            ExpectedChecksumSha256 = RequiredString(existingFixture, "checksum_sha256"),
        };
        var existingTarget = Path.Combine(existingTemp.Path, RequiredString(fixture, "target_relative_path"));
        Directory.CreateDirectory(Path.GetDirectoryName(existingTarget)!);
        File.WriteAllBytes(
            existingTarget,
            Encoding.UTF8.GetBytes(RequiredString(existingFixture, "payload_text")));

        var existing = IpccSourceDownloadExecutionBoundary.Execute(
            existingRequest,
            UnexpectedTransport,
            () => RetrievedAt);
        var dotnetExisting = existingFixture.GetProperty("dotnet");

        Assert.Equal(RequiredString(dotnetExisting, "status"), existing.Status.ToWireName());
        Assert.Equal(dotnetExisting.GetProperty("downloaded").GetBoolean(), existing.Downloaded);
        Assert.Equal(dotnetExisting.GetProperty("already_known").GetBoolean(), existing.AlreadyKnown);
        Assert.NotNull(existing.Artifact);
        Assert.Equal(RequiredString(existingFixture, "checksum_sha256"), existing.Artifact.ChecksumSha256);
        Assert.Equal(existingFixture.GetProperty("size_bytes").GetInt64(), existing.Artifact.SizeBytes);
        AssertIssueCodes(existing.Issues, existingFixture);

        var mismatchFixture = fixture.GetProperty("checksum_mismatch");
        var mismatch = IpccSourceDownloadExecutionBoundary.Execute(
            FixtureRequest(Path.Combine(temp.Path, "mismatch"), fixture) with
            {
                ExpectedChecksumSha256 = RequiredString(mismatchFixture, "expected_checksum_sha256"),
            },
            _ => new IpccSourceDownloadTransportResponse(
                Encoding.UTF8.GetBytes(RequiredString(mismatchFixture, "payload_text"))));

        Assert.Equal(RequiredString(mismatchFixture, "status"), mismatch.Status.ToWireName());
        Assert.Null(mismatch.Artifact);
        AssertIssueCodes(mismatch.Issues, mismatchFixture);

        var blankMetadataFixture = fixture.GetProperty("blank_response_metadata");
        var blankMetadata = IpccSourceDownloadExecutionBoundary.Execute(
            FixtureRequest(Path.Combine(temp.Path, "blank-metadata"), fixture),
            _ => new IpccSourceDownloadTransportResponse("content"u8.ToArray(), " ", " "));

        Assert.Equal(RequiredString(blankMetadataFixture, "status"), blankMetadata.Status.ToWireName());
        Assert.Null(blankMetadata.Artifact);
        AssertIssueCodes(blankMetadata.Issues, blankMetadataFixture);

        var defaultCandidateFixture = fixture.GetProperty("default_candidate_blocked");
        var defaultCandidateRequest = IpccSourceDownloadExecutionBoundary.CreateRequest(
            IpccSourceDiscoveryBoundary.CreateResult().Candidates[0],
            Path.Combine(temp.Path, "default-candidate"),
            RequiredString(fixture, "target_relative_path"),
            allowDownloadExecution: true,
            allowFileWrite: true);

        var defaultCandidate = IpccSourceDownloadExecutionBoundary.Execute(
            defaultCandidateRequest,
            UnexpectedTransport);

        Assert.Equal(RequiredString(defaultCandidateFixture, "status"), defaultCandidate.Status.ToWireName());
        Assert.Null(defaultCandidate.Artifact);
        AssertIssueCodes(defaultCandidate.Issues, defaultCandidateFixture);
    }

    [Fact]
    public void ExistingKnownDocumentIsIdempotentAndDoesNotCallTransport()
    {
        using var temp = new TemporaryDirectory();
        var payload = "deterministic ipcc source bytes"u8.ToArray();
        var checksum = Convert.ToHexString(SHA256.HashData(payload)).ToLowerInvariant();
        var request = ValidRequest(temp.Path) with { ExpectedChecksumSha256 = checksum };
        var targetPath = Path.Combine(temp.Path, request.TargetRelativePath);
        Directory.CreateDirectory(Path.GetDirectoryName(targetPath)!);
        File.WriteAllBytes(targetPath, payload);

        var result = IpccSourceDownloadExecutionBoundary.Execute(
            request,
            UnexpectedTransport,
            () => RetrievedAt);

        Assert.Equal(IpccSourceDownloadExecutionStatus.AlreadyKnown, result.Status);
        Assert.False(result.Downloaded);
        Assert.True(result.AlreadyKnown);
        Assert.Empty(result.Issues);
        Assert.NotNull(result.Artifact);
        Assert.Equal(checksum, result.Artifact.ChecksumSha256);
        Assert.Equal(targetPath, result.Artifact.LocalPath);
        Assert.Equal(RetrievedAt.ToUniversalTime(), result.Artifact.RetrievedAtUtc);
        Assert.True(IpccSourceDownloadExecutionBoundary.Validate(result).IsValid);
    }

    [Fact]
    public void ExistingUnknownDocumentBlocksBeforeTransport()
    {
        using var temp = new TemporaryDirectory();
        var request = ValidRequest(temp.Path);
        var targetPath = Path.Combine(temp.Path, request.TargetRelativePath);
        Directory.CreateDirectory(Path.GetDirectoryName(targetPath)!);
        File.WriteAllBytes(targetPath, "existing"u8.ToArray());

        var result = IpccSourceDownloadExecutionBoundary.Execute(request, UnexpectedTransport);

        Assert.Equal(IpccSourceDownloadExecutionStatus.Blocked, result.Status);
        Assert.Equal(["IPCC_SOURCE_DOWNLOAD_TARGET_EXISTS"], result.Issues.Select(issue => issue.Code));
        Assert.Equal("existing"u8.ToArray(), File.ReadAllBytes(targetPath));
    }

    [Fact]
    public void ChecksumMismatchFailsWithoutWritingFile()
    {
        using var temp = new TemporaryDirectory();
        var request = ValidRequest(temp.Path) with { ExpectedChecksumSha256 = new string('a', 64) };

        var result = IpccSourceDownloadExecutionBoundary.Execute(
            request,
            _ => new IpccSourceDownloadTransportResponse("unexpected"u8.ToArray()));

        Assert.Equal(IpccSourceDownloadExecutionStatus.Failed, result.Status);
        Assert.Null(result.Artifact);
        Assert.Equal(["IPCC_SOURCE_DOWNLOAD_CHECKSUM_MISMATCH"], result.Issues.Select(issue => issue.Code));
        Assert.False(File.Exists(Path.Combine(temp.Path, request.TargetRelativePath)));
    }

    [Fact]
    public void ResultValidationRejectsNonUtcRetrievalTimestamp()
    {
        using var temp = new TemporaryDirectory();
        var payload = "content"u8.ToArray();
        var result = IpccSourceDownloadExecutionBoundary.Execute(
            ValidRequest(temp.Path),
            _ => new IpccSourceDownloadTransportResponse(payload),
            () => RetrievedAt) with
        {
            Artifact = new IpccSourceDownloadedArtifact(
                SourceFamily.IpccEfdb,
                "ipcc_efdb",
                "ipcc_source_discovery_candidate_001_ipcc_efdb",
                "ipcc_source_download_artifact_ipcc_source_discovery_candidate_001_ipcc_efdb",
                "xlsx",
                "mock://ipcc_efdb/efdb.xlsx",
                Path.Combine(temp.Path, "ipcc/efdb.xlsx"),
                "efdb.xlsx",
                Convert.ToHexString(SHA256.HashData(payload)).ToLowerInvariant(),
                payload.LongLength,
                RetrievedAt),
        };

        var validation = IpccSourceDownloadExecutionBoundary.Validate(result);

        Assert.False(validation.IsValid);
        Assert.Equal(
            ["IPCC_SOURCE_DOWNLOAD_ARTIFACT_RETRIEVED_AT_NOT_UTC"],
            validation.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void BoundaryPublicSurfaceOnlyExposesExplicitExecutionMethods()
    {
        var publicMethodNames = typeof(IpccSourceDownloadExecutionBoundary)
            .GetMethods(BindingFlags.Public | BindingFlags.Static | BindingFlags.DeclaredOnly)
            .Select(method => method.Name)
            .ToArray();

        Assert.Contains("CreateRequest", publicMethodNames);
        Assert.Contains("Execute", publicMethodNames);
        Assert.Equal(2, publicMethodNames.Count(methodName => methodName == "Validate"));
        Assert.DoesNotContain("Parse", publicMethodNames);
        Assert.DoesNotContain("Persist", publicMethodNames);
        Assert.DoesNotContain("Schedule", publicMethodNames);
    }

    [Fact]
    public void IpccDownloadExecutionWireNamesArePythonAligned()
    {
        Assert.Equal("blocked", IpccSourceDownloadExecutionStatus.Blocked.ToWireName());
        Assert.Equal("downloaded", IpccSourceDownloadExecutionStatus.Downloaded.ToWireName());
        Assert.Equal("failed", IpccSourceDownloadExecutionStatus.Failed.ToWireName());
        Assert.Equal("already_known", IpccSourceDownloadExecutionStatus.AlreadyKnown.ToWireName());
        Assert.True(ContractWireNames.TryParseIpccSourceDownloadExecutionStatusWireName(
            "already_known",
            out var parsed));
        Assert.Equal(IpccSourceDownloadExecutionStatus.AlreadyKnown, parsed);
        Assert.False(ContractWireNames.TryParseIpccSourceDownloadExecutionStatusWireName("unknown", out _));
        Assert.Throws<ArgumentOutOfRangeException>(() => ((IpccSourceDownloadExecutionStatus)999).ToWireName());
    }

    private static IpccSourceDownloadExecutionRequest ValidRequest(string targetRoot) =>
        IpccSourceDownloadExecutionBoundary.CreateRequest(
            DownloadableCandidate(),
            targetRoot,
            "ipcc/efdb.xlsx",
            allowDownloadExecution: true,
            allowFileWrite: true);

    private static IpccSourceDownloadExecutionRequest FixtureRequest(
        string targetRoot,
        JsonElement fixture) =>
        IpccSourceDownloadExecutionBoundary.CreateRequest(
            new IpccSourceDocumentCandidate(
                SourceFamily.IpccEfdb,
                RequiredString(fixture, "source_key"),
                RequiredString(fixture, "candidate_id"),
                RequiredString(fixture, "candidate_title"),
                RequiredString(fixture, "source_reference_uri"),
                RequiredString(fixture, "artifact_kind"),
                documentYear: fixture.GetProperty("document_year").GetInt32(),
                reportingYear: fixture.GetProperty("reporting_year").GetInt32(),
                contentType: RequiredString(fixture, "content_type"),
                extension: RequiredString(fixture, "extension"),
                versionLabel: RequiredString(fixture, "version_label"),
                downloadAllowed: true),
            targetRoot,
            RequiredString(fixture, "target_relative_path"),
            allowDownloadExecution: true,
            allowFileWrite: true);

    private static IpccSourceDocumentCandidate DownloadableCandidate() =>
        new(
            SourceFamily.IpccEfdb,
            "ipcc_efdb",
            "ipcc_source_discovery_candidate_001_ipcc_efdb",
            "IPCC EFDB",
            "mock://ipcc_efdb/efdb.xlsx",
            "xlsx",
            documentYear: 2006,
            reportingYear: 2024,
            contentType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            extension: ".xlsx",
            versionLabel: "efdb-v2024",
            downloadAllowed: true);

    private static IpccSourceDownloadExecutionRequest WithField(
        IpccSourceDownloadExecutionRequest request,
        string fieldName,
        string value) =>
        fieldName switch
        {
            "source_reference_uri" => request with { SourceReferenceUri = value },
            "target_root" => request with { TargetRoot = value },
            "target_relative_path" => request with { TargetRelativePath = value },
            _ => throw new ArgumentOutOfRangeException(nameof(fieldName), fieldName, "Unknown test field."),
        };

    private static IpccSourceDownloadTransportResponse UnexpectedTransport(string sourceReferenceUri) =>
        throw new InvalidOperationException($"transport should not be called for {sourceReferenceUri}");

    private static void AssertIssueCodes(
        IReadOnlyList<IpccSourceDownloadExecutionIssue> issues,
        JsonElement fixture)
    {
        Assert.Equal(
            fixture
                .GetProperty("issue_codes")
                .EnumerateArray()
                .Select(code => code.GetString() ?? string.Empty),
            issues.Select(issue => issue.Code));
    }

    private static string RequiredString(JsonElement element, string propertyName) =>
        element.GetProperty(propertyName).GetString()
        ?? throw new InvalidOperationException($"Missing string property {propertyName}.");

    private static string ParityFixturePath()
    {
        var current = new DirectoryInfo(AppContext.BaseDirectory);
        while (current is not null)
        {
            var candidate = Path.Combine(
                current.FullName,
                "tests",
                "fixtures",
                "parity",
                "ipcc_source_download_execution_expectations.json");
            if (File.Exists(candidate))
            {
                return candidate;
            }

            current = current.Parent;
        }

        throw new FileNotFoundException("IPCC source download parity fixture was not found.");
    }

    private sealed class TemporaryDirectory : IDisposable
    {
        public string Path { get; } = System.IO.Path.Combine(
            System.IO.Path.GetTempPath(),
            $"carbonops-ipcc-download-{Guid.NewGuid():N}");

        public TemporaryDirectory()
        {
            Directory.CreateDirectory(Path);
        }

        public void Dispose()
        {
            if (Directory.Exists(Path))
            {
                Directory.Delete(Path, recursive: true);
            }
        }
    }
}
