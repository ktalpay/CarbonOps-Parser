namespace CarbonOps.Parser.Contracts;

public sealed record DefraSourceDiscoveryResult
{
    public DefraSourceDiscoveryStatus Status { get; }

    public DefraSourceDiscoveryRequest Request { get; }

    public IReadOnlyList<DefraSourceDocumentCandidate> Candidates { get; }

    public IReadOnlyList<DefraSourceDiscoveryIssue> Issues { get; }

    public bool NoNetwork { get; }

    public bool NoDownload { get; }

    public bool NoParse { get; }

    public bool NoDatabaseWrites { get; }

    public bool NoSql { get; }

    public bool NoScheduler { get; }

    public int CandidateCount => Candidates.Count;

    public IReadOnlyList<string> CandidateIds { get; }

    public DefraSourceDiscoveryResult(
        DefraSourceDiscoveryStatus status,
        DefraSourceDiscoveryRequest request,
        IEnumerable<DefraSourceDocumentCandidate> candidates,
        IEnumerable<DefraSourceDiscoveryIssue>? issues = null,
        bool noNetwork = true,
        bool noDownload = true,
        bool noParse = true,
        bool noDatabaseWrites = true,
        bool noSql = true,
        bool noScheduler = true)
    {
        var candidateSnapshot = candidates.ToArray();

        Status = status;
        Request = request;
        Candidates = Array.AsReadOnly(candidateSnapshot);
        Issues = Array.AsReadOnly((issues ?? Array.Empty<DefraSourceDiscoveryIssue>()).ToArray());
        NoNetwork = noNetwork;
        NoDownload = noDownload;
        NoParse = noParse;
        NoDatabaseWrites = noDatabaseWrites;
        NoSql = noSql;
        NoScheduler = noScheduler;
        CandidateIds = Array.AsReadOnly(candidateSnapshot.Select(candidate => candidate.CandidateId).ToArray());
    }
}
