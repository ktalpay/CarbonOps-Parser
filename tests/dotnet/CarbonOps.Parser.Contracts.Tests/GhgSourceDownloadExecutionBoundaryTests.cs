using System.Reflection;
using System.Security.Cryptography;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class GhgSourceDownloadExecutionBoundaryTests
{
    [Fact]
    public void RequestFromCandidateIsExplicitOptIn()
    {
        var candidate = DownloadableCandidate();
        using var temp = new TemporaryDirectory();

        var request = GhgSourceDownloadExecutionBoundary.CreateRequest(
            candidate,
            temp.Path,
            "ghg/corporate-standard.pdf");

        Assert.Equal(SourceFamily.GhgProtocol, request.SourceFamily);
        Assert.Equal("ghg_protocol", request.SourceKey);
        Assert.Equal("ghg_source_discovery_candidate_001_ghg_protocol", request.CandidateId);
        Assert.Equal("GHG Protocol", request.CandidateTitle);
        Assert.Equal("mock://ghg_protocol/corporate-standard.pdf", request.SourceReferenceUri);
        Assert.Equal("pdf", request.ArtifactKind);
        Assert.True(request.CandidateDownloadAllowed);
        Assert.False(request.AllowDownloadExecution);
        Assert.False(request.AllowFileWrite);
        Assert.Equal("application/pdf", request.ContentType);
        Assert.Equal(".pdf", request.Extension);
        Assert.Equal("dn046_mock_download", request.VersionLabel);

        var validation = GhgSourceDownloadExecutionBoundary.Validate(request);

        Assert.False(validation.IsValid);
        Assert.Equal(
            [
                "GHG_SOURCE_DOWNLOAD_EXECUTION_NOT_ALLOWED",
                "GHG_SOURCE_DOWNLOAD_FILE_WRITE_NOT_ALLOWED",
            ],
            validation.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void DefaultDiscoveryCandidateIsNotDownloadable()
    {
        using var temp = new TemporaryDirectory();
        var candidate = GhgSourceDiscoveryBoundary.CreateResult().Candidates[0];
        var request = GhgSourceDownloadExecutionBoundary.CreateRequest(
            candidate,
            temp.Path,
            "ghg/source.discovery",
            allowDownloadExecution: true,
            allowFileWrite: true);

        var result = GhgSourceDownloadExecutionBoundary.Execute(request, UnexpectedTransport);

        Assert.Equal(GhgSourceDownloadExecutionStatus.Blocked, result.Status);
        Assert.False(result.Downloaded);
        Assert.Null(result.Artifact);
        Assert.Equal(
            [
                "GHG_SOURCE_DOWNLOAD_CANDIDATE_NOT_DOWNLOADABLE",
                "GHG_SOURCE_DOWNLOAD_DISCOVERY_REFERENCE_NOT_DOWNLOADABLE",
            ],
            result.Issues.Select(issue => issue.Code));
        Assert.False(File.Exists(Path.Combine(temp.Path, "ghg/source.discovery")));
    }

    [Fact]
    public void InvalidDownloadRequestFailsClosedBeforeTransport()
    {
        using var temp = new TemporaryDirectory();
        var request = ValidRequest(temp.Path) with
        {
            SourceFamily = SourceFamily.DefraDesnz,
            SourceKey = "defra_desnz",
            AllowParse = true,
            AllowDatabaseWrites = true,
            AllowScheduler = true,
        };

        var result = GhgSourceDownloadExecutionBoundary.Execute(request, UnexpectedTransport);

        Assert.Equal(GhgSourceDownloadExecutionStatus.Blocked, result.Status);
        Assert.False(result.Downloaded);
        Assert.Null(result.Artifact);
        Assert.True(result.NoParse);
        Assert.True(result.NoDatabaseWrites);
        Assert.True(result.NoSql);
        Assert.True(result.NoScheduler);
        Assert.Equal(
            [
                "GHG_SOURCE_DOWNLOAD_SOURCE_FAMILY_MISMATCH",
                "GHG_SOURCE_DOWNLOAD_SOURCE_KEY_MISMATCH",
                "GHG_SOURCE_DOWNLOAD_PARSE_NOT_ALLOWED",
                "GHG_SOURCE_DOWNLOAD_DATABASE_WRITES_NOT_ALLOWED",
                "GHG_SOURCE_DOWNLOAD_SCHEDULER_NOT_ALLOWED",
            ],
            result.Issues.Select(issue => issue.Code));
    }

    [Theory]
    [InlineData("source_reference_uri", "https://example.invalid/ghg.pdf", "GHG_SOURCE_DOWNLOAD_NETWORK_NOT_ALLOWED")]
    [InlineData("source_reference_uri", "http://example.invalid/ghg.pdf", "GHG_SOURCE_DOWNLOAD_INSECURE_HTTP_NOT_ALLOWED")]
    [InlineData("source_reference_uri", "file:///tmp/ghg.pdf", "GHG_SOURCE_DOWNLOAD_UNSAFE_SOURCE_REFERENCE_URI")]
    [InlineData("source_reference_uri", "s3://bucket/ghg.pdf", "GHG_SOURCE_DOWNLOAD_UNSAFE_SOURCE_REFERENCE_URI")]
    [InlineData("source_reference_uri", "ghg/corporate-standard.pdf", "GHG_SOURCE_DOWNLOAD_SOURCE_REFERENCE_URI_MISSING_SCHEME")]
    [InlineData("source_reference_uri", "://ghg/corporate-standard.pdf", "GHG_SOURCE_DOWNLOAD_MALFORMED_SOURCE_REFERENCE_URI")]
    [InlineData("source_reference_uri", "https:///ghg.pdf", "GHG_SOURCE_DOWNLOAD_MALFORMED_SOURCE_REFERENCE_URI")]
    [InlineData("target_root", "relative/root", "GHG_SOURCE_DOWNLOAD_TARGET_ROOT_NOT_ABSOLUTE")]
    [InlineData("target_relative_path", "../outside.pdf", "GHG_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_UNSAFE")]
    [InlineData("target_relative_path", "/absolute.pdf", "GHG_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_ABSOLUTE")]
    [InlineData("target_relative_path", "download://ghg/source.pdf", "GHG_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_URI")]
    public void UnsafeRequestInputsFailClosed(string fieldName, string value, string expectedCode)
    {
        using var temp = new TemporaryDirectory();
        var request = WithField(ValidRequest(temp.Path), fieldName, value);

        var validation = GhgSourceDownloadExecutionBoundary.Validate(request);

        Assert.False(validation.IsValid);
        Assert.Contains(expectedCode, validation.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void SuccessfulDownloadIsExplicitAndUsesInjectedTransport()
    {
        using var temp = new TemporaryDirectory();
        var payload = "deterministic ghg source bytes"u8.ToArray();
        var calls = new List<string>();
        var request = ValidRequest(temp.Path);

        var result = GhgSourceDownloadExecutionBoundary.Execute(
            request,
            sourceReferenceUri =>
            {
                calls.Add(sourceReferenceUri);
                return new GhgSourceDownloadTransportResponse(
                    payload,
                    "application/pdf",
                    "mock://ghg_protocol/final.pdf");
            });

        var targetPath = Path.Combine(temp.Path, "ghg/corporate-standard.pdf");
        var checksum = Convert.ToHexString(SHA256.HashData(payload)).ToLowerInvariant();
        Assert.Equal(["mock://ghg_protocol/corporate-standard.pdf"], calls);
        Assert.Equal(payload, File.ReadAllBytes(targetPath));
        Assert.Equal(GhgSourceDownloadExecutionStatus.Downloaded, result.Status);
        Assert.True(result.Downloaded);
        Assert.Equal(
            new GhgSourceDownloadedArtifact(
                SourceFamily.GhgProtocol,
                "ghg_protocol",
                "ghg_source_discovery_candidate_001_ghg_protocol",
                "ghg_source_download_artifact_ghg_source_discovery_candidate_001_ghg_protocol",
                "pdf",
                "mock://ghg_protocol/corporate-standard.pdf",
                targetPath,
                "corporate-standard.pdf",
                checksum,
                payload.LongLength,
                "application/pdf",
                ".pdf",
                "mock://ghg_protocol/final.pdf",
                VersionLabel: "dn046_mock_download"),
            result.Artifact);
        Assert.True(GhgSourceDownloadExecutionBoundary.Validate(result).IsValid);
    }

    [Fact]
    public void TargetExistsBlocksBeforeTransportByDefault()
    {
        using var temp = new TemporaryDirectory();
        var request = ValidRequest(temp.Path);
        var targetPath = Path.Combine(temp.Path, request.TargetRelativePath);
        Directory.CreateDirectory(Path.GetDirectoryName(targetPath)!);
        File.WriteAllBytes(targetPath, "existing"u8.ToArray());

        var result = GhgSourceDownloadExecutionBoundary.Execute(request, UnexpectedTransport);

        Assert.Equal(GhgSourceDownloadExecutionStatus.Blocked, result.Status);
        Assert.Equal(["GHG_SOURCE_DOWNLOAD_TARGET_EXISTS"], result.Issues.Select(issue => issue.Code));
        Assert.Equal("existing"u8.ToArray(), File.ReadAllBytes(targetPath));
    }

    [Fact]
    public void ExistingFinalTargetSymlinkIsRejected()
    {
        if (OperatingSystem.IsWindows())
        {
            return;
        }

        using var temp = new TemporaryDirectory();
        var outside = Path.Combine(temp.Path, "outside");
        var targetParent = Path.Combine(temp.Path, "target-root", "ghg");
        Directory.CreateDirectory(outside);
        Directory.CreateDirectory(targetParent);
        var targetPath = Path.Combine(targetParent, "escape.pdf");
        File.CreateSymbolicLink(targetPath, Path.Combine(outside, "escape.pdf"));
        var request = ValidRequest(Path.Combine(temp.Path, "target-root")) with
        {
            TargetRelativePath = "ghg/escape.pdf",
            AllowOverwrite = true,
        };

        var result = GhgSourceDownloadExecutionBoundary.Execute(
            request,
            _ => new GhgSourceDownloadTransportResponse("escape"u8.ToArray()));

        Assert.Equal(GhgSourceDownloadExecutionStatus.Blocked, result.Status);
        Assert.Null(result.Artifact);
        Assert.Equal(["GHG_SOURCE_DOWNLOAD_TARGET_SYMLINK_UNSAFE"], result.Issues.Select(issue => issue.Code));
        Assert.False(File.Exists(Path.Combine(outside, "escape.pdf")));
    }

    [Fact]
    public void ParentSymlinkSwapDuringTransportCannotEscapeTargetRoot()
    {
        if (OperatingSystem.IsWindows())
        {
            return;
        }

        using var temp = new TemporaryDirectory();
        var targetRoot = Path.Combine(temp.Path, "target-root");
        var outside = Path.Combine(temp.Path, "outside");
        var targetParent = Path.Combine(targetRoot, "ghg");
        Directory.CreateDirectory(targetParent);
        Directory.CreateDirectory(outside);
        var request = ValidRequest(targetRoot) with { TargetRelativePath = "ghg/escape.pdf" };

        var result = GhgSourceDownloadExecutionBoundary.Execute(
            request,
            _ =>
            {
                Directory.Delete(targetParent, recursive: true);
                Directory.CreateSymbolicLink(targetParent, outside);
                return new GhgSourceDownloadTransportResponse("escape"u8.ToArray());
            });

        Assert.NotEqual(GhgSourceDownloadExecutionStatus.Downloaded, result.Status);
        Assert.False(result.Downloaded);
        Assert.Null(result.Artifact);
        Assert.False(File.Exists(Path.Combine(outside, "escape.pdf")));
        Assert.True(Directory.Exists(targetParent));
    }

    [Fact]
    public void ChecksumMismatchFailsWithoutWritingFile()
    {
        using var temp = new TemporaryDirectory();
        var request = ValidRequest(temp.Path) with { ExpectedChecksumSha256 = new string('a', 64) };

        var result = GhgSourceDownloadExecutionBoundary.Execute(
            request,
            _ => new GhgSourceDownloadTransportResponse("unexpected"u8.ToArray()));

        Assert.Equal(GhgSourceDownloadExecutionStatus.Failed, result.Status);
        Assert.Null(result.Artifact);
        Assert.Equal(["GHG_SOURCE_DOWNLOAD_CHECKSUM_MISMATCH"], result.Issues.Select(issue => issue.Code));
        Assert.False(File.Exists(Path.Combine(temp.Path, request.TargetRelativePath)));
    }

    [Fact]
    public void TransportErrorsAndEmptyContentAreFailedResults()
    {
        using var temp = new TemporaryDirectory();
        using var other = new TemporaryDirectory();

        var failed = GhgSourceDownloadExecutionBoundary.Execute(
            ValidRequest(temp.Path),
            _ => throw new InvalidOperationException("offline"));
        var empty = GhgSourceDownloadExecutionBoundary.Execute(
            ValidRequest(other.Path),
            _ => new GhgSourceDownloadTransportResponse(Array.Empty<byte>()));

        Assert.Equal(GhgSourceDownloadExecutionStatus.Failed, failed.Status);
        Assert.Equal(["GHG_SOURCE_DOWNLOAD_TRANSPORT_FAILED"], failed.Issues.Select(issue => issue.Code));
        Assert.Equal(GhgSourceDownloadExecutionStatus.Failed, empty.Status);
        Assert.Equal(["GHG_SOURCE_DOWNLOAD_RESPONSE_EMPTY_CONTENT"], empty.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void TransportResponseValidationFailsClosed()
    {
        using var missing = new TemporaryDirectory();
        using var missingContent = new TemporaryDirectory();
        using var blankMetadata = new TemporaryDirectory();

        var missingResponse = GhgSourceDownloadExecutionBoundary.Execute(
            ValidRequest(missing.Path),
            _ => null!);
        var missingContentResponse = GhgSourceDownloadExecutionBoundary.Execute(
            ValidRequest(missingContent.Path),
            _ => new GhgSourceDownloadTransportResponse(null!));
        var blankMetadataResponse = GhgSourceDownloadExecutionBoundary.Execute(
            ValidRequest(blankMetadata.Path),
            _ => new GhgSourceDownloadTransportResponse("content"u8.ToArray(), " ", " "));

        Assert.Equal(GhgSourceDownloadExecutionStatus.Failed, missingResponse.Status);
        Assert.Equal(["GHG_SOURCE_DOWNLOAD_RESPONSE_MISSING"], missingResponse.Issues.Select(issue => issue.Code));
        Assert.Equal(GhgSourceDownloadExecutionStatus.Failed, missingContentResponse.Status);
        Assert.Equal(
            ["GHG_SOURCE_DOWNLOAD_RESPONSE_MISSING_CONTENT"],
            missingContentResponse.Issues.Select(issue => issue.Code));
        Assert.Equal(GhgSourceDownloadExecutionStatus.Failed, blankMetadataResponse.Status);
        Assert.Equal(
            [
                "GHG_SOURCE_DOWNLOAD_RESPONSE_BLANK_CONTENT_TYPE",
                "GHG_SOURCE_DOWNLOAD_RESPONSE_BLANK_FINAL_URI",
            ],
            blankMetadataResponse.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void ResultValidationRejectsSideEffectFlags()
    {
        using var temp = new TemporaryDirectory();
        var result = GhgSourceDownloadExecutionBoundary.Execute(
            ValidRequest(temp.Path),
            _ => new GhgSourceDownloadTransportResponse("content"u8.ToArray())) with
        {
            NoDatabaseWrites = false,
            NoSql = false,
        };

        var validation = GhgSourceDownloadExecutionBoundary.Validate(result);

        Assert.False(validation.IsValid);
        Assert.Equal(
            [
                "GHG_SOURCE_DOWNLOAD_RESULT_SIDE_EFFECT_FLAG_ENABLED",
                "GHG_SOURCE_DOWNLOAD_RESULT_SIDE_EFFECT_FLAG_ENABLED",
            ],
            validation.Issues.Select(issue => issue.Code));
        Assert.Equal(["no_database_writes", "no_sql"], validation.Issues.Select(issue => issue.FieldName));
    }

    [Theory]
    [InlineData(GhgSourceDownloadExecutionStatus.Blocked)]
    [InlineData(GhgSourceDownloadExecutionStatus.Failed)]
    public void ResultValidationRejectsBlockedOrFailedResultsWithoutIssues(GhgSourceDownloadExecutionStatus status)
    {
        using var temp = new TemporaryDirectory();
        var result = new GhgSourceDownloadExecutionResult(status, ValidRequest(temp.Path));

        var validation = GhgSourceDownloadExecutionBoundary.Validate(result);

        Assert.False(validation.IsValid);
        Assert.Equal(["GHG_SOURCE_DOWNLOAD_RESULT_MISSING_ISSUES"], validation.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void BoundaryPublicSurfaceOnlyExposesExplicitExecutionMethods()
    {
        var publicMethodNames = typeof(GhgSourceDownloadExecutionBoundary)
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
    public void GhgDownloadExecutionWireNamesArePythonAligned()
    {
        Assert.Equal("blocked", GhgSourceDownloadExecutionStatus.Blocked.ToWireName());
        Assert.Equal("downloaded", GhgSourceDownloadExecutionStatus.Downloaded.ToWireName());
        Assert.Equal("failed", GhgSourceDownloadExecutionStatus.Failed.ToWireName());
        Assert.True(ContractWireNames.TryParseGhgSourceDownloadExecutionStatusWireName("downloaded", out var parsed));
        Assert.Equal(GhgSourceDownloadExecutionStatus.Downloaded, parsed);
        Assert.False(ContractWireNames.TryParseGhgSourceDownloadExecutionStatusWireName("unknown", out _));
        Assert.Throws<ArgumentOutOfRangeException>(() => ((GhgSourceDownloadExecutionStatus)999).ToWireName());
    }

    private static GhgSourceDownloadExecutionRequest ValidRequest(string targetRoot) =>
        GhgSourceDownloadExecutionBoundary.CreateRequest(
            DownloadableCandidate(),
            targetRoot,
            "ghg/corporate-standard.pdf",
            allowDownloadExecution: true,
            allowFileWrite: true);

    private static GhgSourceDocumentCandidate DownloadableCandidate() =>
        new(
            SourceFamily.GhgProtocol,
            "ghg_protocol",
            "ghg_source_discovery_candidate_001_ghg_protocol",
            "GHG Protocol",
            "mock://ghg_protocol/corporate-standard.pdf",
            "pdf",
            contentType: "application/pdf",
            extension: ".pdf",
            versionLabel: "dn046_mock_download",
            downloadAllowed: true);

    private static GhgSourceDownloadExecutionRequest WithField(
        GhgSourceDownloadExecutionRequest request,
        string fieldName,
        string value) =>
        fieldName switch
        {
            "source_reference_uri" => request with { SourceReferenceUri = value },
            "target_root" => request with { TargetRoot = value },
            "target_relative_path" => request with { TargetRelativePath = value },
            _ => throw new ArgumentOutOfRangeException(nameof(fieldName), fieldName, "Unknown test field."),
        };

    private static GhgSourceDownloadTransportResponse UnexpectedTransport(string sourceReferenceUri) =>
        throw new InvalidOperationException($"transport should not be called for {sourceReferenceUri}");

    private sealed class TemporaryDirectory : IDisposable
    {
        public string Path { get; } = System.IO.Path.Combine(
            System.IO.Path.GetTempPath(),
            $"carbonops-ghg-download-{Guid.NewGuid():N}");

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
