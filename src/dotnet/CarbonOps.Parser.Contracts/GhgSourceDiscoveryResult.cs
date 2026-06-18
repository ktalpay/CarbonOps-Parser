namespace CarbonOps.Parser.Contracts;

public sealed record GhgSourceDiscoveryResult
{
    public GhgSourceDiscoveryStatus Status { get; }

    public GhgSourceDiscoveryRequest Request { get; }

    public IReadOnlyList<GhgSourceDocumentCandidate> Candidates { get; }

    public IReadOnlyList<GhgSourceDiscoveryIssue> Issues { get; }

    public bool NoNetwork { get; }

    public bool NoDownload { get; }

    public bool NoParse { get; }

    public bool NoDatabaseWrites { get; }

    public bool NoSql { get; }

    public bool NoScheduler { get; }

    public int CandidateCount => Candidates.Count;

    public IReadOnlyList<string> CandidateIds { get; }

    public GhgSourceDiscoveryResult(
        GhgSourceDiscoveryStatus status,
        GhgSourceDiscoveryRequest request,
        IEnumerable<GhgSourceDocumentCandidate> candidates,
        IEnumerable<GhgSourceDiscoveryIssue>? issues = null,
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
        Issues = Array.AsReadOnly((issues ?? Array.Empty<GhgSourceDiscoveryIssue>()).ToArray());
        NoNetwork = noNetwork;
        NoDownload = noDownload;
        NoParse = noParse;
        NoDatabaseWrites = noDatabaseWrites;
        NoSql = noSql;
        NoScheduler = noScheduler;
        CandidateIds = Array.AsReadOnly(candidateSnapshot.Select(candidate => candidate.CandidateId).ToArray());
    }
}
