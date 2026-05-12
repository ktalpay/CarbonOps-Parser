using CarbonOps.Parser.Contracts;

namespace CarbonOps.Parser.Contracts.Tests;

public sealed class Phase1IngestionOrchestratorTests
{
    [Fact]
    public void OrchestratorRunsSelectedPhaseOneSourcesEndToEndWithFakes()
    {
        var log = new List<string>();
        var orchestrator = CreateOrchestrator(log);
        var request = new Phase1IngestionOrchestratorRequest(
            [SourceFamily.GhgProtocol, SourceFamily.DefraDesnz, SourceFamily.IpccEfdb],
            correlationId: "test-correlation");

        var result = orchestrator.Run(request);

        Assert.Equal(Phase1IngestionRunStatus.Completed, result.Status);
        Assert.Equal(
            [SourceFamily.GhgProtocol, SourceFamily.DefraDesnz, SourceFamily.IpccEfdb],
            result.SelectedSourceFamilies);
        Assert.Equal(3, result.SourceFamilyCount);
        Assert.Equal(3, result.CompletedSourceFamilyCount);
        Assert.Equal(0, result.FailedSourceFamilyCount);
        Assert.Equal(3, result.TotalSourceDocumentMetadataCount);
        Assert.Equal(3, result.TotalParserAcceptedRowCount);
        Assert.Equal(3, result.TotalPersistedMasterCount);
        Assert.Equal(3, result.TotalPersistedDetailCount);
        Assert.Empty(result.Failures);
        Assert.Equal(
            [
                "ghg_protocol:discover_download",
                "ghg_protocol:normalize",
                "defra_desnz:discover_download",
                "defra_desnz:normalize",
                "ipcc_efdb:discover_download",
                "ipcc_efdb:normalize",
            ],
            log);
    }

    [Fact]
    public void OrchestratorRequiresExplicitSourceFamilySelection()
    {
        var log = new List<string>();
        var orchestrator = CreateOrchestrator(log);
        var request = new Phase1IngestionOrchestratorRequest([]);

        var result = orchestrator.Run(request);

        Assert.Equal(Phase1IngestionRunStatus.NotExecutable, result.Status);
        Assert.Equal(0, result.SourceFamilyCount);
        Assert.Equal(["PHASE1_SOURCE_FAMILY_SELECTION_REQUIRED"], result.Failures.Select(failure => failure.Code));
        Assert.Empty(log);
    }

    [Fact]
    public void OrchestratorCanRunSingleSelectedSourceFamily()
    {
        var log = new List<string>();
        var orchestrator = CreateOrchestrator(log);
        var request = new Phase1IngestionOrchestratorRequest([SourceFamily.DefraDesnz]);

        var result = orchestrator.Run(request);

        Assert.Equal(Phase1IngestionRunStatus.Completed, result.Status);
        Assert.Single(result.FamilyResults);
        Assert.Equal(SourceFamily.DefraDesnz, result.FamilyResults[0].SourceFamily);
        Assert.Equal(Phase1IngestionFamilyRunStatus.Completed, result.FamilyResults[0].Status);
        Assert.Equal("phase1_ingestion_orchestrator_run", result.FamilyResults[0].AcquisitionRun?.RunId);
        Assert.Equal(["defra_desnz:discover_download", "defra_desnz:normalize"], log);
    }

    [Fact]
    public void DuplicateSourceFamilySelectionIsIdempotent()
    {
        var log = new List<string>();
        var orchestrator = CreateOrchestrator(log);
        var request = new Phase1IngestionOrchestratorRequest(
            [SourceFamily.IpccEfdb, SourceFamily.IpccEfdb]);

        var result = orchestrator.Run(request);

        Assert.Equal(Phase1IngestionRunStatus.Completed, result.Status);
        Assert.Equal([SourceFamily.IpccEfdb], result.SelectedSourceFamilies);
        Assert.Single(result.FamilyResults);
        Assert.Equal(["ipcc_efdb:discover_download", "ipcc_efdb:normalize"], log);
    }

    [Fact]
    public void PartialFailureSemanticsAreDeterministicPerSourceFamily()
    {
        var log = new List<string>();
        var orchestrator = CreateOrchestrator(log, failingParserFamilies: [SourceFamily.DefraDesnz]);
        var request = new Phase1IngestionOrchestratorRequest(
            [SourceFamily.GhgProtocol, SourceFamily.DefraDesnz, SourceFamily.IpccEfdb]);

        var result = orchestrator.Run(request);

        Assert.Equal(Phase1IngestionRunStatus.CompletedWithFailures, result.Status);
        Assert.Equal(
            [
                Phase1IngestionFamilyRunStatus.Completed,
                Phase1IngestionFamilyRunStatus.Failed,
                Phase1IngestionFamilyRunStatus.Completed,
            ],
            result.FamilyResults.Select(family => family.Status));
        Assert.Equal(2, result.CompletedSourceFamilyCount);
        Assert.Equal(1, result.FailedSourceFamilyCount);
        Assert.Contains(result.FamilyResults[1].Failures, failure =>
            failure.Stage == "parser" &&
            failure.Code.EndsWith("_CONTENT_INVALID_HEADER", StringComparison.Ordinal));
        Assert.Equal(2, result.TotalPersistedMasterCount);
        Assert.Equal(2, result.TotalPersistedDetailCount);
        Assert.Equal(
            [
                "ghg_protocol:discover_download",
                "ghg_protocol:normalize",
                "defra_desnz:discover_download",
                "defra_desnz:normalize",
                "ipcc_efdb:discover_download",
                "ipcc_efdb:normalize",
            ],
            log);
    }

