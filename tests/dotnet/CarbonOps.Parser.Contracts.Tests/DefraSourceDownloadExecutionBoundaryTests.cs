using System.Reflection;
using System.Security.Cryptography;
using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class DefraSourceDownloadExecutionBoundaryTests
{
    [Fact]
    public void RequestFromCandidateIsExplicitOptIn()
    {
        var candidate = DownloadableCandidate();
        using var temp = new TemporaryDirectory();

        var request = DefraSourceDownloadExecutionBoundary.CreateRequest(
            candidate,
            temp.Path,
            "defra/conversion-factors.xlsx");

        Assert.Equal(SourceFamily.DefraDesnz, request.SourceFamily);
        Assert.Equal("defra_desnz", request.SourceKey);
        Assert.Equal("defra_source_discovery_candidate_001_defra_desnz", request.CandidateId);
        Assert.Equal("DEFRA/DESNZ", request.CandidateTitle);
        Assert.Equal("mock://defra_desnz/conversion-factors.xlsx", request.SourceReferenceUri);
        Assert.Equal("xlsx", request.ArtifactKind);
        Assert.True(request.CandidateDownloadAllowed);
        Assert.False(request.AllowDownloadExecution);
        Assert.False(request.AllowFileWrite);
        Assert.Equal("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", request.ContentType);
        Assert.Equal(".xlsx", request.Extension);
        Assert.Equal("dn048_mock_download", request.VersionLabel);

        var validation = DefraSourceDownloadExecutionBoundary.Validate(request);

        Assert.False(validation.IsValid);
        Assert.Equal(
            [
                "DEFRA_SOURCE_DOWNLOAD_EXECUTION_NOT_ALLOWED",
                "DEFRA_SOURCE_DOWNLOAD_FILE_WRITE_NOT_ALLOWED",
            ],
            validation.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void DefaultDiscoveryCandidateIsNotDownloadable()
    {
        using var temp = new TemporaryDirectory();
        var candidate = DefraSourceDiscoveryBoundary.CreateResult().Candidates[0];
        var request = DefraSourceDownloadExecutionBoundary.CreateRequest(
            candidate,
            temp.Path,
            "defra/source.discovery",
            allowDownloadExecution: true,
            allowFileWrite: true);

        var result = DefraSourceDownloadExecutionBoundary.Execute(request, UnexpectedTransport);

        Assert.Equal(DefraSourceDownloadExecutionStatus.Blocked, result.Status);
        Assert.False(result.Downloaded);
        Assert.Null(result.Artifact);
        Assert.Equal(
            [
                "DEFRA_SOURCE_DOWNLOAD_CANDIDATE_NOT_DOWNLOADABLE",
                "DEFRA_SOURCE_DOWNLOAD_DISCOVERY_REFERENCE_NOT_DOWNLOADABLE",
            ],
            result.Issues.Select(issue => issue.Code));
        Assert.False(File.Exists(Path.Combine(temp.Path, "defra/source.discovery")));
    }

    [Fact]
    public void InvalidDownloadRequestFailsClosedBeforeTransport()
    {
        using var temp = new TemporaryDirectory();
        var request = ValidRequest(temp.Path) with
        {
            SourceFamily = SourceFamily.GhgProtocol,
            SourceKey = "ghg_protocol",
            AllowParse = true,
            AllowDatabaseWrites = true,
            AllowScheduler = true,
        };

        var result = DefraSourceDownloadExecutionBoundary.Execute(request, UnexpectedTransport);

        Assert.Equal(DefraSourceDownloadExecutionStatus.Blocked, result.Status);
        Assert.False(result.Downloaded);
        Assert.Null(result.Artifact);
        Assert.True(result.NoParse);
        Assert.True(result.NoDatabaseWrites);
        Assert.True(result.NoSql);
        Assert.True(result.NoScheduler);
        Assert.Equal(
            [
                "DEFRA_SOURCE_DOWNLOAD_SOURCE_FAMILY_MISMATCH",
                "DEFRA_SOURCE_DOWNLOAD_SOURCE_KEY_MISMATCH",
                "DEFRA_SOURCE_DOWNLOAD_PARSE_NOT_ALLOWED",
                "DEFRA_SOURCE_DOWNLOAD_DATABASE_WRITES_NOT_ALLOWED",
                "DEFRA_SOURCE_DOWNLOAD_SCHEDULER_NOT_ALLOWED",
            ],
            result.Issues.Select(issue => issue.Code));
    }

    [Theory]
    [InlineData("source_reference_uri", "https://example.invalid/defra.xlsx", "DEFRA_SOURCE_DOWNLOAD_NETWORK_NOT_ALLOWED")]
    [InlineData("source_reference_uri", "http://example.invalid/defra.xlsx", "DEFRA_SOURCE_DOWNLOAD_INSECURE_HTTP_NOT_ALLOWED")]
    [InlineData("source_reference_uri", "file:///tmp/defra.xlsx", "DEFRA_SOURCE_DOWNLOAD_UNSAFE_SOURCE_REFERENCE_URI")]
    [InlineData("source_reference_uri", "s3://bucket/defra.xlsx", "DEFRA_SOURCE_DOWNLOAD_UNSAFE_SOURCE_REFERENCE_URI")]
    [InlineData("source_reference_uri", "defra/conversion-factors.xlsx", "DEFRA_SOURCE_DOWNLOAD_SOURCE_REFERENCE_URI_MISSING_SCHEME")]
    [InlineData("source_reference_uri", "://defra/conversion-factors.xlsx", "DEFRA_SOURCE_DOWNLOAD_MALFORMED_SOURCE_REFERENCE_URI")]
    [InlineData("source_reference_uri", "https:///defra.xlsx", "DEFRA_SOURCE_DOWNLOAD_MALFORMED_SOURCE_REFERENCE_URI")]
    [InlineData("target_root", "relative/root", "DEFRA_SOURCE_DOWNLOAD_TARGET_ROOT_NOT_ABSOLUTE")]
    [InlineData("target_relative_path", "../outside.xlsx", "DEFRA_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_UNSAFE")]
    [InlineData("target_relative_path", "/absolute.xlsx", "DEFRA_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_ABSOLUTE")]
    [InlineData("target_relative_path", "download://defra/source.xlsx", "DEFRA_SOURCE_DOWNLOAD_TARGET_RELATIVE_PATH_URI")]
    public void UnsafeRequestInputsFailClosed(string fieldName, string value, string expectedCode)
    {
        using var temp = new TemporaryDirectory();
        var request = WithField(ValidRequest(temp.Path), fieldName, value);

        var validation = DefraSourceDownloadExecutionBoundary.Validate(request);

        Assert.False(validation.IsValid);
        Assert.Contains(expectedCode, validation.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void SuccessfulDownloadIsExplicitAndUsesInjectedTransport()
    {
        using var temp = new TemporaryDirectory();
        var payload = "deterministic defra source bytes"u8.ToArray();
        var calls = new List<string>();
        var request = ValidRequest(temp.Path);

        var result = DefraSourceDownloadExecutionBoundary.Execute(
            request,
            sourceReferenceUri =>
            {
                calls.Add(sourceReferenceUri);
                return new DefraSourceDownloadTransportResponse(
                    payload,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    "mock://defra_desnz/final.xlsx");
            });

        var targetPath = Path.Combine(temp.Path, "defra/conversion-factors.xlsx");
        var checksum = Convert.ToHexString(SHA256.HashData(payload)).ToLowerInvariant();
        Assert.Equal(["mock://defra_desnz/conversion-factors.xlsx"], calls);
        Assert.Equal(payload, File.ReadAllBytes(targetPath));
        Assert.Equal(DefraSourceDownloadExecutionStatus.Downloaded, result.Status);
        Assert.True(result.Downloaded);
        Assert.Equal(
            new DefraSourceDownloadedArtifact(
                SourceFamily.DefraDesnz,
                "defra_desnz",
                "defra_source_discovery_candidate_001_defra_desnz",
                "defra_source_download_artifact_defra_source_discovery_candidate_001_defra_desnz",
                "xlsx",
                "mock://defra_desnz/conversion-factors.xlsx",
                targetPath,
                "conversion-factors.xlsx",
                checksum,
                payload.LongLength,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ".xlsx",
                "mock://defra_desnz/final.xlsx",
                VersionLabel: "dn048_mock_download"),
            result.Artifact);
        Assert.True(DefraSourceDownloadExecutionBoundary.Validate(result).IsValid);
    }

    [Fact]
    public void TargetExistsBlocksBeforeTransportByDefault()
    {
        using var temp = new TemporaryDirectory();
        var request = ValidRequest(temp.Path);
        var targetPath = Path.Combine(temp.Path, request.TargetRelativePath);
        Directory.CreateDirectory(Path.GetDirectoryName(targetPath)!);
        File.WriteAllBytes(targetPath, "existing"u8.ToArray());

        var result = DefraSourceDownloadExecutionBoundary.Execute(request, UnexpectedTransport);

        Assert.Equal(DefraSourceDownloadExecutionStatus.Blocked, result.Status);
        Assert.Equal(["DEFRA_SOURCE_DOWNLOAD_TARGET_EXISTS"], result.Issues.Select(issue => issue.Code));
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
        var targetParent = Path.Combine(temp.Path, "target-root", "defra");
        Directory.CreateDirectory(outside);
        Directory.CreateDirectory(targetParent);
        var targetPath = Path.Combine(targetParent, "escape.xlsx");
        File.CreateSymbolicLink(targetPath, Path.Combine(outside, "escape.xlsx"));
        var request = ValidRequest(Path.Combine(temp.Path, "target-root")) with
        {
            TargetRelativePath = "defra/escape.xlsx",
            AllowOverwrite = true,
        };

        var result = DefraSourceDownloadExecutionBoundary.Execute(
            request,
            _ => new DefraSourceDownloadTransportResponse("escape"u8.ToArray()));

        Assert.Equal(DefraSourceDownloadExecutionStatus.Blocked, result.Status);
        Assert.Null(result.Artifact);
        Assert.Equal(["DEFRA_SOURCE_DOWNLOAD_TARGET_SYMLINK_UNSAFE"], result.Issues.Select(issue => issue.Code));
        Assert.False(File.Exists(Path.Combine(outside, "escape.xlsx")));
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
        var targetParent = Path.Combine(targetRoot, "defra");
        Directory.CreateDirectory(targetParent);
        Directory.CreateDirectory(outside);
        var request = ValidRequest(targetRoot) with { TargetRelativePath = "defra/escape.xlsx" };

        var result = DefraSourceDownloadExecutionBoundary.Execute(
            request,
            _ =>
            {
                Directory.Delete(targetParent, recursive: true);
                Directory.CreateSymbolicLink(targetParent, outside);
                return new DefraSourceDownloadTransportResponse("escape"u8.ToArray());
            });

        Assert.NotEqual(DefraSourceDownloadExecutionStatus.Downloaded, result.Status);
        Assert.False(result.Downloaded);
        Assert.Null(result.Artifact);
        Assert.False(File.Exists(Path.Combine(outside, "escape.xlsx")));
        Assert.True(Directory.Exists(targetParent));
    }

    [Fact]
    public void ChecksumMismatchFailsWithoutWritingFile()
    {
        using var temp = new TemporaryDirectory();
        var request = ValidRequest(temp.Path) with { ExpectedChecksumSha256 = new string('a', 64) };

        var result = DefraSourceDownloadExecutionBoundary.Execute(
            request,
            _ => new DefraSourceDownloadTransportResponse("unexpected"u8.ToArray()));

        Assert.Equal(DefraSourceDownloadExecutionStatus.Failed, result.Status);
        Assert.Null(result.Artifact);
        Assert.Equal(["DEFRA_SOURCE_DOWNLOAD_CHECKSUM_MISMATCH"], result.Issues.Select(issue => issue.Code));
        Assert.False(File.Exists(Path.Combine(temp.Path, request.TargetRelativePath)));
    }

    [Fact]
    public void TransportErrorsAndEmptyContentAreFailedResults()
    {
        using var temp = new TemporaryDirectory();
        using var other = new TemporaryDirectory();

        var failed = DefraSourceDownloadExecutionBoundary.Execute(
            ValidRequest(temp.Path),
            _ => throw new InvalidOperationException("offline"));
        var empty = DefraSourceDownloadExecutionBoundary.Execute(
            ValidRequest(other.Path),
            _ => new DefraSourceDownloadTransportResponse(Array.Empty<byte>()));

        Assert.Equal(DefraSourceDownloadExecutionStatus.Failed, failed.Status);
        Assert.Equal(["DEFRA_SOURCE_DOWNLOAD_TRANSPORT_FAILED"], failed.Issues.Select(issue => issue.Code));
        Assert.Equal(DefraSourceDownloadExecutionStatus.Failed, empty.Status);
        Assert.Equal(["DEFRA_SOURCE_DOWNLOAD_RESPONSE_EMPTY_CONTENT"], empty.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void TransportResponseValidationFailsClosed()
    {
        using var missing = new TemporaryDirectory();
        using var missingContent = new TemporaryDirectory();
        using var blankMetadata = new TemporaryDirectory();

        var missingResponse = DefraSourceDownloadExecutionBoundary.Execute(
            ValidRequest(missing.Path),
            _ => null!);
        var missingContentResponse = DefraSourceDownloadExecutionBoundary.Execute(
            ValidRequest(missingContent.Path),
            _ => new DefraSourceDownloadTransportResponse(null!));
        var blankMetadataResponse = DefraSourceDownloadExecutionBoundary.Execute(
            ValidRequest(blankMetadata.Path),
            _ => new DefraSourceDownloadTransportResponse("content"u8.ToArray(), " ", " "));

        Assert.Equal(DefraSourceDownloadExecutionStatus.Failed, missingResponse.Status);
        Assert.Equal(["DEFRA_SOURCE_DOWNLOAD_RESPONSE_MISSING"], missingResponse.Issues.Select(issue => issue.Code));
        Assert.Equal(DefraSourceDownloadExecutionStatus.Failed, missingContentResponse.Status);
        Assert.Equal(
            ["DEFRA_SOURCE_DOWNLOAD_RESPONSE_MISSING_CONTENT"],
            missingContentResponse.Issues.Select(issue => issue.Code));
        Assert.Equal(DefraSourceDownloadExecutionStatus.Failed, blankMetadataResponse.Status);
        Assert.Equal(
            [
                "DEFRA_SOURCE_DOWNLOAD_RESPONSE_BLANK_CONTENT_TYPE",
                "DEFRA_SOURCE_DOWNLOAD_RESPONSE_BLANK_FINAL_URI",
            ],
            blankMetadataResponse.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void ResultValidationRejectsSideEffectFlags()
    {
        using var temp = new TemporaryDirectory();
        var result = DefraSourceDownloadExecutionBoundary.Execute(
            ValidRequest(temp.Path),
            _ => new DefraSourceDownloadTransportResponse("content"u8.ToArray())) with
        {
            NoDatabaseWrites = false,
            NoSql = false,
        };

        var validation = DefraSourceDownloadExecutionBoundary.Validate(result);

        Assert.False(validation.IsValid);
        Assert.Equal(
            [
                "DEFRA_SOURCE_DOWNLOAD_RESULT_SIDE_EFFECT_FLAG_ENABLED",
                "DEFRA_SOURCE_DOWNLOAD_RESULT_SIDE_EFFECT_FLAG_ENABLED",
            ],
            validation.Issues.Select(issue => issue.Code));
        Assert.Equal(["no_database_writes", "no_sql"], validation.Issues.Select(issue => issue.FieldName));
    }

    [Theory]
    [InlineData(DefraSourceDownloadExecutionStatus.Blocked)]
    [InlineData(DefraSourceDownloadExecutionStatus.Failed)]
    public void ResultValidationRejectsBlockedOrFailedResultsWithoutIssues(DefraSourceDownloadExecutionStatus status)
    {
        using var temp = new TemporaryDirectory();
        var result = new DefraSourceDownloadExecutionResult(status, ValidRequest(temp.Path));

        var validation = DefraSourceDownloadExecutionBoundary.Validate(result);

        Assert.False(validation.IsValid);
        Assert.Equal(["DEFRA_SOURCE_DOWNLOAD_RESULT_MISSING_ISSUES"], validation.Issues.Select(issue => issue.Code));
    }

    [Fact]
    public void BoundaryPublicSurfaceOnlyExposesExplicitExecutionMethods()
    {
        var publicMethodNames = typeof(DefraSourceDownloadExecutionBoundary)
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
    public void DefraDownloadExecutionWireNamesArePythonAligned()
    {
        Assert.Equal("blocked", DefraSourceDownloadExecutionStatus.Blocked.ToWireName());
        Assert.Equal("downloaded", DefraSourceDownloadExecutionStatus.Downloaded.ToWireName());
        Assert.Equal("failed", DefraSourceDownloadExecutionStatus.Failed.ToWireName());
        Assert.True(ContractWireNames.TryParseDefraSourceDownloadExecutionStatusWireName("downloaded", out var parsed));
        Assert.Equal(DefraSourceDownloadExecutionStatus.Downloaded, parsed);
        Assert.False(ContractWireNames.TryParseDefraSourceDownloadExecutionStatusWireName("unknown", out _));
        Assert.Throws<ArgumentOutOfRangeException>(() => ((DefraSourceDownloadExecutionStatus)999).ToWireName());
    }

    private static DefraSourceDownloadExecutionRequest ValidRequest(string targetRoot) =>
        DefraSourceDownloadExecutionBoundary.CreateRequest(
            DownloadableCandidate(),
            targetRoot,
            "defra/conversion-factors.xlsx",
            allowDownloadExecution: true,
            allowFileWrite: true);

    private static DefraSourceDocumentCandidate DownloadableCandidate() =>
        new(
            SourceFamily.DefraDesnz,
            "defra_desnz",
            "defra_source_discovery_candidate_001_defra_desnz",
            "DEFRA/DESNZ",
            "mock://defra_desnz/conversion-factors.xlsx",
            "xlsx",
            contentType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            extension: ".xlsx",
            versionLabel: "dn048_mock_download",
            downloadAllowed: true);

    private static DefraSourceDownloadExecutionRequest WithField(
        DefraSourceDownloadExecutionRequest request,
        string fieldName,
        string value) =>
        fieldName switch
        {
            "source_reference_uri" => request with { SourceReferenceUri = value },
            "target_root" => request with { TargetRoot = value },
            "target_relative_path" => request with { TargetRelativePath = value },
            _ => throw new ArgumentOutOfRangeException(nameof(fieldName), fieldName, "Unknown test field."),
        };

    private static DefraSourceDownloadTransportResponse UnexpectedTransport(string sourceReferenceUri) =>
        throw new InvalidOperationException($"transport should not be called for {sourceReferenceUri}");

    private sealed class TemporaryDirectory : IDisposable
    {
        public string Path { get; } = System.IO.Path.Combine(
            System.IO.Path.GetTempPath(),
            $"carbonops-defra-download-{Guid.NewGuid():N}");

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
