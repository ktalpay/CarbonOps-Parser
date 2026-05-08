namespace CarbonOps.Parser.Contracts;

public sealed record SourceAcquisitionRunResult
{
    public SourceFamily SourceFamily { get; }

    public string SourceKey { get; }

    public SourceAcquisitionRunStatus Status { get; }

    public IReadOnlyList<SourceDiscoveryCandidate> Candidates { get; }

    public IReadOnlyList<SourceDownloadArtifact> Artifacts { get; }

    public string? RunId { get; }

    public string? CorrelationId { get; }

    public int? ReportingYear { get; }

    public string? VersionLabel { get; }

    public int CandidateCount => Candidates.Count;

    public int ArtifactCount => Artifacts.Count;

    public SourceAcquisitionRunResult(
        SourceFamily sourceFamily,
        string sourceKey,
        SourceAcquisitionRunStatus status,
        IEnumerable<SourceDiscoveryCandidate> candidates,
        IEnumerable<SourceDownloadArtifact> artifacts,
        string? runId = null,
        string? correlationId = null,
        int? reportingYear = null,
        string? versionLabel = null)
    {
        SourceFamily = sourceFamily;
        SourceKey = sourceKey;
        Status = status;
        Candidates = Array.AsReadOnly(candidates.ToArray());
        Artifacts = Array.AsReadOnly(artifacts.ToArray());
        RunId = runId;
        CorrelationId = correlationId;
        ReportingYear = reportingYear;
        VersionLabel = versionLabel;
    }

    internal static SourceAcquisitionRunResult FromCandidatesAndArtifacts(
        SourceFamily sourceFamily,
        IEnumerable<SourceDiscoveryCandidate> candidates,
        IEnumerable<SourceDownloadArtifact> artifacts)
    {
        var candidateSnapshot = candidates.ToArray();
        var artifactSnapshot = artifacts.ToArray();
        var sourceKey = sourceFamily.ToWireName();

        return new SourceAcquisitionRunResult(
            sourceFamily,
            sourceKey,
            SourceAcquisitionRunStatus.Planned,
            candidateSnapshot,
            artifactSnapshot,
            runId: $"{sourceKey}_source_acquisition_run",
            reportingYear: candidateSnapshot.Length == 1 ? candidateSnapshot[0].ReportingYear : null,
            versionLabel: candidateSnapshot.Length == 1 ? candidateSnapshot[0].VersionLabel : null);
    }
}
