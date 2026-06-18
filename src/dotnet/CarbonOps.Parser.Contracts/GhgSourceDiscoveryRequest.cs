namespace CarbonOps.Parser.Contracts;

public sealed record GhgSourceDiscoveryRequest
{
    public SourceFamily SourceFamily { get; }

    public string SourceKey { get; }

    public string DiscoveryReferenceUri { get; }

    public GhgSourceDiscoveryMode Mode { get; }

    public bool AllowNetwork { get; }

    public bool AllowDownload { get; }

    public bool AllowParse { get; }

    public bool AllowDatabaseWrites { get; }

    public bool AllowScheduler { get; }

    public GhgSourceDiscoveryRequest(
        SourceFamily sourceFamily,
        string sourceKey,
        string discoveryReferenceUri,
        GhgSourceDiscoveryMode mode = GhgSourceDiscoveryMode.RuntimePassive,
        bool allowNetwork = false,
        bool allowDownload = false,
        bool allowParse = false,
        bool allowDatabaseWrites = false,
        bool allowScheduler = false)
    {
        SourceFamily = sourceFamily;
        SourceKey = sourceKey;
        DiscoveryReferenceUri = discoveryReferenceUri;
        Mode = mode;
        AllowNetwork = allowNetwork;
        AllowDownload = allowDownload;
        AllowParse = allowParse;
        AllowDatabaseWrites = allowDatabaseWrites;
        AllowScheduler = allowScheduler;
    }
}
