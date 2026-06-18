namespace CarbonOps.Parser.Contracts;

public sealed record IpccSourceDiscoveryResult
{
    public IpccSourceDiscoveryStatus Status { get; }

    public IpccSourceDiscoveryRequest Request { get; }

    public IReadOnlyList<IpccSourceDocumentCandidate> Candidates { get; }

    public IReadOnlyList<IpccSourceDiscoveryIssue> Issues { get; }

    public bool NoNetwork { get; }

    public bool NoDownload { get; }

    public bool NoParse { get; }

    public bool NoDatabaseWrites { get; }

    public bool NoSql { get; }

    public bool NoScheduler { get; }

    public int CandidateCount => Candidates.Count;

    public IReadOnlyList<string> CandidateIds { get; }

    public IpccSourceDiscoveryResult(
        IpccSourceDiscoveryStatus status,
        IpccSourceDiscoveryRequest request,
        IEnumerable<IpccSourceDocumentCandidate> candidates,
        IEnumerable<IpccSourceDiscoveryIssue>? issues = null,
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
        Issues = Array.AsReadOnly((issues ?? Array.Empty<IpccSourceDiscoveryIssue>()).ToArray());
        NoNetwork = noNetwork;
        NoDownload = noDownload;
        NoParse = noParse;
        NoDatabaseWrites = noDatabaseWrites;
        NoSql = noSql;
        NoScheduler = noScheduler;
        CandidateIds = Array.AsReadOnly(candidateSnapshot.Select(candidate => candidate.CandidateId).ToArray());
    }
}