    [Fact]
    public void BoundedParallelExecutionIsAnExplicitExtensionPoint()
    {
        var log = new List<string>();
        var orchestrator = CreateOrchestrator(log);
        var request = new Phase1IngestionOrchestratorRequest(
            [SourceFamily.GhgProtocol],
            Phase1IngestionExecutionMode.BoundedParallel,
            maxDegreeOfParallelism: 2);

        var result = orchestrator.Run(request);

        Assert.Equal(Phase1IngestionExecutionMode.BoundedParallel, result.Request.ExecutionMode);
        Assert.Equal(2, result.Request.MaxDegreeOfParallelism);
        Assert.Equal(Phase1IngestionRunStatus.NotExecutable, result.Status);
        Assert.Equal([SourceFamily.GhgProtocol], result.SelectedSourceFamilies);
        Assert.Equal(0, result.CompletedSourceFamilyCount);
        Assert.Equal(["PHASE1_INGESTION_BOUNDED_PARALLEL_NOT_ENABLED"], result.Failures.Select(failure => failure.Code));
        Assert.Empty(log);
    }

    [Fact]
    public void RuntimeConfigReadinessBlocksBeforeSourceExecutionWithoutLoadingSecrets()
    {
        var log = new List<string>();
        var orchestrator = CreateOrchestrator(log);
        var request = new Phase1IngestionOrchestratorRequest(
            [SourceFamily.IpccEfdb],
            runtimeConfigGate: new PostgreSQLRuntimeConfigGate(Requested: true));

        var result = orchestrator.Run(request);

        Assert.Equal(PostgreSQLRuntimeConfigGateStatus.Blocked, result.RuntimeConfigDecision.Status);
        Assert.False(result.RuntimeConfigDecision.LoadsEnvironment);
        Assert.False(result.RuntimeConfigDecision.LoadsConfigFiles);
        Assert.False(result.RuntimeConfigDecision.LoadsCredentials);
        Assert.Equal(Phase1IngestionRunStatus.NotExecutable, result.Status);
        Assert.Equal(0, result.CompletedSourceFamilyCount);
        Assert.Equal(["POSTGRESQL_RUNTIME_CONFIG_BLOCKED"], result.Failures.Select(failure => failure.Code));
        Assert.Empty(log);
    }

    private static Phase1IngestionOrchestrator CreateOrchestrator(
        List<string> log,
        IReadOnlySet<SourceFamily>? failingParserFamilies = null)
    {
        var runtimes = new[]
        {
            new FakeSourceFamilyRuntime(SourceFamily.GhgProtocol, log, failingParserFamilies ?? new HashSet<SourceFamily>()),
            new FakeSourceFamilyRuntime(SourceFamily.DefraDesnz, log, failingParserFamilies ?? new HashSet<SourceFamily>()),
            new FakeSourceFamilyRuntime(SourceFamily.IpccEfdb, log, failingParserFamilies ?? new HashSet<SourceFamily>()),
        };
        return new Phase1IngestionOrchestrator(new Phase1IngestionOrchestratorDependencies(
            runtimes,
            new FakeSourceAcquisitionRunRepository(),
            new FakeSourceDocumentRepository(),
            new FakeParserRunRepository(),
            new FakeSourceFamilyRepository()));
    }

