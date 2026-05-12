using System.Reflection;
using System.Security.Cryptography;
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
