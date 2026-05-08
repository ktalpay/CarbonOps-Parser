namespace CarbonOps.Parser.Contracts;

public sealed record SourceAcquisitionRunRequest
{
    public SourceFamily SourceFamily { get; }

    public string SourceKey { get; }

    public IReadOnlyList<SourceDiscoveryCandidate> Candidates { get; }

    public string? RunId { get; }

    public string? CorrelationId { get; }

    public int? RequestedReportingYear { get; }

    public string? RequestedVersionLabel { get; }

    public int CandidateCount => Candidates.Count;

    public SourceAcquisitionRunRequest(
        SourceFamily sourceFamily,
        string sourceKey,
        IEnumerable<SourceDiscoveryCandidate> candidates,
        string? runId = null,
        string? correlationId = null,
        int? requestedReportingYear = null,
        string? requestedVersionLabel = null)
    {
        SourceFamily = sourceFamily;
        SourceKey = sourceKey;
        Candidates = Array.AsReadOnly(candidates.ToArray());
        RunId = runId;
        CorrelationId = correlationId;
        RequestedReportingYear = requestedReportingYear;
        RequestedVersionLabel = requestedVersionLabel;
    }

    internal static SourceAcquisitionRunRequest FromCandidates(
        SourceFamily sourceFamily,
        IEnumerable<SourceDiscoveryCandidate> candidates)
    {
        var candidateSnapshot = candidates.ToArray();
        var sourceKey = sourceFamily.ToWireName();

        return new SourceAcquisitionRunRequest(
            sourceFamily,
            sourceKey,
            candidateSnapshot,
            runId: $"{sourceKey}_source_acquisition_run",
            requestedReportingYear: candidateSnapshot.Length == 1 ? candidateSnapshot[0].ReportingYear : null,
            requestedVersionLabel: candidateSnapshot.Length == 1 ? candidateSnapshot[0].VersionLabel : null);
    }
}
