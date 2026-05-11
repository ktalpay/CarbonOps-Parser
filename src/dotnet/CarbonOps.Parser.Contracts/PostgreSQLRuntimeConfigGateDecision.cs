namespace CarbonOps.Parser.Contracts;

public sealed record PostgreSQLRuntimeConfigGateDecision
{
    public PostgreSQLRuntimeConfigGateStatus Status { get; }

    public bool Requested { get; }

    public string Reason { get; }

    public bool ConfigLoadingEnabled { get; }

    public bool RuntimeEnabled { get; }

    public bool LoadsEnvironment { get; }

    public bool LoadsConfigFiles { get; }

    public bool LoadsCredentials { get; }

    public IReadOnlyList<string> RequiredFutureComponents { get; }

    public IReadOnlyList<string> SafeOperationalNotes { get; }

    public IReadOnlyList<PostgreSQLRuntimeConfigGateIssue> Issues { get; }

    public int RequiredFutureComponentCount => RequiredFutureComponents.Count;

    public int IssueCount => Issues.Count;

    public PostgreSQLRuntimeConfigGateDecision(
        PostgreSQLRuntimeConfigGateStatus status,
        bool requested,
        string reason,
        bool configLoadingEnabled,
        bool runtimeEnabled,
        bool loadsEnvironment,
        bool loadsConfigFiles,
        bool loadsCredentials,
        IEnumerable<string> requiredFutureComponents,
        IEnumerable<string> safeOperationalNotes,
        IEnumerable<PostgreSQLRuntimeConfigGateIssue>? issues = null)
    {
        Status = status;
        Requested = requested;
        Reason = reason;
        ConfigLoadingEnabled = configLoadingEnabled;
        RuntimeEnabled = runtimeEnabled;
        LoadsEnvironment = loadsEnvironment;
        LoadsConfigFiles = loadsConfigFiles;
        LoadsCredentials = loadsCredentials;
        RequiredFutureComponents = Array.AsReadOnly(requiredFutureComponents.ToArray());
        SafeOperationalNotes = Array.AsReadOnly(safeOperationalNotes.ToArray());
        Issues = Array.AsReadOnly((issues ?? []).ToArray());
    }
}