    private sealed class FakeSourceFamilyRuntime(
        SourceFamily sourceFamily,
        ICollection<string> log,
        IReadOnlySet<SourceFamily> failingParserFamilies) : IPhase1SourceFamilyIngestionRuntime
    {
        public SourceFamily SourceFamily { get; } = sourceFamily;

        public SourceAcquisitionRunResult DiscoverAndDownload(string runId, string? correlationId)
        {
            var sourceKey = SourceFamily.ToWireName();
            log.Add($"{sourceKey}:discover_download");
            var candidate = new SourceDiscoveryCandidate(
                SourceFamily,
                sourceKey,
                $"{sourceKey}_candidate",
                $"{sourceKey} fixture",
                2024,
                $"fixture://{sourceKey}/factors.csv",
                ParserSourceFormat.DiscoveryReference,
                "application/x-carbonops-discovery-reference",
                ".csv",
                new SourceDocumentChecksum("sha256", new string('a', 64), IsDryRunPlaceholder: false),
                "fixture-v1");
            var artifact = new SourceDownloadArtifact(
                SourceFamily,
                sourceKey,
                candidate.CandidateId,
                $"{sourceKey}_artifact",
                ParserSourceFormat.DiscoveryReference,
                candidate.SourceReference,
                $"fixture://{sourceKey}/local-factors.csv",
                candidate.Title,
                candidate.ContentType,
                candidate.Extension,
                candidate.Checksum,
                sizeBytes: 128,
                reportingYear: candidate.ReportingYear,
                versionLabel: candidate.VersionLabel);

            return new SourceAcquisitionRunResult(
                SourceFamily,
                sourceKey,
                SourceAcquisitionRunStatus.Completed,
                [candidate],
                [artifact],
                runId,
                correlationId,
                candidate.ReportingYear,
                candidate.VersionLabel);
        }

        public ParserAdapterRunResult Normalize(ParserAdapterRunRequest request)
        {
            log.Add($"{SourceFamily.ToWireName()}:normalize");
            var content = failingParserFamilies.Contains(SourceFamily)
                ? "not,the,expected,header"
                : ContentFor(SourceFamily);
            var contentByReference = request.Artifacts.ToDictionary(
                artifact => artifact.ArtifactReference,
                _ => content,
                StringComparer.Ordinal);

            return SourceFamily switch
            {
                SourceFamily.GhgProtocol => GhgProtocolNormalizedContentParser.Parse(request, contentByReference),
                SourceFamily.DefraDesnz => DefraDesnzNormalizedContentParser.Parse(request, contentByReference),
                SourceFamily.IpccEfdb => IpccEfdbNormalizedContentParser.Parse(request, contentByReference),
                _ => throw new ArgumentOutOfRangeException(nameof(SourceFamily), SourceFamily, "Unknown source family."),
            };
        }

        private static string ContentFor(SourceFamily sourceFamily) =>
            sourceFamily switch
            {
                SourceFamily.GhgProtocol => string.Join(
                    "\n",
                    string.Join(",", GhgProtocolNormalizedContentParser.Header),
                    "emission_factor,2024,fixture-v1,GHG-001,Grid electricity,1.25,kg CO2e/kWh,Energy,Electricity,Scope 2,CO2e,fixture"),
                SourceFamily.DefraDesnz => string.Join(
                    "\n",
                    string.Join(",", DefraDesnzNormalizedContentParser.Header),
                    "2024,fixture-v1,Energy,Electricity,Grid electricity,DEFRA-001,Grid electricity,1.25,kWh,CO2e,fixture"),
                SourceFamily.IpccEfdb => string.Join(
                    "\n",
                    string.Join(",", IpccEfdbNormalizedContentParser.Header),
                    "emission_factor,2024,fixture-v1,IPCC-001,Combustion,1.25,kg,Energy,Fuel,1A,CO2,Global,Default,fixture"),
                _ => throw new ArgumentOutOfRangeException(nameof(sourceFamily), sourceFamily, "Unknown source family."),
            };
    }

    private sealed class FakeSourceAcquisitionRunRepository : ISourceAcquisitionRunRepository
    {
        public string ProviderName => "fake_source_acquisition_runs";

        public SourceAcquisitionRunRepositoryPersistResult PersistRuns(IEnumerable<SourceAcquisitionRunResult> runs) =>
            SourceAcquisitionRunRepositoryRegistry.CreatePersistResult(ProviderName, runs);
    }

    private sealed class FakeSourceDocumentRepository : ISourceDocumentRepository
    {
        public string ProviderName => "fake_source_documents";

        public SourceDocumentRepositoryPersistResult PersistSourceDocuments(IEnumerable<SourceDocumentPersistenceRecord> records) =>
            SourceDocumentRepositoryRegistry.CreatePersistResult(ProviderName, records);
    }

    private sealed class FakeParserRunRepository : IParserRunRepository
    {
        public string ProviderName => "fake_parser_runs";

        public ParserRunRepositoryPersistResult PersistRuns(IEnumerable<ParserRunResult> runs) =>
            ParserRunRepositoryRegistry.CreatePersistResult(ProviderName, runs);
    }

    private sealed class FakeSourceFamilyRepository : ISourceFamilyRepository
    {
        public string ProviderName => "fake_source_family";

        public SourceFamilyRepositoryPersistResult PersistSourceFamilyRecords(
            IEnumerable<SourceFamilyMasterRecord> masterRecords,
            IEnumerable<SourceFamilyDetailRecord> detailRecords) =>
            SourceFamilyRepositoryRegistry.CreatePersistResult(ProviderName, masterRecords, detailRecords);
    }
}
