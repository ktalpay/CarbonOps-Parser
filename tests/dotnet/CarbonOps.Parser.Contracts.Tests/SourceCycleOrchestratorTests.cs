using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class SourceCycleOrchestratorTests
{
    [Fact]
    public async Task NoSuccessfulYearTargetsDefaultInitialYearForAllSourceFamilies()
    {
        var session = new RecordingYearStateSession();
        var result = await CreateOrchestrator(session).PreviewAsync();

        Assert.Equal(3, result.RunCount);
        Assert.Equal(
            SourceFamilyRegistry.SupportedFamilies.OrderBy(family => family.ToWireName(), StringComparer.Ordinal),
            result.Runs.Select(run => run.SourceFamily));
        Assert.All(result.Runs, run =>
        {
            Assert.Null(run.LatestSuccessfulYear);
            Assert.Equal(2024, run.TargetYear);
            Assert.Equal(SourceCycleRunStatus.NoAvailableSourceYear, run.Status);
            Assert.Equal(SourceCycleRunStatus.PersistenceNotImplemented, run.PersistenceStatus);
        });
        Assert.Equal(3, session.LatestReadCount);
        Assert.Equal(0, session.RecordWriteCount);
        Assert.False(result.RecordsInserted);
        Assert.False(result.YearStateAdvanced);
    }

    [Fact]
    public async Task LatestSuccessfulYearTargetsNextYearForAllSourceFamilies()
    {
        var session = new RecordingYearStateSession(
            SourceFamilyRegistry.SupportedFamilies.ToDictionary(family => family, _ => (int?)2024));
        var result = await CreateOrchestrator(session).PreviewAsync();

        Assert.All(result.Runs, run =>
        {
            Assert.Equal(2024, run.LatestSuccessfulYear);
            Assert.Equal(2025, run.TargetYear);
        });
        Assert.Equal(0, session.RecordWriteCount);
    }

    [Fact]
    public async Task UnavailableTargetYearReturnsNoAvailableSourceYear()
    {
        var result = await CreateOrchestrator(new RecordingYearStateSession()).PreviewAsync();

        Assert.All(result.Runs, run =>
        {
            Assert.Equal(SourceCycleRunStatus.NoAvailableSourceYear, run.Status);
            Assert.Equal(SourceCycleRunStatus.NoAvailableSourceYear, run.ParserStatus);
            Assert.Equal(0, run.ArtifactCount);
            Assert.Equal(0, run.ParsedRowCount);
        });
    }

    [Fact]
    public async Task ParserHandoffOutputIsRepresentedForConfiguredLocalArtifact()
    {
        var artifactPath = FixturePath("ghg_protocol", "ghg_protocol_sample_factors.csv");
        var orchestrator = CreateOrchestrator(
            new RecordingYearStateSession(),
            artifacts:
            [
                new SourceCycleArtifact(
                    SourceFamily.GhgProtocol,
                    2024,
                    artifactPath,
                    "text/csv",
                    ".csv",
                    "v1"),
            ]);

        var result = await orchestrator.PreviewAsync();
        var run = result.Runs.Single(item => item.SourceFamily == SourceFamily.GhgProtocol);

        Assert.Equal(SourceCycleRunStatus.PersistenceNotImplemented, run.Status);
        Assert.Equal(SourceCycleRunStatus.Parsed, run.ParserStatus);
        Assert.Equal(SourceCycleRunStatus.PersistenceNotImplemented, run.PersistenceStatus);
        Assert.Equal(ParserRunStatus.Completed, run.ParserRunStatus);
        Assert.Equal(1, run.ArtifactCount);
        Assert.Equal(2, run.ParsedRowCount);
        Assert.Equal(1, run.ParserIssueCount);
        Assert.Equal(artifactPath, run.ArtifactReference);
    }

    [Fact]
    public async Task YearStateIsNotAdvancedByParsingAloneAndNoDbInsertIsAttempted()
    {
        var session = new RecordingYearStateSession();
        var artifactPath = FixturePath("defra_desnz", "defra_desnz_normalized_factors.csv");
        var result = await CreateOrchestrator(
            session,
            enabledFamilies: [SourceFamily.DefraDesnz],
            artifacts:
            [
                new SourceCycleArtifact(SourceFamily.DefraDesnz, 2024, artifactPath, "text/csv", ".csv"),
            ]).PreviewAsync();

        Assert.False(result.PostgreSQLConnectionOpened);
        Assert.False(result.PostgreSQLSqlExecuted);
        Assert.False(result.RecordsInserted);
        Assert.False(result.YearStateAdvanced);
        Assert.Equal(0, session.RecordWriteCount);
        Assert.Equal(SourceCycleRunStatus.PersistenceNotImplemented, result.Runs[0].Status);
    }

    [Fact]
    public async Task UnsupportedArtifactShapeFailsClosedWithoutNetworkAccess()
    {
        var result = await CreateOrchestrator(
            new RecordingYearStateSession(),
            enabledFamilies: [SourceFamily.IpccEfdb],
            artifacts:
            [
                new SourceCycleArtifact(SourceFamily.IpccEfdb, 2024, "https://example.invalid/ipcc.csv", "text/csv", ".csv"),
            ]).PreviewAsync();

        var run = result.Runs.Single();
        Assert.Equal(SourceCycleRunStatus.ParserNotAvailable, run.Status);
        Assert.Equal(SourceCycleRunStatus.ParserNotAvailable, run.ParserStatus);
        Assert.False(result.NetworkAccessAttempted);
        Assert.Equal(0, run.ParsedRowCount);
    }

    [Fact]
    public void SourceCycleConfigurationLoadsEnabledFamiliesAndArtifactsFromConfig()
    {
        var artifactPath = FixturePath("ipcc_efdb", "ipcc_efdb_sample_factors.csv");
        var configPath = WriteSourceCycleConfig(
            $$"""
            {
              "enabled_source_families": ["ipcc_efdb"],
              "source_artifacts": {
                "ipcc_efdb": {
                  "2024": {
                    "path": "{{JsonEscape(artifactPath)}}",
                    "content_type": "text/csv",
                    "extension": ".csv",
                    "version_label": "efdb-v2024"
                  }
                }
              }
            }
            """);

        var families = SourceCycleConfiguration.LoadEnabledSourceFamilies(configPath);
        var artifacts = SourceCycleConfiguration.LoadArtifacts(configPath);

        Assert.Equal([SourceFamily.IpccEfdb], families);
        var artifact = Assert.Single(artifacts);
        Assert.Equal(SourceFamily.IpccEfdb, artifact.SourceFamily);
        Assert.Equal(2024, artifact.ReportingYear);
        Assert.Equal(artifactPath, artifact.ArtifactReference);
        Assert.Equal("efdb-v2024", artifact.VersionLabel);
    }

    [Fact]
    public async Task SourceYearsArtifactUrlFileUriCanBeParsedWithoutNetworkAccess()
    {
        var artifactPath = FixturePath("defra_desnz", "defra_desnz_normalized_factors.csv");
        var artifactUri = new Uri(artifactPath).AbsoluteUri;
        var configPath = WriteSourceCycleConfig(
            $$"""
            {
              "enabled_source_families": ["defra_desnz"],
              "source_years": {
                "defra_desnz": {
                  "2024": {
                    "artifact_url": "{{artifactUri}}",
                    "content_type": "text/csv",
                    "format_hint": "csv",
                    "version_label": "conversion-factors-2024"
                  }
                }
              }
            }
            """);

        var result = await CreateOrchestrator(
            new RecordingYearStateSession(),
            SourceCycleConfiguration.LoadEnabledSourceFamilies(configPath),
            SourceCycleConfiguration.LoadArtifacts(configPath)).PreviewAsync();

        var run = Assert.Single(result.Runs);
        Assert.Equal(SourceCycleRunStatus.PersistenceNotImplemented, run.Status);
        Assert.Equal(SourceCycleRunStatus.Parsed, run.ParserStatus);
        Assert.Equal(2, run.ParsedRowCount);
        Assert.False(result.NetworkAccessAttempted);
    }

    private static SourceCycleOrchestrator CreateOrchestrator(
        RecordingYearStateSession session,
        IEnumerable<SourceFamily>? enabledFamilies = null,
        IEnumerable<SourceCycleArtifact>? artifacts = null) =>
        new(
            new PostgreSQLSourceFamilyYearStateRepository(session),
            enabledFamilies,
            artifacts);

    private static string FixturePath(string familyDirectory, string fileName)
    {
        var directory = new DirectoryInfo(AppContext.BaseDirectory);
        while (directory is not null)
        {
            var fixtureDirectory = Path.Combine(
                directory.FullName,
                "tests",
                "fixtures",
                "source_documents",
                familyDirectory);
            if (Directory.Exists(fixtureDirectory))
            {
                return Path.Combine(fixtureDirectory, fileName);
            }

            directory = directory.Parent;
        }

        throw new DirectoryNotFoundException("Could not locate source document fixture directory.");
    }

    private static string WriteSourceCycleConfig(string json)
    {
        var path = Path.Combine(Path.GetTempPath(), $"carbonops-source-cycle-{Guid.NewGuid():N}.json");
        File.WriteAllText(path, json);
        return path;
    }

    private static string JsonEscape(string value) => value.Replace("\\", "\\\\", StringComparison.Ordinal).Replace("\"", "\\\"", StringComparison.Ordinal);

    private sealed class RecordingYearStateSession : IPostgreSQLSourceFamilyYearStateSession
    {
        private readonly IReadOnlyDictionary<SourceFamily, int?> _latestYears;

        public RecordingYearStateSession(IReadOnlyDictionary<SourceFamily, int?>? latestYears = null)
        {
            _latestYears = latestYears ?? new Dictionary<SourceFamily, int?>();
        }

        public int LatestReadCount { get; private set; }

        public int RecordWriteCount { get; private set; }

        public Task<int?> LatestSuccessfulYearAsync(
            SourceFamily sourceFamily,
            CancellationToken cancellationToken = default)
        {
            LatestReadCount++;
            return Task.FromResult(_latestYears.TryGetValue(sourceFamily, out var value) ? value : null);
        }

        public Task RecordSuccessfulYearAsync(
            SourceFamily sourceFamily,
            int ingestedYear,
            CancellationToken cancellationToken = default)
        {
            RecordWriteCount++;
            return Task.CompletedTask;
        }
    }
}
